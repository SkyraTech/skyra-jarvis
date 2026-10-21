import hashlib
import json
from pathlib import Path
import secrets
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch, MagicMock

REPO = Path(__file__).resolve().parents[3]
for source in ('services/core/src', 'workers/coding/src', 'packages/agent-runtime/src'):
    sys.path.insert(0, str(REPO / source))

from fastapi.testclient import TestClient
from jarvis_core import Core, Conflict, Denied
from jarvis_core.api import Credential, create_app
from jarvis_runtime import RepairRuntime, Skill
from jarvis_runtime.providers import OnlineProvider, load_providers
from skyra_coding import Workspace, FileWorker
from skyra_coding.native import NativeExecutor, NativeProfile
from jarvis_runtime.runtime import model_context, checksum


class ModelContextTests(unittest.TestCase):
    def test_review_is_last_without_losing_source_or_changing_canonical_identity(self):
        context = {'goal': 'original scope', 'files': [{'path': 'source.ts', 'content': 'current source'}],
                   'diagnostics': {'proposal_review': {'feedback': 'current defect'}, 'output': 'old compiler output'},
                   'skills': []}
        original = json.dumps(context, sort_keys=True)
        identity = checksum(context)
        payload = model_context(context)
        decoded = json.loads(payload)
        self.assertEqual(decoded, context)
        self.assertEqual(list(decoded)[-1], 'diagnostics')
        self.assertEqual(list(decoded['diagnostics'])[-1], 'proposal_review')
        self.assertGreater(payload.index('current defect'), payload.index('current source'))
        self.assertEqual(checksum(decoded), identity)
        self.assertEqual(json.dumps(context, sort_keys=True), original)

    def test_nonreview_context_preserves_diagnostics_and_original_plain_encoding(self):
        self.assertEqual(json.loads(model_context({'files': [], 'diagnostics': {'output': 'failure'}})),
                         {'files': [], 'diagnostics': {'output': 'failure'}})
        self.assertEqual(model_context({'goal': 'plain', 'files': []}), '{"files":[],"goal":"plain"}')


class FeatureInstructionTests(unittest.TestCase):
    def test_feature_failure_diagnostics_do_not_replace_current_goal(self):
        from jarvis_runtime.runtime import instructions
        context = {'mode':'feature','edit_protocol':'host-bound-v2','goal':'Build a working editor',
                   'diagnostics':{'output':'Type import fails'}}
        text = instructions(context)
        self.assertIn('A failing baseline or compiler diagnostic does not replace the current feature goal', text)
        self.assertIn('Implement the complete current goal and latest review requirements', text)
        self.assertIn('cannot execute tools', text)
        self.assertNotIn('A failing baseline or compiler diagnostic', instructions({'mode':'repair'}))


