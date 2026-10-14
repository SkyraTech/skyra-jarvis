import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from jarvis_core import Core, Conflict, Denied
from jarvis_core.store import SCHEMA
import sqlite3


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / 'core.sqlite3'
        self.now = 1000.0
        self.core = Core(self.path, clock=lambda: self.now)
        self.project = self.core.create_project('owner', 'Demo')
        self.core.set_policy('owner', self.project, 'ask', ['workspace:demo'])

    def tearDown(self):
        self.core.close()
        self.directory.cleanup()

    def task(self, action='write', resource='workspace:demo'):
        return self.core.create_task('owner', self.project, action, resource, {'file': 'example.py'})

    def restart(self):
        self.core.close()
        self.core = Core(self.path, clock=lambda: self.now)

    def test_messages_persist_and_deduplicate(self):
        c = self.core.create_conversation('owner', self.project)
        mid = self.core.append_message('owner', c, 'user', 'Hello', 'request-1')
        self.restart()
        self.assertEqual(mid, self.core.append_message('owner', c, 'user', 'Hello', 'request-1'))
        self.assertEqual(['Hello'], [m['content'] for m in self.core.messages('owner', c)])
        with self.assertRaises(Conflict):
            self.core.append_message('owner', c, 'user', 'Different', 'request-1')

    def test_actors_cannot_read_or_change_other_projects(self):
        c = self.core.create_conversation('owner', self.project)
        t = self.task()
        operations = [lambda: self.core.messages('intruder', c),
                      lambda: self.core.events('intruder', self.project),
                      lambda: self.core.task('intruder', t),
                      lambda: self.core.set_policy('intruder', self.project, 'full', ['workspace:demo']),
                      lambda: self.core.start('intruder', t)]
        for operation in operations:
            with self.assertRaises(Denied): operation()

    def test_conversations_have_separate_histories(self):
        a = self.core.create_conversation('owner', self.project)
        b = self.core.create_conversation('owner', self.project)
        self.core.append_message('owner', a, 'user', 'Private context', 'same-id')
        self.assertEqual([], self.core.messages('owner', b))

    def test_read_only_rejects_write_and_execute(self):
        self.core.set_policy('owner', self.project, 'read_only', ['workspace:demo'])
        for action in ['write', 'execute']:
            with self.assertRaises(Denied): self.core.start('owner', self.task(action))
        self.assertEqual('running', self.core.start('owner', self.task('read'))['state'])

    def test_full_access_is_still_scoped(self):
        self.core.set_policy('owner', self.project, 'full', ['workspace:demo'])
        with self.assertRaises(Denied): self.core.start('owner', self.task(resource='workspace:other'))
        self.assertEqual('running', self.core.start('owner', self.task())['state'])

    def test_approval_survives_restart_and_is_single_use(self):
        t = self.task()
        a = self.core.start('owner', t)['approval_id']
        self.restart()
        self.assertEqual(a, self.core.start('owner', t)['approval_id'])
        self.core.decide('owner', a, True)
        self.restart()
        lease = self.core.start('owner', t)['lease_token']
        with self.assertRaises(Conflict): self.core.decide('owner', a, True)
        with self.assertRaises(Conflict): self.core.start('owner', t)
        self.core.complete('owner', t, lease, ['artifact:test-report'])
        self.assertEqual('succeeded', self.core.task('owner', t)['state'])

    def test_approval_does_not_authorize_another_action(self):
        a = self.core.start('owner', self.task())['approval_id']
        self.core.decide('owner', a, True)
        self.assertEqual('waiting_approval', self.core.start('owner', self.task('execute'))['state'])

    def test_expired_approval_requires_new_decision(self):
        t = self.task()
        a = self.core.start('owner', t)['approval_id']
        self.now += 301
        with self.assertRaises(Conflict): self.core.decide('owner', a, True)
        self.assertNotEqual(a, self.core.start('owner', t)['approval_id'])

    def test_policy_revision_invalidates_approval(self):
        t = self.task()
        a = self.core.start('owner', t)['approval_id']
        self.core.decide('owner', a, True)
        self.core.set_policy('owner', self.project, 'ask', ['workspace:demo'])
        self.assertNotEqual(a, self.core.start('owner', t)['approval_id'])

    def test_rejected_approval_cancels_task(self):
        t = self.task()
        a = self.core.start('owner', t)['approval_id']
        self.core.decide('owner', a, False)
        with self.assertRaises(Conflict): self.core.start('owner', t)
        self.assertEqual('cancelled', self.core.task('owner', t)['state'])

    def test_expired_worker_requires_reconciliation(self):
        t = self.task('read')
        lease = self.core.start('owner', t)['lease_token']
        self.restart()
        self.assertEqual(0, self.core.recover_expired('owner', self.project))
        self.now += 61
        self.assertEqual(1, self.core.recover_expired('owner', self.project))
        with self.assertRaises(Conflict): self.core.start('owner', t)
        with self.assertRaises(Conflict): self.core.complete('owner', t, lease, ['old-result'])
        self.core.reconcile('owner', t, 'retry', ['verified:no-effects'])
        self.assertNotEqual(lease, self.core.start('owner', t)['lease_token'])

    def test_cancelled_running_work_remains_uncertain(self):
        t = self.task('read')
        lease = self.core.start('owner', t)['lease_token']
        self.core.cancel('owner', t)
        self.assertEqual('cancellation_requested', self.core.task('owner', t)['state'])
        with self.assertRaises(Conflict): self.core.complete('owner', t, lease, ['report'])
        self.now += 61
        self.core.recover_expired('owner', self.project)
        with self.assertRaises(Conflict): self.core.reconcile('owner', t, 'retry', ['report'])
        self.core.reconcile('owner', t, 'cancelled', ['verified:worker-stopped'])
        self.assertEqual('cancelled', self.core.task('owner', t)['state'])

    def test_policy_revocation_blocks_active_worker(self):
        t = self.task('read')
        lease = self.core.start('owner', t)['lease_token']
        self.core.set_policy('owner', self.project, 'read_only', [])
        with self.assertRaises(Denied): self.core.heartbeat('owner', t, lease)
        with self.assertRaises(Denied): self.core.complete('owner', t, lease, ['report'])

    def test_events_replay_without_duplicate_side_effects(self):
        c = self.core.create_conversation('owner', self.project)
        previous = self.core.events('owner', self.project)[-1]['id']
        self.core.append_message('owner', c, 'user', 'Hello', '1')
        self.core.append_message('owner', c, 'user', 'Hello', '1')
        self.restart()
        events = self.core.events('owner', self.project, previous)
        self.assertEqual(['message.appended'], [e['kind'] for e in events])
        self.assertNotIn('Hello', str(events))

    def test_concurrent_claim_has_one_owner(self):
        t = self.task('read')
        def claim(_):
            core = Core(self.path, clock=lambda: self.now)
            try:
                return core.start('owner', t)['state']
            except Conflict:
                return 'conflict'
            finally:
                core.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertCountEqual(['running', 'conflict'], list(pool.map(claim, range(2))))

    def test_completion_requires_evidence(self):
        t = self.task('read')
        lease = self.core.start('owner', t)['lease_token']
        with self.assertRaises(ValueError): self.core.complete('owner', t, lease, [])
        self.assertEqual('running', self.core.task('owner', t)['state'])

    def test_state_and_event_roll_back_together(self):
        count = self.core.db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0]
        with patch.object(self.core, '_event', side_effect=RuntimeError('storage fault')):
            with self.assertRaises(RuntimeError): self.task()
        self.assertEqual(count, self.core.db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0])

    def test_lease_heartbeat_checks_owner_and_expiry(self):
        t = self.task('read')
        lease = self.core.start('owner', t)['lease_token']
        with self.assertRaises(Conflict): self.core.heartbeat('owner', t, 'wrong-token')
        self.now += 30
        self.core.heartbeat('owner', t, lease)
        self.now += 40
        self.assertEqual(0, self.core.recover_expired('owner', self.project))
        self.now += 21
        with self.assertRaises(Conflict): self.core.heartbeat('owner', t, lease)

    def test_approval_rechecked_against_changed_payload_digest(self):
        t = self.task()
        a = self.core.start('owner', t)['approval_id']
        self.core.decide('owner', a, True)
        # Simulate a trusted-host revision: public task API intentionally has no mutation method.
        self.core.db.execute('UPDATE tasks SET digest=? WHERE id=?', ('changed-action-digest', t))
        self.assertNotEqual(a, self.core.start('owner', t)['approval_id'])

    def test_v1_database_migration_preserves_existing_project(self):
        path = Path(self.directory.name) / 'old.sqlite3'
        old = sqlite3.connect(path)
        for statement in SCHEMA:
            old.execute(statement)
        old.execute("INSERT INTO projects VALUES('old','owner','Existing','read_only',1,'[]')")
        old.execute('PRAGMA user_version=1')
        old.commit()
        old.close()
        migrated = Core(path)
        try:
            self.assertEqual('Existing', migrated.projects('owner')[0]['name'])
            self.assertEqual(2, migrated.db.execute('PRAGMA user_version').fetchone()[0])
            first = migrated.create_task('owner', 'old', 'read', 'workspace:demo', {}, 'request')
            self.assertEqual(first, migrated.create_task('owner', 'old', 'read', 'workspace:demo', {}, 'request'))
        finally:
            migrated.close()


if __name__ == '__main__':
    unittest.main()
