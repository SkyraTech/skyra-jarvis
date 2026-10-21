import { useEffect, useRef, useState } from 'react';
import { request } from './api';
import SupervisionStatus, { type Supervision } from './SupervisionStatus';
import type { Dashboard } from './types';

type Assignment = {
  id: string;
  run: string;
  goal: string;
  state: string;
  steps: number;
  max_steps: number;
  deadline: number;
  updated: number;
  control: string | null;
  summary: Record<string, unknown>;
  supervision?: Supervision | null;
};

export default function AssignmentsPanel({
  project,
  dashboard,
  busy,
  active,
  perform,
  notice,
}: {
  project: string;
  dashboard: Dashboard | null;
  busy: boolean;
  active: boolean;
  perform: (operation: () => Promise<void>) => Promise<void>;
  notice: (message: string) => void;
}) {
  const [jobs, setJobs] = useState<Assignment[]>([]);
  const [enabled, setEnabled] = useState(false);
  const [goal, setGoal] = useState('');
  const [run, setRun] = useState('');
  const [steps, setSteps] = useState(20);
  const [minutes, setMinutes] = useState(480);
  const live = useRef(true);
  const pending = useRef({ key: '', id: crypto.randomUUID() });
  const available = (dashboard?.runs || []).filter(
    (r) => !['ready_for_review', 'failed', 'cancelled', 'cancellation_requested'].includes(r.state),
  );
  const selected = run || available[0]?.id || '';
  async function load() {
    const data = await request<{ enabled: boolean; assignments: Assignment[] }>({
      action: 'assignments',
      project,
    });
    if (live.current) {
      setJobs(data.assignments);
      setEnabled(data.enabled);
    }
  }
  useEffect(() => {
    if (!active) return;
    live.current = true;
    let loading = false;
    const poll = async () => {
      if (loading || document.hidden) return;
      loading = true;
      try {
        await load();
      } catch {
        if (live.current) notice('Assignment status unavailable. Check the Core connection.');
      } finally {
        loading = false;
      }
    };
    void poll();
    const timer = setInterval(() => void poll(), 5000);
    return () => {
      live.current = false;
      clearInterval(timer);
    };
  }, [project, active]);
  async function control(id: string, action: string) {
    await request({ action: 'control_assignment', id, body: { action } });
    await load();
    notice(
      action === 'pause'
        ? 'Pause requested. An active step stops at its next checkpoint.'
        : `Assignment ${action} recorded.`,
    );
  }
  return (
    <section className="detail">
      <div className="panel-heading">
        <h2>Unattended assignments</h2>
        <span>{enabled ? 'Core enabled' : 'Disabled in host configuration'}</span>
      </div>
      <p>
        Continue a reviewed coding run without advancing each step manually. The hidden runner must
        be running; enabled configuration alone does not prove it is connected.
      </p>
      <p>
        Approvals still pause dependent actions. This workflow makes no model calls and stops at
        tested review readiness. Source delivery remains separately reviewed.
      </p>
      <p>
        A step slot is reserved before dispatch. An uncertain crash keeps that charge until
        reviewed; it is not automatically refunded or replayed.
      </p>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void perform(async () => {
            const key = JSON.stringify([project, selected, goal, steps, minutes]);
            if (pending.current.key !== key) pending.current = { key, id: crypto.randomUUID() };
            await request({
              action: 'create_assignment',
              project,
              body: {
                run: selected,
                goal,
                max_steps: steps,
                duration_seconds: minutes * 60,
                request_id: pending.current.id,
              },
            });
            await load();
            notice('Assignment queued. The hidden runner will advance authorized steps.');
          });
        }}
      >
        <label>
          Accepted coding run
          <select
            aria-label="Assignment coding run"
            value={selected}
            disabled={busy || !enabled}
            onChange={(event) => setRun(event.target.value)}
          >
            {!available.length && <option value="">No active coding runs</option>}
            {available.map((r) => (
              <option key={r.id} value={r.id}>
                {r.resource} · {r.state} · {r.id.slice(0, 8)}
              </option>
            ))}
          </select>
        </label>
        <label>
          Assignment goal
          <textarea
            aria-label="Assignment goal"
            value={goal}
            maxLength={2000}
            required
            disabled={busy || !enabled}
            onChange={(event) => setGoal(event.target.value)}
          />
        </label>
        <label>
          Step budget
          <input
            aria-label="Assignment step budget"
            type="number"
            min={1}
            max={100}
            required
            value={steps}
            onChange={(event) => setSteps(Number(event.target.value))}
          />
        </label>
        <label>
          Time limit in minutes
          <input
            aria-label="Assignment time limit"
            type="number"
            min={1}
            max={10080}
            required
            value={minutes}
            onChange={(event) => setMinutes(Number(event.target.value))}
          />
        </label>
        <small>
          Limits are checked between steps. An already running test remains bounded by its
          registered timeout.
        </small>
        <button disabled={busy || !enabled || !selected || !goal.trim()}>
          Queue unattended assignment
        </button>
      </form>
      <button disabled={busy} onClick={() => void perform(load)}>
        Refresh assignments
      </button>
      {!jobs.length && <p>No assignments have been queued for this project.</p>}
      {jobs.map((job) => (
        <article className="assignment-card" key={job.id}>
          <h3>{job.goal}</h3>
          <strong>
            {job.state.replaceAll('_', ' ')}
            {job.control ? ` · ${job.control} requested` : ''}
          </strong>
          <p>
            {job.steps}/{job.max_steps} steps · Deadline{' '}
            {new Date(job.deadline * 1000).toLocaleString()}
          </p>
          <small>
            Run {job.run} · Updated {new Date(job.updated * 1000).toLocaleString()}
          </small>
          <SupervisionStatus value={job.state === 'running' ? job.supervision : null} />
          <div>
            <button
              disabled={busy || !['queued', 'running', 'waiting_approval'].includes(job.state)}
              onClick={() => void perform(() => control(job.id, 'pause'))}
            >
              Pause assignment
            </button>
            <button
              disabled={busy || !enabled || !['paused', 'blocked'].includes(job.state)}
              onClick={() => void perform(() => control(job.id, 'resume'))}
            >
              Resume assignment
            </button>
            <button
              disabled={busy || ['completed', 'failed', 'cancelled'].includes(job.state)}
              onClick={() => void perform(() => control(job.id, 'cancel'))}
            >
              Cancel assignment
            </button>
          </div>
          <details>
            <summary>Progress and evidence summary</summary>
            <pre>{JSON.stringify(job.summary, null, 2)}</pre>
          </details>
        </article>
      ))}
    </section>
  );
}
