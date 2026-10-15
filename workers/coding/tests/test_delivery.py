"""Real tested fixtures, never developer source targets."""
import json
import hashlib
import os
import shutil
import unittest
from dataclasses import replace
from unittest.mock import patch

import test_workflow
from jarvis_core import Conflict, Denied
from skyra_coding import FileWorker, Workspace
from skyra_coding.workflow import CodingWorkflow
from fastapi.testclient import TestClient
from jarvis_core.api import Credential, create_app


@unittest.skipUnless(os.name == 'nt', 'Native Windows workflow')
class DeliveryTests(unittest.TestCase):
    setUp = test_workflow.WorkflowTests.setUp
    tearDown = test_workflow.WorkflowTests.tearDown
    create = test_workflow.WorkflowTests.create

    def ready(self):
        self.core.set_policy('owner', self.project, 'full', ['workspace:fixture', 'source:fixture'])
        self.worker = self.register(self.source)
        self.workflow = CodingWorkflow(self.worker)
        run = self.create()
        for _ in range(4):
            result = self.workflow.advance(self.core, 'owner', run)
        self.assertEqual('ready_for_review', result['state'])
        return run

    def register(self, source):
        return FileWorker({(self.project, 'workspace:fixture'): self.workspace},
                          self.root/'evidence', self.executor,
                          [{'project_id': self.project, 'resource_id': 'source:fixture',
                            'workspace_resource': 'workspace:fixture', 'directory': str(source)}])

    def prepared(self, run):
        preview = self.worker.delivery.preview(self.core, 'owner', run, 'source:fixture')
        return self.worker.delivery.prepare(self.core, 'owner', run, 'source:fixture', preview['sha256'], 'one')

    def apply(self, task):
        claim = self.core.start('owner', task['id'])
        self.worker.perform(self.core, 'owner', task['id'], claim['lease_token'])
        return self.worker.delivery.status(self.core, 'owner', task['id'])

    def test_verified_delivery_and_idempotent_prepare(self):
        run = self.ready()
        task = self.prepared(run)
        self.assertEqual(task['id'], self.prepared(run)['id'])
        result = self.apply(task)
        self.assertEqual('succeeded', result['state'])
        self.assertIn('return 42', (self.source/'app.py').read_text())
        report = self.worker.evidence(result['evidence'][0])['result']
        record = json.loads((self.root/'evidence'/report['recovery_record']/'journal.json').read_text())
        self.assertEqual('delivered', record['state'])
        self.assertIn('return 41', (self.root/'evidence'/report['recovery_record']/'before/app.py').read_text())

    def test_changed_source_blocks_without_overwrite(self):
        run = self.ready(); task = self.prepared(run)
        (self.source/'app.py').write_text('owner edit\n')
        result = self.apply(task)
        self.assertEqual('failed', result['state'])
        self.assertEqual('owner edit\n', (self.source/'app.py').read_text())

    def test_target_reconfiguration_invalidates_reviewed_task(self):
        run = self.ready(); task = self.prepared(run)
        other = self.root/'other-source'; shutil.copytree(self.source, other)
        self.worker = self.register(other)
        self.assertEqual('failed', self.apply(task)['state'])
        self.assertIn('return 41', (other/'app.py').read_text())

    def test_changed_snapshot_rejects_preview(self):
        run = self.ready()
        (self.workspace.root/'app.py').write_text('unverified\n')
        with self.assertRaises(Conflict):
            self.worker.delivery.preview(self.core, 'owner', run, 'source:fixture')

    def test_revoked_source_grant_rejects_review(self):
        run = self.ready()
        self.core.set_policy('owner', self.project, 'full', ['workspace:fixture'])
        with self.assertRaises(Denied):
            self.worker.delivery.preview(self.core, 'owner', run, 'source:fixture')

    def test_failed_replace_retains_source_and_recovery_record(self):
        run = self.ready(); task = self.prepared(run)
        real_replace = os.replace
        def fail_source(src, dst):
            if str(dst) == str(self.source/'app.py'):
                raise OSError('simulated source write failure')
            return real_replace(src, dst)
        with patch('skyra_coding.delivery.os.replace', side_effect=fail_source):
            result = self.apply(task)
        self.assertEqual('failed', result['state'])
        self.assertIn('return 41', (self.source/'app.py').read_text())
        report = self.worker.evidence(result['evidence'][0])['result']
        record = json.loads((self.root/'evidence'/report['recovery_record']/'journal.json').read_text())
        self.assertEqual('blocked_or_partial', record['state'])
        self.assertEqual('app.py', record['next'])

    def test_workspace_cannot_be_registered_as_source(self):
        with self.assertRaises(ValueError):
            self.register(self.workspace.directory)

    def test_changed_test_profile_invalidates_evidence(self):
        run = self.ready()
        profile = self.executor.profiles['unit']
        self.executor.profiles['unit'] = replace(profile, timeout=profile.timeout+1)
        with self.assertRaises(Conflict):
            self.worker.delivery.preview(self.core, 'owner', run, 'source:fixture')

    def test_api_delivery_requires_controller_review_and_worker_execution(self):
        run = self.ready()
        tokens = {role: role+'_'+'z'*40 for role in ('controller', 'agent', 'worker')}
        credentials = [Credential(hashlib.sha256(token.encode()).hexdigest(), 'owner', role,
                       frozenset() if role == 'controller' else frozenset({self.project}))
                       for role, token in tokens.items()]
        with TestClient(create_app(self.database, credentials, self.worker),
                        base_url='http://127.0.0.1', client=('127.0.0.1', 50000)) as client:
            def call(path, role, body=None):
                return client.post(path, headers={'Authorization': 'Bearer '+tokens[role]}, json=body)
            url = f'/v1/coding-runs/{run}/delivery-preview'
            self.assertEqual(403, call(url, 'agent', {'target': 'source:fixture'}).status_code)
            preview = call(url, 'controller', {'target': 'source:fixture'})
            self.assertEqual(200, preview.status_code, preview.text)
            body = {'target': 'source:fixture', 'expected_sha256': preview.json()['sha256'], 'request_id': 'api'}
            prepared = call(f'/v1/coding-runs/{run}/deliveries', 'controller', body)
            self.assertEqual(201, prepared.status_code, prepared.text)
            url = f'/v1/deliveries/{prepared.json()["id"]}/advance'
            self.assertEqual(403, call(url, 'controller').status_code)
            result = call(url, 'worker')
            self.assertEqual(200, result.status_code, result.text)
            self.assertEqual('succeeded', result.json()['state'])

    def test_ask_policy_requires_separate_source_approval(self):
        run = self.ready()
        self.core.set_policy('owner', self.project, 'ask', ['workspace:fixture', 'source:fixture'])
        task = self.prepared(run)
        claim = self.core.start('owner', task['id'])
        self.assertEqual('waiting_approval', claim['state'])
        self.assertIn('return 41', (self.source/'app.py').read_text())
        self.core.decide('owner', claim['approval_id'], True)
        self.assertEqual('succeeded', self.apply(task)['state'])

    def test_partial_multifile_delivery_is_explicit_and_not_replayed(self):
        (self.source/'extra.py').write_text('VALUE = 1\n')
        self.workspace = Workspace.snapshot(self.source, self.root/'multi-snapshot',
                                            ['app.py', 'extra.py', 'tests/test_app.py'])
        self.core.set_policy('owner', self.project, 'full', ['workspace:fixture', 'source:fixture'])
        self.worker = self.register(self.source); self.workflow = CodingWorkflow(self.worker)
        run = self.workflow.create(self.core, 'owner', self.project, 'workspace:fixture', 'unit', [
            {'path': 'app.py', 'expected_sha256': self.workspace.read('app.py')['sha256'], 'old': '41', 'new': '42'},
            {'path': 'extra.py', 'expected_sha256': self.workspace.read('extra.py')['sha256'], 'old': '1', 'new': '2'}])
        for _ in range(5): result = self.workflow.advance(self.core, 'owner', run)
        self.assertEqual('ready_for_review', result['state'])
        task = self.prepared(run); real_replace = os.replace
        def fail_second(src, dst):
            if str(dst) == str(self.source/'extra.py'): raise OSError('second write failed')
            return real_replace(src, dst)
        with patch('skyra_coding.delivery.os.replace', side_effect=fail_second):
            result = self.apply(task)
        report = self.worker.evidence(result['evidence'][0])['result']
        self.assertEqual('blocked_or_partial', report['state'])
        self.assertEqual(['app.py'], report['written'])
        self.assertIn('return 42', (self.source/'app.py').read_text())
        self.assertEqual('VALUE = 1\n', (self.source/'extra.py').read_text())
        with self.assertRaises(Conflict): self.core.start('owner', task['id'])


if __name__ == '__main__':
    unittest.main()
