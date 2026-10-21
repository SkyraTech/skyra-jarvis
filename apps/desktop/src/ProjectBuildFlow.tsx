import { useEffect, useRef, useState } from 'react';
import { connection, request } from './api';
import BuildJobsPanel from './BuildJobsPanel';
import DeliveryPanel from './DeliveryPanel';
import type { Dashboard, Run, Specification } from './types';

type Registration = {
  registered?: boolean;
  active?: boolean;
  enabled: boolean;
  reconciliation_required?: boolean;
  registration?: {
    project: string;
    specification: string;
    name: string;
    directory: string;
    workspace: string;
    source: string;
    selected: string[];
    profile: { name: string; argv: string[]; protected_paths: string[]; timeout: number };
  };
  registration_sha256?: string;
};

export default function ProjectBuildFlow({
  spec,
  name,
  planSha,
  active,
  existing = false,
}: {
  spec: Specification;
  name: string;
  planSha: string;
  active: boolean;
  existing?: boolean;
}) {
  const [registration, setRegistration] = useState<Registration | null>(null);
  const [review, setReview] = useState<Registration | null>(null);
  const [consent, setConsent] = useState(false);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [mode, setMode] = useState<'ask' | 'full'>('ask');
  const [grantConsent, setGrantConsent] = useState(false);
  const [worker, setWorker] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [run, setRun] = useState<Run | null>(null);
  const gate = useRef(false),
    live = useRef(true),
    runId = useRef('');
  async function refresh() {
    const data = await request<Dashboard>({ action: 'dashboard', project: spec.project });
    if (live.current) {
      setDashboard(data);
      setGrantConsent(false);
    }
  }
  async function load() {
    const data = await request<Registration>({
      action: 'scaffold_registration',
      id: spec.id,
      body: { name },
    });
    if (!live.current) return;
    setRegistration(data);
    setReview(null);
    setConsent(false);
    setGrantConsent(false);
    const state = await request<Dashboard>({ action: 'dashboard', project: spec.project });
    if (live.current) {
      setDashboard(state);
      setMode(state.project.mode === 'full' ? 'full' : 'ask');
    }
  }
  useEffect(() => {
    live.current = true;
    void load().catch(() => {
      if (live.current) setError('Unable to recover project registration. Refresh its status.');
    });
    void connection().then((data) => {
      if (live.current) setWorker(data.worker_configured);
    });
    return () => {
      live.current = false;
    };
  }, [spec.id, name, planSha, existing]);
  async function perform(operation: () => Promise<void>) {
    if (gate.current) return;
    gate.current = true;
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await operation();
    } catch (e) {
      if (live.current)
        setError(e instanceof Error ? e.message : 'Refresh project status before retrying.');
    } finally {
      gate.current = false;
      if (live.current) setBusy(false);
    }
  }
  const config = registration?.registration;
  const granted =
    !!config &&
    !!dashboard &&
    dashboard.project.mode !== 'read_only' &&
    [config.workspace, config.source].every((value) =>
      dashboard.project.resources?.includes(value),
    );
  const scopedDashboard =
    config && dashboard
      ? {
          ...dashboard,
          workspaces: dashboard.workspaces.filter((item) => item.resource === config.workspace),
          worker: {
            ...dashboard.worker,
            profiles: dashboard.worker.profiles.filter((value) => value === config.profile.name),
          },
        }
      : null;
  async function ready(id: string | null) {
    if (id === null) {
      runId.current = '';
      if (live.current) setRun(null);
      return;
    }
    if (runId.current === id) return;
    runId.current = id;
    try {
      const data = await request<Run>({ action: 'run', id });
      if (live.current && runId.current === id) setRun(data);
    } catch {
      if (runId.current === id) runId.current = '';
      if (live.current && !runId.current)
        setError('Unable to load tested delivery evidence. Refresh project status.');
    }
  }
  return (
    <section className="project-build-flow" aria-label="Project build workflow">
      <h3>Build this project</h3>
      {error && (
        <p role="alert" className="error-text">
          {error}
        </p>
      )}
      {notice && <p role="status">{notice}</p>}
      <button disabled={busy} onClick={() => void perform(load)}>
        Refresh project registration
      </button>
      {!registration?.registered && (
        <>
          <p>
            Review registration to connect the isolated workspace, protected test profile and source
            target. Native execution uses your Windows account access. Resource permissions and
            model calls require separate consent.
          </p>
          {registration?.enabled === false && (
            <p>
              Native registration is host-disabled. Enable trusted native execution or
              scaffold_execution_enabled in the private launcher configuration and restart Core.
            </p>
          )}
          <button
            disabled={busy}
            onClick={() =>
              void perform(async () => {
                const result = await request<Registration>({
                  action: existing
                    ? 'preview_existing_registration'
                    : 'preview_scaffold_registration',
                  id: spec.id,
                  body: { name, expected_plan_sha256: planSha },
                });
                if (live.current) {
                  setReview(result);
                  setConsent(false);
                }
              })
            }
          >
            Review workspace registration
          </button>
          {review && (
            <>
              <pre>{JSON.stringify(review.registration, null, 2)}</pre>
              <p>
                Registration SHA-256: <code>{review.registration_sha256}</code>
              </p>
              <label className="scaffold-consent">
                <input
                  type="checkbox"
                  disabled={busy}
                  checked={consent}
                  onChange={(e) => setConsent(e.target.checked)}
                />
                I reviewed the workspace, source and fixed native test command.
              </label>
              <button
                disabled={busy || !consent || !review.enabled}
                onClick={() =>
                  void perform(async () => {
                    await request({
                      action: existing ? 'register_existing_project' : 'register_scaffold',
                      id: spec.id,
                      body: {
                        name,
                        expected_plan_sha256: planSha,
                        expected_registration_sha256: review.registration_sha256,
                        allow_native_execution: true,
                      },
                    });
                    await load();
                    setReview(null);
                    setNotice('Workspace registration saved. Review project permissions next.');
                  })
                }
              >
                Register reviewed workspace
              </button>
            </>
          )}
        </>
      )}
      {registration?.reconciliation_required && (
        <p role="alert">
          Registered files or host settings changed. Reconcile them and restart Core; execution is
          unavailable.
        </p>
      )}
      {registration?.registered && config && dashboard && !granted && (
        <section aria-label="Project execution permissions">
          <h4>Review project permissions</h4>
          <p>
            Existing grants: {(dashboard.project.resources || []).join(', ') || 'None'}. Add{' '}
            {config.workspace} and {config.source}. The selected mode applies to all granted
            resources in this project.
          </p>
          <label>
            Execution permission mode
            <select
              aria-label="Scaffold execution permission mode"
              value={mode}
              disabled={busy}
              onChange={(e) => setMode(e.target.value as 'ask' | 'full')}
            >
              <option value="ask">Ask for each action</option>
              <option value="full">Full access within granted resources</option>
            </select>
          </label>
          <label className="scaffold-consent">
            <input
              type="checkbox"
              checked={grantConsent}
              disabled={busy}
              onChange={(e) => setGrantConsent(e.target.checked)}
            />
            I reviewed the permission mode and exact resource grants.
          </label>
          <button
            disabled={busy || !grantConsent}
            onClick={() =>
              void perform(async () => {
                await request({
                  action: 'policy',
                  project: spec.project,
                  body: {
                    mode,
                    resources: Array.from(
                      new Set([
                        ...(dashboard.project.resources || []),
                        config.workspace,
                        config.source,
                      ]),
                    ),
                    expected_version: dashboard.project.version,
                  },
                });
                await refresh();
                setGrantConsent(false);
                setNotice(
                  'Reviewed permissions saved. Model calls still require explicit consent.',
                );
              })
            }
          >
            Apply reviewed project permissions
          </button>
        </section>
      )}
      {registration?.active && registration.enabled && config && granted && scopedDashboard && (
        <>
          <BuildJobsPanel
            key={config.workspace}
            project={spec.project}
            dashboard={scopedDashboard}
            busy={busy}
            active={active}
            perform={perform}
            notice={setNotice}
            initial={{
              resource: config.workspace,
              profile: config.profile.name,
              specification: spec.id,
              goal:
                'Implement the approved specification and protected acceptance contract for ' +
                name,
            }}
            onReady={(id) => void ready(id)}
          />
          {run?.state === 'ready_for_review' && (
            <DeliveryPanel
              run={run}
              dashboard={scopedDashboard}
              busy={busy}
              worker={worker}
              perform={perform}
              refresh={refresh}
              notice={setNotice}
            />
          )}
        </>
      )}
    </section>
  );
}
