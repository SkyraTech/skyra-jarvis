"""New-project contract review, guarded creation and real coding handoff."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
for source in ('services/core/src', 'workers/coding/src', 'packages/agent-runtime/src'):
    sys.path.insert(0, str(ROOT / source))

from jarvis_core import Core, Denied
from jarvis_core import specifications
from jarvis_core.store import encode
from jarvis_runtime.conversation import ConversationRuntime
from skyra_coding import BoundaryError, FileWorker, Workspace
from skyra_coding.scaffold import TEMPLATE, TEST, STUB, checksum, preview, materialize, validate_contract
from skyra_coding.native import NativeExecutor, NativeProfile
from skyra_coding.workflow import CodingWorkflow


class ScaffoldTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.database = self.root / 'core.sqlite3'
        self.core = Core(self.database)
        self.addCleanup(self.core.close)
        self.project = self.core.create_project('owner', 'New project')
        class PlanningProvider:
            model = 'fixture'
            def complete(provider, system, context, schema):
                return json.dumps({'reply': 'Plan for owner review', 'plan': {
                    'title': 'Doubling service', 'overview': 'Double the input integer.',
                    'requirements': ['Return twice the input integer'], 'deliverables': ['Python function'],
                    'phases': [{'title': 'Implement', 'tasks': ['Implement handle'],
                                'acceptance': ['Reviewed examples pass']}], 'risks': [], 'questions': []}}), {}
        runtime = ConversationRuntime({'fixture': PlanningProvider()})
        conversation = self.core.create_conversation('owner', self.project)
        turn = runtime.create(self.core, 'owner', conversation, 'fixture', 'plan', 'Plan doubling', 'plan')
        runtime.generate(self.core, 'owner', turn)
        spec = specifications.publish(self.core, 'owner', self.project, turn, 0, 'spec')
        self.spec = spec['id']; self.spec_hash = spec['sha256']; self.documents = spec['documents']
        specifications.approve(self.core, 'owner', self.spec, self.spec_hash)
        self.args = dict(specification=self.spec, expected_sha256=self.spec_hash,
                         contract={'cases': [{'name': 'positive', 'input': 3, 'output': 6},
                                             {'name': 'negative', 'input': -2, 'output': -4}]},
                         parent=str(self.root), name='client-service', python=sys.executable)

    def plan(self, **changes):
        return preview(self.core, 'owner', **{**self.args, **changes})

    def create(self, **changes):
        args = {**self.args, **changes}
        plan = preview(self.core, 'owner', **args)
        return materialize(self.core, 'owner', **args, expected_plan_sha256=checksum(plan))

    def test_review_is_deterministic_and_has_no_file_or_permission_effects(self):
        before = set(self.root.iterdir())
        first = self.plan(); second = self.plan()
        self.assertEqual(checksum(first), checksum(second))
        self.assertEqual(TEMPLATE, first['template'])
        self.assertEqual(before, set(self.root.iterdir()))
        self.assertIn(TEST, first['profile']['protected_paths'])
        self.assertIn('acceptance.json', first['profile']['protected_paths'])
        self.assertEqual(STUB, first['files']['app.py'])
        self.assertEqual(set(specifications.DOCUMENT_NAMES), {name[5:] for name in first['files'] if name.startswith('docs/')})
        for name in specifications.DOCUMENT_NAMES:
            self.assertEqual('approved_specification' if name in self.documents else 'host_template', first['document_provenance'][name])
        self.assertEqual(0, self.core.db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0])

    def test_unapproved_superseded_wrong_hash_and_wrong_owner_rejected(self):
        with self.assertRaises(Denied): preview(self.core, 'outsider', **self.args)
        with self.assertRaises(BoundaryError): self.plan(expected_sha256='0' * 64)
        for state in ('draft', 'superseded'):
            self.core.db.execute('UPDATE project_specs SET state=? WHERE id=?', (state, self.spec))
            with self.assertRaises(BoundaryError): self.plan()

    def test_tampered_document_bundle_is_rejected(self):
        self.core.db.execute('UPDATE project_specs SET documents=? WHERE id=?', (encode({**self.documents, '05_PROJECT_TASKS.md': 'Changed'}), self.spec))
        with self.assertRaises(BoundaryError): self.plan()

    def test_approved_custom_documents_are_preserved_instead_of_template_defaults(self):
        docs = {**self.documents, '02_SYSTEM_ARCHITECTURE.md': '# Owner architecture\n\nCustom constraints.\n'}
        revision = specifications.revise(self.core, 'owner', self.spec, docs, self.spec_hash, 1, 'revision')
        specifications.approve(self.core, 'owner', revision['id'], revision['sha256'])
        plan = self.plan(specification=revision['id'], expected_sha256=revision['sha256'])
        self.assertEqual(docs['02_SYSTEM_ARCHITECTURE.md'], plan['files']['docs/02_SYSTEM_ARCHITECTURE.md'])
        self.assertEqual('approved_specification', plan['document_provenance']['02_SYSTEM_ARCHITECTURE.md'])
        with self.assertRaises(BoundaryError): self.plan()

    def test_contract_is_data_and_not_python_source(self):
        dangerous = '\"); __import__("os").system("anything") #\nUnicode: \u2603'
        plan = self.plan(contract={'cases': [{'name': 'inert data', 'input': dangerous, 'output': {'value': dangerous}}]})
        namespace = {'__file__': str(self.root / TEST)}
        import types
        module = types.ModuleType('app'); module.handle = lambda value: {'value': value}
        with patch.dict(sys.modules, {'app': module}):
            original_path = sys.path[:]
            try:
                exec(compile(plan['files'][TEST], TEST, 'exec'), namespace)
                namespace['AcceptanceTests']('test_contract').test_contract()
            finally:
                sys.path[:] = original_path

    def test_contract_limits_duplicate_inputs_and_ambiguous_types(self):
        valid = self.args['contract']
        invalid = [None, {}, {'cases': []}, {'cases': valid['cases'] * 17},
                   {'cases': [valid['cases'][0], valid['cases'][0]]},
                   {'cases': [{'name': 'x', 'input': float('nan'), 'output': 1}]},
                   {'cases': [{'name': 'x', 'input': 1, 'output': float('inf')}]},
                   {'cases': [{'name': 'x', 'input': {1: 'bad'}, 'output': 1}]},
                   {'cases': [{'name': 'x', 'input': (), 'output': 1}]},
                   {'cases': [{'name': 'x\n', 'input': 1, 'output': 1}]},
                   {'cases': [{'name': 'x', 'input': 'x' * 17000, 'output': 1}]}]
        nested = 1
        for _ in range(12): nested = [nested]
        invalid.append({'cases': [{'name': 'x', 'input': nested, 'output': 1}]})
        for contract in invalid:
            with self.subTest(contract=str(contract)[:50]):
                with self.assertRaises(BoundaryError): validate_contract(contract)
        detached = validate_contract(valid)
        detached['cases'][0]['input'] = 99
        self.assertEqual(3, valid['cases'][0]['input'])

    def test_acceptance_distinguishes_boolean_from_number(self):
        plan = self.plan(contract={'cases': [{'name': 'typed value', 'input': 0, 'output': 1}]})
        namespace = {'__file__': str(self.root / TEST)}
        import types
        module = types.ModuleType('app'); module.handle = lambda value: True
        with patch.dict(sys.modules, {'app': module}):
            original_path = sys.path[:]
            try:
                exec(compile(plan['files'][TEST], TEST, 'exec'), namespace)
                with self.assertRaises(AssertionError): namespace['AcceptanceTests']('test_contract').test_contract()
            finally:
                sys.path[:] = original_path

    def test_path_and_executable_boundaries(self):
        for name in ('../escape', 'CON', 'con', 'nul', 'a/b', 'a\\b', 'UPPER', 'a.', 'x', '.git'):
            with self.subTest(name=name):
                with self.assertRaises(BoundaryError): self.plan(name=name)
        for parent in ('relative', str(self.root / 'missing')):
            with self.assertRaises(BoundaryError): self.plan(parent=parent)
        for python in ('python.exe', str(self.root / 'missing.exe'), str(self.database)):
            with self.assertRaises(BoundaryError): self.plan(python=python)

    @unittest.skipUnless(os.name == 'nt', 'Exclusive Windows publication')
    def test_create_preserves_documents_and_protected_failing_baseline(self):
        result = self.create()
        destination = Path(result['directory'])
        self.assertEqual('unimplemented', result['state'])
        self.assertFalse(result['registration_draft']['execution']['owner_enabled'])
        for name, text in self.documents.items():
            self.assertEqual(text, (destination / 'source/docs' / name).read_text())
        workspace = Workspace(destination / 'snapshot')
        self.assertEqual([], workspace.diff()['changes'])
        self.assertTrue(workspace.verify()['passed'])
        profile = NativeProfile(**{**self.plan()['profile'], 'argv': tuple(self.plan()['profile']['argv']),
                                   'protected_paths': tuple(self.plan()['profile']['protected_paths'])})
        report = NativeExecutor([profile], owner_enabled=True).run(workspace, profile.name)
        self.assertFalse(report['passed'])
        self.assertIn('NotImplementedError', report['output'])
        self.assertIn('Ran 1 test', report['output'])
        self.assertEqual(0, self.core.db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0])
        event = self.core.db.execute("SELECT subject FROM events WHERE kind='scaffold.created'").fetchone()
        self.assertEqual(result['plan_sha256'], json.loads(event[0])['plan_sha256'])

    @unittest.skipUnless(os.name == 'nt', 'Exclusive Windows publication')
    def test_exact_review_and_existing_destination_never_overwritten(self):
        plan = self.plan()
        with self.assertRaises(BoundaryError):
            materialize(self.core, 'owner', **self.args, expected_plan_sha256='0' * 64)
        self.assertFalse((self.root / self.args['name']).exists())
        self.create()
        with self.assertRaises(BoundaryError): self.create()
        self.assertEqual(STUB, (self.root / self.args['name'] / 'source/app.py').read_text())
        changed = {**self.args, 'contract': {'cases': [{'name': 'new', 'input': 1, 'output': 2}]}, 'name': 'other-service'}
        with self.assertRaises(BoundaryError):
            materialize(self.core, 'owner', **changed, expected_plan_sha256=checksum(plan))

    @unittest.skipUnless(os.name == 'nt', 'Exclusive Windows publication')
    def test_changed_interpreter_bytes_invalidate_review_before_writing(self):
        executable = self.root / 'reviewed-python.exe'
        executable.write_bytes(b'first executable fixture')
        args = {**self.args, 'python': str(executable)}
        plan = preview(self.core, 'owner', **args)
        executable.write_bytes(b'changed executable fixture')
        with self.assertRaises(BoundaryError):
            materialize(self.core, 'owner', **args, expected_plan_sha256=checksum(plan))
        self.assertFalse((self.root / self.args['name']).exists())

    @unittest.skipUnless(os.name == 'nt', 'Windows reparse guard')
    def test_junction_parent_is_rejected(self):
        target = self.root / 'real-parent'; target.mkdir()
        junction = self.root / 'linked-parent'
        result = subprocess.run(['cmd.exe', '/d', '/c', 'mklink', '/J', str(junction), str(target)],
                                capture_output=True, timeout=10)
        self.assertEqual(0, result.returncode, result.stderr)
        with self.assertRaises(BoundaryError): self.plan(parent=str(junction))
        nested = target / 'nested'; nested.mkdir()
        with self.assertRaises(BoundaryError): self.plan(parent=str(junction / 'nested'))

    @unittest.skipUnless(os.name == 'nt', 'Exclusive Windows publication')
    def test_publish_race_does_not_replace_newly_created_destination(self):
        real_rename = os.rename
        def race(source, destination):
            Path(destination).mkdir()
            (Path(destination) / 'owner.txt').write_text('Preserve')
            return real_rename(source, destination)
        with patch('skyra_coding.scaffold.os.rename', side_effect=race):
            with self.assertRaises(OSError): self.create()
        self.assertEqual('Preserve', (self.root / self.args['name'] / 'owner.txt').read_text())
        self.assertFalse((self.root / self.args['name'] / 'source').exists())
        self.assertEqual(1, len(list(self.root.glob('.jarvis-scaffold-*'))))

    @unittest.skipUnless(os.name == 'nt', 'Exclusive Windows publication')
    def test_interrupted_staging_keeps_review_and_never_publishes(self):
        with patch('skyra_coding.scaffold.Workspace.snapshot', side_effect=OSError('fixture write failure')):
            with self.assertRaises(OSError): self.create()
        self.assertFalse((self.root / self.args['name']).exists())
        stage = next(self.root.glob('.jarvis-scaffold-*'))
        self.assertEqual(checksum(self.plan()), json.loads((stage / 'review.json').read_text())['plan_sha256'])
        self.assertEqual(0, self.core.db.execute("SELECT COUNT(*) FROM events WHERE kind='scaffold.created'").fetchone()[0])

    @unittest.skipUnless(os.name == 'nt', 'Exclusive Windows publication')
    def test_audit_failure_keeps_published_bundle_and_prevents_replay(self):
        with patch.object(self.core, '_event', side_effect=RuntimeError('fixture audit failure')):
            with self.assertRaises(RuntimeError): self.create()
        self.assertTrue((self.root / self.args['name'] / 'scaffold.json').is_file())
        with self.assertRaises(BoundaryError): self.create()

    def cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / 'workers/coding/scaffold.py'),
                               '--database', str(self.database), '--actor', 'owner',
                               '--request', str(self.root / 'request.json'), *args],
                              capture_output=True, text=True, timeout=20)

    def test_owner_command_review_and_invalid_input_have_no_tracebacks(self):
        request = self.root / 'request.json'
        request.write_text(json.dumps(self.args))
        review = self.root / 'review.json'
        result = self.cli('--review', str(review))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(checksum(self.plan()), json.loads(review.read_text())['plan_sha256'])
        for args in (('--review', str(review)), ('--apply',), ('--apply', '--expected-plan-sha256', '0' * 64)):
            result = self.cli(*args)
            self.assertNotEqual(0, result.returncode)
            self.assertNotIn('Traceback', result.stderr)
        request.write_text('{bad json')
        result = self.cli('--review', str(self.root / 'other-review.json'))
        self.assertEqual(2, result.returncode)
        self.assertNotIn('Traceback', result.stderr)
        request.unlink()
        result = self.cli('--review', str(self.root / 'other-review.json'))
        self.assertEqual(2, result.returncode)
        self.assertNotIn('Traceback', result.stderr)
        self.assertFalse((self.root / self.args['name']).exists())

    @unittest.skipUnless(os.name == 'nt', 'Owner Windows command')
    def test_owner_command_creates_reviewed_bundle_without_enabling_execution(self):
        (self.root / 'request.json').write_text(json.dumps(self.args))
        result = self.cli('--apply', '--expected-plan-sha256', checksum(self.plan()))
        self.assertEqual(0, result.returncode, result.stderr)
        created = json.loads(result.stdout)
        self.assertFalse(created['registration_draft']['execution']['owner_enabled'])
        self.assertEqual('unimplemented', created['state'])
        self.assertEqual(self.project, created['registration_draft']['workspaces'][0]['project_id'])

    @unittest.skipUnless(os.name == 'nt', 'Native coding handoff')
    def test_created_project_completes_existing_governed_repair_and_delivery(self):
        from jarvis_runtime import RepairRuntime
        from jarvis_core.build_jobs import BuildJobs
        result = self.create()
        config = result['registration_draft']
        workspace = Workspace(Path(result['directory']) / 'snapshot')
        resource = config['workspaces'][0]['resource_id']
        self.core.set_policy('owner', self.project, 'full', [resource, 'source:' + self.args['name']])
        profile = config['execution']['profiles'][0]
        executor = NativeExecutor([NativeProfile(profile['name'], tuple(profile['argv']), tuple(profile['protected_paths']), profile['timeout'])], owner_enabled=True)
        worker = FileWorker({(self.project, resource): workspace}, config['evidence_root'], executor, config['delivery_targets'])
        class Provider:
            provider = 'fixture'; model = 'scaffold-fixture'; timeout = 1; max_output_tokens = 256
            calls = 0
            def complete(provider, system, context, schema):
                provider.calls += 1
                data = json.loads(context)
                source = next(file for file in data['files'] if file['path'] == 'app.py')
                return json.dumps({'summary': 'Implement reviewed doubling contract', 'patches': [{
                    'path': 'app.py', 'expected_sha256': source['sha256'],
                    'old': 'raise NotImplementedError("Implementation pending")', 'new': 'return value * 2'}]}), {'total_tokens': 20}
        provider = Provider()
        runtime = RepairRuntime(worker, {'fixture': provider})
        jobs = BuildJobs(runtime)
        job = jobs.create(self.core, 'owner', self.project, resource=resource, profile=profile['name'], provider='fixture',
                          goal='Implement approved doubling contract', files=list(workspace.selected), skills=[],
                          max_calls=1, max_cycles=1, max_steps=20, duration_seconds=3600,
                          auto_accept=True, allow_model_calls=True, request_id='scaffold-build', specification=self.spec)
        now = self.core.clock()
        self.core.clock = lambda: now
        for _ in range(20):
            now += 6
            tick = jobs.tick(self.core, 'owner', self.project)['build_job']
            if tick and tick['state'] in {'completed', 'failed', 'blocked'}: break
        self.assertEqual('completed', tick['state'], tick)
        self.assertEqual(1, provider.calls)
        run = CodingWorkflow(worker).get(self.core, 'owner', tick['run'])
        self.assertEqual('ready_for_review', run['state'])
        self.assertEqual(STUB, (Path(result['directory']) / 'source/app.py').read_text())
        self.assertEqual(self.plan()['files'][TEST], workspace.read(TEST)['content'])
        self.assertEqual(job['id'], tick['id'])
        # Delivery still needs a separate source-task approval, even after the
        # build ran with full snapshot permission.
        self.core.set_policy('owner', self.project, 'ask', [resource, 'source:' + self.args['name']])
        delivery = worker.delivery.preview(self.core, 'owner', tick['run'], 'source:' + self.args['name'])
        prepared = worker.delivery.prepare(self.core, 'owner', tick['run'], 'source:' + self.args['name'], delivery['sha256'], 'deliver')
        approval = self.core.start('owner', prepared['id'])
        self.core.decide('owner', approval['approval_id'], True)
        lease = self.core.start('owner', prepared['id'])
        worker.perform(self.core, 'owner', prepared['id'], lease['lease_token'])
        self.assertEqual('succeeded', self.core.task('owner', prepared['id'])['state'])
        self.assertIn('return value * 2', (Path(result['directory']) / 'source/app.py').read_text())
        self.assertEqual(self.plan()['files'][TEST], (Path(result['directory']) / 'source' / TEST).read_text())


if __name__ == '__main__':
    unittest.main()
