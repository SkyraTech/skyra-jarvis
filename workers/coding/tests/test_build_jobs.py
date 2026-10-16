"""Generated native fixtures; deterministic models, no external requests."""
import json
import os
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

import test_workflow
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'packages/agent-runtime/src'))
from jarvis_core import Core, Conflict, Denied
from jarvis_core.build_jobs import BuildJobs, checksum
from jarvis_core.assignments import Assignments
from jarvis_core.api import Credential, create_app
from fastapi.testclient import TestClient
import hashlib
from jarvis_runtime import RepairRuntime


class Provider:
    provider='fixture'; model='fixture-repair'; timeout=1; max_output_tokens=256
    def __init__(self, answers=(42,)):
        self.answers=answers; self.calls=0; self.contexts=[]
    def complete(self, system, context, schema):
        data=json.loads(context); self.contexts.append(data)
        answer=self.answers[min(self.calls,len(self.answers)-1)]; self.calls+=1
        source=next(f for f in data['files'] if f['path']=='app.py')
        old=next(line.strip() for line in source['content'].splitlines() if 'return ' in line)
        return json.dumps({'summary':'Fixture repair','patches':[{'path':'app.py','expected_sha256':source['sha256'],
                   'old':old,'new':'return '+str(answer)}]}), {'input_tokens':100,'output_tokens':40,'total_tokens':140}


