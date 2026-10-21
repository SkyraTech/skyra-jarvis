export type Project = {
  id: string;
  name: string;
  mode: string;
  version: number;
  resources?: string[];
};
export type Approval = {
  id: string;
  task: string;
  expires: number;
  action: string;
  resource: string;
  decidable: boolean;
};
export type Proposal = {
  id: string;
  state: string;
  provider: string;
  model: string;
  resource: string;
  profile: string;
  error: string | null;
  validation_failure?: string | null;
  run: string | null;
  usage: Record<string, number> | null;
  created: number;
};
export type Run = {
  id: string;
  state: string;
  position: number;
  resource: string;
  steps?: { action: string; expect: string; payload: Record<string, unknown> }[];
  results?: { task_id: string; state: string; evidence: string[]; expectation_met: boolean }[];
  task?: string | null;
};
export type Runtime = {
  providers: { name: string; model: string }[];
  skills: { name: string; version: string; sha256: string }[];
  automatic_execution: boolean;
};
export type Dashboard = {
  activity?: import('./coreActivity').ActivitySnapshot;
  continuation_enabled?: boolean;
  continuation_workspaces?: string[];
  operation_unread?: number;
  delivery_targets?: { resource: string; workspace: string }[];
  registered_resources?: string[];
  project: Project;
  approvals: Approval[];
  proposals: Proposal[];
  runs: Run[];
  conversations: { id: string; message_count: number }[];
  workspaces: { resource: string; files: string[]; create_paths?: string[] }[];
  worker: { execution_available: boolean; profiles: string[] };
  runtime: Runtime;
  events: { id: number; kind: string; subject: string; at: number }[];
  server_time: number;
};
export type ProposalDetail = Proposal & {
  response_sha256?: string;
  context_sha256: string;
  context: {
    retrieval?: {
      task: string;
      evidence: string;
      algorithm: string;
      scope: string;
      input_hashes: Record<string, string>;
      omitted: { path: string; reason: string }[];
      query_sha256: string;
    };
    goal: string;
    files: {
      path: string;
      content: string;
      sha256: string;
      protected: boolean;
      exists?: boolean;
    }[];
    skills: { name: string; version: string; sha256: string }[];
  };
  response: {
    summary: string;
    patches: { path: string; old: string; new: string; expected_sha256: string }[];
  } | null;
};
export type Message = { id: number; role: string; content: string; request_id: string };
export type Request = {
  action: string;
  project?: string;
  id?: string;
  checksum?: string;
  after?: number;
  body?: unknown;
};
export type Connection = { configured: boolean; worker_configured: boolean };
export type Plan = {
  title: string;
  overview: string;
  requirements: string[];
  deliverables: string[];
  phases: { title: string; tasks: string[]; acceptance: string[] }[];
  risks: string[];
  questions: string[];
};
export type ModelTurnSummary = {
  id: string;
  provider: string;
  model: string;
  mode: 'chat' | 'plan';
  state: string;
  error: string | null;
  validation_failure?: string | null;
  created: number;
  user_message: number;
  assistant_message: number | null;
};
export type ModelTurn = ModelTurnSummary & {
  conversation: string;
  context: {
    mode: string;
    history: { id: number; role: string; content: string }[];
    request: string;
    omitted_messages: number;
    coding_history?: { snapshot: { jobs: { id: string }[] }; sha256: string };
  };
  context_sha256: string;
  response: { reply: string; plan?: Plan } | null;
  usage: Record<string, number> | null;
};
export type Setup = {
  core: boolean;
  conversation: {
    providers: { name: string; model: string }[];
    modes: string[];
    tools_enabled: boolean;
    automatic_retry: boolean;
  };
  repair_available: boolean;
  worker: { execution_available: boolean; profiles: string[] };
  configuration_source: string;
  restart_required_for_config: boolean;
};

export type Specification = {
  parent_spec?: string | null;
  id: string;
  project: string;
  version: number;
  source_turn: string;
  sha256: string;
  state: 'draft' | 'approved' | 'superseded';
  created: number;
  approved: number | null;
  documents: Record<string, string>;
};

export type ScaffoldPlan = {
  plan_sha256: string;
  plan: {
    template: string;
    destination: string;
    name: string;
    specification: string;
    specification_sha256: string;
    python_sha256?: string;
    executable_sha256?: string;
    runtime?: {
      kind: string;
      toolchain: {
        node: string;
        node_sha256: string;
        node_version: string;
        compiler: string;
        compiler_sha256: string;
        compiler_version: string;
      };
    };
    contract: { cases: { name: string; input: unknown; output: unknown }[] };
    files: Record<string, string>;
    document_provenance: Record<string, string>;
    selected: string[];
    profile: { name: string; argv: string[]; protected_paths: string[]; timeout: number };
    limitations: string[];
  };
};

export type ScaffoldReceipt = {
  exists?: boolean;
  directory?: string;
  plan_sha256?: string;
  state?: string;
  audit_recorded?: boolean;
};
