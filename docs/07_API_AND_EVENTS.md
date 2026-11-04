# Jarvis Orchestration Core â€” API and Events

## Maintained specification â€” current status

Updated 2026-10-16. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented and verified: durable core, authenticated local API, selected-file worker, owner-enabled native Windows tests, repair workflows and bounded Gemini/Groq repair proposals with versioned skill context and controller review. Native desktop control, flexible 3D/tabbed/multi-window workspace, model-backed conversation, structured draft planning and setup-readiness guidance are implemented. Reviewed function and website/HTTP templates connect desktop creation, durable registration, explicit grants, bounded repair jobs and separate source delivery. The Activity operations center adds durable outcomes, acknowledgement, saved project recovery and recorded runner contact. Build jobs support one-time scheduled starts with input/specification admission guards; final native acceptance is recorded in DEVELOPMENT.md. General autonomous building, a registry/configuration editor, installer/update delivery and mobile pairing remain pending.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](ARCHITECTURE.md)
- [Current functionality and implementation boundaries](FUNCTIONALITY.md)
- [Current milestone and verification summary](DEVELOPMENT.md)

Prepared: 2026-10-14. Requirement/design baseline. Use the maintained current-status section above to distinguish implemented work from planned work.

## Proposed surface

These are draft contracts for implementation, not a list of currently working endpoints. Publish machine-readable OpenAPI/JSON Schema before integrating consumers.

| Operation | Intended behavior |
|---|---|
| `POST /v1/projects` | Create a project boundary; return project ID |
| `POST /v1/conversations/{id}/messages` | Append idempotent message and optionally create a run |
| `POST /v1/runs` | Create a run against an explicit specification and policy version; return 202 |
| `POST /v1/approvals/{id}/decisions` | Authorize the exact pending action hash, or reject it |
| `POST /v1/runs/{id}/cancel` | Persist cancellation and request worker acknowledgement |
| `GET /v1/runs/{id}/events` | Replay ordered events from cursor and stream new events |
| `POST /v1/memories` | Store explicit teaching with scope and provenance |
| `GET /v1/capabilities` | List implemented, connected, ready and unavailable capabilities |

## Identity and validation

Carry request ID, authenticated actor, organization/project scope, action, resource and policy version. The server derives trusted identity from verified credentials; caller-supplied tenant IDs alone grant nothing. Validate schema and resource access before execution. Provider account selection must be explicit. Correlate delegated tasks with parent run and originating actor.

## Jobs, errors and retries

Long work returns `202` with `job_id` and a status resource. State transitions: queued â†’ running â†’ succeeded/failed/cancelled; approval waiting pauses execution and resume revalidates policy. Lease loss or crash triggers reconciliation before another owner dispatches external effects. Store retry attempt, deadline and cancellation acknowledgement.

Errors include stable code, sanitized message, request ID, retry classification and optional details. Distinguish validation, unauthenticated, denied, approval-required, rate-limited, unavailable and outcome-unknown. Do not leak provider credentials in raw exceptions.

Side-effecting requests use an idempotency key scoped to actor/account/operation, plus a canonical payload hash. Same key with different input is a conflict. Duplicate delivery returns the earlier result or current state. Retention of deduplication records must cover the supported retry window. Exactly-once external delivery must not be promised without provider support and reconciliation.

## Event envelope

```json
{
  "event_id": "unique-id",
  "event_type": "job.state_changed",
  "schema_version": "1.0",
  "occurred_at": "2026-10-14T00:00:00Z",
  "producer": "skyra-jarvis",
  "organization_id": "scope-id",
  "project_id": "project-id",
  "correlation_id": "run-id",
  "causation_id": "request-or-event-id",
  "aggregate_id": "job-id",
  "sequence": 1,
  "payload": {"state": "queued"}
}
```

Example only: replace IDs with real values. Ordering is per aggregate, not global; consumers deduplicate event IDs and handle gaps. Publish owned state transitions with an outbox when crossing process boundaries. Store artifact references/checksums rather than large binary content in events.

## Compatibility and MCP

Additive optional fields may be minor changes; removals, changed meaning and new required inputs need a major version or explicit migration. Contract fixtures cover TypeScript and Python consumers. MCP tools expose only supported operations and preserve identity, scopes, idempotency and approval rules. Tool discovery is not authorization. Pin and review external MCP servers and their tool changes.

## Implemented repair API/events

Controller-only: GET `/v1/runtime/capabilities`; POST `/v1/projects/{project}/repair-proposals`; POST `/v1/repair-proposals/{proposal}/generate`, `/accept`, `/interrupt`. GET `/v1/repair-proposals/{proposal}` allows controller or owned/project-scoped agent. Worker access denied. Schema comes from the API source/controller OpenAPI. Creation requires resource/profile/provider/goal/files/request_id; skills optional. Events: `repair_proposal.created`, `.generating`, `.ready`, `.failed`, `.interrupted`, `.accepted`. They contain subject IDs, not source/keys. Generation persists its outcome before response; clients read status after a transport timeout and never blindly resend a new request.

