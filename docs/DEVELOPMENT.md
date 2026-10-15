# Jarvis Orchestration Core — Development

Last maintained: 2026-10-15. This is the cross-milestone summary; the initial task and memory documents are also retained and maintained. Keep architecture and implementation decisions in [ARCHITECTURE.md](ARCHITECTURE.md), requirements in [FUNCTIONALITY.md](FUNCTIONALITY.md).

## Current status

Implemented and verified: durable core, authenticated local API, selected-file worker, owner-enabled native Windows tests, repair workflows and bounded Gemini/Groq repair proposals with versioned skill context and controller review. Native desktop control, model-backed conversation, structured draft planning and setup-readiness guidance are implemented. General autonomous building, a full configuration editor, installer/update delivery and mobile pairing remain pending.

## Completed major milestones

| Milestone | Evidence | Status |
|---|---|---|
| Durable core and scoped policy | Persistence, approvals, leases, state/event rollback tests | Implemented |
| Authenticated local API | Controller/agent/worker separation, request boundaries, migration tests | Implemented |
| Selected-file operations | Scope/stale/hash/evidence tests; original source preserved | Implemented |
| Trusted native repair workflow | Real failing baseline, approved patch, passing retest and diff; Job Object cleanup | Implemented |

Latest per-suite evidence: 41 core/API, 37 worker/execution/workflow, 48 runtime/provider, four desktop bootstrap, thirteen Rust bridge/workspace/export and twenty-seven production-browser tests passed (170 distinct tests). One Windows symlink privilege test is skipped. All suites were rerun in the new-file phase. Strict Clippy, formatting and TypeScript/production build pass. The final Windows release and isolated native new-file acceptance passed against /assets/index-D5JSsflk.js with zero live model calls. Dependency versions and SQLite schema 9 are unchanged in this phase. HTTPX/Starlette TestClient deprecation remains known.

```powershell
.\venv\Scripts\python.exe -m unittest discover -s services/core/tests -v
.\venv\Scripts\python.exe -m unittest discover -s workers/coding/tests -v
.\venv\Scripts\python.exe -m unittest discover -s packages/agent-runtime/tests -v
```

## Next major milestone

- [x] Bounded model-generated repair proposals with explicit provider access and controller review.
- [x] Structured draft project planning with persisted requirements/phases/acceptance.
- [ ] Approved plan-to-build loops and larger evaluation workloads.
- [x] Selected context and trusted versioned skill loading with checksums.
- [ ] Automatic retrieval, skill evaluation and representative speed/quality benchmarks.
- [x] Native Windows control slice connected to core, approvals, runs and artifacts.
- [x] Read-only setup-readiness checklist and provider-only chat startup.
- [ ] Configuration editor and broader agent workspace.
- [ ] Preserve interruption/restart and explicit native-access labels through integration.

## Remaining product phases

- [ ] New curated teaching memory, provenance/revisions/forgetting and specification binding.
- [ ] Employee roles and wider secret provisioning/rotation. Desktop controller/worker credentials now use user-bound Windows DPAPI; model keys remain explicit environment references.
- [x] Hidden local launcher, close-to-tray and single-instance shell.
- [ ] Crash-resilient supervisor, backend packaging, installer/signing/updates and secure mobile pairing.
- [ ] Real isolated backend verification, branch/revision/new-file delivery and parallel conflict handling.
- [ ] Google/document, messaging/social and media workflows with provider-side evidence.
- [ ] Quality/incident integrations and hosted migration/backup recovery.

The owner revoked the earlier exposed token. Current local remotes are clean; config/memory were untracked without deleting local data. Historical secret review remains a separate task. Do not restage runtime data or credentials.

## Development and review rules

- Scope changes to a requirement and meaningful acceptance evidence. Keep providers/storage in adapters and policy outside model logic.
- Prefer reproducible dependency/formatter/type-check configuration. Validate versions before upgrades; no rewrite merely for language uniformity.
- Use structured errors, bounded timeouts, cancellation and retry classification. Label mocks explicitly; they cannot establish production acceptance.
- Review scope, migrations, credentials, failure/recovery behavior and logs. Model agreement is not independent verification.
- Keep product-owned tests with the product. Quality tools aggregate evidence; they do not replace tests with a coverage percentage.
- Do not stage, commit or push. The owner reviews and commits manually. Complete a substantial milestone, inspect Git status/diffs, provide one appropriate commit message, and wait for owner confirmation before the next milestone.
- Update the initial nine project documents and these current implementation references in place as relevant. Add architecture decisions/change rows here or in architecture; do not create per-task Markdown reports. Detailed execution artifacts belong in runtime storage and Git retains document history.

