/** Explicit browser-only visual fixture. Never contacts a core or online model. */
import type { Dashboard, ProposalDetail, Request, Run, Message, ModelTurn } from './types';

const now = Math.floor(Date.now() / 1000);
const id = 'a'.repeat(32),
  runId = 'b'.repeat(32),
  approvalId = 'c'.repeat(32),
  taskId = 'd'.repeat(32);
const proposal: ProposalDetail = {
  id,
  state: 'ready',
  provider: 'gemini-repair',
  model: 'gemini-3.5-flash-lite',
  resource: 'workspace:demo',
  profile: 'unit',
  error: null,
  run: null,
  usage: { input_tokens: 660, output_tokens: 164, total_tokens: 824 },
  created: now - 120,
  context_sha256: 'e'.repeat(64),
  context: {
    goal: 'Correct the total calculation while preserving the protected tests.',
    files: [
      {
        path: 'src/totals.py',
        content: 'def total(items):\n    return sum(items) - 1\n',
        sha256: 'f'.repeat(64),
        protected: false,
      },
      {
        path: 'tests/test_totals.py',
        content: 'assert total([2, 3]) == 5',
        sha256: '0'.repeat(64),
        protected: true,
      },
    ],
    skills: [{ name: 'minimal-repair', version: '1.0.0', sha256: '1'.repeat(64) }],
  },
  response: {
    summary: 'Remove the extra subtraction from the total calculation.',
    patches: [
      {
        path: 'src/totals.py',
        old: 'sum(items) - 1',
        new: 'sum(items)',
        expected_sha256: 'f'.repeat(64),
      },
    ],
  },
};
const run: Run = {
  id: runId,
  state: 'waiting_approval',
  position: 0,
  resource: 'workspace:demo',
  task: taskId,
  steps: [
    { action: 'execute', expect: 'failure', payload: { operation: 'test', profile: 'unit' } },
    { action: 'write', expect: 'success', payload: { operation: 'patch' } },
    { action: 'execute', expect: 'success', payload: { operation: 'test' } },
    { action: 'read', expect: 'success', payload: { operation: 'diff' } },
  ],
  results: [],
};
const dashboard: Dashboard = {
  project: {
    id: 'demo-project',
    name: 'Skyra workspace',
    mode: 'ask',
    version: 3,
    resources: ['workspace:demo'],
  },
  approvals: [
    {
      id: approvalId,
      task: taskId,
      expires: now + 300,
      action: 'execute',
      resource: 'workspace:demo',
      decidable: true,
    },
  ],
  proposals: [proposal],
  runs: [run],
  conversations: [{ id: 'demo-conversation', message_count: 2 }],
  workspaces: [{ resource: 'workspace:demo', files: ['src/totals.py', 'tests/test_totals.py'] }],
  worker: { execution_available: true, profiles: ['unit'] },
  runtime: {
    providers: [
      { name: 'gemini-repair', model: 'gemini-3.5-flash-lite' },
      { name: 'groq-repair', model: 'qwen/qwen3.8-27b' },
    ],
    skills: [{ name: 'minimal-repair', version: '1.0.0', sha256: '1'.repeat(64) }],
    automatic_execution: false,
  },
  events: [
    { id: 2, kind: 'repair_proposal.ready', subject: id, at: now - 120 },
    { id: 1, kind: 'approval.requested', subject: approvalId, at: now - 60 },
  ],
  server_time: now,
};
const messages: Message[] = [
  {
    id: 1,
    role: 'user',
    content: 'Review the totals calculation before we deliver it.',
    request_id: '1',
  },
  {
    id: 2,
    role: 'assistant',
    content:
      'Sample conversation. Choose Ask Jarvis or Create project plan to request a model response.',
    request_id: '2',
  },
];