## Desktop integration contracts

GET `/v1/projects/{project}/dashboard` is controller-only, owner-checked and bounded. It returns policy/resources, conversation counts, proposal metadata, run summaries, pending approval validity, permitted workspace selections, registered logical resources, capabilities, recent events and server time. It returns no tokens, leases or content/payload bodies. GET details/messages/evidence use existing owned routes. PUT project policy accepts optional `expected_version`; desktop sends the reviewed version and handles conflict. Native bridge validates action/IDs/checksums and reserves worker authority for advance. UI creates no new event types; existing core operations emit durable events.

## Conversation and draft planning

Controller-only routes: GET /v1/setup; POST /v1/conversations/{id}/model-turns with provider/mode/content/request_id; GET the same collection (100 recent metadata records); GET /v1/model-turns/{id}; POST its /generate and /interrupt actions. Create persists a user message and snapshot but makes no provider call. Generate dispatches once. Existing message pagination remains unchanged. Events: model_turn.created, .generating, .completed, .failed and .interrupted; user/assistant appends also emit message.appended.

## Flexible 3D workspace

New native commands: open_panel(view, project?) and workspace_action(action, width?, height?). open_panel accepts only Overview, Jarvis core, System map, Repair proposals, Coding runs, Approvals, Conversations, Activity and Setup. Workspace actions are minimize, maximize toggle, fullscreen toggle, resize, show_all, save and restore. No generic URL/window/shell/filesystem command is exposed. Main and host-created panel-* windows can use the existing allowlisted Core bridge; project/owner checks remain enforced by the server.


## Versioned specification workflow - 2026-10-15

Controller-only endpoints: GET/POST /v1/projects/{project}/specifications; GET /v1/specifications/{id}; POST /v1/specifications/{id}/approve. Publication body: source_turn, expected_version (0 for the first version), request_id. Approval body: expected_sha256. Lists contain at most 100 metadata records; exact detail returns documents. Repair proposal creation accepts optional specification ID. Events: specification.published and specification.approved. Publication is an offline operation with no model call.


## Specification revision and delivery - 2026-10-15

Controller POST /v1/specifications/{id}/revisions accepts documents, expected_sha256, expected_version and request_id; returns a new specification (201). POST /v1/specifications/{id}/export accepts expected_sha256 and returns approved canonical documents plus provenance, not an arbitrary-path write. Events: specification.revised and specification.export_prepared. Native command export_specification(id, expected_sha256) performs the bounded local write and returns directory/files/existing.


## Reviewed new-file coding - 2026-10-15

Existing proposal/coding-run APIs carry new-file entries as {path, expected_sha256:"absent", old:"", new:<full content>}. Worker task payload is exactly {operation:"create",path,content}, action write. Dashboard workspace metadata adds create_paths. Existing task/run events and content-addressed create evidence are used; evidence references remain real SHA-256 hashes. The string absent denotes file nonexistence, never a content hash.

## Reviewed source delivery - 2026-10-15

Controller POST /v1/coding-runs/{run}/delivery-preview accepts target and returns plan/sha256. Controller POST /v1/coding-runs/{run}/deliveries accepts target, expected_sha256 and request_id; returns task status (201). GET on the latter path lists up to 100 deliveries for the owned run. Worker POST /v1/deliveries/{task}/advance starts only queued/waiting-approval tasks under the existing task policy. Controller credentials cannot execute this route, and agent credentials cannot prepare source delivery. Existing approval-decision and task-evidence APIs apply.

Status includes id, run, target, state, manifest sha256 and evidence references. Dashboard adds delivery_targets with logical resource/workspace pairs; physical paths remain trusted host configuration. Event delivery.prepared supplements existing task/approval events. Source task payload operation deliver is controller-prepared and includes tested inputs, baseline, change set, profile checksum and target binding checksum. Fixed native bridge actions are delivery_preview, prepare_delivery, deliveries and advance_delivery; only advance_delivery selects the worker credential.

## Model-backed repair-job contracts - 2026-10-15

Controller GET/POST /v1/projects/{project}/build-jobs lists up to 50 metadata records or creates a job (201). Creation requires resource, profile, provider, goal, files, skills, max_calls, max_cycles, max_steps, duration_seconds, auto_accept, allow_model_calls=true and request_id; specification is optional. Host unattended enablement and configured repair runtime are required for new execution. Identical requests are idempotent; changed intent conflicts.

Controller GET /v1/build-jobs/{id} includes cycle history and diagnostic evidence; metadata remains readable with runtime removed. POST /v1/build-jobs/{id}/control accepts pause/resume/cancel. POST /v1/build-jobs/{id}/accept-proposal requires context_sha256 and response_sha256 matching the displayed immutable proposal. Job configuration/budget and existing runtime freshness checks apply before acceptance. Repair proposal detail now exposes response_sha256 as well as context_sha256.

