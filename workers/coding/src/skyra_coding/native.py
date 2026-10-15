"""Owner-enabled native execution for trusted repositories; full account privileges."""

from dataclasses import dataclass, asdict
import os
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import threading
import time

from .execution import SandboxUnavailable
from .workspace import BoundaryError,Workspace


@dataclass(frozen=True)
class NativeProfile:
    name: str
    argv: tuple[str,...]
    protected_paths: tuple[str,...]
    timeout: int=120

    def __post_init__(self):
        if not self.name or not isinstance(self.argv,tuple) or not self.argv or not self.protected_paths:
            raise ValueError('Named fixed command and protected tests required')
        if not all(isinstance(v,str) and v and len(v)<=1024 for v in self.argv):
            raise ValueError('Invalid command argument')
        executable=Path(self.argv[0])
        if not executable.is_absolute() or not executable.is_file() or executable.suffix.lower()!='.exe':
            raise ValueError('Native profile executable must be an existing absolute .exe path')
        if not 1<=self.timeout<=300:raise ValueError('Timeout must be 1..300 seconds')


class NativeExecutor:
    def __init__(self,profiles,*,owner_enabled=False):
        if owner_enabled is not True:
            raise ValueError('Owner must explicitly enable trusted native execution')
        self.profiles={p.name:p for p in profiles}
        if not self.profiles or len(self.profiles)!=len(profiles):
            raise ValueError('Unique profiles required')

    def probe(self):
        if os.name!='nt':raise SandboxUnavailable('Windows native supervisor required')
        return {'backend':'native_trusted','available':True,'os_isolation':False}

    def run(self,workspace,profile_name,poll=lambda:None):
        self.probe()
        if profile_name not in self.profiles:raise BoundaryError('Profile not registered')
        profile=self.profiles[profile_name]
        for path in profile.protected_paths:
            if path not in workspace.selected or workspace.original_hashes[path]=='absent' or workspace.read(path)['sha256']!=workspace.original_hashes[path]:
                raise BoundaryError('Protected tests changed or unavailable')
        from .windows_job import WindowsJob
        poll()
        output=bytearray();overflow=threading.Event();reason=None;exit_code=None;cleanup=False
        started=time.monotonic()
        with tempfile.TemporaryDirectory(prefix='jarvis-native-') as directory:
            snapshot=workspace.execution_snapshot(Path(directory)/'input')
            env={key:value for key,value in os.environ.items() if key.upper() in {
                'SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','PATH','TEMP','TMP','SYSTEMDRIVE'}}
            env['PYTHONDONTWRITEBYTECODE']='1'
            job=WindowsJob();process=None;reader=None
            try:
                # Assign the suspended process before any project code can spawn children.
                process=subprocess.Popen(profile.argv,cwd=snapshot.root,env=env,
                    stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,
                    shell=False,creationflags=subprocess.CREATE_NO_WINDOW|0x4)
                job.attach_and_resume(process.pid)
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
                    except Exception:reason='authorization_or_cancellation';break
                    if overflow.is_set():reason='output_limit';break
                    if time.monotonic()-started>profile.timeout:reason='timeout';break
                    time.sleep(0.1)
                if reason is None:exit_code=process.wait(timeout=5)
            finally:
                cleanup=job.stop()
                if process is not None:
                    if process.poll() is None:process.kill()
                    process.wait(timeout=5)
                    if reader:reader.join(timeout=5)
                    if process.stdout:process.stdout.close()
        if overflow.is_set() and reason is None:reason='output_limit'
        if not cleanup:reason='cleanup_unconfirmed'
        input_hashes={path:snapshot.original_hashes.get(path,'absent') for path in workspace.selected}
        profile_hash=hashlib.sha256(json.dumps(asdict(profile),sort_keys=True,separators=(',',':')).encode()).hexdigest()
        return {'kind':'native_test','mode':'native_trusted','os_isolation':False,
                'input_hashes':input_hashes,'profile_sha256':profile_hash,'profile':profile.name,'argv':list(profile.argv),'exit_code':exit_code,'termination':reason,
                'cleanup_confirmed':cleanup,'output':output.decode('utf-8',errors='replace'),
                'output_truncated':overflow.is_set(),'duration_seconds':round(time.monotonic()-started,3),
                'passed':cleanup and reason is None and exit_code==0}
