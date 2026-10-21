import { useEffect, useId, useRef, useState } from 'react';
import { request } from './api';
import SpecificationReview from './SpecificationReview';
import CodingHistory from './CodingHistory';
import type {
  Dashboard,
  Message,
  ModelTurn,
  ModelTurnSummary,
  Plan,
  Setup,
  Specification,
} from './types';

function PlanView({ plan }: { plan: Plan }) {
  const list = (title: string, items: string[]) => (
    <section>
      <h3>{title}</h3>
      {items.length ? (
        <ul>
          {items.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
      ) : (
        <p>None listed in this draft.</p>
      )}
    </section>
  );
  return (
    <div className="project-plan">
      <span className="pill warn">Draft · review required</span>
      <h2>{plan.title}</h2>
      <p>{plan.overview}</p>
      {list('Requirements', plan.requirements)}
      {list('Deliverables', plan.deliverables)}
      {plan.phases.map((phase, i) => (
        <section className="plan-phase" key={i}>
          <h3>
            {i + 1}. {phase.title}
          </h3>
          {list('Tasks', phase.tasks)}
          {list('Acceptance criteria', phase.acceptance)}
        </section>
      ))}
      {list('Risks and assumptions', plan.risks)}
      {list('Open questions', plan.questions)}
    </div>
  );
}

export default function ConversationPanel({
  project,
  dashboard,
  refresh,
}: {
  project: string;
  dashboard: Dashboard | null;
  refresh: (id: string) => Promise<void>;
}) {
  const messageControl = useId();
  const [specs, setSpecs] = useState<Specification[]>([]);
  const [spec, setSpec] = useState<Specification | null>(null);
  const publication = useRef<{ turn: string; version: number; id: string } | null>(null);
  async function loadSpecs() {
    const result = await request<{ specifications: Specification[] }>({
      action: 'specifications',
      project,
    });
    if (live.current) setSpecs(result.specifications);
  }
  useEffect(() => {
    void loadSpecs().catch(() => setError('Unable to load specifications.'));
  }, [project]);

  const [conversation, setConversation] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [turns, setTurns] = useState<ModelTurnSummary[]>([]);
  const [turn, setTurn] = useState<ModelTurn | null>(null);
  const [setup, setSetup] = useState<Setup | null>(null);
  const [draft, setDraft] = useState('');
  const [mode, setMode] = useState<'note' | 'chat' | 'plan'>('note');
  const [provider, setProvider] = useState('');
  const [includeCodingHistory, setIncludeCodingHistory] = useState(false);
  const [busy, setBusy] = useState(false),
    [controlBusy, setControlBusy] = useState(false);
  const [error, setError] = useState(''),
    [notice, setNotice] = useState('');
  const gate = useRef(false),
    control = useRef(false),
    live = useRef(true);
  const current = useRef('');
  const pending = useRef<{ key: string; id: string } | null>(null);
  useEffect(() => {
    live.current = true;
    request<Setup>({ action: 'setup' })
      .then((data) => {
        if (live.current) setSetup(data);
      })
      .catch(() => {
        if (live.current)
          setError('Unable to load model configuration. Refresh the conversation screen.');
      });
    return () => {
      live.current = false;
    };
  }, []);
  const providers = setup?.conversation.providers || [];
  const selectedProvider = providers.find((p) => p.name === provider);
  const active = turns.find((t) => ['planned', 'generating'].includes(t.state));

  async function perform(operation: () => Promise<void>, interrupt = false) {
    const lock = interrupt ? control : gate;
    if (lock.current || (!interrupt && control.current)) return;
    lock.current = true;
    (interrupt ? setControlBusy : setBusy)(true);
    setError('');
    setNotice('');
    try {
      await operation();
    } catch (e) {
      if (live.current)
        setError(e instanceof Error ? e.message : 'Refresh status before retrying.');
    } finally {
      lock.current = false;
      if (live.current) (interrupt ? setControlBusy : setBusy)(false);
    }
  }
  async function reload(id: string, reset = false) {
    const after = reset ? 0 : messages.at(-1)?.id || 0;
    const [history, modelTurns] = await Promise.all([
      request<{ messages: Message[] }>({ action: 'messages', id, after }),
      request<{ turns: ModelTurnSummary[] }>({ action: 'turns', id }),
    ]);
    if (!live.current || (current.current && current.current !== id)) return;
    setMessages((previous) =>
      reset
        ? history.messages
        : [...previous, ...history.messages.filter((m) => !previous.some((p) => p.id === m.id))],
    );
    setTurns(modelTurns.turns);
  }
  async function choose(id: string) {
    setIncludeCodingHistory(false);
    current.current = id;
    setDraft('');
    pending.current = null;
    setConversation(id);
    setTurn(null);
    setMessages([]);
    setTurns([]);
    await reload(id, true);
  }
  async function showTurn(id: string) {
    const result = await request<ModelTurn>({ action: 'turn', id });
    if (live.current && current.current === result.conversation) {
      // A late generation response must not replace a terminal interruption already shown.
      setTurn((old) => (old?.id === result.id && old.state === 'interrupted' ? old : result));
    }
    await reload(current.current);
  }
  async function generate(id: string) {
    setTurn((old) => (old?.id === id ? { ...old, state: 'generating' } : old));
    setTurns((old) => old.map((t) => (t.id === id ? { ...t, state: 'generating' } : t)));
    await request<ModelTurn>({ action: 'generate_turn', id });
    if (!live.current) return;
    await showTurn(id);
    await refresh(project);
  }
  async function send() {
    const key = JSON.stringify([conversation, mode, provider, draft, includeCodingHistory]);
    if (pending.current?.key !== key) pending.current = { key, id: crypto.randomUUID() };
    const requestId = pending.current.id;
    if (mode === 'note') {
      await request({
        action: 'message',
        id: conversation,
        body: { role: 'user', content: draft, request_id: requestId },
      });
      setDraft('');
      pending.current = null;
      await reload(conversation);
      await refresh(project);
      setNotice('Message saved. Load remaining history to see later messages.');
      return;
    }
    const result = await request<{ turn_id: string }>({
      action: 'create_turn',
      id: conversation,
      body: {
        provider,
        mode,
        content: draft,
        request_id: requestId,
        include_coding_history: includeCodingHistory,
      },
    });
    setDraft('');
    pending.current = null;
    setIncludeCodingHistory(false);
    await showTurn(result.turn_id);
    await generate(result.turn_id);
  }
  return (
    <section className="content-grid conversations">
      <div className="card list-panel">
        <div className="panel-heading">
          <strong>Project conversations</strong>
          <button
            disabled={busy || controlBusy || !project}
            onClick={() =>
              void perform(async () => {
                const result = await request<{ conversation_id: string }>({
                  action: 'conversation',
                  project,
                });
                await refresh(project);
                await choose(result.conversation_id);
              })
            }
          >
            ＋ New
          </button>
        </div>
        {dashboard?.conversations.map((c) => (
          <button
            className="item"
            key={c.id}
            disabled={busy || controlBusy}
            onClick={() => void perform(() => choose(c.id))}
          >
            <div>
              <strong>Conversation {c.id.slice(0, 8)}</strong>
              <small>{c.message_count} messages</small>
            </div>
            <span>→</span>
          </button>
        ))}
        {!dashboard?.conversations.length && (
          <p className="empty">Create a conversation to store project context.</p>
        )}
      </div>
      <div className="card detail chat">
        {error && (
          <div role="alert" className="error">
            {error}
          </div>
        )}
        {notice && (
          <div role="status" className="notice">
            {notice}
          </div>
        )}
        {conversation ? (
          <>
            <div className="panel-heading">
              <strong>Conversation history</strong>
              <button
                disabled={busy || controlBusy}
                onClick={() =>
                  void perform(async () => {
                    await reload(conversation, true);
                    if (turn) await showTurn(turn.id);
                  })
                }
              >
                Refresh
              </button>
            </div>
            <p className="safety-note">
              Messages stay in this project. Chat and planning send up to 30 recent messages to your
              selected online model. Older or oversized history is omitted. Plans are drafts; they
              do not start coding or grant permissions.
            </p>
            <div className="messages">
              {messages.map((m) => (
                <article key={m.id} className={`message ${m.role}`}>
                  <small>{m.role}</small>
                  <p>{m.content}</p>
                </article>
              ))}
            </div>
            {!!dashboard?.conversations.find(
              (c) => c.id === conversation && c.message_count > messages.length,
            ) && (
              <button
                disabled={busy || controlBusy}
                onClick={() => void perform(() => reload(conversation))}
              >
                Load next messages
              </button>
            )}
            <CodingHistory key={conversation} conversation={conversation} />
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (draft.trim()) void perform(send);
              }}
            >
              <div className="conversation-options">
                <label>
                  Response mode
                  <select
                    aria-label="Response mode"
                    value={mode}
                    disabled={busy || controlBusy}
                    onChange={(e) => {
                      setMode(e.target.value as typeof mode);
                      setIncludeCodingHistory(false);
                    }}
                  >
                    <option value="note">Store note only</option>
                    <option value="chat">Ask Jarvis</option>
                    <option value="plan">Create project plan</option>
                  </select>
                </label>
                {mode !== 'note' && (
                  <label>
                    Online model
                    <select
                      aria-label="Online model"
                      value={provider}
                      disabled={busy || controlBusy}
                      onChange={(e) => {
                        setProvider(e.target.value);
                        setIncludeCodingHistory(false);
                      }}
                    >
                      <option value="">Select provider and model</option>
                      {providers.map((p) => (
                        <option key={p.name} value={p.name}>
                          {p.name} · {p.model}
                        </option>
                      ))}
                    </select>
                  </label>
                )}
              </div>
              {mode !== 'note' && (
                <label className="coding-context-consent">
                  <input
                    type="checkbox"
                    checked={includeCodingHistory}
                    disabled={busy || controlBusy}
                    onChange={(e) => setIncludeCodingHistory(e.target.checked)}
                  />
                  Include this conversation’s recent coding history in this request
                  <small>
                    Shares up to three recorded jobs, shortened goals, test-cycle and delivery
                    references with the selected provider. No source code or test output is
                    attached. This does not authorize work.
                  </small>
                </label>
              )}
              {mode !== 'note' && !providers.length && (
                <p role="status">
                  No online model is configured. Open Setup for the configuration checklist.
                </p>
              )}
              <label className="sr-only" htmlFor={messageControl}>
                Message
              </label>
              <textarea
                id={messageControl}
                value={draft}
                maxLength={mode === 'note' ? 100000 : 8000}
                disabled={busy || controlBusy}
                onChange={(e) => setDraft(e.target.value)}
                placeholder={
                  mode === 'note'
                    ? 'Save project context…'
                    : mode === 'plan'
                      ? 'Describe the project, requirements and constraints…'
                      : 'Ask Jarvis…'
                }
              />
              <button
                className="primary"
                disabled={
                  busy ||
                  controlBusy ||
                  !draft.trim() ||
                  (mode !== 'note' && (!selectedProvider || !!active))
                }
              >
                {mode === 'note'
                  ? 'Save message'
                  : mode === 'plan'
                    ? 'Generate draft plan'
                    : 'Send to model'}
              </button>
            </form>
            <section className="model-turns">
              <h3>Project specifications</h3>
              <p>
                Versioned planning documents. Approval records your review; coding and execution
                require separate actions.
              </p>
              <button disabled={busy || controlBusy} onClick={() => void perform(loadSpecs)}>
                Refresh specifications
              </button>
              {specs.map((entry) => (
                <button
                  className="item"
                  key={entry.id}
                  disabled={busy || controlBusy}
                  onClick={() =>
                    void perform(async () =>
                      setSpec(
                        await request<Specification>({ action: 'specification', id: entry.id }),
                      ),
                    )
                  }
                >
                  <strong>Version {entry.version}</strong>
                  <span className="pill">{entry.state}</span>
                </button>
              ))}
              {spec && (
                <SpecificationReview
                  key={spec.id}
                  spec={spec}
                  latestVersion={specs[0]?.version || 0}
                  busy={busy || controlBusy}
                  error={error}
                  perform={perform}
                  notice={setNotice}
                  onSaved={async (result) => {
                    setSpec(result);
                    await loadSpecs();
                  }}
                />
              )}
            </section>
            <section className="model-turns">
              <h3>Model requests</h3>
              <p>
                One request at a time per conversation. No automatic retries. Interrupted requests
                may still be billed by the provider.
              </p>
              {turns.map((t) => (
                <button
                  className="item"
                  key={t.id}
                  disabled={busy || controlBusy}
                  onClick={() => void perform(() => showTurn(t.id))}
                >
                  <div>
                    <strong>
                      {t.mode === 'plan' ? 'Project plan' : 'Chat reply'} · {t.model}
                    </strong>
                    <small>
                      {t.id.slice(0, 8)} · {new Date(t.created * 1000).toLocaleString()}
                    </small>
                  </div>
                  <span className="pill">{t.state}</span>
                </button>
              ))}
              {active && (
                <button
                  disabled={controlBusy}
                  onClick={() =>
                    void perform(async () => {
                      const result = await request<ModelTurn>({
                        action: 'interrupt_turn',
                        id: active.id,
                      });
                      if (live.current) setTurn(result);
                      await reload(conversation);
                      setNotice('Request interrupted. Late output will not be added to history.');
                    }, true)
                  }
                >
                  Interrupt model request
                </button>
              )}
              {turn && (
                <article className="model-result">
                  <div className="panel-heading">
                    <strong>
                      {turn.mode === 'plan' ? 'Draft project plan' : 'Model response'}
                    </strong>
                    <span className="pill">{turn.state}</span>
                  </div>
                  <p>
                    {turn.provider} · {turn.model}
                  </p>
                  {turn.error && (
                    <p role="alert">
                      {turn.error}
                      {turn.validation_failure && ` (${turn.validation_failure})`}. Review
                      configuration or create a new request; this request will not be replayed.
                    </p>
                  )}
                  {turn.state === 'generating' && (
                    <p>
                      The outcome is pending or uncertain. Refresh status; after a restart,
                      interrupt this request before creating another.
                    </p>
                  )}
                  {turn.state === 'planned' && (
                    <button
                      disabled={busy || controlBusy}
                      onClick={() => void perform(() => generate(turn.id))}
                    >
                      Send prepared request once
                    </button>
                  )}
                  {turn.response && <p className="model-reply">{turn.response.reply}</p>}
                  {turn.response?.plan && <PlanView plan={turn.response.plan} />}
                  {turn.state === 'completed' && turn.response?.plan && (
                    <button
                      disabled={busy || controlBusy}
                      onClick={() =>
                        void perform(async () => {
                          const version = specs[0]?.version || 0;
                          if (
                            publication.current?.turn !== turn.id ||
                            publication.current.version !== version
                          )
                            publication.current = {
                              turn: turn.id,
                              version,
                              id: crypto.randomUUID(),
                            };
                          const result = await request<Specification>({
                            action: 'publish_specification',
                            project,
                            body: {
                              source_turn: turn.id,
                              expected_version: version,
                              request_id: publication.current.id,
                            },
                          });
                          setSpec(result);
                          await loadSpecs();
                          setNotice(
                            'Specification snapshot saved. Review its documents before approval.',
                          );
                        })
                      }
                    >
                      Save specification version
                    </button>
                  )}
                  {turn.usage && (
                    <p className="usage">
                      {Object.entries(turn.usage)
                        .map(([k, v]) => `${k.replaceAll('_', ' ')}: ${v}`)
                        .join(' · ')}
                    </p>
                  )}
                  <details>
                    <summary>Context sent to the model</summary>
                    {turn.context.coding_history && (
                      <p>
                        Explicit coding history snapshot:{' '}
                        {turn.context.coding_history.snapshot.jobs.length} recorded jobs. Historical
                        status only; no execution permission. SHA-256:{' '}
                        {turn.context.coding_history.sha256}
                      </p>
                    )}
                    <p>
                      {turn.context.history.length} history messages included;{' '}
                      {turn.context.omitted_messages} omitted.
                    </p>
                    <small>Snapshot SHA-256: {turn.context_sha256}</small>
                    <pre>{JSON.stringify(turn.context, null, 2)}</pre>
                  </details>
                </article>
              )}
            </section>
          </>
        ) : (
          <p className="empty">
            Choose a conversation. Each conversation has separate durable history.
          </p>
        )}
      </div>
    </section>
  );
}
