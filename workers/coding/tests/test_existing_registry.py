"""Existing project handoff, real protected tests, restart and separate delivery."""
import json
import hashlib
import os
import shutil
from pathlib import Path
import sys
import unittest

import test_scaffold
from jarvis_core import Conflict, Denied
from jarvis_core.build_jobs import BuildJobs
from jarvis_runtime import RepairRuntime
from skyra_coding import FileWorker
from skyra_coding.admission import ProjectAdmission
from skyra_coding.existing_registry import ExistingProjectRegistry
from skyra_coding.native import NativeProfile


@unittest.skipUnless(os.name == 'nt', 'Windows trusted project execution')
class ExistingRegistryTests(unittest.TestCase):
    setUp = test_scaffold.ScaffoldTests.setUp

    def prepare(self):
        self.source = self.root / 'existing'; self.source.mkdir()
        (self.source / 'app.py').write_text('def answer():\n    return 1\n', encoding='utf-8')
        (self.source / 'test_acceptance.py').write_text(
            'import unittest\nfrom app import answer\nclass Acceptance(unittest.TestCase):\n'
            '    def test_answer(self): self.assertEqual(2, answer())\n', encoding='utf-8')
        (self.source / 'requirements.md').write_text('# Owner requirements\nReturn two.\n', encoding='utf-8')
        self.state = self.root / 'admissions'; self.state.mkdir()
        self.admission = ProjectAdmission({'internal-project': self.source}, self.state)
        self.review = self.admission.preview('internal-project', 'first-generation',
            ['app.py', 'test_acceptance.py', 'requirements.md'], ['helper.py'])
        self.admission.materialize('internal-project', 'first-generation',
            ['app.py', 'test_acceptance.py', 'requirements.md'], ['helper.py'],
            expected_sha256=self.review['sha256'])
        self.profile = NativeProfile('existing-tests', (sys.executable, '-m', 'unittest', 'test_acceptance'),
                                     ('test_acceptance.py', 'requirements.md'), 30)
        self.worker = FileWorker({}, self.root / 'evidence')
        self.registry = ExistingProjectRegistry(self.worker, self.admission,
            {'internal-project': self.profile}, enabled=True)
        return self.registry.preview_existing(self.core, 'owner', self.spec, 'first-generation', self.review['sha256'])

    def register(self, preview):
        return self.registry.register_existing(self.core, 'owner', self.spec, 'first-generation',
            self.review['sha256'], preview['registration_sha256'], True)

    def test_registration_preserves_grants_and_requires_explicit_native_consent(self):
        review = self.prepare()
        with self.assertRaises(Denied):
            self.registry.register_existing(self.core, 'owner', self.spec, 'first-generation',
                self.review['sha256'], review['registration_sha256'], False)
        result = self.register(review)
        self.assertTrue(result['active'])
        self.assertEqual([], json.loads(self.core._owned('owner', self.project)['resources']))
        self.assertNotIn('python_sha256', result['registration'])
        self.assertEqual('fixed-executable-v1', result['registration']['runtime']['kind'])
        self.assertEqual('def answer():\n    return 1\n', (self.source / 'app.py').read_text())

    def test_real_job_restart_and_source_delivery_preserve_existing_owner_documents(self):
        review = self.prepare(); registration = self.register(review)['registration']
        resource = registration['workspace']; target = registration['source']
        self.core.set_policy('owner', self.project, 'full', [resource, target])
        class Provider:
            provider = 'fixture'; model = 'fixture'; timeout = 1; max_output_tokens = 1024
            calls = 0
            def complete(provider, system, context, schema):
                provider.calls += 1
                files = {f['path']: f for f in json.loads(context)['files']}
                return json.dumps({'summary': 'Implement reviewed function using reusable helper', 'patches': [
                    {'path': 'app.py', 'expected_sha256': files['app.py']['sha256'],
                     'old': files['app.py']['content'], 'new': 'from helper import value\ndef answer():\n    return value()\n'},
                    {'path': 'helper.py', 'expected_sha256': 'absent', 'old': '', 'new': 'def value():\n    return 2\n'}]}), {}
        provider = Provider(); jobs = BuildJobs(RepairRuntime(self.worker, {'fixture': provider}))
        job = jobs.create(self.core, 'owner', self.project, resource=resource, profile=self.profile.name,
            provider='fixture', goal='Return two using a reusable helper', files=registration['selected'], skills=[],
            max_calls=1, max_cycles=1, max_steps=30, duration_seconds=600, auto_accept=True,
            allow_model_calls=True, request_id='existing-project-build', specification=self.spec)
        now = self.core.clock(); self.core.clock = lambda: now
        for _ in range(30):
            now += 6
            state = jobs.tick(self.core, 'owner', self.project)['build_job']
            if state and state['state'] in {'completed', 'failed', 'blocked', 'budget_limited'}: break
        self.assertEqual('completed', state['state'], state)
        self.assertEqual(job['id'], state['id']); self.assertEqual(1, provider.calls)
        self.assertFalse((self.source / 'helper.py').exists())
        restored = FileWorker({}, self.worker.evidence_root)
        registry = ExistingProjectRegistry(restored, self.admission, {'internal-project': self.profile}, enabled=True)
        registry.sync(self.core)
        self.assertTrue(registry.get(self.core, 'owner', self.spec, 'first-generation')['active'])
        review = restored.delivery.preview(self.core, 'owner', state['run'], target)
        delivery = restored.delivery.prepare(self.core, 'owner', state['run'], target, review['sha256'], 'deliver-existing')
        lease = self.core.start('owner', delivery['id'])
        restored.perform(self.core, 'owner', delivery['id'], lease['lease_token'])
        self.assertEqual('succeeded', self.core.task('owner', delivery['id'])['state'])
        self.assertEqual('# Owner requirements\nReturn two.\n', (self.source / 'requirements.md').read_text())
        self.assertIn('from helper import value', (self.source / 'app.py').read_text())
        # Source now differs from original baseline. Restore retains the baseline
        # rather than silently treating delivered code as a new generation.
        again = ExistingProjectRegistry(FileWorker({}, self.worker.evidence_root), self.admission,
                                         {'internal-project': self.profile}, enabled=True)
        again.sync(self.core)
        self.assertTrue(again.get(self.core, 'owner', self.spec, 'first-generation')['active'])
        generation = again.continuation_preview(self.core, 'owner', delivery['id'], 'next-generation')
        continued = again.continue_project(self.core, 'owner', delivery['id'], 'next-generation',
                                           generation['registration_sha256'], True)
        self.assertTrue(continued['active'])
        next_config = continued['registration']
        self.assertEqual('fixed-executable-v1', next_config['runtime']['kind'])
        self.assertEqual(str(self.source), next_config['source_directory'])
        self.assertNotIn(next_config['workspace'], json.loads(self.core._owned('owner', self.project)['resources']))
        restarted = ExistingProjectRegistry(FileWorker({}, self.worker.evidence_root), self.admission,
                                             {'internal-project': self.profile}, enabled=True)
        restarted.sync(self.core)
        self.assertTrue(restarted.get(self.core, 'owner', self.spec, 'next-generation')['active'])

    def test_changed_host_profile_blocks_restore_without_rebinding_resources(self):
        review = self.prepare(); self.register(review)
        changed = NativeProfile(self.profile.name, self.profile.argv, self.profile.protected_paths, 31)
        worker = FileWorker({}, self.worker.evidence_root)
        registry = ExistingProjectRegistry(worker, self.admission, {'internal-project': changed}, enabled=True)
        registry.sync(self.core)
        result = registry.get(self.core, 'owner', self.spec, 'first-generation')
        self.assertFalse(result['active']); self.assertTrue(result['reconciliation_required'])
        self.assertEqual({}, worker.workspaces)

    def test_authenticated_api_uses_logical_roots_and_preserves_separate_registration(self):
        from fastapi.testclient import TestClient
        from jarvis_core.api import Credential, create_app
        self.prepare()
        owner = Credential(hashlib.sha256(b'owner-token'.ljust(40, b'x')).hexdigest(), 'owner', 'controller')
        agent = Credential(hashlib.sha256(b'agent-token'.ljust(40, b'x')).hexdigest(), 'owner', 'agent', frozenset({self.project}))
        app = create_app(self.database, [owner, agent], file_worker=self.worker,
            scaffold_root=self.state, scaffold_execution_enabled=True,
            existing_project_sources={'internal-project': self.source},
            existing_project_profiles={'internal-project': self.profile})
        with TestClient(app, base_url='http://127.0.0.1', client=('127.0.0.1', 50000)) as client:
            headers = {'Authorization': 'Bearer ' + 'owner-token'.ljust(40, 'x')}
            base = f'/v1/specifications/{self.spec}/existing-projects'
            body = {'source': 'internal-project', 'name': 'api-generation', 'files': ['app.py',
                    'test_acceptance.py', 'requirements.md'], 'create_paths': ['helper.py'],
                    'expected_sha256': self.spec_hash}
            denied = client.post(base + '/preview', json=body, headers={'Authorization': 'Bearer ' + 'agent-token'.ljust(40, 'x')})
            self.assertEqual(403, denied.status_code)
            invalid = client.post(base + '/preview', json={**body, 'directory': str(self.source)}, headers=headers)
            self.assertEqual(422, invalid.status_code)
            preview = client.post(base + '/preview', json=body, headers=headers)
            self.assertEqual(200, preview.status_code, preview.text)
            plan_hash = preview.json()['sha256']
            admitted = client.post(base + '/admit', json={**body, 'expected_plan_sha256': plan_hash}, headers=headers)
            self.assertEqual(201, admitted.status_code, admitted.text)
            self.assertFalse(admitted.json()['execution_enabled'])
            self.assertEqual({}, self.worker.workspaces)
            registration_body = {'name': body['name'], 'expected_plan_sha256': plan_hash}
            registration = client.post(base + '/registration-preview', json=registration_body, headers=headers)
            self.assertEqual(200, registration.status_code, registration.text)
            registered = client.post(base + '/register', headers=headers, json={**registration_body,
                'expected_registration_sha256': registration.json()['registration_sha256'],
                'allow_native_execution': True})
            self.assertEqual(201, registered.status_code, registered.text)
            self.assertTrue(registered.json()['active'])
            self.assertEqual([], json.loads(self.core._owned('owner', self.project)['resources']))

    def test_api_disables_unconfigured_admission_and_rejects_stale_spec_review(self):
        from fastapi.testclient import TestClient
        from jarvis_core.api import Credential, create_app
        self.prepare()
        owner = Credential(hashlib.sha256(b'owner-token'.ljust(40, b'x')).hexdigest(), 'owner', 'controller')
        body = {'source': 'internal-project', 'name': 'api-generation', 'files': ['app.py'],
                'create_paths': [], 'expected_sha256': '0' * 64}
        path = f'/v1/specifications/{self.spec}/existing-projects/preview'
        headers = {'Authorization': 'Bearer ' + 'owner-token'.ljust(40, 'x')}
        with TestClient(create_app(self.database, [owner], scaffold_root=self.state), base_url='http://127.0.0.1', client=('127.0.0.1', 50000)) as client:
            self.assertFalse(client.get('/v1/setup', headers=headers).json()['existing_projects']['available'])
            self.assertEqual(403, client.post(path, json=body, headers=headers).status_code)
        with TestClient(create_app(self.database, [owner], scaffold_root=self.state,
                existing_project_sources={'internal-project': self.source}), base_url='http://127.0.0.1', client=('127.0.0.1', 50000)) as client:
            self.assertEqual(409, client.post(path, json=body, headers=headers).status_code)

    def test_host_configuration_loads_only_fixed_sources_and_rejects_unknown_fields(self):
        from dataclasses import asdict
        from skyra_coding.existing_registry import load_host_config
        self.prepare()
        path = self.root / 'existing-projects.json'
        config = {'sources': {'internal-project': {'directory': str(self.source), 'profile': asdict(self.profile)}}}
        path.write_text(json.dumps(config), encoding='utf-8')
        sources, profiles, runtimes = load_host_config(path, self.state)
        self.assertEqual({'internal-project': self.source}, sources)
        self.assertEqual(self.profile, profiles['internal-project']); self.assertEqual({}, runtimes)
        config['sources']['internal-project']['command'] = 'model-selected command'
        path.write_text(json.dumps(config), encoding='utf-8')
        with self.assertRaises(ValueError): load_host_config(path, self.state)
        for invalid in ({'profile': {**asdict(self.profile), 'name': 123}},
                        {'profile': {**asdict(self.profile), 'protected_paths': ['test_acceptance.py'] * 2}},
                        {'runtime_binding': {'runtime': {'kind': 'fixed-executable-v1'},
                                             'executable_sha256': '0' * 64}}):
            config = {'sources': {'internal-project': {'directory': str(self.source),
                'profile': asdict(self.profile), **invalid}}}
            path.write_text(json.dumps(config), encoding='utf-8')
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError): load_host_config(path, self.state)

    @unittest.skipUnless(shutil.which('node'), 'Installed Node and compiler required')
    def test_admitted_typescript_project_binds_compiler_across_execution_and_restart(self):
        from jarvis_runtime import node_calibration
        from skyra_coding.node_templates import plan as node_plan
        from jarvis_core import specifications
        tools = node_calibration.toolchain()
        self.source = self.root / 'existing-node'; self.source.mkdir()
        plan = node_plan(specifications.get(self.core, 'owner', self.spec), self.source, 'existing-node',
            {'cases': [{'name': 'positive', 'input': 3, 'output': 6}]}, tools)
        for name, text in plan['files'].items():
            target = self.source / name; target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding='utf-8')
        self.state = self.root / 'admissions'; self.state.mkdir()
        self.admission = ProjectAdmission({'internal-node': self.source}, self.state)
        review = self.admission.preview('internal-node', 'node-generation', plan['selected'], ['src/double.ts'])
        self.admission.materialize('internal-node', 'node-generation', plan['selected'], ['src/double.ts'],
                                   expected_sha256=review['sha256'])
        profile = NativeProfile('existing-node-tests', tuple(plan['profile']['argv']),
                                 tuple(plan['profile']['protected_paths']), 45)
        bindings = {'internal-node': {key: plan[key] for key in ('runtime', 'executable_sha256')}}
        worker = FileWorker({}, self.root / 'evidence')
        registry = ExistingProjectRegistry(worker, self.admission, {'internal-node': profile},
                                           enabled=True, runtime_bindings=bindings)
        preview = registry.preview_existing(self.core, 'owner', self.spec, 'node-generation', review['sha256'])
        registered = registry.register_existing(self.core, 'owner', self.spec, 'node-generation', review['sha256'],
            preview['registration_sha256'], True)['registration']
        resource = registered['workspace']; self.core.set_policy('owner', self.project, 'full', [resource])
        class Provider:
            provider = 'fixture'; model = 'fixture'; timeout = 1; max_output_tokens = 1024
            def complete(provider, system, context, schema):
                files = {f['path']: f for f in json.loads(context)['files']}
                return json.dumps({'summary': 'Double numeric inputs using a shared helper', 'patches': [
                    {'path': 'src/main.ts', 'expected_sha256': files['src/main.ts']['sha256'],
                     'old': files['src/main.ts']['content'], 'new':
                        "import type { JsonValue } from './types.ts';\nimport { double } from './double.ts';\nexport function handle(value: JsonValue): JsonValue { if(typeof value!=='number') throw new TypeError('Number required'); return double(value); }\n"},
                    {'path': 'src/double.ts', 'expected_sha256': 'absent', 'old': '',
                     'new': 'export function double(value: number): number { return value * 2; }\n'}]}), {}
        jobs = BuildJobs(RepairRuntime(worker, {'fixture': Provider()}))
        jobs.create(self.core, 'owner', self.project, resource=resource, profile=profile.name,
            provider='fixture', goal='Double numbers', files=registered['selected'], skills=[],
            max_calls=1, max_cycles=1, max_steps=30, duration_seconds=600, auto_accept=True,
            allow_model_calls=True, request_id='existing-node-build', specification=self.spec)
        now = self.core.clock(); self.core.clock = lambda: now
        for _ in range(30):
            now += 6; state = jobs.tick(self.core, 'owner', self.project)['build_job']
            if state and state['state'] in {'completed', 'failed', 'blocked', 'budget_limited'}: break
        self.assertEqual('completed', state['state'], state)
        restored = FileWorker({}, worker.evidence_root)
        restored_registry = ExistingProjectRegistry(restored, self.admission, {'internal-node': profile},
                                                     enabled=True, runtime_bindings=bindings)
        restored_registry.sync(self.core)
        self.assertTrue(restored_registry.get(self.core, 'owner', self.spec, 'node-generation')['active'])
        self.assertEqual({tools['compiler']: tools['compiler_sha256']}, restored.toolchain_bindings[(self.project, resource)])
        self.assertFalse((self.source / 'src/double.ts').exists())