class FakeProvider:
    model = 'fixture-model'

    def __init__(self):
        self.calls = 0
        self.response = None
        self.callback = None

    def complete(self, system, context, schema):
        self.calls += 1
        data = json.loads(context)
        self.context = data
        if self.callback:
            self.callback()
        record = data['files'][0]
        return self.response or json.dumps({'summary': 'Correct answer', 'patches': [{
            'path': record['path'], 'expected_sha256': record['sha256'], 'old': '41', 'new': '42'}]}), {'total_tokens': 30}


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'tests').mkdir()
        (self.source / 'app.py').write_text('def answer():\n    return 41\n', encoding='utf-8')
        (self.source / 'tests/test_app.py').write_text(
            'import sys,unittest\nfrom pathlib import Path\nsys.path.insert(0,str(Path(__file__).resolve().parents[1]))\n'
            'from app import answer\nclass TestAnswer(unittest.TestCase):\n    def test_answer(self):self.assertEqual(42,answer())\n', encoding='utf-8')
        self.workspace = Workspace.snapshot(self.source, self.root / 'snapshot', ['app.py', 'tests/test_app.py'])
        self.database = self.root / 'core.sqlite3'
        self.core = Core(self.database)
        self.project = self.core.create_project('owner', 'Runtime fixture')
        self.resource = 'workspace:fixture'
        self.core.set_policy('owner', self.project, 'full', [self.resource])
        profile = NativeProfile('unit', (sys.executable, '-I', '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v'),
                                ('tests/test_app.py',), 10)
        self.worker = FileWorker({(self.project, self.resource): self.workspace}, self.root / 'evidence',
                                 NativeExecutor([profile], owner_enabled=True))
        self.provider = FakeProvider()
        self.runtime = RepairRuntime(self.worker, {'fixture': self.provider}, [Skill('repair', '1', 'Keep fixes minimal.')])

    def tearDown(self):
        self.core.close()
        self.temp.cleanup()

    def create(self, **overrides):
        args = dict(resource=self.resource, profile='unit', provider='fixture', goal='Return the expected answer.',
                    files=['app.py', 'tests/test_app.py'], skills=['repair'], request_id='request-1')
        args.update(overrides)
        return self.runtime.create(self.core, 'owner', self.project, **args)

    def generate(self):
        proposal = self.create()
        return self.runtime.generate(self.core, 'owner', proposal)

    def test_host_bound_full_replacement_has_bounded_raw_size_and_legacy_is_unchanged(self):
        source = 'a' * 35000
        record = {'path':'app.py','content':source,'sha256':hashlib.sha256(source.encode()).hexdigest(),'protected':False}
        data = {'context':{'edit_protocol':'host-bound-v2','files':[record]}}
        text = json.dumps({'summary':'Replace selected source','patches':[{'path':'app.py','old':source,'new':'b'*35000}]})
        self.assertGreater(len(text.encode()),64000)
        self.assertEqual('b'*35000,self.runtime._validate(text,data)['patches'][0]['new'])
        with self.assertRaises(ValueError):self.runtime._validate(text+' '*96001,data)
        legacy = {'context':{'files':[record]}}
        with self.assertRaises(ValueError):self.runtime._validate(text,legacy)

    def test_selected_context_supports_32_small_files_but_keeps_count_and_byte_boundaries(self):
        names = ['app.py', 'tests/test_app.py'] + [f'note-{index}.txt' for index in range(30)]
        for name in names[2:]: (self.source / name).write_text('context', encoding='utf8')
        self.workspace = Workspace.snapshot(self.source, self.root / 'large-selection', names)
        self.worker.workspaces[(self.project,self.resource)] = self.workspace
        proposal = self.create(files=names)
        self.assertEqual(32,len(self.runtime.get(self.core,'owner',proposal)['context']['files']))
        with self.assertRaises(ValueError):self.create(files=names+['extra.txt'],request_id='too-many')
        record = self.workspace.read(names[2])
        self.workspace.patch(names[2],record['sha256'],'context','x'*128001)
        with self.assertRaisesRegex(ValueError,'128 KB'):self.create(files=names,request_id='too-large')
        self.assertEqual(0,self.provider.calls)

    def test_proposal_api_uses_same_selected_file_count_limit(self):
        from jarvis_core.api import ProposalInput
        from pydantic import ValidationError
        values={'resource':'workspace:fixture','profile':'unit','provider':'fixture','goal':'Bounded selection',
                'files':[f'file-{index}.txt' for index in range(32)],'request_id':'count-boundary'}
        self.assertEqual(32,len(ProposalInput(**values).files))
        with self.assertRaises(ValidationError):ProposalInput(**{**values,'files':values['files']+['extra.txt']})

    def test_approved_specification_binds_and_invalidates_repair_handoff(self):
        self.creation_workspace()
        from jarvis_runtime.conversation import ConversationRuntime
        from jarvis_core.specifications import publish, approve
        from test_conversation import Provider
        conversation = self.core.create_conversation('owner', self.project)
        runtime = ConversationRuntime({'fixture':Provider()})
        turn = runtime.create(self.core,'owner',conversation,provider='fixture',mode='plan',content='Plan repair',request_id='plan')
        runtime.generate(self.core,'owner',turn)
        spec = publish(self.core,'owner',self.project,turn,0,'spec')
        with self.assertRaises(Conflict): self.create(specification=spec['id'],files=['feature.py','tests/test_app.py'],skills=[])
        approve(self.core,'owner',spec['id'],spec['sha256'])
        proposal = self.create(specification=spec['id'],files=['feature.py','tests/test_app.py'],skills=[])
        result = self.runtime.generate(self.core,'owner',proposal)
        self.assertEqual('ready',result['state'])
        self.assertEqual(spec['sha256'],self.provider.context['specification']['sha256'])
        newer = publish(self.core,'owner',self.project,turn,1,'spec-next')
        approve(self.core,'owner',newer['id'],newer['sha256'])
        with self.assertRaises(Conflict): self.runtime.accept(self.core,'owner',proposal)
        with self.assertRaises(Conflict): self.runtime.generate(self.core,'owner',proposal)
        self.assertEqual(0,self.core.db.execute('SELECT COUNT(*) FROM coding_runs').fetchone()[0])

    def creation_workspace(self):
        (self.source/'tests/test_app.py').write_text('import sys,unittest\nfrom pathlib import Path\nsys.path.insert(0,str(Path(__file__).resolve().parents[1]))\nfrom feature import answer\nclass TestFeature(unittest.TestCase):\n    def test_answer(self):self.assertEqual(42,answer())\n',encoding='utf-8')
        self.workspace=Workspace.snapshot(self.source,self.root/'creation',['tests/test_app.py'],['feature.py'])
        self.worker=FileWorker({(self.project,self.resource):self.workspace},self.root/'creation-evidence',self.worker.sandbox)
        self.runtime=RepairRuntime(self.worker,{'fixture':self.provider})
        self.provider.response=json.dumps({'summary':'Create the reviewed module.','patches':[{'path':'feature.py','expected_sha256':'absent','old':'','new':'def answer():\n    return 42\n'}]})

    def test_model_new_file_runs_real_missing_module_baseline_and_protected_test(self):
        self.creation_workspace()
        proposal=self.create(files=['feature.py','tests/test_app.py'],skills=[])
        data=self.runtime.generate(self.core,'owner',proposal)
        self.assertEqual('ready',data['state'])
        self.assertFalse((self.workspace.root/'feature.py').exists())
        run=self.runtime.accept(self.core,'owner',proposal)['run']
        self.assertEqual('create',self.runtime.workflow.get(self.core,'owner',run)['steps'][1]['payload']['operation'])
        self.assertEqual(run,self.runtime.accept(self.core,'owner',proposal)['run'])
        for _ in range(4): result=self.runtime.workflow.advance(self.core,'owner',run)
        self.assertEqual('ready_for_review',result['state'],result)
        baseline=self.worker.evidence(result['results'][0]['evidence'][0])['result']
        self.assertIn('ModuleNotFoundError',baseline['output'])
        self.assertEqual('absent',self.workspace.diff()['changes'][0]['before_sha256'])
        self.assertFalse((self.source/'feature.py').exists())
        self.assertEqual(1,self.provider.calls)
        self.assertEqual(run,self.runtime.workflow.create(self.core,'owner',self.project,self.resource,'unit',data['response']['patches'],'proposal:'+proposal))

    def test_new_file_proposal_rejects_unselected_paths_and_stale_absence(self):
        self.creation_workspace()
        proposal=self.create(files=['feature.py','tests/test_app.py'],skills=[])
        self.workspace.create('feature.py','owner_written = True\n')
        with self.assertRaises(Conflict):self.runtime.generate(self.core,'owner',proposal)
        self.assertEqual(0,self.provider.calls)
        self.assertEqual('owner_written = True\n',self.workspace.read('feature.py')['content'])

    def test_new_file_response_cannot_replace_unselected_or_protected_files(self):
        self.creation_workspace()
        proposal=self.create(files=['feature.py','tests/test_app.py'],skills=[])
        self.provider.response=json.dumps({'summary':'Invalid target','patches':[{'path':'unselected.py','expected_sha256':'absent','old':'','new':'bad'}]})
        self.assertEqual('failed',self.runtime.generate(self.core,'owner',proposal)['state'])
        self.assertFalse((self.workspace.root/'unselected.py').exists())

    def test_real_repair_from_proposal_to_review(self):
        data = self.generate()
        self.assertEqual('ready', data['state'])
        self.assertIn('41', self.workspace.read('app.py')['content'])
        data = self.runtime.accept(self.core, 'owner', data['id'])
        self.assertEqual('accepted', data['state'])
        self.assertEqual(data['run'], self.runtime.accept(self.core, 'owner', data['id'])['run'])
        self.core.close()
        self.core = Core(self.database)
        for _ in range(4):
            run = self.runtime.workflow.advance(self.core, 'owner', data['run'])
        self.assertEqual('ready_for_review', run['state'], run)
        self.assertEqual(['failed', 'succeeded', 'succeeded', 'succeeded'], [r['state'] for r in run['results']])
        self.assertIn('return 41', (self.source / 'app.py').read_text())
        self.assertEqual(1, self.provider.calls)

    def test_request_id_is_durable_and_conflicts(self):
        proposal = self.create()
        self.assertEqual(proposal, self.create())
        with self.assertRaises(Conflict): self.create(goal='Changed request')
        self.assertEqual(0, self.provider.calls)

    def test_only_selected_context_and_versioned_skills(self):
        self.generate()
        self.assertEqual(['app.py', 'tests/test_app.py'], [r['path'] for r in self.provider.context['files']])
        self.assertTrue(self.provider.context['files'][1]['protected'])
        self.assertEqual('1', self.provider.context['skills'][0]['version'])
        self.assertEqual(64, len(self.provider.context['skills'][0]['sha256']))

    def test_invalid_model_outputs_never_create_run_or_modify_files(self):
        record = self.workspace.read('app.py')
        good = {'path': 'app.py', 'expected_sha256': record['sha256'], 'old': '41', 'new': '42'}
        bad = ['{"summary":"a","summary":"b","patches":[]}', 'not json',
               json.dumps({'summary': 'No repair', 'patches': []})]
        for key, value in [('path', '../outside.py'), ('path', 'tests/test_app.py'),
                           ('expected_sha256', '0' * 64), ('old', 'missing'), ('new', '41')]:
            bad.append(json.dumps({'summary': 'Bad repair', 'patches': [{**good, key: value}]}))
        bad.append(json.dumps({'summary': 'Duplicate', 'patches': [good, good]}))
        bad.append(json.dumps({'summary': 'Extra field', 'patches': [good], 'command': 'anything'}))
        for index, text in enumerate(bad):
            with self.subTest(index=index):
                self.provider.response = text
                proposal = self.create(request_id=str(index))
                data = self.runtime.generate(self.core, 'owner', proposal)
                self.assertEqual('failed', data['state'])
                self.assertIsNone(data['response'])
        self.assertEqual(0, self.core.db.execute('SELECT count(*) FROM coding_runs').fetchone()[0])
        self.assertEqual(record, self.workspace.read('app.py'))

    def test_host_bound_edits_preserve_crlf_and_bind_original_hash(self):
        proposal=self.create(edit_protocol='host-bound-v2')
        original=self.workspace.read('app.py')
        self.assertIn('\r\n',original['content'])
        self.provider.response=json.dumps({'summary':'Correct answer','patches':[{
            'path':'app.py','old':original['content'].replace('\r\n','\n'),
            'new':original['content'].replace('\r\n','\n').replace('41','42')}]})
        data=self.runtime.generate(self.core,'owner',proposal)
        self.assertEqual('ready',data['state'],data)
        patch=data['response']['patches'][0]
        self.assertEqual(original['sha256'],patch['expected_sha256'])
        self.assertEqual(original['content'],patch['old'])
        self.assertIn('\r\n',patch['new'])
        self.core.close();self.core=Core(self.database)
        run=self.runtime.accept(self.core,'owner',proposal)['run']
        for _ in range(4):result=self.runtime.workflow.advance(self.core,'owner',run)
        self.assertEqual('ready_for_review',result['state'],result)
        self.assertEqual(original['content'].replace('41','42'),self.workspace.read('app.py')['content'])
        self.assertEqual(1,self.provider.calls)

    def test_host_bound_creation_uses_absence_without_model_hash(self):
        self.creation_workspace()
        proposal=self.create(files=['feature.py','tests/test_app.py'],skills=[],edit_protocol='host-bound-v2')
        self.provider.response=json.dumps({'summary':'Implement module','patches':[{
            'path':'feature.py','old':'','new':'def answer():\n    return 42\n'}]})
        data=self.runtime.generate(self.core,'owner',proposal)
        self.assertEqual('ready',data['state'],data)
        self.assertEqual('absent',data['response']['patches'][0]['expected_sha256'])
        self.assertFalse((self.workspace.root/'feature.py').exists())

    def test_host_bound_large_creation_stays_reviewable_and_oversized_text_is_rejected(self):
        self.creation_workspace()
        content = 'def answer():\n    return 42\n#' + 'x' * 32000
        proposal=self.create(files=['feature.py','tests/test_app.py'],skills=[],edit_protocol='host-bound-v2')
        self.provider.response=json.dumps({'summary':'Implement selected module','patches':[
            {'path':'feature.py','old':'','new':content}]})
        data=self.runtime.generate(self.core,'owner',proposal)
        self.assertEqual('ready',data['state'],data)
        self.assertEqual(content,data['response']['patches'][0]['new'])
        self.assertFalse((self.workspace.root/'feature.py').exists())
        proposal=self.create(files=['feature.py','tests/test_app.py'],skills=[],edit_protocol='host-bound-v2',request_id='too-large-text')
        self.provider.response=json.dumps({'summary':'Too large','patches':[{'path':'feature.py','old':'','new':'x'*48001}]})
        data=self.runtime.generate(self.core,'owner',proposal)
        self.assertEqual('patch_text_bounds',data['validation_failure'])
        self.assertFalse((self.workspace.root/'feature.py').exists())

    def test_host_bound_disjoint_edits_combine_against_original_and_execute_atomically(self):
        proposal = self.create(edit_protocol='host-bound-v2')
        original = self.workspace.read('app.py')
        self.provider.response = json.dumps({'summary': 'Correct result and document function', 'patches': [
            {'path': 'app.py', 'old': 'return 41', 'new': 'return 42'},
            {'path': 'app.py', 'old': 'def answer():', 'new': 'def answer(): # corrected'}]})
        data = self.runtime.generate(self.core, 'owner', proposal)
        self.assertEqual('ready', data['state'], data)
        self.assertEqual(1, len(data['response']['patches']))
        merged = data['response']['patches'][0]
        self.assertEqual(original['sha256'], merged['expected_sha256'])
        self.assertIn('\r\n', merged['old'])
        self.assertEqual(original, self.workspace.read('app.py'))
        self.core.close(); self.core = Core(self.database)
        run = self.runtime.accept(self.core, 'owner', proposal)['run']
        for _ in range(4): result = self.runtime.workflow.advance(self.core, 'owner', run)
        self.assertEqual('ready_for_review', result['state'], result)
        self.assertEqual(original['content'].replace('return 41', 'return 42').replace('def answer():', 'def answer(): # corrected'),
                         self.workspace.read('app.py')['content'])

    def test_host_bound_rejects_overlapping_and_dependent_multi_edits(self):
        cases = [
            ([{'path':'app.py','old':'return 41','new':'return 42'},
              {'path':'app.py','old':'41','new':'43'}], 'patch_overlap'),
            ([{'path':'app.py','old':'41','new':'42'},
              {'path':'app.py','old':'42','new':'43'}], 'patch_old_text_mismatch'),
        ]
        for index, (patches, code) in enumerate(cases):
            proposal = self.create(edit_protocol='host-bound-v2', request_id='multi-reject-'+str(index))
            self.provider.response = json.dumps({'summary':'Invalid edits','patches':patches})
            data = self.runtime.generate(self.core, 'owner', proposal)
            self.assertEqual('failed', data['state'], data)
            self.assertEqual(code, data['validation_failure'])
            self.assertIsNone(data['run'])
        self.assertIn('41', self.workspace.read('app.py')['content'])

    def test_host_bound_multi_edit_cannot_duplicate_creation_or_expand_patch_size_limit(self):
        original = self.workspace.read('app.py')
        large = '# first\n' + '# gap\n' * 9000 + original['content']
        self.workspace.patch('app.py', original['sha256'], original['content'], large)
        before = self.workspace.read('app.py')
        proposal = self.create(edit_protocol='host-bound-v2')
        self.provider.response = json.dumps({'summary':'Oversized combined patch','patches':[
            {'path':'app.py','old':'# first','new':'# start'},
            {'path':'app.py','old':'41','new':'42'}]})
        data = self.runtime.generate(self.core,'owner',proposal)
        self.assertEqual('patch_combined_text_bounds',data['validation_failure'])
        self.assertEqual(before,self.workspace.read('app.py'))
        self.creation_workspace()
        proposal = self.create(files=['feature.py','tests/test_app.py'],skills=[],
                               edit_protocol='host-bound-v2',request_id='duplicate-creation')
        self.provider.response = json.dumps({'summary':'Duplicate creation','patches':[
            {'path':'feature.py','old':'','new':'def answer(): return 42\n'},
            {'path':'feature.py','old':'','new':'def other(): return 1\n'}]})
        data = self.runtime.generate(self.core,'owner',proposal)
        self.assertEqual('patch_duplicate_path',data['validation_failure'])
        self.assertFalse((self.workspace.root/'feature.py').exists())

    def test_explicit_thinking_is_request_bound_and_fresh_at_review(self):
        self.provider.thinking_level='high'
        proposal=self.create()
        self.assertEqual({'thinking_level':'high'},self.runtime.get(self.core,'owner',proposal)['context']['generation'])
        self.provider.thinking_level='medium'
        with self.assertRaises(Conflict):self.create()
        with self.assertRaises(Conflict):self.runtime.generate(self.core,'owner',proposal)
        self.assertEqual(0,self.provider.calls)
        self.provider.thinking_level='high'
        self.assertEqual('ready',self.runtime.generate(self.core,'owner',proposal)['state'])
        self.provider.thinking_level=None
        with self.assertRaises(Conflict):self.runtime.accept(self.core,'owner',proposal)
        self.assertEqual(1,self.provider.calls)

    def test_client_guidance_selection_is_exact_and_request_bound(self):
        expected={'repair':self.runtime.skills['repair'].record()['sha256']}
        proposal=self.create(expected_skills=expected)
        self.assertEqual(expected['repair'],self.runtime.get(self.core,'owner',proposal)['context']['skills'][0]['sha256'])
        with self.assertRaises(Conflict):self.create(expected_skills=None)
        with self.assertRaises(Conflict):self.create(request_id='wrong-revision',expected_skills={'repair':'0'*64})
        with self.assertRaises(ValueError):self.create(request_id='missing-pin',expected_skills={})
        self.assertEqual(0,self.provider.calls)

    def test_unchanged_patch_reports_no_change_without_creating_a_run(self):
        proposal=self.create(edit_protocol='host-bound-v2')
        self.provider.response=json.dumps({'summary':'No actual correction','patches':[{'path':'app.py','old':'41','new':'41'}]})
        result=self.runtime.generate(self.core,'owner',proposal)
        self.assertEqual('patch_no_change',result['validation_failure'])
        self.assertIsNone(result['run'])
        self.assertIn('41',self.workspace.read('app.py')['content'])

    def test_host_bound_rejects_extra_hash_and_reports_safe_validation_detail(self):
        proposal=self.create(edit_protocol='host-bound-v2')
        data=self.runtime.generate(self.core,'owner',proposal)
        self.assertEqual('invalid_model_response',data['error'])
        self.assertEqual('patch_shape',data['validation_failure'])
        self.core.close();self.core=Core(self.database)
        self.assertEqual('patch_shape',self.runtime.get(self.core,'owner',proposal)['validation_failure'])
        self.assertIsNone(data['response'])

    def test_host_bound_contract_and_stale_source_block_before_call(self):
        proposal=self.create(edit_protocol='host-bound-v2')
        with self.assertRaises(Conflict):self.create(edit_protocol='legacy-v1')
        with patch('jarvis_runtime.runtime.HOST_BOUND_SCHEMA',{}):
            with self.assertRaises(Conflict):self.runtime.generate(self.core,'owner',proposal)
        with patch('jarvis_runtime.runtime.SYSTEM','Changed'):
            with self.assertRaises(Conflict):self.runtime.generate(self.core,'owner',proposal)
        self.workspace.patch('app.py',self.workspace.read('app.py')['sha256'],'41','40')
        with self.assertRaises(Conflict):self.runtime.generate(self.core,'owner',proposal)
        self.assertEqual(0,self.provider.calls)

    def test_newline_canonicalization_is_conservative_for_mixed_files(self):
        from skyra_coding.workspace import canonical_edit
        self.assertEqual(('x\r\ny','z\r\nw'),canonical_edit('a\r\nb\r\n','x\ny','z\nw'))
        self.assertEqual(('x\ny','z\nw'),canonical_edit('a\nb\n','x\r\ny','z\r\nw'))
        self.assertEqual(('x\ny','z\nw'),canonical_edit('a\r\nb\n','x\ny','z\nw'))
        self.assertEqual(('x','y'),canonical_edit('single line','x','y'))

    def test_stale_context_rejected_before_call_and_accept(self):
        data = self.generate()
        self.workspace.patch('app.py', self.workspace.read('app.py')['sha256'], '41', '40')
        with self.assertRaises(Conflict): self.runtime.accept(self.core, 'owner', data['id'])
        with self.assertRaises(Conflict): self.runtime.generate(self.core, 'owner', data['id'])
        self.assertEqual(1, self.provider.calls)

    def test_policy_revocation_prevents_export_and_accept(self):
        proposal = self.create()
        self.core.set_policy('owner', self.project, 'read_only', [])
        with self.assertRaises(Denied): self.runtime.generate(self.core, 'owner', proposal)
        self.assertEqual(0, self.provider.calls)

    def test_generation_is_not_replayed_after_restart(self):
        proposal = self.create()
        self.core.db.execute("UPDATE repair_proposals SET state='generating' WHERE id=?", (proposal,))
        self.core.close()
        self.core = Core(self.database)
        self.assertEqual('generating', self.runtime.generate(self.core, 'owner', proposal)['state'])
        self.assertEqual(0, self.provider.calls)
        self.assertEqual('interrupted', self.runtime.interrupt(self.core, 'owner', proposal)['state'])

    def test_registered_toolchain_change_blocks_provider_dispatch(self):
        proposal=self.create()
        self.worker.toolchain_bindings[(self.project,'workspace:fixture')]={sys.executable:'0'*64}
        with self.assertRaises(Conflict):self.runtime.generate(self.core,'owner',proposal)
        self.assertEqual(0,self.provider.calls)
        self.assertEqual('planned',self.runtime.get(self.core,'owner',proposal)['state'])

    def test_late_response_cannot_revive_interrupted_request(self):
        proposal = self.create()
        self.provider.callback = lambda: self.runtime.interrupt(self.core, 'owner', proposal)
        self.assertEqual('interrupted', self.runtime.generate(self.core, 'owner', proposal)['state'])
        self.assertIsNone(self.runtime.get(self.core, 'owner', proposal)['response'])

    def test_output_limit_keeps_reported_usage_without_response_or_replay(self):
        from jarvis_runtime.responses import IncompleteResponse
        proposal=self.create()
        def fail(): raise IncompleteResponse(output_limited=True,usage={'total_tokens':99})
        self.provider.callback=fail
        result=self.runtime.generate(self.core,'owner',proposal)
        self.assertEqual('provider_output_limit',result['error'])
        self.assertEqual({'total_tokens':99},result['usage'])
        self.assertIsNone(result['response']);self.assertIsNone(result['validation_failure'])
        self.core.close();self.core=Core(self.database)
        self.assertEqual('failed',self.runtime.generate(self.core,'owner',proposal)['state'])
        self.assertEqual(1,self.provider.calls)
        self.assertEqual([],self.workspace.diff()['changes'])

    def test_provider_error_details_are_not_stored(self):
        def fail(): raise RuntimeError('SECRET_API_KEY_AND_PROMPT')
        self.provider.callback = fail
        data = self.generate()
        self.assertEqual('failed', data['state'])
        self.assertNotIn('SECRET', json.dumps(data))
        self.assertEqual('generation_failed', data['error'])

    def test_context_size_limit_and_unselected_files(self):
        with self.assertRaises(ValueError): self.create(files=['unknown.py'])
        with self.assertRaises(ValueError): self.create(skills=['unknown'])
        (self.workspace.root / 'app.py').write_text('x' * 128001)
        with self.assertRaises(ValueError): self.create()
        self.assertEqual(0, self.provider.calls)

    def test_accept_is_atomic_with_run_creation(self):
        data = self.generate()
        original = self.core._event
        def fail(project, kind, subject):
            if kind == 'repair_proposal.accepted': raise RuntimeError('Injected failure')
            return original(project, kind, subject)
        with patch.object(self.core, '_event', fail):
            with self.assertRaises(RuntimeError): self.runtime.accept(self.core, 'owner', data['id'])
        self.assertEqual(0, self.core.db.execute('SELECT count(*) FROM coding_runs').fetchone()[0])
        self.assertEqual('ready', self.runtime.get(self.core, 'owner', data['id'])['state'])

    def test_review_does_not_bypass_ask_mode(self):
        self.core.set_policy('owner', self.project, 'ask', [self.resource])
        data = self.generate()
        accepted = self.runtime.accept(self.core, 'owner', data['id'])
        run = self.runtime.workflow.advance(self.core, 'owner', accepted['run'])
        self.assertEqual('waiting_approval', run['state'])
        self.assertIn('return 41', self.workspace.read('app.py')['content'])

    def test_profile_changes_invalidate_review(self):
        data = self.generate()
        old = self.worker.sandbox.profiles['unit']
        self.worker.sandbox.profiles['unit'] = NativeProfile('unit', old.argv, old.protected_paths, 11)
        with self.assertRaises(Conflict): self.runtime.accept(self.core, 'owner', data['id'])

    def test_changed_context_during_call_is_rejected_and_usage_retained(self):
        self.provider.callback = lambda: self.workspace.patch('app.py', self.workspace.read('app.py')['sha256'], '41', '40')
        data = self.generate()
        self.assertEqual('failed', data['state'])
        self.assertEqual('context_changed', data['error'])
        self.assertEqual({'total_tokens': 30}, data['usage'])

    def test_concurrent_generation_dispatches_once(self):
        proposal = self.create()
        entered, release = threading.Event(), threading.Event()
        def hold():
            entered.set()
            if not release.wait(5): raise RuntimeError('Test timed out')
        self.provider.callback = hold
        results = []
        def generate():
            c = Core(self.database)
            try: results.append(self.runtime.generate(c, 'owner', proposal))
            finally: c.close()
        thread = threading.Thread(target=generate)
        thread.start()
        try:
            self.assertTrue(entered.wait(5))
            self.assertEqual('generating', self.runtime.generate(self.core, 'owner', proposal)['state'])
        finally:
            release.set()
            thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(1, self.provider.calls)
        self.assertEqual('ready', results[0]['state'])

    def test_v5_migration_preserves_conversations(self):
        conversation = self.core.create_conversation('owner', self.project)
        self.core.append_message('owner', conversation, 'user', 'Keep this message', 'message-1')
        self.core.db.execute('DROP TABLE repair_proposals')
        self.core.db.execute('DROP TABLE project_specs')
        self.core.db.execute('DROP TABLE model_turns')
        self.core.db.execute('DROP TABLE assignment_attempts')
        self.core.db.execute('DROP TABLE assignments')
        self.core.db.execute('DROP TABLE runner_contacts')
        self.core.db.execute('DROP TABLE operation_notices')
        self.core.db.execute('DROP TABLE scaffold_registrations')
        self.core.db.execute('DROP TABLE build_attempts')
        self.core.db.execute('DROP TABLE build_cycles')
        self.core.db.execute('DROP TABLE build_jobs')
        self.core.db.execute('PRAGMA user_version=5')
        self.core.close()
        self.core = Core(self.database)
        self.assertEqual(15, self.core.db.execute('PRAGMA user_version').fetchone()[0])
        self.assertEqual('Keep this message', self.core.messages('owner', conversation)[0]['content'])
        self.assertEqual('planned', self.runtime.get(self.core, 'owner', self.create())['state'])

    def test_http_roles_and_controller_review(self):
        tokens = {role: secrets.token_urlsafe(32) for role in ('controller', 'agent', 'worker')}
        credentials = [Credential(hashlib.sha256(token.encode()).hexdigest(), 'owner', role,
                                  frozenset({self.project}) if role != 'controller' else frozenset())
                       for role, token in tokens.items()]
        app = create_app(self.database, credentials, self.worker, self.runtime)
        with TestClient(app, base_url='http://127.0.0.1', client=('127.0.0.1', 50000)) as client:
            def call(method, path, role='controller', **kwargs):
                return client.request(method, path, headers={'Authorization': 'Bearer ' + tokens[role]}, **kwargs)
            body = dict(resource=self.resource, profile='unit', provider='fixture', goal='Fix answer',
                        files=['app.py', 'tests/test_app.py'], skills=['repair'], request_id='http-1')
            url = f'/v1/projects/{self.project}/repair-proposals'
            self.assertEqual(403, call('POST', url, 'agent', json=body).status_code)
            response = call('POST', url, json=body)
            self.assertEqual(201, response.status_code, response.text)
            proposal = response.json()['proposal_id']
            base = '/v1/repair-proposals/' + proposal
            self.assertEqual(403, call('POST', base + '/generate', 'agent').status_code)
            self.assertEqual('ready', call('POST', base + '/generate').json()['state'])
            self.assertEqual(200, call('GET', base, 'agent').status_code)
            self.assertEqual(403, call('GET', base, 'worker').status_code)
            self.assertEqual(403, call('POST', base + '/accept', 'agent').status_code)
            self.assertEqual('accepted', call('POST', base + '/accept').json()['state'])

    def test_http_host_bound_proposal_checks_selected_guidance_before_generation(self):
        token=secrets.token_urlsafe(32)
        credential=Credential(hashlib.sha256(token.encode()).hexdigest(),'owner','controller',frozenset())
        with TestClient(create_app(self.database,[credential],self.worker,self.runtime),base_url='http://127.0.0.1',client=('127.0.0.1',50000)) as client:
            headers={'Authorization':'Bearer '+token};url=f'/v1/projects/{self.project}/repair-proposals'
            body=dict(resource=self.resource,profile='unit',provider='fixture',goal='Fix answer',files=['app.py','tests/test_app.py'],
                      skills=['repair'],expected_skills={'repair':'0'*64},edit_protocol='host-bound-v2',request_id='pinned-http')
            self.assertEqual(409,client.post(url,headers=headers,json=body).status_code)
            self.assertEqual(0,self.provider.calls)
            body['expected_skills']={'repair':self.runtime.skills['repair'].record()['sha256']}
            response=client.post(url,headers=headers,json=body)
            self.assertEqual(201,response.status_code,response.text)
            self.provider.response=json.dumps({'summary':'Correct answer','patches':[{'path':'app.py','old':'41','new':'42'}]})
            result=client.post('/v1/repair-proposals/'+response.json()['proposal_id']+'/generate',headers=headers).json()
            self.assertEqual('ready',result['state'],result)
            self.assertEqual(self.workspace.read('app.py')['sha256'],result['response']['patches'][0]['expected_sha256'])


