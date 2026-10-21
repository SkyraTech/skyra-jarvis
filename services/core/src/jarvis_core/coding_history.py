"""Read-only conversation provenance over existing durable execution records."""
import json
import hashlib


def model_snapshot(core, actor, conversation):
    """Explicit, bounded recorded-status context; never current execution authority."""
    result = read(core, actor, conversation, limit=3)
    for job in result['jobs']:
        goal = job['goal']
        job['goal'] = goal[:1000]
        job['goal_truncated'] = len(goal) > 1000
        job['goal_sha256'] = hashlib.sha256(goal.encode()).hexdigest()
    result.update(version=1, model_context_included=True, captured_at=core.clock(),
                  interpretation='Recorded historical status only; not current verification or permission.')
    payload = json.dumps(result, sort_keys=True, separators=(',', ':'), allow_nan=False)
    if len(payload.encode()) > 32000:
        raise ValueError('Coding history exceeds model context budget')
    return {'snapshot': result, 'sha256': hashlib.sha256(payload.encode()).hexdigest()}


def read(core, actor, conversation, before=0, limit=10):
    # A runner may advance a job while the desktop reads its cycle/evidence joins.
    # Keep the entire owned page in one SQLite snapshot, including inside a caller transaction.
    core.db.execute('SAVEPOINT coding_history_projection')
    try:
        return _read(core,actor,conversation,before,limit)
    finally:
        core.db.execute('RELEASE coding_history_projection')


def _read(core, actor, conversation, before=0, limit=10):
    if (type(before) is not int or not 0 <= before <= 9223372036854775807
            or type(limit) is not int or not 1 <= limit <= 10):
        raise ValueError('Bounded history cursor required')
    project = core.conversation_project(actor, conversation)
    rows = list(core.db.execute(
        "SELECT j.rowid AS cursor,j.* FROM build_jobs j JOIN coding_job_links l ON l.job=j.id "
        "WHERE j.project=? AND l.conversation=? AND (?=0 OR j.rowid<?) ORDER BY j.rowid DESC LIMIT ?",
        (project, conversation, before, before, limit + 1)))
    page = rows[:limit]
    jobs = []
    for row in page:
        config = json.loads(row['config'])
        cycles = [dict(r) for r in core.db.execute(
            "SELECT c.cycle,c.baseline_task,c.proposal,c.run,c.state,p.model,p.provider,json_extract(c.diagnostics,'$.context_task') AS context_task FROM build_cycles c "
            'LEFT JOIN repair_proposals p ON p.id=c.proposal WHERE c.job=? ORDER BY c.cycle', (row['id'],))]
        run_ids = [item['run'] for item in cycles if item['run']]
        deliveries = []
        generations = []
        if run_ids:
            placeholders = ','.join('?' for _ in run_ids)
            deliveries = [dict(r) for r in core.db.execute(
                "SELECT id,resource,state,evidence FROM tasks WHERE project=? AND json_extract(payload,'$.operation')='deliver' "
                f"AND json_extract(payload,'$.run') IN ({placeholders}) ORDER BY rowid DESC LIMIT 11",
                (project, *run_ids))]
            for delivery in deliveries:
                references = json.loads(delivery['evidence'] or '[]')
                delivery['evidence'] = references[:3]
                delivery['evidence_limited'] = len(references) > 3
            generations = [dict(r) for r in core.db.execute(
                "SELECT r.name,r.created,json_extract(r.config,'$.workspace') AS workspace,"
                "json_extract(r.config,'$.previous_workspace') AS previous_workspace FROM scaffold_registrations r "
                "JOIN tasks t ON t.id=json_extract(r.config,'$.delivery_task') WHERE r.project=? "
                f"AND json_extract(t.payload,'$.run') IN ({placeholders}) ORDER BY r.rowid DESC LIMIT 11",
                (project, *run_ids))]
        jobs.append({'id': row['id'], 'goal': row['goal'], 'state': row['state'], 'phase': row['phase'],
                     'created': row['created'], 'updated': row['updated'], 'calls': row['calls'], 'steps': row['steps'],
                     'resource': config['resource'], 'provider': config['provider'], 'mode': config.get('mode', 'repair'),
                     'cycles': cycles, 'deliveries': deliveries[:10], 'generations': generations[:10],
                     'details_limited': len(deliveries) > 10 or len(generations) > 10})
    return {'conversation': conversation, 'project': project, 'jobs': jobs,
            'next_before': page[-1]['cursor'] if len(rows) > limit else None,
            'model_context_included': False, 'automatic_execution': False}
