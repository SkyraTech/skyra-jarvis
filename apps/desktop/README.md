# Jarvis Windows Desktop

Component of `skyra-jarvis`. Implemented Windows control slice: dedicated React Flow subsystem canvas, project permissions, proposal review, approvals, coding checkpoints/evidence, stored conversations and recent events; Tauri Rust bridge, DPAPI credentials, hidden launcher and tray lifecycle. Release executable builds; native acceptance is recorded in the owning development tracker. Model chat, structured draft plans and a setup-readiness checklist are implemented. Installer, signed updates, mobile pairing, configuration editing and automatic workflow scheduling remain pending. The legacy UI stays separate.

## Initial project documents — retain and maintain

- [Product requirements](docs/01_PRODUCT_REQUIREMENTS.md)
- [System architecture](docs/02_SYSTEM_ARCHITECTURE.md)
- [Development rules](docs/03_DEVELOPMENT_RULES.md)
- [Design system](docs/04_DESIGN_SYSTEM.md)
- [Project tasks](docs/05_PROJECT_TASKS.md)
- [Project memory](docs/06_PROJECT_MEMORY.md)
- [API and event contracts](docs/07_API_AND_EVENTS.md)
- [Testing and acceptance](docs/08_TESTING_AND_ACCEPTANCE.md)
- [Security and operations](docs/09_SECURITY_AND_OPERATIONS.md)

## Build and run on this Windows PC

The UI uses its own design and React Flow, with no Skyra Platform UI dependency. Prerequisites: Node matching Vite requirements, pnpm 11.25.0, pinned Rust 1.99.0, Microsoft C++ Build Tools/Windows SDK, and WebView2. Build tools are needed for development, not as visible background terminals while Jarvis runs.

From `apps/desktop`:

```powershell
$env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
pnpm install --frozen-lockfile
pnpm build
pnpm tauri build --no-bundle
```

The release executable is `src-tauri/target/release/jarvis-desktop.exe`. It embeds the production UI and uses the Windows GUI subsystem. It still needs the configured local Python core: this slice does not bundle Python or provide a signed installer/updater.

For a new private state directory, run once from the Jarvis repository root:

```powershell
.\venv\Scripts\python.exe apps\desktop\bootstrap.py
```

This creates `%LOCALAPPDATA%/Skyra/Jarvis` with a hashed controller auth registry, DPAPI-protected desktop credential and launcher configuration. It refuses to overwrite existing state. If that directory already exists, preserve it and use an explicit new private `--directory`; pass the same path as `--state` to the launcher. It enables no provider, worker or native execution by default. Never delete existing core state to bypass initialization.

Start without a terminal window:

```powershell
.\venv\Scripts\pythonw.exe apps\desktop\launch.pyw
```

The hidden launcher starts its own core if no authenticated core is already running, then opens Jarvis. Close hides the window to the system tray; Open restores it; Exit ends Jarvis and stops only a core owned by that launcher. A second desktop launch restores the existing window. Do not use Exit as a substitute for safe cancellation/reconciliation of active work.

Trusted workspace registration and fixed test profiles use the core launcher configuration described in the owning architecture. Provider registration uses the runtime's existing configuration example and explicit environment keys. The desktop connection file accepts `port`, `controller_token_dpapi` and optional `worker_token_dpapi`; a worker credential must be separately registered with the same owner and exact project IDs. Changing auth/config requires restarting the relevant process. The renderer cannot register paths/commands or read credentials. Setup now displays a read-only readiness checklist. Configuration editing and credential rotation UI remain pending.

## Validation

```powershell
pnpm format:check
pnpm test
cd src-tauri
cargo fmt --check
cargo clippy --all-targets --locked -- -D warnings
cargo test --locked
```

`pnpm test` builds and serves production assets for browser acceptance in installed Edge. Explicit `?preview=1` in a browser loads labelled fixtures only; ordinary browser mode cannot connect to the core, and preview is disabled in the native app.

After a release build, `pnpm test:native` creates a new ignored `.runtime/desktop-native-*` fixture and exercises the actual Tauri/WebView2 application with a real local core, DPAPI tokens, separate worker/controller roles, three approval gates, real Windows tests, evidence, conversation persistence, model chat, structured plans and setup readiness. The acceptance-only core replaces outbound provider calls with deterministic fixtures; this native test makes zero online model calls. It opens only its own test GUI, uses a temporary loopback CDP debugging port, verifies actual Win32 close/restore visibility, and cleans up its test processes. Never enable that test debug port for normal launches. Review JSON and screenshots stay in runtime storage, outside tracked documentation.