Worker POST /v1/runner/tick still accepts only project. It selects one due assignment/build lane under shared exclusion and returns assignment or build_job plus recovered. Workers cannot create/review/control jobs, and controllers cannot tick execution. Native controller actions are build_jobs, create_build_job, build_job, control_build_job and accept_build_proposal; no generic URL or renderer tick is added. Events include build_job.created/dispatched/model_call_reserved/proposal_accepted plus state/control/interruption events. Job reads omit lease tokens and internal request digests; physical paths and provider keys are not renderer configuration.

## Unattended assignment contracts - 2026-10-15

Controller GET /v1/projects/{project}/assignments returns enabled plus up to 100 owner-scoped assignments. POST creates one from run, goal (1â€“2000 characters), max_steps (1â€“100), duration_seconds (60â€“604800) and request_id; returns 201. Repeated identical requests return the same record; changed intent conflicts. Controller POST /v1/assignments/{id}/control accepts action pause/resume/cancel. Pausing/cancelling existing work remains available when new execution is host-disabled; resume requires enablement.

Worker-only POST /v1/runner/tick accepts project within credential scope, claims at most one due assignment and returns assignment or null plus recovered count. Creation and ticks require explicit host enablement and a registered workflow. Assignment reads omit lease tokens and internal request digests. Events assignment.created/dispatched/queued/waiting_approval/paused/blocked/completed/failed/cancelled/budget_limited/interrupted plus pause/resume/cancel control events identify state changes. Quiet pending-approval polls add no dispatch attempt or event. Native controller bridge actions are assignments, create_assignment and control_assignment. There is intentionally no renderer runner_tick route: execution belongs to the hidden worker.

## Scaffold host interface - 2026-10-15

Controller-only scaffold routes now supplement the owner maintenance command. The command accepts an existing Core database/owner and a bounded request containing specification, expected_sha256, contract, parent, name and python. --review writes an exclusive JSON review artifact. --apply requires --expected-plan-sha256 and revalidates the approved specification. Existing project events gain scaffold.created with a JSON subject containing specification, plan_sha256, destination and template. This event indicates creation only, not implementation/test success, policy enablement or delivery. The scaffold manifest is an immutable initial receipt; current coding/delivery progress remains in existing Core records.

## Desktop scaffold contracts - 2026-10-15

POST /v1/specifications/{spec}/scaffolds/preview accepts exactly name, expected_sha256 and contract; returns plan and plan_sha256. POST .../create additionally requires expected_plan_sha256 and returns 201 with the creation receipt/registration draft. POST .../status accepts exactly name and returns exists=false or directory, plan_sha256, initial state and audit_recorded. All are authenticated controller-only and enforce specification ownership; create/preview require an intact approved specification. Draft/superseded history is readable through status if its receipt bindings match.

The parent and interpreter come only from trusted host configuration/Core, never the request. Extra path/executable/file fields fail validation. Setup includes scaffolds.available and template. Disabled host creation is forbidden. Native bridge actions are preview_scaffold, create_scaffold and scaffold_status; they use fixed suffixes and validated specification IDs. Existing scaffold.created events and schema 11 remain unchanged. An on-disk receipt without its audit event is explicitly flagged and never authorizes further work.


## Integrated project-building milestone - 2026-10-15

Controller-only scaffold registration-preview/register/registration routes accept fixed name, expected plan hash, expected registration hash and explicit native consent as appropriate; extra paths/commands are rejected. The Rust bridge exposes fixed matching actions. Preview/create accepts only the two enumerated host template IDs. Registration writes scaffold.registered; resource grants remain the existing expected-version policy API, jobs remain existing bounded APIs and delivery retains its independent exact-action authority. Agent/worker credentials cannot register scaffolds.


## Unattended operations milestone - 2026-10-16

GET /v1/projects/{project}/operations?before=<event-id> returns at most 50 newest notices, unread count, next_before cursor, bounded current work, library and host_enabled. Host enablement is not a health claim. POST /v1/operations/{notice}/acknowledge preserves the first acknowledgement timestamp and cannot control jobs/tasks. Both routes require controller credentials and owner project scope. Dashboard operation_unread is read-only. Fixed Rust actions are operations and acknowledge_operation; no new worker execution route is exposed.


## Scheduled background builds - 2026-10-16

BuildJobInput now accepts optional start_at (integer UTC Unix seconds) and start_window_seconds (60..86400, default 900). Local UI converts the reviewed local time to UTC. New schedules must start in the future within seven days; existing identical request IDs recover saved intent rather than revalidating the now-past start. Only controller/owner creates/controls jobs. Worker runner/tick records scoped contact and dispatches existing eligible work. Operations returns runner_contact; neither that read model nor a notice grants action authority. No new renderer worker-execution route is exposed.


