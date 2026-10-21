"""Durable read tools preserve scope, input provenance and owner permissions."""
from dataclasses import replace
import json
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
for source in ('services/core/src', 'workers/coding/src'):
    sys.path.insert(0, str(REPO / source))
from jarvis_core import Core, Conflict, Denied
from skyra_coding import BoundaryError, FileWorker, Workspace
from skyra_coding.inspection import InspectionTools
from skyra_coding.scaffold import checksum
from skyra_coding.native import NativeExecutor, NativeProfile


@unittest.skipUnless(os.name == 'nt', 'Windows host profile identity')
class InspectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'; self.source.mkdir()
        (self.source / 'app.py').write_bytes(b'def answer():\r\n    return 41\r\n')
        (self.source / 'test_app.py').write_text('# protected acceptance\n')
        (self.source / '.env').write_text('DO_NOT_READ=secret')
        self.workspace = Workspace.snapshot(self.source, self.root / 'snapshot', ['app.py', 'test_app.py'], ['new.py'])
        self.database = self.root / 'core.sqlite3'; self.core = Core(self.database)
        self.addCleanup(self.core.close)
        self.project = self.core.create_project('owner', 'Inspection')
        self.core.set_policy('owner', self.project, 'read_only', ['workspace:demo'])
        self.profile = NativeProfile('test-profile', (sys.executable, '-m', 'unittest', 'test_app'), ('test_app.py',), 30)
        self.worker = FileWorker({(self.project, 'workspace:demo'): self.workspace}, self.root / 'evidence',
                                 NativeExecutor([self.profile], owner_enabled=True))
        self.worker.profile_bindings[(self.project, 'workspace:demo')] = self.profile.name
        self.tools = InspectionTools(self.worker)
        self.requests = [{'operation': 'inventory'}, {'operation': 'search', 'query': 'return'},
                         {'operation': 'read_lines', 'path': 'app.py', 'start': 1, 'count': 2}]

    def preview(self, requests=None):
        return self.tools.preview(self.core, 'owner', self.project, 'workspace:demo', self.profile.name,
                                  self.requests if requests is None else requests)

    def test_one_durable_read_batch_is_idempotent_after_restart_and_preserves_source(self):
        review = self.preview(); self.assertEqual(0, self.core.db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0])
        prepared = self.tools.prepare(self.core, 'owner', review['plan'], review['sha256'])
        with patch.object(self.worker.sandbox, 'run', side_effect=AssertionError('Inspection must not execute commands')):
            result = self.tools.step(self.core, 'owner', review['plan'], review['sha256'])
        self.assertTrue(result['complete']); self.assertEqual(3, len(result['results']))
        self.assertEqual('    return 41\r\n', result['results'][2]['result']['lines'][1]['text'])
        self.assertEqual('absent', result['results'][0]['result']['files'][1]['sha256'])
        self.assertNotIn('DO_NOT_READ', json.dumps(result))
        self.assertEqual(b'def answer():\r\n    return 41\r\n', (self.source / 'app.py').read_bytes())
        self.assertFalse((self.source / 'new.py').exists())
        other = Core(self.database)
        try:
            self.assertEqual(prepared, self.tools.prepare(other, 'owner', review['plan'], review['sha256']))
            self.assertEqual(result, self.tools.step(other, 'owner', review['plan'], review['sha256']))
            self.assertEqual(1, other.db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0])
            self.assertEqual(0, other.db.execute('SELECT COUNT(*) FROM approvals').fetchone()[0])
        finally: other.close()

    def test_commands_writes_unselected_paths_and_unbounded_requests_rejected_before_tasks(self):
        invalid = [[{'operation': 'execute', 'command': 'arbitrary'}], [{'operation': 'patch'}],
            [{'operation': 'read_lines', 'path': '.env', 'start': 1, 'count': 1}],
            [{'operation': 'read_lines', 'path': 'new.py', 'start': 1, 'count': 1}],
            [{'operation': 'read_lines', 'path': 'app.py', 'start': True, 'count': 1}],
            [{'operation': 'read_lines', 'path': 'app.py', 'start': 1, 'count': 201}],
            [{'operation': 'search', 'query': 'x' * 257}], [{'operation': 'inventory'}] * 2,
            [{'operation': 'search', 'query': str(n)} for n in range(5)]]
        for requests in invalid:
            with self.subTest(requests=requests):
                with self.assertRaises(BoundaryError): self.preview(requests)
        self.assertEqual(0, self.core.db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0])

    def test_revoked_resource_or_wrong_owner_cannot_prepare_or_read_results(self):
        review = self.preview()
        with self.assertRaises(Denied):
            self.tools.preview(self.core, 'other', self.project, 'workspace:demo', self.profile.name, self.requests)
        self.tools.prepare(self.core, 'owner', review['plan'], review['sha256'])
        self.tools.step(self.core, 'owner', review['plan'], review['sha256'])
        self.core.set_policy('owner', self.project, 'read_only', [])
        with self.assertRaises(Denied): self.tools.results(self.core, 'owner', review['plan'], review['sha256'])

    def test_changed_input_or_profile_blocks_before_dispatch_and_after_result(self):
        review = self.preview(); prepared = self.tools.prepare(self.core, 'owner', review['plan'], review['sha256'])
        record = self.workspace.read('app.py')
        self.workspace.patch('app.py', record['sha256'], '41', '42')
        with self.assertRaises(Conflict): self.tools.step(self.core, 'owner', review['plan'], review['sha256'])
        self.assertEqual('queued', self.core.task('owner', prepared['task'])['state'])
        self.workspace.patch('app.py', self.workspace.read('app.py')['sha256'], '42', '41')
        self.tools.step(self.core, 'owner', review['plan'], review['sha256'])
        self.worker.sandbox.profiles[self.profile.name] = replace(self.profile, timeout=31)
        with self.assertRaises(Conflict): self.tools.results(self.core, 'owner', review['plan'], review['sha256'])

    def test_all_operations_share_one_captured_hash_verified_view(self):
        expected = {path: self.workspace.read(path)['sha256'] for path in self.workspace.selected}
        # Inventory and search operate on the captured records. A change after
        # capture cannot introduce unbound text through a second per-tool read.
        original_inventory = self.workspace.inventory
        def changed_inventory(*args, **kwargs):
            result = original_inventory(*args, **kwargs)
            self.workspace.patch('app.py', self.workspace.read('app.py')['sha256'], '41', '99')
            return result
        with patch.object(self.workspace, 'inventory', side_effect=changed_inventory):
            result = self.workspace.inspect(self.requests, expected)
        self.assertEqual(expected, result['input_hashes'])
        self.assertIn('41', result['results'][1]['result']['hits'][0]['text'])
        self.assertIn('41', result['results'][2]['result']['lines'][1]['text'])
        with self.assertRaises(BoundaryError): self.workspace.inspect(self.requests, expected)

    def test_cancelled_batch_is_not_replayed(self):
        review = self.preview(); prepared = self.tools.prepare(self.core, 'owner', review['plan'], review['sha256'])
        self.core.cancel('owner', prepared['task'])
        with self.assertRaises(Conflict): self.tools.step(self.core, 'owner', review['plan'], review['sha256'])
        self.assertEqual('cancelled', self.core.task('owner', prepared['task'])['state'])
        cancelled = self.tools.results(self.core, 'owner', review['plan'], review['sha256'])
        self.assertEqual('cancelled', cancelled['state']); self.assertTrue(cancelled['recovery_required'])
        new = self.tools.preview(self.core, 'owner', self.project, 'workspace:demo', self.profile.name,
                                 self.requests, request_id='owner-approved-new-inspection')
        prepared_new = self.tools.prepare(self.core, 'owner', new['plan'], new['sha256'])
        self.assertNotEqual(prepared['task'], prepared_new['task'])
        self.assertTrue(self.tools.step(self.core, 'owner', new['plan'], new['sha256'])['complete'])

    def test_raw_worker_boundary_also_rejects_mutating_inspection_requests(self):
        task = self.core.create_task('owner', self.project, 'read', 'workspace:demo',
            {'operation': 'inspect', 'requests': [{'operation': 'create', 'path': 'new.py', 'content': 'bad'}],
             'expected_inputs': self.preview()['plan']['inputs']})
        lease = self.core.start('owner', task)
        with self.assertRaises(BoundaryError): self.worker.perform(self.core, 'owner', task, lease['lease_token'])
        self.assertFalse((self.workspace.root / 'new.py').exists())

    def test_authenticated_agent_api_reads_only_its_project_and_cannot_submit_commands(self):
        from jarvis_core.api import Credential, create_app
        from fastapi.testclient import TestClient
        credentials = [Credential(hashlib.sha256(role.ljust(40, 'x').encode()).hexdigest(), 'owner', role,
                       frozenset({self.project}) if role != 'controller' else frozenset())
                       for role in ('controller', 'agent', 'worker')]
        client = TestClient(create_app(self.database, credentials, file_worker=self.worker),
                            base_url='http://127.0.0.1', client=('127.0.0.1', 50000))
        self.addCleanup(client.close)
        headers = {'Authorization': 'Bearer ' + 'agent'.ljust(40, 'x')}
        base = f'/v1/projects/{self.project}/inspection/'
        request = {'resource': 'workspace:demo', 'profile': self.profile.name, 'requests': self.requests}
        review = client.post(base + 'preview', json=request, headers=headers)
        self.assertEqual(200, review.status_code, review.text)
        plan = {'plan': review.json()['plan'], 'expected_sha256': review.json()['sha256']}
        prepared = client.post(base + 'prepare', json=plan, headers=headers)
        self.assertEqual(200, prepared.status_code, prepared.text)
        result = client.post(base + 'step', json=plan, headers=headers)
        self.assertEqual(200, result.status_code, result.text); self.assertTrue(result.json()['complete'])
        self.assertEqual(result.json(), client.post(base + 'results', json=plan, headers=headers).json())
        denied = client.post(base + 'preview', json=request,
            headers={'Authorization': 'Bearer ' + 'worker'.ljust(40, 'x')})
        self.assertEqual(403, denied.status_code)
        for invalid in ({**request, 'command': 'execute'},
                        {**request, 'requests': [{'operation': 'execute', 'command': 'execute'}]}):
            self.assertEqual(422, client.post(base + 'preview', json=invalid, headers=headers).status_code)
        self.assertEqual(403, client.post('/v1/projects/foreign/inspection/prepare', json=plan, headers=headers).status_code)

    def test_completed_evidence_is_not_returned_after_its_input_changes(self):
        review = self.preview(); self.tools.prepare(self.core, 'owner', review['plan'], review['sha256'])
        self.tools.step(self.core, 'owner', review['plan'], review['sha256'])
        self.workspace.patch('app.py', self.workspace.read('app.py')['sha256'], '41', '42')
        with self.assertRaises(Conflict): self.tools.results(self.core, 'owner', review['plan'], review['sha256'])

    def test_plan_versions_and_resource_types_are_strict_before_storage_access(self):
        review = self.preview()
        for changed in ({'version': True}, {'version': 1.0}, {'project': []}, {'profile': 42},
                        {'operation': 'execute'}, {'inputs': []}):
            plan = {**review['plan'], **changed}
            with self.subTest(changed=changed):
                with self.assertRaises(BoundaryError):
                    self.tools.prepare(self.core, 'owner', plan, checksum(plan))
        self.assertEqual(0, self.core.db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0])
