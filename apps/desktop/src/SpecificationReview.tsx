import { useEffect, useId, useRef, useState } from 'react';
import { exportSpecification, request } from './api';
import type { Specification } from './types';

const names = [
  '01_PRODUCT_REQUIREMENTS.md',
  '02_SYSTEM_ARCHITECTURE.md',
  '03_DEVELOPMENT_RULES.md',
  '04_DESIGN_SYSTEM.md',
  '05_PROJECT_TASKS.md',
  '06_PROJECT_MEMORY.md',
  '07_API_AND_EVENTS.md',
  '08_TESTING_AND_ACCEPTANCE.md',
  '09_SECURITY_AND_OPERATIONS.md',
];
const required = new Set([names[0], names[4], names[5], names[7]]);

function RevisionEditor({
  spec,
  version,
  busy,
  error,
  close,
  save,
}: {
  spec: Specification;
  version: number;
  busy: boolean;
  error: string;
  close: () => void;
  save: (documents: Record<string, string>, version: number, requestId: string) => void;
}) {
  const [documents, setDocuments] = useState({ ...spec.documents });
  const [selected, setSelected] = useState(Object.keys(spec.documents).sort()[0]);
  const [additional, setAdditional] = useState('');
  const [expectedVersion] = useState(version);
  const requestId = useRef({ signature: '', id: crypto.randomUUID() });
  const heading = useId(),
    control = useId();
  const editor = useRef<HTMLTextAreaElement>(null);
  const previous = useRef(document.activeElement);
  useEffect(() => {
    editor.current?.focus();
    return () => {
      if (previous.current instanceof HTMLElement) previous.current.focus();
    };
  }, []);
  const changed = JSON.stringify(documents) !== JSON.stringify(spec.documents);
  return (
    <div className="modal-backdrop">
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby={heading}
        className="modal specification-editor"
        onKeyDown={(e) => {
          if (e.key === 'Escape' && !busy) close();
          if (e.key === 'Tab') {
            const controls = Array.from(
              e.currentTarget.querySelectorAll<HTMLElement>(
                'button:not(:disabled),select:not(:disabled),textarea:not(:disabled)',
              ),
            );
            if (e.shiftKey && document.activeElement === controls[0]) {
              e.preventDefault();
              controls.at(-1)?.focus();
            } else if (!e.shiftKey && document.activeElement === controls.at(-1)) {
              e.preventDefault();
              controls[0]?.focus();
            }
          }
        }}
      >
        {error && (
          <p role="alert" className="error-text">
            {error}
          </p>
        )}
        <h2 id={heading}>Revise specification version {spec.version}</h2>
        <p>
          Save creates a new draft. The original documents and approval remain unchanged until you
          approve a newer version.
        </p>
        <label>
          Document
          <select
            aria-label="Revision document"
            value={selected}
            disabled={busy}
            onChange={(e) => setSelected(e.target.value)}
          >
            {Object.keys(documents)
              .sort()
              .map((name) => (
                <option key={name}>{name}</option>
              ))}
          </select>
        </label>
        <label htmlFor={control}>Document content</label>
        <textarea
          id={control}
          ref={editor}
          value={documents[selected]}
          disabled={busy}
          maxLength={24000}
          rows={14}
          onChange={(e) => setDocuments({ ...documents, [selected]: e.target.value })}
        />
        <div className="two-columns">
          <label>
            Additional document
            <select
              aria-label="Additional specification document"
              value={additional}
              disabled={busy}
              onChange={(e) => setAdditional(e.target.value)}
            >
              <option value="">Choose a document</option>
              {names
                .filter((name) => !(name in documents))
                .map((name) => (
                  <option key={name}>{name}</option>
                ))}
            </select>
          </label>
          <button
            disabled={busy || !additional}
            onClick={() => {
              setDocuments({ ...documents, [additional]: '' });
              setSelected(additional);
              setAdditional('');
            }}
          >
            Add document
          </button>
        </div>
        {!required.has(selected) && (
          <button
            disabled={busy}
            onClick={() => {
              const next = { ...documents };
              delete next[selected];
              setDocuments(next);
              setSelected(Object.keys(next).sort()[0]);
            }}
          >
            Remove optional document
          </button>
        )}
        <p>Each document: up to 24 KB. Canonical bundle: up to 64 KB. No model call is made.</p>
        <button disabled={busy} onClick={close}>
          Cancel revision
        </button>
        <button
          className="primary"
          disabled={busy || !changed || Object.values(documents).some((text) => !text.trim())}
          onClick={() => {
            const signature = JSON.stringify(documents);
            if (requestId.current.signature !== signature)
              requestId.current = { signature, id: crypto.randomUUID() };
            save(documents, expectedVersion, requestId.current.id);
          }}
        >
          Save revised draft
        </button>
      </section>
    </div>
  );
}

export default function SpecificationReview({
  spec,
  latestVersion,
  busy,
  error,
  perform,
  onSaved,
  notice,
}: {
  spec: Specification;
  latestVersion: number;
  busy: boolean;
  error: string;
  perform: (operation: () => Promise<void>) => Promise<void>;
  onSaved: (spec: Specification) => Promise<void>;
  notice: (message: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  return (
    <article className="model-result">
      <h3>
        Specification version {spec.version} - {spec.state}
      </h3>
      <small>SHA-256: {spec.sha256}</small>
      {spec.parent_spec && <p>Revised from specification {spec.parent_spec.slice(0, 8)}.</p>}
      {Object.entries(spec.documents).map(([name, content]) => (
        <details key={name}>
          <summary>{name}</summary>
          <pre>{content}</pre>
        </details>
      ))}
      <button disabled={busy} onClick={() => setEditing(true)}>
        Edit as new revision
      </button>
      <button
        disabled={busy || spec.state !== 'draft' || latestVersion !== spec.version}
        onClick={() =>
          void perform(async () => {
            await onSaved(
              await request<Specification>({
                action: 'approve_specification',
                id: spec.id,
                body: { expected_sha256: spec.sha256 },
              }),
            );
            notice('Specification approved. No coding tasks have been started.');
          })
        }
      >
        Approve reviewed specification
      </button>
      <button
        disabled={busy || spec.state !== 'approved'}
        onClick={() =>
          void perform(async () => {
            const result = await exportSpecification(spec.id, spec.sha256);
            notice(
              `${result.existing ? 'Verified existing export' : 'Exported ' + result.files + ' documents'}: ${result.directory}`,
            );
          })
        }
      >
        Export approved documents
      </button>
      <p>
        Export creates a version folder in Documents/Skyra/Jarvis/exports, or the trusted
        host-configured export root. Existing files are never overwritten.
      </p>
      {editing && (
        <RevisionEditor
          spec={spec}
          version={latestVersion}
          busy={busy}
          error={error}
          close={() => setEditing(false)}
          save={(documents, expected_version, request_id) =>
            void perform(async () => {
              const result = await request<Specification>({
                action: 'revise_specification',
                id: spec.id,
                body: { documents, expected_version, expected_sha256: spec.sha256, request_id },
              });
              setEditing(false);
              await onSaved(result);
              notice('Revised draft saved. Review and approve it separately.');
            })
          }
        />
      )}
    </article>
  );
}
