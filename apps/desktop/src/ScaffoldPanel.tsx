import { useEffect, useRef, useState } from 'react';
import { request } from './api';
import type { ScaffoldPlan, ScaffoldReceipt, Specification } from './types';
import ProjectBuildFlow from './ProjectBuildFlow';

export default function ScaffoldPanel({ spec }: { spec: Specification }) {
  const [available, setAvailable] = useState<boolean | null>(null);
  const [nodeConfigured, setNodeConfigured] = useState(false);
  const [name, setName] = useState('');
  const [template, setTemplate] = useState('python-json-function-v1');
  const [expanded, setExpanded] = useState(false);
  const [examples, setExamples] = useState('');
  const [plan, setPlan] = useState<ScaffoldPlan | null>(null);
  const [receipt, setReceipt] = useState<ScaffoldReceipt | null>(null);
  const [reviewed, setReviewed] = useState(false);
  const [attempted, setAttempted] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const gate = useRef(false);
  const live = useRef(true);
  useEffect(() => {
    live.current = true;
    void request<{ scaffolds?: { available: boolean; templates?: string[] } }>({ action: 'setup' })
      .then((data) => {
        if (live.current) setAvailable(data.scaffolds?.available === true);
        if (live.current)
          setNodeConfigured(
            data.scaffolds?.templates?.includes('typescript-json-function-v1') === true,
          );
      })
      .catch(() => {
        if (live.current)
          setError('Unable to check scaffold configuration. Reopen the specification.');
      });
    return () => {
      live.current = false;
    };
  }, []);

  function invalidate() {
    setPlan(null);
    setReceipt(null);
    setReviewed(false);
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
        setError(e instanceof Error ? e.message : 'Unable to complete this action.');
    } finally {
      gate.current = false;
      if (live.current) setBusy(false);
    }
  }
  const validName = /^[a-z][a-z0-9-]{1,47}$/.test(name);
  return (
    <details className="scaffold-panel" onToggle={(e) => setExpanded(e.currentTarget.open)}>
      <summary>New project scaffold</summary>
      <h3>Create project from specification</h3>
      <p>
        Create a Python/TypeScript function project or a local website/HTTP service from approved
        requirements and protected acceptance examples.
      </p>
      {available === null && <p>Checking trusted host configuration…</p>}
      {available === false && (
        <p>
          Project creation is disabled. Configure an existing private scaffold_root in the launcher
          and restart Core. No execution permission is enabled by this setting.
        </p>
      )}
      {spec.state !== 'approved' && (
        <p>
          Approve this specification before previewing or creating a new project. Existing creation
          receipts can still be checked.
        </p>
      )}
      {error && (
        <p className="error-text" role="alert">
          {error}
        </p>
      )}
      <fieldset disabled={busy || available !== true}>
        <label>
          Project template
          <select
            aria-label="Scaffold project template"
            value={template}
            onChange={(e) => {
              invalidate();
              setTemplate(e.target.value);
            }}
          >
            <option value="python-json-function-v1">Python JSON function</option>
            <option value="python-web-service-v1">Local website / HTTP service</option>
            <option value="typescript-json-function-v1" disabled={!nodeConfigured}>
              TypeScript JSON function
            </option>
          </select>
        </label>
        {!nodeConfigured && (
          <small>TypeScript creation needs a reviewed host Node/TypeScript toolchain.</small>
        )}
        {template === 'typescript-json-function-v1' && (
          <p>
            Strict TypeScript library. The registered host profile compiles before running protected
            Node tests. No dependencies are installed during creation.
          </p>
        )}
        {template === 'python-web-service-v1' && (
          <p>
            Web cases use input method (GET/POST), path and body; output status, content_type and
            body. For an HTML home page, expected body must match index.html. Tests make real
            loopback HTTP requests.
          </p>
        )}
        <label>
          New project name
          <input
            aria-label="Scaffold project name"
            value={name}
            maxLength={48}
            placeholder="client-service"
            onChange={(e) => {
              invalidate();
              setName(e.target.value);
            }}
          />
        </label>
        <label>
          Acceptance examples (JSON)
          <textarea
            aria-label="Scaffold acceptance examples"
            value={examples}
            maxLength={16000}
            rows={8}
            placeholder={'{"cases":[{"name":"positive","input":3,"output":6}]}'}
            onChange={(e) => {
              invalidate();
              setExamples(e.target.value);
            }}
          />
        </label>
        <p>
          Use 1–32 unique named cases matching the approved requirements. Review the complete
          input/output contract. Passing these examples alone does not establish coverage or
          security.
        </p>
        <div className="scaffold-actions">
          <button
            disabled={!validName || !examples.trim() || spec.state !== 'approved' || attempted}
            onClick={() =>
              void perform(async () => {
                setPlan(null);
                setReviewed(false);
                setReceipt(null);
                let contract: unknown;
                try {
                  contract = JSON.parse(examples);
                } catch {
                  throw new Error('Acceptance examples must be valid JSON.');
                }
                const result = await request<ScaffoldPlan>({
                  action: 'preview_scaffold',
                  id: spec.id,
                  body: { name, contract, expected_sha256: spec.sha256, template },
                });
                if (live.current) setPlan(result);
              })
            }
          >
            Preview project files
          </button>
          <button
            disabled={!validName}
            onClick={() =>
              void perform(async () => {
                const result = await request<ScaffoldReceipt>({
                  action: 'scaffold_status',
                  id: spec.id,
                  body: { name },
                });
                if (live.current) setReceipt(result);
              })
            }
          >
            Check creation receipt
          </button>
        </div>
        {plan && (
          <section className="scaffold-review" aria-label="Scaffold file review">
            <h4>Review every planned file</h4>
            <p>
              Destination: <code>{plan.plan.destination}</code>
            </p>
            <p>
              Plan SHA-256: <code>{plan.plan_sha256}</code>
            </p>
            <p>
              {plan.plan.runtime ? 'Node SHA-256' : 'Interpreter SHA-256'}:{' '}
              <code>{plan.plan.executable_sha256 || plan.plan.python_sha256}</code>
            </p>
            {plan.plan.runtime && (
              <p>
                {plan.plan.runtime.toolchain.node_version} ·{' '}
                {plan.plan.runtime.toolchain.compiler_version}
                <br />
                Compiler SHA-256: <code>{plan.plan.runtime.toolchain.compiler_sha256}</code>
              </p>
            )}
            <details>
              <summary>Protected tests and fixed execution profile</summary>
              <pre>{JSON.stringify(plan.plan.profile, null, 2)}</pre>
            </details>
            {Object.entries(plan.plan.files).map(([path, content]) => (
              <details key={path}>
                <summary>{path}</summary>
                {path.startsWith('docs/') && (
                  <p>Document origin: {plan.plan.document_provenance[path.slice(5)]}</p>
                )}
                <pre>{content}</pre>
              </details>
            ))}
            <ul>
              {plan.plan.limitations.map((limit) => (
                <li key={limit}>{limit}</li>
              ))}
            </ul>
            <label className="scaffold-consent">
              <input
                type="checkbox"
                checked={reviewed}
                disabled={attempted}
                onChange={(e) => setReviewed(e.target.checked)}
              />
              I reviewed the destination, all files, examples and execution profile.
            </label>
            <button
              className="primary"
              disabled={!reviewed || attempted || spec.state !== 'approved'}
              onClick={() =>
                void perform(async () => {
                  setAttempted(true);
                  const result = await request<ScaffoldReceipt>({
                    action: 'create_scaffold',
                    id: spec.id,
                    body: {
                      name: plan.plan.name,
                      contract: plan.plan.contract,
                      expected_sha256: plan.plan.specification_sha256,
                      expected_plan_sha256: plan.plan_sha256,
                      template: plan.plan.template,
                    },
                  });
                  if (live.current) setReceipt({ ...result, exists: true });
                })
              }
            >
              Create reviewed project
            </button>
          </section>
        )}
      </fieldset>
      {attempted && !receipt?.exists && (
        <p role="status">
          Creation was attempted. Check its receipt before taking another action; no automatic retry
          will run.
        </p>
      )}
      {receipt && (
        <section aria-label="Scaffold creation receipt" role="status">
          {receipt.exists ? (
            <>
              <h4>Project creation receipt</h4>
              <p>
                <code>{receipt.directory}</code>
              </p>
              <p>
                Plan SHA-256: <code>{receipt.plan_sha256}</code>
              </p>
              {receipt.audit_recorded === false && (
                <p className="error-text">
                  The creation audit event is missing. Inspect the receipt and reconcile manually
                  before continuing.
                </p>
              )}
              <p>
                Initial state: unimplemented. Creation does not register this workspace or enable
                its execution. Continue below to review registration, permissions and the build job.
                Source delivery requires its own review.
              </p>
            </>
          ) : (
            <p>
              No published project receipt was found for this name. An interrupted staging folder
              may still require owner inspection.
            </p>
          )}
        </section>
      )}
      {receipt?.exists && receipt.plan_sha256 && expanded && (
        <ProjectBuildFlow
          key={spec.id + name + receipt.plan_sha256}
          spec={spec}
          name={name}
          planSha={receipt.plan_sha256}
          active={expanded}
        />
      )}
    </details>
  );
}
