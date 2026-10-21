# Jarvis â€” Functionality

Last maintained: 2026-10-19. This is the canonical project requirement/capability reference. Current implementation and planned work are explicitly distinguished.

## Product and users

An internal, persistent coordinator that turns owner requests into versioned plans, delegated tasks, verified deliverables and reviewable incident fixes. Runs on Windows first; supports remote workers and future hosted operation through explicit migration.

Users: Skyra owner and authorized employees; service consumers act under scoped user/project/account identity. Commercial products stay independent of internal Jarvis privileges.

## Current implementation

Implemented: scoped durable Core, selected-file repair and feature jobs, trusted native tests, hidden bounded/scheduled execution, reviewed source delivery and snapshot generations, native multi-window controls, stored chat/planning/specifications, project-library recovery and optional conversation-linked coding history. Broader repository/tool selection, semantic memory/compaction, installer/update delivery and mobile pairing remain pending. Regression verification and final packaged acceptance are recorded in DEVELOPMENT.md.

## Required capabilities

- Isolated projects, conversations, branches and versioned project specifications
- Plan-only workflow generating the appropriate project documents before an explicit build instruction
- Persistent task graphs with delegation, checkpoints, cancellation, restart reconciliation and acceptance evidence
- Configurable read-only, ask, selected-actions, scoped full-access and custom permission policies
- Memory Centre for explicit teachings, provenance, revisions, conflict handling and forgetting
- Skills and capability discovery, online model routing and MCP client integration
- Mobile commands and approvals through Telegram first; dedicated mobile interface after platform decision
- Technical and business incident playbooks; known local rules work without model connectivity

## Implemented capability matrix

| Area | Available behavior | Limit |
|---|---|---|
| Projects/conversations | Owner-scoped durable state, separate histories, idempotent messages | Native note/chat/plan UI implemented; employee roles remain pending. |
| Permissions | Controller/agent/worker credentials; read-only/ask/scoped full; exact approvals | Exact grants and DPAPI desktop credentials implemented; richer custom policies remain pending. |
| File work | Read/search/patch/create/diff on selected snapshots; separately reviewed source delivery | Host-registered targets and verified tests required; no Git branch/revision delivery or automatic recovery. |
| Native tests | Fixed owner-enabled profiles, real outputs, timeout/cancel/ordinary child cleanup | Trusted code runs with Windows account access. |
| Repair runs | Controller plan, baseline failure, approved patch, protected retest, diff/evidence | Gemini/Groq proposals now feed reviewed runs; general autonomous building remains pending. |
| Mobile/voice | Legacy Telegram/voice prototype | New authenticated core/desktop is not wired to it. |
| Persistent teaching | Legacy memory prototype | Curated teaching revisions, provenance and deletion are planned. |

## Jarvis Windows Desktop requirements

- Installable Windows application with system tray, explicit Quit and optional sign-in autostart
- No visible console windows for background runtime, worker, update or recovery launches
- Subsystem canvas showing capabilities, connection readiness and permission scope
- Live runs with task dependencies, artifacts, evidence and drill-down diagnostics
- Conversation browser, Memory Centre, approvals inbox and incident timeline
- Pairing and management of mobile clients; visible online/offline status
- Accessible keyboard navigation and a list alternative to the canvas
- Restart/reconnect without duplicated commands or lost pending user input

## Skyra Agent Runtime requirements

- Versioned SKILL.md packages with required tools, resources and acceptance checks
- Progressive loading of skill metadata and task-relevant content
- Online model adapters for tool calling, structured output, vision and streaming
- Persistent agent checkpoints and resumable task execution
- Scoped child-task delegation with bounded concurrency and cancellation
- Explicit planning/review/verification roles with shared task contracts
- Token/cost accounting and capability-compatible provider fallback
- Evaluation datasets for tool selection, permissions, recovery and completion claims

## Skyra Coding Worker requirements