## Build-job coding mode - 2026-10-16

POST /v1/projects/{project}/build-jobs accepts optional mode: repair | feature, default repair. Unknown modes are rejected. Mode is bound to request identity, saved configuration and proposal context; changing mode with the same request ID conflicts. No renderer command/path authority is added. Feature mode proceeds after a verified baseline regardless of test exit success; malformed, uncertain or unclean execution cannot trigger generation. Final run still requires passing tests. Completion reason tested_feature_ready_for_review explicitly requires independent feature review. Legacy repair config/digests omit the additive key and retain baseline_passed_no_repair behaviour.

## Reviewed project continuation

Controller-only POST routes: /v1/deliveries/{task}/continuation-preview and /continuation-status accept {name}; /continue accepts {name, expected_registration_sha256, allow_native_execution}. Names use the existing 2..48 lowercase slug contract; extra fields are rejected. Native bridge actions continuation_preview, continuation_status and continue_project map only to these fixed loopback routes and never use the worker credential. Registration emits scaffold.continued once; no source/task execution is implied. Dashboard adds continuation_enabled and continuation_workspaces. Project-library entries add kind and previous_workspace. Existing registration status handles generation names through their original approved specification. No database migration or automatic permission update.

## Coding-history association

BuildJobInput adds optional conversation. The Core verifies same-project ownership and binds it into request identity, including scheduled jobs. Existing null/omitted associations preserve old digests. GET /v1/conversations/{conversation}/coding-history?before=0 is controller-only and returns conversation/project, jobs, next_before, model_context_included=false and automatic_execution=false. The native coding_history action maps only to this fixed GET route; Request.after carries the bounded before cursor. No execution or raw filesystem path is accepted. Schema 15 adds coding_job_links with job/conversation foreign keys and coding_job_conversation index.

## Retrieval context mode

BuildJobInput adds context_mode=selected|retrieve. files permits up to 100 structurally; Core enforces at most 20 for selected mode and 100 for retrieve. Only retrieve is persisted as an additive configuration key, preserving legacy request digests. Scheduled intent includes retrieval mode. The existing guarded read-task contract adds {operation: retrieve, query, paths, profile}. Its content-addressed result includes lexical-v1, selected_snapshot, whole files, candidate input_hashes, omitted reasons, query_sha256 and profile_sha256. No new route, renderer command, model-selected tool or database migration. Linked coding-history cycles add optional context_task. Proposal context records retrieval provenance, which is checked against current files/profile before model dispatch and acceptance.


## Explicit history context contract

POST /v1/conversations/{conversation}/model-turns accepts optional strict boolean include_coding_history (default false). True binds the request identity to coding-history-v1 and captures up to three linked jobs in context.coding_history={snapshot,sha256}. The snapshot is capped at 32,000 canonical JSON bytes; each goal is limited to 1,000 characters with goal_truncated and goal_sha256. Existing pagination/detail-limit markers are retained. Same request IDs return the original snapshot, not a fresh read; toggling inclusion with the same ID conflicts. Context remains within the existing whole-turn byte limit, may omit older message records, and grants no actions. Controller ownership checks and model-call deduplication remain unchanged. No new route, bridge action, event kind or schema version.

## Host-bound edit protocol and validation diagnostics â€” 2026-10-19

ProposalInput and BuildJobInput accept edit_protocol: legacy-v1 | host-bound-v2, default legacy-v1. Unknown values fail validation. The selected protocol participates in request identity and scheduled intent. New desktop build requests explicitly use host-bound-v2; existing callers retain their digest/config shape. Provider schema for version two is path/old/new; accepted review responses remain path/expected_sha256/old/new with host-attached preconditions. No new endpoint or renderer execution authority.

Failed proposal/model-turn reads add nullable validation_failure from safe enums (for example patch_shape, patch_hash_mismatch, patch_old_text_mismatch, invalid_json). Events use repair_proposal.validation_<code> or model_turn.validation_<code>; public error stays invalid_model_response. Codes reveal no raw response, private exception text or credentials. Existing budgets, status transitions and ownership checks remain authoritative.

## Configured thinking and usage metadata â€” 2026-10-19

Trusted runtime provider entries may add thinking_level (currently verified only for Gemini gemini-3.5-flash-lite). Omitted entries retain existing behavior. Proposal/model-turn context adds generation={thinking_level:...} only when configured; request identity/freshness and job bindings include it. No model/renderer-supplied permission field or new execution route. Usage may include nonnegative bounded integer reasoning_tokens alongside input/output/total counts. Public validation_failure adds patch_no_change, separating unchanged edits from non-unique/missing old text. Raw invalid output remains excluded from production storage.

## Dashboard activity snapshot â€” 2026-10-19

