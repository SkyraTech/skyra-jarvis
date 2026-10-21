"""Real Node execution with deterministic proposals; no online model or dependency install."""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

REPO=Path(__file__).resolve().parents[3]
for source in ('services/core/src','workers/coding/src','packages/agent-runtime/src'):
    sys.path.insert(0,str(REPO/source))
from jarvis_core import Core
from jarvis_core.build_jobs import BuildJobs
from jarvis_runtime import RepairRuntime
from skyra_coding import Workspace,FileWorker
from skyra_coding.native import NativeExecutor,NativeProfile

ORIGINAL='export function normalize(value) { return value; }\n'
NORMALIZE='''export function normalize(value) {
  if (typeof value !== 'string') throw new TypeError('Text required');
  return value.trim().toLowerCase().replace(/\\s+/gu, '-');
}
'''
LABEL="import { normalize } from './normalize.js';\nexport function label(value) { return `Skyra · ${normalize(value)}`; }\n"
CONTRACT='''import test from 'node:test';
import assert from 'node:assert/strict';
import { normalize } from '../src/normalize.js';
import { label } from '../src/label.js';
console.log('Node runtime', process.version);
test('normalizes surrounding and repeated whitespace', () => assert.equal(normalize(' Hello  World '), 'hello-world'));
test('reuses normalization in the branded label', () => assert.equal(label(' Build Agent '), 'Skyra · build-agent'));
test('rejects non-text values', () => assert.throws(() => normalize(4), TypeError));
'''


class Provider:
    provider='fixture';model='node-fixture';timeout=1;max_output_tokens=4096
    def __init__(self,broken_first=False):self.calls=0;self.contexts=[];self.broken_first=broken_first
    def complete(self,system,context,schema):
        data=json.loads(context);self.contexts.append(data);self.calls+=1
        source={record['path']:record for record in data['files']}
        replacements={'src/normalize.js': 'export function normalize( {\n' if self.broken_first and self.calls==1 else NORMALIZE}
        if source['src/label.js']['sha256']=='absent':replacements['src/label.js']=LABEL
        return json.dumps({'summary':'Implement shared normalization and reusable branded label',
            'patches':[{'path':path,'old':source[path]['content'],'new':content} for path,content in replacements.items()]}),{'total_tokens':80}