const turns: ModelTurn[] = [];
const fixturePlan = {
  title: 'Client website delivery',
  overview: 'Build the agreed responsive website in reviewed phases.',
  requirements: ['Responsive pages and accessible navigation'],
  deliverables: ['Website source and handover guide'],
  phases: [
    {
      title: 'Build and verify',
      tasks: ['Implement approved pages'],
      acceptance: ['Tests and keyboard navigation pass'],
    },
  ],
  risks: ['Brand assets have not been confirmed'],
  questions: ['Who supplies final content?'],
};
let policyChangeScheduled = false;
export async function fixtureRequest(input: Request): Promise<unknown> {
  const body = input.body as Record<string, unknown>;
  switch (input.action) {
    case 'setup':
      return {
        core: true,
        conversation: {
          providers: new URLSearchParams(location.search).has('nomodel')
            ? []
            : dashboard.runtime.providers,
          modes: ['chat', 'plan'],
          tools_enabled: false,
          automatic_retry: false,
        },
        repair_available: true,
        worker: dashboard.worker,
        configuration_source: 'trusted_local_files',
        restart_required_for_config: true,
      };
    case 'turns':
      return { turns: structuredClone([...turns].reverse()) };
    case 'turn':
      return structuredClone(turns.find((t) => t.id === input.id));
    case 'create_turn': {
      const turn: ModelTurn = {
        id: `fixture-turn-${turns.length}`,
        conversation: String(input.id),
        provider: String(body.provider),
        model: dashboard.runtime.providers[0].model,
        mode: body.mode as 'chat' | 'plan',
        state: 'planned',
        error: null,
        created: now,
        user_message: messages.length + 1,
        assistant_message: null,
        context: {
          mode: String(body.mode),
          history: messages.map((m) => ({ id: m.id, role: m.role, content: m.content })),
          request: String(body.content),
          omitted_messages: 0,
        },
        context_sha256: 'e'.repeat(64),
        response: null,
        usage: null,
      };
      messages.push({
        id: messages.length + 1,
        role: 'user',
        content: String(body.content),
        request_id: String(body.request_id),
      });
      turns.push(turn);
      return { turn_id: turn.id };
    }
    case 'generate_turn': {
      const turn = turns.find((t) => t.id === input.id)!;
      if (turn.state !== 'planned') return structuredClone(turn);
      turn.state = 'generating';
      if (new URLSearchParams(location.search).has('slowchat'))
        await new Promise((r) => setTimeout(r, 1800));
      if (turn.state === 'generating') {
        if (new URLSearchParams(location.search).has('failchat')) {
          turn.state = 'failed';
          turn.error = 'provider_http_429';
        } else {
          turn.state = 'completed';
          turn.response = {
            reply: 'Fixture response for human review.',
            ...(turn.mode === 'plan' ? { plan: fixturePlan } : {}),
          };
          turn.usage = { total_tokens: 42 };
          messages.push({
            id: messages.length + 1,
            role: 'assistant',
            content: turn.response.reply,
            request_id: turn.id,
          });
          turn.assistant_message = messages.length;
        }
      }
      return structuredClone(turn);
    }
    case 'interrupt_turn': {
      const turn = turns.find((t) => t.id === input.id)!;
      turn.state = 'interrupted';
      return structuredClone(turn);
    }
    case 'policy':
      if (body.expected_version !== dashboard.project.version)
        throw new Error('The state changed. Close this dialog and review current permissions.');
      dashboard.project.mode = String(body.mode);
      dashboard.project.resources = body.resources as string[];
      dashboard.project.version++;
      dashboard.approvals.forEach((a) => (a.decidable = false));
      return { updated: true };
    case 'projects':
      return {
        projects:
          new URLSearchParams(location.search).get('empty') === '1' ? [] : [dashboard.project],
      };
    case 'dashboard':
      if (new URLSearchParams(location.search).get('stale') === '1' && !policyChangeScheduled) {
        policyChangeScheduled = true;
        setTimeout(() => {
          dashboard.project.version++;
          dashboard.approvals.forEach((a) => (a.decidable = false));
        }, 1000);
      }
      return structuredClone({ ...dashboard, server_time: Math.floor(Date.now() / 1000) });
    case 'proposal':
      return structuredClone(proposal);
    case 'run':
      return structuredClone(run);
    case 'approval':
      return {
        approval: { id: approvalId, expires: now + 300, state: 'pending', version: 3 },
        task: {
          id: taskId,
          action: 'execute',
          resource: 'workspace:demo',
          payload: JSON.stringify({ operation: 'test', profile: 'unit' }),
        },
      };
    case 'decide':
      dashboard.approvals = [];
      return { recorded: true };
    case 'accept':
      proposal.state = 'accepted';
      proposal.run = runId;
      return structuredClone(proposal);
    case 'interrupt':
      proposal.state = 'interrupted';
      return structuredClone(proposal);
    case 'cancel_run':
      run.state = 'cancelled';
      return structuredClone(run);
    case 'advance':
      if (new URLSearchParams(location.search).get('slow') === '1')
        await new Promise((resolve) => setTimeout(resolve, 1500));
      if (run.state !== 'cancelled') {
        run.state = 'ready_for_review';
        run.position = 4;
      }
      return structuredClone(run);
    case 'messages':
      return { messages: structuredClone(messages.filter((m) => m.id > (input.after || 0))) };
    case 'message':
      if (!messages.some((m) => m.request_id === body.request_id))
        messages.push({
          id: messages.length + 1,
          role: 'user',
          content: String(body.content),
          request_id: String(body.request_id),
        });
      return { message_id: messages.length };
    case 'conversation':
      return { conversation_id: 'demo-conversation' };
    case 'create_project':
      return { project_id: 'demo-project' };
    case 'evidence':
      return {
        operation: 'diff',
        result: {
          changes: [
            { path: 'src/totals.py', diff: '- return sum(items) - 1\n+ return sum(items)' },
          ],
        },
      };
    default:
      throw new Error('This operation is unavailable in the visual preview.');
  }
}