- Repository registration and isolated workspaces per run
- Read/search/edit/patch capabilities restricted to granted workspaces
- Explicit branch/base revision and selected-file change delivery
- Process supervision, timeouts, cancellation and process-tree cleanup
- Build/test execution with captured outputs and resource metrics
- Structured diffs, test artifacts and reproducible environment manifests
- Separate release/deployment actions governed by policy

## Implemented local API

Task payload operations: `read(path)`, literal `search(query)`, `patch(path, expected_sha256, old, new)`, `diff`, static `verify`, and configured `test(profile)`. Operation/action consistency is enforced (`read`, `write`, `execute`). Profiles cannot be replaced with model-supplied shell strings. Messages, tasks and repair-run creation require request IDs in their current API schemas. Unknown fields and coerced values are rejected.

Repair-run creation requires `resource`, `profile`, `request_id` and 1â€“10 patches with `path`, `expected_sha256`, `old`, `new`. It is controller-only. Worker advance processes one step, preserves approval pauses and uses exact task-bound evidence. Statuses include planned/running/waiting approval/blocked/failed/cancelled/ready for review. Project/conversation creation still lacks request deduplication; clients must not blindly retry an unknown creation outcome.

All routes require authenticated local clients; role/scope rules are in architecture.

| Method | Route |
|---|---|
| GET | `/v1/health` |
| GET | `/v1/openapi.json` |
| POST | `/v1/projects` |
| GET | `/v1/projects` |
| PUT | `/v1/projects/{project}/policy` |
| POST | `/v1/projects/{project}/conversations` |
| POST | `/v1/conversations/{conversation}/messages` |
| GET | `/v1/conversations/{conversation}/messages` |
| POST | `/v1/projects/{project}/tasks` |
| GET | `/v1/tasks/{task}` |
| POST | `/v1/tasks/{task}/start` |
| POST | `/v1/tasks/{task}/heartbeat` |
| POST | `/v1/tasks/{task}/perform` |
| GET | `/v1/workers/capabilities` |
| POST | `/v1/projects/{project}/coding-runs` |
| GET | `/v1/projects/{project}/coding-runs` |
| GET | `/v1/coding-runs/{run}` |
| POST | `/v1/coding-runs/{run}/advance` |
| POST | `/v1/coding-runs/{run}/cancel` |
| GET | `/v1/tasks/{task}/evidence/{checksum}` |
| POST | `/v1/tasks/{task}/complete` |
| POST | `/v1/tasks/{task}/cancel` |
| GET | `/v1/approvals/{approval}` |
| POST | `/v1/approvals/{approval}/decision` |
| POST | `/v1/projects/{project}/recover` |
| POST | `/v1/tasks/{task}/reconcile` |
| GET | `/v1/projects/{project}/events` |

Core developer input schemas live in `services/core/src/jarvis_core/api.py`; generated OpenAPI is controller-only at `/v1/openapi.json`. Do not maintain a conflicting handwritten schema.

## Desktop design requirements â€” proposed

Dedicated Jarvis design; do not import Skyra Platform UI. Proposed tokens: background #0B1220, surface #111C2F, raised surface #1B2940, primary text #F3F6FC, secondary text #B9C5D8, accent #75B8FF, success #72D6A0, warning #FFD166, error #FF8F9A. Verify contrast in actual component states before adoption.

Use Segoe UI/system sans for interface and Cascadia Code/system monospace for code. Type sizes: 12 metadata, 14 controls, 16 body, 20 section, 28 page title. Spacing scale: 4/8/12/16/24/32/48 px; 8 px control radius and 12 px panels. Focus rings remain visible; never encode status using color alone.

Primary shell: navigation rail, central subsystem/workflow canvas, inspector, conversation panel and approval inbox. A node shows name, available capability, readiness, current task and permission scope. Edges describe actual dependencies, not decorative activity. Provide zoom, fit, keyboard selection, searchable list alternative, minimap and reduced motion. Inspector exposes evidence/artifacts without exposing credentials.