The initial nine documents above remain the maintained specifications; detailed current architecture, functionality and milestone evidence belong to the owning Jarvis documents.

## Conversations and draft plans

Create a conversation, then choose Store note only, Ask Jarvis or Create project plan. Paid modes require selecting a provider/model explicitly. Recent history is sent to that provider; inspect the stored snapshot and omitted-message count in Model requests. Interruption suppresses late output but may not stop external billing. A generating request left after restart is uncertain: refresh/inspect it, then interrupt before creating another. Jarvis never automatically replays it.

To enable chat without coding execution, copy the existing runtime configuration example into private state, register a provider alias/model/environment key and reference its absolute path in launcher.json as runtime_config. A workspace_config or worker credential is optional for chat/planning. Use the model registry in Setup to check registration. Do not paste keys into conversations. Draft plans stay in SQLite and do not create project files or authorize a build.

## Arrange Jarvis across your screens

The overview now includes an interactive 3D Jarvis core. Drag it to rotate, or focus it and use arrow keys/Home. Animate orbit is optional and respects reduced motion. Core and System map also have separate sidebar views. Dashboard popout arrows and New window open independent native panels.

Use + Tab to choose a new workspace tab (Ctrl+T opens Overview). Drag tabs to reorder, or use tab arrow/Home/End navigation. Arrange offers Minimize tab, Move tab left and Open tab in new window. Restore minimized tabs from the bottom shelf; Ctrl+W closes the active tab. Drafts survive switching/minimizing visited tabs within the current session; closing/restarting restores tab metadata, not unsaved message content.

Move native windows by their Windows title bars; resize edges or use Arrange → Window width/height → Apply window size. The toolbar offers minimize, maximize/restore and fullscreen (F11). Toggle focus layout hides navigation. Arrange → Show all windows restores minimized panels. Save window arrangement records all open normal/maximized windows; exit fullscreen and restore minimized windows before saving. Restore window arrangement reopens/repositions saved panels and recovers offscreen positions when monitors change. It does not close extra current windows or replay tasks. Up to eight tabs per window and eight additional windows are supported.

Closing an additional panel closes that window; closing the main window hides to the system tray. Use the tray Exit to end Jarvis. The existing hidden launcher is unchanged. No legacy code or user memory was removed in this UI phase.

Native acceptance now sets a separate WEBVIEW2_USER_DATA_FOLDER inside each generated runtime fixture, alongside isolated Core/DPAPI state. Test tab preferences and native-window metadata stay separate from the normal application profile.

## Model-backed repair jobs

Build jobs can start from a repair goal without a pre-generated patch. Configure a trusted selected-file snapshot, pre-existing protected tests, fixed execution profile and explicit provider alias, then enable the same hidden runner described below. No private configuration is enabled by this code change.

In Build jobs, select the workspace, test profile, model and context files (including protected tests). Optionally select an approved specification. Set model-call, repair-cycle, step and duration limits, and explicitly allow sharing selected context/diagnostics with that provider. Queue the job. A passing initial baseline completes without calling a model; a verified failure starts repair generation. Review job proposal shows the exact response/checksums before acceptance. Each coding action still follows the project's current task policy. After a verified failing retest, another bounded repair cycle may request a new proposal with updated hashes and diagnostics.

Default behavior requires reviewing every generated proposal. Automatic acceptance requires both the per-job checkbox and current full-access policy. Validation checks schema, selected paths, protected tests and freshness; it is not a security certification of generated code. Tests use the configured executor's permissions, including full account privileges for trusted native execution.

Call slots are reserved before generation and retained for failed/unknown requests. This is a request cap, not a currency cap. Provider-reported usage can be incomplete. A saved ready response can be recovered after explicit resume without another request; generating after a crash remains uncertain and requires inspection. Provider errors are not automatically retried or routed to another model. Cycle history is retained in the job detail API; the dashboard shows current phase/budgets and a progress summary.

Completion stops at tested review readiness. Open the final run in Coding runs for evidence and separately reviewed source delivery. General empty-project scaffolding, autonomous protected-test authoring, currency budgets and production deployment remain future work.

## Hidden unattended assignments

The Assignments screen queues bounded progression of an already accepted coding run. Review/accept the repair proposal first, then enter a goal, step budget and time limit. The runner handles baseline, approved writes, retest and diff without manual Advance clicks. Ask mode still waits for exact-action approvals. Completion stops at tested review readiness; source delivery remains separate. No paid model request, iterative model debugging or new project scaffold is generated by this executor.

Enable only in trusted private state after configuring workspaces, fixed test profiles and the separately registered project-scoped worker credential in desktop.json. Preserve all existing configuration fields and add unattended_enabled=true to launcher.json. Restart an existing Core explicitly so it reads the new setting. Create runner.json in that same private state directory:

