import { invoke, isTauri } from '@tauri-apps/api/core';
import type { Connection, Request } from './types';

export const preview = !isTauri() && new URLSearchParams(location.search).get('preview') === '1';

export async function connection(): Promise<Connection> {
  if (preview) return { configured: true, worker_configured: true };
  if (!isTauri()) return { configured: false, worker_configured: false };
  return invoke('connection_status');
}

export async function request<T>(input: Request): Promise<T> {
  if (preview) {
    const { fixtureRequest } = await import('./fixture');
    return (await fixtureRequest(input)) as T;
  }
  if (!isTauri()) throw new Error('Open the Windows app to connect to Jarvis.');
  try {
    return await invoke<T>('core_request', { request: input });
  } catch (error) {
    const detail = error as { code?: string; request_id?: string };
    const messages: Record<string, string> = {
      disconnected: 'Jarvis core is unavailable. Check the local launcher and reconnect.',
      not_configured: 'Configure the private desktop connection file, then restart Jarvis.',
      unauthenticated:
        'The local credential was rejected. Update the private connection configuration.',
      forbidden: 'This action is outside the current permissions.',
      conflict: 'The state changed. Refresh and review the latest details.',
      invalid_input: 'Review the selected fields and try again.',
      timeout: 'The outcome is uncertain. Refresh status before taking another action.',
      worker_unavailable: 'Configure a separate project-scoped worker credential to advance runs.',
      response_too_large:
        'This result exceeds the safe display limit. Use a smaller context or a bounded artifact export.',
    };
    throw new Error(
      (messages[detail?.code || ''] ||
        'The action could not be completed. Refresh status before retrying.') +
        (detail?.request_id ? ` Reference: ${detail.request_id}` : ''),
    );
  }
}
