"""Complete new-project flow: real HTTP, durable scope, repair cycles and delivery."""
import json
import os
from pathlib import Path
import unittest
import hashlib

import test_scaffold
from jarvis_core import Core, Conflict, Denied
from jarvis_core.api import Credential, create_app
from fastapi.testclient import TestClient
from jarvis_core import specifications
from jarvis_core.build_jobs import BuildJobs
from jarvis_runtime import RepairRuntime
from skyra_coding import FileWorker, Workspace
from skyra_coding.registry import ScaffoldRegistry
from skyra_coding.scaffold import checksum, materialize, preview
from skyra_coding.templates import WEB_TEMPLATE


HTML = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Client site</title></head><body><main><h1>Site ready</h1></main></body></html>\n'
APP = '''from pathlib import Path
def handle(value):
    if value["method"] == "GET" and value["path"] == "/":
        return {"status":200,"content_type":"text/html; charset=utf-8","body":Path("index.html").read_text(encoding="utf-8")}
    if value["method"] == "GET" and value["path"] == "/health":
        return {"status":200,"content_type":"application/json","body":'{"status":"ok"}'}
    return {"status":200,"content_type":"text/plain; charset=utf-8","body":value["body"]}
'''


class WebProvider:
    provider = 'fixture'; model = 'web-fixture'; timeout = 1; max_output_tokens = 4096
    def __init__(self): self.calls = 0
    def complete(self, system, context, schema):
        self.calls += 1
        records = {item['path']: item for item in json.loads(context)['files']}
        replacements = {'index.html': 'Wrong first attempt\n' if self.calls == 1 else HTML}
        if self.calls == 1: replacements['app.py'] = APP
        patches = [{'path': path, 'expected_sha256': records[path]['sha256'],
                    'old': records[path]['content'], 'new': text} for path, text in replacements.items()]
        return json.dumps({'summary': 'Implement reviewed local website and API', 'patches': patches}), {'total_tokens': 300}


