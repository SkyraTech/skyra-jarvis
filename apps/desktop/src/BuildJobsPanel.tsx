import { useEffect, useRef, useState } from 'react';
import { request } from './api';
import type { Dashboard, ProposalDetail, Specification } from './types';
import RetrievalReview from './RetrievalReview';
import SupervisionStatus, { type Supervision } from './SupervisionStatus';
import TrustedSkills, { skillsAreCurrent, type SkillSelection } from './TrustedSkills';
import GenerationRecovery from './GenerationRecovery';

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
  config: {
    auto_accept?: boolean;
    skill_bindings?: Record<string, string>;
    context_mode?: 'retrieve';
    conversation?: string;
    mode?: 'repair' | 'feature';
    max_calls: number;
    max_cycles: number;
    max_steps: number;
    schedule?: { start_at: number; start_by: number; inputs_sha256: string };
  };
  summary: Record<string, unknown>;
  supervision?: Supervision | null;
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
  const [configurationOpen, setConfigurationOpen] = useState(true);
  const [enabled, setEnabled] = useState(false);
  const [mode, setMode] = useState<'repair' | 'feature'>('repair');
  const [contextMode, setContextMode] = useState<'selected' | 'retrieve'>('selected');
  const [conversation, setConversation] = useState('');
  const [goal, setGoal] = useState(initial?.goal || '');
  const [resource, setResource] = useState(
    initial?.resource || dashboard?.workspaces[0]?.resource || '',
  );
  const [profile, setProfile] = useState(initial?.profile || dashboard?.worker.profiles[0] || '');
  const [provider, setProvider] = useState(dashboard?.runtime.providers[0]?.name || '');
  const [files, setFiles] = useState<string[] | null>(null);
  const [consent, setConsent] = useState(false);
  const [skills, setSkills] = useState<SkillSelection>({});
  const skillChoices = dashboard?.runtime.skills || [];
  const skillSelectionValid = skillsAreCurrent(skillChoices, skills);
  useEffect(() => {
    if (!skillSelectionValid) {
      setConsent(false);
      setAutoAccept(false);
      setScheduleReviewed(false);
    }
  }, [skillSelectionValid]);
  const [autoAccept, setAutoAccept] = useState(false);
  const [calls, setCalls] = useState(2);
  const [cycles, setCycles] = useState(2);
  const [steps, setSteps] = useState(40);
  const [minutes, setMinutes] = useState(480);
  const [scheduled, setScheduled] = useState(false);
  const [startTime, setStartTime] = useState('');
  const [startWindow, setStartWindow] = useState(15);
  const [scheduleReviewed, setScheduleReviewed] = useState(false);
  const scheduledEpoch = Math.floor(new Date(startTime).getTime() / 1000);
  const scheduleValid =
    !scheduled ||
    (Number.isFinite(scheduledEpoch) && scheduledEpoch > Date.now() / 1000 && scheduleReviewed);
  const [specification, setSpecification] = useState(initial?.specification || '');
  const [specs, setSpecs] = useState<Specification[]>([]);
  const [review, setReview] = useState<{ job: string; proposal: ProposalDetail } | null>(null);
  const live = useRef(true);
  const pending = useRef({ key: '', id: crypto.randomUUID() });
  const selectedWorkspace = dashboard?.workspaces.find((w) => w.resource === resource);
  const fileLimit = contextMode === 'retrieve' ? 100 : 20;
  const selectedFiles = files || selectedWorkspace?.files.slice(0, fileLimit) || [];
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
        <h2>Model-backed coding jobs</h2>
        <span>{enabled ? 'Core enabled' : 'Disabled or runtime unavailable'}</span>
      </div>
      <p>
        Repair a failing baseline or implement a feature on a registered snapshot. Both modes
        require a verified baseline, reviewed changes and passing retests. Passing tests establish
        tested behaviour; feature completeness still needs independent review. Original source
        delivery remains separately reviewed.
      </p>
      <p>
        Each model-call slot is charged before dispatch, including failed or uncertain requests.
        Currency estimates are not available. Time limits are checked between bounded steps.
      </p>
      <details
        className="build-job-configuration"
        open={configurationOpen}
        onToggle={(event) => setConfigurationOpen(event.currentTarget.open)}
      >
        <summary>{jobs.length ? 'Configure another repair job' : 'Configure repair job'}</summary>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void perform(async () => {
              if (!scheduleValid)
                throw new Error('Review a valid future start time and scheduling conditions.');
              if (!skillSelectionValid)
                throw new Error('Review the current trusted skill revisions.');
              const body = {
                edit_protocol: 'host-bound-v2',
                context_mode: contextMode,
                conversation: conversation || null,
                mode,
                resource,
                profile,
                provider,
                goal,
                files: selectedFiles,
                skills: Object.keys(skills),
                expected_skills: skills,
                max_calls: calls,
                max_cycles: cycles,
                max_steps: steps,
                duration_seconds: minutes * 60,
                auto_accept: autoAccept,
                allow_model_calls: consent,
                specification: specification || null,
                start_at: scheduled ? scheduledEpoch : null,
                start_window_seconds: scheduled ? startWindow * 60 : 900,
              };
              const key = JSON.stringify([project, body]);
              if (pending.current.key !== key) pending.current = { key, id: crypto.randomUUID() };
              await request({
                action: 'create_build_job',
                project,
                body: { ...body, request_id: pending.current.id },
              });
              await load();
              setConfigurationOpen(false);
              notice(
                scheduled
                  ? 'Scheduled coding job saved with bound inputs. The PC, Core and hidden runner must remain running.'
                  : `${mode === 'feature' ? 'Feature' : 'Repair'} job queued. The hidden runner must be active to continue.`,
              );
            });
          }}
        >
          <label>
            Coding mode
            <select
              aria-label="Build coding mode"
              value={mode}
              disabled={busy || !enabled}
              onChange={(event) => {
                setMode(event.target.value as 'repair' | 'feature');
                setConsent(false);
                setAutoAccept(false);
                setScheduleReviewed(false);
              }}
            >
              <option value="repair">Repair a failing baseline</option>
              <option value="feature">Implement a feature</option>
            </select>
          </label>
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
            Coding goal
            <textarea
              aria-label="Build goal"
              value={goal}
              required
              maxLength={8000}
              disabled={busy || !enabled}
              onChange={(event) => setGoal(event.target.value)}
            />
          </label>
          <label className="wide">
            Link coding history to conversation
            <select
              aria-label="Coding history conversation"
              value={conversation}
              disabled={busy || !enabled}
              onChange={(event) => {
                setConversation(event.target.value);
                setConsent(false);
                setAutoAccept(false);
                setScheduleReviewed(false);
              }}
            >
              <option value="">Keep this job separate from conversations</option>
              {dashboard?.conversations.map((item) => (
                <option key={item.id} value={item.id}>
                  Conversation {item.id.slice(0, 8)} · {item.message_count} messages
                </option>
              ))}
            </select>
            <small>
              The link records coding history. Model input still uses the selected files and
              specification.
            </small>
          </label>
          <fieldset>
            <legend>
              {contextMode === 'retrieve'
                ? 'Approved retrieval candidates'
                : 'Selected model context'}
            </legend>
            <label className="wide">
              Context selection
              <select
                aria-label="Build context mode"
                value={contextMode}
                disabled={busy || !enabled}
                onChange={(event) => {
                  setContextMode(event.target.value as 'selected' | 'retrieve');
                  setFiles(null);
                  setConsent(false);
                  setAutoAccept(false);
                  setScheduleReviewed(false);
                }}
              >
                <option value="selected">Send selected files</option>
                <option value="retrieve">Retrieve from approved snapshot candidates</option>
              </select>
            </label>
            <small>
              {contextMode === 'retrieve'
                ? 'Locally rank up to 100 checked snapshot files. Send at most 20 whole files, protected tests and selection metadata. No source-folder scan or automatic dependency access.'
                : "Include the profile's protected tests. Only selected files and bounded verified test output are shared."}
            </small>
            {selectedWorkspace?.files.map((path) => (
              <label key={path} className="checkbox">
                <input
                  type="checkbox"
                  checked={selectedFiles.includes(path)}
                  disabled={
                    busy || (!selectedFiles.includes(path) && selectedFiles.length >= fileLimit)
                  }
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
            Implementation-cycle limit
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
              aria-label="Schedule build start"
              checked={scheduled}
              disabled={busy || !enabled}
              onChange={(event) => {
                setScheduled(event.target.checked);
                setScheduleReviewed(false);
              }}
            />
            Start this job at a future time
          </label>
          {scheduled && (
            <>
              <label>
                Local start time
                <input
                  type="datetime-local"
                  step="1"
                  aria-label="Scheduled build start time"
                  required
                  value={startTime}
                  onChange={(event) => {
                    setStartTime(event.target.value);
                    setScheduleReviewed(false);
                  }}
                />
              </label>
              <label>
                Allowed late start (minutes)
                <input
                  type="number"
                  aria-label="Scheduled build start window"
                  min="1"
                  max="1440"
                  required
                  value={startWindow}
                  onChange={(event) => {
                    setStartWindow(Number(event.target.value));
                    setScheduleReviewed(false);
                  }}
                />
              </label>
              <p className="wide">
                Time zone: {Intl.DateTimeFormat().resolvedOptions().timeZone}. One-time start within
                seven days. The duration budget begins at the planned time. Missed starts fail
                without execution; changed selected inputs require a new reviewed job. The PC, Core
                and runner must be running. This does not wake or start Windows.
              </p>
              <label className="checkbox wide">
                <input
                  type="checkbox"
                  aria-label="Review scheduled build conditions"
                  checked={scheduleReviewed}
                  onChange={(event) => setScheduleReviewed(event.target.checked)}
                />
                I reviewed the start time, late-start window and unchanged-input requirement.
              </label>
            </>
          )}
          <TrustedSkills
            available={skillChoices}
            selected={skills}
            disabled={busy || !enabled}
            onChange={(value) => {
              setSkills(value);
              setConsent(false);
              setAutoAccept(false);
              setScheduleReviewed(false);
            }}
          />
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
              !scheduleValid ||
              !skillSelectionValid ||
              !consent ||
              !goal.trim() ||
              !selectedFiles.length ||
              !resource ||
              !provider ||
              !profile
            }
          >
            {mode === 'feature' ? 'Queue model feature job' : 'Queue model repair job'}
          </button>
        </form>
      </details>
      <button disabled={busy} onClick={() => void perform(load)}>
        Refresh build jobs
      </button>
      {!jobs.length && <p>No coding jobs have been queued.</p>}
      {jobs.map((job) => (
        <article className="build-job-card" data-job-id={job.id} key={job.id}>
          <h3>{job.goal}</h3>
          <p>
            {job.config.mode === 'feature' ? 'Feature · independent acceptance required' : 'Repair'}
          </p>
          {job.config.context_mode === 'retrieve' && (
            <p>Retrieved context · approved snapshot scope</p>
          )}
          <strong>
            {job.state === 'queued' && job.summary.reason === 'scheduled'
              ? 'scheduled'
              : job.state.replaceAll('_', ' ')}{' '}
            · {job.phase}
          </strong>
          <p>
            {job.calls}/{job.config.max_calls} model-call slots · Cycle {job.cycle}/
            {job.config.max_cycles} · {job.steps}/{job.config.max_steps} step slots
          </p>
          <small>
            Job {job.id} · Deadline {new Date(job.deadline * 1000).toLocaleString()}
          </small>
          {job.config.skill_bindings && Object.keys(job.config.skill_bindings).length > 0 && (
            <p className="job-guidance">
              Selected guidance:{' '}
              {Object.entries(job.config.skill_bindings).map(([name, sha]) => (
                <span key={name} title={sha}>
                  {name} · {sha.slice(0, 12)}{' '}
                </span>
              ))}
            </p>
          )}
          <SupervisionStatus value={job.state === 'running' ? job.supervision : null} />
          {job.config.schedule && (
            <p>
              Planned start: {new Date(job.config.schedule.start_at * 1000).toLocaleString()} ·
              Start by: {new Date(job.config.schedule.start_by * 1000).toLocaleString()}. Selected
              inputs are bound to this schedule.
            </p>
          )}
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
              <RetrievalReview context={review.proposal.context} />
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
          <GenerationRecovery
            key={job.proposal || job.id}
            job={job}
            disabled={busy || !enabled}
            perform={perform}
            onQueued={async () => {
              await load();
              notice(
                'New generation queued within the original job budget. The failed attempt is retained.',
              );
            }}
          />
        </article>
      ))}
    </section>
  );
}
