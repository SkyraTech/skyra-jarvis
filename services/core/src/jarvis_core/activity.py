"""Owned project activity projection; recorded state, never process-health attestation."""


def snapshot(core, actor, project):
    core.db.execute('SAVEPOINT activity_projection')
    try:
        return _snapshot(core,actor,project)
    finally:
        core.db.execute('RELEASE activity_projection')


def _snapshot(core, actor, project):
    policy = core._owned(actor, project)
    now = core.clock()
    def count(query, values=()):
        return core.db.execute(query, (project,*values)).fetchone()[0]
    counts = {'testing':0,'coding':0,'inspecting':0,'stopping':0}
    rows = core.db.execute("SELECT action,state,COUNT(*) AS count FROM tasks WHERE project=? AND state IN ('running','cancellation_requested') AND lease_until>? GROUP BY action,state",(project,now))
    for row in rows:
        key = 'stopping' if row['state']=='cancellation_requested' else {
            'execute':'testing','write':'coding','read':'inspecting'}.get(row['action'],'inspecting')
        counts[key] += row['count']
    counts['blocked'] = count("SELECT COUNT(*) FROM tasks WHERE project=? AND (state IN ('interrupted','cancellation_unconfirmed') OR (state IN ('running','cancellation_requested') AND (lease_until IS NULL OR lease_until<=?)))",(now,))
    counts['coding_requests'] = count("SELECT COUNT(*) FROM repair_proposals WHERE project=? AND state='generating'")
    for mode,key in [('plan','planning_requests'),('chat','chat_requests')]:
        counts[key] = count("SELECT COUNT(*) FROM model_turns WHERE project=? AND mode=? AND state='generating' AND state IN ('planned','generating')",(mode,))
    counts['approvals'] = count("SELECT COUNT(*) FROM approvals a JOIN tasks t ON t.id=a.task WHERE t.project=? AND a.state='pending' AND t.state='waiting_approval' AND a.expires>? AND a.version=? AND a.digest=t.digest",(now,policy['version']))
    counts['reviews'] = count("SELECT COUNT(*) FROM build_jobs WHERE project=? AND state='waiting_review'")
    # Standalone proposals require review too; linked waiting jobs are counted once.
    counts['reviews'] += count("SELECT COUNT(*) FROM repair_proposals p WHERE p.project=? AND p.state='ready' AND p.id NOT IN(SELECT proposal FROM build_jobs WHERE project=? AND proposal IS NOT NULL)",(project,))
    for table in ('build_jobs','assignments'):
        counts['blocked'] += count(f"SELECT COUNT(*) FROM {table} WHERE project=? AND state IN ('blocked','budget_limited')")
    for state in ('queued','paused'):
        counts[state] = sum(count(f"SELECT COUNT(*) FROM {table} WHERE project=? AND state=?",(state,)) for table in ('build_jobs','assignments'))
    return {'source':'core-state-v1','project':project,'captured_at':now,'counts':counts,
            'interpretation':'Recorded project state; pending model requests are not provider health or live reasoning evidence.'}
