"""Project activity is an owned, read-only projection of live leases and recorded work."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from jarvis_core import Core, Denied
from jarvis_core.activity import snapshot
from jarvis_core.store import identifier


class ActivityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'core.sqlite3'
        self.now=1000.;self.core=Core(self.path,clock=lambda:self.now)
        self.project=self.core.create_project('owner','Visible project')
        self.core.set_policy('owner',self.project,'full',['workspace:demo'])
    def tearDown(self):self.core.close();self.temp.cleanup()
    def task(self,action):
        task=self.core.create_task('owner',self.project,action,'workspace:demo',{'private':'SECRET_CONTEXT'},identifier())
        self.core.start('owner',task)
        return task
    def test_owned_live_leases_are_scoped_private_and_read_only(self):
        for action in ('execute','write','read'):self.task(action)
        before=self.core.db.total_changes
        result=snapshot(self.core,'owner',self.project)
        self.assertEqual([1,1,1],[result['counts'][k] for k in ('testing','coding','inspecting')])
        self.assertEqual(before,self.core.db.total_changes)
        self.assertNotIn('SECRET',json.dumps(result));self.assertNotIn('lease_token',json.dumps(result))
        other=self.core.create_project('owner','Other')
        self.assertFalse(any(snapshot(self.core,'owner',other)['counts'].values()))
        with self.assertRaises(Denied):snapshot(self.core,'foreign',self.project)
    def test_expired_and_uncertain_tasks_never_look_live_after_restart(self):
        self.task('execute');self.now+=61
        self.core.close();self.core=Core(self.path,clock=lambda:self.now)
        result=snapshot(self.core,'owner',self.project)['counts']
        self.assertEqual(0,result['testing']);self.assertEqual(1,result['blocked'])
        self.core.recover_expired('owner',self.project)
        self.assertEqual(1,snapshot(self.core,'owner',self.project)['counts']['blocked'])
    def test_cancel_request_is_stopping_and_historical_failure_is_not_live(self):
        task=self.task('execute');self.core.cancel('owner',task)
        counts=snapshot(self.core,'owner',self.project)['counts']
        self.assertEqual(1,counts['stopping']);self.assertEqual(0,counts['testing'])
        self.core.db.execute("UPDATE tasks SET state='failed',lease_until=NULL WHERE id=?",(task,))
        self.assertFalse(any(snapshot(self.core,'owner',self.project)['counts'].values()))
    def test_expired_or_old_policy_approvals_do_not_signal_actionable_review(self):
        self.core.set_policy('owner',self.project,'ask',['workspace:demo'])
        task=self.core.create_task('owner',self.project,'write','workspace:demo',{},identifier())
        self.core.start('owner',task)
        self.assertEqual(1,snapshot(self.core,'owner',self.project)['counts']['approvals'])
        self.core.set_policy('owner',self.project,'ask',['workspace:demo'])
        self.assertEqual(0,snapshot(self.core,'owner',self.project)['counts']['approvals'])
        self.assertEqual('waiting_approval',self.core.task('owner',task)['state'])
        self.core.start('owner',task);self.now+=301
        self.assertEqual(0,snapshot(self.core,'owner',self.project)['counts']['approvals'])

    def test_pending_model_modes_are_counts_without_context_or_health_claims(self):
        for mode in ('chat','plan'):
            conversation=self.core.create_conversation('owner',self.project)
            message=self.core.append_message('owner',conversation,'user','SECRET_MODEL_INPUT',identifier())
            self.core.db.execute("INSERT INTO model_turns(id,conversation,project,request_id,digest,provider,model,mode,state,context,user_message,created) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (identifier(),conversation,self.project,identifier(),'digest','fixture','fixture',mode,'generating','{"private":"SECRET_CONTEXT"}',message,1000))
        result=snapshot(self.core,'owner',self.project)
        self.assertEqual(1,result['counts']['planning_requests']);self.assertEqual(1,result['counts']['chat_requests'])
        self.assertNotIn('SECRET',json.dumps(result));self.assertIn('not provider health',result['interpretation'])

    def test_linked_job_review_is_not_counted_again_as_standalone_proposal(self):
        proposal=identifier()
        self.core.db.execute("INSERT INTO repair_proposals(id,project,request_id,digest,resource,profile,provider,model,state,context,created) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (proposal,self.project,identifier(),'digest','workspace:demo','unit','fixture','fixture','ready','{}',1000))
        self.assertEqual(1,snapshot(self.core,'owner',self.project)['counts']['reviews'])
        job=identifier()
        self.core.db.execute("INSERT INTO build_jobs(id,project,request_id,digest,config,goal,state,phase,cycle,calls,steps,deadline,next_due,summary,created,updated,proposal) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (job,self.project,identifier(),'digest','{}','SECRET_GOAL','waiting_review','review',1,1,2,2000,1000,'{}',1000,1000,proposal))
        self.assertEqual(1,snapshot(self.core,'owner',self.project)['counts']['reviews'])
        self.core.db.execute("UPDATE build_jobs SET state='completed' WHERE id=?",(job,))
        self.assertEqual(0,snapshot(self.core,'owner',self.project)['counts']['reviews'])


if __name__=='__main__':unittest.main()