Approval cards show exact action, target, account, cost/risk when known, expiry and scope. Changed actions require a fresh decision. Destructive decisions cannot be the default focused action. Mobile layouts prioritize approvals, run status and cancellation over editing large graphs.

## Interface direction

## Acceptance requirements

- Two simultaneous conversations cannot read each other's private context
- Restart while waiting for approval preserves the pending action without executing it
- A changed proposed action invalidates an earlier approval
- An interrupted external operation is reconciled before a retry
- Plan mode does not begin implementation; build mode binds to a reviewed specification version
- A taught fact can be inspected, revised and forgotten, including its derived search entries
- A disconnected PC is reported unavailable on mobile; jobs are not falsely marked running
- Stopping a workflow cancels descendants and records workers that did not acknowledge

## Explicit boundaries and open decisions

- Mobile OS and companion-app approach are unconfirmed
- Production-release policies and per-project budgets require configuration
- Existing memory data needs an explicit non-destructive migration/export plan

A proposal, simulation or passing build does not authorize production release. Account connection, publication, money movement and employee/payroll actions obey their configured permission policies.

## Initial specification set

Retain and update the original nine documents. They describe product requirements, system architecture, development rules, design, tasks, memory, API/events, testing/acceptance and security/operations. These current overview files supplement them; they do not replace them.

- [Product requirements](01_PRODUCT_REQUIREMENTS.md)
- [System architecture](02_SYSTEM_ARCHITECTURE.md)
- [Development rules](03_DEVELOPMENT_RULES.md)
- [Design system](04_DESIGN_SYSTEM.md)
- [Project tasks](05_PROJECT_TASKS.md)
- [Project memory](06_PROJECT_MEMORY.md)
- [API and event contracts](07_API_AND_EVENTS.md)
- [Testing and acceptance](08_TESTING_AND_ACCEPTANCE.md)
- [Security and operations](09_SECURITY_AND_OPERATIONS.md)

## Implemented model repair proposals

Controller creates a proposal with `resource`, `profile`, configured `provider` alias, `goal`, explicit `files`, optional selected `skills`, and `request_id`. Creation snapshots context without contacting a provider. Generation is a separate explicit online action. Review shows the proposal, context checksum, model, token counts and errors. Acceptance creates a coding run; it does not start tests or authorize later tasks. Agent credentials can read an owned, explicitly scoped proposal but cannot create/export it, call models, accept it or interrupt it. Worker credentials cannot read proposal source through these routes. Disabled runtime returns 503 for proposal routes.

| Method | Route | Authority |
|---|---|---|
| GET | `/v1/runtime/capabilities` | Controller |
| POST | `/v1/projects/{project}/repair-proposals` | Controller |
| GET | `/v1/repair-proposals/{proposal}` | Controller / project-scoped agent |
| POST | `/v1/repair-proposals/{proposal}/generate` | Controller |
| POST | `/v1/repair-proposals/{proposal}/accept` | Controller |
| POST | `/v1/repair-proposals/{proposal}/interrupt` | Controller |

The generated-fixture demo is `packages/agent-runtime/live_demo.py`. It requires `--allow-live-call`, an explicit provider/model/key environment name and a new output directory. It auto-accepts only its own tiny generated fixture and writes JSON/SQLite evidence under the chosen runtime directory. It must not be treated as a production unattended approval policy. Production source and Git are untouched. The native desktop includes proposal review and acceptance.

## Windows desktop control slice

