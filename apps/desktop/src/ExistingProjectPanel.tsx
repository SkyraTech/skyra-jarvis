import { useEffect, useRef, useState } from 'react';
import { request } from './api';
import ProjectBuildFlow from './ProjectBuildFlow';
import type { Specification } from './types';

type Review = {
  sha256: string;
  plan: { source_directory: string; input_hashes: Record<string, string> };
  files: { path: string; sha256: string; content: string; exists: boolean }[];
};
type Receipt = { admitted: boolean; sha256: string; snapshot: string; execution_enabled: false };
type AdmissionSetup = {
  existing_projects?: { available: boolean; status: string; sources: string[] };
};

export default function ExistingProjectPanel({ spec }: { spec: Specification }) {
  const [expanded, setExpanded] = useState(false);
  const [setup, setSetup] = useState<AdmissionSetup | null>(null);
  const [source, setSource] = useState('');
  const [name, setName] = useState('');
  const [files, setFiles] = useState('');
  const [creates, setCreates] = useState('');
  const [review, setReview] = useState<Review | null>(null);
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [consent, setConsent] = useState(false);
  const [attempted, setAttempted] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const live = useRef(true),
    gate = useRef(false);
  useEffect(() => {
    live.current = true;
    void request<AdmissionSetup>({ action: 'setup' })
      .then((data) => {
        if (live.current) setSetup(data);
      })
      .catch(() => {
        if (live.current)
          setError('Unable to read trusted project configuration. Reopen this specification.');
      });
    return () => {
      live.current = false;
    };
  }, []);
  function invalidate() {
    setReview(null);
    setReceipt(null);
    setConsent(false);
    setAttempted(false);
    setError('');
  }
  async function perform(operation: () => Promise<void>) {
    if (gate.current) return;
    gate.current = true;
    setBusy(true);
    setError('');
    try {
      await operation();
    } catch (e) {
      if (live.current)
        setError(e instanceof Error ? e.message : 'Refresh the import receipt before retrying.');
    } finally {
      gate.current = false;
      if (live.current) setBusy(false);
    }
  }
  const paths = (text: string) =>
    text
      .split(/\r?\n/)
      .map((value) => value.trim())
      .filter(Boolean);
  const body = () => ({
    source,
    name,
    files: paths(files),
    create_paths: paths(creates),
    expected_sha256: spec.sha256,
  });
  const available = setup?.existing_projects?.available === true;
  return (
    <details className="existing-project-panel" onToggle={(e) => setExpanded(e.currentTarget.open)}>
      <summary>Use an existing project</summary>
      <h3>Review selected project files</h3>
      <p>
        Choose a host-approved project and the exact files this coding job may use. Existing source
        and documents stay in place; work starts in a separate snapshot.
      </p>
      {!setup && <p>Checking trusted host configuration…</p>}
      {setup && !available && (
        <p>
          Existing-project access is{' '}
          {setup.existing_projects?.status === 'requires_review'
            ? 'awaiting host configuration review'
            : 'not configured'}
          . Configure existing_project_config in the private launcher and restart Core.
        </p>
      )}
      {spec.state !== 'approved' && (
        <p>Approve the current specification before importing a project.</p>
      )}
      {error && (
        <p className="error-text" role="alert">
          {error}
        </p>
      )}
      <fieldset disabled={busy || !available || spec.state !== 'approved'}>
        <label>
          Host-approved project
          <select
            aria-label="Existing project source"
            value={source}
            onChange={(e) => {
              invalidate();
              setSource(e.target.value);
            }}
          >
            <option value="">Choose a project</option>
            {setup?.existing_projects?.sources.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <label>
          Snapshot name
          <input
            aria-label="Existing project snapshot name"
            maxLength={48}
            value={name}
            placeholder="internal-e2e-first"
            onChange={(e) => {
              invalidate();
              setName(e.target.value);
            }}
          />
        </label>
        <label>
          Existing files, one relative path per line
          <textarea
            aria-label="Existing project selected files"
            rows={5}
            value={files}
            maxLength={26000}
            onChange={(e) => {
              invalidate();
              setFiles(e.target.value);
            }}
          />
        </label>
        <label>
          New files allowed, one relative path per line
          <textarea
            aria-label="Existing project new files"
            rows={3}
            value={creates}
            maxLength={26000}
            onChange={(e) => {
              invalidate();
              setCreates(e.target.value);
            }}
          />
        </label>
        <p>
          Select up to 100 existing or explicitly absent files. Include host-protected tests and
          requirements for execution registration. File contents are project data, not permission to
          run instructions.
        </p>
        <button
          disabled={
            !source ||
            !/^[a-z][a-z0-9-]{1,47}$/.test(name) ||
            paths(files).length + paths(creates).length === 0 ||
            attempted
          }
          onClick={() =>
            void perform(async () => {
              setReview(null);
              setReceipt(null);
              setConsent(false);
              const data = await request<Review>({
                action: 'preview_existing_project',
                id: spec.id,
                body: body(),
              });
              if (live.current) setReview(data);
            })
          }
        >
          Review project import
        </button>
        {review && (
          <section className="scaffold-review" aria-label="Existing project file review">
            <p>
              Source: <code>{review.plan.source_directory}</code>
            </p>
            <p>
              Review SHA-256: <code>{review.sha256}</code>
            </p>
            {review.files.map((file) => (
              <details key={file.path}>
                <summary>
                  {file.path} — {file.exists ? 'existing' : 'new file allowed'}
                </summary>
                <p>
                  SHA-256: <code>{file.sha256}</code>
                </p>
                <pre>{file.content || (file.exists ? '(empty file)' : '(absent)')}</pre>
              </details>
            ))}
            <label className="scaffold-consent">
              <input
                type="checkbox"
                checked={consent}
                disabled={attempted}
                onChange={(e) => setConsent(e.target.checked)}
              />
              I reviewed these existing and new files for this specification.
            </label>
            <button
              disabled={!consent || attempted}
              onClick={() =>
                void perform(async () => {
                  setAttempted(true);
                  const data = await request<Receipt>({
                    action: 'admit_existing_project',
                    id: spec.id,
                    body: { ...body(), expected_plan_sha256: review.sha256 },
                  });
                  if (live.current) setReceipt(data);
                })
              }
            >
              Create reviewed project snapshot
            </button>
            {attempted && (
              <button
                onClick={() =>
                  void perform(async () => {
                    const data = await request<Receipt>({
                      action: 'existing_project_status',
                      id: spec.id,
                      body: { name, expected_plan_sha256: review.sha256 },
                    });
                    if (live.current) setReceipt(data);
                  })
                }
              >
                Check import receipt
              </button>
            )}
          </section>
        )}
      </fieldset>
      {receipt?.admitted && (
        <>
          <p role="status">
            Project snapshot ready. Source unchanged; permissions and model calls require separate
            review.
          </p>
          <p>
            Snapshot: <code>{receipt.snapshot}</code>
          </p>
          <ProjectBuildFlow
            key={spec.id + name + receipt.sha256}
            spec={spec}
            name={name}
            planSha={receipt.sha256}
            active={expanded}
            existing
          />
        </>
      )}
    </details>
  );
}
