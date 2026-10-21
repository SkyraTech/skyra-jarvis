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
from jarvis_runtime import RepairRuntime, Skill


class Provider:
    provider='fixture'; model='fixture-repair'; timeout=1; max_output_tokens=256
    def __init__(self, answers=(42,)):
        self.answers=answers; self.calls=0; self.contexts=[]
    def complete(self, system, context, schema):
        data=json.loads(context); self.contexts.append(data)
        answer=self.answers[min(self.calls,len(self.answers)-1)]; self.calls+=1
        source=next(f for f in data['files'] if f['path']=='app.py')
        old=next(line.strip() for line in source['content'].splitlines() if 'return ' in line)
        edit={'path':'app.py','old':old,'new':'return '+str(answer)}
        if data.get('edit_protocol')!='host-bound-v2':edit['expected_sha256']=source['sha256']
        return json.dumps({'summary':'Fixture repair','patches':[edit]}), {'input_tokens':100,'output_tokens':40,'total_tokens':140}


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

    def review_fixture(self):
        job = self.create(auto_accept=False)
        for _ in range(8):
            job = self.tick()
            if job['state'] == 'waiting_review': break
        self.assertEqual('waiting_review', job['state'])
        proposal = self.runtime.get(self.core, 'owner', job['proposal'])
        return job, proposal

    def revise_fixture(self, job, proposal, **overrides):
        args = dict(proposal_id=proposal['id'], context_sha256=proposal['context_sha256'],
                    response_sha256=checksum(proposal['response']), feedback='Please correct the edge cases.', allow_model_call=True)
        args.update(overrides)
        return self.jobs.request_revision(self.core, 'owner', job['id'], **args)

    def test_review_correction_preserves_history_scope_and_call_budget(self):
        job, proposal = self.review_fixture()
        corrected = self.revise_fixture(job, proposal)
        self.assertEqual(1, corrected['calls'])
        self.assertEqual(2, corrected['cycle'])
        self.assertEqual('rejected_review', corrected['cycles'][0]['state'])
        self.assertEqual(proposal['id'], corrected['cycles'][0]['proposal'])
        self.assertEqual(corrected['id'], self.revise_fixture(job, proposal)['id'])
        self.core.close(); self.core = Core(self.database, clock=lambda: self.now)
        result = self.tick()
        result = self.tick() if result['state'] != 'waiting_review' else result
        self.assertEqual('waiting_review', result['state'], result)
        self.assertEqual(2, self.provider.calls)
        review = self.provider.contexts[-1]['diagnostics']['proposal_review']
        self.assertEqual(proposal['response'], review['previous_response'])
        self.assertEqual('Please correct the edge cases.', review['feedback'])
        with self.assertRaises(Conflict):
            self.revise_fixture(result, self.runtime.get(self.core, 'owner', result['proposal']))
        self.assertIn('return 41', (self.workspace.root/'app.py').read_text())
        self.assertIsNone(result['run'])

    def pending_correction_fixture(self):
        self.provider.answers = (40, 42)
        job = self.create()
        for _ in range(20):
            job = self.tick()
            if job['calls'] == 1 and job['cycle'] == 2 and job['phase'] == 'propose': break
        self.assertEqual('queued',job['state'],job)
        self.assertEqual('propose',job['phase'],job)
        digest = checksum({path:self.workspace.read(path)['sha256'] for path in self.workspace.selected})
        return job,digest

    def test_pending_failed_retest_review_reaches_next_model_without_resetting_budget(self):
        job,digest = self.pending_correction_fixture()
        findings = 'Fix the failed test and preserve truthful cleanup.'
        reviewed = self.jobs.review_pending_correction(self.core,'owner',job['id'],job['baseline_task'],digest,findings)
        self.assertEqual((job['calls'],job['cycle'],job['steps'],job['deadline']),
                         (reviewed['calls'],reviewed['cycle'],reviewed['steps'],reviewed['deadline']))
        self.assertEqual(1,self.provider.calls)
        self.jobs.review_pending_correction(self.core,'owner',job['id'],job['baseline_task'],digest,findings)
        with self.assertRaises(Conflict):
            self.jobs.review_pending_correction(self.core,'owner',job['id'],job['baseline_task'],digest,'Changed review')
        self.core.close();self.core=Core(self.database,clock=lambda:self.now)
        for _ in range(20):
            result=self.tick()
            if result['state']=='completed':break
        self.assertEqual('completed',result['state'],result)
        self.assertEqual(2,self.provider.calls)
        self.assertEqual(findings,self.provider.contexts[-1]['diagnostics']['pending_review']['feedback'])

    def test_pending_review_rejects_wrong_baseline_source_drift_and_expired_job(self):
        job,digest=self.pending_correction_fixture()
        for baseline,identity in [('missing',digest),(job['baseline_task'],'0'*64)]:
            with self.assertRaises(Conflict):
                self.jobs.review_pending_correction(self.core,'owner',job['id'],baseline,identity,'Review failure')
        record=self.workspace.read('app.py');self.workspace.patch('app.py',record['sha256'],'40','39')
        with self.assertRaises(Conflict):
            self.jobs.review_pending_correction(self.core,'owner',job['id'],job['baseline_task'],digest,'Stale source')
        self.now=job['deadline']
        with self.assertRaises(Conflict):
            self.jobs.review_pending_correction(self.core,'owner',job['id'],job['baseline_task'],digest,'Expired review')
        self.assertEqual(1,self.provider.calls)

    def test_review_correction_rejects_wrong_identity_and_changed_feedback(self):
        job, proposal = self.review_fixture()
        for change in ({'response_sha256': '0'*64}, {'context_sha256': '0'*64}, {'proposal_id': 'missing'}):
            with self.assertRaises(Conflict): self.revise_fixture(job, proposal, **change)
        for feedback in ('', ' '*4, 'x'*8001):
            with self.assertRaises(ValueError): self.revise_fixture(job, proposal, feedback=feedback)
        with self.assertRaises(ValueError): self.revise_fixture(job, proposal, allow_model_call=False)
        self.revise_fixture(job, proposal)
        with self.assertRaises(Conflict): self.revise_fixture(job, proposal, feedback='Different review')
        self.assertEqual(1, self.provider.calls)

    def test_large_review_preserves_exact_proposal_and_compacts_only_duplicate_source(self):
        original=self.provider.complete
        def large(*args):
            response,usage=original(*args);data=json.loads(response)
            data['patches'][0]['new']+=' #'+('x'*14000)
            return json.dumps(data),usage
        with patch.object(self.provider,'complete',side_effect=large):
            job,proposal=self.review_fixture()
        reviewed=self.revise_fixture(job,proposal)
        review=reviewed['cycles'][1]['diagnostics']['proposal_review']
        self.assertTrue(review['previous_response_omitted'])
        self.assertEqual(checksum(proposal['response']),review['response_sha256'])
        self.assertLessEqual(len(json.dumps(reviewed['cycles'][1]['diagnostics']).encode()),12000)
        self.assertEqual(proposal['response'],self.runtime.get(self.core,'owner',proposal['id'])['response'])
        result=self.tick()
        if result['state']!='waiting_review':result=self.tick()
        self.assertEqual('waiting_review',result['state'],result)
        self.assertTrue(self.provider.contexts[-1]['diagnostics']['proposal_review']['previous_response_omitted'])
        self.assertEqual(2,self.provider.calls)

    def test_review_correction_rechecks_source_and_deadline(self):
        job, proposal = self.review_fixture()
        self.now = job['deadline']
        with self.assertRaises(Conflict): self.revise_fixture(job, proposal)
        self.now = 1100
        (self.workspace.root/'app.py').write_text('Changed input')
        with self.assertRaises(Conflict): self.revise_fixture(job, proposal)
        self.assertEqual(1, self.provider.calls)

    def test_host_bound_job_survives_restart_and_retests(self):
        created=self.create(edit_protocol='host-bound-v2')
        self.assertEqual('host-bound-v2',created['config']['edit_protocol'])
        self.tick()
        self.core.close();self.core=Core(self.database,clock=lambda:self.now)
        result=self.finish()
        self.assertEqual('completed',result['state'],result)
        self.assertEqual(1,self.provider.calls)
        self.assertEqual('host-bound-v2',self.provider.contexts[0]['edit_protocol'])
        self.assertIn('return 41',(self.source/'app.py').read_text())

    def _tested_inputs_hash(self):
        return checksum({path:self.workspace.read(path)['sha256'] for path in self.workspace.selected})

    def test_independent_review_withholds_tested_run_and_corrects_within_same_budget(self):
        self.provider.answers=(42,'42 # independent correction')
        created=self.create(mode='feature');job=self.finish();run=job['run'];inputs=self._tested_inputs_hash()
        revised=self.jobs.request_tested_revision(self.core,'owner',job['id'],run,inputs,'Fix the independently observed edge case.',True)
        self.assertEqual(1,revised['calls']);self.assertEqual(created['deadline'],revised['deadline'])
        self.assertEqual('failed',self.workflow.get(self.core,'owner',run)['state'])
        self.assertEqual('rejected_independent_review',revised['cycles'][0]['state'])
        self.core.close();self.core=Core(self.database,clock=lambda:self.now)
        repeated=self.jobs.request_tested_revision(self.core,'owner',job['id'],run,inputs,'Fix the independently observed edge case.',True)
        self.assertEqual(2,repeated['cycle'])
        with self.assertRaises(Conflict):self.jobs.request_tested_revision(self.core,'owner',job['id'],run,inputs,'Changed feedback',True)
        final=self.finish();self.assertEqual('completed',final['state'],final)
        self.assertEqual(2,final['calls'])
        self.assertEqual(run,self.provider.contexts[-1]['diagnostics']['proposal_review']['tested_run'])
        self.assertIn('return 41',(self.source/'app.py').read_text())

    def test_independent_review_rechecks_inputs_consent_and_deadline(self):
        self.create(mode='feature');job=self.finish();inputs=self._tested_inputs_hash()
        def request(digest=inputs,consent=True):
            return self.jobs.request_tested_revision(self.core,'owner',job['id'],job['run'],digest,'Independent defect',consent)
        with self.assertRaises(ValueError):request(consent=False)
        with self.assertRaises(Conflict):request('0'*64)
        self.now=job['deadline']
        with self.assertRaises(Conflict):request()
        self.now=1100
        self.workspace.patch('app.py',self.workspace.read('app.py')['sha256'],'42','40')
        with self.assertRaises(Conflict):request(self._tested_inputs_hash())
        self.assertEqual(1,self.jobs.get(self.core,'owner',job['id'])['calls'])

    def test_independent_review_cannot_revive_exhausted_or_prepared_delivery(self):
        self.create(mode='feature',max_calls=1);job=self.finish()
        with self.assertRaises(Conflict):self.jobs.request_tested_revision(self.core,'owner',job['id'],job['run'],self._tested_inputs_hash(),'Defect',True)
        # A separately prepared source write is a hard boundary, even before dispatch.
        self.provider.answers=('42 # delivery test',)
        self.create(mode='feature',request_id='independent-delivery')
        job=self.finish()
        self.core.set_policy('owner',self.project,'full',['workspace:fixture','source:fixture'])
        self.core.create_task('owner',self.project,'write','source:fixture',{'operation':'deliver','run':job['run']},'fixture-delivery-intent')
        with self.assertRaises(Conflict):self.jobs.request_tested_revision(self.core,'owner',job['id'],job['run'],self._tested_inputs_hash(),'Defect',True)

    def test_thinking_change_invalidates_job_binding_before_execution_or_call(self):
        self.provider.thinking_level='high';self.create(edit_protocol='host-bound-v2')
        self.provider.thinking_level='medium'
        with self.assertRaises(Conflict):self.create(edit_protocol='host-bound-v2')
        result=self.tick()
        self.assertEqual('blocked',result['state'])
        self.assertEqual(0,self.provider.calls)
        self.assertEqual(0,self.core.db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0])

    def test_selected_guidance_hashes_survive_restart_and_reach_exact_context(self):
        skill=Skill('quality','1','Preserve required behavior.');self.runtime.skills[skill.name]=skill
        expected={'quality':skill.record()['sha256']}
        created=self.create(skills=['quality'],expected_skills=expected)
        self.assertEqual(expected,created['config']['skill_bindings'])
        self.core.close();self.core=Core(self.database,clock=lambda:self.now)
        result=self.finish()
        self.assertEqual('completed',result['state'],result)
        self.assertEqual([skill.record()],self.provider.contexts[0]['skills'])
        self.assertEqual(1,self.provider.calls)

    def test_wrong_or_changed_guidance_blocks_before_native_execution(self):
        skill=Skill('quality','1','Preserve behavior.');self.runtime.skills[skill.name]=skill
        with self.assertRaises(Conflict):self.create(skills=['quality'],expected_skills={'quality':'0'*64})
        with self.assertRaises(ValueError):self.create(skills=['quality'],expected_skills={})
        self.create(skills=['quality'],expected_skills={'quality':skill.record()['sha256']})
        self.runtime.skills['quality']=Skill('quality','2','Updated guidance.')
        self.assertEqual('blocked',self.tick()['state'])
        self.assertEqual(0,self.provider.calls)
        self.assertEqual(0,self.core.db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0])

    def test_scheduled_guidance_request_recovers_original_pins_and_blocks_drift(self):
        skill=Skill('quality','1','Preserve behavior.');self.runtime.skills[skill.name]=skill
        expected={'quality':skill.record()['sha256']}
        created=self.create(skills=['quality'],expected_skills=expected,start_at=1100)
        self.runtime.skills['quality']=Skill('quality','2','Updated guidance.')
        self.assertEqual(created['id'],self.create(skills=['quality'],expected_skills=expected,start_at=1100)['id'])
        with self.assertRaises(Conflict):self.create(skills=['quality'],expected_skills={'quality':self.runtime.skills['quality'].record()['sha256']},start_at=1100)
        self.now=1100
        self.assertEqual('blocked',self.tick()['state']);self.assertEqual(0,self.provider.calls)

    def test_guidance_drift_after_generation_cannot_be_accepted(self):
        skill=Skill('quality','1','Preserve behavior.');self.runtime.skills[skill.name]=skill
        created=self.create(skills=['quality'],expected_skills={'quality':skill.record()['sha256']},auto_accept=False)
        for _ in range(8):
            job=self.tick()
            if job['state']=='waiting_review':break
        self.assertEqual('waiting_review',job['state'],job)
        proposal=self.runtime.get(self.core,'owner',job['proposal'])
        self.runtime.skills['quality']=Skill('quality','2','Updated guidance.')
        with self.assertRaises(Conflict):self.jobs.accept(self.core,'owner',created['id'],proposal['context_sha256'],proposal['response_sha256'])
        self.assertEqual(1,self.provider.calls);self.assertIn('41',self.workspace.read('app.py')['content'])

    def retrieval_scope(self):
        from skyra_coding import Workspace
        names=['app.py','tests/test_app.py']
        for number in range(30):
            name=f'noise{number:02}.py';names.append(name)
            (self.source/name).write_text('# unrelated '+str(number)+'\n'+'padding = 0\n'*450)
        self.workspace=Workspace.snapshot(self.source,self.root/'retrieval-snapshot',names)
        self.worker.workspaces[(self.project,'workspace:fixture')]=self.workspace
        return names

    def test_retrieval_build_recovers_evidence_without_uploading_all_candidates(self):
        names=self.retrieval_scope()
        self.create(files=names,context_mode='retrieve')
        first=self.tick();self.assertEqual('retrieve',first['phase']);self.assertEqual(0,self.provider.calls)
        second=self.tick();self.assertEqual('propose',second['phase']);self.assertEqual(0,self.provider.calls)
        task=second['cycles'][0]['diagnostics']['context_task']
        self.core.close();self.core=Core(self.database,clock=lambda:self.now)
        self.jobs=BuildJobs(self.runtime)
        result=self.finish()
        self.assertEqual('completed',result['state'],result)
        context=self.provider.contexts[0]
        self.assertLessEqual(len(context['files']),20)
        self.assertIn('tests/test_app.py',[record['path'] for record in context['files']])
        self.assertTrue(context['retrieval']['omitted'])
        self.assertEqual(task,context['retrieval']['task'])
        self.assertEqual(1,self.core.db.execute("SELECT COUNT(*) FROM tasks WHERE json_extract(payload,'$.operation')='retrieve'").fetchone()[0])
        self.assertEqual(1,self.provider.calls)
        self.assertIn('return 41',(self.source/'app.py').read_text())

    def test_retrieval_blocks_changed_omitted_context_before_any_model_call(self):
        names=self.retrieval_scope();self.create(files=names,context_mode='retrieve')
        self.tick();job=self.tick();task=job['cycles'][0]['diagnostics']['context_task']
        report=self.worker.evidence(json.loads(self.core.task('owner',task)['evidence'])[0])['result']
        omitted=report['omitted'][0]['path']
        (self.workspace.root/omitted).write_text('# owner changed omitted file\n')
        result=self.tick();self.assertEqual('blocked',result['state']);self.assertEqual(0,self.provider.calls)
        self.assertEqual(0,result['calls'])

    def test_retrieval_refreshes_each_repair_cycle_and_keeps_failed_cycle_evidence(self):
        names=self.retrieval_scope();self.provider.answers=(43,42)
        self.create(files=names,context_mode='retrieve');result=self.finish()
        self.assertEqual('completed',result['state'],result)
        self.assertEqual(2,self.provider.calls)
        tasks=[cycle['diagnostics']['context_task'] for cycle in result['cycles']]
        self.assertEqual(2,len(set(tasks)))
        self.assertEqual(tasks,[context['retrieval']['task'] for context in self.provider.contexts])
        self.assertNotEqual(self.provider.contexts[0]['retrieval']['input_hashes']['app.py'],
                            self.provider.contexts[1]['retrieval']['input_hashes']['app.py'])

    def test_model_cannot_patch_an_omitted_retrieval_candidate(self):
        names=self.retrieval_scope()
        def complete(system,context,schema):
            data=json.loads(context);path=data['retrieval']['omitted'][0]['path']
            record=self.workspace.read(path)
            return json.dumps({'summary':'Blind candidate edit','patches':[{
                'path':path,'expected_sha256':record['sha256'],'old':record['content'],'new':'# blind edit\n'}]}),{}
        self.provider.complete=complete
        self.create(files=names,context_mode='retrieve');result=self.finish()
        self.assertEqual('failed',result['state'],result)
        self.assertEqual('invalid_model_response',result['summary']['reason'])
        self.assertEqual('patch_unselected_path',result['summary']['validation_failure'])
        self.assertEqual([],self.workspace.diff()['changes'])
        self.assertEqual(1,result['calls'])

    def test_step_budget_does_not_dispatch_retrieval(self):
        self.create(context_mode='retrieve',max_steps=1)
        self.tick();result=self.tick()
        self.assertEqual('budget_limited',result['state'])
        self.assertEqual(0,self.provider.calls)
        self.assertEqual(0,self.core.db.execute("SELECT COUNT(*) FROM tasks WHERE json_extract(payload,'$.operation')='retrieve'").fetchone()[0])

    def test_passing_repair_does_not_retrieve_or_call_a_provider(self):
        self.workspace.patch('app.py',self.workspace.read('app.py')['sha256'],'41','42')
        job=self.create(context_mode='retrieve'); result=self.tick()
        self.assertEqual('completed',result['state']);self.assertEqual(0,self.provider.calls)
        self.assertEqual(0,self.core.db.execute("SELECT COUNT(*) FROM tasks WHERE json_extract(payload,'$.operation')='retrieve'").fetchone()[0])
        with self.assertRaises(Conflict):self.create(context_mode='selected')
    def finish(self, limit=30):
        result=None
        for _ in range(limit):
            result=self.tick()
            if result and result['state'] in {'completed','failed','blocked','budget_limited','cancelled'}: return result
        self.fail(str(result))

    def test_native_poll_renews_parent_and_task_without_duplicate_dispatch(self):
        from jarvis_core.runner_contact import begin, read
        begin(self.core,'owner',self.project)
        self.create()
        original=self.executor.run
        def long_step(workspace,profile,poll):
            for _ in range(22):
                self.now+=40;poll()
                observed=self.jobs.get(self.core,'owner',self.core.db.execute('SELECT id FROM build_jobs').fetchone()[0])['supervision']
                self.assertTrue(observed['lease_valid'])
                self.assertGreater(observed['elapsed_seconds'],0)
                self.assertNotIn('token',json.dumps(observed))
                self.assertEqual('in_progress',read(self.core,'owner',self.project)['state'])
                nested=self.jobs.tick(self.core,'owner',self.project)
                self.assertIsNone(nested['build_job'])
                self.assertEqual(0,nested['recovered'])
            return original(workspace,profile,poll)
        with patch.object(self.executor,'run',side_effect=long_step): result=self.tick()
        self.assertEqual('queued',result['state'],result)
        self.assertEqual('propose',result['phase'])
        self.assertEqual(1,self.core.db.execute('SELECT count(*) FROM build_attempts').fetchone()[0])
        self.assertEqual(1,self.core.db.execute('SELECT count(*) FROM execution_attempts').fetchone()[0])
        self.assertEqual(0,self.provider.calls)

    def test_deadline_during_native_execution_stops_before_model_or_patch(self):
        self.create(duration_seconds=60)
        original=self.executor.run;calls=0
        def deadline_step(workspace,profile,poll):
            def expire():
                nonlocal calls
                calls+=1
                if calls==2:self.now+=61
                poll()
            return original(workspace,profile,expire)
        with patch.object(self.executor,'run',side_effect=deadline_step): result=self.tick()
        self.assertEqual('budget_limited',result['state'],result)
        self.assertEqual('deadline',result['summary']['reason'])
        task=self.core.task('owner',result['baseline_task'])
        evidence=self.worker.evidence(json.loads(task['evidence'])[0])['result']
        self.assertEqual('deadline',evidence['supervision_stop'])
        self.assertTrue(evidence['cleanup_confirmed'],evidence)
        self.assertFalse(evidence['passed'])
        self.assertEqual(0,self.provider.calls)
        self.assertIn('return 41',(self.workspace.root/'app.py').read_text())

    def test_lost_parent_token_stops_native_process_and_preserves_new_owner(self):
        job=self.create();original=self.executor.run;calls=0
        def lose_owner(workspace,profile,poll):
            def change_owner():
                nonlocal calls
                calls+=1
                if calls==2:self.core.db.execute("UPDATE build_jobs SET lease_token='replacement' WHERE id=?",(job['id'],))
                poll()
            return original(workspace,profile,change_owner)
        with patch.object(self.executor,'run',side_effect=lose_owner):
            with self.assertRaises(Conflict):self.tick()
        row=self.core.db.execute('SELECT lease_token,baseline_task FROM build_jobs WHERE id=?',(job['id'],)).fetchone()
        self.assertEqual('replacement',row['lease_token'])
        task=self.core.task('owner',row['baseline_task'])
        report=self.worker.evidence(json.loads(task['evidence'])[0])['result']
        self.assertEqual('parent_lease_lost',report['supervision_stop'])
        self.assertTrue(report['cleanup_confirmed'],report)
        self.assertEqual(0,self.provider.calls)
        self.assertIn('return 41',(self.workspace.root/'app.py').read_text())

    def test_real_baseline_model_patch_retest_and_diff(self):
        conversation=self.core.create_conversation('owner',self.project)
        self.core.append_message('owner',conversation,'user','PRIVATE_HISTORY_NOT_MODEL_CONTEXT','note')
        self.create(conversation=conversation); result=self.finish()
        self.assertEqual('completed',result['state'],result)
        self.assertEqual(1,result['calls']); self.assertEqual(1,self.provider.calls)
        self.assertEqual('ready_for_review',self.workflow.get(self.core,'owner',result['run'])['state'])
        self.assertIn('return 41',(self.source/'app.py').read_text())
        self.assertEqual(1,len(result['cycles']))
        self.assertEqual('completed',result['cycles'][0]['state'])
        self.assertIn('FAILED',self.provider.contexts[0]['diagnostics']['output'])
        self.assertEqual(1,self.provider.contexts[0]['diagnostics']['exit_code'])
        from jarvis_core.coding_history import read
        history=read(self.core,'owner',conversation)
        self.assertEqual(result['id'],history['jobs'][0]['id'])
        self.assertEqual(result['run'],history['jobs'][0]['cycles'][0]['run'])
        self.assertEqual('fixture-repair',history['jobs'][0]['cycles'][0]['model'])
        self.assertNotIn('PRIVATE_HISTORY_NOT_MODEL_CONTEXT',json.dumps(self.provider.contexts))
        self.assertEqual(1,len(self.core.messages('owner',conversation)))

    def test_coding_history_page_keeps_one_snapshot_during_runner_update(self):
        from jarvis_core.coding_history import read
        conversation=self.core.create_conversation('owner',self.project)
        job=self.create(conversation=conversation)
        other=Core(self.database);changed=[]
        def advance(query):
            if query.startswith('SELECT c.cycle') and not changed:
                changed.append(True)
                with other.transaction():
                    other.db.execute("UPDATE build_jobs SET state='failed' WHERE id=?",(job['id'],))
                    other.db.execute("UPDATE build_cycles SET state='failed' WHERE job=?",(job['id'],))
        self.core.db.set_trace_callback(advance)
        try:
            page=read(self.core,'owner',conversation)
        finally:
            self.core.db.set_trace_callback(None);other.close()
        self.assertEqual([True],changed)
        self.assertEqual('queued',page['jobs'][0]['state'])
        self.assertEqual('baseline',page['jobs'][0]['cycles'][0]['state'])
        refreshed=read(self.core,'owner',conversation)
        self.assertEqual('failed',refreshed['jobs'][0]['state'])
        self.assertEqual('failed',refreshed['jobs'][0]['cycles'][0]['state'])
        self.assertFalse(self.core.db.in_transaction)

    def test_coding_history_link_is_owned_exact_and_paginated_after_restart(self):
        from jarvis_core.coding_history import read
        conversation=self.core.create_conversation('owner',self.project)
        other=self.core.create_project('owner','Other project')
        foreign=self.core.create_conversation('owner',other)
        with self.assertRaises(Denied):self.create(conversation=foreign)
        first=self.create(conversation=conversation)
        self.assertEqual(first['id'],self.create(conversation=conversation)['id'])
        self.assertNotIn('context',read(self.core,'owner',conversation)['jobs'][0])
        another=self.core.create_conversation('owner',self.project)
        with self.assertRaises(Conflict):self.create(conversation=another)
        with self.assertRaises(Denied):read(self.core,'stranger',conversation)
        ids=[first['id']]
        self.jobs.control(self.core,'owner',first['id'],'cancel')
        for number in range(2):
            job=self.create(conversation=conversation,request_id='history-'+str(number));ids.append(job['id'])
            self.jobs.control(self.core,'owner',job['id'],'cancel')
        original=dict(self.core.db.execute('SELECT * FROM build_jobs WHERE id=?',(first['id'],)).fetchone())
        self.core.db.execute('DROP TABLE coding_job_links');self.core.db.execute('PRAGMA user_version=14')
        self.core.close();self.core=Core(self.database,clock=lambda:self.now)
        self.assertEqual(15,self.core.db.execute('PRAGMA user_version').fetchone()[0])
        self.assertEqual(original,dict(self.core.db.execute('SELECT * FROM build_jobs WHERE id=?',(first['id'],)).fetchone()))
        page=read(self.core,'owner',conversation,limit=1);seen=[page['jobs'][0]['id']]
        while page['next_before'] is not None:
            page=read(self.core,'owner',conversation,page['next_before'],limit=1);seen.extend(job['id'] for job in page['jobs'])
        self.assertEqual(ids[::-1],seen)
        self.assertEqual([],read(self.core,'owner',another)['jobs'])
        self.assertEqual(0,self.provider.calls)
        with self.assertRaises(ValueError):read(self.core,'owner',conversation,before=True)
        import sqlite3
        with self.assertRaises(sqlite3.IntegrityError):
            self.core.db.execute('DELETE FROM conversations WHERE id=?',(conversation,))
        self.create(conversation=conversation,start_at=1100,request_id='scheduled-history')
        with self.assertRaises(Conflict):
            self.create(conversation=another,start_at=1100,request_id='scheduled-history')

    def test_model_history_snapshot_is_scoped_bounded_and_frozen(self):
        from jarvis_core.coding_history import model_snapshot
        from jarvis_runtime.conversation import ConversationRuntime
        conversation=self.core.create_conversation('owner',self.project)
        other=self.core.create_conversation('owner',self.project)
        ids=[]
        for number in range(5):
            job=self.create(conversation=conversation,request_id='snapshot-'+str(number),goal='X'*8000)
            ids.append(job['id']); self.jobs.control(self.core,'owner',job['id'],'cancel')
        snapshot=model_snapshot(self.core,'owner',conversation)
        self.assertEqual(ids[-3:][::-1],[j['id'] for j in snapshot['snapshot']['jobs']])
        self.assertIsNotNone(snapshot['snapshot']['next_before'])
        self.assertTrue(all(j['goal_truncated'] and len(j['goal'])==1000 for j in snapshot['snapshot']['jobs']))
        self.assertEqual([],model_snapshot(self.core,'owner',other)['snapshot']['jobs'])
        with self.assertRaises(Denied): model_snapshot(self.core,'stranger',conversation)
        runtime=ConversationRuntime({'fixture':self.provider})
        turn=runtime.create(self.core,'owner',conversation,'fixture','chat','What next?','followup',True)
        frozen=runtime.get(self.core,'owner',turn)['context']['coding_history']
        new=self.create(conversation=conversation,request_id='later')
        self.assertEqual(turn,runtime.create(self.core,'owner',conversation,'fixture','chat','What next?','followup',True))
        self.assertEqual(frozen,runtime.get(self.core,'owner',turn)['context']['coding_history'])
        self.assertNotIn(new['id'],json.dumps(frozen))
        self.assertEqual(0,self.provider.calls)

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

    def test_feature_on_passing_baseline_builds_and_recovers_after_restart(self):
        (self.workspace.root/'app.py').write_text('def answer():\n    return 42\n',encoding='utf-8')
        self.provider.answers=('42\n\ndef greeting():\n    return "Hello Skyra"',)
        created=self.create(mode='feature',goal='Add greeting() returning Hello Skyra')
        baseline=self.tick()
        self.assertEqual('propose',baseline['phase'])
        self.assertEqual('feature_baseline_verified',baseline['summary']['reason'])
        self.assertEqual(0,self.provider.calls)
        self.core.close(); self.core=Core(self.database,clock=lambda:self.now)
        self.assertEqual('feature',self.jobs.get(self.core,'owner',created['id'])['config']['mode'])
        result=self.finish()
        self.assertEqual('completed',result['state'],result)
        self.assertEqual('tested_feature_ready_for_review',result['summary']['reason'])
        self.assertEqual(1,self.provider.calls)
        self.assertEqual('feature',self.provider.contexts[0]['mode'])
        self.assertEqual(0,self.provider.contexts[0]['diagnostics']['exit_code'])
        self.assertIn('def greeting()',self.workspace.read('app.py')['content'])
        self.assertNotIn('greeting',(self.source/'app.py').read_text())
        run=self.workflow.get(self.core,'owner',result['run'])
        self.assertEqual('complete',run['steps'][0]['expect'])
        self.assertTrue(all(r['expectation_met'] for r in run['results']))
        self.assertEqual('ready_for_review',run['state'])

    def test_passing_feature_can_create_and_use_a_reusable_module(self):
        from skyra_coding import Workspace
        (self.source/'app.py').write_text('def answer():\n    return 42\n',encoding='utf-8')
        workspace=Workspace.snapshot(self.source,self.root/'feature-snapshot',
                                     ['app.py','tests/test_app.py'],['calculations.py'])
        self.workspace=workspace
        self.worker.workspaces[(self.project,'workspace:fixture')]=workspace
        def complete(system,context,schema):
            data=json.loads(context)
            self.assertIn('requested feature',system)
            self.assertEqual('lexical-v1',data['retrieval']['algorithm'])
            self.assertEqual(0,data['diagnostics']['exit_code'])
            source=next(f for f in data['files'] if f['path']=='app.py')
            return json.dumps({'summary':'Extract reusable computation and use it', 'patches':[
                {'path':'app.py','expected_sha256':source['sha256'],'old':'return 42',
                 'new':'from calculations import compute\n    return compute(6, 7)'},
                {'path':'calculations.py','expected_sha256':'absent','old':'',
                 'new':'def compute(left, right):\n    return left * right\n'}]}), {}
        self.provider.complete=complete
        self.create(mode='feature',context_mode='retrieve',files=['app.py','tests/test_app.py','calculations.py'])
        result=self.finish()
        self.assertEqual('completed',result['state'],result)
        self.assertEqual(1,result['calls'])
        run=self.workflow.get(self.core,'owner',result['run'])
        self.assertEqual('ready_for_review',run['state'])
        self.assertEqual(5,len(run['results']))
        self.assertTrue(all(r['expectation_met'] for r in run['results']))
        self.assertEqual({'app.py','calculations.py'},{c['path'] for c in workspace.diff()['changes']})
        self.assertFalse((self.source/'calculations.py').exists())
        self.assertIn('return 42',(self.source/'app.py').read_text())

    def test_feature_still_repairs_a_failed_retest(self):
        self.provider.answers=(40,42)
        self.create(mode='feature')
        result=self.finish()
        self.assertEqual('completed',result['state'],result)
        self.assertEqual(2,self.provider.calls)
        self.assertEqual('failed_retest',result['cycles'][0]['state'])

    def test_mode_is_bound_to_idempotency_and_legacy_repair_config_is_unchanged(self):
        job=self.create()
        self.assertNotIn('mode',job['config'])
        self.assertEqual(job['id'],self.create(mode='repair')['id'])
        with self.assertRaises(Conflict): self.create(mode='feature')
        with self.assertRaises(ValueError): self.create(mode='unknown')

    def test_api_rejects_unknown_mode_and_persists_feature_mode(self):
        from jarvis_core.api import BuildJobInput
        from pydantic import ValidationError
        fields=dict(resource='workspace:fixture',profile='unit',provider='fixture',goal='Feature',
                    files=['app.py','tests/test_app.py'],skills=[],max_calls=1,max_cycles=1,max_steps=30,
                    duration_seconds=3600,auto_accept=True,allow_model_calls=True,request_id='mode-api')
        self.assertEqual('repair',BuildJobInput(**fields).mode)
        self.assertEqual('legacy-v1',BuildJobInput(**fields).edit_protocol)
        with self.assertRaises(ValidationError):BuildJobInput(**fields,edit_protocol='unknown')
        self.assertEqual('host-bound-v2',BuildJobInput(**fields,edit_protocol='host-bound-v2').edit_protocol)
        with self.assertRaises(ValidationError): BuildJobInput(**fields,mode='unknown')
        body=BuildJobInput(**fields,mode='feature').model_dump()
        result=self.jobs.create(self.core,'owner',self.project,**body)
        self.assertEqual('feature',result['config']['mode'])

    def test_feature_baseline_requires_verified_cleanup_before_model_call(self):
        self.create(mode='feature'); result=self.tick(); task=result['baseline_task']
        data=self.core.task('owner',task)
        report=self.worker.evidence(json.loads(data['evidence'])[0])['result']
        report['cleanup_confirmed']=False
        forged=self.worker._report(task,'test',report)
        self.core.db.execute('UPDATE tasks SET evidence=? WHERE id=?',(json.dumps(forged['evidence']),task))
        self.assertEqual('blocked',self.tick()['state'])
        self.assertEqual(0,self.provider.calls)

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
        self.assertNotIn('validation_failure',result['summary'])
        self.assertNotIn('private provider failure',json.dumps(result))
        self.assertIsNone(self.tick())

    def test_invalid_response_summary_survives_restart_without_raw_output_or_replay(self):
        job=self.create();self.tick()
        with patch.object(self.provider,'complete',return_value=('PRIVATE_MODEL_OUTPUT_NOT_JSON',{'total_tokens':12})) as complete:
            result=self.tick()
            self.assertEqual(1,complete.call_count)
        self.assertEqual('failed',result['state'])
        self.assertEqual('invalid_json',result['summary']['validation_failure'])
        self.assertEqual({'total_tokens':12},result['summary']['last_reported_usage'])
        self.core.close();self.core=Core(self.database,clock=lambda:self.now)
        restored=self.jobs.get(self.core,'owner',job['id'])
        self.assertEqual(result['summary'],restored['summary'])
        self.assertNotIn('PRIVATE_MODEL_OUTPUT_NOT_JSON',json.dumps(restored))
        self.assertIsNone(self.tick())
        self.assertEqual(1,restored['calls'])
        self.assertEqual([],self.workspace.diff()['changes'])

    def failed_generation(self, error=None, **config):
        job=self.create(**config);self.tick()
        with patch.object(self.provider,'complete',side_effect=error) if error else patch.object(
                self.provider,'complete',return_value=('invalid json',{})):
            result=self.tick()
        failed=self.runtime.get(self.core,'owner',result['proposal'])
        return job,result,failed

    def test_reviewed_generation_retry_preserves_failure_and_budgets_after_restart(self):
        job,failed,proposal=self.failed_generation()
        retried=self.jobs.retry_generation(self.core,'owner',job['id'],proposal['id'],proposal['context_sha256'],True)
        self.assertEqual('queued',retried['state']);self.assertEqual(2,retried['cycle'])
        self.assertEqual(1,retried['calls']);self.assertEqual(job['deadline'],retried['deadline'])
        self.assertEqual('failed',self.runtime.get(self.core,'owner',proposal['id'])['state'])
        self.core.close();self.core=Core(self.database,clock=lambda:self.now)
        self.assertEqual(2,self.jobs.retry_generation(self.core,'owner',job['id'],proposal['id'],proposal['context_sha256'],True)['cycle'])
        result=self.finish()
        self.assertEqual('completed',result['state'],result);self.assertEqual(2,result['calls'])
        self.assertEqual('failed',result['cycles'][0]['state'])
        self.assertEqual('invalid_json',self.provider.contexts[-1]['diagnostics']['generation_retry']['validation_failure'])
        self.assertEqual(result['id'],self.jobs.retry_generation(self.core,'owner',job['id'],proposal['id'],proposal['context_sha256'],True)['id'])
        with self.assertRaises(Conflict):self.jobs.retry_generation(self.core,'owner',job['id'],proposal['id'],'0'*64,True)

    def test_generation_retry_requires_consent_exact_context_and_remaining_budget(self):
        job,failed,proposal=self.failed_generation(max_calls=1)
        for consent in (False,1,None):
            with self.assertRaises(ValueError):self.jobs.retry_generation(self.core,'owner',job['id'],proposal['id'],proposal['context_sha256'],consent)
        with self.assertRaises(Conflict):self.jobs.retry_generation(self.core,'owner',job['id'],proposal['id'],'0'*64,True)
        with self.assertRaises(Conflict):self.jobs.retry_generation(self.core,'owner',job['id'],proposal['id'],proposal['context_sha256'],True)
        self.assertEqual(1,self.jobs.get(self.core,'owner',job['id'])['cycle'])

    def test_output_limit_retry_explicitly_rebinds_same_model_without_resetting_budget(self):
        from jarvis_runtime.responses import IncompleteResponse
        job, failed, proposal = self.failed_generation(IncompleteResponse(output_limited=True, usage={}))
        larger = Provider(); larger.max_output_tokens = 1024
        self.runtime.providers['larger'] = larger
        retried = self.jobs.retry_generation(self.core,'owner',job['id'],proposal['id'],proposal['context_sha256'],True,'larger')
        self.assertEqual('larger',retried['config']['provider'])
        self.assertEqual(1,retried['calls']); self.assertEqual(job['deadline'],retried['deadline'])
        self.assertEqual(2,retried['config']['max_calls'])
        self.core.close(); self.core=Core(self.database,clock=lambda:self.now)
        result=self.finish()
        self.assertEqual('completed',result['state'],result)
        self.assertEqual(2,result['calls']); self.assertEqual(1,larger.calls)
        self.assertEqual(256,result['cycles'][1]['diagnostics']['generation_retry']['output_limit_review']['previous_max_output_tokens'])
        self.assertEqual(result['id'],self.jobs.retry_generation(self.core,'owner',job['id'],proposal['id'],proposal['context_sha256'],True,'larger')['id'])
        with self.assertRaises(Conflict): self.jobs.retry_generation(self.core,'owner',job['id'],proposal['id'],proposal['context_sha256'],True)

    def test_output_limit_retry_rejects_model_changes_and_unrelated_failures(self):
        job, failed, proposal = self.failed_generation()
        larger = Provider(); larger.max_output_tokens=1024
        self.runtime.providers['larger']=larger
        with self.assertRaises(Conflict): self.jobs.retry_generation(self.core,'owner',job['id'],proposal['id'],proposal['context_sha256'],True,'larger')
        self.assertEqual(1,self.jobs.get(self.core,'owner',job['id'])['calls'])

    def test_generation_retry_rejects_uncertain_provider_outcome_and_stale_files(self):
        job,failed,proposal=self.failed_generation(OSError('private uncertain transport'))
        with self.assertRaises(Conflict):self.jobs.retry_generation(self.core,'owner',job['id'],proposal['id'],proposal['context_sha256'],True)
        self.assertEqual(1,self.jobs.get(self.core,'owner',job['id'])['calls'])
        job,failed,proposal=self.failed_generation(request_id='second')
        self.workspace.patch('app.py',self.workspace.read('app.py')['sha256'],'41','40')
        with self.assertRaises(Conflict):self.jobs.retry_generation(self.core,'owner',job['id'],proposal['id'],proposal['context_sha256'],True)
        self.assertEqual(1,self.jobs.get(self.core,'owner',job['id'])['cycle'])

    def test_unknown_generation_requires_explicit_review_and_keeps_spent_call(self):
        job,failed,proposal=self.failed_generation(TimeoutError('private payload'))
        self.assertEqual('provider_timeout',proposal['error'])
        with self.assertRaises(Conflict):
            self.jobs.retry_generation(self.core,'owner',job['id'],proposal['id'],proposal['context_sha256'],True)
        with self.assertRaises(ValueError):
            self.jobs.retry_generation(self.core,'owner',job['id'],proposal['id'],proposal['context_sha256'],True,acknowledge_unknown_outcome=1)
        reviewed=self.jobs.retry_generation(self.core,'owner',job['id'],proposal['id'],proposal['context_sha256'],True,acknowledge_unknown_outcome=True)
        self.assertEqual(1,reviewed['calls']);self.assertEqual(job['deadline'],reviewed['deadline'])
        self.assertTrue(reviewed['cycles'][1]['diagnostics']['generation_retry']['unknown_outcome_acknowledged'])
        result=self.finish()
        self.assertEqual('completed',result['state'],result)
        self.assertEqual(2,result['calls'])
        self.assertEqual('failed',self.runtime.get(self.core,'owner',proposal['id'])['state'])
        with self.assertRaises(Conflict):
            self.jobs.retry_generation(self.core,'owner',job['id'],proposal['id'],proposal['context_sha256'],True)

    def test_generation_retry_http_is_controller_only_and_explicit(self):
        import time
        self.now=time.time()
        job,failed,proposal=self.failed_generation()
        tokens={role:role+'_'+'z'*40 for role in ('controller','worker')}
        credentials=[Credential(hashlib.sha256(token.encode()).hexdigest(),'owner',role,
                     frozenset() if role=='controller' else frozenset({self.project})) for role,token in tokens.items()]
        url='/v1/build-jobs/'+job['id']+'/retry-generation'
        body={'proposal':proposal['id'],'context_sha256':proposal['context_sha256'],'allow_model_call':True}
        with TestClient(create_app(self.database,credentials,self.worker,self.runtime,unattended_enabled=True),
                        base_url='http://127.0.0.1',client=('127.0.0.1',50000)) as client:
            def call(role='controller',data=body):return client.post(url,json=data,headers={'Authorization':'Bearer '+tokens[role]})
            self.assertEqual(403,call('worker').status_code)
            self.assertEqual(422,call(data={**body,'allow_model_call':False}).status_code)
            self.assertEqual(422,call(data={**body,'allow_model_call':1}).status_code)
            response=call();self.assertEqual(200,response.status_code,response.text)
            self.assertEqual(2,response.json()['cycle']);self.assertEqual(1,response.json()['calls'])
            self.assertEqual(2,call().json()['cycle'])

    def test_generation_retry_refreshes_retrieval_and_keeps_safe_failure_feedback(self):
        names=self.retrieval_scope()
        job=self.create(files=names,context_mode='retrieve');self.tick();self.tick()
        with patch.object(self.provider,'complete',return_value=('invalid json',{})):
            failed=self.tick()
        proposal=self.runtime.get(self.core,'owner',failed['proposal'])
        retry=self.jobs.retry_generation(self.core,'owner',job['id'],proposal['id'],proposal['context_sha256'],True)
        self.assertEqual('retrieve',retry['phase'])
        result=self.finish();self.assertEqual('completed',result['state'],result)
        tasks=[cycle['diagnostics']['context_task'] for cycle in result['cycles']]
        self.assertEqual(2,len(set(tasks)))
        self.assertEqual(proposal['id'],self.provider.contexts[-1]['diagnostics']['generation_retry']['proposal'])

    def test_generation_retry_identity_remains_after_failed_retest(self):
        job,failed,proposal=self.failed_generation()
        self.jobs.retry_generation(self.core,'owner',job['id'],proposal['id'],proposal['context_sha256'],True)
        self.provider.answers=(43,)
        result=self.finish()
        self.assertEqual('budget_limited',result['state'])
        repeated=self.jobs.retry_generation(self.core,'owner',job['id'],proposal['id'],proposal['context_sha256'],True)
        self.assertEqual(result['cycles'],repeated['cycles'])
        self.assertEqual(2,repeated['calls'])

    def test_generation_retry_pins_legacy_guidance_through_dispatch_and_acceptance(self):
        skill=Skill('quality','1','Preserve behavior.');self.runtime.skills[skill.name]=skill
        job,failed,proposal=self.failed_generation(skills=['quality'],auto_accept=False)
        self.jobs.retry_generation(self.core,'owner',job['id'],proposal['id'],proposal['context_sha256'],True)
        self.runtime.skills['quality']=Skill('quality','2','Changed guidance.')
        self.assertEqual('blocked',self.tick()['state']);self.assertEqual(0,self.provider.calls)
        self.runtime.skills['quality']=skill
        self.jobs.control(self.core,'owner',job['id'],'resume')
        for _ in range(5):
            reviewed=self.tick()
            if reviewed['state']=='waiting_review':break
        self.assertEqual('waiting_review',reviewed['state'])
        response=self.runtime.get(self.core,'owner',reviewed['proposal'])
        self.runtime.skills['quality']=Skill('quality','2','Changed guidance.')
        with self.assertRaises(Conflict):self.jobs.accept(self.core,'owner',job['id'],response['context_sha256'],response['response_sha256'])
        self.assertIsNone(self.jobs.get(self.core,'owner',job['id'])['run'])

    def test_generation_retry_checks_legacy_skill_revision_and_original_cycle_deadline(self):
        skill=Skill('quality','1','Preserve behavior.');self.runtime.skills[skill.name]=skill
        job,failed,proposal=self.failed_generation(skills=['quality'])
        self.runtime.skills['quality']=Skill('quality','2','Changed guidance.')
        with self.assertRaises(Conflict):self.jobs.retry_generation(self.core,'owner',job['id'],proposal['id'],proposal['context_sha256'],True)
        self.runtime.skills['quality']=skill
        self.now=job['deadline']
        with self.assertRaises(Conflict):self.jobs.retry_generation(self.core,'owner',job['id'],proposal['id'],proposal['context_sha256'],True)
        self.now=1000
        job,failed,proposal=self.failed_generation(max_cycles=1,request_id='no-cycle')
        with self.assertRaises(Conflict):self.jobs.retry_generation(self.core,'owner',job['id'],proposal['id'],proposal['context_sha256'],True)

    def test_generation_retry_allows_known_service_rejections_but_not_unknown_timeouts(self):
        class Failure(Exception):
            def __init__(self,status):self.status_code=status
        for status,allowed in [(429,True),(503,True),(401,False),(504,False)]:
            job,failed,proposal=self.failed_generation(Failure(status),request_id='http-'+str(status))
            if allowed:
                retried=self.jobs.retry_generation(self.core,'owner',job['id'],proposal['id'],proposal['context_sha256'],True)
                self.assertEqual('queued',retried['state']);self.assertEqual(1,retried['calls'])
                self.jobs.control(self.core,'owner',job['id'],'cancel')
            else:
                with self.assertRaises(Conflict):self.jobs.retry_generation(self.core,'owner',job['id'],proposal['id'],proposal['context_sha256'],True)

    def test_output_limited_call_is_charged_and_reported_without_dispatching_a_patch(self):
        from jarvis_runtime.responses import IncompleteResponse
        self.create();self.tick()
        with patch.object(self.provider,'complete',side_effect=IncompleteResponse(
                output_limited=True,usage={'total_tokens':8192,'reasoning_tokens':7000})) as complete:
            result=self.tick()
            self.assertEqual(1,complete.call_count)
        self.assertEqual('failed',result['state'])
        self.assertEqual('provider_output_limit',result['summary']['reason'])
        self.assertEqual({'total_tokens':8192,'reasoning_tokens':7000},result['summary']['last_reported_usage'])
        self.assertEqual(1,result['calls']);self.assertIsNone(result['run'])
        self.assertIsNone(self.tick())
        self.assertEqual([],self.workspace.diff()['changes'])

    def test_api_job_creation_review_and_reads_preserve_role_boundaries(self):
        conversation=self.core.create_conversation('owner',self.project)
        tokens={role:role+'_'+'z'*40 for role in ('controller','worker')}
        credentials=[Credential(hashlib.sha256(token.encode()).hexdigest(),'owner',role,
                     frozenset() if role=='controller' else frozenset({self.project})) for role,token in tokens.items()]
        with TestClient(create_app(self.database,credentials,self.worker,self.runtime,unattended_enabled=True),
                        base_url='http://127.0.0.1',client=('127.0.0.1',50000)) as client:
            def call(method,path,role='controller',body=None):
                return client.request(method,path,headers={'Authorization':'Bearer '+tokens[role]},json=body)
            body=dict(conversation=conversation,resource='workspace:fixture',profile='unit',provider='fixture',goal='Repair answer',
                      files=['app.py','tests/test_app.py'],skills=[],max_calls=1,max_cycles=1,max_steps=20,
                      duration_seconds=3600,auto_accept=False,allow_model_calls=True,request_id='http')
            url=f'/v1/projects/{self.project}/build-jobs'
            self.assertEqual(403,call('POST',url,'worker',body).status_code)
            self.assertEqual(422,call('POST',url,body={**body,'allow_model_calls':False}).status_code)
            response=call('POST',url,body=body); self.assertEqual(201,response.status_code,response.text)
            job=response.json()['id']
            history=f'/v1/conversations/{conversation}/coding-history'
            self.assertEqual(403,call('GET',history,'worker').status_code)
            history_response=call('GET',history)
            self.assertEqual(200,history_response.status_code,history_response.text)
            self.assertEqual(job,history_response.json()['jobs'][0]['id'])
            self.assertEqual(422,call('GET',history+'?before=-1').status_code)
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
        self.assertEqual(15,self.core.db.execute('PRAGMA user_version').fetchone()[0])
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
