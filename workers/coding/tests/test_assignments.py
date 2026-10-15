"""Durable unattended progression with real Windows test subprocesses."""
import hashlib
import os
import unittest
from unittest.mock import patch

import test_workflow
from jarvis_core import Core, Conflict, Denied
from jarvis_core.assignments import Assignments
from jarvis_core.api import Credential, create_app
from fastapi.testclient import TestClient


@unittest.skipUnless(os.name == 'nt', 'Native Windows workflow')
class AssignmentTests(unittest.TestCase):
    tearDown = test_workflow.WorkflowTests.tearDown
    create = test_workflow.WorkflowTests.create

    def setUp(self):
        test_workflow.WorkflowTests.setUp(self)
        self.now = 1000.0
        self.core.clock = lambda: self.now
        self.assignments = Assignments(self.workflow)
        self.run = self.create()

    def assignment(self, steps=10, duration=3600):
        return self.assignments.create(self.core, 'owner', self.project, self.run,
                                       'Fix answer and verify protected tests', steps, duration, 'overnight')

    def tick(self):
        self.now += 6
        return self.assignments.tick(self.core, 'owner', self.project)

    def test_automatic_workflow_reaches_review_with_evidence_and_source_unchanged(self):
        job = self.assignment()
        for _ in range(4): result = self.tick()['assignment']
        self.assertEqual('completed', result['state'])
        self.assertEqual(4, result['steps'])
        self.assertEqual(4, len(result['summary']['results']))
        self.assertEqual(0, result['summary']['model_calls'])
        self.assertIn('return 41', (self.source/'app.py').read_text())
        self.assertIsNone(self.tick()['assignment'])
        self.assertEqual('completed', self.assignments.get(self.core, 'owner', job['id'])['state'])

    def test_approval_wait_does_not_consume_step_budget(self):
        self.core.set_policy('owner', self.project, 'ask', ['workspace:fixture'])
        self.assignment()
        for _ in range(3):
            result = self.tick()['assignment']
            self.assertEqual('waiting_approval', result['state'])
            self.assertEqual(0, result['steps'])
        run = self.workflow.get(self.core, 'owner', self.run)
        approval = self.core.start('owner', run['task'])['approval_id']
        self.core.decide('owner', approval, True)
        self.assertEqual(1, self.tick()['assignment']['steps'])

    def test_pause_resume_and_cancel_are_durable(self):
        job = self.assignment()
        self.assertEqual('paused', self.assignments.control(self.core, 'owner', job['id'], 'pause')['state'])
        self.assertIsNone(self.tick()['assignment'])
        self.core.close(); self.core = Core(self.database, clock=lambda: self.now)
        self.assignments.control(self.core, 'owner', job['id'], 'resume')
        self.assertEqual(1, self.tick()['assignment']['steps'])
        self.assertEqual('cancelled', self.assignments.control(self.core, 'owner', job['id'], 'cancel')['state'])
        self.assertEqual('cancelled', self.workflow.get(self.core, 'owner', self.run)['state'])

    def test_deadline_and_step_budget_stop_before_next_dispatch(self):
        job = self.assignment(steps=1)
        self.tick()
        self.assertEqual('budget_limited', self.tick()['assignment']['state'])
        self.assertEqual(1, self.workflow.get(self.core, 'owner', self.run)['position'])
        with self.assertRaises(Conflict): self.assignments.control(self.core, 'owner', job['id'], 'resume')

    def test_expired_deadline_never_starts_a_task(self):
        self.assignment(duration=60); self.now += 61
        self.assertEqual('budget_limited', self.tick()['assignment']['state'])
        self.assertIsNone(self.workflow.get(self.core, 'owner', self.run)['task'])

    def test_request_deduplication_and_exclusive_run(self):
        job = self.assignment()
        self.assertEqual(job['id'], self.assignment()['id'])
        with self.assertRaises(Conflict): self.assignment(steps=5)
        with self.assertRaises(Conflict):
            self.assignments.create(self.core, 'owner', self.project, self.run, 'Another', 10, 3600, 'other')
        with self.assertRaises(Denied): self.assignments.get(self.core, 'other-owner', job['id'])

    def test_restart_after_uncertain_dispatch_blocks_replay(self):
        job = self.assignment(steps=1)
        def crash(*args): raise KeyboardInterrupt('simulated process death')
        with patch.object(self.workflow, 'advance', side_effect=crash):
            with self.assertRaises(KeyboardInterrupt): self.tick()
        self.core.close(); self.now += 601
        self.core = Core(self.database, clock=lambda: self.now)
        result = self.tick()
        self.assertEqual(1, result['recovered'])
        self.assertEqual('blocked', self.assignments.get(self.core, 'owner', job['id'])['state'])
        self.assertIsNone(self.workflow.get(self.core, 'owner', self.run)['task'])
        self.assertEqual(1, self.assignments.get(self.core, 'owner', job['id'])['steps'])
        with self.assertRaises(Conflict): self.assignments.control(self.core, 'owner', job['id'], 'resume')

    def test_pause_during_dispatch_stops_at_next_checkpoint(self):
        job = self.assignment(); advance = self.workflow.advance
        def pause_then_advance(*args):
            self.assignments.control(self.core, 'owner', job['id'], 'pause')
            return advance(*args)
        with patch.object(self.workflow, 'advance', side_effect=pause_then_advance):
            result = self.tick()['assignment']
        self.assertEqual('paused', result['state'])
        self.assertEqual(1, result['steps'])
        self.assertIsNone(self.tick()['assignment'])

    def test_second_tick_cannot_dispatch_while_project_claim_is_active(self):
        self.assignment(); advance = self.workflow.advance
        def concurrent_tick(*args):
            self.assertIsNone(self.tick()['assignment'])
            return advance(*args)
        with patch.object(self.workflow, 'advance', side_effect=concurrent_tick):
            self.assertEqual(1, self.tick()['assignment']['steps'])
        self.assertEqual(1, self.core.db.execute('SELECT count(*) FROM assignment_attempts').fetchone()[0])

    def test_pending_approval_polls_do_not_create_more_attempts(self):
        self.core.set_policy('owner', self.project, 'ask', ['workspace:fixture'])
        self.assignment()
        for _ in range(4): self.tick()
        self.assertEqual(1, self.core.db.execute('SELECT count(*) FROM assignment_attempts').fetchone()[0])

    def test_rejected_approval_cancels_without_advancing_or_editing(self):
        self.core.set_policy('owner', self.project, 'ask', ['workspace:fixture'])
        self.assignment(); self.tick()
        run = self.workflow.get(self.core, 'owner', self.run)
        approval = self.core.start('owner', run['task'])['approval_id']
        self.core.decide('owner', approval, False)
        self.assertEqual('cancelled', self.tick()['assignment']['state'])
        self.assertIn('return 41', (self.source/'app.py').read_text())

    def test_host_disabled_assignment_creation_and_ticks_are_unavailable(self):
        token = 'controller_'+'z'*40
        credentials = [Credential(hashlib.sha256(token.encode()).hexdigest(), 'owner', 'controller')]
        with TestClient(create_app(self.database, credentials, self.worker),
                        base_url='http://127.0.0.1', client=('127.0.0.1', 50000)) as client:
            body = {'run': self.run, 'goal': 'Verify', 'max_steps': 10, 'duration_seconds': 3600, 'request_id': 'disabled'}
            response = client.post(f'/v1/projects/{self.project}/assignments', headers={'Authorization': 'Bearer '+token}, json=body)
            self.assertEqual(503, response.status_code)
            self.assertEqual(0, self.core.db.execute('SELECT count(*) FROM assignments').fetchone()[0])

    def test_revoked_policy_blocks_instead_of_bypassing_permission(self):
        self.assignment(); self.core.set_policy('owner', self.project, 'read_only', ['workspace:fixture'])
        result = self.tick()['assignment']
        self.assertEqual('blocked', result['state'])
        self.assertEqual(0, result['steps'])

    def test_uncertain_task_outcome_keeps_reserved_budget_without_checkpoint(self):
        self.assignment(steps=1)
        def uncertain(*args):
            task = self.core.create_task('owner', self.project, 'execute', 'workspace:fixture', {'operation': 'test', 'profile': 'unit'})
            self.core.db.execute("UPDATE tasks SET state='interrupted' WHERE id=?", (task,))
            self.core.db.execute("UPDATE coding_runs SET task=?,state='blocked' WHERE id=?", (task, self.run))
            return self.workflow.get(self.core, 'owner', self.run)
        with patch.object(self.workflow, 'advance', side_effect=uncertain):
            result = self.tick()['assignment']
        self.assertEqual('blocked', result['state'])
        self.assertEqual(1, result['steps'])
        self.assertEqual(0, result['summary']['position'])
        self.assertEqual('interrupted', result['summary']['task_state'])
        self.assertTrue(result['summary']['step_slot_uncertain'])

    def test_api_worker_cannot_create_or_control_assignments(self):
        tokens = {role: role+'_'+'z'*40 for role in ('controller', 'agent', 'worker')}
        credentials = [Credential(hashlib.sha256(token.encode()).hexdigest(), 'owner', role,
                       frozenset() if role == 'controller' else frozenset({self.project}))
                       for role, token in tokens.items()]
        with TestClient(create_app(self.database, credentials, self.worker, unattended_enabled=True),
                        base_url='http://127.0.0.1', client=('127.0.0.1', 50000)) as client:
            def call(path, role, body):
                return client.post(path, headers={'Authorization': 'Bearer '+tokens[role]}, json=body)
            url = f'/v1/projects/{self.project}/assignments'
            body = {'run': self.run, 'goal': 'Verify accepted repair', 'max_steps': 10, 'duration_seconds': 3600, 'request_id': 'api'}
            self.assertEqual(403, call(url, 'worker', body).status_code)
            response = call(url, 'controller', body)
            self.assertEqual(201, response.status_code, response.text)
            control = f'/v1/assignments/{response.json()["id"]}/control'
            self.assertEqual(403, call(control, 'worker', {'action': 'resume'}).status_code)
            self.assertEqual(403, call('/v1/runner/tick', 'controller', {'project': self.project}).status_code)
            self.assertEqual(403, call('/v1/runner/tick', 'worker', {'project': 'outside'}).status_code)
            self.assertEqual(200, call('/v1/runner/tick', 'worker', {'project': self.project}).status_code)


if __name__ == '__main__': unittest.main()
