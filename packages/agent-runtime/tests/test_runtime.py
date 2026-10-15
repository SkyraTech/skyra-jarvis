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

    def test_late_response_cannot_revive_interrupted_request(self):
        proposal = self.create()
        self.provider.callback = lambda: self.runtime.interrupt(self.core, 'owner', proposal)
        self.assertEqual('interrupted', self.runtime.generate(self.core, 'owner', proposal)['state'])
        self.assertIsNone(self.runtime.get(self.core, 'owner', proposal)['response'])

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
        (self.workspace.root / 'app.py').write_text('x' * 96001)
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
        self.core.db.execute('DROP TABLE scaffold_registrations')
        self.core.db.execute('DROP TABLE build_attempts')
        self.core.db.execute('DROP TABLE build_cycles')
        self.core.db.execute('DROP TABLE build_jobs')
        self.core.db.execute('PRAGMA user_version=5')
        self.core.close()
        self.core = Core(self.database)
        self.assertEqual(12, self.core.db.execute('PRAGMA user_version').fetchone()[0])
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


class ProviderTests(unittest.TestCase):
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
