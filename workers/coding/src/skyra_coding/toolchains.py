"""Trusted host toolchain identities; renderer/model input cannot select executables."""
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

from .native import NativeExecutor,NativeProfile
from .workspace import BoundaryError,Workspace

FIELDS={'node','node_sha256','node_version','compiler','compiler_sha256','compiler_version'}


def typescript_configuration():
    return {'compilerOptions':{'target':'ES2022','module':'NodeNext','moduleResolution':'NodeNext',
        'strict':True,'noEmit':True,'allowImportingTsExtensions':True,'verbatimModuleSyntax':True,
        'erasableSyntaxOnly':True,'noUncheckedIndexedAccess':True,'exactOptionalPropertyTypes':True,
        'types':[],'lib':['ES2022','DOM']},'include':['src/**/*.ts']}


def typescript_driver(test_path):
    if not isinstance(test_path,str) or not re.fullmatch(r'tests/[a-z][a-z0-9_.-]{1,80}\.mjs',test_path):
        raise BoundaryError('Fixed host test path required')
    return """import { spawnSync } from 'node:child_process';
const command = (exe,args) => {
  const result=spawnSync(exe,args,{stdio:'inherit',windowsHide:true,timeout:20000,shell:false});
  if(result.error || result.status!==0) process.exit(typeof result.status==='number' && result.status!==0 ? result.status : 1);
};
console.log('Node runtime',process.version);
command(process.argv[2],['--noEmit','--project','tsconfig.json']);
command(process.execPath,['--test','--test-reporter=spec',TEST_PATH]);
""".replace('TEST_PATH',json.dumps(test_path))


def _executable(value):
    if not isinstance(value,str) or not 1<=len(value)<=1024:
        raise BoundaryError('Absolute toolchain executable required')
    path=Path(value)
    if not path.is_absolute() or path.suffix.lower()!='.exe' or not path.is_file():
        raise BoundaryError('Existing absolute toolchain .exe required')
    return path.resolve()


def executable_digest(path):
    checksum=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):checksum.update(chunk)
    return checksum.hexdigest()


def verify_typescript(value):
    """Check detached, host-reviewed identities without executing project code."""
    if (not isinstance(value,dict) or set(value)!=FIELDS
            or not all(isinstance(item,str) for item in value.values())
            or any(len(value[key])>100 for key in ('node_version','compiler_version'))
            or not re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?',value['node_version'])
            or not re.fullmatch(r'Version [0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?',value['compiler_version'])
            or any(not re.fullmatch(r'[a-f0-9]{64}',value[key]) for key in ('node_sha256','compiler_sha256'))):
        raise BoundaryError('Exact reviewed TypeScript toolchain required')
    if int(value['node_version'][1:].split('.')[0])<24:
        raise BoundaryError('Node 24 or newer is required for this erasable-TypeScript profile')
    result=dict(value)
    for name in ('node','compiler'):
        path=_executable(value[name])
        if executable_digest(path)!=value[name+'_sha256']:
            raise BoundaryError('Reviewed toolchain changed; inspect and review it again')
        result[name]=str(path)
    return result


def inspect_typescript(node,compiler,*,owner_enabled=False):
    """Bounded hidden --version probes through the existing process-tree supervisor."""
    if owner_enabled is not True or os.name!='nt':
        raise BoundaryError('Explicit trusted Windows toolchain inspection required')
    executables={'node':_executable(node),'compiler':_executable(compiler)}
    hashes={name:executable_digest(path) for name,path in executables.items()}
    with tempfile.TemporaryDirectory(prefix='jarvis-toolchain-probe-') as directory:
        root=Path(directory);source=root/'source';source.mkdir()
        (source/'probe.json').write_text('{"purpose":"host-version-inspection"}\n',encoding='utf-8')
        workspace=Workspace.snapshot(source,root/'snapshot',['probe.json'])
        profiles=[NativeProfile(name+'-version',(str(path),'--version'),('probe.json',),15)
                  for name,path in executables.items()]
        runner=NativeExecutor(profiles,owner_enabled=True)
        versions={}
        for name in executables:
            report=runner.run(workspace,name+'-version')
            if not report['passed'] or report['cleanup_confirmed'] is not True or report['output_truncated']:
                raise BoundaryError('Toolchain version inspection failed or cleanup is uncertain')
            output=report['output'].strip()
            if len(output)>100:raise BoundaryError('Unexpected toolchain version output')
            versions[name]=output
    result={name:str(path) for name,path in executables.items()}
    for name in executables:
        result[name+'_sha256']=hashes[name];result[name+'_version']=versions[name]
    # A concurrent installer must not pair new version text with an older executable hash.
    return verify_typescript(result)


def runtime_fields(value):
    """Additive Node binding; preserve the exact legacy Python registration shape."""
    if 'runtime' not in value:return {'python_sha256':value['python_sha256']}
    runtime=value['runtime']
    if isinstance(runtime,dict) and runtime=={'kind':'fixed-executable-v1'}:
        identity=value.get('executable_sha256')
        if not isinstance(identity,str) or not re.fullmatch(r'[a-f0-9]{64}',identity):
            raise BoundaryError('Reviewed primary executable identity required')
        return {'runtime':{'kind':'fixed-executable-v1'},'executable_sha256':identity}
    if not isinstance(runtime,dict) or set(runtime)!={'kind','toolchain'} or runtime['kind']!='node-typescript-v1':
        raise BoundaryError('Unknown reviewed runtime binding')
    tools=verify_typescript(runtime['toolchain'])
    if (value.get('executable_sha256')!=tools['node_sha256']
            or value['profile']['argv']!=[tools['node'],'tests/run.mjs',tools['compiler']]):
        raise BoundaryError('Reviewed Node execution profile differs from its toolchain')
    return {'runtime':{'kind':'node-typescript-v1','toolchain':tools},'executable_sha256':tools['node_sha256']}


def primary_digest(value):
    fields=runtime_fields(value)
    return fields['executable_sha256'] if 'runtime' in fields else fields['python_sha256']


def secondary_bindings(value):
    fields=runtime_fields(value)
    if 'runtime' not in fields or fields['runtime']['kind']=='fixed-executable-v1':return {}
    tools=fields['runtime']['toolchain']
    return {tools['compiler']:tools['compiler_sha256']}