## Documentation checkpoint

2026-10-14: initial specifications are retained alongside consolidated current architecture/functionality/development references; only redundant per-work reports are removed. Current vs proposed schema/capabilities are separated. No application code or runtime data changed by consolidation.

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

## Model repair milestone — 2026-10-14

Implemented durable proposal state/migration 6, explicit Gemini/Groq adapters, bounded selected context, versioned trusted skills, strict patches, controller routes, atomic acceptance and preserved task approvals. Deterministic checks cover malformed/protected/stale patches, context revocation/change, restart without billable replay, concurrent single dispatch, late-output interruption, rollback and version-5 conversation preservation.

Live generated fixture results (single observation each, not a model ranking):

| Provider/model | Generation | Tokens in/out/total | Result |
|---|---|---|---|
| Gemini `gemini-3.5-flash-lite` | 4.306 s | 660 / 164 / 824 | Baseline failed, patch applied, retest passed, diff ready |
| Groq `qwen/qwen3.8-27b` | 1.999 s | 635 / 170 / 805 | Baseline failed, patch applied, retest passed, diff ready |

Evidence: ignored `.runtime/model-repair-gemini-configured-20261014/review.json` and `.runtime/model-repair-groq-20261014/review.json`, their databases and task-bound checksummed reports. Originals were preserved. Two earlier Gemini `gemini-2.5-flash-lite` fixture requests failed; the diagnostic classified HTTP 404, although listing advertised it. No automatic fallback occurred. Existing configured 3.5 model was then explicitly selected and verified. Availability must be checked at use time. Existing local key files were read only, never printed or committed.

The subsequent Windows control milestone implements projects, stored conversations, proposal review, approvals, run progress, evidence and the subsystem canvas. Next: guided trusted configuration, model-backed conversation/planning and controlled build loops. Desktop scheduling/mobile pairing and general production delivery remain pending. Owner review/commit is the checkpoint before the next milestone.

## Windows control milestone — 2026-10-15

Implemented a dedicated React Flow subsystem map and native Tauri 2 Windows host; project creation/selection, owner policy review, model repair proposal review, exact-action approvals, worker checkpoints/cancellation, task-bound evidence, stored conversation history and recent events. Planned subsystems are labelled explicitly. Permission saves compare the version reviewed when the dialog opened; stale background refreshes cannot silently change that decision. Canvas tests verify measured minimap geometry.

The final portable release passed native acceptance with the exact production asset `/assets/index-DRDPxJyl.js`. Evidence: ignored `.runtime/desktop-native-1792045527774/review.json`, `native-overview.png` and `native-review.png`. The real executable connected through its Rust bridge using DPAPI-protected credentials, saved owner policy, completed a deterministic repair through three approval gates, produced four reports with passing retest/diff, preserved the source and stored a message. Closing hid the live app to its tray; a second launch restored that same window. The executable uses Windows GUI subsystem 2; normal launcher/core operation does not open a terminal. This acceptance made zero live model calls.

Release: `apps/desktop/src-tauri/target/release/jarvis-desktop.exe`, 4,911,616 bytes, SHA-256 `C8B80AD539D63D30DE62547795A052A93F8AA393D56ED71547BDE8615DAA4328`. Build prerequisites installed: Rust 1.99.0 and Microsoft C++ Build Tools/Windows SDK. WebView2 was already installed. Source and exact JS/Rust dependencies are locked. Build/start instructions are maintained in the desktop README. This remains a portable developer build with a separately provisioned local Python core; no installer, bundled Python, signing or updater is delivered.

Verification: 115 tests passed and one Windows symlink privilege test skipped, plus the native acceptance above. Formatting, strict Rust Clippy, TypeScript/production compilation, production dependency audit, Git whitespace checks and local document links passed. All 36 initial specification documents remain present; none are deleted. No changes were staged, committed or pushed.

