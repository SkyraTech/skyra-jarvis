import { useEffect, useRef, useState } from 'react';
import { request } from './api';
import ProjectBuildFlow from './ProjectBuildFlow';
import type { Dashboard, Specification } from './types';
import type { View } from './App';

type Outcome = {
  lane: string;
  id: string;
  goal: string;
  state: string;
  reason: string;
  run: string | null;
  resource: string | null;
  calls: number;
  max_calls: number;
  steps: number;
  max_steps: number;
  deadline: number;
  evidence?: string[];
  phase?: string;
  cycle?: number;
  proposal?: string | null;
  task?: string | null;
};
type Notice = {
  id: string;
  event: number;
  created: number;
  acknowledged: number | null;
  snapshot: Outcome;
};
type Entry = {
  name: string;
  specification: string;
  plan_sha256: string;
  active: boolean;
  enabled: boolean;
  granted: boolean;
  reconciliation_required: boolean;
};
type State = {
  notices: Notice[];
  next_before: number | null;
  unread: number;
  host_enabled: boolean;
  server_time: number;
  work: (Outcome & { expired: boolean })[];
  library: Entry[];
};

export default function OperationsPanel({
  project,
  dashboard,
  active,
  open,
}: {
  project: string;
  dashboard: Dashboard | null;
  active: boolean;
  open: (view: View, run?: string) => Promise<void>;
}) {
  const [data, setData] = useState<State | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState<{ entry: Entry; spec: Specification } | null>(null);
  const live = useRef(true),
    gate = useRef(false);
  async function load(before = 0, preserve = false) {
    const result = await request<State>({ action: 'operations', project, after: before });
    if (live.current)
      setData((old) => {
        if (!old || (!before && !preserve)) return result;
        const notices = [...result.notices, ...old.notices]
          .filter((notice, index, all) => all.findIndex((item) => item.id === notice.id) === index)
          .sort((a, b) => b.event - a.event)
          .slice(0, 500);
        return { ...result, notices, next_before: preserve ? old.next_before : result.next_before };
      });
  }
  async function perform(action: () => Promise<void>) {
    if (gate.current) return;
    gate.current = true;
    setBusy(true);
    setError('');
    try {
      await action();
    } catch (e) {
      if (live.current)
        setError(e instanceof Error ? e.message : 'Unable to refresh operations. Try again.');
    } finally {
      gate.current = false;
      if (live.current) setBusy(false);
    }
  }
  useEffect(() => {
    live.current = true;
    void perform(() => load());
    const timer = window.setInterval(() => {
      if (active && document.visibilityState === 'visible' && !gate.current)
        void perform(() => load(0, true));
    }, 10000);
    return () => {
      live.current = false;
      window.clearInterval(timer);
    };
  }, [project, active]);
  function actions(item: Outcome) {
    return (
      <div className="operations-actions">
        <button
          disabled={busy}
          onClick={() =>
            void perform(() => open(item.lane === 'assignment' ? 'Assignments' : 'Build jobs'))
          }
        >
          Open {item.lane === 'assignment' ? 'assignments' : 'build jobs'}
        </button>
        {item.state === 'waiting_approval' && (
          <button disabled={busy} onClick={() => void perform(() => open('Approvals'))}>
            Review approvals
          </button>
        )}
        {item.run && (
          <button
            disabled={busy}
            onClick={() => void perform(() => open('Coding runs', item.run!))}
          >
            Inspect tested run and delivery
          </button>
        )}
      </div>
    );
  }
  return (
    <section className="card operations-panel" aria-label="Unattended operations">
      <div className="panel-heading">
        <h2>Unattended operations</h2>
        <button disabled={busy} onClick={() => void perform(() => load())}>
          Refresh operations
        </button>
      </div>
      <p>
        Return to recorded outcomes and work that needs your attention. Reading or acknowledging an
        outcome never approves, resumes or delivers work.
      </p>
      {error && (
        <p role="alert" className="error-text">
          {error}
        </p>
      )}
      {!data && !error && <p>Loading persistent operations…</p>}
      {data && (
        <>
          <p className="operations-host">
            Background execution {data.host_enabled ? 'host-enabled' : 'host-disabled'}. This
            setting does not confirm runner health. The hidden runner and PC must remain running;
            approval waits and budgets still apply.
          </p>
          <section aria-label="Work needing attention">
            <h3>Current work</h3>
            {!data.work.length && <p>No active or blocked work in this project.</p>}
            {data.work.map((item) => (
              <article className="operation-item" key={item.id}>
                <h4>{item.goal}</h4>
                <strong>{item.state.replaceAll('_', ' ')}</strong>
                <p>
                  {item.reason?.replaceAll('_', ' ')} · {item.steps}/{item.max_steps} steps ·{' '}
                  {item.calls}/{item.max_calls} reserved model-call slots
                </p>
                <p>
                  {item.expired
                    ? 'Deadline elapsed. This work cannot continue within its original budget.'
                    : 'Deadline: ' + new Date(item.deadline * 1000).toLocaleString()}
                </p>
                <small>{item.id}</small>
                {actions(item)}
              </article>
            ))}
          </section>
          <section aria-label="Persistent outcome inbox">
            <h3>Outcome inbox · {data.unread} unread</h3>
            <p>
              Snapshots record what happened at that time. Inspect the current run before delivery;
              acknowledgement only marks the notice as read.
            </p>
            {!data.notices.length && (
              <p>
                No recorded outcomes yet. Completion, failures, approval waits and budget stops will
                appear here.
              </p>
            )}
            {data.notices.map((item) => (
              <article className="operation-item" key={item.id} data-notice-id={item.id}>
                <div className="panel-heading">
                  <h4>{item.snapshot.goal}</h4>
                  <span className="pill">
                    {item.acknowledged === null ? 'Unread' : 'Acknowledged'}
                  </span>
                </div>
                <strong>{item.snapshot.state.replaceAll('_', ' ')}</strong>
                <p>{item.snapshot.reason.replaceAll('_', ' ')}</p>
                <small>
                  {new Date(item.created * 1000).toLocaleString()} · {item.snapshot.id}
                </small>
                <p>
                  {item.snapshot.calls}/{item.snapshot.max_calls} reserved model-call slots ·{' '}
                  {item.snapshot.steps}/{item.snapshot.max_steps} steps. Source delivery requires
                  separate review.
                </p>
                {actions(item.snapshot)}
                <details>
                  <summary>Recorded evidence and scope</summary>
                  <pre>{JSON.stringify(item.snapshot, null, 2)}</pre>
                </details>
                {item.acknowledged === null && (
                  <button
                    disabled={busy}
                    onClick={() =>
                      void perform(async () => {
                        const result = await request<{ acknowledged: number }>({
                          action: 'acknowledge_operation',
                          id: item.id,
                        });
                        if (live.current)
                          setData((old) =>
                            old
                              ? {
                                  ...old,
                                  unread: Math.max(0, old.unread - 1),
                                  notices: old.notices.map((n) =>
                                    n.id === item.id
                                      ? { ...n, acknowledged: result.acknowledged }
                                      : n,
                                  ),
                                }
                              : old,
                          );
                      })
                    }
                  >
                    Acknowledge outcome
                  </button>
                )}
              </article>
            ))}
            {data.next_before !== null && (
              <button disabled={busy} onClick={() => void perform(() => load(data.next_before!))}>
                Load older outcomes
              </button>
            )}
          </section>
          <section aria-label="Registered project library">
            <h3>Registered project library</h3>
            <p>
              Durable projects created through reviewed templates. Other manually configured
              workspaces remain in Build jobs.
            </p>
            {!data.library.length && <p>No template projects registered in this project yet.</p>}
            <div className="project-library">
              {data.library.map((entry) => (
                <article className="operation-item" key={entry.name}>
                  <h4>{entry.name}</h4>
                  <p>
                    {entry.reconciliation_required
                      ? 'Reconciliation required'
                      : entry.active
                        ? 'Registration active'
                        : 'Registration unavailable in this host configuration'}{' '}
                    · {entry.granted ? 'Resources granted' : 'Permission review needed'}
                  </p>
                  <button
                    disabled={busy}
                    onClick={() =>
                      void perform(async () => {
                        const spec = await request<Specification>({
                          action: 'specification',
                          id: entry.specification,
                        });
                        if (live.current) setSelected({ entry, spec });
                      })
                    }
                  >
                    Open project workflow
                  </button>
                </article>
              ))}
            </div>
            {selected && (
              <section className="library-workflow" aria-label="Saved project workflow">
                <div className="panel-heading">
                  <h3>{selected.entry.name}</h3>
                  <button onClick={() => setSelected(null)}>Close project workflow</button>
                </div>
                {selected.spec.state !== 'approved' && (
                  <p role="status">
                    This project references a {selected.spec.state} specification. Existing evidence
                    remains available; new jobs require a current approved specification.
                  </p>
                )}
                <ProjectBuildFlow
                  key={selected.entry.name}
                  spec={selected.spec}
                  name={selected.entry.name}
                  planSha={selected.entry.plan_sha256}
                  active={active}
                />
              </section>
            )}
          </section>
        </>
      )}
      <details>
        <summary>Recent Core events</summary>
        {dashboard?.events.map((event) => (
          <p key={event.id}>
            <strong>{event.kind}</strong> · {event.subject} ·{' '}
            {new Date(event.at * 1000).toLocaleString()}
          </p>
        ))}
      </details>
    </section>
  );
}
