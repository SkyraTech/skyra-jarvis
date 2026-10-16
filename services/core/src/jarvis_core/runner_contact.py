"""Project-scoped worker contact, not OS process-health attestation."""
from .store import identifier

def begin(core, actor, project):
    core._owned(actor,project)
    attempt=identifier()
    with core.transaction():
        core.db.execute("INSERT INTO runner_contacts VALUES(?,?,?,NULL,'in_progress') ON CONFLICT(project) DO UPDATE SET attempt=excluded.attempt,started=excluded.started,finished=NULL,outcome='in_progress'",(project,attempt,core.clock()))
    return attempt

def finish(core, project, attempt, outcome):
    if outcome not in {'responded','error'}: raise ValueError('Invalid contact outcome')
    with core.transaction():
        core.db.execute('UPDATE runner_contacts SET finished=?,outcome=? WHERE project=? AND attempt=?',(core.clock(),outcome,project,attempt))

def read(core, actor, project):
    core._owned(actor,project)
    row=core.db.execute('SELECT started,finished,outcome FROM runner_contacts WHERE project=?',(project,)).fetchone()
    if row is None: return {'state':'never_seen','started':None,'finished':None,'outcome':None}
    data=dict(row)
    age=max(0,core.clock()-(data['finished'] if data['finished'] is not None else data['started']))
    data['state']='stale' if age > (660 if data['outcome']=='in_progress' else 180) else 'in_progress' if data['outcome']=='in_progress' else 'recent'
    data['age_seconds']=age
    return data
