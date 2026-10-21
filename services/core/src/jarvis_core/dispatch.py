"""Shared dispatch recovery/exclusion for both local scheduler lanes."""
import json


class DispatchStopped(RuntimeError):
    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


def supervisor(core, actor, table, identity, token):
    """Renew only this owned dispatch; never resurrect an expired parent lease."""
    if table not in {'assignments', 'build_jobs'}:
        raise ValueError('Known scheduler lane required')
    def poll():
        with core.transaction():
            row = core.db.execute(f'SELECT project,state,lease_token,lease_until,deadline,control FROM {table} WHERE id=?', (identity,)).fetchone()
            if row is None:
                raise DispatchStopped('parent_lease_lost')
            core._owned(actor, row['project'])
            now = core.clock()
            if row['state'] != 'running' or row['lease_token'] != token or row['lease_until'] <= now:
                raise DispatchStopped('parent_lease_lost')
            if row['control'] == 'cancel':
                raise DispatchStopped('owner_cancel')
            if now >= row['deadline']:
                raise DispatchStopped('deadline')
            # Pause is a step boundary; cancellation/deadline stop external work.
            until = min(now + 600, row['deadline'])
            if until > row['lease_until'] + 1:
                core.db.execute(f'UPDATE {table} SET lease_until=?,updated=? WHERE id=? AND lease_token=?', (until, now, identity, token))
    return poll


def status(core, actor, table, identity):
    """Read-only observed dispatch timing, not completion or OS-health evidence."""
    attempts = {'build_jobs': 'build_attempts', 'assignments': 'assignment_attempts'}
    if table not in attempts: raise ValueError('Known scheduler lane required')
    row = core.db.execute(f'SELECT project,state,lease_token,lease_until,deadline,updated FROM {table} WHERE id=?', (identity,)).fetchone()
    if row is None: return None
    core._owned(actor, row['project'])
    if row['state'] != 'running': return None
    attempt = core.db.execute(f'SELECT started FROM {attempts[table]} WHERE token=? AND finished IS NULL', (row['lease_token'],)).fetchone()
    if attempt is None: return None
    now = core.clock()
    return {'started_at': attempt['started'], 'heartbeat_at': row['updated'],
            'lease_expires_at': row['lease_until'], 'lease_valid': row['lease_until'] is not None and row['lease_until'] > now,
            'elapsed_seconds': round(max(0, now-attempt['started']), 1),
            'deadline_remaining_seconds': round(max(0, row['deadline']-now), 1)}


def recover(core, actor, project):
    core._owned(actor, project)
    core.recover_expired(actor, project)
    count = 0
    with core.transaction():
        for table, attempts, event in (('assignments', 'assignment_attempts', 'assignment'),
                                       ('build_jobs', 'build_attempts', 'build_job')):
            rows = list(core.db.execute(f"SELECT id,lease_token,summary FROM {table} WHERE project=? AND state='running' AND lease_until<=?", (project, core.clock())))
            for row in rows:
                summary = json.loads(row['summary']); summary['reason'] = 'runner_interrupted'
                core.db.execute(f"UPDATE {table} SET state='blocked',lease_token=NULL,lease_until=NULL,summary=?,updated=? WHERE id=?",
                                (json.dumps(summary), core.clock(), row['id']))
                core.db.execute(f"UPDATE {attempts} SET finished=?,outcome='interrupted' WHERE token=? AND finished IS NULL", (core.clock(), row['lease_token']))
                core._event(project, event+'.interrupted', row['id']); count += 1
    return count


def busy(core, project):
    return any(core.db.execute(f"SELECT 1 FROM {table} WHERE project=? AND state='running'", (project,)).fetchone()
               for table in ('assignments', 'build_jobs'))


def lane(core, project):
    row = core.db.execute("SELECT lane FROM (SELECT 'assignment' lane,next_due due FROM assignments WHERE project=? AND state IN ('queued','waiting_approval') UNION ALL SELECT 'build' lane,next_due due FROM build_jobs WHERE project=? AND state IN ('queued','waiting_approval','waiting_review')) WHERE due<=? ORDER BY due,lane LIMIT 1", (project, project, core.clock())).fetchone()
    return row['lane'] if row else None
