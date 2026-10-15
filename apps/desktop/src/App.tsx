import { useCallback, useId, useEffect, useMemo, useRef, useState } from 'react';
import {
  Background,
  Controls,
  Handle,
  MiniMap,
  Position,
  ReactFlow,
  useNodesState,
  type Node,
  type NodeProps,
  type Edge,
} from '@xyflow/react';
import { connection, preview, request } from './api';
import PolicyDialog from './PolicyDialog';
import ConversationPanel from './ConversationPanel';
import SetupPanel from './SetupPanel';
import JarvisCore from './JarvisCore';
import type { Approval, Connection, Dashboard, Project, ProposalDetail, Run } from './types';

export type View =
  | 'Overview'
  | 'Repair proposals'
  | 'Coding runs'
  | 'Approvals'
  | 'Conversations'
  | 'Activity'
  | 'Setup'
  | 'System map'
  | 'Jarvis core';
type System = {
  name: string;
  category: string;
  icon: string;
  description: string;
  state: string;
  capabilities: string[];
};
const planned: System[] = [
  {
    name: 'Google Workspace',
    category: 'PRODUCTIVITY',
    icon: 'G',
    state: 'Planned',
    description: 'Reusable Google service integration is not connected to this core.',
    capabilities: ['Documents & spreadsheets', 'Calendar & invitations', 'Drive operations'],
  },
  {
    name: 'Messaging',
    category: 'CONNECTIONS',
    icon: '↗',
    state: 'Planned',
    description: 'WhatsApp and messaging workflows need a registered service connection.',
    capabilities: ['WhatsApp workflows', 'Delivery evidence', 'Account-scoped approvals'],
  },
  {
    name: 'Social studio',
    category: 'PUBLISHING',
    icon: '◎',
    state: 'Planned',
    description: 'Social accounts and scheduled publishing are not connected.',
    capabilities: ['Instagram connections', 'Scheduled publishing', 'Publication approvals'],
  },
  {
    name: 'Media studio',
    category: 'CREATION',
    icon: '◈',
    state: 'Planned',
    description: 'Image and video agent integration remains future work.',
    capabilities: ['Image generation', 'Video generation', 'Asset review'],
  },
  {
    name: 'Quality & incidents',
    category: 'ASSURANCE',
    icon: '⌁',
    state: 'Planned',
    description: 'Product monitoring, vulnerability checks and incident triage are not connected.',
    capabilities: ['Coverage & security', 'Product alerts', 'Incident investigation'],
  },
  {
    name: 'Browser & vision',
    category: 'AUTOMATION',
    icon: '▣',
    state: 'Planned',
    description: 'Screen actions and browser automation need explicit adapters and grants.',
    capabilities: ['Browser tasks', 'Screen inspection', 'Permission-bound actions'],
  },
];
function Pill({ state }: { state: string }) {
  return (
    <span
      className={`pill ${/ready|accepted|connected|available/i.test(state) ? 'good' : /failed|error|interrupted/i.test(state) ? 'bad' : /approval|planned|configured/i.test(state) ? 'warn' : ''}`}
    >
      {state.replaceAll('_', ' ')}
    </span>
  );
}
function SystemNode({ data }: NodeProps<Node<System>>) {
  return (
    <div className={`system-node ${data.state === 'Planned' ? 'planned' : ''}`}>
      <Handle type="target" position={Position.Left} />
      <div className="node-top">
        <span className="node-icon">{data.icon}</span>
        <span className="node-category">{data.category}</span>
      </div>
      <strong>{data.name}</strong>
      <div className="node-footer">
        <Pill state={data.state} />
        <span>↗</span>
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
const nodeTypes = { system: SystemNode };
export const views: { name: View; icon: string }[] = [
  { name: 'Overview', icon: '⌘' },
  { name: 'Jarvis core', icon: '◉' },
  { name: 'System map', icon: '⌁' },
  { name: 'Repair proposals', icon: '◇' },
  { name: 'Coding runs', icon: '⌁' },
  { name: 'Approvals', icon: '✓' },
  { name: 'Conversations', icon: '◌' },
  { name: 'Activity', icon: '≋' },
  { name: 'Setup', icon: '⚙' },
];

export default function App({
  view,
  setView,
  initialProject = '',
  active = true,
  onProjectChange,
  onPopout,
}: {
  view: View;
  setView: (view: View) => void;
  initialProject?: string;
  active?: boolean;
  onProjectChange: (project: string) => void;
  onPopout: (view: View, project: string) => void;
}) {
  const projectControl = useId();
  const [host, setHost] = useState<Connection>({ configured: false, worker_configured: false });
  const [online, setOnline] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]),
    [project, setProject] = useState(initialProject);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [taskBusy, setBusy] = useState(false),
    [error, setError] = useState(''),
    [notice, setNotice] = useState('');
  const [selectedSystem, setSelectedSystem] = useState<System | null>(null);
  const [editingPolicy, setEditingPolicy] = useState(false);
  const [proposal, setProposal] = useState<ProposalDetail | null>(null),
    [run, setRun] = useState<Run | null>(null);
  const [approval, setApproval] = useState<{
    approval: { id: string; expires: number; version: number; state: string };
    task: { action: string; resource: string; payload: string };
  } | null>(null);
  const [evidence, setEvidence] = useState<unknown>(null),
    [create, setCreate] = useState<'project' | 'proposal' | null>(null);
  const activeProject = useRef(initialProject);
  const projectChanged = useRef(onProjectChange);
  projectChanged.current = onProjectChange;
  useEffect(() => {
    projectChanged.current(project);
  }, [project]);
  useEffect(() => {
    if (!active) {
      setCreate(null);
      setEditingPolicy(false);
    }
  }, [active]);
  const inFlight = useRef(false);
  const controlInFlight = useRef(false);
  const [controlBusy, setControlBusy] = useState(false);
  const busy = taskBusy || controlBusy;

  const refresh = useCallback(async (id: string) => {
    const data = await request<Dashboard>({ action: 'dashboard', project: id });
    if (activeProject.current === id) {
      setDashboard(data);
      setOnline(true);
    }
  }, []);
  const load = useCallback(async () => {
    const status = await connection();
    setHost(status);
    if (!status.configured) {
      setOnline(false);
      setNotice(
        'Set up the private Windows connection to begin. The canvas shows planned capabilities until connected.',
      );
      return;
    }
    let data: { projects: Project[] };
    try {
      data = await request({ action: 'projects' });
      setOnline(true);
    } catch (error) {
      setOnline(false);
      throw error;
    }
    setProjects(data.projects);
    if (activeProject.current && !data.projects.some((p) => p.id === activeProject.current)) {
      activeProject.current = '';
      setProject('');
    }
    if (!activeProject.current && data.projects.length) {
      activeProject.current = data.projects[0].id;
      setProject(data.projects[0].id);
    }
    if (activeProject.current) await refresh(activeProject.current);
    setNotice(
      data.projects.length ? '' : 'Create a project to begin. New projects default to read only.',
    );
  }, [refresh]);

  async function perform(operation: () => Promise<void>, control = false) {
    const gate = control ? controlInFlight : inFlight;
    if (gate.current || (!control && controlInFlight.current)) return;
    gate.current = true;
    (control ? setControlBusy : setBusy)(true);
    setError('');
    setNotice('');
    try {
      await operation();
    } catch (e) {
      setError(
        e instanceof Error ? e.message : 'Unable to complete the action. Refresh before retrying.',
      );
    } finally {
      gate.current = false;
      (control ? setControlBusy : setBusy)(false);
    }
  }
  useEffect(() => {
    void perform(load);
  }, [load]);
  useEffect(() => {
    if (!project || !active) return;
    const timer = window.setInterval(() => {
      if (inFlight.current || document.hidden) return;
      void refresh(project).catch(() => {
        setOnline(false);
        setError('Connection lost. Displayed information may be stale; reconnect before acting.');
      });
    }, 10000);
    return () => clearInterval(timer);
  }, [project, refresh, active]);
  useEffect(() => {
    setProposal(null);
    setRun(null);
    setApproval(null);
    setEvidence(null);
  }, [project]);

  const systems: System[] = [
    {
      name: 'Jarvis core',
      category: 'ORCHESTRATION',
      icon: 'J',
      state: online ? 'Connected' : 'Disconnected',
      description: 'Durable projects, conversations, permissions and execution checkpoints.',
      capabilities: ['SQLite-backed history', 'Exact-action approvals', 'Durable repair runs'],
    },
    {
      name: 'Coding agent',
      category: 'DEVELOPMENT',
      icon: '</>',
      state: dashboard?.worker.execution_available ? 'Available' : 'Unavailable',
      description:
        'Selected-file repairs through protected baseline tests, patches, retest and diff.',
      capabilities: ['Native trusted execution', 'Protected test profiles', 'Checksummed evidence'],
    },
    {
      name: 'Model runtime',
      category: 'INTELLIGENCE',
      icon: '✳',
      state: dashboard?.runtime.providers.length ? 'Configured' : 'Unavailable',
      description:
        'Configured online models propose patches from explicit context. Configured does not mean provider health has been checked.',
      capabilities: dashboard?.runtime.providers.map((p) => `${p.name} · ${p.model}`) || [
        'No provider configured',
      ],
    },
    ...planned,
  ];
  const graphNodes = useMemo<Node<System>[]>(
    () =>
      systems.map((data, index) => ({
        id: String(index),
        type: 'system',
        data,
        position:
          index === 0
            ? { x: 40, y: 220 }
            : { x: 350 + (index > 4 ? 310 : 0), y: ((index - 1) % 4) * 168 - 15 },
      })),
    [dashboard, online],
  );
  const [nodes, setNodes, onNodesChange] = useNodesState<Node<System>>(graphNodes);
  useEffect(() => {
    // Retain measured dimensions and selection when readiness data is refreshed.
    setNodes((current) =>
      graphNodes.map((node) => ({
        ...current.find((previous) => previous.id === node.id),
        ...node,
      })),
    );
  }, [graphNodes, setNodes]);
  const edges: Edge[] = dashboard
    ? [
        { id: 'core-worker', source: '0', target: '1', label: 'tasks & evidence', animated: false },
        ...(dashboard.runtime.providers.length
          ? [
              {
                id: 'core-model',
                source: '0',
                target: '2',
                label: 'reviewed proposals',
                animated: false,
              },
            ]
          : []),
      ]
    : [];

  return (
    <div className="shell">
      <aside className="rail" aria-label="Company">
        <div className="brand-mark">
          S<span>✳</span>
        </div>
        <button className="rail-active" aria-label="Jarvis workspace">
          J
        </button>
        <div className="rail-bottom">ST</div>
      </aside>
      <aside className="sidebar">
        <div className="wordmark">
          JARVIS<span>by Skyra Tech</span>
        </div>
        <div className="workspace-label">WORKSPACE</div>
        <label className="sr-only" htmlFor={projectControl}>
          Project
        </label>
        <select
          id={projectControl}
          value={project}
          disabled={busy || !projects.length}
          onChange={(e) => {
            const id = e.target.value;
            activeProject.current = id;
            setProject(id);
            setDashboard(null);
            void perform(() => refresh(id));
          }}
        >
          <option value="" disabled>
            Select project
          </option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        <button
          className="subtle new-project"
          disabled={busy || !host.configured}
          onClick={() => setCreate('project')}
        >
          ＋ New project
        </button>
        <nav aria-label="Main navigation">
          {views.map((v) => (
            <button
              key={v.name}
              className={view === v.name ? 'nav-active' : ''}
              onClick={() => {
                setView(v.name);
                setProposal(null);
                setRun(null);
                setApproval(null);
                setEvidence(null);
              }}
            >
              <span>{v.icon}</span>
              {v.name}
              {v.name === 'Approvals' && !!dashboard?.approvals.length && (
                <b>{dashboard.approvals.length}</b>
              )}
            </button>
          ))}
        </nav>
        <div className="sidebar-note">
          <span className="tiny-dot" /> HUMAN IN CONTROL
          <p>
            Models propose.
            <br />
            Permissions decide.
          </p>
        </div>
        <div className="profile">
          <span>ST</span>
          <div>
            Skyra Tech<small>Internal workspace</small>
          </div>
        </div>
      </aside>
      <div className="main">
        <header className="topbar">
          <span>
            Workspace <i>/</i> <strong>{view}</strong>
          </span>
          <div>
            <span className="connection">
              <span className={`tiny-dot ${online ? '' : 'offline'}`} />
              {online ? 'Local core connected' : 'Disconnected'}
            </span>
            <button
              onClick={() => onPopout(view, project)}
              aria-label="Open current panel in new window"
            >
              ↗ New window
            </button>
            <button disabled={busy} onClick={() => void perform(load)}>
              {busy ? 'Working…' : '↻ Reconnect'}
            </button>
          </div>
        </header>
        {preview && (
          <div className="preview-banner">
            VISUAL PREVIEW · Sample data only. Actions are simulated; no core, models or services
            are contacted.
          </div>
        )}
        {error && (
          <div className="alert error" role="alert">
            {error}
            <button onClick={() => setError('')} aria-label="Dismiss error">
              ×
            </button>
          </div>
        )}
        {notice && (
          <div className="alert" role="status">
            {notice}
          </div>
        )}
        <section className="page-heading">
          <div>
            <div className="eyebrow">YOUR OPERATING LAYER</div>
            <h1>{view === 'Overview' ? 'One workspace. Every capability.' : view}</h1>
            <p>
              {view === 'Overview'
                ? 'See what Jarvis can do, what is connected, and what needs your attention.'
                : 'Review durable project state and take explicit, permission-bound actions.'}
            </p>
          </div>
          <button
            className="header-tag"
            aria-label="Edit project permissions"
            disabled={busy || !dashboard}
            onClick={() => setEditingPolicy(true)}
          >
            ◇ <span>{dashboard?.project.mode.replaceAll('_', ' ') || 'No active policy'}</span>
          </button>
        </section>
        {view === 'Jarvis core' && (
          <div className="core-only">
            <JarvisCore
              online={online}
              project={dashboard?.project.name}
              onOpen={(panel) => onPopout(panel, project)}
            />
          </div>
        )}
        {(view === 'Overview' || view === 'System map') && (
          <>
            {view === 'Overview' && (
              <>
                <JarvisCore
                  online={online}
                  project={dashboard?.project.name}
                  onOpen={(panel) => onPopout(panel, project)}
                />
                <section className="stats">
                  <div>
                    <span>Connected core</span>
                    <button
                      className="stat-popout"
                      aria-label="Open core card in new window"
                      onClick={() => onPopout('Jarvis core', project)}
                    >
                      ↗
                    </button>
                    <strong>
                      {online ? '01' : '00'}
                      <small> / local</small>
                    </strong>
                  </div>
                  <div>
                    <span>Configured models</span>
                    <button
                      className="stat-popout"
                      aria-label="Open models card in new window"
                      onClick={() => onPopout('Setup', project)}
                    >
                      ↗
                    </button>
                    <strong>
                      {String(dashboard?.runtime.providers.length || 0).padStart(2, '0')}
                      <small> providers</small>
                    </strong>
                  </div>
                  <div>
                    <span>Needs approval</span>
                    <button
                      className="stat-popout"
                      aria-label="Open approvals card in new window"
                      onClick={() => onPopout('Approvals', project)}
                    >
                      ↗
                    </button>
                    <strong>
                      {String(dashboard?.approvals.filter((a) => a.decidable).length || 0).padStart(
                        2,
                        '0',
                      )}
                      <small> requests</small>
                    </strong>
                  </div>
                  <div>
                    <span>Coding runs</span>
                    <button
                      className="stat-popout"
                      aria-label="Open coding card in new window"
                      onClick={() => onPopout('Coding runs', project)}
                    >
                      ↗
                    </button>
                    <strong>
                      {String(dashboard?.runs.length || 0).padStart(2, '0')}
                      <small> recent</small>
                    </strong>
                  </div>
                </section>
              </>
            )}
            <div className="canvas-layout">
              <section className="canvas-panel" aria-label="Subsystem workflow canvas">
                <div className="panel-heading">
                  <div>
                    <strong>System map</strong>
                    <span>Capabilities & connections</span>
                  </div>
                  <button
                    className="subtle"
                    aria-label="Open system map in new window"
                    onClick={() => onPopout('System map', project)}
                  >
                    ↗ New window
                  </button>
                  <span className="live-label">
                    ◉ {online ? 'LIVE LOCAL STATE' : 'NOT CONNECTED'}
                  </span>
                </div>
                <div className="canvas">
                  <ReactFlow
                    nodes={nodes}
                    onNodesChange={onNodesChange}
                    edges={edges}
                    nodeTypes={nodeTypes}
                    fitView
                    minZoom={0.25}
                    maxZoom={1.5}
                    nodesConnectable={false}
                    nodesDraggable={false}
                    onNodeClick={(_, n) => setSelectedSystem(n.data)}
                    colorMode="dark"
                    proOptions={{ hideAttribution: false }}
                  >
                    <Background gap={24} size={1} color="#28334b" />
                    <Controls showInteractive={false} />
                    <MiniMap pannable zoomable nodeColor="#26344c" maskColor="#0b1220aa" />
                  </ReactFlow>
                </div>
                <div className="canvas-foot">
                  <span>
                    <i className="legend-dot" />
                    Connected / configured
                  </span>
                  <span>
                    <i className="legend-dot planned-dot" />
                    Planned capability
                  </span>
                  <span>Edges show implemented integration</span>
                </div>
              </section>
              <aside className="inspector">
                <div className="panel-heading">
                  <strong>{selectedSystem ? 'Subsystem details' : 'Workspace focus'}</strong>
                  <span>↗</span>
                </div>
                {selectedSystem ? (
                  <>
                    <div className="inspector-icon">{selectedSystem.icon}</div>
                    <h2>{selectedSystem.name}</h2>
                    <Pill state={selectedSystem.state} />
                    <p>{selectedSystem.description}</p>
                    <div className="eyebrow">CAPABILITIES</div>
                    <ul className="capabilities">
                      {selectedSystem.capabilities.map((c) => (
                        <li key={c}>{c}</li>
                      ))}
                    </ul>
                    <button className="wide" onClick={() => setSelectedSystem(null)}>
                      Back to workspace
                    </button>
                  </>
                ) : (
                  <>
                    <div className="focus-symbol">✳</div>
                    <h2>Built around your control.</h2>
                    <p>
                      Start with a scoped repair. Review the proposal, approve the exact action,
                      then inspect the evidence.
                    </p>
                    <button
                      className="primary wide"
                      disabled={!dashboard}
                      onClick={() => setView('Repair proposals')}
                    >
                      Open repair proposals <span>↗</span>
                    </button>
                    <div className="attention">
                      <span>REQUIRES ATTENTION</span>
                      <strong>
                        {dashboard?.approvals.filter((a) => a.decidable).length || 0} pending
                        approvals
                      </strong>
                      <button className="subtle" onClick={() => setView('Approvals')}>
                        Review requests →
                      </button>
                    </div>
                    <div className="safety-note">
                      Native execution uses your Windows account’s access. Test success means ready
                      for review.
                    </div>
                  </>
                )}
              </aside>
            </div>
            <section className="system-list">
              <h2>All subsystems</h2>
              <div>
                {systems.map((s) => (
                  <button key={s.name} onClick={() => setSelectedSystem(s)}>
                    <span>{s.icon}</span>
                    {s.name}
                    <Pill state={s.state} />
                  </button>
                ))}
              </div>
            </section>
          </>
        )}

        {view === 'Repair proposals' && (
          <section className="content-grid">
            <div className="card">
              <div className="panel-heading">
                <strong>Recent proposals</strong>
                <button
                  className="primary"
                  disabled={
                    busy || !dashboard?.workspaces.length || !dashboard.runtime.providers.length
                  }
                  onClick={() => setCreate('proposal')}
                >
                  ＋ New proposal
                </button>
              </div>
              {!dashboard?.proposals.length && (
                <Empty text="No repair proposals yet. Register a selected-file workspace and provider to begin." />
              )}
              {dashboard?.proposals.map((p) => (
                <button
                  className="item"
                  key={p.id}
                  onClick={() =>
                    void perform(async () =>
                      setProposal(await request({ action: 'proposal', id: p.id })),
                    )
                  }
                >
                  <div>
                    <strong>{p.resource}</strong>
                    <small>{p.model}</small>
                  </div>
                  <Pill state={p.state} />
                </button>
              ))}
            </div>
            <div className="card detail">
              {proposal ? (
                <>
                  <div className="panel-heading">
                    <strong>Proposal review</strong>
                    <Pill state={proposal.state} />
                  </div>
                  <h2>{proposal.response?.summary || 'Context prepared for generation'}</h2>
                  <p>{proposal.context.goal}</p>
                  <dl>
                    <dt>Provider / model</dt>
                    <dd>
                      {proposal.provider} / {proposal.model}
                    </dd>
                    <dt>Context checksum</dt>
                    <dd className="hash">{proposal.context_sha256}</dd>
                    <dt>Usage</dt>
                    <dd>{proposal.usage ? JSON.stringify(proposal.usage) : 'Not reported'}</dd>
                  </dl>
                  <h3>Selected context</h3>
                  {proposal.context.files.map((f) => (
                    <div className="file" key={f.path}>
                      <span>{f.path}</span>
                      <Pill
                        state={
                          f.protected
                            ? 'Protected test'
                            : f.sha256 === 'absent'
                              ? 'New file target'
                              : 'Selected source'
                        }
                      />
                    </div>
                  ))}
                  {proposal.context.skills.map((s) => (
                    <p className="muted" key={s.name}>
                      Skill: {s.name} · {s.version}
                    </p>
                  ))}
                  {proposal.response?.patches.map((p) => (
                    <div className="patch" key={p.path}>
                      <strong>{p.path}</strong>
                      <pre className="removed">
                        {p.expected_sha256 === 'absent'
                          ? 'New file (must not exist)'
                          : '− ' + p.old}
                      </pre>
                      <pre className="added">＋ {p.new}</pre>
                    </div>
                  ))}
                  {proposal.error && <p className="error-text">{proposal.error}</p>}
                  <div className="actions">
                    {proposal.state === 'planned' && (
                      <button
                        className="primary"
                        disabled={busy}
                        onClick={() =>
                          void perform(async () => {
                            setProposal(await request({ action: 'generate', id: proposal.id }));
                            await refresh(project);
                          })
                        }
                      >
                        Generate with online model
                      </button>
                    )}
                    {proposal.state === 'ready' && (
                      <button
                        className="primary"
                        disabled={busy}
                        onClick={() =>
                          void perform(async () => {
                            setProposal(await request({ action: 'accept', id: proposal.id }));
                            await refresh(project);
                            setNotice(
                              'Proposal accepted. The coding run still follows the current task approval policy.',
                            );
                          })
                        }
                      >
                        Accept into coding run
                      </button>
                    )}
                    {['planned', 'generating', 'ready'].includes(proposal.state) && (
                      <button
                        disabled={controlBusy}
                        onClick={() =>
                          void perform(async () => {
                            setProposal(await request({ action: 'interrupt', id: proposal.id }));
                            await refresh(project);
                            setNotice(
                              'Interruption recorded. A provider request may still complete and incur cost.',
                            );
                          }, true)
                        }
                      >
                        Interrupt proposal
                      </button>
                    )}
                    <button
                      disabled={busy}
                      onClick={() =>
                        void perform(async () =>
                          setProposal(await request({ action: 'proposal', id: proposal.id })),
                        )
                      }
                    >
                      Refresh status
                    </button>
                  </div>
                  <p className="safety-note">
                    Generation sends the selected context to the configured provider and may incur
                    cost. Interruption cannot reverse an online request or its cost. Review selected
                    files for embedded secrets.
                  </p>
                </>
              ) : (
                <Empty text="Choose a proposal to inspect context, patches, skills and usage." />
              )}
            </div>
          </section>
        )}

        {view === 'Coding runs' && (
          <section className="content-grid">
            <div className="card">
              <div className="panel-heading">
                <strong>Recent coding runs</strong>
                <span>{dashboard?.runs.length || 0}</span>
              </div>
              {!dashboard?.runs.length && <Empty text="Accepted repair plans will appear here." />}
              {dashboard?.runs.map((r) => (
                <button
                  className="item"
                  key={r.id}
                  onClick={() =>
                    void perform(async () => {
                      setRun(await request({ action: 'run', id: r.id }));
                      setEvidence(null);
                    })
                  }
                >
                  <div>
                    <strong>{r.resource}</strong>
                    <small>
                      Step {r.position} · {r.id.slice(0, 8)}
                    </small>
                  </div>
                  <Pill state={r.state} />
                </button>
              ))}
            </div>
            <div className="card detail">
              {run ? (
                <>
                  <div className="panel-heading">
                    <strong>Execution checkpoint</strong>
                    <Pill state={run.state} />
                  </div>
                  <h2>{run.resource}</h2>
                  <ol className="steps">
                    {run.steps?.map((step, i) => (
                      <li key={i}>
                        <span className={i < run.position ? 'step-done' : ''}>{i + 1}</span>
                        <div>
                          <strong>
                            {step.action} · {String(step.payload.operation)}
                          </strong>
                          <small>Expected: {step.expect}</small>
                        </div>
                        <Pill
                          state={
                            run.results?.[i]?.state || (i === run.position ? run.state : 'queued')
                          }
                        />
                      </li>
                    ))}
                  </ol>
                  <div className="actions">
                    <button
                      className="primary"
                      disabled={
                        busy ||
                        !host.worker_configured ||
                        !dashboard?.worker.execution_available ||
                        [
                          'failed',
                          'ready_for_review',
                          'cancelled',
                          'running',
                          'cancellation_requested',
                        ].includes(run.state)
                      }
                      onClick={() =>
                        void perform(async () => {
                          setRun(await request({ action: 'advance', id: run.id }));
                          await refresh(project);
                        })
                      }
                    >
                      Advance one step
                    </button>
                    <button
                      disabled={
                        controlBusy ||
                        ['failed', 'ready_for_review', 'cancelled'].includes(run.state)
                      }
                      onClick={() =>
                        void perform(async () => {
                          setRun(await request({ action: 'cancel_run', id: run.id }));
                          await refresh(project);
                          setNotice(
                            'Cancellation recorded. Inspect the run state and evidence before assuming cleanup.',
                          );
                        }, true)
                      }
                    >
                      Cancel run
                    </button>
                    <button
                      disabled={busy}
                      onClick={() =>
                        void perform(async () =>
                          setRun(await request({ action: 'run', id: run.id })),
                        )
                      }
                    >
                      Refresh status
                    </button>
                  </div>
                  {!host.worker_configured && (
                    <p className="safety-note">
                      A separate scoped worker credential is required to advance runs.
                    </p>
                  )}
                  <h3>Verification evidence</h3>
                  {run.results?.flatMap((r) =>
                    r.evidence.map((ref) => (
                      <button
                        className="evidence"
                        key={ref}
                        onClick={() =>
                          void perform(async () =>
                            setEvidence(
                              await request({
                                action: 'evidence',
                                id: r.task_id,
                                checksum: ref.slice(7),
                              }),
                            ),
                          )
                        }
                      >
                        {r.state} · {ref.slice(0, 22)}… ↗
                      </button>
                    )),
                  )}
                  {evidence !== null && (
                    <pre className="evidence-output">{JSON.stringify(evidence, null, 2)}</pre>
                  )}
                  <p className="safety-note">
                    Advance dispatches a single task through the worker credential. Approval pauses
                    and uncertain effects remain in the core. Cancellation requested is not
                    confirmed cleanup.
                  </p>
                </>
              ) : (
                <Empty text="Select a run to inspect its checkpoints and task-bound evidence." />
              )}
            </div>
          </section>
        )}

        {view === 'Approvals' && (
          <section className="content-grid">
            <div className="card">
              <div className="panel-heading">
                <strong>Approval inbox</strong>
                <span>Latest 100</span>
              </div>
              {!dashboard?.approvals.length && <Empty text="No pending approval requests." />}
              {dashboard?.approvals.map((a: Approval) => (
                <button
                  className="item"
                  key={a.id}
                  onClick={() =>
                    void perform(async () =>
                      setApproval(await request({ action: 'approval', id: a.id })),
                    )
                  }
                >
                  <div>
                    <strong>
                      {a.action} · {a.resource}
                    </strong>
                    <small>
                      {a.decidable
                        ? 'Review exact action before approval'
                        : 'Expired or invalidated; worker must request again'}
                    </small>
                  </div>
                  <Pill state={a.decidable ? 'Needs approval' : 'Stale'} />
                </button>
              ))}
            </div>
            <div className="card detail">
              {approval ? (
                <>
                  <div className="panel-heading">
                    <strong>Exact-action review</strong>
                    <Pill state={approval.approval.state} />
                  </div>
                  <h2>{approval.task.action}</h2>
                  <p>{approval.task.resource}</p>
                  <dl>
                    <dt>Policy version</dt>
                    <dd>{approval.approval.version}</dd>
                    <dt>Expires</dt>
                    <dd>{new Date(approval.approval.expires * 1000).toLocaleString()}</dd>
                  </dl>
                  <pre>{JSON.stringify(JSON.parse(approval.task.payload), null, 2)}</pre>
                  <div className="actions">
                    <button
                      disabled={
                        busy ||
                        !dashboard?.approvals.find((a) => a.id === approval.approval.id)?.decidable
                      }
                      onClick={() =>
                        void perform(async () => {
                          await request({
                            action: 'decide',
                            id: approval.approval.id,
                            body: { approve: false },
                          });
                          setApproval(null);
                          await refresh(project);
                        })
                      }
                    >
                      Reject
                    </button>
                    <button
                      className="primary"
                      disabled={
                        busy ||
                        !dashboard?.approvals.find((a) => a.id === approval.approval.id)?.decidable
                      }
                      onClick={() =>
                        void perform(async () => {
                          await request({
                            action: 'decide',
                            id: approval.approval.id,
                            body: { approve: true },
                          });
                          setApproval(null);
                          await refresh(project);
                          setNotice('Decision saved. Advance the coding run to continue.');
                        })
                      }
                    >
                      Approve exact action
                    </button>
                  </div>
                  <p className="safety-note">
                    The core rechecks expiry, task digest and policy version when deciding and
                    consuming this approval. Approval does not widen project access.
                  </p>
                </>
              ) : (
                <Empty text="Select a request to inspect its action, target, payload and expiry." />
              )}
            </div>
          </section>
        )}

        {view === 'Conversations' && (
          <ConversationPanel
            key={project}
            project={project}
            dashboard={dashboard}
            refresh={refresh}
          />
        )}
        {view === 'Setup' && <SetupPanel host={host} online={online} dashboard={dashboard} />}

        {view === 'Activity' && (
          <section className="card activity">
            <div className="panel-heading">
              <strong>Recent core events</strong>
              <span>Latest 50 · newest first</span>
            </div>
            {dashboard?.events.map((e) => (
              <div className="event" key={e.id}>
                <span className="event-dot" />
                <div>
                  <strong>{e.kind}</strong>
                  <small>{e.subject}</small>
                </div>
                <time>{new Date(e.at * 1000).toLocaleTimeString()}</time>
              </div>
            ))}
            {!dashboard?.events.length && (
              <Empty text="Project events will appear here when connected." />
            )}
          </section>
        )}
        <footer className="page-footer">
          <span>
            SKYRA TECH <i>✳</i> JARVIS
          </span>
          <span>
            {dashboard
              ? `Policy v${dashboard.project.version} · Recent lists are bounded`
              : 'Windows control centre · Local first'}
          </span>
        </footer>
      </div>
      {editingPolicy && dashboard && (
        <PolicyDialog
          dashboard={dashboard}
          busy={busy}
          error={error}
          close={() => setEditingPolicy(false)}
          save={(mode, resources, reviewedVersion) =>
            void perform(async () => {
              await request({
                action: 'policy',
                project,
                body: { mode, resources, expected_version: reviewedVersion },
              });
              await refresh(project);
              setEditingPolicy(false);
              setNotice('Permission policy updated. Earlier approvals are invalidated.');
            })
          }
        />
      )}
      {create && (
        <CreateDialog
          key={view}
          project={project}
          dashboard={dashboard}
          projectMode={create === 'project'}
          busy={busy}
          error={error}
          close={() => setCreate(null)}
          submit={(op) => void perform(op)}
          onCreated={async (action, body) => {
            if (action === 'create_project') {
              const data = await request<{ project_id: string }>({ action, body });
              activeProject.current = data.project_id;
              setProject(data.project_id);
              await load();
            } else {
              const data = await request<{ proposal_id: string }>({ action, project, body });
              await refresh(project);
              setProposal(await request({ action: 'proposal', id: data.proposal_id }));
            }
            setCreate(null);
          }}
        />
      )}
    </div>
  );
}

