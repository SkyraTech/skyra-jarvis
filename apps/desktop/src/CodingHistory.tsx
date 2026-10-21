import { useEffect, useRef, useState } from 'react';
import { request } from './api';

type Job = {
  id: string;
  goal: string;
  resource: string;
  state: string;
  phase: string;
  mode: string;
  calls: number;
  steps: number;
  cycles: {
    cycle: number;
    state: string;
    baseline_task: string | null;
    context_task?: string | null;
    proposal: string | null;
    run: string | null;
    model: string | null;
  }[];
  deliveries: {
    id: string;
    resource: string;
    state: string;
    evidence: string[];
    evidence_limited: boolean;
  }[];
  generations: { name: string; workspace: string; previous_workspace: string }[];
  details_limited: boolean;
};
type Page = { conversation: string; jobs: Job[]; next_before: number | null };

export default function CodingHistory({ conversation }: { conversation: string }) {
  const [jobs, setJobs] = useState<Job[] | null>(null);
  const [before, setBefore] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const gate = useRef(false),
    live = useRef(true);
  useEffect(() => {
    live.current = true;
    return () => {
      live.current = false;
    };
  }, []);
  async function load(older = false) {
    if (gate.current || (older && before === null)) return;
    gate.current = true;
    setBusy(true);
    setError('');
    try {
      const page = await request<Page>({
        action: 'coding_history',
        id: conversation,
        after: older ? before! : 0,
      });
      if (!live.current || page.conversation !== conversation) return;
      setJobs((old) =>
        older
          ? [
              ...(old || []),
              ...page.jobs.filter((item) => !old?.some((existing) => existing.id === item.id)),
            ]
          : page.jobs,
      );
      setBefore(page.next_before);
    } catch {
      if (live.current) setError('Unable to load linked coding history. Refresh to retry.');
    } finally {
      gate.current = false;
      if (live.current) setBusy(false);
    }
  }
  return (
    <section className="coding-history" aria-label="Linked coding history">
      <h3>Coding work linked to this conversation</h3>
      <p>
        Inspect recorded jobs, test cycles, source deliveries and subsequent generations. Loading
        history does not run work or send it to a model.
      </p>
      <button disabled={busy} onClick={() => void load()}>
        {jobs === null ? 'Load coding history' : 'Refresh coding history'}
      </button>
      {error && <p role="alert">{error}</p>}
      {jobs?.length === 0 && <p>No coding jobs are linked to this conversation.</p>}
      {jobs?.map((job) => (
        <details key={job.id}>
          <summary>
            {job.goal} · {job.state} · {job.resource}
          </summary>
          <p>
            {job.mode} · {job.phase} · {job.calls} reserved calls · {job.steps} steps
          </p>
          <small>Job {job.id}</small>
          <ul>
            {job.cycles.map((cycle) => (
              <li key={cycle.cycle}>
                Cycle {cycle.cycle}: {cycle.state}. Model: {cycle.model || 'No proposal generated'}.
                Baseline task: {cycle.baseline_task || 'Not dispatched'}. Proposal:{' '}
                {cycle.proposal || 'None'}. Run: {cycle.run || 'None'}.
                {cycle.context_task && <> Retrieval read task: {cycle.context_task}.</>}
              </li>
            ))}
            {job.deliveries.map((delivery) => (
              <li key={delivery.id}>
                Delivery {delivery.id} to {delivery.resource}: {delivery.state}. Evidence:{' '}
                {delivery.evidence.join(', ') || 'None'}
                {delivery.evidence_limited
                  ? ' (more references available in delivery details)'
                  : ''}
                .
              </li>
            ))}
            {job.generations.map((generation) => (
              <li key={generation.name}>
                Generation {generation.name}: {generation.previous_workspace} →{' '}
                {generation.workspace}. Registration does not confirm current grants.
              </li>
            ))}
          </ul>
          {job.details_limited && (
            <p>
              Only the latest ten deliveries and generations are listed. Inspect the coding run and
              project library for further records.
            </p>
          )}
        </details>
      ))}
      {before !== null && (
        <button disabled={busy} onClick={() => void load(true)}>
          Load older coding jobs
        </button>
      )}
    </section>
  );
}
