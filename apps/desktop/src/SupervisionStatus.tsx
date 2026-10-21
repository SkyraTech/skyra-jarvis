export type Supervision = {
  started_at: number;
  heartbeat_at: number;
  lease_expires_at: number | null;
  lease_valid: boolean;
  elapsed_seconds: number;
  deadline_remaining_seconds: number;
};

export default function SupervisionStatus({ value }: { value?: Supervision | null }) {
  if (!value) return null;
  return (
    <section aria-label="Dispatch supervision">
      <p>
        {value.lease_valid
          ? 'Dispatch lease active'
          : 'Dispatch lease expired · reconciliation required'}
        {' · '}
        {Math.floor(value.elapsed_seconds)} seconds elapsed at last refresh
      </p>
      <small>
        Last supervision update: {new Date(value.heartbeat_at * 1000).toLocaleString()}. Deadline
        budget remaining: {Math.floor(value.deadline_remaining_seconds)} seconds. Timing is observed
        activity, not proof of successful completion.
      </small>
    </section>
  );
}
