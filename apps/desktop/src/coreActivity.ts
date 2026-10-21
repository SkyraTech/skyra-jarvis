export type ActivitySnapshot = {
  source: 'core-state-v1';
  project: string;
  captured_at: number;
  counts: Record<string, number>;
};

export type CoreActivity = {
  state:
    | 'offline'
    | 'unknown'
    | 'idle'
    | 'review'
    | 'stopping'
    | 'testing'
    | 'coding'
    | 'planning'
    | 'thinking'
    | 'inspecting'
    | 'blocked'
    | 'paused'
    | 'queued';
  label: string;
  detail: string;
  observedAt?: number;
};

/** Presentation only: recorded work never grants tools or attests provider/OS health. */
export function resolveCoreActivity(
  online: boolean,
  project: string,
  activity?: ActivitySnapshot,
): CoreActivity {
  if (!online)
    return {
      state: 'offline',
      label: 'Core disconnected',
      detail: 'Displayed work may be stale. Reconnect to inspect current state.',
    };
  if (
    !activity ||
    activity.source !== 'core-state-v1' ||
    activity.project !== project ||
    !Number.isFinite(activity.captured_at) ||
    !activity.counts ||
    typeof activity.counts !== 'object' ||
    Array.isArray(activity.counts)
  )
    return {
      state: 'unknown',
      label: 'Core connected',
      detail: 'Project activity is unavailable from this connection.',
    };
  const count = (key: string) =>
    Number.isSafeInteger(activity.counts[key]) && activity.counts[key] > 0
      ? activity.counts[key]
      : 0;
  const pending = count('approvals') + count('reviews');
  const details = [
    pending && `${pending} review${pending === 1 ? '' : 's'}`,
    count('testing') && `${count('testing')} test execution${count('testing') === 1 ? '' : 's'}`,
    count('coding') && `${count('coding')} source operation${count('coding') === 1 ? '' : 's'}`,
    count('inspecting') &&
      `${count('inspecting')} file inspection${count('inspecting') === 1 ? '' : 's'}`,
    count('stopping') &&
      `${count('stopping')} execution${count('stopping') === 1 ? '' : 's'} stopping`,
    count('coding_requests') + count('planning_requests') + count('chat_requests') &&
      'model response pending',
    count('blocked') &&
      `${count('blocked')} item${count('blocked') === 1 ? '' : 's'} needing attention`,
    count('queued') && `${count('queued')} queued`,
    count('paused') && `${count('paused')} paused`,
  ]
    .filter(Boolean)
    .join(' · ');
  const state: CoreActivity['state'] = pending
    ? 'review'
    : count('stopping')
      ? 'stopping'
      : count('testing')
        ? 'testing'
        : count('coding')
          ? 'coding'
          : count('coding_requests')
            ? 'coding'
            : count('planning_requests')
              ? 'planning'
              : count('chat_requests')
                ? 'thinking'
                : count('inspecting')
                  ? 'inspecting'
                  : count('blocked')
                    ? 'blocked'
                    : count('paused')
                      ? 'paused'
                      : count('queued')
                        ? 'queued'
                        : 'idle';
  const labels: Record<CoreActivity['state'], string> = {
    offline: 'Core disconnected',
    unknown: 'Core connected',
    idle: 'Ready for your next task',
    review: 'Your review is needed',
    stopping: 'Stopping current execution',
    testing: 'Running protected tests',
    coding: count('coding') ? 'Applying reviewed changes' : 'Coding response pending',
    planning: 'Project plan response pending',
    thinking: 'Conversation response pending',
    inspecting: 'Inspecting approved files',
    blocked: 'Work needs attention',
    paused: 'Work paused',
    queued: 'Work queued',
  };
  return {
    state,
    label: labels[state],
    detail: details || 'No active work recorded in this project.',
    observedAt: activity.captured_at,
  };
}