The next conversation/planning milestone below adds model replies and read-only setup guidance. Configuration editing and controlled project build loops remain future work. General autonomous building, scheduler, mobile pairing and production deployment remain pending. The owner reviews and commits this milestone before the next development phase.

## Conversation and draft planning milestone — 2026-10-15

Implemented ConversationRuntime, separate from repair execution, with explicit Gemini/Groq provider selection, chat/plan modes, persisted request snapshots, token usage, safe errors, controller interruption and strict structured output. Plans include requirements/deliverables/phases/tasks/acceptance/risks/questions. They remain reviewable draft data and do not create tasks, files, permissions or coding runs. SQLite migration 7 preserves existing state and adds model_turns plus an active-conversation uniqueness index. User message and turn creation commit together; assistant message/response/completion commit together. Concurrent/restarted/terminal requests cannot replay paid generation. A trusted instruction hash, provider family and exact response schema are part of the saved context and are checked again before dispatch.

The desktop adds local-note/chat/draft-plan modes, provider selection, recent request history, inspectable context/omissions, usage and independent interruption. A Setup screen reads configuration readiness without provisioning paths, commands, credentials or execution. Provider-only core startup works without workspace registration; an isolated real-process test covers that path. Existing records remain readable/interruptible when provider configuration is removed. The renderer receives no provider keys.

Live generated-prompt observations (not a benchmark): Gemini gemini-3.5-flash-lite chat completed in 8.697 s with 249/44/293 input/output/total tokens; Groq qwen/qwen3.8-27b planning completed in 4.001 s with 480/630/1110 tokens. Evidence: ignored .runtime/chat-gemini-20261015/review.json and .runtime/plan-groq-schema-20261015/review.json. An initial Groq plan consumed 299/680/979 tokens but failed strict validation because its JSON-mode prompt omitted the schema. The schema is now explicitly included and regression checked; the failed turn remains terminal in .runtime/plan-groq-20261015. There were three explicitly initiated live calls in this phase, all with fictional context; no real project files or user conversations were sent and no execution tasks were created.

Verification across suites: 139 tests passed and one Windows symlink test skipped. Core/API 41, worker 33, runtime/provider 38 (20 prior repair/provider tests plus 18 conversation tests), desktop bootstrap 4, Rust bridge 5, browser 18. Strict Rust Clippy, formatting and production compilation pass. Final native acceptance passed with `/assets/index-xnOCH8ud.js`, the exact final production UI asset. Evidence: `.runtime/desktop-native-1792047273451/review.json` and `native-plan.png`. The real Windows executable completed chat and structured-plan requests through deterministic test providers, verified setup readiness and repeated the existing three-approval repair/evidence and tray/single-instance flow. No live provider calls occurred during native acceptance. The release is 4,915,712 bytes with SHA-256 `92F0F8929F891DE78386B9BDD492F9749F3E7FA8E7B188CD6D4C27E81724CCCE`. This remains a portable developer executable with a separately configured Python core, not an installer.

Remaining work: editable trusted setup, streaming replies, approved plan-to-build handoff, specification/document file delivery, learned-memory governance, general new-file coding loops, installer/signing/update distribution, mobile pairing and service integrations. The owner stages/commits/pushes manually; no Git mutation was performed by the assistant.

## Flexible 3D workspace milestone — 2026-10-15

Implemented a 3D CSS orbital Jarvis object with pointer/keyboard rotation and optional reduced-motion-aware animation. Core and System map can be viewed independently. The workspace adds up to eight tabs per window, tab reordering/minimization/restoration/closure, keyboard navigation, focus layout, dashboard-card popouts and up to eight additional native windows. Tab metadata restores automatically; visited conversation drafts survive tab switching/minimization in the current session. Restored unvisited tabs mount lazily, and inactive dashboard tabs do not poll.

Native commands validate built-in views/project IDs and expose calling-window controls plus explicit show-all/save/restore. Windows support edge resizing and explicit width/height, minimize/maximize/fullscreen and native monitor movement. A validated versioned arrangement file stores UI geometry; restored windows are fitted onto connected monitor work areas. Closing main hides to tray; child windows close independently. Existing API/DPAPI/project/resource boundaries remain unchanged. No new Core table/schema or external dependency was added. No legacy code/user memory was removed, and no service was deployed.