GET /v1/projects/{project}/dashboard adds an optional activity object from an owned consistent read, using source=core-state-v1 and captured_at. Counts: testing, coding, inspecting, stopping, blocked, coding_requests, planning_requests, chat_requests, approvals, reviews, queued and paused. Expired leases do not signal live execution; model requests are pending, not health evidence. Reads expose counts only. No new route, database table, permission or renderer action. The frontend falls back to unavailable activity when connecting to an older host or foreign-project snapshot.

## Expected guidance revisions â€” 2026-10-19

BuildJobInput and ProposalInput add optional expected_skills: a maximum-five name/hash map. Null/omission preserves legacy request identity. A provided map must exactly cover selected names; malformed maps fail validation and stale hashes conflict. Build jobs persist skill_bindings and recheck before steps/acceptance. Scheduled idempotency binds the requested map. No migration, extra resource grants or execution endpoint. The desktop submits explicit observed hashes, including an empty map for no guidance.

## Explicit failed-generation recovery

Controller POST /v1/build-jobs/{job}/retry-generation accepts only proposal, context_sha256 and allow_model_call=true (actual boolean; numeric aliases rejected). Host unattended enablement and configured runtime are required. Native fixed controller action retry_build_generation uses this route; no renderer worker credential or arbitrary route is introduced. The action schedules a new cycle without making a provider call. An identical failed-proposal/context request recovers its existing result; changed context conflicts. Original budgets and failed attempt records remain. Event: build_job.generation_retry_requested.

Only invalid_model_response, provider_output_limit, provider_http_429 and provider_http_503 may enter reviewed recovery, subject to current evidence/configuration checks. Proposal/model-turn error codes also distinguish provider_incomplete_response. Valid reported usage is retained for incomplete responses; response stays null. Build-job summaries include allowlisted validation_failure when available. No model request is automatically replayed.

## TypeScript scaffold metadata

Scaffold template input additionally accepts typescript-json-function-v1. Executables/toolchain paths remain trusted host configuration and are rejected as extra renderer fields. Setup scaffolds adds templates, node_toolchain_configured and node_toolchain_status (configured/not_configured/requires_review). Missing or invalid host configuration denies new TypeScript creation. Existing preview/create/status/register/continue routes and native actions are reused.

Legacy plans keep python_sha256. Node plans/registrations use executable_sha256 and runtime.kind=node-typescript-v1 with six toolchain path/hash/version fields. Compiler identity is restored and verified alongside Node; no new database table. Creation remains unimplemented with registration_draft.execution.owner_enabled=false. Numeric examples for this template are finite and bounded to the safe JavaScript range.

## Existing-project API

Controller-only specification routes under /v1/specifications/{spec}/existing-projects: POST preview, admit, status, registration-preview and register. Preview/admit require the current approved specification hash plus source (logical host slug), snapshot name, files and create_paths; admit also binds expected_plan_sha256. Status binds name and expected_plan_sha256 without replaying admission. Registration uses the shared exact plan/registration hashes and explicit native consent. Unknown request fields, including renderer filesystem roots or commands, are rejected. Source roots and profiles are private host configuration only. project.admitted records a successful admission observation; registration currently retains the existing scaffold.registered event for storage compatibility. Setup adds existing_projects available/status/sources/registration_sources. No schema migration.

## Existing-project routes

Controller-only POST routes under /v1/specifications/{spec}/existing-projects are preview, admit, status, registration-preview and register. Preview/admit bind current approved specification hash, logical source, name, files and create_paths; admit also requires expected_plan_sha256. Status binds name and expected_plan_sha256 without replaying admission. Registration binds the exact plan and registration hashes and explicit native consent. Request bodies cannot provide root paths or commands. Setup adds existing_projects available/status/sources/registration_sources. project.admitted records successful admission observation; registration retains the existing scaffold.registered event for compatibility. No schema change.

## Bounded inspection tool API

POST /v1/projects/{project}/inspection/preview accepts resource, profile and 1-4 requests. Supported request objects: {operation:inventory}, {operation:search,query}, {operation:read_lines,path,start,count}. Search is literal and bounded to 256 characters; line count is 1-200, and absent/unselected files are rejected. Additional fields and commands are invalid.

POST prepare/step/results accept the exact returned plan plus expected_sha256. Preparation creates one idempotent read task. Step performs that task or recovers completed evidence; cancelled/running/uncertain tasks require existing explicit recovery. Results are available only while input/profile identity and current ownership/grants still match. Controller and project-scoped agent roles may use the port; worker role is rejected. Existing task.created/started/succeeded events and evidence are reused. No model calls or source writes occur.


## Explicit coding conversation contract

POST /v1/conversations/{conversation}/coding-commands accepts exactly connection_id, goal (1..8000 characters, nonblank) and request_id (1..256). Response schema_version=1 includes conversation_id, current task projection, request_message_id and receipt_message_id. Submission requires the exact approved controller/coding_agent credential; no authority overrides. POST .../coding-command-request accepts connection_id/request_id and returns command or null for restart reconciliation.

