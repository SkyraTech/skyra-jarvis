"""Durable, controller-approved repair plans. No model or automatic release policy."""

import json
import uuid
from contextlib import nullcontext
from jarvis_core import Conflict
from .workspace import BoundaryError


class CodingWorkflow:
    def __init__(self,worker):self.worker=worker

    def create(self,core,actor,project,resource,profile,patches,request_id=None,mode='repair'):
        core._owned(actor,project)
        if mode not in {'repair','feature'}: raise BoundaryError('Unsupported coding mode')
        workspace=self.worker.workspaces.get((project,resource))
        if workspace is None or self.worker.sandbox is None or profile not in self.worker.sandbox.profiles:
            raise BoundaryError('Registered workspace and test profile required')
        protected=self.worker.profile(project,resource,profile).protected_paths
        if not isinstance(patches,list) or not 1<=len(patches)<=10:
            raise BoundaryError('A repair plan requires 1..10 explicit patches')
        if (not all(isinstance(patch,dict) and isinstance(patch.get('path'),str) for patch in patches)
                or len({patch['path'] for patch in patches})!=len(patches)):
            raise BoundaryError('Duplicate or invalid patch paths')
        for patch in patches:
            if not isinstance(patch,dict) or set(patch)!={'path','expected_sha256','old','new'}:
                raise BoundaryError('Invalid patch plan')
            if patch['path'] in protected:
                raise BoundaryError('Repair plan cannot edit protected tests')
            workspace._selected(patch['path'])
            if not all(isinstance(v,str) for v in patch.values()) or (not patch['old'] and patch['expected_sha256']!='absent'):
                raise BoundaryError('Invalid patch values')
        steps=[{'action':'execute','payload':{'operation':'test','profile':profile},'expect':'complete' if mode=='feature' else 'failure'}]
        for patch in patches:
            if patch['expected_sha256']=='absent':
                if patch['old'] or not patch['new'] or patch['path'] not in workspace.create_paths:
                    raise BoundaryError('Creation target is stale or invalid')
                payload={'operation':'create','path':patch['path'],'content':patch['new']}
            else:
                payload={'operation':'patch',**patch}
            steps.append({'action':'write','payload':payload,'expect':'success'})
        steps += [{'action':'execute','payload':{'operation':'test','profile':profile},'expect':'success'},
                  {'action':'read','payload':{'operation':'diff'},'expect':'success'}]
        run=uuid.uuid4().hex
        plan=json.dumps(steps,sort_keys=True)
        with (nullcontext() if core.db.in_transaction else core.transaction()):
            if request_id is not None:
                previous=core.db.execute('SELECT id,plan,resource FROM coding_runs WHERE project=? AND request_id=?',(project,request_id)).fetchone()
                if previous:
                    if previous['plan']!=plan or previous['resource']!=resource:raise Conflict('Run request ID reused with changed plan')
                    return previous['id']
            for patch in patches:
                if patch['expected_sha256']=='absent' and workspace.read(patch['path'])['sha256']!='absent':
                    raise BoundaryError('Creation target already exists')
            if core.db.execute("SELECT 1 FROM coding_runs WHERE project=? AND resource=? AND state NOT IN ('failed','ready_for_review','cancelled')",(project,resource)).fetchone():
                raise Conflict('Resource already has an active coding run')
            core.db.execute("INSERT INTO coding_runs VALUES(?,?,?,?,?,'planned',0,NULL,'[]',?)",
                            (run,project,resource,plan,actor,request_id))
            core._event(project,'coding_run.created',run)
        return run

    def list(self,core,actor,project):
        core._owned(actor,project)
        return [dict(r) for r in core.db.execute('SELECT id,state,position,resource FROM coding_runs WHERE project=? ORDER BY rowid DESC LIMIT 100',(project,))]

    def get(self,core,actor,run):
        row=core.db.execute('SELECT * FROM coding_runs WHERE id=?',(run,)).fetchone()
        if row is None:raise BoundaryError('Coding run unavailable')
        core._owned(actor,row['project'])
        result=dict(row)
        result['steps']=json.loads(result.pop('plan'))
        result['results']=json.loads(result['results'])
        return result

    def advance(self,core,actor,run,supervise=None):
        current=self.get(core,actor,run)
        if current['state'] in {'failed','ready_for_review','cancelled'}:return current
        step=current['steps'][current['position']]
        task=current['task']
        if task is None:
            task=core.create_task(actor,current['project'],step['action'],current['resource'],step['payload'],
                                  request_id=f'coding:{run}:{current["position"]}')
            with core.transaction():
                core.db.execute('UPDATE coding_runs SET task=? WHERE id=? AND position=? AND task IS NULL',
                                (task,run,current['position']))
        state=core.task(actor,task)['state']
        if state in {'queued','waiting_approval'}:
            if step['action']=='execute' and not self.worker.capabilities()['execution_available']:
                self._state(core,run,'blocked');return self.get(core,actor,run)
            claim=core.start(actor,task)
            if claim['state']=='waiting_approval':
                self._state(core,run,'waiting_approval');return self.get(core,actor,run)
            self._state(core,run,'running')
            self.worker.perform(core,actor,task,claim['lease_token'],supervise=supervise)
            state=core.task(actor,task)['state']
        elif state in {'running','cancellation_requested'}:
            # Another worker owns it. Never execute an already-dispatched task twice.
            return self.get(core,actor,run)
        if state in {'interrupted','cancellation_unconfirmed'}:
            self._state(core,run,'blocked');return self.get(core,actor,run)
        if state=='cancelled':
            self._state(core,run,'cancelled');return self.get(core,actor,run)
        expected='failed' if step['expect']=='failure' else 'succeeded'
        evidence=json.loads(core.task(actor,task)['evidence'] or '[]')
        matched=state in {'succeeded','failed'} if step['expect']=='complete' else state==expected
        if step['action']=='execute' and matched:
            record=self.worker.evidence(evidence[0]) if evidence else {}
            report=record.get('result',{})
            matched=(record.get('task_id')==task and record.get('operation')=='test'
                     and report.get('profile')==step['payload']['profile']
                     and report.get('kind') in {'container_test','native_test'}
                     and report.get('termination') is None and report.get('cleanup_confirmed') is True)
            if step['expect']=='failure':matched=matched and report.get('exit_code') not in (None,0)
            elif step['expect']=='complete':
                matched=(matched and type(report.get('exit_code')) is int
                         and report.get('passed') is (report.get('exit_code')==0)
                         and state==('succeeded' if report.get('exit_code')==0 else 'failed'))
            else:matched=matched and report.get('exit_code')==0 and report.get('passed') is True
        with core.transaction():
            latest=self.get(core,actor,run)
            if latest['state'] in {'cancelled','cancellation_requested'}:
                core.db.execute("UPDATE coding_runs SET state='cancelled' WHERE id=?",(run,))
                return self.get(core,actor,run)
            if latest['position']!=current['position']:return latest
            results=latest['results']+[{'task_id':task,'state':state,'evidence':evidence,'expectation_met':matched}]
            position=current['position']+1
            next_state='failed' if not matched else ('ready_for_review' if position==len(current['steps']) else 'planned')
            core.db.execute('UPDATE coding_runs SET state=?,position=?,task=NULL,results=? WHERE id=?',
                            (next_state,position,json.dumps(results),run))
            core._event(current['project'],'coding_run.'+next_state,run)
        return self.get(core,actor,run)

    def cancel(self,core,actor,run):
        current=self.get(core,actor,run)
        if current['state'] in {'ready_for_review','failed','cancelled'}:
            raise BoundaryError('Coding run already terminal')
        state='cancelled'
        if current['task']:
            task=core.task(actor,current['task'])
            if task['state'] not in {'succeeded','failed','cancelled'}:
                core.cancel(actor,current['task'])
                if task['state']=='running':state='cancellation_requested'
        self._state(core,run,state)
        return self.get(core,actor,run)

    def _state(self,core,run,state):
        with core.transaction():
            # Cancellation is sticky, including across a concurrent step completion.
            if state=='cancelled':
                core.db.execute("UPDATE coding_runs SET state='cancelled' WHERE id=? AND state NOT IN ('failed','ready_for_review')",(run,))
            else:core.db.execute("UPDATE coding_runs SET state=? WHERE id=? AND state NOT IN ('cancelled','cancellation_requested')",(state,run))
