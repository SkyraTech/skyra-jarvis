import { useEffect, useRef, useState } from 'react';
import { request } from './api';
import type { Dashboard, Run } from './types';
import ContinuationPanel from './ContinuationPanel';

type Preview = {
  sha256: string;
  plan: { changes: { path: string; before_sha256: string; sha256: string; patch: string }[] };
};
type Delivery = { id: string; target: string; state: string; sha256: string; evidence: string[] };

export default function DeliveryPanel({
  run,
  dashboard,
  busy,
  worker,
  perform,
  refresh,
  notice,
}: {
  run: Run;
  dashboard: Dashboard | null;
  busy: boolean;
  worker: boolean;
  perform: (operation: () => Promise<void>) => Promise<void>;
  refresh: () => Promise<void>;
  notice: (text: string) => void;
}) {
  const targets = (dashboard?.delivery_targets || []).filter((t) => t.workspace === run.resource);
  const [target, setTarget] = useState(targets[0]?.resource || '');
  const [preview, setPreview] = useState<Preview | null>(null);
  const [deliveries, setDeliveries] = useState<Delivery[]>([]);
  const [evidence, setEvidence] = useState<unknown>(null);
  const pending = useRef({ key: '', id: crypto.randomUUID() });
  const live = useRef(true);
  async function load() {
    const data = await request<{ deliveries: Delivery[] }>({ action: 'deliveries', id: run.id });
    if (live.current) setDeliveries(data.deliveries);
  }
  useEffect(() => {
    live.current = true;
    void load().catch(() => notice('Unable to load delivery history. Refresh the run.'));
    return () => {
      live.current = false;
    };
  }, [run.id]);
  return (
    <section className="source-delivery">
      <h3>Deliver to project source</h3>
      <p>
        Review the tested files, then prepare a separate source write. Source conflicts block
        delivery. A multi-file interruption may need recovery; it does not automatically roll back.
      </p>
      {!targets.length ? (
        <p>No source target is registered and granted for this workspace.</p>
      ) : (
        <>
          <label>
            Source target
            <select
              aria-label="Source target"
              value={target}
              disabled={busy}
              onChange={(e) => {
                setTarget(e.target.value);
                setPreview(null);
              }}
            >
              {targets.map((t) => (
                <option key={t.resource}>{t.resource}</option>
              ))}
            </select>
          </label>
          <button
            disabled={busy || !target}
            onClick={() =>
              void perform(async () =>
                setPreview(
                  await request<Preview>({
                    action: 'delivery_preview',
                    id: run.id,
                    body: { target },
                  }),
                ),
              )
            }
          >
            Review source delivery
          </button>
          {preview && (
            <div className="delivery-review">
              <small>Delivery manifest SHA-256: {preview.sha256}</small>
              {preview.plan.changes.map((change) => (
                <details key={change.path}>
                  <summary>
                    {change.path} ·{' '}
                    {change.before_sha256 === 'absent' ? 'new file' : 'replace matching baseline'}
                  </summary>
                  <pre>{change.patch}</pre>
                </details>
              ))}
              <button
                disabled={busy}
                onClick={() =>
                  void perform(async () => {
                    const key = JSON.stringify([run.id, target, preview.sha256]);
                    if (pending.current.key !== key)
                      pending.current = { key, id: crypto.randomUUID() };
                    await request<Delivery>({
                      action: 'prepare_delivery',
                      id: run.id,
                      body: {
                        target,
                        expected_sha256: preview.sha256,
                        request_id: pending.current.id,
                      },
                    });
                    await load();
                    notice(
                      'Source delivery prepared. Advance it to request the current permission-policy approval.',
                    );
                  })
                }
              >
                Prepare reviewed delivery
              </button>
            </div>
          )}
        </>
      )}
      <button disabled={busy} onClick={() => void perform(load)}>
        Refresh deliveries
      </button>
      {deliveries.map((delivery) => (
        <article key={delivery.id}>
          <strong>
            Delivery {delivery.target} · {delivery.state}
          </strong>
          <p>
            <small>
              {delivery.id} · {delivery.sha256}
            </small>
          </p>
          <button
            disabled={busy || !worker || !['queued', 'waiting_approval'].includes(delivery.state)}
            onClick={() =>
              void perform(async () => {
                const result = await request<Delivery>({
                  action: 'advance_delivery',
                  id: delivery.id,
                });
                await load();
                await refresh();
                notice(
                  result.state === 'waiting_approval'
                    ? 'Source delivery is waiting for exact-action approval in Approvals.'
                    : `Source delivery state: ${result.state}. Inspect its evidence before continuing.`,
                );
              })
            }
          >
            Advance source delivery
          </button>
          {delivery.evidence.map((reference) => (
            <button
              className="delivery-evidence"
              key={reference}
              disabled={busy}
              onClick={() =>
                void perform(async () =>
                  setEvidence(
                    await request({
                      action: 'evidence',
                      id: delivery.id,
                      checksum: reference.slice(7),
                    }),
                  ),
                )
              }
            >
              Inspect delivery evidence
            </button>
          ))}
          {delivery.state === 'succeeded' &&
            dashboard?.continuation_enabled &&
            dashboard.continuation_workspaces?.includes(run.resource) && (
              <ContinuationPanel
                task={delivery.id}
                busy={busy}
                perform={perform}
                refresh={refresh}
              />
            )}
        </article>
      ))}
      {evidence !== null && (
        <pre className="delivery-evidence-output">{JSON.stringify(evidence, null, 2)}</pre>
      )}
    </section>
  );
}