POST /v1/conversations/{conversation}/coding-tasks/{task}/observe records/reuses a status observation; POST the same prefix with /cancel requests cancellation and records actual state. Both return schema_version, conversation_id, task and status_message_id. Observe is not GET because it writes transcript provenance. Repeated cancellation leaves completed work completed and preserves pending control=cancel on running work. Missing optional capability returns unavailable; disabled execution rejects submission. Conversation commands do not launch a runner or invoke a model.

Structured tool messages use coding.request, coding.submitted and coding.observed with schema_version=1, linked to canonical messages/build/delegation records and existing message.appended/job events. Immutable acknowledgment is not delivery evidence. Capabilities report conversation_commands and natural_language_dispatch=false. The current native composer and ordinary model replies do not dispatch automatically.


## Conversational intent withdrawal and direct client metadata

POST /v1/conversations/{conversation}/coding-command-withdraw accepts connection_id/request_id, authenticated as the exact connection controller/coding_agent. It serializes with admission. If a command already exists it returns withdrawn=false and its original command receipt without cancellation/refund. Otherwise it returns withdrawn=true, command=null and message_id after persisting coding.withdrawn in the existing message table; delayed conversational submissions under that intent conflict. Repeated withdrawal is stable. Credentials/session/project scope remain enforced, including inactive connection inspection. No database version beyond 16 is required.

Coding connection projections now include credential_matches, an identity/role match flag rather than any secret/digest. The separate desktop filters this flag plus active state, expiry and capacity; backend binding and policy checks remain authoritative. Its native gateway permits catalogue/history, scoped coding commands, exact proposal acceptance and exact pending-action decisions, with no arbitrary task/process/policy/connection-creation route exposed to the renderer.


## Read-only coding workspace catalogue
Owner-controller only: POST /v1/coding-workspaces/preview(directory,name), POST /v1/coding-workspaces/register(directory,name,expected_sha256,request_id), GET /v1/projects/{project}/coding-workspace. Optional coding service package required. Registration is metadata-only and creates a read_only project with empty resources, atomically with a folder bookmark, workspace.registered event and owner-bound idempotency record. Schema 17 adds coding_workspaces and coding_workspace_requests; no existing session/job tables are replaced. Existing direct execution/source-admission APIs retain their separate permissions. See ARCHITECTURE.md for exact storage and recovery semantics.


## Owner connection onboarding API
The reusable owner_setup module wraps the canonical DelegationService. GET /v1/projects/{project}/coding-setup returns only that owner's policy-authorized host scopes, their selected paths/protected profile names, and configured provider/model names. POST .../preview validates the same canonical template checks as connection creation and returns the exact test profile/command, provider settings, selected content hashes, policy version, immutable binding, expiry and total call budget. No source contents or credential digests are returned. Review SHA-256 additionally binds the hidden native credential identity/role. POST .../confirm accepts the original input, expected_sha256 and stable request_id, revalidates under the existing transaction and creates a normal coding_connections record bound only to the authenticated controller. A different token of the same owner cannot reuse the review. No policy/resource/delegate changes can be supplied by this interface. Source changes between review/confirmation require another review; subsequent tasks use the approved logical context and existing engine bindings, not a permanently frozen unprotected source hash.

POST .../request recovers a connection by owner-setup request identity, requiring exact credential/project scope. POST .../withdraw serializes with confirmation and either returns an already admitted connection unchanged or writes an immutable coding_setup.withdrawn event whose subject hashes credential, role, project and request identity. A delayed confirm conflicts after withdrawal. Withdrawal does not revoke admitted access, cancel work, refund reservations or create a connection. The canonical event is an authority tombstone, not an external diagnostic log; future event retention must preserve these tombstones or migrate them to an equivalent durable intent table. No schema beyond 17 is introduced.

Native IPC permits these dedicated owner endpoints while generic policy mutation, arbitrary connection/delegate creation, arbitrary process requests and provider chat remain blocked. Renderer state has no credential value. The UI stores reviewed metadata/input/request identity before confirmation, looks up the original request on recovery, refreshes the canonical project catalogue before clearing local intent and offers server-backed withdrawal. Corrupt journals block replacement. Host-configured source admission and project permissions remain separate requirements.


## Reviewed source preparation and schema 18
SourceSetup reuses the existing skyra_coding.admission.ProjectAdmission and Workspace snapshot/baseline engine. The source directory comes only from the owner-owned coding_workspaces bookmark; folder identity and ancestry are revalidated on each operation. The renderer supplies only 1..20 relative existing file paths, a nonempty protected subset and bounded stable request identity. Existing engine boundaries reject traversal, symlinks/reparse points, linked files, generated/internal paths, private key/database types, oversized/non-UTF-8 inputs and .env paths. Preparation additionally rejects common private application credential directories/files. No contents are returned to the renderer or a provider; review carries hashes and metadata. Protected paths here are owner selection metadata, not proof that a test command ran.