@unittest.skipUnless(os.name=='nt' and shutil.which('node'),'Windows and installed Node required')
class NodeJobTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.source=self.root/'source';(self.source/'src').mkdir(parents=True);(self.source/'tests').mkdir()
        (self.source/'src/normalize.js').write_text(ORIGINAL,encoding='utf-8')
        (self.source/'package.json').write_text('{"name":"skyra-agent-node-fixture","private":true,"type":"module"}\n',encoding='utf-8')
        (self.source/'tests/contract.test.js').write_text(CONTRACT,encoding='utf-8')
        self.files=['package.json','tests/contract.test.js','src/normalize.js','src/label.js']
        self.workspace=Workspace.snapshot(self.source,self.root/'snapshot',self.files[:-1],self.files[-1:])
        self.database=self.root/'core.sqlite3';self.now=1000.;self.core=Core(self.database,clock=lambda:self.now)
        self.project=self.core.create_project('owner','Internal Node execution fixture')
        self.core.set_policy('owner',self.project,'full',['workspace:node'])
        self.profile=NativeProfile('node-contract',(str(Path(shutil.which('node')).resolve()),'--test','--test-reporter=spec','tests/contract.test.js'),
            ('package.json','tests/contract.test.js'),20)
        self.worker=FileWorker({(self.project,'workspace:node'):self.workspace},self.root/'evidence',NativeExecutor([self.profile],owner_enabled=True))
        self.provider=Provider();self.runtime=RepairRuntime(self.worker,{'fixture':self.provider});self.jobs=BuildJobs(self.runtime)

    def tearDown(self):self.core.close();self.temp.cleanup()

    def create(self,auto_accept=False):
        return self.jobs.create(self.core,'owner',self.project,'workspace:node','node-contract','fixture',
            'Create a reusable normalization module and branded label, preserve the independent contract.',self.files,[],
            2,2,40,3600,auto_accept,True,'node-feature',mode='feature',edit_protocol='host-bound-v2',expected_skills={})

    def tick(self):
        self.now+=6
        return self.jobs.tick(self.core,'owner',self.project)['build_job']

    def until(self,states):
        for _ in range(40):
            result=self.tick()
            if result and result['state'] in states:return result
        self.fail('Node job did not reach the expected bounded state')

    def assert_completed(self,result):
        self.assertEqual('completed',result['state'],result)
        self.assertEqual(ORIGINAL,(self.source/'src/normalize.js').read_text(encoding='utf-8'))
        self.assertFalse((self.source/'src/label.js').exists())
        for name in self.profile.protected_paths:self.assertEqual(self.workspace.original_hashes[name],self.workspace.read(name)['sha256'])
        run=self.runtime.workflow.get(self.core,'owner',result['run'])
        tests=[self.worker.evidence(item['evidence'][0])['result'] for item in run['results'] if item['evidence']
               and self.worker.evidence(item['evidence'][0])['operation']=='test']
        self.assertIs(tests[-1]['passed'],True);self.assertIs(tests[-1]['cleanup_confirmed'],True)
        self.assertEqual('native_trusted',tests[-1]['mode']);self.assertIs(tests[-1]['os_isolation'],False)
        self.assertIn('tests 3',tests[-1]['output']);self.assertIn('Node runtime v',tests[-1]['output'])
        self.assertEqual(set(self.files),set(tests[-1]['input_hashes']))

    def test_reviewed_node_multifile_creation_retests_after_core_restart(self):
        self.create()
        waiting=self.until({'waiting_review','failed','blocked'})
        self.assertEqual('waiting_review',waiting['state'],waiting)
        proposal=self.runtime.get(self.core,'owner',waiting['proposal'])
        creation=next(edit for edit in proposal['response']['patches'] if edit['path']=='src/label.js')
        self.assertEqual('absent',creation['expected_sha256'])
        self.jobs.accept(self.core,'owner',waiting['id'],proposal['context_sha256'],proposal['response_sha256'])
        self.core.close();self.core=Core(self.database,clock=lambda:self.now)
        result=self.until({'completed','failed','blocked','budget_limited'})
        self.assert_completed(result);self.assertEqual(1,self.provider.calls)
        self.assertEqual(LABEL,self.workspace.read('src/label.js')['content'])

    def test_node_syntax_failure_drives_a_second_bound_generation(self):
        self.provider.broken_first=True;self.create(auto_accept=True)
        result=self.until({'completed','failed','blocked','budget_limited'})
        self.assert_completed(result);self.assertEqual(2,self.provider.calls)
        self.assertEqual('failed_retest',result['cycles'][0]['state'])
        self.assertIn('SyntaxError',self.provider.contexts[1]['diagnostics']['output'])
        current=next(record for record in self.provider.contexts[1]['files'] if record['path']=='src/normalize.js')
        self.assertIn('normalize( {',current['content'])
        # Generic static checks still honestly report JavaScript as unsupported.
        self.assertIs(self.workspace.verify()['passed'],False)
        self.assertEqual('unsupported',next(record for record in self.workspace.verify()['files'] if record['path']=='src/normalize.js')['status'])

    def test_typescript_calibration_baseline_is_real_and_toolchain_drift_blocks_resume(self):
        from jarvis_runtime import node_calibration
        source=self.root/'typescript-source'
        fixture=node_calibration.prepare(source)
        config={'node_toolchain':fixture['toolchain'],'protected_paths':fixture['protected']}
        workspace=Workspace.snapshot(source,self.root/'typescript-snapshot',fixture['selected'],fixture['absent'])
        profile=node_calibration.profile(config)
        result=NativeExecutor([profile],owner_enabled=True).run(workspace,'contract')
        self.assertIs(result['passed'],False);self.assertIs(result['cleanup_confirmed'],True)
        self.assertEqual(1,result['exit_code'])
        self.assertIn('ERR_MODULE_NOT_FOUND',result['output'])
        self.assertNotIn('error TS',result['output'])
        self.assertIn('Node runtime v',result['output'])
        name,independent=node_calibration.independent_profile(config)
        self.assertEqual(name,independent.name)
        self.assertEqual(profile.protected_paths,independent.protected_paths)
        config['node_toolchain']['compiler_sha256']='0'*64
        with self.assertRaises(ValueError):node_calibration.profile(config)


if __name__=='__main__':unittest.main()
