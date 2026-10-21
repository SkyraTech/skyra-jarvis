import { useEffect, useRef, useState } from 'react';
import { request } from './api';
import type { ProposalDetail } from './types';

const knownFailures = new Set([
  'invalid_model_response',
  'provider_output_limit',
  'provider_http_429',
  'provider_http_503',
]);

type RecoveryJob = {
  id: string;
  state: string;
  phase: string;
  proposal: string | null;
  cycle: number;
  calls: number;
  steps: number;
  deadline: number;
  summary: Record<string, unknown>;
  config: { max_calls: number; max_cycles: number; max_steps: number; auto_accept?: boolean };
};

export default function GenerationRecovery({
  job,
  disabled,
  perform,
  onQueued,
}: {
  job: RecoveryJob;
  disabled: boolean;
  perform: (operation: () => Promise<void>) => Promise<void>;
  onQueued: () => Promise<void>;
}) {
  const [review, setReview] = useState<ProposalDetail | null>(null);
  const [consent, setConsent] = useState(false);
  const live = useRef(true);
  useEffect(() => {
    live.current = true;
    return () => {
      live.current = false;
    };
  }, []);
  if (
    job.state !== 'failed' ||
    job.phase !== 'propose' ||
    !job.proposal ||
    !knownFailures.has(String(job.summary.reason)) ||
    job.calls >= job.config.max_calls ||
    job.cycle >= job.config.max_cycles ||
    job.steps >= job.config.max_steps ||
    Date.now() / 1000 >= job.deadline
  )
    return null;
  return (
    <section aria-label="Failed generation recovery">
      <button
        disabled={disabled}
        onClick={() =>
          void perform(async () => {
            setConsent(false);
            const value = await request<ProposalDetail>({ action: 'proposal', id: job.proposal! });
            if (
              value.id !== job.proposal ||
              value.state !== 'failed' ||
              !knownFailures.has(value.error || '')
            )
              throw new Error('Failed generation changed. Refresh the job.');
            if (live.current) setReview(value);
          })
        }
      >
        Review failed generation
      </button>
      {review && (
        <>
          <p>
            {review.model} · {review.error}
            {review.validation_failure ? ` · ${review.validation_failure}` : ''}
          </p>
          <p>Reported usage: {review.usage ? JSON.stringify(review.usage) : 'unavailable'}</p>
          <small>
            Failed proposal {review.id} · Context {review.context_sha256}
          </small>
          <p>
            Request one new generation within the original call, cycle and deadline limits. The
            failed attempt stays in history. Current inputs and permissions are checked again.
            {job.config.auto_accept
              ? ' This job still has automatic proposal acceptance enabled.'
              : ' The new proposal requires review.'}
          </p>
          <label className="checkbox">
            <input
              type="checkbox"
              aria-label="Allow one new model generation"
              checked={consent}
              disabled={disabled}
              onChange={(event) => setConsent(event.target.checked)}
            />
            I approve another model call using this job’s remaining budget.
          </label>
          <button
            disabled={disabled || !consent}
            onClick={() =>
              void perform(async () => {
                setConsent(false);
                await request({
                  action: 'retry_build_generation',
                  id: job.id,
                  body: {
                    proposal: review.id,
                    context_sha256: review.context_sha256,
                    allow_model_call: true,
                  },
                });
                if (live.current) setReview(null);
                await onQueued();
              })
            }
          >
            Queue reviewed generation retry
          </button>
        </>
      )}
    </section>
  );
}
