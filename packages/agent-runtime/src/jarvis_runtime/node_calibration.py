"""Supervisor-owned TypeScript acceptance, not the E2E product implementation."""
import json
import os
from pathlib import Path
import shutil
import subprocess
from skyra_coding.toolchains import inspect_typescript,typescript_configuration,typescript_driver

REPO=Path(__file__).resolve().parents[4]

GOAL='''Build a reusable strict TypeScript target-profile validator for the future Skyra E2E engine.
Create only src/guards.ts and src/target.ts. Reuse the protected Target interface in
src/types.ts. Do not change tests, package.json, tsconfig.json or tests/run.mjs.
No dependencies, network requests, filesystem access, subprocesses or global mutation.

guards.ts exports reusable record(value: unknown): Record<string, unknown>,
text(value: unknown, maximum: number): string, and
onlyKeys(value: Record<string, unknown>, allowed: readonly string[]): void.
record accepts plain objects with Object.prototype or null prototype, rejecting
arrays, null, classes and non-JSON property keys. text trims a string, requires
1..maximum characters after trimming and rejects non-strings. onlyKeys rejects
extra own keys, including symbols and non-enumerable properties. Error messages
must never echo input values. Use these helpers in target.ts rather than duplicating validation.

target.ts exports validateTarget(input: unknown, options?: {allowProduction: boolean}): Target.
Accept exactly project, environment, baseUrl and optional build. project is trimmed,
nonempty text <=100 characters. environment is exactly local, staging or production.
Production is disabled by default; only a separately supplied literal boolean true
options.allowProduction permits it. Validate options at runtime; reject unexpected
options keys and non-boolean allowProduction. This is a host option, never an input field.
Optional build is trimmed nonempty text <=128 characters. Reject explicit undefined.

baseUrl is a string <=2048 characters before and after URL canonicalization, trimmed
at its edges. Permit only absolute http/https URLs, including localhost, private IPs
and IPv6 for explicitly configured local work. Reject any credentials, raw backslash,
ASCII control character, query or fragment delimiter (even an empty ? or #).
Return canonical URL text with trailing slashes removed, preserving a non-root path
prefix. Do not resolve DNS or describe format validation as SSRF protection or authorization.
Return a fresh Target without mutating the input or adding absent optional properties.
Use type-only imports for Target and .ts extensions for local imports; Node executes
erasable TypeScript directly while the protected compiler enforces strict typing.
The tests are examples, not the entire specification. Explain the concrete changes
briefly and return only the host-bound patch schema; do not claim tests already ran.'''

TYPES="""export type Target = {
  project: string;
  environment: 'local' | 'staging' | 'production';
  baseUrl: string;
  build?: string;
};
"""

CONTRACT="""import test from 'node:test';
import assert from 'node:assert/strict';
import { validateTarget } from '../src/target.ts';
import { record, text, onlyKeys } from '../src/guards.ts';
const valid = (extra = {}) => ({project:'  article-dashboard  ', environment:'local', baseUrl:'http://localhost:4200/', ...extra});
const rejects = (input, options) => assert.throws(() => validateTarget(input, options), TypeError);
test('local URL and project normalize without mutation or invented fields', () => {
  const input=Object.freeze(valid());
  assert.deepEqual(validateTarget(input), {project:'article-dashboard', environment:'local', baseUrl:'http://localhost:4200'});
  assert.equal(input.baseUrl,'http://localhost:4200/');
});
test('HTTPS prefixes, IPv6, and optional build normalize', () => {
  assert.deepEqual(validateTarget(valid({environment:'staging',baseUrl:'https://EXAMPLE.test/articles///',build:'  abc123  '})),
    {project:'article-dashboard',environment:'staging',baseUrl:'https://example.test/articles',build:'abc123'});
  assert.equal(validateTarget(valid({baseUrl:'http://[::1]:4200/'})).baseUrl,'http://[::1]:4200');
});
test('production requires separate exact host consent', () => {
  const input=valid({environment:'production'}); rejects(input);
  assert.equal(validateTarget(input,{allowProduction:true}).environment,'production');
  for (const options of [{allowProduction:1},{allowProduction:'true'},{allowProduction:true,extra:true},null,[]]) rejects(input,options);
  rejects(valid({allowProduction:true,environment:'production'}));
});
test('wrong field types and unknown keys fail', () => {
  for (const patch of [{project:4},{project:''},{project:'x'.repeat(101)}, {environment:'LOCAL'}, {environment:4},
    {baseUrl:4},{build:4},{build:''},{build:'x'.repeat(129)},{build:undefined},{extra:true}]) rejects(valid(patch));
  for (const input of [null,[],4,'text',new Date()]) rejects(input);
  const missing=valid();delete missing.project;rejects(missing);
});
test('credentials, relative URLs and non-HTTP schemes fail safely', () => {
  for (const baseUrl of ['https://private-user:private-pass@example.test/','/relative','file:///tmp/data','javascript:alert(1)','ws://example.test','not-a-url-private-secret']) {
    try { validateTarget(valid({baseUrl})); assert.fail('Expected rejection'); }
    catch (error) { assert.ok(error instanceof TypeError);assert.doesNotMatch(error.message,/private-user|private-pass|private-secret/); }
  }
});
test('queries, fragments and parser control normalization are rejected', () => {
  for (const baseUrl of ['https://example.test/?q=1','https://example.test/?','https://example.test/#','https://example.test/#part',
    'https://example.test/\\\\evil','https://example.test/a\\nb','\\thttps://example.test/']) rejects(valid({baseUrl}));
});
test('URL bounds apply before and after canonicalization', () => {
  rejects(valid({baseUrl:'https://example.test/'+'x'.repeat(2048)}));
  rejects(valid({baseUrl:'https://example.test/'+'é'.repeat(400)}));
});
test('null-prototype records work; exotic own keys are rejected', () => {
  assert.equal(validateTarget(Object.assign(Object.create(null),valid())).project,'article-dashboard');
  const symbol=valid();symbol[Symbol('unexpected')]=true;rejects(symbol);
  const hidden=valid();Object.defineProperty(hidden,'hidden',{value:true});rejects(hidden);
  rejects(JSON.parse('{"project":"article","environment":"local","baseUrl":"https://example.test","__proto__":{}}'));
});
test('reusable guards enforce exact data boundaries', () => {
  const input=Object.create(null);input.name='Skyra';assert.equal(record(input),input);
  assert.equal(text(' Skyra ',10),'Skyra');onlyKeys(input,['name']);
  for (const input of [null,[],new Date(),4]) assert.throws(() => record(input),TypeError);
  for (const input of [4,null,'','  ','x'.repeat(11)]) assert.throws(() => text(input,10),TypeError);
  assert.throws(() => onlyKeys({unexpected:true},['name']),TypeError);
});
"""