Focused checks: 24 production-browser acceptance cases, nine Rust unit checks, strict Clippy, formatting and TypeScript/production compilation. These include existing proposal/approval/run/chat regressions and new 3D, tab draft/lifecycle/reload, focus, corrupt-layout and small-window checks. Backend code is unchanged in this phase; the previous 41 core/API, 33 worker, 38 runtime/provider and four bootstrap tests remain the last backend-suite evidence. Native acceptance passed against the final embedded asset `/assets/index-BVd2McEc.js`. Evidence: `.runtime/desktop-native-1792051774717/review.json`, `native-3d-workspace.png` and `native-independent-panel.png`. The actual release opened two simultaneous independent panels plus main, verified explicit width/height, minimize/maximize/fullscreen using Win32 state, saved/restored the arrangement, recreated a closed panel and recovered simulated offscreen coordinates. The existing approval-controlled repair, chat, plan, DPAPI and main tray/single-instance flows also passed. This acceptance made zero online model calls. Release size: 5,035,008 bytes; SHA-256 `508941760059C3F3D17159BB0989CB51AAA46FA2368B6E24DBC6AC933968FD65`; GUI subsystem 2. Windows initially prevented replacing the previous running executable; after the owner confirmed exiting it, the verified old background PID was stopped, the newly linked executable was copied into the standard release path, its hash was verified and acceptance completed. All API work targeted generated fixture state; the final accepted run also used its own WebView2 profile under the fixture directory.

Remaining: named layout profiles, full internal docking/tile editing, automatic recreation of external windows on launch, cross-device layouts, packaged/signed installer and the previously planned approved plan-to-build workflow. Native monitor recovery is tested with simulated saved offscreen positions; physically dragging between multiple attached monitors still needs an owner hardware check.


## Versioned specification milestone - 2026-10-15

Implemented offline publication of completed planning turns into immutable requirements/tasks/acceptance/memory document bundles. SQLite migration 8 retains existing history, introduces owner-scoped per-project versions, request idempotency, exact canonical-bundle SHA-256 approval and atomic approval supersession. The Conversations screen provides document/version review; repair preparation optionally binds an approved specification. Its snapshot is added to model context and stale approval blocks generation/acceptance. Existing resource grants, native test profiles, source snapshots and exact-action approvals still govern work. General greenfield builds, complete architecture/design document authoring and document file export remain pending.

Verification: concurrent publication conflict, event-rollback atomicity, migration 7 to 8 with completed-plan preservation, owner/project/controller boundaries, approval checksum/idempotency/supersession, optional repair context and rejection of a superseded handoff. All 156 distinct suite checks above pass, with one known skipped symlink test. Browser acceptance initially caught invalid encoding in the new heading; corrected before the final passing suite. Native acceptance harness now includes real Core-backed specification publication and approval. Zero live model calls were made in this phase.

Release compilation linked the updated executable (5,036,544 bytes, SHA-256 C6DEAF8639F4DCEEAE485FDE51EAF32E04A28478AD9AE98EF00248BDB965C098) but Cargo could not replace the standard release path while owner Jarvis PID 10708 holds it. A verified copy is preserved in target/release/next/jarvis-desktop.exe. After the owner authorized closing Jarvis, the verified running process was stopped. Windows briefly retained the executable lock; replacement succeeded on retry and its checksum was verified. The standard release now contains the updated version. Native acceptance passed against embedded asset /assets/index-C25jlpKl.js. Evidence: .runtime/desktop-native-1792055068344/review.json and native-specification.png. The real Windows app published/reviewed/approved a specification through the Core, completed the three-approval repair workflow with four evidence reports and original source preserved, and verified chat/plan, DPAPI, independent panels, native window controls, arrangement recovery and tray/single-instance behavior. Fixture processes were closed after testing. No staging, commits or pushes were performed.


## Specification revision and document delivery milestone - 2026-10-15

Implemented owner-authored immutable document revisions with parent provenance, explicit current-version/checksum comparison, request deduplication and schema 9 migration preserving existing snapshots. Four core documents remain required; five other standard document types can be added and authored. A revision is a draft and approval is separate. Conflicting saves retain edits and show an actionable error inside the keyboard-accessible editor.

