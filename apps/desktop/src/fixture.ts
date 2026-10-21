/** Explicit browser-only visual fixture. Never contacts a core or online model. */
import type { Supervision } from './SupervisionStatus';
import type {
  Dashboard,
  ProposalDetail,
  Request,
  Run,
  Message,
  ModelTurn,
  Specification,
  ScaffoldPlan,
  ScaffoldReceipt,
} from './types';

const specifications: Specification[] = [];
const scaffoldReceipts = new Map<string, ScaffoldReceipt>();
const scaffoldPlans = new Map<string, ScaffoldPlan>();
const scaffoldRegistrations = new Map<string, Record<string, unknown>>();
const continuations = new Map<string, Record<string, unknown>>();
type AdmissionFixture = {
  sha256: string;
  specification: string;
  plan: { source_directory: string; input_hashes: Record<string, string> };
  files: { path: string; content: string; sha256: string; exists: boolean }[];
};
const admissionReviews = new Map<string, AdmissionFixture>();
const admissionReceipts = new Map<
  string,
  { admitted: boolean; sha256: string; snapshot: string; execution_enabled: false }
>();
function registrationReview(name: string) {
  const admission = admissionReviews.get(name);
  if (admission && admissionReceipts.has(name))
    return {
      enabled: !new URLSearchParams(location.search).has('noregistration'),
      registration_sha256: admission.sha256,
      registration: {
        project: dashboard.project.id,
        specification: admission.specification,
        name,
        directory: 'C:/fixture/snapshots/' + name,
        workspace: 'workspace:' + name,
        source: 'source:' + name,
        selected: admission.files.map((file) => file.path),
        profile: {
          name: 'existing-tests',
          argv: ['C:/fixture/python.exe', '-m', 'unittest', 'test_acceptance'],
          protected_paths: ['test_acceptance.py', 'requirements.md'],
          timeout: 30,
        },
      },
    };
  const source = scaffoldPlans.get(name)!;
  if (!source) throw new Error('Created scaffold required');
  return {
    enabled: !new URLSearchParams(location.search).has('noregistration'),
    registration_sha256: source.plan_sha256,
    registration: {
      project: dashboard.project.id,
      specification: source.plan.specification,
      name,
      directory: source.plan.destination,
      workspace: 'workspace:' + name,
      source: 'source:' + name,
      selected: source.plan.selected,
      profile: { ...source.plan.profile, name: 'scaffold-' + source.plan_sha256.slice(0, 16) },
    },
  };
}
async function scaffoldPreview(input: Request): Promise<ScaffoldPlan> {
  const body = input.body as {
    name: string;
    contract: { cases: unknown[] };
    expected_sha256: string;
    template?: string;
  };
  const spec = specifications.find((s) => s.id === input.id)!;
  if (
    spec?.state !== 'approved' ||
    spec.sha256 !== body.expected_sha256 ||
    !body.contract?.cases?.length
  )
    throw new Error('Review the approved specification and acceptance cases.');
  const files: Record<string, string> = {
    'app.py': 'def handle(value):\n    raise NotImplementedError("Implementation pending")\n',
    'tests/test_acceptance.py': '# Host-owned protected JSON acceptance examples\n',
    'acceptance.json': JSON.stringify(body.contract),
  };
  const provenance: Record<string, string> = {};
  for (const name of [
    '01_PRODUCT_REQUIREMENTS.md',
    '02_SYSTEM_ARCHITECTURE.md',
    '03_DEVELOPMENT_RULES.md',
    '04_DESIGN_SYSTEM.md',
    '05_PROJECT_TASKS.md',
    '06_PROJECT_MEMORY.md',
    '07_API_AND_EVENTS.md',
    '08_TESTING_AND_ACCEPTANCE.md',
    '09_SECURITY_AND_OPERATIONS.md',
  ]) {
    files['docs/' + name] = spec.documents[name] || '# Host template default\n';
    provenance[name] = name in spec.documents ? 'approved_specification' : 'host_template';
  }
  const plan: ScaffoldPlan['plan'] = {
    template: String(body.template || 'python-json-function-v1'),
    destination: 'C:/fixture/scaffolds/' + body.name,
    name: body.name,
    specification: spec.id,
    specification_sha256: spec.sha256,
    python_sha256: 'a'.repeat(64),
    contract: body.contract as ScaffoldPlan['plan']['contract'],
    files,
    document_provenance: provenance,
    selected: ['app.py', 'tests/test_acceptance.py', 'acceptance.json'],
    profile: {
      name: 'scaffold-acceptance',
      argv: ['C:/fixture/python.exe', '-I', '-B', '-m', 'unittest'],
      protected_paths: ['tests/test_acceptance.py', 'acceptance.json'],
      timeout: 30,
    },
    limitations: [
      'Preview fixture only. No files are written.',
      'Only reviewed JSON examples are tested.',
    ],
  };
  if (body.template === 'python-web-service-v1') {
    files['server.py'] = '# Protected loopback HTTP transport\n';
    files['index.html'] = '<!doctype html><title>Implementation pending</title>\n';
    plan.selected.push('server.py', 'index.html');
    plan.profile.protected_paths.push('server.py');
  }
  if (body.template === 'typescript-json-function-v1') {
    delete plan.python_sha256;
    plan.executable_sha256 = 'b'.repeat(64);
    plan.runtime = {
      kind: 'node-typescript-v1',
      toolchain: {
        node: 'C:/fixture/node.exe',
        node_sha256: 'b'.repeat(64),
        node_version: 'v24.21.0',
        compiler: 'C:/fixture/tsc.exe',
        compiler_sha256: 'c'.repeat(64),
        compiler_version: 'Version 7.0.2',
      },
    };
    delete files['app.py'];
    delete files['tests/test_acceptance.py'];
    files['src/main.ts'] =
      'export function handle(value: unknown): unknown { throw new Error("Pending"); }\n';
    files['src/types.ts'] = 'export type JsonValue = unknown;\n';
    files['tests/acceptance.test.mjs'] = '// Protected Node examples\n';
    plan.selected = ['src/main.ts', 'src/types.ts', 'tests/acceptance.test.mjs', 'acceptance.json'];
    plan.profile = {
      name: 'scaffold-acceptance',
      argv: ['C:/fixture/node.exe', 'tests/run.mjs', 'C:/fixture/tsc.exe'],
      protected_paths: ['src/types.ts', 'tests/acceptance.test.mjs', 'acceptance.json'],
      timeout: 45,
    };
  }
  const hash = await crypto.subtle.digest(
    'SHA-256',
    new TextEncoder().encode(JSON.stringify(plan)),
  );
  return {
    plan,
    plan_sha256: Array.from(new Uint8Array(hash), (b) => b.toString(16).padStart(2, '0')).join(''),
  };
}
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
  config: {
    auto_accept?: boolean;
    skill_bindings?: Record<string, string>;
    context_mode?: 'retrieve';
    conversation?: string;
    mode?: 'repair' | 'feature';
    resource: string;
    max_calls: number;
    max_cycles: number;
    max_steps: number;
    schedule?: { start_at: number; start_by: number; inputs_sha256: string };
  };
  summary: Record<string, unknown>;
  supervision?: Supervision;
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
let releaseAdvance: (() => void) | null = null;
const dashboard: Dashboard = {
  continuation_enabled: true,
  continuation_workspaces: ['workspace:demo'],
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
        existing_projects: {
          available: !new URLSearchParams(location.search).has('noexisting'),
          status: 'configured',
          sources: ['internal-project'],
          registration_sources: ['internal-project'],
        },
        scaffolds: {
          available: !new URLSearchParams(location.search).has('noscaffold'),
          template: 'python-json-function-v1',
          templates: [
            'python-json-function-v1',
            'python-web-service-v1',
            ...(!new URLSearchParams(location.search).has('nonode')
              ? ['typescript-json-function-v1']
              : []),
          ],
        },
        worker: dashboard.worker,
        configuration_source: 'trusted_local_files',
        restart_required_for_config: true,
      };
    case 'turns':
      return { turns: structuredClone([...turns].reverse()) };
    case 'preview_existing_project': {
      const spec = specifications.find((value) => value.id === input.id);
      if (
        spec?.state !== 'approved' ||
        spec.sha256 !== body.expected_sha256 ||
        body.source !== 'internal-project'
      )
        throw new Error('Current approved specification and host-approved source required.');
      const existing: Record<string, string> = {
        'app.py': 'def answer():\n    return 1\n',
        'requirements.md': '# Owner requirements\nReturn two.\n',
        'test_acceptance.py': '# Protected acceptance tests\n',
      };
      const selected = body.files as string[],
        creates = body.create_paths as string[];
      if (selected.some((path) => !(path in existing)) || creates.some((path) => path in existing))
        throw new Error('Review existing and absent file paths.');
      const files = [
        ...selected.map((path) => ({
          path,
          content: existing[path]!,
          sha256: 'a'.repeat(64),
          exists: true,
        })),
        ...creates.map((path) => ({ path, content: '', sha256: 'absent', exists: false })),
      ];
      const identity = await crypto.subtle.digest(
        'SHA-256',
        new TextEncoder().encode(JSON.stringify(body)),
      );
      const review = {
        sha256: Array.from(new Uint8Array(identity), (b) => b.toString(16).padStart(2, '0')).join(
          '',
        ),
        specification: input.id!,
        plan: {
          source_directory: 'C:/fixture/internal-project',
          input_hashes: Object.fromEntries(files.map((file) => [file.path, file.sha256])),
        },
        files,
      };
      admissionReviews.set(String(body.name), review);
      return review;
    }
    case 'admit_existing_project': {
      const review = admissionReviews.get(String(body.name));
      if (!review || review.sha256 !== body.expected_plan_sha256)
        throw new Error('Review the exact current import.');
      const receipt = {
        admitted: true,
        sha256: review.sha256,
        snapshot: 'C:/fixture/snapshots/' + String(body.name) + '/snapshot',
        execution_enabled: false as const,
      };
      admissionReceipts.set(String(body.name), receipt);
      if (new URLSearchParams(location.search).has('importlost'))
        throw new Error('The outcome is uncertain. Check the import receipt.');
      return receipt;
    }
    case 'existing_project_status': {
      const receipt = admissionReceipts.get(String(body.name));
      if (!receipt || receipt.sha256 !== body.expected_plan_sha256)
        throw new Error('Import receipt unavailable.');
      return receipt;
    }
    case 'preview_scaffold':
      return scaffoldPreview(input);
    case 'create_scaffold': {
      const result = await scaffoldPreview(input);
      if (
        body.expected_plan_sha256 !== result.plan_sha256 ||
        scaffoldReceipts.has(result.plan.name)
      )
        throw new Error('The plan changed or this project already exists.');
      const receipt = {
        exists: true,
        directory: result.plan.destination,
        plan_sha256: result.plan_sha256,
        state: 'unimplemented',
        audit_recorded: true,
      };
      scaffoldReceipts.set(result.plan.name, receipt);
      scaffoldPlans.set(result.plan.name, result);
      if (new URLSearchParams(location.search).has('scaffoldlost'))
        throw new Error('The outcome is uncertain. Check the creation receipt.');
      return receipt;
    }
    case 'scaffold_status':
      return scaffoldReceipts.get(String(body.name)) || { exists: false };
    case 'preview_scaffold_registration':
    case 'preview_existing_registration':
      return registrationReview(String(body.name));
    case 'scaffold_registration':
      return (
        scaffoldRegistrations.get(String(body.name)) || {
          registered: false,
          enabled: !new URLSearchParams(location.search).has('noregistration'),
        }
      );
    case 'register_scaffold':
    case 'register_existing_project': {
      const review = registrationReview(String(body.name));
      if (
        !review.enabled ||
        body.allow_native_execution !== true ||
        body.expected_registration_sha256 !== review.registration_sha256
      )
        throw new Error('Reviewed native registration consent required');
      const config = review.registration;
      const result = { ...review, registered: true, active: true };
      if (!scaffoldRegistrations.has(config.name)) {
        dashboard.workspaces.push({ resource: config.workspace, files: config.selected });
        dashboard.worker.profiles.push(config.profile.name);
        dashboard.delivery_targets!.push({ resource: config.source, workspace: config.workspace });
      }
      scaffoldRegistrations.set(config.name, result);
      return result;
    }
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
          ...(body.include_coding_history === true
            ? {
                coding_history: {
                  snapshot: {
                    jobs: buildJobs
                      .filter((j) => j.config.conversation === input.id)
                      .slice(-3)
                      .reverse()
                      .map((j) => ({ id: j.id })),
                  },
                  sha256: 'c'.repeat(64),
                },
              }
            : {}),
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
      if (
        new URLSearchParams(location.search).has('skilldrift') &&
        sessionStorage.getItem('fixture.skill-revision') === 'updated'
      ) {
        dashboard.runtime.skills = [
          { name: 'minimal-repair', version: '2.0.0', sha256: '2'.repeat(64) },
        ];
      }
      if (new URLSearchParams(location.search).has('manyskills')) {
        dashboard.runtime.skills = Array.from({ length: 6 }, (_, index) => ({
          name: `skill-${index + 1}`,
          version: '1.0.0',
          sha256: String(index + 1).repeat(64),
        }));
      }
      if (new URLSearchParams(location.search).get('stale') === '1' && !policyChangeScheduled) {
        policyChangeScheduled = true;
        setTimeout(() => {
          dashboard.project.version++;
          dashboard.approvals.forEach((a) => (a.decidable = false));
        }, 1000);
      }
      {
        const state = new URLSearchParams(location.search).get('coreactivity');
        const counts: Record<string, number> = state
          ? {}
          : {
              approvals: dashboard.approvals.filter((a) => a.decidable).length,
              reviews: dashboard.proposals.filter((p) => p.state === 'ready').length,
            };
        const keys: Record<string, string> = {
          testing: 'testing',
          coding: 'coding',
          planning: 'planning_requests',
          thinking: 'chat_requests',
          inspecting: 'inspecting',
          blocked: 'blocked',
          paused: 'paused',
          queued: 'queued',
          stopping: 'stopping',
        };
        if (state && keys[state]) counts[keys[state]] = 1;
        if (state === 'mixed') Object.assign(counts, { approvals: 1, testing: 1, blocked: 1 });
        const activity =
          state === 'unknown'
            ? undefined
            : {
                source: 'core-state-v1',
                project: state === 'foreign' ? 'foreign-project' : dashboard.project.id,
                captured_at: Math.floor(Date.now() / 1000),
                counts,
              };
        return structuredClone({
          ...dashboard,
          activity,
          server_time: Math.floor(Date.now() / 1000),
        });
      }
    case 'proposal':
      return structuredClone(proposal);
    case 'run':
      return structuredClone(run);
    case 'assignments':
      return {
        enabled: !new URLSearchParams(location.search).has('runnerdisabled'),
        assignments: structuredClone(assignments),
      };
    case 'operations': {
      const outcome = {
        lane: 'build_job',
        id: 'd'.repeat(32),
        goal: 'Overnight client portal repair',
        state: 'completed',
        reason: 'tested_repair_ready',
        run: run.id,
        resource: 'workspace:fixture',
        calls: 2,
        max_calls: 2,
        steps: 13,
        max_steps: 40,
        deadline: now + 3600,
        evidence: ['sha256:' + 'e'.repeat(64)],
        source_delivery: 'separate_review_required',
      };
      const notices = [2, 1].map((event) => ({
        id: String(event).repeat(32),
        event,
        created: now - event,
        acknowledged: sessionStorage.getItem('fixture.notice.' + event) ? now : null,
        snapshot:
          event === 2
            ? outcome
            : { ...outcome, state: 'blocked', reason: 'runner_interrupted', run: null },
      }));
      return {
        notices: input.after ? [] : notices,
        next_before: null,
        unread: notices.filter((n) => n.acknowledged === null).length,
        host_enabled: !new URLSearchParams(location.search).has('runnerdisabled'),
        runner_contact: {
          state: new URLSearchParams(location.search).has('runnerdisabled')
            ? 'never_seen'
            : 'recent',
          started: now - 4,
          finished: now - 2,
          outcome: 'responded',
        },
        server_time: now,
        work: [
          {
            ...outcome,
            id: 'b'.repeat(32),
            state: 'budget_limited',
            reason: 'model_call_budget',
            expired: true,
          },
        ],
        library: [...scaffoldRegistrations.values()].map((value) => {
          const config = value.registration as {
            name: string;
            specification: string;
            workspace: string;
            source: string;
          };
          return {
            name: config.name,
            specification: config.specification,
            plan_sha256: value.registration_sha256,
            active: true,
            enabled: true,
            reconciliation_required: false,
            granted: [config.workspace, config.source].every((r) =>
              dashboard.project.resources?.includes(r),
            ),
          };
        }),
      };
    }
    case 'acknowledge_operation':
      sessionStorage.setItem('fixture.notice.' + input.id![0], '1');
      return { id: input.id, acknowledged: now };
    case 'build_jobs':
      return {
        enabled: !new URLSearchParams(location.search).has('runnerdisabled'),
        jobs: structuredClone(buildJobs),
      };
    case 'create_build_job':
      if (body.expected_skills) {
        for (const [name, sha] of Object.entries(body.expected_skills as Record<string, string>)) {
          if (
            !dashboard.runtime.skills.some((skill) => skill.name === name && skill.sha256 === sha)
          )
            throw new Error('Selected skill guidance changed.');
        }
      }
      if (body.context_mode === 'retrieve')
        proposal.context.retrieval = {
          task: '7'.repeat(32),
          evidence: 'sha256:' + '8'.repeat(64),
          algorithm: 'lexical-v1',
          scope: 'selected_snapshot',
          input_hashes: {
            'src/totals.py': 'f'.repeat(64),
            'tests/test_totals.py': '0'.repeat(64),
            'large.py': 'a'.repeat(64),
          },
          omitted: [{ path: 'large.py', reason: 'context_budget' }],
          query_sha256: 'b'.repeat(64),
        };
      if (!buildJobs.length)
        buildJobs.push({
          id: '9'.repeat(32),
          goal: String(body.goal),
          state: new URLSearchParams(location.search).has('runningbuild')
            ? 'running'
            : new URLSearchParams(location.search).has('buildreview')
              ? 'waiting_review'
              : 'queued',
          phase: body.start_at ? 'baseline' : 'review',
          cycle: 1,
          calls: body.start_at ? 0 : 1,
          steps: body.start_at ? 0 : 2,
          proposal: id,
          run: null,
          deadline: Number(body.start_at || now) + Number(body.duration_seconds),
          control: null,
          config: {
            auto_accept: body.auto_accept === true,
            ...(body.context_mode === 'retrieve' ? { context_mode: 'retrieve' as const } : {}),
            ...(typeof body.conversation === 'string' ? { conversation: body.conversation } : {}),
            mode: body.mode === 'feature' ? 'feature' : 'repair',
            resource: String(body.resource),
            ...(body.expected_skills
              ? { skill_bindings: structuredClone(body.expected_skills as Record<string, string>) }
              : {}),
            ...(body.start_at
              ? {
                  schedule: {
                    start_at: Number(body.start_at),
                    start_by: Number(body.start_at) + Number(body.start_window_seconds),
                    inputs_sha256: 'f'.repeat(64),
                  },
                }
              : {}),
            max_calls: Number(body.max_calls),
            max_cycles: Number(body.max_cycles),
            max_steps: Number(body.max_steps),
          },
          summary: { reason: body.start_at ? 'scheduled' : 'proposal_ready' },
          ...(new URLSearchParams(location.search).has('runningbuild')
            ? {
                supervision: {
                  started_at: now - 610,
                  heartbeat_at: now - 1,
                  lease_expires_at: now + 599,
                  lease_valid: !new URLSearchParams(location.search).has('expiredlease'),
                  elapsed_seconds: 610,
                  deadline_remaining_seconds: 2990,
                },
              }
            : {}),
        });
      if (new URLSearchParams(location.search).has('failedgeneration')) {
        const failure = new URLSearchParams(location.search).get('failedgeneration')!;
        buildJobs[0].state = 'failed';
        buildJobs[0].phase = 'propose';
        buildJobs[0].summary = { reason: failure, validation_failure: 'invalid_json' };
        proposal.state = 'failed';
        proposal.error = failure;
        proposal.validation_failure = 'invalid_json';
      }
      return structuredClone(buildJobs[0]);
    case 'retry_build_generation':
      if (
        body.allow_model_call !== true ||
        body.proposal !== proposal.id ||
        body.context_sha256 !== proposal.context_sha256
      )
        throw new Error('Exact failed generation and consent required');
      buildJobs[0].state = 'queued';
      buildJobs[0].phase = 'propose';
      buildJobs[0].cycle += 1;
      buildJobs[0].proposal = null;
      buildJobs[0].summary = { reason: 'owner_requested_new_generation' };
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
    case 'continuation_preview':
      if (!deliveries.some((d) => d.id === input.id && d.state === 'succeeded'))
        throw new Error('Successful reviewed delivery required');
      return {
        enabled: true,
        registration_sha256: 'c'.repeat(64),
        registration: {
          workspace: 'workspace:' + String(body.name),
          source: 'source:' + String(body.name),
          previous_workspace: 'workspace:demo',
          selected: ['src/totals.py', 'tests/test_totals.py'],
          profile: { name: 'unit', protected_paths: ['tests/test_totals.py'] },
          lineage: {
            review: {
              hashes: { 'src/totals.py': 'e'.repeat(64), 'tests/test_totals.py': '0'.repeat(64) },
            },
          },
        },
      };
    case 'continuation_status':
      return structuredClone(
        continuations.get(String(body.name)) || { registered: false, enabled: true },
      );
    case 'continue_project': {
      if (
        body.allow_native_execution !== true ||
        body.expected_registration_sha256 !== 'c'.repeat(64)
      )
        throw new Error('Exact registration consent required');
      const review = (await fixtureRequest({
        action: 'continuation_preview',
        id: input.id,
        body: { name: body.name },
      })) as { registration: Record<string, unknown> };
      const result = { registered: true, active: true, registration: review.registration };
      continuations.set(String(body.name), result);
      return structuredClone(result);
    }
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
      releaseAdvance?.();
      releaseAdvance = null;
      return structuredClone(run);
    case 'advance':
      if (new URLSearchParams(location.search).get('slow') === '1')
        await new Promise<void>((resolve) => {
          releaseAdvance = resolve;
        });
      if (run.state !== 'cancelled') {
        run.state = 'ready_for_review';
        run.position = 4;
      }
      return structuredClone(run);
    case 'coding_history':
      return {
        conversation: input.id,
        project: dashboard.project.id,
        jobs: buildJobs
          .filter((job) => job.config.conversation === input.id)
          .map((job) => ({
            ...job,
            resource: job.config.resource,
            mode: job.config.mode || 'repair',
            cycles: [],
            deliveries: [],
            generations: [],
            details_limited: false,
          })),
        next_before: null,
        model_context_included: false,
        automatic_execution: false,
      };
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