```json
{"projects": ["<actual-32-character-project-id>"], "interval_seconds": 5}
```

Start the hidden background supervisor from the repository root, then open the normal dashboard:

```powershell
.\venv\Scripts\pythonw.exe apps\desktop\launch.pyw --background --state "$env:LOCALAPPDATA\Skyra\Jarvis"
.\venv\Scripts\pythonw.exe apps\desktop\launch.pyw --state "$env:LOCALAPPDATA\Skyra\Jarvis"
```

If enabled and no Core exists, the normal launcher can also start that supervisor automatically. The supervisor owns its Core independently of the dashboard. With unattended_enabled absent, default launcher ownership remains unchanged. Core enablement alone does not establish runner health: check runner-status.json for its heartbeat and the assignment's updated time. Work needs an awake connected PC. No login task or Windows service is installed.

Pause/resume/cancel individual assignments in the dashboard. Pause applies after the active bounded step; cancel uses existing task cancellation. Step slots are reserved before dispatch, refunded for known approval/no-progress waits and retained after uncertain crashes. Time limits are checked between steps. Expired worker claims block for review rather than replay effects. Inspect task/evidence before resuming uncertain work.

To stop the background runner after its current step:

```powershell
.\venv\Scripts\pythonw.exe apps\desktop\launch.pyw --stop-background --state "$env:LOCALAPPDATA\Skyra\Jarvis"
```

This writes runner.stop. Wait for runner-status.json to report stopped. The supervisor then stops only the Core it owns; connected dashboards may become disconnected. Starting --background explicitly clears the old marker. Private status, lock and stop files contain no API keys; keep all state private. Do not stop a process to bypass reconciliation of uncertain work.

## Review and create a new project from a specification

In private launcher.json, optionally set scaffold_root to an existing absolute private directory without links/reparse points. New bootstraps set it to null. Restart the launcher-owned Core after changing this host setting. Direct Core startup uses --scaffold-root. This setting enables reviewed project creation only; it does not enable execution or configure providers. No actual private setting is changed automatically.

In Conversations, select an approved specification and expand New project scaffold. Enter an unused lowercase slug and a JSON cases contract matching the requirements, for example {"cases":[{"name":"positive","input":3,"output":6}]} for a specification requiring doubling. Preview all files and the destination/profile, then check the explicit review consent and create. Changing input clears the old preview. All nine original documents are included, preserving approved content and identifying host defaults.

Choose the function template or website/HTTP template, both with protected reviewed examples. The stub is unimplemented. After an uncertain response, use Check creation receipt instead of retrying; a missing audit event needs manual reconciliation. Continue below the receipt to review/register the exact workspace/profile, explicitly consent to native commands, grant intended resources and queue a scoped Build job. Host execution must already be enabled using scaffold_execution_enabled=true (direct Core: --enable-scaffold-execution), or an existing trusted NativeExecutor. Fresh bootstrap leaves this false. Source delivery remains separately reviewed; arbitrary registry editing remains deferred.


The website template protects its loopback server and acceptance contract/tests while allowing app.py and index.html implementation. Review actual GET/POST response examples; at least one success case is required. Registration persists in schema 12 and restores without per-project JSON edits/restart. Inspect reconciliation errors explicitly. This is local tested project generation; it does not install dependencies, host publicly or deploy.


## Unattended operations and saved projects

Activity contains persistent completion/attention outcomes, current work, unread acknowledgement and a Registered project library. Use Open project workflow to recover build/delivery history directly. Acknowledging a notice does not approve, resume or deliver anything. Inbox snapshots preserve the outcome at that time; inspect current evidence/source before delivery. Background host enablement is distinct from runner health. The PC/Core/hidden worker must remain running; one-time starts are available below, while wake, recurrence, Windows login startup and external notifications remain pending.


## One-time scheduled build starts

Build jobs can start at a reviewed future local time within seven days. Enable Schedule build start, enter the time and allowed late-start window (1..1440 minutes), then review scheduling conditions and model-call consent. Runtime duration is measured from the planned time. Scheduled jobs reserve their workspace; pause/resume preserves not-before. Missed starts fail and changed selected inputs/specification block without execution; cancel and submit a fresh reviewed job. Approval waits remain explicit, and source delivery is separate. Keep the PC, Core and worker running; scheduling does not wake Windows.

Activity Runner contact records authenticated requests received by Core and their latest response/error. Recent/in-progress/stale is communication evidence, not OS process-health certification. New schema 14 preserves existing history and defaults to no recorded contact. No actual private configuration is changed.
