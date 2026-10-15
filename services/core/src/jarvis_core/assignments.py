"""Durable bounded progression of controller-accepted coding runs.

This runner neither generates model requests nor applies source deliveries.
Uncertain dispatched steps require reconciliation, never blind replay.
"""
import hashlib
import json
import uuid

from .store import Conflict, Denied, encode
from .dispatch import recover, busy

TERMINAL = {'completed', 'failed', 'cancelled'}


class Assignments:
    def __init__(self, workflow):
        self.workflow = workflow

    def get(self, core, actor, assignment):
        row = core.db.execute('SELECT * FROM assignments WHERE id=?', (assignment,)).fetchone()
        if row is None:
            raise Denied('Assignment unavailable')
        core._owned(actor, row['project'])
        data = dict(row)
        data.pop('lease_token', None)
        data.pop('digest', None)
        data['summary'] = json.loads(data['summary'])
        return data

    def list(self, core, actor, project):
        core._owned(actor, project)
        return [self.get(core, actor, row['id']) for row in core.db.execute(
            'SELECT id FROM assignments WHERE project=? ORDER BY created DESC,rowid DESC LIMIT 100', (project,))]

    def create(self, core, actor, project, run, goal, max_steps, duration_seconds, request_id):
        if (not isinstance(goal, str) or not 1 <= len(goal.strip()) <= 2000
                or type(max_steps) is not int or not 1 <= max_steps <= 100
                or type(duration_seconds) is not int or not 60 <= duration_seconds <= 604800
                or not isinstance(request_id, str) or not 1 <= len(request_id) <= 256):
            raise ValueError('Explicit goal and bounded assignment required')
        digest = hashlib.sha256(encode([run, goal, max_steps, duration_seconds]).encode()).hexdigest()
        with core.transaction():
            current = self.workflow.get(core, actor, run)
            if current['project'] != project:
                raise Denied('Run outside assignment project')
            prior = core.db.execute('SELECT id,digest FROM assignments WHERE project=? AND request_id=?',
                                    (project, request_id)).fetchone()
            if prior:
                if prior['digest'] != digest:
                    raise Conflict('Assignment request reused')
                return self.get(core, actor, prior['id'])
            if current['state'] in {'ready_for_review', 'failed', 'cancelled', 'cancellation_requested'}:
                raise Conflict('Run is terminal or cancelling')
            if core.db.execute("SELECT 1 FROM assignments WHERE run=? AND state NOT IN ('completed','failed','cancelled')", (run,)).fetchone():
                raise Conflict('Run already has an assignment')
            now = core.clock(); assignment = uuid.uuid4().hex
            core.db.execute('INSERT INTO assignments VALUES(?,?,?,?,?,?,?, ?,0,?,?,NULL,NULL,NULL,?,?,?)',
                            (assignment, project, run, request_id, digest, goal, 'queued', max_steps,
                             now+duration_seconds, now, encode({'reason': 'queued', 'model_calls': 0}), now, now))
            core._event(project, 'assignment.created', assignment)
        return self.get(core, actor, assignment)

    def control(self, core, actor, assignment, action):
        if action not in {'pause', 'resume', 'cancel'}:
            raise ValueError('Unknown assignment control')
        # The control flag is durable before requesting cancellation of an external task.
        with core.transaction():
            data = self.get(core, actor, assignment)
            if data['state'] in TERMINAL:
                raise Conflict('Assignment is terminal')
            if data['control'] == 'cancel' and action != 'cancel':
                raise Conflict('Cancellation cannot be replaced by another control')
            if action == 'resume':
                if data['state'] not in {'paused', 'blocked'}:
                    raise Conflict('Assignment cannot resume')
                run = self.workflow.get(core, actor, data['run'])
                if run['task'] and core.task(actor, run['task'])['state'] in {
                        'running', 'cancellation_requested', 'interrupted', 'cancellation_unconfirmed'}:
                    raise Conflict('Reconcile uncertain task before resuming')
                if core.clock() >= data['deadline'] or data['steps'] >= data['max_steps']:
                    raise Conflict('Assignment budget exhausted')
                state, control = 'queued', None
            elif data['state'] == 'running':
                state, control = 'running', action
            else:
                state, control = ('paused' if action == 'pause' else 'cancelled'), None
            core.db.execute('UPDATE assignments SET state=?,control=?,next_due=?,updated=? WHERE id=?',
                            (state, control, core.clock(), core.clock(), assignment))
            core._event(data['project'], 'assignment.'+action, assignment)
        if action == 'cancel':
            run = self.workflow.get(core, actor, data['run'])
            if run['state'] not in {'ready_for_review', 'failed', 'cancelled'}:
                self.workflow.cancel(core, actor, data['run'])
        return self.get(core, actor, assignment)

    def tick(self, core, actor, project):
        """One durable claim and at most one workflow advance, outside the claim transaction."""
        recovered = recover(core, actor, project)
        with core.transaction():
            now = core.clock()
            if busy(core, project):
                return {'assignment': None, 'recovered': recovered}
            row = core.db.execute("SELECT id FROM assignments WHERE project=? AND state IN ('queued','waiting_approval') AND next_due<=? ORDER BY next_due,rowid LIMIT 1", (project, now)).fetchone()
            if row is None:
                return {'assignment': None, 'recovered': recovered}
            data = self.get(core, actor, row['id'])
            if now >= data['deadline'] or data['steps'] >= data['max_steps']:
                core.db.execute("UPDATE assignments SET state='budget_limited',summary=?,updated=? WHERE id=?",
                                (encode({'reason': 'deadline' if now >= data['deadline'] else 'step_budget', 'model_calls': 0}), now, data['id']))
                core._event(project, 'assignment.budget_limited', data['id'])
                return {'assignment': self.get(core, actor, data['id']), 'recovered': recovered}
            before = self.workflow.get(core, actor, data['run'])
            if data['state'] == 'waiting_approval' and before['task']:
                policy = core._owned(actor, project)
                approval = core.db.execute("SELECT 1 FROM approvals WHERE task=? AND version=? AND state='pending' AND expires>?",
                                           (before['task'], policy['version'], now)).fetchone()
                if approval:
                    core.db.execute('UPDATE assignments SET next_due=? WHERE id=?', (now+5, data['id']))
                    return {'assignment': self.get(core, actor, data['id']), 'recovered': recovered}
            token = uuid.uuid4().hex
            # Reserve a slot before dispatch. Uncertain crashes retain that charge;
            # known no-progress/approval waits refund it at settlement.
            core.db.execute("UPDATE assignments SET state='running',steps=steps+1,lease_token=?,lease_until=?,updated=? WHERE id=?", (token, now+600, now, data['id']))
            core.db.execute("INSERT INTO assignment_attempts VALUES(?,?,?,NULL,?,NULL,'dispatched')", (token, data['id'], now, before['position']))
            core._event(project, 'assignment.dispatched', data['id'])
        try:
            after = self.workflow.advance(core, actor, data['run'])
            state = {'ready_for_review': 'completed', 'failed': 'failed', 'cancelled': 'cancelled',
                     'cancellation_requested': 'blocked', 'blocked': 'blocked',
                     'waiting_approval': 'waiting_approval', 'running': 'blocked'}.get(after['state'], 'queued')
            reason = after['state']
        except (Conflict, Denied, ValueError, RuntimeError, OSError):
            after = self.workflow.get(core, actor, data['run'])
            state, reason = 'blocked', 'step_requires_review'
        with core.transaction():
            lease = core.db.execute('SELECT lease_token,control FROM assignments WHERE id=?', (data['id'],)).fetchone()
            if lease['lease_token'] != token:
                raise Conflict('Assignment ownership lost; inspect recorded outcome')
            if lease['control']:
                state = 'paused' if lease['control'] == 'pause' else 'cancelled'
                reason = 'owner_'+lease['control']
            progressed = max(0, after['position']-before['position'])
            uncertain = bool(after['task'] and core.task(actor, after['task'])['state'] in {
                'running', 'interrupted', 'cancellation_requested', 'cancellation_unconfirmed'})
            charged = max(progressed, 1 if uncertain else 0)
            summary = {'reason': reason, 'run_state': after['state'], 'position': after['position'],
                       'task': after['task'], 'task_state': core.task(actor, after['task'])['state'] if after['task'] else None,
                       'step_slot_uncertain': uncertain,
                       'results': after['results'], 'model_calls': 0, 'source_delivery': 'separate_review_required'}
            now = core.clock()
            core.db.execute('UPDATE assignments SET state=?,steps=steps+?,next_due=?,lease_token=NULL,lease_until=NULL,control=NULL,summary=?,updated=? WHERE id=?',
                            (state, charged-1, now+(5 if state == 'waiting_approval' else 1), encode(summary), now, data['id']))
            core.db.execute('UPDATE assignment_attempts SET finished=?,position_after=?,outcome=? WHERE token=?',
                            (now, after['position'], state, token))
            core._event(project, 'assignment.'+state, data['id'])
        return {'assignment': self.get(core, actor, data['id']), 'recovered': recovered}
