import { useState } from 'react';
import { request } from './api';

type Review = {
  enabled: boolean;
  registration_sha256: string;
  registration: {
    workspace: string;
    source: string;
    previous_workspace: string;
    selected: string[];
    profile: { name: string; protected_paths: string[] };
    lineage: { review: { hashes: Record<string, string> } };
  };
};
type Status = {
  registered: boolean;
  active?: boolean;
  reconciliation_required?: boolean;
  registration?: Review['registration'];
};

export default function ContinuationPanel({
  task,
  busy,
  perform,
  refresh,
}: {
  task: string;
  busy: boolean;
  perform: (operation: () => Promise<void>) => Promise<void>;
  refresh: () => Promise<void>;
}) {
  const [name, setName] = useState(`next-${task.slice(0, 12)}`);
  const [review, setReview] = useState<Review | null>(null);
  const [consent, setConsent] = useState(false);
  const [status, setStatus] = useState<Status | null>(null);
  const valid = /^[a-z][a-z0-9-]{1,47}$/.test(name);
  return (
    <section className="snapshot-continuation" aria-label="Continue delivered project">
      <h4>Continue in a fresh snapshot</h4>
      <p>
        Keep this run and its evidence unchanged. Register a new generation from the delivered
        source. Source edits or changed protected tests block continuation.
      </p>
      <label>
        Next generation name
        <input
          value={name}
          maxLength={48}
          disabled={busy}
          onChange={(e) => {
            setName(e.target.value);
            setReview(null);
            setConsent(false);
            setStatus(null);
          }}
        />
      </label>
      <button
        disabled={busy || !valid}
        onClick={() =>
          void perform(async () => {
            setReview(null);
            setConsent(false);
            setStatus(
              await request<Status>({ action: 'continuation_status', id: task, body: { name } }),
            );
          })
        }
      >
        Check generation status
      </button>
      <button
        disabled={busy || !valid || status?.registered === true}
        onClick={() =>
          void perform(async () => {
            setReview(null);
            setConsent(false);
            setReview(
              await request<Review>({ action: 'continuation_preview', id: task, body: { name } }),
            );
          })
        }
      >
        Review next snapshot
      </button>
      {review && !status?.registered && (
        <div className="continuation-review">
          <p>
            {review.registration.previous_workspace} → {review.registration.workspace}
          </p>
          <small>Registration SHA-256: {review.registration_sha256}</small>
          <p>Test profile: {review.registration.profile.name}</p>
          <details>
            <summary>Selected source hashes and protected files</summary>
            <ul>
              {review.registration.selected.map((path) => (
                <li key={path}>
                  {path} · {review.registration.lineage.review.hashes[path]}
                  {review.registration.profile.protected_paths.includes(path) ? ' · protected' : ''}
                </li>
              ))}
            </ul>
          </details>
          <label className="check-label">
            <input
              type="checkbox"
              disabled={busy || !review.enabled}
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
            />
            Allow this reviewed generation to use the existing native test profile
          </label>
          {!review.enabled && <p>Native registration is disabled by the host.</p>}
          <button
            disabled={busy || !consent || !review.enabled}
            onClick={() =>
              void perform(async () => {
                const result = await request<Status>({
                  action: 'continue_project',
                  id: task,
                  body: {
                    name,
                    expected_registration_sha256: review.registration_sha256,
                    allow_native_execution: consent,
                  },
                });
                setStatus(result);
                setConsent(false);
                await refresh();
              })
            }
          >
            Register reviewed generation
          </button>
        </div>
      )}
      {status && (
        <p role="status">
          {status.registered
            ? status.active
              ? `Generation registered: ${status.registration?.workspace}. Grant its workspace and source resources in Permissions before starting work.`
              : 'Generation saved but inactive. Reconcile the registered files before use.'
            : 'No generation is registered under this name.'}
        </p>
      )}
    </section>
  );
}
