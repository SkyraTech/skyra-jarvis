"""Durable owner inbox snapshots; reading/acknowledging never authorizes work."""
import hashlib
import json
from .store import Denied, encode, identifier

ATTENTION = {'completed', 'failed', 'blocked', 'budget_limited', 'waiting_review', 'waiting_approval', 'interrupted', 'cancelled'}

def capture(core, event, project, kind, subject):
    lane, _, outcome = kind.partition('.')
    if lane not in {'build_job', 'assignment'} or outcome not in ATTENTION | {'cancel'}:
        return
    table = 'build_jobs' if lane == 'build_job' else 'assignments'
    row = core.db.execute(f'SELECT * FROM {table} WHERE id=? AND project=?', (subject, project)).fetchone()
    if row is None or (outcome == 'cancel' and row['state'] != 'cancelled'):
        return
    cfg = json.loads(row['config']) if lane == 'build_job' else {}
    summary = json.loads(row['summary'])
    run = core.db.execute('SELECT resource,state,results,task FROM coding_runs WHERE id=?', (row['run'],)).fetchone() if row['run'] else None
    payload = {'lane': lane, 'id': subject, 'goal': row['goal'][:1000], 'state': row['state'],
               'reason': 'owner_cancel' if outcome == 'cancel' else summary.get('reason', outcome), 'run': row['run'],
               'resource': cfg.get('resource') or (run['resource'] if run else None),
               'phase': row['phase'] if lane == 'build_job' else None,
               'cycle': row['cycle'] if lane == 'build_job' else None,
               'calls': row['calls'] if lane == 'build_job' else 0,
               'max_calls': cfg.get('max_calls', 0), 'steps': row['steps'],
               'max_steps': cfg.get('max_steps') if lane == 'build_job' else row['max_steps'],
               'deadline': row['deadline'], 'proposal': row['proposal'] if lane == 'build_job' else None,
               'task': run['task'] if run else (row['baseline_task'] if lane == 'build_job' else None),
               'run_state': run['state'] if run else None,
               'evidence': list(dict.fromkeys(ref for result in json.loads(run['results']) for ref in result.get('evidence', [])))[:100] if run else [],
               'schedule': cfg.get('schedule'),
               'source_delivery': 'separate_review_required'}
    task = core.db.execute('SELECT state,evidence FROM tasks WHERE id=? AND project=?',(payload['task'],project)).fetchone() if payload['task'] else None
    payload['task_state'] = task['state'] if task else None
    payload['uncertain_task'] = bool(task and task['state'] in {'running','interrupted','cancellation_requested','cancellation_unconfirmed'})
    if not run and task:
        payload['evidence'] = json.loads(task['evidence'] or '[]')[:100]
    approval = core.db.execute("SELECT id,version,expires FROM approvals WHERE task=? AND state='pending' ORDER BY rowid DESC LIMIT 1",(payload['task'],)).fetchone() if payload['task'] and payload['state']=='waiting_approval' else None
    payload['approval'] = dict(approval) if approval else None
    # Quiet repeated waits: mutable progress counters/timing do not create alerts.
    fingerprint = hashlib.sha256(encode({k: payload[k] for k in ('lane','id','state','reason','run','task','proposal','cycle','task_state','approval')}).encode()).hexdigest()
    last = core.db.execute('SELECT fingerprint FROM operation_notices WHERE project=? AND subject=? ORDER BY event DESC LIMIT 1', (project, subject)).fetchone()
    if last and last['fingerprint'] == fingerprint:
        return
    core.db.execute('INSERT INTO operation_notices VALUES(?,?,?,?,?,?,?,NULL)',
                    (identifier(), project, event, subject, fingerprint, encode(payload),
                     core.db.execute('SELECT at FROM events WHERE id=?',(event,)).fetchone()[0]))

def backfill(core):
    for table, lane in (('build_jobs','build_job'), ('assignments','assignment')):
        for row in core.db.execute(f'SELECT id,project,state FROM {table}'):
            if row['state'] not in ATTENTION:
                continue
            event = core.db.execute('SELECT id,kind FROM events WHERE project=? AND subject=? AND kind IN (?,?) ORDER BY id DESC LIMIT 1',
                (row['project'],row['id'],lane+'.'+row['state'],lane+'.interrupted' if row['state']=='blocked' else lane+'.cancel' if row['state']=='cancelled' else lane+'.'+row['state'])).fetchone()
            if event:
                capture(core,event['id'],row['project'],event['kind'],row['id'])

def inbox(core, actor, project, before=0):
    core._owned(actor, project)
    if type(before) is not int or not 0 <= before <= 9223372036854775807:
        raise ValueError('Invalid cursor')
    rows = list(core.db.execute('SELECT * FROM operation_notices WHERE project=? AND (?=0 OR event<?) ORDER BY event DESC LIMIT 51', (project,before,before)))
    items = []
    for row in rows[:50]:
        item = dict(row); item['snapshot'] = json.loads(item.pop('payload')); items.append(item)
    return {'notices': items, 'next_before': rows[49]['event'] if len(rows)>50 else None,
            'unread': core.db.execute('SELECT COUNT(*) FROM operation_notices WHERE project=? AND acknowledged IS NULL',(project,)).fetchone()[0]}

def acknowledge(core, actor, notice):
    with core.transaction():
        row = core.db.execute('SELECT project FROM operation_notices WHERE id=?',(notice,)).fetchone()
        if row is None:
            raise Denied('Notice unavailable')
        core._owned(actor,row['project'])
        core.db.execute('UPDATE operation_notices SET acknowledged=COALESCE(acknowledged,?) WHERE id=?',(core.clock(),notice))
        return {'id': notice, 'acknowledged': core.db.execute('SELECT acknowledged FROM operation_notices WHERE id=?',(notice,)).fetchone()[0]}

def status(core, actor, project):
    core._owned(actor,project)
    items=[]
    for table,lane in (('build_jobs','build_job'),('assignments','assignment')):
        for row in core.db.execute(f"SELECT * FROM {table} WHERE project=? AND state NOT IN ('completed','failed','cancelled') ORDER BY updated DESC LIMIT 100",(project,)):
            cfg=json.loads(row['config']) if lane=='build_job' else {}
            items.append({'id':row['id'],'lane':lane,'goal':row['goal'][:1000],'state':row['state'],
                          'reason':json.loads(row['summary']).get('reason'),'deadline':row['deadline'],
                          'schedule':cfg.get('schedule'),'expired':core.clock()>=row['deadline'],'run':row['run'],'resource':cfg.get('resource'),
                          'calls':row['calls'] if lane=='build_job' else 0,'max_calls':cfg.get('max_calls',0),
                          'steps':row['steps'],'max_steps':cfg.get('max_steps') if lane=='build_job' else row['max_steps']})
    return items
