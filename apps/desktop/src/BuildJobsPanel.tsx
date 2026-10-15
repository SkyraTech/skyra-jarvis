import { useEffect, useRef, useState } from 'react';
import { request } from './api';
import type { Dashboard, ProposalDetail, Specification } from './types';

type Job = {
  id: string;
  goal: string;
  state: string;
  phase: string;
  cycle: number;
  calls: number;
  steps: number;
  proposal: string | null;
  run: string | null;
  deadline: number;
  control: string | null;
  config: { max_calls: number; max_cycles: number; max_steps: number };
  summary: Record<string, unknown>;
};

export default function BuildJobsPanel({
  project,
  dashboard,
  busy,
  active,
  perform,
  notice,
  initial,
  onReady,
}: {
  project: string;
  dashboard: Dashboard | null;
  busy: boolean;
  active: boolean;
  perform: (operation: () => Promise<void>) => Promise<void>;
  notice: (message: string) => void;
  initial?: { resource: string; profile: string; specification: string; goal: string };
  onReady?: (run: string | null) => void;
}) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [enabled, setEnabled] = useState(false);
  const [goal, setGoal] = useState(initial?.goal || '');
  const [resource, setResource] = useState(
    initial?.resource || dashboard?.workspaces[0]?.resource || '',
  );
  const [profile, setProfile] = useState(initial?.profile || dashboard?.worker.profiles[0] || '');
  const [provider, setProvider] = useState(dashboard?.runtime.providers[0]?.name || '');
  const [files, setFiles] = useState<string[] | null>(null);
  const [consent, setConsent] = useState(false);
  const [autoAccept, setAutoAccept] = useState(false);
  const [calls, setCalls] = useState(2);
  const [cycles, setCycles] = useState(2);
  const [steps, setSteps] = useState(40);
  const [minutes, setMinutes] = useState(480);
  const [specification, setSpecification] = useState(initial?.specification || '');
  const [specs, setSpecs] = useState<Specification[]>([]);
  const [review, setReview] = useState<{ job: string; proposal: ProposalDetail } | null>(null);
  const live = useRef(true);
  const pending = useRef({ key: '', id: crypto.randomUUID() });
  const selectedWorkspace = dashboard?.workspaces.find((w) => w.resource === resource);
  const selectedFiles = files || selectedWorkspace?.files.slice(0, 20) || [];
  useEffect(() => {
    setResource((value) => value || dashboard?.workspaces[0]?.resource || '');
    setProfile((value) => value || dashboard?.worker.profiles[0] || '');
    setProvider((value) => value || dashboard?.runtime.providers[0]?.name || '');
    if (dashboard?.project.mode !== 'full') setAutoAccept(false);
  }, [dashboard]);
  async function load() {
    const data = await request<{ enabled: boolean; jobs: Job[] }>({
      action: 'build_jobs',
      project,
    });
    if (live.current) {
      setEnabled(data.enabled);
      const visible = initial
        ? data.jobs.filter(
            (job) => (job.config as { resource?: string }).resource === initial.resource,
          )
        : data.jobs;
      setJobs(visible);
      const completed = visible[0]?.state === 'completed' ? visible[0] : null;
      onReady?.(completed?.run || null);
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
        if (live.current) notice('Build-job status unavailable. Refresh the Core connection.');
      } finally {
        loading = false;
      }
    };
    void poll();
    void request<{ specifications: Specification[] }>({ action: 'specifications', project })
      .then((data) => {
        if (live.current) setSpecs(data.specifications.filter((s) => s.state === 'approved'));
      })
      .catch(() => {});
    const timer = setInterval(() => void poll(), 5000);
    return () => {
      live.current = false;
      clearInterval(timer);
    };
  }, [project, active]);
  async function control(id: string, action: string) {
    await request({ action: 'control_build_job', id, body: { action } });
    await load();
    notice(`Job ${action} recorded. Active work follows its cancellation/checkpoint rules.`);
  }
  return (
    <section className="detail build-jobs-panel">
      <div className="panel-heading">
        <h2>Model-backed repair jobs</h2>
        <span>{enabled ? 'Core enabled' : 'Disabled or runtime unavailable'}</span>
      </div>
      <p>
        Test a registered snapshot, propose a repair, then test again. A failing retest can request
        another repair within your budgets. Original source delivery remains separately reviewed.
      </p>
      <p>
        Each model-call slot is charged before dispatch, including failed or uncertain requests.
        Currency estimates are not available. Time limits are checked between bounded steps.
      </p>
      <details className="build-job-configuration" open={jobs.length === 0}>
        <summary>{jobs.length ? 'Configure another repair job' : 'Configure repair job'}</summary>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void perform(async () => {
              const body = {
                resource,
                profile,
                provider,
                goal,
                files: selectedFiles,
                skills: [],
                max_calls: calls,
                max_cycles: cycles,
                max_steps: steps,
                duration_seconds: minutes * 60,
                auto_accept: autoAccept,
                allow_model_calls: consent,
                specification: specification || null,
              };
              const key = JSON.stringify([project, body]);
              if (pending.current.key !== key) pending.current = { key, id: crypto.randomUUID() };
              await request({
                action: 'create_build_job',
                project,
                body: { ...body, request_id: pending.current.id },
              });
              await load();
              notice('Repair job queued. The hidden runner must be active to continue.');
            });
          }}
        >
          <label>
            Workspace
            <select
              aria-label="Build workspace"
              value={resource}
              disabled={busy || !enabled}
              onChange={(event) => {
                setResource(event.target.value);
                setFiles(null);
              }}
            >
              {dashboard?.workspaces.map((w) => (
                <option key={w.resource}>{w.resource}</option>
              ))}
            </select>
          </label>
          <label>
            Test profile
            <select
              aria-label="Build test profile"
              value={profile}
              disabled={busy || !enabled}
              onChange={(event) => setProfile(event.target.value)}
            >
              {dashboard?.worker.profiles.map((p) => (
                <option key={p}>{p}</option>
              ))}
            </select>
          </label>
          <label>
            Model
            <select
              aria-label="Build model"
              value={provider}
              disabled={busy || !enabled}
              onChange={(event) => setProvider(event.target.value)}
            >
              {dashboard?.runtime.providers.map((p) => (
                <option key={p.name} value={p.name}>
                  {p.name} · {p.model}
                </option>
              ))}
            </select>
          </label>
          <label>
            Approved specification
            <select
              aria-label="Build specification"
              value={specification}
              onChange={(event) => setSpecification(event.target.value)}
            >
              <option value="">No specification selected</option>
              {specs.map((s) => (
                <option key={s.id} value={s.id}>
                  Version {s.version} · {s.sha256.slice(0, 12)}
                </option>
              ))}
            </select>
          </label>
          <label className="wide">
            Repair goal
            <textarea
              aria-label="Build goal"
              value={goal}
              required
              maxLength={8000}
              disabled={busy || !enabled}
              onChange={(event) => setGoal(event.target.value)}
            />
          </label>
          <fieldset>
            <legend>Selected model context</legend>
            <small>
              Include the profile's protected tests. Only selected files and bounded verified test
              output are shared.
            </small>
            {selectedWorkspace?.files.map((path) => (
              <label key={path} className="checkbox">
                <input
                  type="checkbox"
                  checked={selectedFiles.includes(path)}
                  disabled={busy || (!selectedFiles.includes(path) && selectedFiles.length >= 20)}
                  onChange={(event) =>
                    setFiles(
                      event.target.checked
                        ? [...selectedFiles, path]
                        : selectedFiles.filter((p) => p !== path),
                    )
                  }
                />
                {path}
              </label>
            ))}
          </fieldset>
          <label>
            Model-call budget
            <input
              aria-label="Build model-call budget"
              type="number"
              min={1}
              max={8}
              required
              value={calls}
              onChange={(event) => setCalls(Number(event.target.value))}
            />
          </label>
          <label>
            Repair-cycle limit
            <input
              aria-label="Build cycle limit"
              type="number"
              min={1}
              max={8}
              required
              value={cycles}
              onChange={(event) => setCycles(Number(event.target.value))}
            />
          </label>
          <label>
            Step budget
            <input
              aria-label="Build step budget"
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
              aria-label="Build time limit"
              type="number"
              min={1}
              max={10080}
              required
              value={minutes}
              onChange={(event) => setMinutes(Number(event.target.value))}
            />
          </label>
          <label className="checkbox wide">
            <input
              type="checkbox"
              aria-label="Allow model calls for this job"
              checked={consent}
              onChange={(event) => setConsent(event.target.checked)}
            />
            Allow model calls using the selected files, specification and bounded test output for
            this job.
          </label>
          <label className="checkbox wide">
            <input
              type="checkbox"
              aria-label="Automatically accept validated repair proposals"
              checked={autoAccept}
              disabled={dashboard?.project.mode !== 'full'}
              onChange={(event) => setAutoAccept(event.target.checked)}
            />
            Automatically accept validated proposals. Requires full-access policy; otherwise review
            every proposal.
          </label>
          <button
            disabled={
              busy ||
              !enabled ||
              !consent ||
              !goal.trim() ||
              !selectedFiles.length ||
              !resource ||
              !provider ||
              !profile
            }
          >
            Queue model repair job
          </button>
        </form>
      </details>
      <button disabled={busy} onClick={() => void perform(load)}>
        Refresh build jobs
      </button>
      {!jobs.length && <p>No model repair jobs have been queued.</p>}
      {jobs.map((job) => (
        <article className="build-job-card" data-job-id={job.id} key={job.id}>
          <h3>{job.goal}</h3>
          <strong>
            {job.state.replaceAll('_', ' ')} · {job.phase}
          </strong>
          <p>
            {job.calls}/{job.config.max_calls} model-call slots · Cycle {job.cycle}/
            {job.config.max_cycles} · {job.steps}/{job.config.max_steps} step slots
          </p>
          <small>
            Job {job.id} · Deadline {new Date(job.deadline * 1000).toLocaleString()}
          </small>
          {job.run && (
            <p>
              Coding run {job.run} — inspect it in Coding runs for test/diff evidence and separate
              source delivery.
            </p>
          )}
          <div>
            <button
              disabled={busy || job.state !== 'waiting_review' || !job.proposal}
              onClick={() =>
                void perform(async () => {
                  const proposal = await request<ProposalDetail>({
                    action: 'proposal',
                    id: job.proposal!,
                  });
                  setReview({ job: job.id, proposal });
                })
              }
            >
              Review job proposal
            </button>
            <button
              disabled={
                busy ||
                !['queued', 'running', 'waiting_approval', 'waiting_review'].includes(job.state)
              }
              onClick={() => void perform(() => control(job.id, 'pause'))}
            >
              Pause repair job
            </button>
            <button
              disabled={busy || !enabled || !['paused', 'blocked'].includes(job.state)}
              onClick={() => void perform(() => control(job.id, 'resume'))}
            >
              Resume repair job
            </button>
            <button
              disabled={busy || ['completed', 'failed', 'cancelled'].includes(job.state)}
              onClick={() => void perform(() => control(job.id, 'cancel'))}
            >
              Cancel repair job
            </button>
          </div>
          {review?.job === job.id && (
            <section aria-label="Job proposal review">
              <h4>{review.proposal.response?.summary}</h4>
              <small>
                Context {review.proposal.context_sha256} · Response{' '}
                {review.proposal.response_sha256}
              </small>
              {review.proposal.response?.patches.map((p) => (
                <details key={p.path} open>
                  <summary>{p.path}</summary>
                  <pre>{p.old ? `Before:\n${p.old}\nAfter:\n${p.new}` : p.new}</pre>
                </details>
              ))}
              <button
                disabled={
                  busy || job.state !== 'waiting_review' || !review.proposal.response_sha256
                }
                onClick={() =>
                  void perform(async () => {
                    await request({
                      action: 'accept_build_proposal',
                      id: job.id,
                      body: {
                        context_sha256: review.proposal.context_sha256,
                        response_sha256: review.proposal.response_sha256,
                      },
                    });
                    setReview(null);
                    await load();
                    notice('Reviewed repair accepted. Current task permissions still apply.');
                  })
                }
              >
                Accept reviewed job repair
              </button>
            </section>
          )}
          <details>
            <summary>Job progress and evidence summary</summary>
            <pre>{JSON.stringify(job.summary, null, 2)}</pre>
          </details>
        </article>
      ))}
    </section>
  );
}