- System map with selectable subsystem nodes, minimap/zoom/fit and an accessible list alternative. Only implemented core/worker/runtime links are drawn; Google, messaging, social, media, browser/vision and quality/incidents remain labelled planned.
- Project selection and creation; owner permission dialog for read-only, ask and full within exact resources, with reviewed-version conflict checks. Host workspace paths/commands are not editable in the renderer.
- Prepare selected-file proposals, review context/protected files/skills/patches/usage, explicitly generate online, accept into runs or interrupt. Generation has no automatic retry/fallback.
- Inspect coding checkpoints, advance one worker step, cancel independently of an active request and fetch task-bound evidence. Approval inbox shows exact payload, target, policy version and expiry with separate reject/approve actions.
- Stored conversation history and user messages with request IDs and paged reads. Explicit model chat and draft plans are now connected; teaching-memory governance remains pending.
- Recent event view, disconnection/errors/empty states, keyboard modal focus and responsive narrow Windows layout. Close-to-tray and single-instance restoration are native host responsibilities.

New controller route: `GET /v1/projects/{project}/dashboard`. Optional `expected_version` on policy PUT preserves compatibility with existing controller clients; desktop supplies it. Discovery returns registered logical resource IDs to the owner, then actual selected filenames only after a resource grant. This view adds no tables and does not probe optional service URLs or spend provider tokens.

Desktop scripts and private startup configuration are described in [desktop README](../apps/desktop/README.md). Production delivery still needs trusted configuration editing, packaged backend/installer, signed updates, mobile transport and general build workflows.

## Conversation and planning functionality

The desktop Conversations screen defaults to local notes. Ask Jarvis and Create project plan require an explicit configured online provider. Sending creates a durable user-message/turn snapshot, then dispatches that request once. The owner can inspect the saved context and omitted-message count, view usage and safe failures, load previous request details, interrupt an active request or resume a prepared request that was never dispatched. Replies and all plan fields render as text.

Draft plans contain title, overview, requirements, deliverables, ordered phases with tasks and acceptance criteria, risks and questions. They are persisted JSON alongside the assistant reply; this slice does not write specification files into a client repository or start a coding run. Notes, model turns and plans remain separate between project conversations. A worker is not required for chat/planning.

Setup shows connection/project/model/workspace/execution prerequisites and the current provider/model registry. It reads host configuration and makes no provider calls or permission changes. Full editing/provisioning remains future work.

| Method | Route | Behavior |
|---|---|---|
| GET | `/v1/setup` | Controller-only readiness and safe capabilities |
| POST | `/v1/conversations/{conversation}/model-turns` | Persist provider, chat/plan mode, content and request ID |
| GET | `/v1/conversations/{conversation}/model-turns` | Recent 100 request metadata records |
| GET | `/v1/model-turns/{turn}` | Owner-scoped snapshot, response and usage |
| POST | `/v1/model-turns/{turn}/generate` | Claim and dispatch planned request once |
| POST | `/v1/model-turns/{turn}/interrupt` | Terminal interruption; suppress late output |

## Flexible 3D workspace

Implemented: interactive orbital Jarvis core, separate core/map panels, dashboard-card popouts, up to eight tabs in each native window, tab minimization/restoration/reordering/closure, Ctrl+T/Ctrl+W and arrow/Home/End tab navigation. Focus layout hides the sidebar/rail. The top workspace controls remain reachable as the dashboard scrolls within the window.

Open current panel in new window and card shortcuts create independent Windows panels that can be moved across monitors, snapped, resized, minimized, maximized and fullscreened (F11 or the toolbar). Arrange includes explicit logical width/height, Show all windows, Save window arrangement and Restore window arrangement. Up to eight additional windows are supported. Layout restoration checks disconnected-monitor positions and moves otherwise unreachable saved windows onto a connected monitor.

These actions change presentation only. They do not grant permission, retry generation, approve actions or cancel tasks. Tabs preserve unsaved conversation drafts while switching/minimizing in the same session; only layout metadata persists after restart. Browser preview explains that native windows require the Windows app. Named layout profiles and full internal docking remain pending.


## Reviewed specifications - 2026-10-15

In Conversations, select a completed project plan and choose Save specification version. Inspect the four fixed Markdown documents, then choose Approve reviewed specification. Version history is project-wide and survives restart. In Repair proposals, choose New proposal and optionally select an approved specification; select explicit workspace/files/provider/profile and prepare context as usual. Its documents are included in the model context and its approval must still be current at generation and acceptance. Specification approval does not start coding, run tests or grant permissions. Architecture/design authoring, export to project folders and general new-file building remain pending.


