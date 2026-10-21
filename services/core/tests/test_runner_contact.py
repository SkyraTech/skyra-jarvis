import sys
from pathlib import Path
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from jarvis_core import Core, Denied
from jarvis_core.runner_contact import begin, finish, read

class RunnerContactTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'core.sqlite3';self.now=1000.
        self.core=Core(self.path,clock=lambda:self.now);self.project=self.core.create_project('owner','Runner')
    def tearDown(self):self.core.close();self.temp.cleanup()
    def test_idle_busy_stale_and_restart_are_distinct(self):
        self.assertEqual('never_seen',read(self.core,'owner',self.project)['state'])
        attempt=begin(self.core,'owner',self.project);self.now+=300
        self.assertEqual('in_progress',read(self.core,'owner',self.project)['state'])
        self.now+=361;self.assertEqual('stale',read(self.core,'owner',self.project)['state'])
        finish(self.core,self.project,attempt,'responded');self.assertEqual('recent',read(self.core,'owner',self.project)['state'])
        self.core.close();self.core=Core(self.path,clock=lambda:self.now)
        self.assertEqual('responded',read(self.core,'owner',self.project)['outcome'])
        self.now+=181;self.assertEqual('stale',read(self.core,'owner',self.project)['state'])
    def test_old_response_cannot_overwrite_newer_request(self):
        old=begin(self.core,'owner',self.project);self.now+=1;new=begin(self.core,'owner',self.project)
        finish(self.core,self.project,old,'responded');self.assertIsNone(read(self.core,'owner',self.project)['finished'])
        finish(self.core,self.project,new,'error');self.assertEqual('error',read(self.core,'owner',self.project)['outcome'])
    def test_owner_scope_does_not_grant_actions_or_resources(self):
        with self.assertRaises(Denied):begin(self.core,'other',self.project)
        with self.assertRaises(Denied):read(self.core,'other',self.project)
        self.assertEqual('read_only',self.core._owned('owner',self.project)['mode'])
        self.assertEqual(0,self.core.db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0])
    def test_migration_13_preserves_existing_history(self):
        conversation=self.core.create_conversation('owner',self.project)
        self.core.append_message('owner',conversation,'user','Preserved','message')
        self.core.db.execute('DROP TABLE runner_contacts');self.core.db.execute('PRAGMA user_version=13')
        self.core.close();self.core=Core(self.path)
        self.assertEqual(15,self.core.db.execute('PRAGMA user_version').fetchone()[0])
        self.assertEqual('Preserved',self.core.messages('owner',conversation)[0]['content'])
        self.assertEqual('never_seen',read(self.core,'owner',self.project)['state'])
