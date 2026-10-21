"""Bounded model/test repair cycles with separately reviewed proposals and call reservations."""
from dataclasses import asdict
import hashlib
import json
import os
import uuid

from .store import Conflict, Denied, encode
from .dispatch import busy, recover, supervisor, status
from .limits import SELECTED_CONTEXT_FILES, SELECTED_CONTEXT_BYTES


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
        data['supervision'] = status(core, actor, 'build_jobs', job)
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
        generation = {'generation':{'thinking_level':model.thinking_level}} if getattr(model,'thinking_level',None) is not None else {}
        return checksum({'workspace': os.path.normcase(str(workspace.directory)), 'files': workspace.selected,
                         'create_paths': workspace.create_paths, 'profile': asdict(selected),
                         'protected': {p: workspace.read(p)['sha256'] for p in selected.protected_paths},
                         'provider': getattr(model, 'provider', type(model).__name__), 'model': model.model,
                         'timeout': getattr(model, 'timeout', None), 'max_output_tokens': getattr(model, 'max_output_tokens', None), **generation})

    def create(self, core, actor, project, resource, profile, provider, goal, files, skills,
               max_calls, max_cycles, max_steps, duration_seconds, auto_accept, allow_model_calls,
               request_id, specification=None, start_at=None, start_window_seconds=900, mode='repair', conversation=None,
               context_mode='selected', edit_protocol='legacy-v1', expected_skills=None):
        if (edit_protocol not in {'legacy-v1','host-bound-v2'} or context_mode not in {'selected','retrieve'} or mode not in {'repair', 'feature'} or allow_model_calls is not True or type(auto_accept) is not bool
                or not isinstance(goal, str) or not 1 <= len(goal.strip()) <= 8000
                or not isinstance(files, list) or not 1 <= len(files) <= (100 if context_mode == 'retrieve' else SELECTED_CONTEXT_FILES)
                or not all(isinstance(p, str) for p in files) or len(set(files)) != len(files)
                or not isinstance(skills, list) or len(skills) > 5 or len(set(skills)) != len(skills)
                or not all(isinstance(s, str) and s in self.runtime.skills for s in skills)
                or not all(type(v) is int and 1 <= v <= 8 for v in (max_calls, max_cycles))
                or type(max_steps) is not int or not 1 <= max_steps <= 100
                or type(duration_seconds) is not int or not 60 <= duration_seconds <= 604800
                or not isinstance(request_id, str) or not 1 <= len(request_id) <= 256):
            raise ValueError('Explicit selected context, call consent and bounded job required')
        self.runtime.check_skill_bindings(skills,expected_skills,verify_current=False)
        if ((start_at is not None and type(start_at) is not int)
                or type(start_window_seconds) is not int or not 60 <= start_window_seconds <= 86400):
            raise ValueError('Bounded UTC scheduled start required')
        scheduled_digest = None
        if conversation is not None:
            if not isinstance(conversation, str) or not 1 <= len(conversation) <= 256:
                raise ValueError('Conversation identifier required')
            if core.conversation_project(actor, conversation) != project:
                raise Denied('Coding history must belong to this project')
        if start_at is not None:
            core._owned(actor,project)
            scheduled_digest = checksum(['scheduled-v1',resource,profile,provider,goal,files,skills,max_calls,max_cycles,
                                         max_steps,duration_seconds,auto_accept,specification,start_at,start_window_seconds])
            if mode == 'feature': scheduled_digest = checksum([scheduled_digest, mode])
            if conversation is not None: scheduled_digest = checksum([scheduled_digest, 'conversation', conversation])
            if context_mode == 'retrieve': scheduled_digest = checksum([scheduled_digest, 'context_mode', context_mode])
            if edit_protocol == 'host-bound-v2': scheduled_digest = checksum([scheduled_digest, 'edit_protocol', edit_protocol])
            if expected_skills is not None: scheduled_digest = checksum([scheduled_digest,'expected_skills',expected_skills])
            prior = core.db.execute('SELECT id,digest FROM build_jobs WHERE project=? AND request_id=?',(project,request_id)).fetchone()
            if prior:
                if prior['digest'] != scheduled_digest: raise Conflict('Build request reused')
                return self.get(core,actor,prior['id'])
            if not core.clock()+1 <= start_at <= core.clock()+604800:
                raise ValueError('Schedule a future start within seven days')
        binding = self.binding(core, actor, project, resource, profile, provider)
        self.runtime.check_skill_bindings(skills,expected_skills)
        workspace = self.worker.workspaces[(project, resource)]
        if not set(self.worker.sandbox.profiles[profile].protected_paths) <= set(files):
            raise ValueError('Protected tests must be included in selected model context')
        for path in files: workspace.read(path)
        if context_mode == 'selected' and len(encode([workspace.read(p) for p in files]).encode()) > SELECTED_CONTEXT_BYTES:
            raise ValueError('Select at most 96 KB of source for iterative context')
        config = dict(resource=resource, profile=profile, provider=provider, files=files, skills=skills,
                      max_calls=max_calls, max_cycles=max_cycles, max_steps=max_steps, auto_accept=auto_accept,
                      allow_model_calls=True, specification=specification, binding_sha256=binding)
        if mode == 'feature': config['mode'] = mode
        if conversation is not None: config['conversation'] = conversation
        if context_mode == 'retrieve': config['context_mode'] = context_mode
        if edit_protocol == 'host-bound-v2': config['edit_protocol'] = edit_protocol
        if expected_skills is not None: config['skill_bindings'] = dict(expected_skills)
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
            if conversation is not None:
                core.db.execute('INSERT INTO coding_job_links VALUES(?,?)', (job, conversation))
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

    def _baseline(self, core, actor, job, supervise=None):
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
            self.worker.perform(core, actor, task, claim['lease_token'], supervise=supervise)
        state = core.task(actor, task)['state']
        if state == 'cancelled': return 'cancelled', 'baseline_cancelled_or_rejected'
        if state in {'running','interrupted','cancellation_requested','cancellation_unconfirmed'}:
            return 'blocked', 'baseline_requires_reconciliation'
        data = self.diagnostic(core, actor, job, task)
        needs_work = data['exit_code'] != 0 or cfg.get('mode') == 'feature'
        next_phase = ('retrieve' if cfg.get('context_mode') == 'retrieve' else 'propose') if needs_work else 'done'
        with core.transaction():
            core.db.execute('UPDATE build_cycles SET baseline_task=?,diagnostics=?,state=? WHERE job=? AND cycle=?',
                            (task, encode(data), next_phase if needs_work else 'baseline_passed', job['id'], job['cycle']))
        self._update(core, job['id'], phase=next_phase)
        if not needs_work: return 'completed', 'baseline_passed_no_repair'
        return 'queued', 'feature_baseline_verified' if cfg.get('mode') == 'feature' else 'failing_baseline_verified'

    def _retrieve(self, core, actor, job):
        cfg = job['config']
        cycle = core.db.execute('SELECT * FROM build_cycles WHERE job=? AND cycle=?', (job['id'],job['cycle'])).fetchone()
        diagnostic = self.diagnostic(core, actor, job, cycle['baseline_task'])
        retry = json.loads(cycle['diagnostics'] or '{}').get('generation_retry')
        if retry: diagnostic['generation_retry'] = retry
        review = json.loads(cycle['diagnostics'] or '{}').get('proposal_review')
        if review: diagnostic['proposal_review'] = review
        pending = json.loads(cycle['diagnostics'] or '{}').get('pending_review')
        if pending: diagnostic['pending_review'] = pending
        payload = {'operation':'retrieve', 'paths':cfg['files'], 'profile':cfg['profile'],
                   'query':(job['goal']+'\n'+diagnostic['output'])[:16000]}
        task = core.create_task(actor, job['project'], 'read', cfg['resource'], payload,
                                'build-context:'+job['id']+':'+str(job['cycle']))
        with core.transaction():
            core.db.execute('UPDATE build_cycles SET diagnostics=? WHERE job=? AND cycle=?',
                            (encode({**diagnostic,'context_task':task}), job['id'], job['cycle']))
        state = core.task(actor, task)['state']
        if state in {'queued','waiting_approval'}:
            claim = core.start(actor, task)
            if claim['state'] == 'waiting_approval': return 'waiting_approval','context_approval'
            self.worker.perform(core, actor, task, claim['lease_token'])
        state = core.task(actor, task)['state']
        if state == 'cancelled': return 'cancelled','context_cancelled'
        if state != 'succeeded': return 'blocked','context_requires_reconciliation'
        self.runtime.retrieval(core,actor,job['project'],cfg['resource'],cfg['profile'],task)
        with core.transaction():
            core.db.execute("UPDATE build_cycles SET state='propose' WHERE job=? AND cycle=?", (job['id'],job['cycle']))
        self._update(core,job['id'],phase='propose')
        return 'queued','context_retrieved'

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
        retry = json.loads(cycle['diagnostics'] or '{}').get('generation_retry')
        if retry: diagnostic['generation_retry'] = retry
        review = json.loads(cycle['diagnostics'] or '{}').get('proposal_review')
        if review: diagnostic['proposal_review'] = review
        pending = json.loads(cycle['diagnostics'] or '{}').get('pending_review')
        if pending: diagnostic['pending_review'] = pending
        if diagnostic['exit_code'] == 0 and cfg.get('mode') != 'feature':
            raise Conflict('A failing test is required for repair generation')
        retrieval_task = None; files = cfg['files']
        if cfg.get('context_mode') == 'retrieve':
            retrieval_task = json.loads(cycle['diagnostics'])['context_task']
            retrieved, _ = self.runtime.retrieval(core,actor,job['project'],cfg['resource'],cfg['profile'],retrieval_task)
            files = [record['path'] for record in retrieved['files']]
            diagnostic['context_task'] = retrieval_task
        proposal = self.runtime.create(core, actor, job['project'], cfg['resource'], cfg['profile'], cfg['provider'],
            job['goal'], files, cfg['skills'], 'build:'+job['id']+':'+str(job['cycle']), cfg['specification'], diagnostic,
            mode=cfg.get('mode', 'repair'), retrieval_task=retrieval_task, edit_protocol=cfg.get('edit_protocol','legacy-v1'),
            expected_skills=self.check_job_skills(job))
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
            self.check_job_skills(job)
            if core.clock() >= job['deadline'] or job['steps'] >= cfg['max_steps']: raise Conflict('Job budget exhausted')
            if self.binding(core,actor,job['project'],cfg['resource'],cfg['profile'],cfg['provider']) != cfg['binding_sha256']:
                raise Conflict('Job configuration changed')
            self._accept(core, actor, job, proposal)
            core.db.execute("UPDATE build_jobs SET state='queued',next_due=?,updated=? WHERE id=?", (core.clock(), core.clock(), job_id))
        return self.get(core, actor, job_id)

    def request_revision(self, core, actor, job_id, proposal_id, context_sha256,
                         response_sha256, feedback, allow_model_call):
        """Retain a rejected proposal and request a correction within original budgets."""
        if (allow_model_call is not True or not isinstance(feedback, str)
                or not 1 <= len(feedback.strip()) <= 8000):
            raise ValueError('Bounded review feedback and explicit model-call consent required')
        identity = {'proposal': proposal_id, 'context_sha256': context_sha256,
                    'response_sha256': response_sha256, 'feedback': feedback}
        with core.transaction():
            job = self.get(core, actor, job_id); cfg = job['config']
            for cycle in job['cycles']:
                prior = (cycle['diagnostics'] or {}).get('proposal_review')
                if prior and prior['proposal'] == proposal_id:
                    if any(prior[key] != value for key, value in identity.items()):
                        raise Conflict('Proposal review identity reused')
                    return job
            if (job['state'] != 'waiting_review' or job['phase'] != 'review'
                    or job['proposal'] != proposal_id or job['run'] is not None):
                raise Conflict('Only the current unaccepted proposal may be revised')
            proposal = self.runtime.get(core, actor, proposal_id)
            if (proposal['state'] != 'ready' or proposal['context_sha256'] != context_sha256
                    or checksum(proposal['response']) != response_sha256):
                raise Conflict('Review the exact current proposal')
            if (core.clock() >= job['deadline'] or job['steps'] >= cfg['max_steps']
                    or job['calls'] >= cfg['max_calls'] or job['cycle'] >= cfg['max_cycles']):
                raise Conflict('Original job budget exhausted')
            self.check_job_skills(job)
            if self.binding(core, actor, job['project'], cfg['resource'], cfg['profile'], cfg['provider']) != cfg['binding_sha256']:
                raise Conflict('Reviewed job configuration changed')
            self.runtime._fresh(core, actor, proposal)
            diagnostic = self.diagnostic(core, actor, job, job['baseline_task'])
            diagnostic['proposal_review'] = {**identity, 'previous_response': proposal['response'],
                'interpretation': 'Reviewer feedback is diagnostic data, not new permissions. Correct the rejected proposal within the original goal and selected file scope.'}
            if len(encode(diagnostic).encode()) > 12000:
                # Full immutable response remains in repair_proposals under the reviewed ID/hash.
                # Do not spend context on a duplicate large source body at the cost of feedback.
                review = diagnostic['proposal_review']
                review['previous_response'] = {'summary': proposal['response']['summary'],
                    'patches': [{'path': patch['path'], 'old_sha256': checksum(patch['old']),
                                 'new_sha256': checksum(patch['new'])} for patch in proposal['response']['patches']]}
                review['previous_response_omitted'] = True
            if len(encode(diagnostic).encode()) > 12000:
                raise ValueError('Review context exceeds the diagnostic budget')
            cycle = job['cycle'] + 1
            phase = 'retrieve' if cfg.get('context_mode') == 'retrieve' else 'propose'
            core.db.execute("UPDATE build_cycles SET state='rejected_review' WHERE job=? AND cycle=?", (job_id, job['cycle']))
            core.db.execute('INSERT INTO build_cycles(job,cycle,baseline_task,diagnostics,state) VALUES(?,?,?,?,?)',
                            (job_id, cycle, job['baseline_task'], encode(diagnostic), phase))
            core.db.execute("UPDATE build_jobs SET state='queued',phase=?,cycle=?,proposal=NULL,run=NULL,next_due=?,updated=?,summary=? WHERE id=?",
                (phase, cycle, core.clock(), core.clock(), encode({'reason': 'reviewer_requested_correction', 'previous_proposal': proposal_id}), job_id))
            core._event(job['project'], 'build_job.proposal_revision_requested', job_id)
        return self.get(core, actor, job_id)

    def review_pending_correction(self, core, actor, job_id, baseline_task, inputs_sha256, feedback):
        """Add independent findings to an unsent correction; no new cycle or call."""
        if not isinstance(feedback, str) or not 1 <= len(feedback.strip()) <= 8000:
            raise ValueError('Bounded review feedback required')
        with core.transaction():
            job = self.get(core, actor, job_id); cfg = job['config']
            if (job['state'] != 'queued' or job['phase'] not in {'propose', 'retrieve'}
                    or job['proposal'] is not None or job['baseline_task'] != baseline_task):
                raise Conflict('Review the exact unsent correction baseline')
            if (core.clock() >= job['deadline'] or job['steps'] >= cfg['max_steps']
                    or job['calls'] >= cfg['max_calls']):
                raise Conflict('Original job budget exhausted')
            self.check_job_skills(job)
            if self.binding(core, actor, job['project'], cfg['resource'], cfg['profile'], cfg['provider']) != cfg['binding_sha256']:
                raise Conflict('Reviewed job configuration changed')
            workspace = self.worker.workspaces[(job['project'], cfg['resource'])]
            observed = checksum({path: workspace.read(path)['sha256'] for path in workspace.selected})
            if observed != inputs_sha256: raise Conflict('Review exact current inputs')
            diagnostic = self.diagnostic(core, actor, job, baseline_task)
            if diagnostic['exit_code'] == 0: raise Conflict('Failing correction baseline required')
            identity = {'baseline_task': baseline_task, 'inputs_sha256': observed, 'feedback': feedback}
            cycle = job['cycles'][-1]
            prior = (cycle['diagnostics'] or {}).get('pending_review')
            if prior:
                if prior != identity: raise Conflict('Pending review identity reused')
                return job
            data = {**(cycle['diagnostics'] or {}), 'pending_review': identity}
            if len(encode(data).encode()) > 12000: raise ValueError('Review context exceeds the diagnostic budget')
            core.db.execute('UPDATE build_cycles SET diagnostics=? WHERE job=? AND cycle=?',
                            (encode(data), job_id, job['cycle']))
            core._event(job['project'], 'build_job.pending_correction_reviewed', job_id)
        return self.get(core, actor, job_id)

    def request_tested_revision(self, core, actor, job_id, run_id, inputs_sha256, feedback, allow_model_call):
        """Owner's independent review may withhold a tested run before source delivery."""
        if (allow_model_call is not True or not isinstance(feedback, str)
                or not 1 <= len(feedback.strip()) <= 8000):
            raise ValueError('Bounded independent feedback and explicit new-call consent required')
        with core.transaction():
            job = self.get(core, actor, job_id); cfg = job['config']
            for cycle in job['cycles']:
                prior = (cycle['diagnostics'] or {}).get('proposal_review')
                if prior and prior.get('tested_run') == run_id:
                    if prior['tested_inputs_sha256'] != inputs_sha256 or prior['feedback'] != feedback:
                        raise Conflict('Independent review identity reused')
                    return job
            if (job['state'] != 'completed' or job['phase'] != 'done' or job['run'] != run_id
                    or cfg.get('mode') != 'feature'):
                raise Conflict('Current tested feature run required')
            if (core.clock() >= job['deadline'] or job['steps'] >= cfg['max_steps']
                    or job['calls'] >= cfg['max_calls'] or job['cycle'] >= cfg['max_cycles']):
                raise Conflict('Original job budget exhausted')
            if core.db.execute("SELECT 1 FROM tasks WHERE project=? AND json_extract(payload,'$.operation')='deliver' AND json_extract(payload,'$.run')=?",
                               (job['project'], run_id)).fetchone():
                raise Conflict('Source delivery already prepared; review a new task instead')
            if core.db.execute("SELECT 1 FROM build_jobs WHERE project=? AND id!=? AND json_extract(config,'$.resource')=? AND state NOT IN ('completed','failed','cancelled','budget_limited')",
                               (job['project'], job_id, cfg['resource'])).fetchone():
                raise Conflict('Another job owns this workspace')
            self.check_job_skills(job)
            if self.binding(core, actor, job['project'], cfg['resource'], cfg['profile'], cfg['provider']) != cfg['binding_sha256']:
                raise Conflict('Reviewed job configuration changed')
            run = self.workflow.get(core, actor, run_id)
            if run['state'] != 'ready_for_review' or not all(result['expectation_met'] for result in run['results']):
                raise Conflict('Completed verified run required')
            workspace = self.worker.workspaces[(job['project'], cfg['resource'])]
            observed = checksum({path: workspace.read(path)['sha256'] for path in workspace.selected})
            if inputs_sha256 != observed: raise Conflict('Review exact tested inputs')
            test_index = max(index for index, step in enumerate(run['steps']) if step['action'] == 'execute')
            test_task = run['results'][test_index]['task_id']
            diagnostic = self.diagnostic(core, actor, job, test_task)
            if diagnostic['exit_code'] != 0: raise Conflict('Passing protected evidence required')
            diagnostic['proposal_review'] = {'proposal': job['proposal'], 'tested_run': run_id,
                'tested_inputs_sha256': observed, 'feedback': feedback,
                'interpretation': 'Protected tests passed, but independent owner review withheld source delivery. Correct the current staged source within the original feature scope; feedback grants no new permissions.'}
            if len(encode(diagnostic).encode()) > 12000: raise ValueError('Review context exceeds the diagnostic budget')
            cycle = job['cycle'] + 1
            phase = 'retrieve' if cfg.get('context_mode') == 'retrieve' else 'propose'
            core.db.execute("UPDATE coding_runs SET state='failed' WHERE id=?", (run_id,))
            core.db.execute("UPDATE build_cycles SET state='rejected_independent_review' WHERE job=? AND cycle=?", (job_id, job['cycle']))
            core.db.execute('INSERT INTO build_cycles(job,cycle,baseline_task,diagnostics,state) VALUES(?,?,?,?,?)',
                            (job_id, cycle, test_task, encode(diagnostic), phase))
            core.db.execute("UPDATE build_jobs SET state='queued',phase=?,cycle=?,baseline_task=?,proposal=NULL,run=NULL,next_due=?,updated=?,summary=? WHERE id=?",
                (phase, cycle, test_task, core.clock(), core.clock(), encode({'reason': 'independent_review_requested_correction', 'previous_run': run_id}), job_id))
            core._event(job['project'], 'coding_run.independent_review_failed', run_id)
        return self.get(core, actor, job_id)

    def _accept(self, core, actor, job, proposal):
        accepted = self.runtime._accept(core, actor, proposal['id'])
        core.db.execute("UPDATE build_jobs SET run=?,phase='execute' WHERE id=?", (accepted['run'], job['id']))
        core.db.execute("UPDATE build_cycles SET run=?,state='execute' WHERE job=? AND cycle=?", (accepted['run'],job['id'],job['cycle']))
        core._event(job['project'], 'build_job.proposal_accepted', job['id'])

    def _execute(self, core, actor, job, supervise=None):
        run = self.workflow.advance(core, actor, job['run'], supervise)
        if run['state'] == 'ready_for_review':
            with core.transaction():
                core.db.execute("UPDATE build_cycles SET state='completed' WHERE job=? AND cycle=?", (job['id'],job['cycle']))
                core.db.execute("UPDATE build_jobs SET phase='done' WHERE id=?", (job['id'],))
            return 'completed', 'tested_feature_ready_for_review' if job['config'].get('mode') == 'feature' else 'tested_repair_ready'
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
            previous = core.db.execute('SELECT diagnostics FROM build_cycles WHERE job=? AND cycle=?',(job['id'],job['cycle'])).fetchone()
            retained = json.loads(previous['diagnostics'] or '{}')
            cycle_data = {**data, **{key:retained[key] for key in ('context_task','generation_retry') if key in retained}}
            core.db.execute("UPDATE build_cycles SET diagnostics=?,state='failed_retest' WHERE job=? AND cycle=?", (encode(cycle_data),job['id'],job['cycle']))
            if job['cycle'] >= cfg['max_cycles'] or job['calls'] >= cfg['max_calls']: return 'budget_limited', 'repair_cycle_or_call_budget'
            cycle = job['cycle']+1
            next_phase = 'retrieve' if cfg.get('context_mode') == 'retrieve' else 'propose'
            core.db.execute("INSERT INTO build_cycles(job,cycle,baseline_task,diagnostics,state) VALUES(?,?,?,?,?)", (job['id'],cycle,last['task_id'],encode(data),next_phase))
            core.db.execute("UPDATE build_jobs SET cycle=?,baseline_task=?,proposal=NULL,run=NULL,phase=? WHERE id=?", (cycle,last['task_id'],next_phase,job['id']))
        return 'queued', 'next_repair_cycle'

    def check_job_skills(self, job):
        bindings=job['config'].get('skill_bindings')
        for cycle in job['cycles']:
            retry=(cycle['diagnostics'] or {}).get('generation_retry')
            if cycle['cycle']<=job['cycle'] and retry:bindings=retry['skill_bindings']
        self.runtime.check_skill_bindings(job['config']['skills'],bindings)
        return bindings

    def retry_generation(self, core, actor, job_id, proposal, context_sha256, allow_model_call,
                         replacement_provider=None, acknowledge_unknown_outcome=False):
        """Explicit new billed attempt; never replay an uncertain call or extend its budgets."""
        if (allow_model_call is not True or type(acknowledge_unknown_outcome) is not bool
                or not isinstance(proposal,str) or not 1<=len(proposal)<=256
                or not isinstance(context_sha256,str) or len(context_sha256)!=64
                or any(c not in '0123456789abcdef' for c in context_sha256)):
            raise ValueError('Exact failed proposal and explicit new model-call consent required')
        with core.transaction():
            job=self.get(core,actor,job_id);cfg=job['config']
            # The failed proposal is the idempotency identity, even after the new cycle advances.
            for cycle in job['cycles']:
                prior=(cycle['diagnostics'] or {}).get('generation_retry')
                if prior and prior['proposal']==proposal:
                    if (prior['context_sha256']!=context_sha256
                            or prior.get('replacement_provider')!=replacement_provider
                            or prior.get('unknown_outcome_acknowledged',False)!=acknowledge_unknown_outcome):raise Conflict('Retry identity reused')
                    return job
            if job['state']!='failed' or job['phase']!='propose' or job['proposal']!=proposal:
                raise Conflict('Only the exact failed generation may be reviewed for retry')
            failed=self.runtime.get(core,actor,proposal)
            unknown_outcome = failed['error'] in {'generation_failed','provider_timeout','provider_connection_failed'}
            if (failed['state']!='failed' or failed['context_sha256']!=context_sha256
                    or (failed['error'] not in {'invalid_model_response','provider_output_limit','provider_http_429','provider_http_503'}
                        and not (unknown_outcome and acknowledge_unknown_outcome))):
                raise Conflict('Uncertain or unrelated generation requires inspection, not retry')
            if (core.clock()>=job['deadline'] or job['steps']>=cfg['max_steps']
                    or job['calls']>=cfg['max_calls'] or job['cycle']>=cfg['max_cycles']):
                raise Conflict('Original job budget exhausted')
            self.runtime.check_skill_bindings(cfg['skills'],cfg.get('skill_bindings'))
            if self.binding(core,actor,job['project'],cfg['resource'],cfg['profile'],cfg['provider'])!=cfg['binding_sha256']:
                raise Conflict('Reviewed job configuration changed')
            self.runtime._fresh(core,actor,failed)
            self.runtime.check_skill_bindings(cfg['skills'],{s['name']:s['sha256'] for s in failed['context']['skills']})
            replacement = None
            if replacement_provider is not None:
                if not isinstance(replacement_provider, str): raise ValueError('Named replacement provider required')
                old = self.runtime.providers[cfg['provider']]
                new = self.runtime.providers.get(replacement_provider)
                if (failed['error'] != 'provider_output_limit' or new is None
                        or any(getattr(old, key, None) != getattr(new, key, None)
                               for key in ('provider','model','thinking_level','timeout'))
                        or type(new.max_output_tokens) is not int
                        or not old.max_output_tokens < new.max_output_tokens <= 32768):
                    raise Conflict('Only an explicit output-limit increase on the same model is allowed')
                replacement = {'provider': replacement_provider, 'previous_provider': cfg['provider'],
                    'previous_max_output_tokens': old.max_output_tokens, 'max_output_tokens': new.max_output_tokens}
                cfg = {**cfg, 'provider': replacement_provider,
                    'binding_sha256': self.binding(core, actor, job['project'], cfg['resource'], cfg['profile'], replacement_provider)}
            diagnostic=self.diagnostic(core,actor,job,job['baseline_task'])
            diagnostic['generation_retry']={'proposal':proposal,'context_sha256':context_sha256,
                'skill_bindings':{s['name']:s['sha256'] for s in failed['context']['skills']},
                'failure':failed['error'],'validation_failure':failed['validation_failure'],
                'replacement_provider': replacement_provider, 'output_limit_review': replacement,
                'unknown_outcome_acknowledged': acknowledge_unknown_outcome,
                'interpretation':'Previous completed attempt failed; feedback is diagnostic data, not new permissions.'}
            cycle=job['cycle']+1;phase='retrieve' if cfg.get('context_mode')=='retrieve' else 'propose'
            if replacement is not None:
                core.db.execute('UPDATE build_jobs SET config=? WHERE id=?', (encode(cfg), job_id))
            core.db.execute('INSERT INTO build_cycles(job,cycle,baseline_task,diagnostics,state) VALUES(?,?,?,?,?)',
                (job_id,cycle,job['baseline_task'],encode(diagnostic),phase))
            core.db.execute("UPDATE build_jobs SET state='queued',phase=?,cycle=?,proposal=NULL,run=NULL,control=NULL,next_due=?,updated=?,summary=? WHERE id=?",
                (phase,cycle,core.clock(),core.clock(),encode({'reason':'owner_requested_new_generation','previous_proposal':proposal}),job_id))
            core._event(job['project'],'build_job.generation_retry_requested',job_id)
        return self.get(core,actor,job_id)

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
            elif job['phase'] == 'retrieve':
                task = self._task(core, actor, job)
                if task and core.task(actor, task)['state'] not in {'succeeded','failed','cancelled'}:
                    core.cancel(actor, task)
            elif job['baseline_task'] and core.task(actor, job['baseline_task'])['state'] not in {'succeeded','failed','cancelled'}:
                core.cancel(actor, job['baseline_task'])
        return self.get(core, actor, job_id)

    def _task(self, core, actor, job):
        if job['phase'] == 'retrieve':
            cycle = core.db.execute('SELECT diagnostics FROM build_cycles WHERE job=? AND cycle=?',(job['id'],job['cycle'])).fetchone()
            return json.loads(cycle['diagnostics'] or '{}').get('context_task') if cycle else None
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
            supervise = supervisor(core, actor, 'build_jobs', job['id'], token)
            supervise()
            self.check_job_skills(job)
            if self.binding(core,actor,project,cfg['resource'],cfg['profile'],cfg['provider']) != cfg['binding_sha256']:
                raise Conflict('Reviewed job configuration changed')
            if job['phase'] == 'baseline': state, reason = self._baseline(core,actor,job,supervise)
            elif job['phase'] == 'retrieve': state, reason = self._retrieve(core,actor,job)
            elif job['phase'] == 'propose': state, reason = self._propose(core,actor,job)
            elif job['phase'] == 'review':
                if cfg['auto_accept'] and core._owned(actor,project)['mode'] == 'full':
                    with core.transaction(): self._accept(core,actor,job,self.runtime.get(core,actor,job['proposal']))
                    state, reason = 'queued', 'proposal_auto_accepted'
                else: state, reason = 'waiting_review', 'review_exact_proposal'
            elif job['phase'] == 'execute': state, reason = self._execute(core,actor,job,supervise)
            else: raise Conflict('Unknown job phase')
        except (ValueError,Denied,RuntimeError,OSError): state, reason = 'blocked','step_requires_review'
        with core.transaction():
            latest = self.get(core, actor, job['id'])
            row = core.db.execute('SELECT lease_token FROM build_jobs WHERE id=?', (job['id'],)).fetchone()
            if row['lease_token'] != token: raise Conflict('Job lease lost; inspect effects')
            if latest['control']: state, reason = ('paused' if latest['control'] == 'pause' else 'cancelled'), 'owner_'+latest['control']
            elif core.clock() >= latest['deadline']: state, reason = 'budget_limited', 'deadline'
            task = self._task(core,actor,latest)
            uncertain = bool(task and core.task(actor,task)['state'] in {'running','interrupted','cancellation_requested','cancellation_unconfirmed'})
            refund = state in {'waiting_approval','waiting_review'} or (state == 'blocked' and not uncertain and latest['calls'] == job['calls'])
            summary = {'reason':reason,'phase':latest['phase'],'cycle':latest['cycle'],'model_calls_reserved':latest['calls'],
                       'proposal':latest['proposal'],'run':latest['run'],'task':task,'uncertain_task':uncertain,'source_delivery':'separate_review_required'}
            if latest['proposal']:
                proposal = self.runtime.get(core,actor,latest['proposal']); summary['last_reported_usage'] = proposal['usage']
                if proposal.get('validation_failure'):
                    summary['validation_failure'] = proposal['validation_failure']
            core.db.execute('UPDATE build_jobs SET state=?,steps=steps-?,lease_token=NULL,lease_until=NULL,control=NULL,summary=?,next_due=?,updated=? WHERE id=?',
                            (state,1 if refund else 0,encode(summary),core.clock()+(5 if state.startswith('waiting') else 1),core.clock(),job['id']))
            core.db.execute('UPDATE build_attempts SET finished=?,outcome=? WHERE token=?', (core.clock(),state,token))
            core._event(project,'build_job.'+state,job['id'])
        return {'build_job': self.get(core,actor,job['id']), 'recovered':recovered}