The native export command fetches approved canonical documents through the Core, independently checks SHA-256 and supported filenames and creates an immutable version folder under Documents/Skyra/Jarvis/exports (or trusted JARVIS_EXPORT_ROOT). Exact UTF-8 Markdown and a provenance manifest are staged and renamed into place. Repeat export verifies existing bytes; altered contents fail without overwrite. Renderer arguments contain only specification ID and expected checksum, with no filesystem path or file contents. Core export-prepared events record preparation, not successful local delivery. No model call or coding run is triggered.

Verification so far: 162 distinct tests passed, one existing Windows symlink test skipped; migration/lineage, stale conflicts, controller boundaries, approved-only export, document size/name validation, canonical integrity, literal output/re-export checks, editor draft retention and focus restoration pass. Strict Clippy, formatting and production TypeScript build pass. Native acceptance passed using isolated Core data and a separate WebView profile, including revision/approval and export of five documents with exact read-back and verified repeat export. Evidence: .runtime/desktop-native-1792056122316/review.json. Final review caught and fixed a manifest envelope limit that could reject re-export of heavily escaped bundles near 64 KB. The regression uses a valid canonical bundle whose manifest exceeds the old 128,000-byte limit. Native manifest reads now allow a bounded 256 KiB envelope and also compare parent/approval provenance. The final release rebuild and repeated native acceptance passed. Final evidence: .runtime/desktop-native-1792056466391/review.json and native-specification-export.png. Release size: 5,115,392 bytes; SHA-256 A8533D5D1D84926C0F43A76E8A46460669D701B5DFF5BE5022184A00FED4EC98; embedded asset /assets/index-CZFENX_W.js; Windows GUI subsystem 2. Final acceptance used generated Core state, its own WebView2 profile and an export root inside its fixture. It verified revised version 2, five exact exported Markdown files plus manifest, repeat export, three repair approval gates/four evidence reports with source preserved, chat/plan, DPAPI, native panels/window controls/arrangement recovery and tray/single-instance behavior. No paid model calls occurred and fixture processes were closed. All 36 initial documents remain, with no deleted or staged files. No stage, commit or push was performed.


## Reviewed new-file coding milestone - 2026-10-15

Implemented explicit absent creation targets in snapshot manifest v2, exclusive non-overwriting create actions, absent-baseline addition diffs, model content/target validation, stale-absence checks and exact create action approvals. Existing snapshot manifests remain readable. Protected tests must already exist and remain unchanged. Execution copies omit absent optional targets while refusing absent protected tests. Coding runs retain their failing baseline, reviewed writes, passing retest and diff progression. Retry deduplication recovers an existing run after its target file is created. The UI discloses new-file intent and full generated content.

Verification: 170 distinct tests passed, one existing symlink privilege test skipped. Runtime tests execute an actual missing-module baseline and passing protected retest, preserve original source and reject unselected/stale targets. Approved specification binding/supersession is checked against a new-file proposal. Worker tests cover exact write approval, reload/addition evidence, invalid/colliding/occupied target paths and missing protected-test refusal. The production browser suite includes explicit new-file review. Native acceptance is updated to perform a new-module workflow and verify that the original project did not gain the generated file; release compilation and native acceptance passed. Final evidence: .runtime/desktop-native-1792057413527/review.json and native-review.png. The Windows app passed three exact action approvals, created feature.py in the registered snapshot, passed the protected retest and delivered four evidence reports including a /dev/null addition. It verified source/feature.py remained absent and source/app.py unchanged. Existing conversation/planning, specification revision/export, DPAPI, independent panels/native window controls, arrangement recovery and tray/single-instance acceptance passed. All fixture state, export files and WebView data stayed inside the generated test root and fixture processes were closed. Release: 5,115,392 bytes, SHA-256 F56D91CC30911401E062A2F15FE5E0D5F1A3D0E56EA153F4FC0B37E7D79DDCBA, Windows GUI subsystem 2, embedded asset /assets/index-D5JSsflk.js. No live model calls were made.

The previous revision/export phase was still uncommitted at phase start; the user authorized further development. It remains preserved alongside this phase. No staging, commits or pushes were performed. General greenfield builds, owner test scaffolding, iterative debugging and source delivery remain pending.
