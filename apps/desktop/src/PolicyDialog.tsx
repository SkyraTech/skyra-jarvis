import { useEffect, useRef, useState } from 'react';
import type { Dashboard } from './types';

export default function PolicyDialog({
  dashboard,
  busy,
  error,
  close,
  save,
}: {
  dashboard: Dashboard;
  busy: boolean;
  error: string;
  close: () => void;
  save: (mode: string, resources: string[], reviewedVersion: number) => void;
}) {
  const [mode, setMode] = useState(dashboard.project.mode);
  const [reviewedVersion] = useState(dashboard.project.version);
  const [resources, setResources] = useState(dashboard.project.resources || []);
  const available = [
    ...new Set([...(dashboard.registered_resources || []), ...(dashboard.project.resources || [])]),
  ];
  const select = useRef<HTMLSelectElement>(null);
  const blocked = useRef(busy);
  blocked.current = busy;
  useEffect(() => {
    const previous = document.activeElement;
    select.current?.focus();
    const key = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !blocked.current) close();
    };
    document.addEventListener('keydown', key);
    return () => {
      document.removeEventListener('keydown', key);
      if (previous instanceof HTMLElement) previous.focus();
    };
  }, []);
  return (
    <div className="modal-backdrop">
      <section
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="policy-title"
        onKeyDown={(e) => {
          if (e.key !== 'Tab') return;
          const fields = Array.from(
            e.currentTarget.querySelectorAll<HTMLElement>(
              'button:not(:disabled),select:not(:disabled),input:not(:disabled)',
            ),
          );
          if (e.shiftKey && document.activeElement === fields[0]) {
            e.preventDefault();
            fields.at(-1)?.focus();
          }
          if (!e.shiftKey && document.activeElement === fields.at(-1)) {
            e.preventDefault();
            fields[0]?.focus();
          }
        }}
      >
        <div className="panel-heading">
          <h2 id="policy-title">Project permissions</h2>
          <button disabled={busy} aria-label="Close permissions" onClick={close}>
            ×
          </button>
        </div>
        {error && (
          <p className="error-text" role="alert">
            {error}
          </p>
        )}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            save(mode, resources, reviewedVersion);
          }}
        >
          <label>
            Permission mode
            <select
              ref={select}
              value={mode}
              disabled={busy}
              onChange={(e) => setMode(e.target.value)}
            >
              <option value="read_only">Read only</option>
              <option value="ask">Ask for approval</option>
              <option value="full">Full access within selected resources</option>
            </select>
          </label>
          <p className="safety-note">
            Reviewed policy v{reviewedVersion}. If another client changes permissions, close and
            reopen this review before saving.
          </p>
          <fieldset>
            <legend>Exact resource grants</legend>
            {available.length ? (
              available.map((resource) => (
                <label key={resource} className="checkbox">
                  <input
                    type="checkbox"
                    checked={resources.includes(resource)}
                    disabled={busy}
                    onChange={(e) =>
                      setResources(
                        e.target.checked
                          ? [...resources, resource]
                          : resources.filter((r) => r !== resource),
                      )
                    }
                  />
                  {resource}
                </label>
              ))
            ) : (
              <p>No workspaces are registered by the trusted host.</p>
            )}
          </fieldset>
          <p className="safety-note">
            Saving changes increments the policy version and invalidates earlier approvals. Full
            mode allows writes and execution within these exact resources. Native execution carries
            your Windows account’s access. Register filesystem paths and fixed test commands outside
            the renderer.
          </p>
          <div className="actions">
            <button type="button" disabled={busy} onClick={close}>
              Cancel
            </button>
            <button className="primary" disabled={busy}>
              Save permission policy
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
