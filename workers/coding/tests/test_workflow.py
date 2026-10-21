import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest

REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'services/core/src'))
sys.path.insert(0,str(REPO/'workers/coding/src'))
from fastapi.testclient import TestClient
from jarvis_core import Core,Conflict,Denied
from jarvis_core.api import Credential,create_app
from skyra_coding import Workspace,FileWorker,BoundaryError
from skyra_coding.native import NativeExecutor,NativeProfile
from skyra_coding.workflow import CodingWorkflow


@unittest.skipUnless(os.name=='nt','Native Windows workflow')
class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.source=self.root/'source';self.source.mkdir();(self.source/'tests').mkdir()
        (self.source/'app.py').write_text('def answer():\n    return 41\n',encoding='utf-8')
        test='import sys,unittest\nfrom pathlib import Path\nsys.path.insert(0,str(Path(__file__).resolve().parents[1]))\nfrom app import answer\nclass TestAnswer(unittest.TestCase):\n    def test_answer(self):self.assertEqual(42,answer())\n'
        (self.source/'tests/test_app.py').write_text(test,encoding='utf-8')
        self.workspace=Workspace.snapshot(self.source,self.root/'snapshot',['app.py','tests/test_app.py'])
        self.database=self.root/'core.sqlite3';self.core=Core(self.database)
        self.project=self.core.create_project('owner','Repair fixture')
        self.core.set_policy('owner',self.project,'full',['workspace:fixture'])
        profile=NativeProfile('unit',(sys.executable,'-I','-B','-m','unittest','discover','-s','tests','-v'),('tests/test_app.py',),10)
        self.executor=NativeExecutor([profile],owner_enabled=True)
        self.worker=FileWorker({(self.project,'workspace:fixture'):self.workspace},self.root/'evidence',self.executor)
        self.workflow=CodingWorkflow(self.worker)

    def tearDown(self):self.core.close();self.temp.cleanup()

    def create(self,new='42'):
        return self.workflow.create(self.core,'owner',self.project,'workspace:fixture','unit',[
            {'path':'app.py','expected_sha256':self.workspace.read('app.py')['sha256'],'old':'41','new':new}])

    def test_real_fail_repair_pass_and_diff_survive_restart(self):
        run=self.create()
        first=self.workflow.advance(self.core,'owner',run)
        self.assertTrue(first['results'][0]['expectation_met'])
        self.assertEqual('failed',first['results'][0]['state'])
        self.core.close();self.core=Core(self.database)
        self.assertEqual(1,self.workflow.get(self.core,'owner',run)['position'])
        for _ in range(3):result=self.workflow.advance(self.core,'owner',run)
        self.assertEqual('ready_for_review',result['state'],result)
        self.assertEqual(['failed','succeeded','succeeded','succeeded'],[r['state'] for r in result['results']])
        final_test=self.worker.evidence(result['results'][2]['evidence'][0])['result']
        self.assertIn('Ran 1 test',final_test['output']);self.assertEqual(0,final_test['exit_code'])
        diff=self.worker.evidence(result['results'][3]['evidence'][0])['result']
        self.assertEqual(['app.py'],[r['path'] for r in diff['changes']])
        self.assertIn('return 41',(self.source/'app.py').read_text())

    def test_failed_repair_never_becomes_ready(self):
        run=self.create(new='40')
        for _ in range(3):result=self.workflow.advance(self.core,'owner',run)
        self.assertEqual('failed',result['state'])
        self.assertEqual(3,len(result['results']))

    def test_feature_baseline_rejects_inconsistent_adapter_evidence(self):
        from unittest.mock import patch
        run=self.workflow.create(self.core,'owner',self.project,'workspace:fixture','unit',[
            {'path':'app.py','expected_sha256':self.workspace.read('app.py')['sha256'],'old':'41','new':'42'}],
            mode='feature')
        original=self.worker.evidence
        def inconsistent(reference):
            record=original(reference)
            record['result']['exit_code']=0
            record['result']['passed']=True
            return record
        with patch.object(self.worker,'evidence',side_effect=inconsistent):
            result=self.workflow.advance(self.core,'owner',run)
        self.assertEqual('failed',result['state'])
        self.assertFalse(result['results'][0]['expectation_met'])
        self.assertIn('return 41',self.workspace.read('app.py')['content'])

    def test_cannot_weaken_protected_tests(self):
        with self.assertRaises(BoundaryError):self.workflow.create(self.core,'owner',self.project,'workspace:fixture','unit',[
            {'path':'tests/test_app.py','expected_sha256':self.workspace.read('tests/test_app.py')['sha256'],'old':'42','new':'41'}])

    def test_execution_cannot_dispatch_twice_on_same_lease(self):
        task=self.core.create_task('owner',self.project,'execute','workspace:fixture',{'operation':'test','profile':'unit'})
        token=self.core.start('owner',task)['lease_token']
        self.core.begin_execution('owner',task,token)
        self.core.close();self.core=Core(self.database)
        with self.assertRaises(Conflict):self.core.begin_execution('owner',task,token)

    def test_unknown_cleanup_stays_interrupted(self):
        task=self.core.create_task('owner',self.project,'execute','workspace:fixture',{'operation':'test','profile':'unit'})
        token=self.core.start('owner',task)['lease_token']
        self.core.begin_execution('owner',task,token)
        self.assertEqual('interrupted',self.core.settle_execution('owner',task,token,['report'],True,False))
        with self.assertRaises(Conflict):self.core.start('owner',task)

    def test_cancelled_run_is_not_advanced(self):
        run=self.create();self.workflow.cancel(self.core,'owner',run)
        self.assertEqual('cancelled',self.workflow.advance(self.core,'owner',run)['state'])

    def test_api_pipeline_requires_controller_plan_and_step_approvals(self):
        self.core.set_policy('owner',self.project,'ask',['workspace:fixture'])
        tokens={role:role+'_'+'z'*40 for role in ('controller','agent','worker')}
        credentials=[Credential(hashlib.sha256(value.encode()).hexdigest(),'owner',role,
                     frozenset() if role=='controller' else frozenset({self.project})) for role,value in tokens.items()]
        app=create_app(self.database,credentials,self.worker)
        with TestClient(app,base_url='http://127.0.0.1',client=('127.0.0.1',50000)) as client:
            def call(method,path,role='controller',body=None):
                return client.request(method,path,headers={'Authorization':'Bearer '+tokens[role]},json=body)
            body={'resource':'workspace:fixture','profile':'unit','request_id':'repair-fixture','patches':[
                {'path':'app.py','expected_sha256':self.workspace.read('app.py')['sha256'],'old':'41','new':'42'}]}
            self.assertEqual(403,call('POST',f'/v1/projects/{self.project}/coding-runs','agent',body).status_code)
            response=call('POST',f'/v1/projects/{self.project}/coding-runs',body=body)
            self.assertEqual(201,response.status_code,response.text);run=response.json()['run_id']
            self.assertEqual(run,call('POST',f'/v1/projects/{self.project}/coding-runs',body=body).json()['run_id'])
            self.assertEqual(run,call('GET',f'/v1/projects/{self.project}/coding-runs','agent').json()['runs'][0]['id'])
            result=None
            for _ in range(10):
                response=call('POST',f'/v1/coding-runs/{run}/advance','worker')
                self.assertEqual(200,response.status_code,response.text);result=response.json()
                if result['state']=='waiting_approval':
                    task=result['task'];approval=call('POST',f'/v1/tasks/{task}/start','worker').json()['approval_id']
                    self.assertEqual(403,call('POST',f'/v1/approvals/{approval}/decision','agent',{'approve':True}).status_code)
                    self.assertEqual(200,call('POST',f'/v1/approvals/{approval}/decision',body={'approve':True}).status_code)
                if result['state']=='ready_for_review':break
            self.assertEqual('ready_for_review',result['state'],result)


if __name__=='__main__':unittest.main()