## Owner revisions and export - 2026-10-15

Choose a specification and Edit as new revision. Edit the Markdown text, optionally add any missing standard document, then Save revised draft. Conflicts retain the unsaved editor contents. Each revision preserves its parent and requires separate review/approval. Export approved documents writes exact Markdown plus a provenance manifest to a dedicated version folder in Documents/Skyra/Jarvis/exports (or your configured export root), and displays the location. Repeating an export verifies existing bytes; external changes cause rejection without overwrite. No model call, source write, coding run or permission grant is triggered. Export is native-app only; visual preview writes no files.


## New-file coding additions - 2026-10-15

Prepare a trusted snapshot with existing protected tests and explicit --create target paths. Register it as usual, select those targets in the proposal dialog and review New file target plus the full generated content. Accepting creates a durable coding run; the current ask/full/read-only resource policy governs every step. The run expects a failing protected baseline before creating files, then a passing retest and additions diff. Generated content initially stays in the snapshot. Empty-project scaffolding, autonomous test authoring and repeated debugging remain pending.

## Reviewed source delivery

For a completed coding run, select a separately registered/granted source target, choose Review source delivery, inspect the manifest checksum and changes, then Prepare reviewed delivery. Advance requests any required exact-action source approval; approve in Approvals and advance again. Inspect delivery evidence for its outcome. A conflicting source or changed tested snapshot blocks the operation. Partial multi-file effects require manual reconciliation using the recovery journal and saved originals; no automatic rollback is promised. The feature does not stage, commit, push or deploy.

## Unattended assignments

