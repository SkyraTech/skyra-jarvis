"""Shared dispatch recovery/exclusion for both local scheduler lanes."""
import json


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
