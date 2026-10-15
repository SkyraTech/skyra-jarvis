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
