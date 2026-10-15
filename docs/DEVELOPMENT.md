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

Latest code verification: 41 core/API, 33 worker/execution/workflow, 38 runtime/provider, four desktop bootstrap, five Rust bridge and eighteen production-browser acceptance tests passed (139 passed total). One Windows symlink test was skipped because the account could not create it. Rust formatting, strict Clippy, TypeScript/production build and production dependency audit also passed. Docker behavior has contract tests only, not live engine verification. HTTPX/Starlette TestClient deprecation remains known. The current model-repair milestone includes runtime code and live provider verification.

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