The Assignments view queues an existing accepted coding run with a goal label, 1â€“100 step budget and 1-minute to 7-day duration. The separate hidden runner advances one authorized step per claim; ask mode pauses for approval and full mode uses current resource grants. The owner can pause/resume/cancel, inspect persistent state and expand its progress/evidence summary. Only one assignment claim runs per project. Current executor stops at ready_for_review; it does not generate paid model requests or perform source delivery. The time limit is checked between bounded steps; unknown interrupted attempts retain a reserved slot and require review. Core enablement and process health are distinguished. Background launch/setup/stop instructions are in [desktop README](../apps/desktop/README.md#hidden-unattended-assignments).

General goal-to-plan-to-scaffold loops, currency budgets, morning notifications, scheduled start times and remote/mobile execution remain future work. Bounded model/test repair cycles are implemented below. Existing source-delivery review, no-stage/no-commit/no-push and production approval boundaries still apply.

## Model-backed repair cycles

Build jobs now provide bounded iterative repair of a registered snapshot with pre-existing protected tests. Choose a goal, provider, profile, files/skills, optional approved specification and explicit model-call consent. A verified failing baseline precedes generation; passing baseline uses no model call. Each generated proposal is reviewed unless the job explicitly allows automatic acceptance under current full policy. Accepted repairs use the existing coding workflow. A verified failed retest can start a new cycle with current files and bounded task-bound diagnostics, preserving earlier attempts.

The UI provides budgets, context selection, consent, proposal diff/checksums, pause/resume/cancel and current progress summaries. Full cycle history is available in job detail API. Accepted-run assignments remain supported separately; both use one project dispatch slot in the hidden runner. Call reservations are durable and not refunded after unknown/failed outcomes. A saved ready response can be resumed without repeating generation. Currency limits, generic tool planning, new empty-project scaffolds and autonomous protected-test creation remain pending. Source delivery and production release remain separate.

## Approved specification to new-project foundation - 2026-10-15

Implemented host workflow: review an approved specification plus owner-defined input/output examples; inspect the complete file plan and checksum; create a new Python JSON-function project; register the prepared isolated snapshot/profile through trusted configuration; use Build jobs for implementation/test/debug; separately review source delivery. Preview/application never enables a provider, native execution or policy grant automatically. The first project contains all nine initial documents, distinguishing approved content from host defaults.

The owner command supports review/create with exact checksum binding and refuses changed plans, changed interpreter bytes, unapproved/tampered specifications, protected paths, linked parent directories and existing destinations. A created stub is unimplemented and intentionally fails protected acceptance tests. The function template and integrated website/HTTP template below are bounded host templates, not arbitrary framework generators. Only the reviewed examples are tested; independent broader quality/security checks remain necessary work.

## Desktop specification-to-scaffold flow - 2026-10-15

Open Conversations, select an approved specification and expand New project scaffold. Enter an unused lowercase project slug and an owner-authored JSON cases contract matching the requirements. Preview every file, destination, interpreter/profile and document provenance, then explicitly confirm review before creating. Changed input discards the previous plan/consent. Choose either the Python JSON-function template or the website/HTTP-service template; both start with intentionally failing protected tests.

The host must explicitly configure an existing private scaffold_root and restart Core. Creation is otherwise disabled with visible setup guidance. The desktop cannot choose arbitrary filesystem roots or executables. After an uncertain create, use Check creation receipt; there is no automatic retry. A missing audit event is visible and requires manual reconciliation. The generated file draft is inert. Continue through the registration, command-consent and resource-permission reviews below; source delivery remains separate.


## Complete specification-to-tested-project workflow - 2026-10-15

After reviewed creation or receipt recovery, expand the integrated project builder. Review the exact durable registration and fixed interpreter/profile, explicitly permit trusted native commands, and register. Host enablement must already exist; a renderer checkbox cannot enable the host. Review workspace/source grants separately and choose ask/full policy with awareness that mode affects the entire project. The grant update rejects stale policy versions. Existing resources are retained.

Queue the scoped Build job with a goal, provider, fresh selected-context consent and bounded budgets. In ask mode review exact proposals/actions; full mode automatic proposal acceptance needs its own explicit opt-in. A wrong repair can fail protected retests and feed another bounded model cycle. Completion exposes the latest tested run. Review and prepare its source delivery, approve the exact source-write action where required, then explicitly advance delivery. Original source remains unchanged until delivery.

The website/HTTP template supports real loopback GET/POST requests and editable HTML. Acceptance examples specify exact response fields; tests also compare the HTML home response to index.html. The fixed server and contract/tests remain protected. The initial stub is not represented as finished. Durable registration and job/delivery history recover without per-project JSON merging or Core restart; damaged metadata is exposed for manual reconciliation. This is a local developer build workflow, not public hosting or a security-certified release.


## Return to unattended work - 2026-10-16

Open Activity to see current jobs/assignments, elapsed deadlines/budgets and a persistent outcome inbox. A notice is a historical snapshot, not a live readiness/deployment guarantee. Inspect the exact run or current approvals before acting. Acknowledge only marks a notice as read and survives restart; repeated identical waits stay quiet. Older outcomes use explicit pagination. The Activity badge shows project unread count.

The Registered project library reopens a saved specification/build/delivery workflow without re-entering scaffold details. It shows host availability, reconciliation and permission state, preserves all existing consent boundaries and never retries creation or delivery. Raw Core events remain available in a collapsed section. No scheduled task, Windows startup/wake behavior, push/email notification or production deployment is configured.


## Schedule trusted work - 2026-10-16

In Build jobs, select a registered workspace/profile/provider and enable Start this job at a future time. Review the local date/time and displayed time zone, late-start minutes and scheduling conditions; changing time/window clears that consent. Review model context/call budgets and optional full-policy automatic acceptance separately, then queue. The card shows planned start/start-by and consumes no dispatch/model-call slots before due. Pausing/resuming preserves the scheduled time; cancellation prevents later dispatch. The runtime duration begins at the planned time.

A missed start fails rather than silently catching up. Changed selected bytes or a superseded/changed approved specification block before the first baseline, including during approval waits; cancel and create a fresh reviewed job. Once admitted, normal approval waits may continue within the runtime deadline. Existing bounded repair, immutable evidence and separately reviewed source delivery remain unchanged. These are one-time schedules; the PC/Core/worker must be running.

Activity now shows recorded worker contact separately from host enablement: never seen, recent, in progress or stale, with last request/result. This does not attest OS process health or guarantee success. Recurrence, wake/login startup, schedule editing, external/mobile notifications and a full overnight soak remain pending.


## Feature-building foundation - 2026-10-16

Build jobs now offers explicit Repair or Feature mode. Feature mode can generate changes after a passing baseline and execute selected multi-file/new-file plans, then require passing retests and reviewable diffs. The UI resets model/automatic-acceptance/schedule consent when mode changes. Existing repair requests keep their behaviour and digest; feature jobs persist through restart and scheduled admission. A completed feature job means tested changes ready for independent review, not proof of complete requirements. General repository tool use, arbitrary path creation, governed dependencies and unified coding sessions remain pending.


### Selected-snapshot inspection tools - 2026-10-16

The coding worker accepts guarded read operations inventory (no arguments) and read_lines (path, start, count). Inventory exposes only manifest-selected paths, logical directories, current hashes, content sizes/line counts and absent creation targets; it explicitly marks source_repository_complete false. It does not traverse the repository. Line reads preserve complete UTF-8 lines and original line endings, with the full file hash, a 1..200 line request, 16 KB content bound and an explicit next_line/truncated response. Oversized individual lines fail explicitly. Unselected paths, credential paths, absent file reads and revoked resource grants remain denied. Both operations create durable content-addressed task evidence. These are worker primitives for the future model tool loop, not automatic repository retrieval or a new desktop explorer.


The dashboard refreshes on active-view changes, focus and visibility recovery, with overlapping timer polls suppressed. Approvals includes an explicit Refresh approvals read action so native timer throttling does not leave users dependent on a cached inbox. Backend expiry/digest/policy checks remain authoritative. The coding goal editor fills its form width and uses feature-neutral labels.

The coding configuration disclosure now retains its own open/closed state across background history refreshes and closes after a successful queue action, preserving the owner's editing intent.

## Continue a delivered registered project

After a successful reviewed delivery, review and register a fresh snapshot generation from the matching selected source files. Historical runs, snapshots and diff evidence remain available. The new generation appears in the registered project library and uses the existing protected test profile. It receives no automatic resource grants or model consent. A changed generation name clears review and consent; Check generation status recovers an uncertain registration without replay. Source edits, incomplete directories, changed evidence or missing grants block continuation. Manually configured, nonregistered source targets do not expose this flow. Broader repository discovery and unified conversational coding sessions remain separate pending work.

## Linked coding work in conversations

A new build job can optionally link to a conversation in its project. That conversation can display recorded goals/status, reserved calls/steps, each test cycle's actual proposal model and task/run IDs, source delivery states/evidence references and registered continuation generations. Refresh and older-page controls are read-only. Linking does not add chat messages or change what source/specification is sent to a model. Existing independent jobs remain independent, and permissions/model consent stay explicit. This does not yet turn chat into a general coding-agent session.

## Opt-in bounded context retrieval

A coding job can scan up to 100 checked paths from its approved snapshot locally and send a bounded whole-file subset to its selected provider. Protected tests stay included. Selected files, omission reasons and the durable retrieval read/evidence are inspectable in proposal review; linked conversation history identifies each cycle's read task. Consent resets on mode changes. Owner edits, including changes to omitted candidates, invalidate stale context before use. Direct selected-file mode remains available. This adds deterministic lexical retrieval, not arbitrary repository access or a model-controlled tool loop.


## Coding-history follow-up context

Ask Jarvis/Create project plan offers an unchecked option to include the conversation's recent recorded coding work. It shares up to three linked jobs, shortened goals and cycle/delivery/generation references with the selected online provider, without source or test-output attachments. Existing chat messages remain part of normal chat context. The stored turn exposes exactly which snapshot was included. Consent resets between requests and on conversation/mode/provider changes. Historical status can support discussion and draft planning, but cannot authorize execution or establish current source correctness. Loading the separate history panel still does not send it to a model.

## Supervised coding reliability â€” 2026-10-19

Long owner-configured native steps renew task and scheduler ownership while enforcing cancellation and deadlines. The hidden runner dispatches different projects independently within four slots, one per project; observed supervision timestamps are visible in build and assignment cards. A real 610-second execution crossed the former 600-second parent lease and finished once with cleanup confirmed (evidence in DEVELOPMENT.md).

New desktop builds use host-bound edits, eliminating model-copied hash mistakes and preserving consistent Windows line endings. Invalid output exposes a safe diagnostic code. Explicit reusable integrity/review skills and an internal calibration CLI exercise real online providers, exact review, protected retests and independent checks. These are small task-store foundation trials, not completed applications or proof of general coding quality. General model-directed tools, project dependency/dev-server environments, durable interactive coding sessions and three supervised project builds remain open.

## Review a failed coding generation

An eligible failed build with remaining budget offers Review failed generation. It shows the exact proposal/context, safe failure and reported token counts. A fresh checkbox approves one new generation; rereading clears the checkbox. The review discloses whether the job still allows automatic proposal acceptance. Queueing preserves the first failure and consumes the existing budget when dispatched. Files, skills and test provenance must still match. Unknown transport failures and exhausted/expired jobs do not offer this recovery. Existing repair/feature mode and source-delivery approvals remain separate. Native acceptance for this added flow is in progress.

## Supervised TypeScript project development

A calibration command can now build a strict TypeScript E2E target-profile foundation through the same Core/coding worker, with selected files, frozen skills, protected compilation/tests and exact review. An architecture review can request a new one-call revision without the supervisor editing generated code. The accepted synthetic foundation validates project/environment/base URLs and explicit production consent; it makes no network requests. It remains in ignored evaluation snapshots. Browser execution, test-case editing, project registration/dashboard and general dependency/dev-server environments are still pending. No complete E2E product or general coding-agent milestone is claimed.

## TypeScript creation in the Windows dashboard

Approved specifications can create a TypeScript JSON-function library when the host has a reviewed Node/compiler configuration. Review shows versions and both executable hashes. It creates organized src/tests/docs files and a protected compile/test profile, then requires the existing separate registration, permission and model-call choices. Native acceptance built a real typed module with a deterministic provider and independently executed its output. Real-model E2E target development remains separately measured calibration evidence. Existing-project enrollment, full browser testing engine/dashboard and general conversational coding remain pending.

## Existing projects

An approved specification can now review and import selected files from a host-approved existing project. The desktop exposes logical project selection, explicit existing files and allowed new paths, complete file review, a snapshot receipt and separate native registration. Existing source and initial documents remain untouched until a separately reviewed successful delivery. Imports do not automatically grant resources, buy model calls, install dependencies or deploy. Existing protected tests are required for execution registration. A documentation-only project still needs a separately reviewed acceptance/bootstrap arrangement; this is not yet a general repository bootstrap agent.

## Existing-project workflow

An approved specification can review and import selected files from host-approved existing projects. The desktop exposes logical source selection, explicit existing and new paths, file review, a source-preserving snapshot receipt and separate native registration. No grant, model call, installation or deployment occurs during import. Existing requirements can be selected as protected files. Execution registration requires existing protected tests; documentation-only bootstrap remains pending.

## Interactive coding preparation

The reusable inspection tool boundary is implemented: scoped inventory, literal search and bounded line reads execute as one durable, hash-bound read task. Results survive restart and reject stale inputs or revoked access. It is an API/worker capability; ordinary Chat has not gained automatic file tools, and a complete model-driven coding-session/checkpoint loop remains pending.