Canonical SQLite migration 17 -> 18 adds coding_source_preparations(project FK, request_id, reviewed digest, immutable plan/config JSON, state, created; composite primary key project/request_id). Existing folder, session, chat, job and grant data remain in place. States are preparing, prepared and withdrawn. A durable preparing record/event commits before filesystem materialization. Snapshots live under the host database parent's coding-source-preparations directory, outside the selected source; deterministic generated names bind project/request identity. Host-state ancestry and source separation are checked before creation. Preview may initialize that empty private state directory, but copies no source until confirmation.

POST /v1/projects/{project}/source-setup/preview returns versioned selected hashes/identity/flags and a SHA-256 review. POST .../prepare rechecks the review, reserves durable identity and invokes canonical materialize. POST .../request returns actual preparation state and validates manifest/baseline plus current source freshness. GET .../source-setup lists at most 20 saved metadata records. POST .../withdraw seals an unstarted identity as withdrawn; delayed preparation conflicts. Already started/prepared work is recovered without deletion. All endpoints require the owner controller; coding_agent/worker credentials cannot prepare arbitrary folders.

A completed on-disk admission can finalize after a crash. A durable request with no output can safely retry the identical reviewed selection. Partial existing output is retained and marked reconciliation-required; there is no blind overwrite, automatic cleanup or reuse. Canonical snapshot integrity and current-source freshness are reported separately. Later source edits do not destroy the prepared baseline. Confirmation/preparation never changes project resources/mode, approves a runtime command, creates model-call grants or starts tasks. No fake LLM specification/model turn is created to bypass existing execution-registration requirements.

The shared SourceSetupClient and standalone desktop use native IPC with an explicit path allowlist. The UI journals the original reviewed selection before preparation, supports lookup/retry/withdrawal and retains saved history. Editing a selection invalidates review. Corrupt local journals fail closed. Newly selected folders still need reviewed executable/profile/test-command binding, project policy and a coding connection before they can execute.


## Runtime activation, schema 19 and scoped runner discovery
ActivationRegistry consumes a fresh prepared-source receipt and reuses ScaffoldRegistry's canonical candidate validation/publication, NativeExecutor, FileWorker, protected profiles, executable identity checks, toolchain binding and delivery-boundary machinery. Existing registries and prepared-source activation share the FileWorker registration lock; no models/tests execute under that publication lock. No second coding engine or alternate task database is introduced. Restore allows legitimate unprotected working edits while preserving immutable baseline/protected-test checks. Preparation status now distinguishes activated working changes from protected/baseline corruption.

Runtime catalogue entries derive from configured, owner-enabled native profile executables named python.exe/python3.exe/node.exe. Executable hashes and preset IDs are reviewed; the renderer cannot send an arbitrary path/argv. Python uses an isolated host-owned bootstrap that imports stdlib unittest before adding the snapshot root; selected .py paths must be importable names. Node uses --test --test-reporter=spec -- followed by selected JS/TS test paths, preventing option injection. These presets do not provision third-party dependencies or run Playwright/npm build scripts automatically.

Canonical migration 18 -> 19 adds coding_source_activations(project FK, request identity, preparation identity, owner, exact worker credential digest, review digest, immutable config/checksum, state, created; unique project/preparation) and a worker/owner/state index. Existing preparations, folders, chats, jobs and grants remain intact. Config records point to the original prepared snapshot, selected files, protected paths, exact preset argv, timeout, primary executable hash and source/delivery boundary. No fake model turn/specification is manufactured.

GET /v1/projects/{project}/source-activation returns scoped trusted runtimes, opaque worker choices and saved activation metadata. POST .../preview binds current source/preparation/manifest, executable, test preset, timeout, current policy version/resources, requested ask/full mode and exact worker selection to the hidden owner credential. POST .../confirm requires explicit native-execution consent and the exact review hash, then atomically records registration and updates policy with the new workspace resource only, preserving existing resources. The original source/delivery resource is not granted. Runtime publication follows commit and status distinguishes active from reconciliation-required. Identical request recovery does not regrant permissions or bump the policy version. POST .../request recovers actual status. POST .../withdraw blocks late unconfirmed approval with an immutable credential-bound coding_activation.withdrawn event, or returns already admitted access unchanged; it does not revoke existing grants. Authority tombstones must survive future event retention.

The owner-approved record also binds one configured worker credential of the same actor. GET /v1/runner/projects (worker only) returns its owned static scopes plus only projects approved for that exact token. Worker project_scope checks the same records before runner/tick; other same-owner workers gain no access. Renderer IPC cannot invoke worker discovery/tick or mutate generic credentials/policy. The hidden runner refreshes this read-only catalogue, validates IDs/count <=100, retains its last explicit set on transport/parse failure and preserves round-robin position when unchanged. Existing in-flight dispatch stays bounded to four. No auth file or runner configuration is silently broadened; API approval state is canonical. Preview rejects grants exceeding the worker's 100-project bound.

