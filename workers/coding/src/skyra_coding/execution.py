"""Fixed-profile Docker execution. No host-shell fallback or automatic image pulls."""

from dataclasses import dataclass, asdict
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
import time
import uuid

from .workspace import BoundaryError, Workspace


class SandboxUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class TestProfile:
    name: str
    image: str
    argv: tuple[str, ...]
    protected_paths: tuple[str, ...]
    timeout: int = 120

    def __post_init__(self):
        if not re.fullmatch(r'[a-z0-9_-]{1,64}',self.name):
            raise ValueError('Invalid profile name')
        if not re.fullmatch(r'(?:[a-z0-9./:_-]+@)?sha256:[a-f0-9]{64}',self.image):
            raise ValueError('Pin a reviewed image digest; mutable tags are forbidden')
        if not isinstance(self.argv,tuple) or not self.argv or any(not isinstance(x,str) or not x or len(x)>512 for x in self.argv):
            raise ValueError('Fixed command argument tuple required')
        if not self.protected_paths or not 1<=self.timeout<=300:
            raise ValueError('Protected tests and bounded timeout required')


class DockerSandbox:
    def __init__(self, profiles, executable=None, context='desktop-linux'):
        self.profiles={p.name:p for p in profiles}
        if len(self.profiles)!=len(profiles) or not self.profiles:
            raise ValueError('Unique test profiles required')
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}',context):
            raise ValueError('Invalid Docker context')
        self.executable=executable or shutil.which('docker')
        self.context=context

    def _cli(self,*args,timeout=10):
        if not self.executable:
            raise SandboxUnavailable('Docker executable unavailable')
        options={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}
        try:
            response=subprocess.run([self.executable,'--context',self.context,*args],
                                    capture_output=True,timeout=timeout,**options)
        except (OSError,subprocess.TimeoutExpired):
            raise SandboxUnavailable('Docker command unavailable or timed out') from None
        if response.returncode!=0:
            raise SandboxUnavailable('Docker command failed; host execution remains disabled')
        return response.stdout.decode('utf-8',errors='replace').strip()

    def probe(self):
        value=self._cli('info','--format','{{json .OSType}}')
        if json.loads(value)!='linux':
            raise SandboxUnavailable('Reviewed Linux-container backend required')
        return {'backend':'docker','context':self.context,'available':True}

    def create_args(self,profile,files, name):
        mount=str(Path(files).resolve())
        if ',' in mount or '\n' in mount:
            raise BoundaryError('Mount path cannot be encoded safely')
        return ['create','--pull=never','--name',name,'--label','skyra.jarvis.owner='+name,
                '--network=none','--read-only','--cap-drop=ALL','--security-opt=no-new-privileges',
                '--user=65534:65534','--pids-limit=64','--memory=512m','--memory-swap=512m',
                '--cpus=1','--ipc=private','--log-driver=none',
                '--tmpfs','/tmp:rw,nosuid,noexec,size=67108864',
                '--env','HOME=/tmp','--env','PYTHONDONTWRITEBYTECODE=1',
                '--mount','type=bind,source='+mount+',target=/workspace,readonly',
                '--workdir','/workspace','--entrypoint',profile.argv[0],profile.image,*profile.argv[1:]]

    def _remove_owned(self,cid,name):
        # Inspect ownership before removing the exact container created by this attempt.
        owner=self._cli('inspect','--format','{{index .Config.Labels "skyra.jarvis.owner"}}',cid)
        if owner!=name:
            raise SandboxUnavailable('Container ownership could not be verified')
        self._cli('rm','--force','--volumes',cid)

    def run(self,workspace,profile_name,poll=lambda:None):
        if profile_name not in self.profiles:
            raise BoundaryError('Test profile not registered')
        profile=self.profiles[profile_name]
        for path in profile.protected_paths:
            if path not in workspace.selected or workspace.original_hashes[path]=='absent' or workspace.read(path)['sha256']!=workspace.original_hashes[path]:
                raise BoundaryError('Protected test changed or unavailable')
        poll()
        self.probe()
        self._cli('image','inspect',profile.image)  # No pull/install during execution.
        name='jarvis-'+uuid.uuid4().hex
        started=time.monotonic()
        output=bytearray();overflow=threading.Event()
        cid=None;process=None;termination=None;exit_code=None;cleanup=False
        with tempfile.TemporaryDirectory(prefix='jarvis-execution-') as temporary:
            # Validate/copy only selected files. Container cannot see baseline, credentials or host repo.
            snapshot=workspace.execution_snapshot(Path(temporary)/'input')
            try:
                cid=self._cli(*self.create_args(profile,snapshot.root,name))
                if not re.fullmatch('[a-f0-9]{64}',cid):
                    raise SandboxUnavailable('Invalid container identifier')
                poll()
                options={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}
                process=subprocess.Popen([self.executable,'--context',self.context,'start','--attach',cid],
                                         stdout=subprocess.PIPE,stderr=subprocess.STDOUT,**options)
                def drain():
                    while True:
                        chunk=process.stdout.read(8192)
                        if not chunk:break
                        remaining=262144-len(output)
                        output.extend(chunk[:max(0,remaining)])
                        if len(chunk)>remaining:overflow.set()
                reader=threading.Thread(target=drain,daemon=True);reader.start()
                while process.poll() is None:
                    try:poll()
                    except Exception:
                        termination='authorization_or_cancellation';break
                    if overflow.is_set():termination='output_limit';break
                    if time.monotonic()-started>profile.timeout:termination='timeout';break
                    time.sleep(0.2)
                if termination is None:
                    process.wait(timeout=5)
                    status=json.loads(self._cli('inspect','--format','{{json .State}}',cid))
                    if status.get('Status')!='exited' or status.get('Running') or status.get('OOMKilled') or status.get('Error'):
                        termination='container_failure'
                    else:exit_code=status['ExitCode']
            finally:
                if cid and re.fullmatch('[a-f0-9]{64}',cid):
                    try:self._remove_owned(cid,name);cleanup=True
                    except SandboxUnavailable:cleanup=False
                if process is not None:
                    if process.poll() is None:
                        process.kill()
                    process.wait(timeout=5)
                    if 'reader' in locals():reader.join(timeout=5)
                    if process.stdout is not None:process.stdout.close()
        if overflow.is_set() and termination is None:
            termination='output_limit'
        if not cleanup:
            termination='cleanup_unconfirmed'
        input_hashes={path:snapshot.original_hashes.get(path,'absent') for path in workspace.selected}
        profile_hash=hashlib.sha256(json.dumps(asdict(profile),sort_keys=True,separators=(',',':')).encode()).hexdigest()
        return {'kind':'container_test','input_hashes':input_hashes,'profile_sha256':profile_hash,'profile':profile.name,'image':profile.image,
                'argv':list(profile.argv),'exit_code':exit_code,'termination':termination,
                'cleanup_confirmed':cleanup,'container_name':name,
                'output':output.decode('utf-8',errors='replace'),'output_truncated':overflow.is_set(),
                'duration_seconds':round(time.monotonic()-started,3),
                'passed':cleanup and termination is None and exit_code==0}
