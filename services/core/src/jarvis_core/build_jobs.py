"""Bounded model/test repair cycles with separately reviewed proposals and call reservations."""
from dataclasses import asdict
import hashlib
import json
import os
import uuid

from .store import Conflict, Denied, encode
from .dispatch import busy, recover


def checksum(value):
    return hashlib.sha256(encode(value).encode()).hexdigest()


class BuildJobs:
    def __init__(self, runtime):
        self.runtime = runtime
        self.worker = runtime.worker if runtime else None
        self.workflow = runtime.workflow if runtime else None

    def get(self, core, actor, job, cycles=True):
        row = core.db.execute('SELECT * FROM build_jobs WHERE id=?', (job,)).fetchone()
        if row is None: raise Denied('Build job unavailable')
        core._owned(actor, row['project'])
        data = dict(row); data.pop('lease_token', None); data.pop('digest', None)
        data['config'] = json.loads(data['config']); data['summary'] = json.loads(data['summary'])
        if cycles:
            data['cycles'] = [dict(r) for r in core.db.execute('SELECT * FROM build_cycles WHERE job=? ORDER BY cycle', (job,))]
            for cycle in data['cycles']:
                cycle['diagnostics'] = json.loads(cycle['diagnostics']) if cycle['diagnostics'] else None
        return data

    def list(self, core, actor, project):
        core._owned(actor, project)
        return [self.get(core, actor, r['id'], False) for r in core.db.execute(
            'SELECT id FROM build_jobs WHERE project=? ORDER BY created DESC,rowid DESC LIMIT 50', (project,))]

    def binding(self, core, actor, project, resource, profile, provider):
        workspace = self.runtime._workspace(core, actor, project, resource)
        selected = self.worker.sandbox.profiles.get(profile) if self.worker.sandbox else None
        model = self.runtime.providers.get(provider)
        if selected is None or model is None: raise Conflict('Configured test profile and provider required')
        self.worker.profile(project, resource, profile)
        return checksum({'workspace': os.path.normcase(str(workspace.directory)), 'files': workspace.selected,
                         'create_paths': workspace.create_paths, 'profile': asdict(selected),
                         'protected': {p: workspace.read(p)['sha256'] for p in selected.protected_paths},
                         'provider': getattr(model, 'provider', type(model).__name__), 'model': model.model,
                         'timeout': getattr(model, 'timeout', None), 'max_output_tokens': getattr(model, 'max_output_tokens', None)})

    def create(self, core, actor, project, resource, profile, provider, goal, files, skills,
               max_calls, max_cycles, max_steps, duration_seconds, auto_accept, allow_model_calls,
               request_id, specification=None, start_at=None, start_window_seconds=900):
        if (allow_model_calls is not True or type(auto_accept) is not bool
                or not isinstance(goal, str) or not 1 <= len(goal.strip()) <= 8000
                or not isinstance(files, list) or not 1 <= len(files) <= 20
                or not all(isinstance(p, str) for p in files) or len(set(files)) != len(files)
                or not isinstance(skills, list) or len(skills) > 5 or len(set(skills)) != len(skills)
                or not all(isinstance(s, str) and s in self.runtime.skills for s in skills)
                or not all(type(v) is int and 1 <= v <= 8 for v in (max_calls, max_cycles))
                or type(max_steps) is not int or not 1 <= max_steps <= 100
                or type(duration_seconds) is not int or not 60 <= duration_seconds <= 604800
                or not isinstance(request_id, str) or not 1 <= len(request_id) <= 256):
            raise ValueError('Explicit selected context, call consent and bounded job required')
        if ((start_at is not None and type(start_at) is not int)
                or type(start_window_seconds) is not int or not 60 <= start_window_seconds <= 86400):
            raise ValueError('Bounded UTC scheduled start required')
        scheduled_digest = None
        if start_at is not None:
            core._owned(actor,project)
            scheduled_digest = checksum(['scheduled-v1',resource,profile,provider,goal,files,skills,max_calls,max_cycles,
                                         max_steps,duration_seconds,auto_accept,specification,start_at,start_window_seconds])
            prior = core.db.execute('SELECT id,digest FROM build_jobs WHERE project=? AND request_id=?',(project,request_id)).fetchone()
            if prior:
                if prior['digest'] != scheduled_digest: raise Conflict('Build request reused')
                return self.get(core,actor,prior['id'])
            if not core.clock()+1 <= start_at <= core.clock()+604800:
                raise ValueError('Schedule a future start within seven days')
        binding = self.binding(core, actor, project, resource, profile, provider)
        workspace = self.worker.workspaces[(project, resource)]
        if not set(self.worker.sandbox.profiles[profile].protected_paths) <= set(files):
            raise ValueError('Protected tests must be included in selected model context')
        for path in files: workspace.read(path)
        if len(encode([workspace.read(p) for p in files]).encode()) > 80000:
            raise ValueError('Select at most 80 KB of source for iterative context')
        config = dict(resource=resource, profile=profile, provider=provider, files=files, skills=skills,
                      max_calls=max_calls, max_cycles=max_cycles, max_steps=max_steps, auto_accept=auto_accept,
                      allow_model_calls=True, specification=specification, binding_sha256=binding)
        if start_at is not None:
            config['schedule'] = {'start_at': start_at, 'start_by': start_at+start_window_seconds,
                                  'inputs_sha256': self.input_binding(project,resource)}
            if specification:
                from .specifications import get
                config['schedule']['specification_sha256'] = get(core,actor,specification)['sha256']
        digest = scheduled_digest or checksum([config, goal, duration_seconds])
        with core.transaction():
            policy = core._owned(actor, project)
            if auto_accept and policy['mode'] != 'full': raise Denied('Automatic proposal acceptance requires full policy')
            prior = core.db.execute('SELECT id,digest FROM build_jobs WHERE project=? AND request_id=?', (project, request_id)).fetchone()
            if prior:
                if prior['digest'] != digest: raise Conflict('Build request reused')
                return self.get(core, actor, prior['id'])
            if core.db.execute("SELECT 1 FROM build_jobs WHERE project=? AND json_extract(config,'$.resource')=? AND state NOT IN ('completed','failed','cancelled')", (project, resource)).fetchone():
                raise Conflict('Workspace already has a build job')
            if core.db.execute("SELECT 1 FROM coding_runs WHERE project=? AND resource=? AND state NOT IN ('ready_for_review','failed','cancelled')", (project, resource)).fetchone():
                raise Conflict('Workspace already has an active coding run')
            if specification:
                from .specifications import get
                spec = get(core, actor, specification)
                if spec['project'] != project or spec['state'] != 'approved': raise Conflict('Approved project specification required')
            now = core.clock(); job = uuid.uuid4().hex
            core.db.execute("INSERT INTO build_jobs(id,project,request_id,digest,config,goal,state,phase,cycle,calls,steps,deadline,next_due,summary,created,updated) VALUES(?,?,?,?,?,?,'queued','baseline',1,0,0,?,?,?,?,?)",
                            (job, project, request_id, digest, encode(config), goal, (start_at if start_at is not None else now)+duration_seconds, start_at if start_at is not None else now, encode({'reason': 'scheduled' if start_at is not None else 'queued'}), now, now))
            core.db.execute("INSERT INTO build_cycles(job,cycle,state) VALUES(?,1,'baseline')", (job,))
            core._event(project, 'build_job.created', job)
        return self.get(core, actor, job)

    def input_binding(self, project, resource):
        workspace = self.worker.workspaces[(project,resource)]
        return checksum({path:workspace.read(path)['sha256'] for path in workspace.selected})

    def schedule_admission(self, core, actor, job):
        schedule = job['config'].get('schedule')
        if not schedule: return None
        if job['baseline_task'] is not None:
            # Admission can wait for approval, but bytes remain bound until the
            # first baseline actually dispatches. Model edits after it are allowed.
            if core.task(actor,job['baseline_task'])['state'] not in {'queued','waiting_approval'}: return None
        else:
            if core.clock() < schedule['start_at']: return 'scheduled_not_due'
            if core.clock() > schedule['start_by']: return 'scheduled_start_missed'
        if core.db.execute("SELECT 1 FROM coding_runs WHERE project=? AND resource=? AND id!=? AND state NOT IN ('ready_for_review','failed','cancelled')",
                           (job['project'],job['config']['resource'],job['run'] or '')).fetchone():
            return 'scheduled_workspace_busy'
        try:
            if self.input_binding(job['project'],job['config']['resource']) != schedule['inputs_sha256']:
                return 'scheduled_inputs_changed'
            if job['config'].get('specification'):
                from .specifications import get
                spec = get(core,actor,job['config']['specification'])
                if spec['state'] != 'approved' or spec['sha256'] != schedule['specification_sha256']:
                    return 'scheduled_specification_changed'
        except (ValueError,Denied,OSError,KeyError):
            return 'scheduled_inputs_unavailable'
        return None

    def _update(self, core, job, **fields):
        if not set(fields) <= {'phase', 'cycle', 'proposal', 'run', 'baseline_task'}: raise ValueError('Invalid checkpoint')
        with core.transaction():
            core.db.execute('UPDATE build_jobs SET '+','.join(k+'=?' for k in fields)+' WHERE id=?', (*fields.values(), job))

    def diagnostic(self, core, actor, job, task):
        intent = core.task(actor, task)
        refs = json.loads(intent['evidence'] or '[]')
        if len(refs) != 1: raise Conflict('Exact tested evidence required')
        evidence = self.worker.evidence(refs[0]); report = evidence.get('result', {})
        cfg = job['config']; workspace = self.worker.workspaces[(job['project'], cfg['resource'])]
        if (intent['project'] != job['project'] or intent['resource'] != cfg['resource']
                or intent['action'] != 'execute' or json.loads(intent['payload']) != {'operation':'test','profile':cfg['profile']}
                or intent['state'] not in {'failed', 'succeeded'} or evidence.get('task_id') != task
                or evidence.get('operation') != 'test' or report.get('kind') not in {'native_test','container_test'}
                or report.get('profile') != cfg['profile'] or report.get('termination') is not None
                or report.get('cleanup_confirmed') is not True or type(report.get('exit_code')) is not int
                or report.get('passed') is not (report.get('exit_code') == 0)
                or intent['state'] != ('succeeded' if report.get('exit_code') == 0 else 'failed')
                or report.get('input_hashes') != {p: workspace.read(p)['sha256'] for p in workspace.selected}
                or report.get('profile_sha256') != checksum(asdict(self.worker.sandbox.profiles[cfg['profile']]))):
            raise Conflict('Current verified test inputs and cleanup required')
        data = {'task': task, 'evidence': refs[0], 'exit_code': report['exit_code'],
                'output': str(report.get('output', '')).encode()[:8000].decode(errors='ignore')}
        while len(encode(data).encode()) > 10000: data['output'] = data['output'][:len(data['output'])//2]
        return data

    def _baseline(self, core, actor, job):
        cfg = job['config']; task = job['baseline_task']
        admission = self.schedule_admission(core,actor,job)
        if admission: return ('failed' if admission=='scheduled_start_missed' else 'blocked'), admission
        if task is None:
            task = core.create_task(actor, job['project'], 'execute', cfg['resource'], {'operation': 'test', 'profile': cfg['profile']}, 'build-baseline:'+job['id'])
            self._update(core, job['id'], baseline_task=task)
        state = core.task(actor, task)['state']
        if state in {'queued','waiting_approval'}:
            claim = core.start(actor, task)
            if claim['state'] == 'waiting_approval': return 'waiting_approval', 'baseline_approval'
            self.worker.perform(core, actor, task, claim['lease_token'])
        state = core.task(actor, task)['state']
        if state == 'cancelled': return 'cancelled', 'baseline_cancelled_or_rejected'
        if state in {'running','interrupted','cancellation_requested','cancellation_unconfirmed'}:
            return 'blocked', 'baseline_requires_reconciliation'
        data = self.diagnostic(core, actor, job, task)
        with core.transaction():
            core.db.execute('UPDATE build_cycles SET baseline_task=?,diagnostics=?,state=? WHERE job=? AND cycle=?',
                            (task, encode(data), 'baseline_passed' if data['exit_code'] == 0 else 'propose', job['id'], job['cycle']))
        self._update(core, job['id'], phase='done' if data['exit_code'] == 0 else 'propose')
        return ('completed', 'baseline_passed_no_repair') if data['exit_code'] == 0 else ('queued', 'failing_baseline_verified')

    def _propose(self, core, actor, job):
        cfg = job['config']
        if job['proposal']:
            previous = self.runtime.get(core, actor, job['proposal'])
            if previous['state'] == 'ready':
                self.runtime._fresh(core, actor, previous)
                self._update(core, job['id'], phase='review')
                return 'queued', 'saved_proposal_recovered_without_call'
            if previous['state'] in {'generating','failed','interrupted'}:
                return 'blocked', 'inspect_reserved_model_call'
        if job['calls'] >= cfg['max_calls']: return 'budget_limited', 'model_call_budget'
        cycle = core.db.execute('SELECT * FROM build_cycles WHERE job=? AND cycle=?', (job['id'],job['cycle'])).fetchone()
        # Recheck the diagnostic provenance immediately before selecting external context.
        diagnostic = self.diagnostic(core, actor, job, cycle['baseline_task'])
        if diagnostic['exit_code'] == 0: raise Conflict('A failing test is required for repair generation')
        proposal = self.runtime.create(core, actor, job['project'], cfg['resource'], cfg['profile'], cfg['provider'],
            job['goal'], cfg['files'], cfg['skills'], 'build:'+job['id']+':'+str(job['cycle']), cfg['specification'], diagnostic)
        self._update(core, job['id'], proposal=proposal)
        with core.transaction():
            core.db.execute('UPDATE build_cycles SET proposal=?,diagnostics=?,state=? WHERE job=? AND cycle=?',
                            (proposal, encode(diagnostic), 'generating', job['id'], job['cycle']))
            control = core.db.execute('SELECT control FROM build_jobs WHERE id=?', (job['id'],)).fetchone()['control']
            if control: return 'paused' if control == 'pause' else 'cancelled', 'owner_'+control
            core.db.execute('UPDATE build_jobs SET calls=calls+1 WHERE id=?', (job['id'],))
            core._event(job['project'], 'build_job.model_call_reserved', job['id'])
        response = self.runtime.generate(core, actor, proposal)
        with core.transaction():
            core.db.execute('UPDATE build_cycles SET state=? WHERE job=? AND cycle=?',
                            ('review' if response['state']=='ready' else response['state'],job['id'],job['cycle']))
        if response['state'] != 'ready': return 'failed', response['error'] or response['state']
        self._update(core, job['id'], phase='review')
        return 'queued', 'proposal_ready'

    def accept(self, core, actor, job_id, context_sha256, response_sha256):
        with core.transaction():
            job = self.get(core, actor, job_id)
            proposal = self.runtime.get(core, actor, job['proposal']) if job['proposal'] else None
            if proposal is None or proposal['context_sha256'] != context_sha256 or checksum(proposal['response']) != response_sha256:
                raise Conflict('Review the exact current proposal')
            if job['phase'] == 'execute' and proposal['state'] == 'accepted': return job
            if job['state'] != 'waiting_review' or job['phase'] != 'review': raise Conflict('Job is not awaiting proposal review')
            cfg = job['config']
            if core.clock() >= job['deadline'] or job['steps'] >= cfg['max_steps']: raise Conflict('Job budget exhausted')
            if self.binding(core,actor,job['project'],cfg['resource'],cfg['profile'],cfg['provider']) != cfg['binding_sha256']:
                raise Conflict('Job configuration changed')
            self._accept(core, actor, job, proposal)
            core.db.execute("UPDATE build_jobs SET state='queued',next_due=?,updated=? WHERE id=?", (core.clock(), core.clock(), job_id))
        return self.get(core, actor, job_id)

    def _accept(self, core, actor, job, proposal):
        accepted = self.runtime._accept(core, actor, proposal['id'])
        core.db.execute("UPDATE build_jobs SET run=?,phase='execute' WHERE id=?", (accepted['run'], job['id']))
        core.db.execute("UPDATE build_cycles SET run=?,state='execute' WHERE job=? AND cycle=?", (accepted['run'],job['id'],job['cycle']))
        core._event(job['project'], 'build_job.proposal_accepted', job['id'])

    def _execute(self, core, actor, job):
        run = self.workflow.advance(core, actor, job['run'])
        if run['state'] == 'ready_for_review':
            with core.transaction():
                core.db.execute("UPDATE build_cycles SET state='completed' WHERE job=? AND cycle=?", (job['id'],job['cycle']))
                core.db.execute("UPDATE build_jobs SET phase='done' WHERE id=?", (job['id'],))
            return 'completed', 'tested_repair_ready'
        if run['state'] == 'waiting_approval': return 'waiting_approval', 'coding_action_approval'
        if run['state'] in {'blocked','running','interrupted','cancellation_requested'}: return 'blocked', 'coding_step_requires_review'
        if run['state'] == 'cancelled': return 'cancelled', 'coding_run_cancelled'
        if run['state'] != 'failed': return 'queued', 'coding_step_completed'
        last = run['results'][-1] if run['results'] else None
        if last is None: return 'blocked', 'failed_run_without_test_evidence'
        data = self.diagnostic(core, actor, job, last['task_id'])
        if data['exit_code'] == 0: return 'blocked', 'failure_is_not_a_failing_retest'
        cfg = job['config']
        with core.transaction():
            core.db.execute("UPDATE build_cycles SET diagnostics=?,state='failed_retest' WHERE job=? AND cycle=?", (encode(data),job['id'],job['cycle']))
            if job['cycle'] >= cfg['max_cycles'] or job['calls'] >= cfg['max_calls']: return 'budget_limited', 'repair_cycle_or_call_budget'
            cycle = job['cycle']+1
            core.db.execute("INSERT INTO build_cycles(job,cycle,baseline_task,diagnostics,state) VALUES(?,?,?,?,'propose')", (job['id'],cycle,last['task_id'],encode(data)))
            core.db.execute("UPDATE build_jobs SET cycle=?,baseline_task=?,proposal=NULL,run=NULL,phase='propose' WHERE id=?", (cycle,last['task_id'],job['id']))
        return 'queued', 'next_repair_cycle'

    def control(self, core, actor, job_id, action):
        if action not in {'pause','resume','cancel'}: raise ValueError('Unknown job control')
        with core.transaction():
            job = self.get(core, actor, job_id)
            if job['state'] in {'completed','failed','cancelled'}: raise Conflict('Job is terminal')
            if job['control'] == 'cancel' and action != 'cancel': raise Conflict('Cancellation is sticky')
            if action == 'resume':
                if job['state'] not in {'paused','blocked'}: raise Conflict('Cannot resume this job')
                if core.clock() >= job['deadline'] or job['steps'] >= job['config']['max_steps']: raise Conflict('Job budget exhausted')
                if job['proposal'] and self.runtime.get(core, actor, job['proposal'])['state'] in {'generating','failed','interrupted'}:
                    raise Conflict('Generation must be inspected; no automatic paid replay')
                task = self._task(core, actor, job)
                if task and core.task(actor, task)['state'] in {'running','interrupted','cancellation_requested','cancellation_unconfirmed'}:
                    raise Conflict('Reconcile the active task first')
                admission = self.schedule_admission(core,actor,job)
                if admission and admission != 'scheduled_not_due':
                    raise Conflict('Cancel and review a new scheduled job; original admission is no longer valid')
                state, control = 'queued', None
            else:
                state, control = ('running',action) if job['state'] == 'running' else ('paused' if action == 'pause' else 'cancelled',None)
            due = core.clock()
            if action == 'resume' and job['config'].get('schedule') and job['baseline_task'] is None:
                due = max(due,job['config']['schedule']['start_at'])
            core.db.execute('UPDATE build_jobs SET state=?,control=?,next_due=?,updated=? WHERE id=?', (state,control,due,core.clock(),job_id))
            core._event(job['project'], 'build_job.'+action, job_id)
        if action == 'cancel':
            if job['proposal'] and self.runtime.get(core, actor, job['proposal'])['state'] in {'planned','generating','ready'}:
                self.runtime.interrupt(core, actor, job['proposal'])
            if job['run'] and self.workflow.get(core, actor, job['run'])['state'] not in {'failed','ready_for_review','cancelled'}:
                self.workflow.cancel(core, actor, job['run'])
            elif job['baseline_task'] and core.task(actor, job['baseline_task'])['state'] not in {'succeeded','failed','cancelled'}:
                core.cancel(actor, job['baseline_task'])
        return self.get(core, actor, job_id)

    def _task(self, core, actor, job):
        return self.workflow.get(core, actor, job['run'])['task'] if job['run'] else job['baseline_task']

    def tick(self, core, actor, project):
        recovered = recover(core, actor, project)
        with core.transaction():
            if busy(core, project): return {'build_job': None, 'recovered': recovered}
            row = core.db.execute("SELECT id FROM build_jobs WHERE project=? AND state IN ('queued','waiting_approval','waiting_review') AND next_due<=? ORDER BY next_due,rowid LIMIT 1", (project, core.clock())).fetchone()
            if row is None: return {'build_job': None, 'recovered': recovered}
            job = self.get(core, actor, row['id']); cfg = job['config']; now = core.clock()
            if now >= job['deadline'] or job['steps'] >= cfg['max_steps']:
                core.db.execute("UPDATE build_jobs SET state='budget_limited',summary=?,updated=? WHERE id=?", (encode({'reason':'deadline_or_step_budget'}),now,job['id']))
                core._event(project,'build_job.budget_limited',job['id'])
                return {'build_job': self.get(core, actor, job['id']), 'recovered': recovered}
            admission = self.schedule_admission(core,actor,job)
            if admission == 'scheduled_not_due':
                core.db.execute('UPDATE build_jobs SET next_due=? WHERE id=?',(cfg['schedule']['start_at'],job['id']))
                return {'build_job':self.get(core,actor,job['id']),'recovered':recovered}
            if admission:
                state = 'failed' if admission == 'scheduled_start_missed' else 'blocked'
                core.db.execute('UPDATE build_jobs SET state=?,summary=?,updated=? WHERE id=?',(state,encode({'reason':admission}),now,job['id']))
                core._event(project,'build_job.'+state,job['id'])
                return {'build_job':self.get(core,actor,job['id']),'recovered':recovered}
            task = self._task(core, actor, job)
            if job['phase']=='review' and job['proposal'] and self.runtime.get(core,actor,job['proposal'])['state'] in {'failed','interrupted'}:
                core.db.execute("UPDATE build_jobs SET state='blocked',summary=?,updated=? WHERE id=?", (encode({'reason':'proposal_no_longer_available'}),now,job['id']))
                core._event(project,'build_job.blocked',job['id'])
                return {'build_job':self.get(core,actor,job['id']),'recovered':recovered}
            pending = task and core.db.execute("SELECT 1 FROM approvals WHERE task=? AND state='pending' AND expires>? AND version=?", (task,now,core._owned(actor,project)['version'])).fetchone()
            if (job['state'] == 'waiting_approval' and pending) or (job['state'] == 'waiting_review' and (not cfg['auto_accept'] or core._owned(actor,project)['mode'] != 'full')):
                core.db.execute('UPDATE build_jobs SET next_due=? WHERE id=?', (now+5,job['id']))
                return {'build_job': self.get(core, actor, job['id']), 'recovered': recovered}
            token = uuid.uuid4().hex
            core.db.execute("UPDATE build_jobs SET state='running',steps=steps+1,lease_token=?,lease_until=?,updated=? WHERE id=?", (token,now+600,now,job['id']))
            core.db.execute("INSERT INTO build_attempts VALUES(?,?,?,?,NULL,'dispatched')", (token,job['id'],job['phase'],now))
            core._event(project, 'build_job.dispatched', job['id'])
        try:
            if self.binding(core,actor,project,cfg['resource'],cfg['profile'],cfg['provider']) != cfg['binding_sha256']:
                raise Conflict('Reviewed job configuration changed')
            if job['phase'] == 'baseline': state, reason = self._baseline(core,actor,job)
            elif job['phase'] == 'propose': state, reason = self._propose(core,actor,job)
            elif job['phase'] == 'review':
                if cfg['auto_accept'] and core._owned(actor,project)['mode'] == 'full':
                    with core.transaction(): self._accept(core,actor,job,self.runtime.get(core,actor,job['proposal']))
                    state, reason = 'queued', 'proposal_auto_accepted'
                else: state, reason = 'waiting_review', 'review_exact_proposal'
            elif job['phase'] == 'execute': state, reason = self._execute(core,actor,job)
            else: raise Conflict('Unknown job phase')
        except (ValueError,Denied,RuntimeError,OSError): state, reason = 'blocked','step_requires_review'
        with core.transaction():
            latest = self.get(core, actor, job['id'])
            row = core.db.execute('SELECT lease_token FROM build_jobs WHERE id=?', (job['id'],)).fetchone()
            if row['lease_token'] != token: raise Conflict('Job lease lost; inspect effects')
            if latest['control']: state, reason = ('paused' if latest['control'] == 'pause' else 'cancelled'), 'owner_'+latest['control']
            task = self._task(core,actor,latest)
            uncertain = bool(task and core.task(actor,task)['state'] in {'running','interrupted','cancellation_requested','cancellation_unconfirmed'})
            refund = state in {'waiting_approval','waiting_review'} or (state == 'blocked' and not uncertain and latest['calls'] == job['calls'])
            summary = {'reason':reason,'phase':latest['phase'],'cycle':latest['cycle'],'model_calls_reserved':latest['calls'],
                       'proposal':latest['proposal'],'run':latest['run'],'task':task,'uncertain_task':uncertain,'source_delivery':'separate_review_required'}
            if latest['proposal']:
                proposal = self.runtime.get(core,actor,latest['proposal']); summary['last_reported_usage'] = proposal['usage']
            core.db.execute('UPDATE build_jobs SET state=?,steps=steps-?,lease_token=NULL,lease_until=NULL,control=NULL,summary=?,next_due=?,updated=? WHERE id=?',
                            (state,1 if refund else 0,encode(summary),core.clock()+(5 if state.startswith('waiting') else 1),core.clock(),job['id']))
            core.db.execute('UPDATE build_attempts SET finished=?,outcome=? WHERE token=?', (core.clock(),state,token))
            core._event(project,'build_job.'+state,job['id'])
        return {'build_job': self.get(core,actor,job['id']), 'recovered':recovered}
