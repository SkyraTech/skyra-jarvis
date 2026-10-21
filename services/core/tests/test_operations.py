import hashlib
import json
import sys
import tempfile
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from jarvis_core import Core, Denied
from jarvis_core.store import encode, identifier
from jarvis_core.operations import inbox, acknowledge, status
from jarvis_core.api import create_app, Credential
from fastapi.testclient import TestClient

class OperationsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'core.sqlite3'
        self.now=1000.;self.core=Core(self.path,clock=lambda:self.now)
        self.project=self.core.create_project('owner','Operations')
    def tearDown(self):
        self.core.close();self.temp.cleanup()
    def job(self,state='waiting_review',reason='review_exact_proposal'):
        job=identifier();cfg={'resource':'workspace:demo','max_steps':20,'max_calls':2}
        with self.core.transaction():
            self.core.db.execute("INSERT INTO build_jobs(id,project,request_id,digest,config,goal,state,phase,cycle,calls,steps,deadline,next_due,summary,created,updated) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(job,self.project,job,'digest',encode(cfg),'Build client portal',state,'review',1,1,3,2000,1000,encode({'reason':reason,'output':'secret log not for inbox'}),1000,1000))
            self.core._event(self.project,'build_job.'+state,job)
        return job
    def test_wait_dedup_and_acknowledgement_survive_restart(self):
        job=self.job();notice=inbox(self.core,'owner',self.project)['notices'][0]
        self.now+=10
        with self.core.transaction(): self.core._event(self.project,'build_job.waiting_review',job)
        self.assertEqual(1,inbox(self.core,'owner',self.project)['unread'])
        first=acknowledge(self.core,'owner',notice['id']);self.now+=10
        self.assertEqual(first,acknowledge(self.core,'owner',notice['id']))
        self.core.close();self.core=Core(self.path)
        self.assertEqual(0,inbox(self.core,'owner',self.project)['unread'])
        self.assertEqual(1,len(inbox(self.core,'owner',self.project)['notices']))
    def test_snapshot_is_immutable_and_new_attention_is_unread(self):
        job=self.job();old=inbox(self.core,'owner',self.project)['notices'][0]
        acknowledge(self.core,'owner',old['id'])
        with self.core.transaction():
            self.core.db.execute("UPDATE build_jobs SET state='blocked',summary=? WHERE id=?",(encode({'reason':'runner_interrupted'}),job))
            self.core._event(self.project,'build_job.interrupted',job)
        result=inbox(self.core,'owner',self.project)
        self.assertEqual(1,result['unread']);self.assertEqual('blocked',result['notices'][0]['snapshot']['state'])
        self.assertEqual(old['snapshot'],result['notices'][1]['snapshot'])
        self.assertNotIn('secret log',encode(result));self.assertNotIn('output',result['notices'][0]['snapshot'])
    def test_ack_never_changes_policy_job_or_tasks(self):
        job=self.job();before=dict(self.core.db.execute('SELECT * FROM build_jobs WHERE id=?',(job,)).fetchone())
        notice=inbox(self.core,'owner',self.project)['notices'][0]
        with self.assertRaises(Denied): acknowledge(self.core,'outsider',notice['id'])
        with self.assertRaises(Denied): inbox(self.core,'outsider',self.project)
        acknowledge(self.core,'owner',notice['id'])
        self.assertEqual(before,dict(self.core.db.execute('SELECT * FROM build_jobs WHERE id=?',(job,)).fetchone()))
        self.assertEqual('read_only',self.core._owned('owner',self.project)['mode'])
        self.assertEqual(0,self.core.db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0])
    def test_keyset_pagination_has_no_duplicates_and_counts_all_unread(self):
        for _ in range(53): self.job('completed','tested_repair_ready')
        first=inbox(self.core,'owner',self.project);second=inbox(self.core,'owner',self.project,first['next_before'])
        self.assertEqual(50,len(first['notices']));self.assertEqual(3,len(second['notices']))
        self.assertEqual(53,second['unread']);self.assertIsNone(second['next_before'])
        self.assertFalse({n['id'] for n in first['notices']} & {n['id'] for n in second['notices']})
    def test_event_and_notice_rollback_together(self):
        job=self.job('queued','queued')
        with self.assertRaises(RuntimeError):
            with self.core.transaction():
                self.core.db.execute("UPDATE build_jobs SET state='completed' WHERE id=?",(job,))
                self.core._event(self.project,'build_job.completed',job)
                raise RuntimeError('rollback')
        self.assertEqual([],inbox(self.core,'owner',self.project)['notices'])
        self.assertEqual('queued',status(self.core,'owner',self.project)[0]['state'])
    def test_migration_12_backfills_current_outcomes_without_losing_history(self):
        self.job('completed','tested_repair_ready')
        conversation=self.core.create_conversation('owner',self.project)
        self.core.append_message('owner',conversation,'user','Keep this message','keep')
        self.core.db.execute('DROP TABLE runner_contacts')
        self.core.db.execute('DROP TABLE operation_notices');self.core.db.execute('PRAGMA user_version=12')
        self.core.close();self.core=Core(self.path)
        self.assertEqual(15,self.core.db.execute('PRAGMA user_version').fetchone()[0])
        self.assertEqual(1,inbox(self.core,'owner',self.project)['unread'])
        self.assertEqual(1000.,inbox(self.core,'owner',self.project)['notices'][0]['created'])
        self.assertEqual('Keep this message',self.core.messages('owner',conversation)[0]['content'])
        self.core.close();self.core=Core(self.path)
        self.assertEqual(1,inbox(self.core,'owner',self.project)['unread'])
    def test_budget_stops_and_expired_work_remain_visible(self):
        self.job('budget_limited','model_call_budget');self.now=3000
        work=status(self.core,'owner',self.project)
        self.assertEqual('budget_limited',work[0]['state']);self.assertTrue(work[0]['expired'])
        self.assertEqual('separate_review_required',inbox(self.core,'owner',self.project)['notices'][0]['snapshot']['source_delivery'])
    def test_controller_api_scope_and_read_without_execution_runtime(self):
        self.job();notice=inbox(self.core,'owner',self.project)['notices'][0]
        tokens={'controller':'c'*40,'worker':'w'*40,'agent':'a'*40,'outsider':'o'*40}
        credentials=[Credential(hashlib.sha256(token.encode()).hexdigest(),'outsider' if role=='outsider' else 'owner','controller' if role=='outsider' else role,frozenset() if role in {'controller','outsider'} else frozenset({self.project})) for role,token in tokens.items()]
        with TestClient(create_app(self.path,credentials),base_url='http://127.0.0.1',client=('127.0.0.1',50000)) as client:
            def call(method,path,role='controller'):
                return client.request(method,path,headers={'Authorization':'Bearer '+tokens[role]})
            path='/v1/projects/'+self.project+'/operations'
            data=call('GET',path).json();self.assertFalse(data['host_enabled']);self.assertEqual([],data['library'])
            for role in ('worker','agent','outsider'):
                self.assertEqual(403,call('GET',path,role).status_code)
                self.assertEqual(403,call('POST','/v1/operations/'+notice['id']+'/acknowledge',role).status_code)
            self.assertEqual(422,call('GET',path+'?before=-1').status_code)
            self.assertEqual(422,call('GET',path+'?before='+str(2**64)).status_code)
            self.assertEqual(200,call('POST','/v1/operations/'+notice['id']+'/acknowledge').status_code)
            self.assertEqual(0,call('GET',path).json()['unread'])

    def test_assignment_evidence_snapshot_excludes_raw_results_and_repeated_waits(self):
        run=identifier();assignment=identifier();ref='sha256:'+'a'*64
        with self.core.transaction():
            self.core.db.execute('INSERT INTO coding_runs(id,project,resource,plan,owner,state,position,task,results) VALUES(?,?,?,?,?,?,?,?,?)',(run,self.project,'workspace:demo','[]','owner','ready_for_review',4,None,encode([{'task_id':'test','state':'succeeded','evidence':[ref],'output':'private test stdout'}])))
            self.core.db.execute('INSERT INTO assignments(id,project,run,request_id,digest,goal,state,max_steps,steps,deadline,next_due,summary,created,updated) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(assignment,self.project,run,assignment,'digest','Accepted overnight repair','completed',20,4,2000,1000,encode({'reason':'ready_for_review'}),1000,1000))
            self.core._event(self.project,'assignment.completed',assignment)
        item=inbox(self.core,'owner',self.project)['notices'][0]['snapshot']
        self.assertEqual('assignment',item['lane']);self.assertEqual([ref],item['evidence'])
        self.assertEqual(0,item['calls']);self.assertNotIn('private test stdout',encode(item))

    def test_cancel_request_does_not_claim_running_effects_are_cancelled(self):
        job=self.job('running','queued')
        with self.core.transaction(): self.core._event(self.project,'build_job.cancel',job)
        self.assertEqual([],inbox(self.core,'owner',self.project)['notices'])
        with self.core.transaction():
            self.core.db.execute("UPDATE build_jobs SET state='cancelled' WHERE id=?",(job,))
            self.core._event(self.project,'build_job.cancel',job)
        item=inbox(self.core,'owner',self.project)['notices'][0]['snapshot']
        self.assertEqual('cancelled',item['state']);self.assertEqual('owner_cancel',item['reason'])

    def test_renewed_approval_gets_new_notice_but_same_pending_request_is_quiet(self):
        job=self.job('queued','queued')
        self.core.set_policy('owner',self.project,'ask',['workspace:demo'])
        task=self.core.create_task('owner',self.project,'execute','workspace:demo',{'operation':'test'})
        first=self.core.start('owner',task)['approval_id']
        with self.core.transaction():
            self.core.db.execute("UPDATE build_jobs SET state='waiting_approval',baseline_task=? WHERE id=?",(task,job))
            self.core._event(self.project,'build_job.waiting_approval',job)
        with self.core.transaction(): self.core._event(self.project,'build_job.waiting_approval',job)
        self.assertEqual(1,inbox(self.core,'owner',self.project)['unread'])
        self.now+=301
        second=self.core.start('owner',task)['approval_id'];self.assertNotEqual(first,second)
        with self.core.transaction(): self.core._event(self.project,'build_job.waiting_approval',job)
        notices=inbox(self.core,'owner',self.project)['notices']
        self.assertEqual(2,len(notices));self.assertEqual(second,notices[0]['snapshot']['approval']['id'])
        self.assertEqual(first,notices[1]['snapshot']['approval']['id'])