class ProviderTests(unittest.TestCase):
    def test_transport_failures_have_safe_typed_codes_without_private_text(self):
        import httpx
        from jarvis_runtime.responses import failure_code
        for error,expected in [(TimeoutError('private prompt'),'provider_timeout'),
                (ConnectionError('private key'),'provider_connection_failed'),
                (httpx.ReadTimeout('private request'),'provider_timeout'),
                (httpx.ConnectError('private endpoint'),'provider_connection_failed')]:
            self.assertEqual(expected,failure_code(error,'generation_failed',provider_failure=True))
        self.assertEqual('generation_failed',failure_code(RuntimeError('private'),'generation_failed',provider_failure=True))

    def test_explicit_gemini_output_budget_is_bounded_and_groq_limit_unchanged(self):
        self.assertEqual(32768, OnlineProvider('gemini','fixture','fixture',max_output_tokens=32768).max_output_tokens)
        for provider, budget in [('gemini',32769),('gemini',True),('groq',8193)]:
            with self.assertRaises(ValueError): OnlineProvider(provider,'fixture','fixture',max_output_tokens=budget)

    def test_incomplete_provider_outputs_preserve_only_valid_counts_and_safe_reason(self):
        from types import SimpleNamespace
        from jarvis_runtime.responses import IncompleteResponse, failure_code, failure_usage
        for provider,limit,other in [('gemini','MAX_TOKENS','SECRET_UNKNOWN_REASON'),('groq','length','SECRET_UNKNOWN_REASON')]:
            target='google.genai.Client' if provider=='gemini' else 'groq.Groq'
            with patch(target) as factory:
                client=factory.return_value.__enter__.return_value
                for finish,expected in [(limit,'provider_output_limit'),(other,'provider_incomplete_response')]:
                    if provider=='gemini':
                        response=SimpleNamespace(candidates=[SimpleNamespace(finish_reason=finish)],
                            usage_metadata=SimpleNamespace(prompt_token_count=10,candidates_token_count=2,total_token_count=12))
                        client.models.generate_content.return_value=response
                    else:
                        response=SimpleNamespace(choices=[SimpleNamespace(finish_reason=finish)],
                            usage=SimpleNamespace(prompt_tokens=10,completion_tokens=2,total_tokens=12))
                        client.chat.completions.create.return_value=response
                    with self.assertRaises(IncompleteResponse) as caught:
                        OnlineProvider(provider,'fixture','fixture').complete('system','{}',{})
                    self.assertEqual(expected,failure_code(caught.exception,'fallback',provider_failure=True))
                    self.assertEqual({'input_tokens':10,'output_tokens':2,'total_tokens':12},failure_usage(caught.exception))
                    self.assertNotIn('SECRET',str(caught.exception))
                self.assertEqual(2,(client.models.generate_content if provider=='gemini' else client.chat.completions.create).call_count)
        for usage in ({'total_tokens':True},{'total_tokens':-1},{'private':'secret'},'secret'):
            self.assertIsNone(failure_usage(IncompleteResponse(usage=usage)))
        self.assertIsNone(failure_usage(ValueError('private response')))

    def test_thinking_configuration_is_explicit_and_provider_specific(self):
        fields={'name':'coding','provider':'gemini','model':'gemini-3.5-flash-lite','api_key_env':'TEST_JARVIS_KEY','timeout':90,'max_output_tokens':8192}
        with patch.dict('os.environ',{'TEST_JARVIS_KEY':'fixture'}):
            self.assertIsNone(load_providers([fields])['coding'].thinking_level)
            self.assertEqual('high',load_providers([{**fields,'thinking_level':'high'}])['coding'].thinking_level)
        for provider,model,level in [('groq','qwen/qwen3.8-27b','high'),('gemini','gemini-2.5-flash','high'),('gemini','gemini-3.5-flash-lite',[]),('gemini','gemini-3.5-flash-lite','unbounded')]:
            with self.assertRaises(ValueError):OnlineProvider(provider,model,'fixture',thinking_level=level)

    def test_gemini_thinking_keeps_thoughts_private_and_reports_counts(self):
        from types import SimpleNamespace
        with patch('google.genai.Client') as factory:
            client=factory.return_value.__enter__.return_value
            client.models.generate_content.return_value=SimpleNamespace(text='{}',candidates=[SimpleNamespace(finish_reason='STOP')],
                usage_metadata=SimpleNamespace(prompt_token_count=10,candidates_token_count=5,total_token_count=35,thoughts_token_count=20))
            text,usage=OnlineProvider('gemini','gemini-3.5-flash-lite','fixture',thinking_level='high').complete('system','{}',{})
            cfg=client.models.generate_content.call_args.kwargs['config']
            self.assertEqual('HIGH',cfg.thinking_config.thinking_level.value)
            self.assertIs(cfg.thinking_config.include_thoughts,False)
            self.assertEqual(20,usage['reasoning_tokens']);self.assertEqual('{}',text)
            self.assertEqual(1,factory.call_args.kwargs['http_options'].retry_options.attempts)
    def test_environment_config_never_accepts_inline_secrets(self):
        with self.assertRaises(ValueError): load_providers([{'api_key': 'secret'}])
        with self.assertRaises(ValueError): OnlineProvider('unknown', 'model', 'secret')

    def test_groq_disables_retry_and_uses_no_tools(self):
        with patch('groq.Groq') as factory:
            client = factory.return_value.__enter__.return_value
            response = MagicMock()
            response.choices = [MagicMock(finish_reason='stop', message=MagicMock(content='{}'))]
            response.usage = None
            client.chat.completions.create.return_value = response
            self.assertEqual(('{}', {}), OnlineProvider('groq', 'llama-3.3-70b-versatile', 'fixture-key').complete('system', '{}', {}))
            self.assertEqual(0, factory.call_args.kwargs['max_retries'])
            self.assertNotIn('tools', client.chat.completions.create.call_args.kwargs)
            request = client.chat.completions.create.call_args.kwargs
            self.assertEqual(0, request['temperature'])
            self.assertEqual('system\nRequired output JSON Schema:\n{}', request['messages'][0]['content'])
            self.assertEqual('{}', request['messages'][1]['content'])

    def test_gemini_disables_retry_and_validates_completion(self):
        with patch('google.genai.Client') as factory:
            client = factory.return_value.__enter__.return_value
            response = MagicMock(text='{}', usage_metadata=None)
            response.candidates = [MagicMock(finish_reason='STOP')]
            client.models.generate_content.return_value = response
            self.assertEqual(('{}', {}), OnlineProvider('gemini', 'fixture-model', 'fixture-key').complete('system', '{}', {}))
            self.assertEqual(1, factory.call_args.kwargs['http_options'].retry_options.attempts)
            response.candidates[0].finish_reason = 'MAX_TOKENS'
            with self.assertRaises(ValueError):
                OnlineProvider('gemini', 'fixture-model', 'fixture-key').complete('system', '{}', {})


if __name__ == '__main__': unittest.main()
