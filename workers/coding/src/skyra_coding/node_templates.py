"""Host-owned strict TypeScript library scaffold; no model-selected commands."""
import json
import math

from .toolchains import verify_typescript,typescript_configuration,typescript_driver
from .workspace import BoundaryError

TEMPLATE='typescript-json-function-v1'
TEST='tests/acceptance.test.mjs'
TYPES='export type JsonValue = null | boolean | number | string | JsonValue[] | { [key: string]: JsonValue };\n'
STUB='import type { JsonValue } from "./types.ts";\n\nexport function handle(value: JsonValue): JsonValue {\n  throw new Error("Implementation pending");\n}\n'


def portable_numbers(value):
    if type(value) in (int,float):
        if abs(value)>9007199254740991 or (type(value) is float and not math.isfinite(value)):
            raise BoundaryError('TypeScript examples require finite numbers within the safe JSON number range')
    elif type(value) is list:
        for item in value:portable_numbers(item)
    elif type(value) is dict:
        for item in value.values():portable_numbers(item)


def plan(data,target,name,contract,toolchain):
    from jarvis_core.specifications import DOCUMENT_NAMES
    tools=verify_typescript(toolchain)
    portable_numbers(contract)
    serialized=json.dumps(contract,sort_keys=True,separators=(',',':'),allow_nan=False)
    test="""import test from 'node:test';
import assert from 'node:assert/strict';
import { handle } from '../src/main.ts';
const cases=JSON.parse(CONTRACT);
function jsonData(value,depth=0) {
  if(depth>20) throw new TypeError('JSON output is nested too deeply');
  if(value===null || typeof value==='string' || typeof value==='boolean') return value;
  if(typeof value==='number' && Number.isFinite(value) && Math.abs(value)<=Number.MAX_SAFE_INTEGER) return value;
  if(Array.isArray(value)) {
    if(Reflect.ownKeys(value).length!==value.length+1) throw new TypeError('Invalid JSON array');
    return Array.from(value,item=>jsonData(item,depth+1));
  }
  if(typeof value==='object' && (Object.getPrototypeOf(value)===Object.prototype || Object.getPrototypeOf(value)===null)) {
    const keys=Reflect.ownKeys(value);
    if(keys.some(key=>typeof key!=='string' || !Object.getOwnPropertyDescriptor(value,key)?.enumerable || !('value' in Object.getOwnPropertyDescriptor(value,key))))
      throw new TypeError('Invalid JSON object');
    return Object.fromEntries(keys.sort().map(key=>[key,jsonData(value[key],depth+1)]));
  }
  throw new TypeError('Non-JSON output');
}
for(const item of cases.cases) test(item.name,()=>assert.deepStrictEqual(jsonData(handle(structuredClone(item.input))),jsonData(item.output)));
""".replace('CONTRACT',json.dumps(serialized))
    compiler_version=tools['compiler_version'].removeprefix('Version ')
    files={'src/main.ts':STUB,'src/helpers.ts':'// Add shared helpers here when required by the approved specification.\nexport {};\n',
        'src/types.ts':TYPES,TEST:test,'tests/run.mjs':typescript_driver(TEST),
        'acceptance.json':serialized+'\n','tsconfig.json':json.dumps(typescript_configuration(),indent=2)+'\n',
        'package.json':json.dumps({'name':name,'private':True,'type':'module','engines':{'node':'>=24'},
            'scripts':{'typecheck':'tsc --noEmit','test':'node --test --test-reporter=spec '+TEST},
            'devDependencies':{'typescript':compiler_version}},indent=2)+'\n',
        **{'docs/'+key:value for key,value in data['documents'].items()}}
    defaults={
        '02_SYSTEM_ARCHITECTURE.md':'# System architecture\n\nStrict TypeScript ES-module function library. src/main.ts exports handle(value); src/helpers.ts may hold reusable helpers; protected src/types.ts defines JsonValue. Fixed host acceptance compiles before running Node tests. No server, browser executor or deployment is included.\n',
        '03_DEVELOPMENT_RULES.md':'# Development rules\n\nUse strict, erasable TypeScript and type-only imports. Preserve protected manifests/types/tests. Run the reviewed fixed acceptance profile. Dependency installation and lockfile creation require a separate governed step; no installation occurs during scaffolding. Do not commit or deploy automatically.\n',
        '04_DESIGN_SYSTEM.md':'# Design system\n\nThis library has no user interface. Preserve approved product branding in any future interface scope.\n',
        '07_API_AND_EVENTS.md':'# API and events\n\nThe current interface is src/main.ts handle(value: JsonValue): JsonValue. Acceptance examples use portable finite JSON numbers within the safe JavaScript range. HTTP APIs and events are not implemented.\n',
        '09_SECURITY_AND_OPERATIONS.md':'# Security and operations\n\nNo credentials are included. Native execution uses the Windows account privileges and requires separate host/owner consent. Node/compiler executable hashes and protected acceptance inputs are bound. Source delivery stays separate. Tests cover reviewed examples; they do not certify security or production readiness.\n'}
    for key,value in defaults.items():files.setdefault('docs/'+key,value)
    selected=[path for path in files if not path.startswith('docs/')]
    protected=[path for path in selected if path not in {'src/main.ts','src/helpers.ts'}]
    return {'template':TEMPLATE,'project':data['project'],'specification':data['id'],
        'specification_sha256':data['sha256'],'destination':str(target),'name':name,'contract':contract,
        'files':files,'selected':selected,'profile':{'name':'scaffold-acceptance',
            'argv':[tools['node'],'tests/run.mjs',tools['compiler']],'protected_paths':protected,'timeout':45},
        'runtime':{'kind':'node-typescript-v1','toolchain':tools},'executable_sha256':tools['node_sha256'],
        'document_provenance':{key:'approved_specification' if key in data['documents'] else 'host_template' for key in DOCUMENT_NAMES},
        'limitations':['Only the reviewed JSON examples are tested.',
            'TS/MJS static checks are unsupported here; compilation occurs only in the separately owner-enabled fixed profile.',
            'No dependency installation or lockfile, server, browser execution, Git operations or deployment is performed.',
            'Filesystem publication and SQLite audit are separate; registration/grants/native execution require separate owner consent.']}