function Empty({ text }: { text: string }) {
  return (
    <div className="empty">
      <span>◇</span>
      <p>{text}</p>
    </div>
  );
}

function CreateDialog({
  project,
  projectMode,
  dashboard,
  busy,
  error,
  close,
  submit,
  onCreated,
}: {
  project: string;
  projectMode: boolean;
  dashboard: Dashboard | null;
  busy: boolean;
  error: string;
  close: () => void;
  submit: (op: () => Promise<void>) => void;
  onCreated: (action: string, body: unknown) => Promise<void>;
}) {
  const [name, setName] = useState(''),
    [goal, setGoal] = useState('');
  const [resource, setResource] = useState(dashboard?.workspaces[0]?.resource || '');
  const [provider, setProvider] = useState(dashboard?.runtime.providers[0]?.name || '');
  const [profile, setProfile] = useState(dashboard?.worker.profiles[0] || '');
  const [files, setFiles] = useState<string[]>([]),
    [skills, setSkills] = useState<string[]>([]);
  const [specifications, setSpecifications] = useState<
    { id: string; version: number; state: string }[]
  >([]);
  const [specification, setSpecification] = useState('');
  useEffect(() => {
    let mounted = true;
    if (!projectMode)
      void request<{ specifications: { id: string; version: number; state: string }[] }>({
        action: 'specifications',
        project,
      })
        .then((data) => {
          if (mounted) setSpecifications(data.specifications.filter((s) => s.state === 'approved'));
        })
        .catch(() => {
          /* Optional linkage unavailable. */
        });
    return () => {
      mounted = false;
    };
  }, [project, projectMode]);
  const requestId = useRef(crypto.randomUUID());
  const intent = useRef('');
  const first = useRef<HTMLInputElement>(null);
  const firstGoal = useRef<HTMLTextAreaElement>(null);
  const blocked = useRef(busy);
  blocked.current = busy;
  useEffect(() => {
    const previous = document.activeElement;
    (first.current || firstGoal.current)?.focus();
    const key = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !blocked.current) close();
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
        role="dialog"
        aria-modal="true"
        aria-labelledby="create-title"
        className="modal"
        onKeyDown={(e) => {
          if (e.key === 'Tab') {
            const elements = Array.from(
              e.currentTarget.querySelectorAll<HTMLElement>(
                'button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled)',
              ),
            );
            const first = elements[0],
              last = elements.at(-1);
            if (e.shiftKey && document.activeElement === first) {
              e.preventDefault();
              last?.focus();
            } else if (!e.shiftKey && document.activeElement === last) {
              e.preventDefault();
              first?.focus();
            }
          }
        }}
      >
        <div className="panel-heading">
          <h2 id="create-title">{projectMode ? 'Create project' : 'Prepare repair context'}</h2>
          <button aria-label="Close dialog" disabled={busy} onClick={close}>
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
            const body = projectMode
              ? { name }
              : {
                  resource,
                  provider,
                  profile,
                  goal,
                  files,
                  skills,
                  ...(specification ? { specification } : {}),
                };
            const signature = JSON.stringify(body);
            if (intent.current && intent.current !== signature)
              requestId.current = crypto.randomUUID();
            intent.current = signature;
            submit(() =>
              onCreated(
                projectMode ? 'create_project' : 'create_proposal',
                projectMode ? body : { ...body, request_id: requestId.current },
              ),
            );
          }}
        >
          {projectMode ? (
            <label>
              Project name
              <input
                ref={first}
                value={name}
                onChange={(e) => setName(e.target.value)}
                maxLength={256}
                required
                disabled={busy}
              />
            </label>
          ) : (
            <>
              <label>
                Goal
                <textarea
                  ref={firstGoal}
                  value={goal}
                  onChange={(e) => setGoal(e.target.value)}
                  maxLength={8000}
                  required
                  disabled={busy}
                />
              </label>
              <label>
                Approved specification (optional)
                <select
                  aria-label="Approved specification"
                  value={specification}
                  disabled={busy}
                  onChange={(e) => setSpecification(e.target.value)}
                >
                  <option value="">No specification linked</option>
                  {specifications.map((s) => (
                    <option key={s.id} value={s.id}>
                      Version {s.version} - {s.id.slice(0, 8)}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Workspace
                <select
                  value={resource}
                  disabled={busy}
                  onChange={(e) => {
                    setResource(e.target.value);
                    setFiles([]);
                  }}
                >
                  {dashboard?.workspaces.map((w) => (
                    <option key={w.resource}>{w.resource}</option>
                  ))}
                </select>
              </label>
              <div className="two-columns">
                <label>
                  Provider
                  <select
                    value={provider}
                    onChange={(e) => setProvider(e.target.value)}
                    disabled={busy}
                  >
                    {dashboard?.runtime.providers.map((p) => (
                      <option key={p.name}>{p.name}</option>
                    ))}
                  </select>
                </label>
                <label>
                  Test profile
                  <select
                    value={profile}
                    onChange={(e) => setProfile(e.target.value)}
                    disabled={busy}
                  >
                    {dashboard?.worker.profiles.map((p) => (
                      <option key={p}>{p}</option>
                    ))}
                  </select>
                </label>
              </div>
              <fieldset>
                <legend>Files to include · select 1–20</legend>
                {dashboard?.workspaces
                  .find((w) => w.resource === resource)
                  ?.files.map((f) => (
                    <label className="checkbox" key={f}>
                      <input
                        type="checkbox"
                        disabled={busy || (!files.includes(f) && files.length >= 20)}
                        checked={files.includes(f)}
                        onChange={(e) =>
                          setFiles(e.target.checked ? [...files, f] : files.filter((x) => x !== f))
                        }
                      />
                      {f}
                      {dashboard?.workspaces
                        .find((w) => w.resource === resource)
                        ?.create_paths?.includes(f)
                        ? ' (creation allowed)'
                        : ''}
                    </label>
                  ))}
              </fieldset>
              <fieldset>
                <legend>Trusted skills · optional</legend>
                {dashboard?.runtime.skills.map((s) => (
                  <label className="checkbox" key={s.name}>
                    <input
                      type="checkbox"
                      disabled={busy || (!skills.includes(s.name) && skills.length >= 5)}
                      checked={skills.includes(s.name)}
                      onChange={(e) =>
                        setSkills(
                          e.target.checked
                            ? [...skills, s.name]
                            : skills.filter((x) => x !== s.name),
                        )
                      }
                    />
                    {s.name} · {s.version}
                  </label>
                ))}
              </fieldset>
              <p className="safety-note">
                Preparation stores selected context locally. A separate Generate action sends it
                online. Protected tests remain read-only. Review source for embedded secrets.
              </p>
            </>
          )}
          <div className="actions">
            <button type="button" disabled={busy} onClick={close}>
              Cancel
            </button>
            <button
              className="primary"
              disabled={
                busy ||
                (projectMode
                  ? !name.trim()
                  : !files.length || !goal.trim() || !profile || !provider)
              }
            >
              {projectMode ? 'Create project' : 'Prepare proposal'}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