def toolchain():
    node=shutil.which('node')
    compiler=REPO/'apps/desktop/node_modules/typescript/lib/getExePath.js'
    if os.name!='nt' or not node or not compiler.is_file():raise ValueError('Installed Windows Node/TypeScript toolchain required')
    node=str(Path(node).resolve())
    options={'capture_output':True,'text':True,'timeout':15,'check':True,'creationflags':subprocess.CREATE_NO_WINDOW}
    script='import getExePath from '+json.dumps(compiler.as_uri())+'; console.log(getExePath());'
    executable=Path(subprocess.run([node,'--input-type=module','-e',script],**options).stdout.strip()).resolve()
    if not executable.is_file() or executable.suffix.lower()!='.exe':raise ValueError('Installed TypeScript executable required')
    return inspect_typescript(node,str(executable),owner_enabled=True)


def prepare(source):
    tools=toolchain()
    (source/'src').mkdir(parents=True,exist_ok=True);(source/'tests').mkdir(parents=True,exist_ok=True)
    runner=typescript_driver('tests/contract.test.mjs')
    files={'src/types.ts':TYPES,'tests/contract.test.mjs':CONTRACT,'tests/run.mjs':runner,
           'package.json':json.dumps({'name':'skyra-e2e-target-calibration','private':True,'type':'module'}),
           'tsconfig.json':json.dumps(typescript_configuration())}
    for path,content in files.items():(source/path).write_text(content,encoding='utf-8')
    return {'selected':list(files),'protected':list(files),'absent':['src/guards.ts','src/target.ts'],'toolchain':tools}


def profile(config):
    from skyra_coding.native import NativeProfile
    if toolchain()!=config['node_toolchain']:raise ValueError('Reviewed Node/TypeScript toolchain changed')
    return NativeProfile('contract',(config['node_toolchain']['node'],'tests/run.mjs',config['node_toolchain']['compiler']),tuple(config['protected_paths']),45)


def independent_profile(config):
    from skyra_coding.native import NativeProfile
    script="""import a from 'node:assert/strict';import {pathToFileURL as u} from 'node:url';import {resolve} from 'node:path';
const {validateTarget:v}=await import(u(resolve('src/target.ts')).href);
const t={project:'A',environment:'local',baseUrl:'https://example.test/'};
a.equal(v({...t,baseUrl:'HTTPS://EXAMPLE.test:443/'}).baseUrl,'https://example.test');
a.equal(v({...t,baseUrl:'http://192.168.1.2:4200/p%3Fx/'}).baseUrl,'http://192.168.1.2:4200/p%3Fx');
for(const o of [{},{allowProduction:undefined},new Date()])a.throws(()=>v(t,o),TypeError);
for(const p of [{project:new String('A')},{environment:true},{baseUrl:'https://example.test/a'+String.fromCharCode(127)}])a.throws(()=>v({...t,...p}),TypeError);
const out=v(Object.freeze(t));out.project='B';a.equal(t.project,'A');
console.log('Independent target checks passed');"""
    return 'independent-e2e-targets-v1',NativeProfile('independent-e2e-targets-v1',
        (config['node_toolchain']['node'],'--input-type=module','-e',script),tuple(config['protected_paths']),20)
