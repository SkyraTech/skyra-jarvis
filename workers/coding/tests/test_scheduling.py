"""One-time scheduled builds: no early effects, bounded admission, restart and consent."""
import hashlib
import json
import os
import time
import unittest
from unittest.mock import patch
import test_build_jobs
from jarvis_core import Core, Conflict
from jarvis_core.operations import inbox
from jarvis_core.api import Credential, create_app
from fastapi.testclient import TestClient

@unittest.skipUnless(os.name=='nt','Windows native scheduled workflow')
class SchedulingTests(unittest.TestCase):
    setUp=test_build_jobs.BuildJobTests.setUp
    tearDown=test_build_jobs.BuildJobTests.tearDown
    create=test_build_jobs.BuildJobTests.create
    tick=test_build_jobs.BuildJobTests.tick
    finish=test_build_jobs.BuildJobTests.finish
    def schedule(self,**kwargs):
        return self.create(start_at=1200,start_window_seconds=60,**kwargs)
    def test_future_job_has_no_tasks_calls_or_attempts_before_start(self):
        job=self.schedule()
        self.assertEqual(4800,job['deadline']);self.assertEqual(1200,job['next_due'])
        for _ in range(4):self.assertIsNone(self.tick())
        self.assertEqual(0,self.provider.calls)
        self.assertEqual(0,self.core.db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0])
        self.assertEqual(0,self.core.db.execute('SELECT COUNT(*) FROM build_attempts').fetchone()[0])
    def test_real_scheduled_fail_repair_pass_survives_core_restart(self):
        job=self.schedule();self.core.close();self.core=Core(self.database,clock=lambda:self.now)
        self.assertIsNone(self.tick());self.now=1200
        result=self.finish();self.assertEqual('completed',result['state'],result)
        self.assertEqual(1,result['calls']);self.assertEqual('ready_for_review',self.workflow.get(self.core,'owner',result['run'])['state'])
        self.assertIn('return 41',(self.source/'app.py').read_text())
        notice=inbox(self.core,'owner',self.project)['notices'][0]['snapshot']
        self.assertEqual(1200,notice['schedule']['start_at'])
    def test_missed_start_fails_without_execution_or_generation(self):
        self.schedule();self.now=1261
        result=self.tick();self.assertEqual('failed',result['state'])
        self.assertEqual('scheduled_start_missed',result['summary']['reason'])
        self.assertEqual((0,0),(result['steps'],result['calls']))
        self.assertEqual(0,self.core.db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0])
    def test_edited_selected_input_blocks_and_cannot_be_resumed_without_new_review(self):
        job=self.schedule();(self.workspace.root/'app.py').write_text('def answer():\n    return 40\n')
        self.now=1200;result=self.tick()
        self.assertEqual('blocked',result['state']);self.assertEqual('scheduled_inputs_changed',result['summary']['reason'])
        self.assertEqual(0,result['steps']);self.assertEqual(0,self.provider.calls)
        with self.assertRaises(Conflict):self.jobs.control(self.core,'owner',job['id'],'resume')
    def test_pause_resume_before_due_does_not_start_early(self):
        job=self.schedule();self.jobs.control(self.core,'owner',job['id'],'pause')
        result=self.jobs.control(self.core,'owner',job['id'],'resume')
        self.assertEqual(1200,result['next_due']);self.assertIsNone(self.tick())
        self.assertEqual(0,self.provider.calls)
    def test_cancelled_scheduled_job_never_starts(self):
        job=self.schedule();self.jobs.control(self.core,'owner',job['id'],'cancel')
        self.now=1200;self.assertIsNone(self.tick())
        self.assertEqual('cancelled',self.jobs.get(self.core,'owner',job['id'])['state'])
        self.assertEqual(0,self.provider.calls)
    def test_replayed_creation_recovers_same_job_after_start_and_input_edit(self):
        job=self.schedule();self.now=1300
        (self.workspace.root/'app.py').write_text('Changed after review')
        self.assertEqual(job['id'],self.schedule()['id'])
        with self.assertRaises(Conflict):self.schedule(goal='Different intent')
    def test_changed_specification_blocks_before_baseline(self):
        spec={'project':self.project,'state':'approved','sha256':'a'*64}
        with patch('jarvis_core.specifications.get',return_value=spec):self.schedule(specification='approved-spec')
        self.now=1200
        with patch('jarvis_core.specifications.get',return_value={**spec,'state':'superseded'}):result=self.tick()
        self.assertEqual('scheduled_specification_changed',result['summary']['reason'])
        self.assertEqual(0,result['steps']);self.assertEqual(0,self.provider.calls)
    def test_due_ask_mode_wait_remains_governed_after_admission_window(self):
        self.core.set_policy('owner',self.project,'ask',['workspace:fixture'])
        self.schedule(auto_accept=False);self.now=1200
        result=self.tick();self.assertEqual('waiting_approval',result['state'])
        self.now=1280;result=self.tick();self.assertEqual('waiting_approval',result['state'])
        self.assertEqual(0,self.provider.calls)
    def test_invalid_time_and_window_never_create_job(self):
        for start,window in [(1000,60),(1001+604800,60),(1200,59),(1200,86401),(True,60),(1200,False)]:
            with self.assertRaises(ValueError):self.create(start_at=start,start_window_seconds=window)
        self.assertEqual(0,self.core.db.execute('SELECT COUNT(*) FROM build_jobs').fetchone()[0])
    def test_controller_schedule_and_worker_contact_api_are_separate_authorities(self):
        tokens={'controller':'c'*40,'worker':'w'*40,'agent':'a'*40}
        credentials=[Credential(hashlib.sha256(token.encode()).hexdigest(),'owner',role,frozenset() if role=='controller' else frozenset({self.project})) for role,token in tokens.items()]
        with TestClient(create_app(self.database,credentials,file_worker=self.worker,repair_runtime=self.runtime,unattended_enabled=True),base_url='http://127.0.0.1',client=('127.0.0.1',50000)) as client:
            def call(method,path,role='controller',body=None):return client.request(method,path,json=body,headers={'Authorization':'Bearer '+tokens[role]})
            path='/v1/projects/'+self.project+'/operations'
            self.assertEqual('never_seen',call('GET',path).json()['runner_contact']['state'])
            self.assertEqual(403,call('POST','/v1/runner/tick',body={'project':self.project}).status_code)
            body=dict(resource='workspace:fixture',profile='unit',provider='fixture',goal='Future repair',files=['app.py','tests/test_app.py'],skills=[],max_calls=1,max_cycles=1,max_steps=20,duration_seconds=3600,auto_accept=True,allow_model_calls=True,request_id='schedule-api',start_at=int(time.time())+300,start_window_seconds=60)
            for role in ('worker','agent'):self.assertEqual(403,call('POST','/v1/projects/'+self.project+'/build-jobs',role,body).status_code)
            result=call('POST','/v1/projects/'+self.project+'/build-jobs',body=body)
            self.assertEqual(201,result.status_code,result.text)
            self.assertEqual(422,call('POST','/v1/projects/'+self.project+'/build-jobs',body={**body,'start_at':True}).status_code)
            self.assertEqual(200,call('POST','/v1/runner/tick','worker',{'project':self.project}).status_code)
            contact=call('GET',path).json()['runner_contact'];self.assertEqual('recent',contact['state']);self.assertEqual('responded',contact['outcome'])
            self.assertEqual(0,self.provider.calls)

    def test_pending_baseline_approval_does_not_release_the_selected_input_binding(self):
        self.core.set_policy('owner',self.project,'ask',['workspace:fixture'])
        self.schedule(auto_accept=False);self.now=1200
        self.assertEqual('waiting_approval',self.tick()['state'])
        (self.workspace.root/'app.py').write_text('def answer():\n    return 40\n')
        self.now=1280;result=self.tick()
        self.assertEqual('blocked',result['state']);self.assertEqual('scheduled_inputs_changed',result['summary']['reason'])
        self.assertEqual(0,result['calls']);self.assertEqual(0,self.core.db.execute('SELECT COUNT(*) FROM build_attempts WHERE outcome NOT IN (\'waiting_approval\')').fetchone()[0])

    def test_new_manual_run_blocks_scheduled_admission_until_owner_resolves_it(self):
        job=self.schedule()
        run=test_build_jobs.test_workflow.WorkflowTests.create(self)
        self.now=1200;result=self.tick()
        self.assertEqual('blocked',result['state']);self.assertEqual('scheduled_workspace_busy',result['summary']['reason'])
        self.assertIsNone(result['baseline_task']);self.assertEqual(0,result['calls'])
        self.workflow.cancel(self.core,'owner',run)
        self.jobs.control(self.core,'owner',job['id'],'resume')
        self.assertEqual('completed',self.finish()['state'])