@unittest.skipUnless(os.name == 'nt', 'Windows trusted project execution')
class RegistryTests(unittest.TestCase):
    setUp = test_scaffold.ScaffoldTests.setUp

    def prepare(self, web=False):
        args = dict(self.args)
        if web:
            docs = {**self.documents, '01_PRODUCT_REQUIREMENTS.md': '# Website\n\nServe the reviewed HTML home page, a health endpoint and POST echo.\n'}
            revised = specifications.revise(self.core, 'owner', self.spec, docs, self.spec_hash, 1, 'website')
            specifications.approve(self.core, 'owner', revised['id'], revised['sha256'])
            self.spec = revised['id']; self.spec_hash = revised['sha256']
            args.update(specification=self.spec, expected_sha256=self.spec_hash, template=WEB_TEMPLATE,
                        contract={'cases': [
                            {'name': 'home', 'input': {'method': 'GET', 'path': '/', 'body': ''},
                             'output': {'status': 200, 'content_type': 'text/html; charset=utf-8', 'body': HTML}},
                            {'name': 'health', 'input': {'method': 'GET', 'path': '/health', 'body': ''},
                             'output': {'status': 200, 'content_type': 'application/json', 'body': '{"status":"ok"}'}},
                            {'name': 'echo', 'input': {'method': 'POST', 'path': '/echo', 'body': 'Hello'},
                             'output': {'status': 200, 'content_type': 'text/plain; charset=utf-8', 'body': 'Hello'}},
                        ]})
        self.plan = preview(self.core, 'owner', **args)
        self.creation = materialize(self.core, 'owner', **args, expected_plan_sha256=checksum(self.plan))
        self.worker = FileWorker({}, self.root / 'evidence')
        self.registry = ScaffoldRegistry(self.worker, self.root, enabled=True)
        self.review = self.registry.preview(self.core, 'owner', self.spec, args['name'], checksum(self.plan))
        return args

    def register(self, **changes):
        args = dict(name=self.plan['name'], expected_plan_sha256=checksum(self.plan),
                    expected_registration_sha256=self.review['registration_sha256'], allow_native_execution=True)
        args.update(changes)
        return self.registry.register(self.core, 'owner', self.spec, **args)

    def deliver_change(self, config, content, request_id):
        from skyra_coding.workflow import CodingWorkflow
        self.core.set_policy('owner', self.project, 'full', [config['workspace'], config['source']])
        workspace = self.worker.workspaces[(self.project, config['workspace'])]
        current = workspace.read('app.py')
        workflow = CodingWorkflow(self.worker)
        run = workflow.create(self.core, 'owner', self.project, config['workspace'], config['profile']['name'],
                              [{'path': 'app.py', 'expected_sha256': current['sha256'],
                                'old': current['content'], 'new': content}], request_id, mode='feature')
        for _ in range(10):
            result = workflow.advance(self.core, 'owner', run)
            if result['state'] in {'ready_for_review', 'failed'}: break
        self.assertEqual('ready_for_review', result['state'], result)
        review = self.worker.delivery.preview(self.core, 'owner', run, config['source'])
        task = self.worker.delivery.prepare(self.core, 'owner', run, config['source'], review['sha256'], request_id)['id']
        lease = self.core.start('owner', task)
        self.worker.perform(self.core, 'owner', task, lease['lease_token'])
        self.assertEqual('succeeded', self.core.task('owner', task)['state'])
        return task, run

    def test_continuation_two_deliveries_restart_and_immutable_history(self):
        self.prepare(); initial = self.register()['registration']
        task, run = self.deliver_change(initial, 'def handle(value):\n    return value * 2\n', 'first')
        original = self.worker.workspaces[(self.project, initial['workspace'])]
        historical = original.diff()
        review = self.registry.continuation_preview(self.core, 'owner', task, 'client-second')
        args = dict(name='client-second', expected_registration_sha256=review['registration_sha256'], allow_native_execution=True)
        with self.assertRaises(Denied): self.registry.continue_project(self.core, 'owner', task, **{**args, 'allow_native_execution': False})
        with self.assertRaises(Conflict): self.registry.continue_project(self.core, 'owner', task, **{**args, 'expected_registration_sha256': '0'*64})
        policy_before = dict(self.core._owned('owner', self.project))
        created = self.registry.continue_project(self.core, 'owner', task, **args)
        self.assertTrue(created['active']); self.assertEqual(policy_before, dict(self.core._owned('owner', self.project)))
        self.assertEqual(created, self.registry.continue_project(self.core, 'owner', task, **args))
        config = created['registration']
        self.assertEqual([], self.worker.workspaces[(self.project, config['workspace'])].diff()['changes'])
        self.worker = FileWorker({}, self.worker.evidence_root)
        self.registry = ScaffoldRegistry(self.worker, self.root, enabled=True); self.registry.sync(self.core)
        self.assertEqual({}, self.registry.errors)
        self.assertEqual(2, len(self.worker.workspaces)); self.assertEqual(2, len(self.worker.delivery.targets))
        second, _ = self.deliver_change(config, 'def handle(value):\n    return value + value\n', 'second')
        self.assertEqual(historical, self.worker.workspaces[(self.project, initial['workspace'])].diff())
        self.assertIn('value + value', (Path(self.creation['directory'])/'source/app.py').read_text())
        third_review = self.registry.continuation_preview(self.core, 'owner', second, 'client-third')
        third = self.registry.continue_project(self.core, 'owner', second, 'client-third', third_review['registration_sha256'], True)
        self.assertTrue(third['active'])
        # An identical retry remains a status read even after later source changes.
        self.assertEqual(created, self.registry.continue_project(self.core, 'owner', task, **args))
        self.assertEqual('ready_for_review', self.core.db.execute('SELECT state FROM coding_runs WHERE id=?',(run,)).fetchone()[0])

    def test_continuation_source_drift_and_missing_grants_are_blocked(self):
        self.prepare(); config = self.register()['registration']
        task, _ = self.deliver_change(config, 'def handle(value):\n    return value * 2\n', 'first')
        review = self.registry.continuation_preview(self.core, 'owner', task, 'client-second')
        self.core.set_policy('owner', self.project, 'read_only', [])
        with self.assertRaises(Denied): self.registry.continuation_preview(self.core, 'owner', task, 'client-second')
        self.core.set_policy('owner', self.project, 'full', [config['workspace'], config['source']])
        (Path(self.creation['directory'])/'source/app.py').write_text('owner edit\n')
        with self.assertRaises(ValueError):
            self.registry.continue_project(self.core, 'owner', task, 'client-second', review['registration_sha256'], True)
        self.assertFalse((self.root/'client-second').exists())

    def test_continuation_http_roles_exact_review_and_restart_catalog(self):
        self.prepare(); config = self.register()['registration']
        task, _ = self.deliver_change(config, 'def handle(value):\n    return value * 2\n', 'http-first')
        tokens = {role: role.ljust(40, 'x') for role in ('controller', 'agent', 'worker')}
        credentials = [Credential(hashlib.sha256(token.encode()).hexdigest(), 'owner', role,
                                  frozenset() if role == 'controller' else frozenset({self.project}))
                       for role, token in tokens.items()]
        def client(worker):
            return TestClient(create_app(self.database, credentials, file_worker=worker,
                                        scaffold_root=self.root, scaffold_execution_enabled=True),
                              base_url='http://127.0.0.1', client=('127.0.0.1', 50000))
        def call(api, suffix, body, role='controller'):
            return api.post(f'/v1/deliveries/{task}/{suffix}', json=body,
                            headers={'Authorization': 'Bearer '+tokens[role]})
        with client(self.worker) as api:
            name = {'name':'http-next'}
            for role in ('agent', 'worker'):
                for suffix in ('continuation-preview', 'continuation-status'):
                    self.assertEqual(403, call(api, suffix, name, role).status_code)
            preview = call(api, 'continuation-preview', name)
            self.assertEqual(200, preview.status_code, preview.text)
            body = {**name, 'expected_registration_sha256':preview.json()['registration_sha256'], 'allow_native_execution':True}
            for role in ('agent','worker'):
                self.assertEqual(403,call(api,'continue',body,role).status_code)
            self.assertEqual(403,call(api,'continue',{**body,'allow_native_execution':False}).status_code)
            self.assertEqual(422,call(api,'continue',{**body,'directory':'C:/untrusted'}).status_code)
            self.assertEqual(409,call(api,'continue',{**body,'expected_registration_sha256':'0'*64}).status_code)
            created = call(api, 'continue', body)
            self.assertEqual(201, created.status_code, created.text)
            self.assertEqual(created.json(), call(api, 'continue', body).json())
        worker = FileWorker({}, self.worker.evidence_root)
        with client(worker) as api:
            status = call(api,'continuation-status',name)
            self.assertEqual(200,status.status_code,status.text)
            self.assertTrue(status.json()['active'])
            headers={'Authorization':'Bearer '+tokens['controller']}
            dashboard=api.get('/v1/projects/'+self.project+'/dashboard',headers=headers)
            self.assertEqual(200,dashboard.status_code,dashboard.text)
            self.assertIn('workspace:http-next',dashboard.json()['continuation_workspaces'])
            self.assertNotIn('workspace:http-next',dashboard.json()['project']['resources'])
            catalog=api.get('/v1/projects/'+self.project+'/operations',headers=headers).json()['library']
            entry=next(item for item in catalog if item['name']=='http-next')
            self.assertTrue(entry['active']);self.assertFalse(entry['granted'])

    def test_continuation_recovers_complete_receipt_but_reconciles_incomplete_or_changed_lineage(self):
        from unittest.mock import patch
        self.prepare(); config = self.register()['registration']
        task, _ = self.deliver_change(config, 'def handle(value):\n    return value * 2\n', 'receipt-first')
        review = self.registry.continuation_preview(self.core, 'owner', task, 'receipt-next')
        args = ('owner', task, 'receipt-next', review['registration_sha256'], True)
        with patch.object(self.registry, '_candidate', side_effect=Conflict('Simulated pre-commit interruption')):
            with self.assertRaises(Conflict): self.registry.continue_project(self.core, *args)
        self.assertFalse(self.registry.continuation_status(self.core, 'owner', task, 'receipt-next')['registered'])
        self.assertTrue((self.root/'receipt-next'/'registration.json').is_file())
        copied = self.root/'receipt-next'/'snapshot'/'files'/'app.py'
        pristine = copied.read_bytes(); copied.write_bytes(pristine+b'\n# unregistered edit\n')
        with self.assertRaises(Conflict): self.registry.continue_project(self.core, *args)
        copied.write_bytes(pristine)
        result = self.registry.continue_project(self.core, *args)
        self.assertTrue(result['active'])
        broken = self.registry.continuation_preview(self.core, 'owner', task, 'broken-next')
        target = self.root/'broken-next';target.mkdir();(target/'owner.txt').write_text('retain')
        with self.assertRaises(Conflict):
            self.registry.continue_project(self.core, 'owner', task, 'broken-next', broken['registration_sha256'], True)
        self.assertEqual('retain',(target/'owner.txt').read_text())
        (self.root/'receipt-next'/'snapshot'/'continuation.json').write_text('{}')
        restored = ScaffoldRegistry(FileWorker({},self.worker.evidence_root),self.root,enabled=True)
        restored.sync(self.core)
        status=restored.continuation_status(self.core,'owner',task,'receipt-next')
        self.assertFalse(status['active']);self.assertTrue(status['reconciliation_required'])

    def test_generation_source_aliases_remain_project_scoped_and_nonoverlapping(self):
        self.prepare(); config = self.register()['registration']
        source = Path(self.creation['directory'])/'source'
        extra = Workspace.snapshot(source,self.root/'extra-snapshot',config['selected'])
        targets = [{'project_id':self.project,'resource_id':config['source'],
                    'workspace_resource':config['workspace'],'directory':str(source)}]
        workspaces={**self.worker.workspaces,(self.project,'workspace:extra'):extra}
        alias={'project_id':self.project,'resource_id':'source:extra','workspace_resource':'workspace:extra','directory':str(source)}
        FileWorker(workspaces,self.worker.evidence_root,self.worker.sandbox,[*targets,alias])
        other=self.core.create_project('owner','Other')
        with self.assertRaises(ValueError):
            FileWorker({**self.worker.workspaces,(other,'workspace:extra'):extra},self.worker.evidence_root,
                       self.worker.sandbox,[*targets,{**alias,'project_id':other}])
        nested=source/'nested';nested.mkdir()
        with self.assertRaises(ValueError):
            FileWorker(workspaces,self.worker.evidence_root,self.worker.sandbox,[*targets,{**alias,'directory':str(nested)}])

    def test_registration_is_exact_durable_idempotent_and_does_not_grant_permissions(self):
        self.prepare()
        with self.assertRaises(Denied): self.register(allow_native_execution=False)
        with self.assertRaises(Conflict): self.register(expected_registration_sha256='0' * 64)
        first = self.register(); second = self.register()
        self.assertEqual(first, second); self.assertTrue(first['active'])
        self.assertEqual(1, self.core.db.execute('SELECT COUNT(*) FROM scaffold_registrations').fetchone()[0])
        policy = self.core._owned('owner', self.project)
        self.assertEqual('read_only', policy['mode']); self.assertEqual('[]', policy['resources'])
        restored_worker = FileWorker({}, self.worker.evidence_root)
        restored = ScaffoldRegistry(restored_worker, self.root, enabled=True); restored.sync(self.core)
        self.assertTrue(restored.get(self.core, 'owner', self.spec, self.plan['name'])['active'])
        self.assertEqual(1, len(restored_worker.workspaces)); self.assertEqual(1, len(restored_worker.delivery.targets))
        self.assertEqual(1, len(restored_worker.sandbox.profiles))

    def test_registration_rejects_mutated_scaffold_and_missing_host_permission(self):
        self.prepare()
        self.registry.enabled = False
        with self.assertRaises(Denied): self.register()
        self.registry.enabled = True
        (Path(self.creation['directory'])/'source/app.py').write_text('changed')
        with self.assertRaises(Conflict): self.register()
        self.assertFalse(self.worker.workspaces)

    def test_restore_blocks_tampered_manifest_without_blocking_other_projects(self):
        self.prepare(); self.register()
        (Path(self.creation['directory'])/'snapshot/manifest.json').write_text('{}')
        worker = FileWorker({}, self.worker.evidence_root)
        restored = ScaffoldRegistry(worker, self.root, enabled=True); restored.sync(self.core)
        self.assertFalse(worker.workspaces)
        self.assertTrue(restored.get(self.core, 'owner', self.spec, self.plan['name'])['reconciliation_required'])
        self.assertTrue(self.core.projects('owner'))

    def test_restore_without_host_enablement_does_not_enable_native_execution(self):
        self.prepare(); self.register()
        worker = FileWorker({}, self.worker.evidence_root)
        restored = ScaffoldRegistry(worker, self.root, enabled=False); restored.sync(self.core)
        self.assertIsNone(worker.sandbox)
        self.assertFalse(restored.get(self.core, 'owner', self.spec, self.plan['name'])['enabled'])

    def test_migration_from_11_preserves_specification_and_messages(self):
        self.core.db.execute('DROP TABLE runner_contacts')
        self.core.db.execute('DROP TABLE operation_notices')
        self.core.db.execute('DROP TABLE scaffold_registrations')
        self.core.db.execute('PRAGMA user_version=11')
        migrated = Core(self.database); self.addCleanup(migrated.close)
        self.assertEqual(15, migrated.db.execute('PRAGMA user_version').fetchone()[0])
        self.assertEqual(self.spec_hash, specifications.get(migrated, 'owner', self.spec)['sha256'])
        self.assertGreater(migrated.db.execute('SELECT COUNT(*) FROM messages').fetchone()[0], 0)

    def test_bound_profile_cannot_be_replaced_with_a_weaker_profile(self):
        from skyra_coding.native import NativeProfile
        self.prepare(web=True); config = self.register()['registration']
        original = self.worker.sandbox.profiles[config['profile']['name']]
        self.worker.sandbox.profiles['weaker'] = NativeProfile('weaker', original.argv, ('tests/test_acceptance.py',), 30)
        self.core.set_policy('owner', self.project, 'full', [config['workspace']])
        runtime = RepairRuntime(self.worker, {'fixture': WebProvider()})
        with self.assertRaises(ValueError):
            runtime.create(self.core, 'owner', self.project, config['workspace'], 'weaker', 'fixture',
                           'Do not weaken protection', config['selected'], [], 'wrong-profile')
        task = self.core.create_task('owner', self.project, 'write', config['workspace'],
                                    {'operation': 'patch', 'path': 'server.py',
                                     'expected_sha256': self.worker.workspaces[(self.project, config['workspace'])].read('server.py')['sha256'],
                                     'old': '127.0.0.1', 'new': '0.0.0.0'})
        token = self.core.start('owner', task)['lease_token']
        with self.assertRaises(ValueError): self.worker.perform(self.core, 'owner', task, token)
        self.assertIn('127.0.0.1', self.worker.workspaces[(self.project, config['workspace'])].read('server.py')['content'])

    def test_changed_interpreter_is_refused_before_model_generation(self):
        executable = self.root / 'fixture-python.exe'; executable.write_bytes(b'reviewed executable bytes')
        self.args['python'] = str(executable)
        self.prepare(); config = self.register()['registration']
        executable.write_bytes(b'changed executable bytes')
        self.core.set_policy('owner', self.project, 'full', [config['workspace']])
        provider = WebProvider(); runtime = RepairRuntime(self.worker, {'fixture': provider})
        with self.assertRaises(ValueError):
            runtime.create(self.core, 'owner', self.project, config['workspace'], config['profile']['name'],
                           'fixture', 'Implement approved requirements', config['selected'], [], 'changed-interpreter')
        self.assertEqual(0, provider.calls)

    def test_web_template_requires_real_success_cases_and_safe_response_headers(self):
        from skyra_coding.templates import web_files
        good = {'name':'home','input':{'method':'GET','path':'/','body':''},
                'output':{'status':200,'content_type':'text/html','body':'<h1>Hello</h1>'}}
        for case in ({**good, 'input':{**good['input'],'method':'SHELL'}},
                     {**good, 'input':{**good['input'],'path':'http://external.example'}},
                     {**good, 'output':{**good['output'],'status':500}},
                     {**good, 'output':{**good['output'],'content_type':'text/html\r\nInjected: value'}}):
            with self.assertRaises(ValueError): web_files({'cases':[case]},'website')

    def test_controller_api_registration_survives_restart_without_json_config_edits(self):
        self.prepare()
        tokens = {role: role.ljust(40, 'x') for role in ('controller', 'agent', 'worker')}
        credentials = [Credential(hashlib.sha256(token.encode()).hexdigest(), 'owner', role,
                                  frozenset() if role == 'controller' else frozenset({self.project}))
                       for role, token in tokens.items()]
        def client(worker):
            runtime = RepairRuntime(worker, {'fixture': WebProvider()})
            result = TestClient(create_app(self.database, credentials, file_worker=worker, repair_runtime=runtime,
                                           scaffold_root=self.root, scaffold_execution_enabled=True, unattended_enabled=True),
                                base_url='http://127.0.0.1', client=('127.0.0.1',50000))
            self.addCleanup(result.close)
            return result
        api = client(self.worker)
        def call(api, route, body, role='controller'):
            return api.post(f'/v1/specifications/{self.spec}/scaffolds/{route}', json=body,
                            headers={'Authorization':'Bearer '+tokens[role]})
        body = {'name': self.plan['name'], 'expected_plan_sha256': checksum(self.plan)}
        review = call(api, 'registration-preview', body)
        self.assertEqual(200, review.status_code, review.text)
        request = {**body, 'expected_registration_sha256': review.json()['registration_sha256'], 'allow_native_execution': True}
        for role in ('agent', 'worker'):
            self.assertEqual(403, call(api, 'register', request, role).status_code)
            self.assertEqual(403, call(api, 'registration', {'name':self.plan['name']}, role).status_code)
        self.assertEqual(422, call(api, 'register', {**request, 'directory':'C:/untrusted'}).status_code)
        self.assertEqual(201, call(api, 'register', request).status_code)
        self.assertEqual(201, call(api, 'register', request).status_code)
        api.close()
        restored_worker = FileWorker({}, self.worker.evidence_root)
        restored = client(restored_worker)
        status = call(restored, 'registration', {'name':self.plan['name']})
        self.assertTrue(status.json()['active'], status.text)
        self.assertEqual(1,len(restored_worker.workspaces))
        catalog = restored.get('/v1/projects/'+self.project+'/operations',headers={'Authorization':'Bearer '+tokens['controller']})
        self.assertEqual(200,catalog.status_code,catalog.text)
        self.assertEqual(self.plan['name'],catalog.json()['library'][0]['name'])
        self.assertTrue(catalog.json()['library'][0]['active'])
        self.assertFalse(catalog.json()['library'][0]['granted'])
        self.assertEqual('read_only', self.core._owned('owner',self.project)['mode'])

    def test_real_website_failed_repair_second_cycle_restart_and_separate_delivery(self):
        self.prepare(web=True); registration = self.register()['registration']
        resource = registration['workspace']; target = registration['source']
        self.core.set_policy('owner', self.project, 'full', [resource, target])
        provider = WebProvider(); runtime = RepairRuntime(self.worker, {'fixture': provider})
        jobs = BuildJobs(runtime)
        conversation = self.core.create_conversation('owner', self.project)
        job = jobs.create(self.core, 'owner', self.project, resource=resource,
                          profile=registration['profile']['name'], provider='fixture',
                          goal='Build the reviewed website and API', files=registration['selected'], skills=[],
                          max_calls=2, max_cycles=2, max_steps=40, duration_seconds=3600,
                          auto_accept=True, allow_model_calls=True, request_id='website-build', specification=self.spec,
                          conversation=conversation)
        now = self.core.clock(); self.core.clock = lambda: now
        for _ in range(40):
            now += 6
            state = jobs.tick(self.core, 'owner', self.project)['build_job']
            if state and state['state'] in {'completed', 'failed', 'blocked', 'budget_limited'}: break
        self.assertEqual('completed', state['state'], state)
        self.assertEqual(2, provider.calls); self.assertEqual(2, len(state['cycles']))
        self.assertEqual('failed_retest', state['cycles'][0]['state'])
        root = Path(self.creation['directory'])
        self.assertIn('NotImplementedError', (root/'source/app.py').read_text())
        # Restore from durable records after the snapshot has changed; no replay.
        worker = FileWorker({}, self.worker.evidence_root)
        registry = ScaffoldRegistry(worker, self.root, enabled=True); registry.sync(self.core)
        self.assertTrue(registry.get(self.core, 'owner', self.spec, self.plan['name'])['active'])
        self.core.set_policy('owner', self.project, 'ask', [resource, target])
        delivery = worker.delivery.preview(self.core, 'owner', state['run'], target)
        self.assertEqual({'app.py', 'index.html'}, {item['path'] for item in delivery['plan']['changes']})
        prepared = worker.delivery.prepare(self.core, 'owner', state['run'], target, delivery['sha256'], 'deliver-site')
        approval = self.core.start('owner', prepared['id'])
        self.assertIn('approval_id', approval)
        self.core.decide('owner', approval['approval_id'], True)
        lease = self.core.start('owner', prepared['id'])
        worker.perform(self.core, 'owner', prepared['id'], lease['lease_token'])
        self.assertEqual('succeeded', self.core.task('owner', prepared['id'])['state'])
        self.assertEqual(HTML, (root/'source/index.html').read_text())
        self.assertEqual(self.plan['files']['server.py'], (root/'source/server.py').read_text())
        self.assertEqual(job['id'], state['id'])
        generation = registry.continuation_preview(self.core, 'owner', prepared['id'], 'website-next')
        registry.continue_project(self.core, 'owner', prepared['id'], 'website-next', generation['registration_sha256'], True)
        from jarvis_core.coding_history import read
        linked = read(self.core, 'owner', conversation)['jobs'][0]
        self.assertEqual('failed_retest',linked['cycles'][0]['state'])
        self.assertEqual('web-fixture',linked['cycles'][0]['model'])
        self.assertEqual('succeeded',linked['deliveries'][0]['state'])
        self.assertEqual('workspace:website-next',linked['generations'][0]['workspace'])


if __name__ == '__main__': unittest.main()
