import { useEffect, useState } from 'react';
import { request } from './api';
import type { Connection, Dashboard, Setup } from './types';

export default function SetupPanel({
  host,
  online,
  dashboard,
}: {
  host: Connection;
  online: boolean;
  dashboard: Dashboard | null;
}) {
  const [setup, setSetup] = useState<Setup | null>(null),
    [error, setError] = useState('');
  useEffect(() => {
    let live = true;
    if (online)
      request<Setup>({ action: 'setup' })
        .then((data) => {
          if (live) setSetup(data);
        })
        .catch(() => {
          if (live) setError('Could not read current setup. Reconnect and reopen Setup.');
        });
    return () => {
      live = false;
    };
  }, [online]);
  const rows = [
    {
      title: '1. Private Windows connection',
      ready: host.configured && online,
      detail:
        'Start Jarvis with the hidden launcher. Controller credentials remain DPAPI protected in your Windows profile.',
    },
    {
      title: '2. Project',
      ready: !!dashboard,
      detail:
        'Create or choose a project. New projects default to read only; each has separate conversations and permissions.',
    },
    {
      title: '3. Online model',
      ready: !!setup?.conversation.providers.length,
      detail:
        'Register Gemini or Groq in the trusted runtime configuration. Use an environment variable for its API key. Chat and planning do not require a coding worker.',
    },
    {
      title: '4. Coding workspace',
      ready: !!dashboard?.workspaces.length,
      detail:
        'Register an explicit selected-file snapshot in the workspace configuration, then grant its logical resource through project permissions. Your original source remains separate.',
    },
    {
      title: '5. Approved execution',
      ready:
        !!setup?.worker.execution_available &&
        host.worker_configured &&
        !!dashboard?.workspaces.length,
      detail:
        'Add an owner-enabled native test profile and separate project-scoped worker credential. Native tests run with your Windows account access. Review each exact action in Ask mode.',
    },
  ];
  return (
    <section className="card setup-panel">
      <h2>Set up your workspace</h2>
      <p>
        This checklist reads current configuration. It does not change permissions, install software
        or make model calls.
      </p>
      {error && <p role="alert">{error}</p>}
      {rows.map((row) => (
        <article className="setup-step" key={row.title}>
          <div className="panel-heading">
            <h3>{row.title}</h3>
            <span className={`pill ${row.ready ? 'good' : 'warn'}`}>
              {row.ready ? 'Ready' : 'Needs setup'}
            </span>
          </div>
          <p>{row.detail}</p>
        </article>
      ))}
      <h3>Configured online models</h3>
      {setup?.conversation.providers.length ? (
        <ul>
          {setup.conversation.providers.map((p) => (
            <li key={p.name}>
              {p.name} · {p.model}
            </li>
          ))}
        </ul>
      ) : (
        <p>No online models are registered.</p>
      )}
      <h3>Configuration workflow</h3>
      <p>
        Use the existing desktop README to provision a new private state directory. In that
        directory, launcher.json references runtime.json and optional workspaces.json; desktop.json
        contains protected connection credentials. Provider keys belong in the launcher environment,
        never in chat or project files. Restart Jarvis after trusted configuration changes.
      </p>
      <p>
        Chat can answer questions and create structured draft plans. It cannot execute tools, create
        project files, publish content or start a build. Plan execution and a full configuration
        editor remain upcoming work.
      </p>
    </section>
  );
}