@unittest.skipUnless(os.name=='nt','Native Windows workflow')
class BuildJobTests(unittest.TestCase):
    tearDown=test_workflow.WorkflowTests.tearDown
    def setUp(self):
        test_workflow.WorkflowTests.setUp(self)
        self.now=1000.0; self.core.clock=lambda:self.now
        self.provider=Provider(); self.runtime=RepairRuntime(self.worker,{'fixture':self.provider})
        self.jobs=BuildJobs(self.runtime)
    def create(self, **overrides):
        args=dict(resource='workspace:fixture',profile='unit',provider='fixture',goal='Make answer return 42',
                  files=['app.py','tests/test_app.py'],skills=[],max_calls=2,max_cycles=2,max_steps=30,
                  duration_seconds=3600,auto_accept=True,allow_model_calls=True,request_id='build')
        args.update(overrides)
        return self.jobs.create(self.core,'owner',self.project,**args)
    def tick(self):
        self.now+=6
        return self.jobs.tick(self.core,'owner',self.project)['build_job']
    def finish(self, limit=30):
        result=None
        for _ in range(limit):
            result=self.tick()
            if result and result['state'] in {'completed','failed','blocked','budget_limited','cancelled'}: return result
        self.fail(str(result))

    def test_real_baseline_model_patch_retest_and_diff(self):
        self.create(); result=self.finish()
        self.assertEqual('completed',result['state'],result)
        self.assertEqual(1,result['calls']); self.assertEqual(1,self.provider.calls)
        self.assertEqual('ready_for_review',self.workflow.get(self.core,'owner',result['run'])['state'])
        self.assertIn('return 41',(self.source/'app.py').read_text())
        self.assertEqual(1,len(result['cycles']))
        self.assertEqual('completed',result['cycles'][0]['state'])
        self.assertIn('FAILED',self.provider.contexts[0]['diagnostics']['output'])
        self.assertEqual(1,self.provider.contexts[0]['diagnostics']['exit_code'])

    def test_failed_retest_drives_second_model_cycle_with_current_hashes(self):
        self.provider.answers=(40,42)
        self.create(); result=self.finish()
        self.assertEqual('completed',result['state'],result)
        self.assertEqual(2,result['calls']); self.assertEqual(2,len(result['cycles']))
        self.assertIn('return 40',self.provider.contexts[1]['files'][0]['content'])
        self.assertIn('42 != 40',self.provider.contexts[1]['diagnostics']['output'])
        self.assertEqual('failed_retest',result['cycles'][0]['state'])
        self.assertIn('return 42',self.workspace.read('app.py')['content'])

    def test_call_budget_stops_failed_repair_without_replay(self):
        self.provider.answers=(40,42)
        self.create(max_calls=1); result=self.finish()
        self.assertEqual('budget_limited',result['state']); self.assertEqual(1,self.provider.calls)
        self.assertIsNone(self.tick())

    def test_passing_baseline_uses_no_model_calls(self):
        (self.workspace.root/'app.py').write_text('def answer():\n    return 42\n')
        self.create(); result=self.finish()
        self.assertEqual('completed',result['state']); self.assertEqual(0,self.provider.calls)
        self.assertEqual('baseline_passed_no_repair',result['summary']['reason'])

    def test_model_consent_and_full_policy_are_not_implicit(self):
        with self.assertRaises(ValueError): self.create(allow_model_calls=False)
        self.core.set_policy('owner',self.project,'ask',['workspace:fixture'])
        with self.assertRaises(Denied): self.create(auto_accept=True)

    def test_exact_proposal_review_and_separate_action_approvals(self):
        self.core.set_policy('owner',self.project,'ask',['workspace:fixture'])
        job=self.create(auto_accept=False); approvals=0; reviewed=False
        for _ in range(35):
            result=self.tick()
            if result['state']=='waiting_approval':
                task=result['baseline_task'] if result['phase']=='baseline' else self.workflow.get(self.core,'owner',result['run'])['task']
                approval=self.core.start('owner',task)['approval_id']; self.core.decide('owner',approval,True); approvals+=1
            if result['state']=='waiting_review':
                proposal=self.runtime.get(self.core,'owner',result['proposal'])
                with self.assertRaises(Conflict): self.jobs.accept(self.core,'owner',job['id'],'0'*64,checksum(proposal['response']))
                self.jobs.accept(self.core,'owner',job['id'],proposal['context_sha256'],checksum(proposal['response'])); reviewed=True
            if result['state']=='completed': break
        self.assertEqual('completed',result['state'],result); self.assertTrue(reviewed); self.assertEqual(4,approvals)

    def test_unknown_billable_dispatch_survives_restart_without_replay(self):
        job=self.create(); self.tick()
        def crash(*args): self.provider.calls+=1; raise KeyboardInterrupt('unknown provider outcome')
        with patch.object(self.provider,'complete',side_effect=crash):
            with self.assertRaises(KeyboardInterrupt): self.tick()
        self.now+=601; self.core.close(); self.core=Core(self.database,clock=lambda:self.now)
        self.assertIsNone(self.tick())
        result=self.jobs.get(self.core,'owner',job['id'])
        self.assertEqual('blocked',result['state']); self.assertEqual(1,result['calls']); self.assertEqual(1,self.provider.calls)
        with self.assertRaises(Conflict): self.jobs.control(self.core,'owner',job['id'],'resume')
        self.jobs.control(self.core,'owner',job['id'],'cancel')
        self.assertEqual('interrupted',self.runtime.get(self.core,'owner',result['proposal'])['state'])

    def test_step_budget_prevents_paid_generation(self):
        self.create(max_steps=1); self.tick(); result=self.tick()
        self.assertEqual('budget_limited',result['state']); self.assertEqual(0,self.provider.calls)

    def test_request_identity_and_changed_binding(self):
        job=self.create(); self.assertEqual(job['id'],self.create()['id'])
        with self.assertRaises(Conflict): self.create(max_calls=1)
        self.provider.model='changed-model'
        self.assertEqual('blocked',self.tick()['state']); self.assertEqual(0,self.provider.calls)

    def test_schedulers_share_one_project_dispatch_slot(self):
        self.create(); self.tick(); complete=self.provider.complete
        def nested(*args):
            self.assertIsNone(Assignments(self.workflow).tick(self.core,'owner',self.project)['assignment'])
            self.assertIsNone(self.jobs.tick(self.core,'owner',self.project)['build_job'])
            return complete(*args)
        with patch.object(self.provider,'complete',side_effect=nested): self.tick()
        self.assertEqual(1,self.provider.calls)

    def test_changed_test_inputs_block_before_external_context_is_sent(self):
        self.create(); self.tick()
        (self.workspace.root/'app.py').write_text('def answer():\n    return 39\n')
        self.assertEqual('blocked',self.tick()['state']); self.assertEqual(0,self.provider.calls)

    def test_policy_downgrade_removes_automatic_acceptance(self):
        self.create(); self.tick(); self.tick()
        self.core.set_policy('owner',self.project,'ask',['workspace:fixture'])
        result=self.tick()
        self.assertEqual('waiting_review',result['state']); self.assertIsNone(result['run'])
        self.assertEqual(1,self.provider.calls)

    def test_cancel_suppresses_late_model_output_without_refunding_the_call(self):
        job=self.create(); self.tick(); complete=self.provider.complete
        def cancel(*args):
            self.jobs.control(self.core,'owner',job['id'],'cancel')
            return complete(*args)
        with patch.object(self.provider,'complete',side_effect=cancel): result=self.tick()
        self.assertEqual('cancelled',result['state']); self.assertEqual(1,result['calls'])
        self.assertIsNone(result['run']); self.assertIn('return 41',self.workspace.read('app.py')['content'])

    def test_provider_failure_is_charged_once_and_not_retried(self):
        self.create(); self.tick()
        with patch.object(self.provider,'complete',side_effect=OSError('private provider failure')):
            result=self.tick()
        self.assertEqual('failed',result['state']); self.assertEqual(1,result['calls'])
        self.assertEqual('generation_failed',result['summary']['reason'])
        self.assertIsNone(self.tick())

    def test_api_job_creation_review_and_reads_preserve_role_boundaries(self):
        tokens={role:role+'_'+'z'*40 for role in ('controller','worker')}
        credentials=[Credential(hashlib.sha256(token.encode()).hexdigest(),'owner',role,
                     frozenset() if role=='controller' else frozenset({self.project})) for role,token in tokens.items()]
        with TestClient(create_app(self.database,credentials,self.worker,self.runtime,unattended_enabled=True),
                        base_url='http://127.0.0.1',client=('127.0.0.1',50000)) as client:
            def call(method,path,role='controller',body=None):
                return client.request(method,path,headers={'Authorization':'Bearer '+tokens[role]},json=body)
            body=dict(resource='workspace:fixture',profile='unit',provider='fixture',goal='Repair answer',
                      files=['app.py','tests/test_app.py'],skills=[],max_calls=1,max_cycles=1,max_steps=20,
                      duration_seconds=3600,auto_accept=False,allow_model_calls=True,request_id='http')
            url=f'/v1/projects/{self.project}/build-jobs'
            self.assertEqual(403,call('POST',url,'worker',body).status_code)
            self.assertEqual(422,call('POST',url,body={**body,'allow_model_calls':False}).status_code)
            response=call('POST',url,body=body); self.assertEqual(201,response.status_code,response.text)
            job=response.json()['id']
            self.assertEqual(403,call('GET',f'/v1/build-jobs/{job}','worker').status_code)
            self.assertEqual(200,call('POST','/v1/runner/tick','worker',{'project':self.project}).status_code)
            self.assertEqual(403,call('POST',f'/v1/build-jobs/{job}/accept-proposal','worker',{'context_sha256':'a'*64,'response_sha256':'a'*64}).status_code)
        with TestClient(create_app(self.database,credentials),base_url='http://127.0.0.1',client=('127.0.0.1',50000)) as client:
            response=client.get(f'/v1/build-jobs/{job}',headers={'Authorization':'Bearer '+tokens['controller']})
            self.assertEqual(200,response.status_code,response.text)

    def test_schema_ten_migration_preserves_existing_assignments(self):
        run=test_workflow.WorkflowTests.create(self)
        assignment=Assignments(self.workflow).create(self.core,'owner',self.project,run,'Preserve queued work',10,3600,'old')
        self.core.db.execute('DROP TABLE runner_contacts')
        self.core.db.execute('DROP TABLE operation_notices')
        self.core.db.execute('DROP TABLE scaffold_registrations')
        self.core.db.execute('DROP TABLE build_attempts')
        self.core.db.execute('DROP TABLE build_cycles')
        self.core.db.execute('DROP TABLE build_jobs')
        self.core.db.execute('PRAGMA user_version=10')
        self.core.close(); self.core=Core(self.database,clock=lambda:self.now)
        self.assertEqual(14,self.core.db.execute('PRAGMA user_version').fetchone()[0])
        self.assertEqual('Preserve queued work',Assignments(self.workflow).get(self.core,'owner',assignment['id'])['goal'])
        self.assertEqual(1,Assignments(self.workflow).tick(self.core,'owner',self.project)['assignment']['steps'])

    def test_saved_ready_proposal_recovers_without_reserving_another_call(self):
        job=self.create(max_calls=1); self.tick(); update=self.jobs._update
        def crash_after_response(core, job_id, **fields):
            if fields.get('phase')=='review': raise KeyboardInterrupt('crash after durable response')
            return update(core,job_id,**fields)
        with patch.object(self.jobs,'_update',side_effect=crash_after_response):
            with self.assertRaises(KeyboardInterrupt): self.tick()
        self.now+=601; self.tick()
        self.jobs.control(self.core,'owner',job['id'],'resume')
        result=self.finish()
        self.assertEqual('completed',result['state'],result)
        self.assertEqual(1,result['calls']); self.assertEqual(1,self.provider.calls)

    def test_rejected_baseline_approval_cancels_without_a_model_request(self):
        self.core.set_policy('owner',self.project,'ask',['workspace:fixture'])
        self.create(auto_accept=False); result=self.tick()
        approval=self.core.start('owner',result['baseline_task'])['approval_id']
        self.core.decide('owner',approval,False)
        self.assertEqual('cancelled',self.tick()['state']); self.assertEqual(0,self.provider.calls)

    def test_interrupted_reviewed_proposal_blocks_the_job_without_another_call(self):
        self.create(auto_accept=False); self.tick(); self.tick(); result=self.tick()
        self.assertEqual('waiting_review',result['state'])
        self.runtime.interrupt(self.core,'owner',result['proposal'])
        self.assertEqual('blocked',self.tick()['state']); self.assertEqual(1,self.provider.calls)

    def test_inconsistent_test_result_cannot_trigger_a_model_call(self):
        self.create(); result=self.tick(); task=result['baseline_task']
        data=self.core.task('owner',task)
        report=self.worker.evidence(json.loads(data['evidence'])[0])['result']
        report['passed']=True  # Simulate an adapter that contradicts its nonzero exit.
        forged=self.worker._report(task,'test',report)
        self.core.db.execute('UPDATE tasks SET evidence=? WHERE id=?',(json.dumps(forged['evidence']),task))
        self.assertEqual('blocked',self.tick()['state']); self.assertEqual(0,self.provider.calls)


if __name__=='__main__': unittest.main()