Host native enablement, configured executable/worker credentials and background service remain prerequisites. Activation is trusted Windows-account execution without an OS sandbox. Source remains untouched by coding in the snapshot; delivery/deployment/commits are separate actions. Full independent host packaging, general shell/dependency tools, broader test/build adapters and model-quality evaluation remain incomplete.


### Optional live task observations
`GET /v1/coding-tasks/{task}` includes optional `diagnostics` on compatible hosts. Fields: `observed_at`, `last_progress_at` and `next_due` are finite nonnegative epoch seconds; `runner_state` is `never_seen | recent | in_progress | stale`; `runner_age_seconds` is null or finite nonnegative seconds. Scope checks are identical to the task read. These fields contain no source, prompts, credentials or raw errors. Worker contact is a Core observation, not OS process health. Clients must support older task responses without diagnostics.

Changing diagnostics are deliberately excluded from submit/lookup/cancel receipts and durable conversation observations. Stable request identities still deduplicate commands and model-call reservations. A refresh does not create work, claim a lease, grant model calls or renew approvals.


### Source delivery handoff
Owner-controller routes: `GET /v1/coding-tasks/{task}/source-delivery` lists run-bound registered targets and canonical receipts. `POST .../preview` takes `{target}` and returns a fingerprinted review with destination, mode, policy version, source-grant consequence and canonical diff. `POST .../confirm` takes `{target, expected_sha256, request_id}` (request ID 1..128 characters), returning a canonical delivery receipt. `POST .../request` and `POST .../withdraw` take `{request_id}` and return `{delivery: receipt | null}`. A null withdrawal is durable and blocks delayed confirmation of that intent. An admitted withdrawal returns the existing task and is not cancellation.

The worker-only existing `/v1/runner/tick` may return `delivery` in addition to its coding/assignment result. Generic policy mutation, source filesystem access and `/v1/deliveries/{task}/advance` remain forbidden to the standalone renderer. Unknown routes and query expansions remain rejected. No new credential scopes or schema version are introduced.


## Coding desktop history adapter - 2026-10-25
The shared Core host adds GET /v1/conversations/{conversation}/message-page with bounded before(default0)/limit(default20,max50), backed by skyra_coding_service.history. Existing controller/agent ownership and project scope checks apply; missing coding service503, invalid cursor/input422. Response messages are chronological with has_more and exclusive next_before (0 when exhausted). Only existing canonical messages are read; no migration/task admission/provider call. Existing /messages after/limit behaviour is unchanged. Implementation and desktop acceptance are documented in skyra-coding-agent/docs/07_API_AND_EVENTS.md.


## Coding chat metadata adapter - 2026-10-25
Core schema20 preserves canonical messages and adds coding_chat_metadata, coding_chat_requests and a conversation/message paging index. Owner-controller POST /v1/projects/{project}/chat-catalog provides bounded title search; POST /v1/conversations/{conversation}/chat-metadata applies revision-checked, idempotent rename/pin/archive edits through skyra_coding_service.chats. Metadata edits never modify execution permissions/tasks or delete messages. Detailed contracts and acceptance evidence live in skyra-coding-agent/docs/07_API_AND_EVENTS.md and06_PROJECT_MEMORY.md. Upgrade the shared host alongside the desktop; retain a private SQLite backup before upgrading an existing workbench.

## Read-only message search and context routes — 2026-10-25

- `POST /v1/projects/{project}/message-search`: `{query:string(1..120 code points),include_archived?:boolean=false,include_tools?:boolean=false,before?:safeInteger=0,snapshot?:safeInteger=0,limit?:integer(1..50)=20}`. Returns `{project_id,query,snapshot,results,has_more,next_before}`. Each result has `conversation_id,message_id,role,title,archived,snippet`. IDs descend within the project-bound snapshot. Continuation uses the returned snapshot and exclusive before cursor. Native dispatch retains POST while treating this as a read, with no mutation-uncertainty classification.
- `GET /v1/conversations/{conversation}/message-window?message={positiveSafeId}&limit={1..50}`: bounded contiguous message page plus `project_id,conversation_id,anchor_id,has_newer`. The exact anchor must belong to the authorized conversation. Existing older-page cursor semantics are retained.
- `GET /v1/projects/{project}/chats/{conversation}`: `{project_id,chat}` using the existing metadata projection; the conversation must belong to that owned project.

All routes require controller authorization and project ownership. They emit no transcript/task events and do not grant execution permission. Results are validated again in the TypeScript client for scope, types, ordering, snapshot/cursors and anchor presence. Search does not consume provider reservations. Canonical schema remains20.
