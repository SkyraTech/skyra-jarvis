/** Explicit browser-only visual fixture. Never contacts a core or online model. */
import type {
  Dashboard,
  ProposalDetail,
  Request,
  Run,
  Message,
  ModelTurn,
  Specification,
} from './types';

const specifications: Specification[] = [];
const buildJobs: {
  id: string;
  goal: string;
  state: string;
  phase: string;
  cycle: number;
  calls: number;
  steps: number;
  proposal: string | null;
  run: string | null;
  deadline: number;
  control: string | null;
  config: { max_calls: number; max_cycles: number; max_steps: number };
  summary: Record<string, unknown>;
}[] = [];
const assignments: {
  id: string;
  run: string;
  goal: string;
  state: string;
  steps: number;
  max_steps: number;
  deadline: number;
  updated: number;
  control: string | null;
  summary: Record<string, unknown>;
}[] = [];
const deliveries: {
  id: string;
  target: string;
  state: string;
  sha256: string;
  evidence: string[];
}[] = [];
const now = Math.floor(Date.now() / 1000);
const id = 'a'.repeat(32),
  runId = 'b'.repeat(32),
  approvalId = 'c'.repeat(32),
  taskId = 'd'.repeat(32);
const proposal: ProposalDetail = {
  response_sha256: '2'.repeat(64),
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
if (new URLSearchParams(location.search).has('newfile')) {
  proposal.context.files[0] = {
    path: 'src/feature.py',
    content: '',
    sha256: 'absent',
    protected: false,
    exists: false,
  };
  proposal.response = {
    summary: 'Create the selected feature module.',
    patches: [
      {
        path: 'src/feature.py',
        expected_sha256: 'absent',
        old: '',
        new: 'def answer():\n    return 42\n',
      },
    ],
  };
}
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
  delivery_targets: new URLSearchParams(location.search).has('delivery')
    ? [{ resource: 'source:demo', workspace: 'workspace:demo' }]
    : [],
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
    case 'specifications':
      return { specifications: structuredClone([...specifications].reverse()) };
    case 'specification':
      return structuredClone(specifications.find((s) => s.id === input.id));
    case 'revise_specification': {
      if (new URLSearchParams(location.search).has('stalespec'))
        throw new Error('The state changed. Refresh and review the latest details.');
      const parent = specifications.find((s) => s.id === input.id)!;
      const spec: Specification = {
        ...parent,
        id: `spec-${specifications.length}`,
        version: specifications.length + 1,
        documents: body.documents as Record<string, string>,
        parent_spec: parent.id,
        state: 'draft',
        approved: null,
        sha256: 'e'.repeat(64),
      };
      specifications.push(spec);
      return structuredClone(spec);
    }
    case 'publish_specification': {
      const spec: Specification = {
        id: `spec-${specifications.length}`,
        project: String(input.project),
        version: specifications.length + 1,
        source_turn: String(body.source_turn),
        sha256: 'f'.repeat(64),
        state: 'draft',
        created: now,
        approved: null,
        documents: {
          '01_PRODUCT_REQUIREMENTS.md': '# Fixture requirements\n\nResponsive client website.',
        },
      };
      specifications.push(spec);
      return structuredClone(spec);
    }
    case 'approve_specification': {
      specifications.filter((s) => s.state === 'approved').forEach((s) => (s.state = 'superseded'));
      const spec = specifications.find((s) => s.id === input.id)!;
      spec.state = 'approved';
      spec.approved = now;
      return structuredClone(spec);
    }
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
    case 'assignments':
      return {
        enabled: !new URLSearchParams(location.search).has('runnerdisabled'),
        assignments: structuredClone(assignments),
      };
    case 'build_jobs':
      return {
        enabled: !new URLSearchParams(location.search).has('runnerdisabled'),
        jobs: structuredClone(buildJobs),
      };
    case 'create_build_job':
      if (!buildJobs.length)
        buildJobs.push({
          id: '9'.repeat(32),
          goal: String(body.goal),
          state: new URLSearchParams(location.search).has('buildreview')
            ? 'waiting_review'
            : 'queued',
          phase: 'review',
          cycle: 1,
          calls: 1,
          steps: 2,
          proposal: id,
          run: null,
          deadline: now + Number(body.duration_seconds),
          control: null,
          config: {
            max_calls: Number(body.max_calls),
            max_cycles: Number(body.max_cycles),
            max_steps: Number(body.max_steps),
          },
          summary: { reason: 'proposal_ready' },
        });
      return structuredClone(buildJobs[0]);
    case 'accept_build_proposal':
      if (
        body.context_sha256 !== proposal.context_sha256 ||
        body.response_sha256 !== proposal.response_sha256
      )
        throw new Error('Review changed');
      buildJobs[0].state = 'queued';
      buildJobs[0].phase = 'execute';
      buildJobs[0].run = runId;
      return structuredClone(buildJobs[0]);
    case 'control_build_job':
      buildJobs[0].state =
        body.action === 'pause' ? 'paused' : body.action === 'resume' ? 'queued' : 'cancelled';
      return structuredClone(buildJobs[0]);
    case 'create_assignment':
      if (!assignments.length)
        assignments.push({
          id: 'f'.repeat(32),
          run: runId,
          goal: String(body.goal),
          state: 'queued',
          steps: 0,
          max_steps: Number(body.max_steps),
          deadline: now + Number(body.duration_seconds),
          updated: now,
          control: null,
          summary: { model_calls: 0, reason: 'queued' },
        });
      return structuredClone(assignments[0]);
    case 'control_assignment':
      assignments[0].state =
        body.action === 'pause' ? 'paused' : body.action === 'resume' ? 'queued' : 'cancelled';
      return structuredClone(assignments[0]);
    case 'deliveries':
      return { deliveries: structuredClone(deliveries) };
    case 'delivery_preview':
      return {
        sha256: 'a'.repeat(64),
        plan: {
          changes: [
            {
              path: 'src/totals.py',
              before_sha256: 'f'.repeat(64),
              sha256: 'e'.repeat(64),
              patch: '- return sum(items) - 1\n+ return sum(items)',
            },
          ],
        },
      };
    case 'prepare_delivery':
      if (!deliveries.length)
        deliveries.push({
          id: 'e'.repeat(32),
          target: 'source:demo',
          state: 'queued',
          sha256: 'a'.repeat(64),
          evidence: [],
        });
      return structuredClone(deliveries[0]);
    case 'advance_delivery':
      deliveries[0].state = 'succeeded';
      deliveries[0].evidence = ['sha256:' + 'e'.repeat(64)];
      return structuredClone(deliveries[0]);
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
