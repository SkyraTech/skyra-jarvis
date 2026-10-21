# Jarvis Orchestration Core — Project Tasks

## Maintained specification — current status

Updated 2026-10-16. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented and verified: durable core, authenticated local API, selected-file worker, owner-enabled native Windows tests, repair workflows and bounded Gemini/Groq repair proposals with versioned skill context and controller review. Native desktop control, flexible 3D/tabbed/multi-window workspace, model-backed conversation, structured draft planning and setup-readiness guidance are implemented. Reviewed function and website/HTTP templates connect desktop creation, durable registration, explicit grants, bounded repair jobs and separate source delivery. The Activity operations center adds durable outcomes, acknowledgement, saved project recovery and recorded runner contact. Build jobs support one-time scheduled starts with input/specification admission guards; final native acceptance is recorded in DEVELOPMENT.md. General autonomous building, a registry/configuration editor, installer/update delivery and mobile pairing remain pending.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](ARCHITECTURE.md)
- [Current functionality and implementation boundaries](FUNCTIONALITY.md)
- [Current milestone and verification summary](DEVELOPMENT.md)

Prepared: 2026-10-14. Requirement/design baseline. Use the maintained current-status section above to distinguish implemented work from planned work.

## Planning baseline

## Trusted coding-workflow milestone — 2026-10-14

- [x] EXEC-NATIVE-01: Owner-approved native mode, fixed profiles and Windows process-tree supervision.
- [x] EXEC-NATIVE-02: Real test outputs, timeout/cancellation, bounded logs and protected regression tests.
- [x] WORKFLOW-01: Durable repair plans, approval pauses, task-bound gates, run deduplication and review evidence.
- [x] WORKFLOW-02: Real baseline-failure → repair → passing-retest → diff demo; regression suite and setup docs.
- [ ] EXEC-ISOLATED: Verify optional Docker/other isolation backend; native mode does not satisfy OS security isolation.
- [x] AGENT-ONLINE: Connect bounded model repair proposals and persisted draft planning with evaluation fixtures.
- [ ] AGENT-BUILD: Add an approved plan-to-build handoff and broader project build loop.

This is a larger executable-workflow checkpoint. Owner manually commits; no staging/commit/push performed by the assistant. Evidence and native-access limits are in the maintained [architecture](ARCHITECTURE.md#worker-and-execution-boundaries).

The broad phase tasks below remain open; the first implementation slice is recorded separately here. Existing prototype code may satisfy a task only after it is checked against target acceptance criteria.

## Core baseline slice — 2026-10-14

- [x] CORE-001: Remove credential-bearing local remote URLs; preserve and untrack local config/memory files.
- [x] CORE-002: Implement versioned SQLite state for projects, conversations, tasks and events.
- [x] CORE-003: Implement exact-resource permission modes and versioned, expiring approvals.
- [x] CORE-004: Implement exclusive claims, cancellation uncertainty and explicit reconciliation.
- [x] CORE-005A: Add authenticated local API with separate controller/agent/worker credentials, project scopes and API integration tests.
- [x] CORE-005B-FILES: Connect selected-file snapshots and guarded file operations; verify scope, approval and evidence boundaries end to end.
- [ ] CORE-005B-PROCESS: Implement and verify OS/container isolation before running repository code or build/test commands.
- [x] SECURITY-002A: Owner confirmed revocation of the exposed token.
- [ ] SECURITY-002B: Complete historical secret review and any required cleanup before publication.

Earlier API-only checkpoint: 38 core/API tests passed, with v1→v2 migration and task-request deduplication. Subsequent worker integration and migrations reached schema 5; current tests and remaining work are in [development](DEVELOPMENT.md). The implemented [API catalogue](FUNCTIONALITY.md#implemented-local-api) replaces the earlier standalone API report.

See [current implementation evidence and limits](DEVELOPMENT.md). CORE-001 records local hygiene; the owner subsequently confirmed credential revocation, while historical secret review remains separate.

## Phase 1: Define domain state machines, SQLite schema, permissions and specification contracts

- [ ] JARVIS-P1-01: Define scope, affected requirements and failure cases for this phase.
- [ ] JARVIS-P1-02: Implement: define domain state machines, SQLite schema, permissions and specification contracts.
- [ ] JARVIS-P1-03: Run relevant contract, integration and acceptance checks; attach evidence.
- [ ] JARVIS-P1-04: Review permissions, recovery and documentation; record completion in memory.

Exit gate: implementation is demonstrated against its mapped requirements; failures and follow-up work are recorded. No phase is complete merely because its files exist.

## Phase 2: Implement conversations, events, artifacts, memory and checkpoint recovery

- [ ] JARVIS-P2-01: Define scope, affected requirements and failure cases for this phase.
- [ ] JARVIS-P2-02: Implement: implement conversations, events, artifacts, memory and checkpoint recovery.
- [ ] JARVIS-P2-03: Run relevant contract, integration and acceptance checks; attach evidence.
- [ ] JARVIS-P2-04: Review permissions, recovery and documentation; record completion in memory.

Exit gate: implementation is demonstrated against its mapped requirements; failures and follow-up work are recorded. No phase is complete merely because its files exist.

## Phase 3: Integrate agent runtime, coding worker and quality gates for one complete project workflow

- [ ] JARVIS-P3-01: Define scope, affected requirements and failure cases for this phase.
- [ ] JARVIS-P3-02: Implement: integrate agent runtime, coding worker and quality gates for one complete project workflow.
- [ ] JARVIS-P3-03: Run relevant contract, integration and acceptance checks; attach evidence.
- [ ] JARVIS-P3-04: Review permissions, recovery and documentation; record completion in memory.

Exit gate: implementation is demonstrated against its mapped requirements; failures and follow-up work are recorded. No phase is complete merely because its files exist.

## Phase 4: Add desktop/mobile controls, MCP registry, schedules and incident playbooks

- [ ] JARVIS-P4-01: Define scope, affected requirements and failure cases for this phase.
- [ ] JARVIS-P4-02: Implement: add desktop/mobile controls, MCP registry, schedules and incident playbooks.
- [ ] JARVIS-P4-03: Run relevant contract, integration and acceptance checks; attach evidence.
- [ ] JARVIS-P4-04: Review permissions, recovery and documentation; record completion in memory.

Exit gate: implementation is demonstrated against its mapped requirements; failures and follow-up work are recorded. No phase is complete merely because its files exist.

## Phase 5: Validate hosted migration and remote-worker ownership without changing local-first scope

- [ ] JARVIS-P5-01: Define scope, affected requirements and failure cases for this phase.
- [ ] JARVIS-P5-02: Implement: validate hosted migration and remote-worker ownership without changing local-first scope.
- [ ] JARVIS-P5-03: Run relevant contract, integration and acceptance checks; attach evidence.
- [ ] JARVIS-P5-04: Review permissions, recovery and documentation; record completion in memory.

Exit gate: implementation is demonstrated against its mapped requirements; failures and follow-up work are recorded. No phase is complete merely because its files exist.

## Dependencies and sequencing

- [skyra-service-contracts](../../skyra-service-contracts/README.md)
- [skyra-service-foundation](../../skyra-service-contracts/packages/foundation/README.md)
- [skyra-agent-runtime](../packages/agent-runtime/README.md)
- [skyra-jarvis-desktop](../apps/desktop/README.md)
- [skyra-quality](../../skyra-quality/README.md)

Start with contracts and the smallest complete workflow. Agree interfaces early; do not wait for every neighboring project to be complete. Mock fixtures are useful for development but must be replaced with isolated integration evidence before release.

## Cross-cutting release checklist

- [ ] Acceptance matrix has evidence against a commit and environment.
- [ ] Permission, isolation, restart and duplicate-delivery cases pass where applicable.
- [ ] Secrets are protected and logs are sanitized.
- [ ] Backup/migration/recovery procedure is verified for stateful components.
- [ ] Owner reviews release candidate and the configured release policy permits the next action.

## Completed bounded repair milestone

- [x] Explicit Gemini/Groq adapters and trusted startup registration.
- [x] Selected-file context and versioned skill checksums.
- [x] Durable proposals, request deduplication and no automatic generation replay.
- [x] Strict patch validation and atomic controller acceptance into coding runs.
- [x] Negative/restart/concurrency/migration/approval checks and two real online fixture repairs.
- [ ] Windows project/proposal/approval/run/evidence interface and subsystem canvas.
- [ ] Approved plan-to-build execution, new-file delivery, scheduling and representative evaluations.

These completed items cover the bounded repair subset; broad baseline phases below remain open until all their acceptance criteria are met.

## Windows control slice checkpoint

- [x] Dedicated subsystem canvas and explicit unavailable/planned states.
- [x] Project/policy controls with exact grants and optimistic policy version checking.
- [x] Proposals, approval inbox, run checkpoints/evidence, stored conversations and events.
- [x] Native allowlisted bridge, DPAPI provisioning and hidden launcher ownership tests.
- [x] Production UI build and thirteen browser acceptance cases.
- [x] Confirm/record native end-to-end release acceptance in the owning development tracker (2026-10-15).
- [ ] Configuration editing, controlled project build loops and executable workflow authoring.
- [ ] Packaged backend, installer/signing/updates, login startup/mobile pairing and crash supervisor.

The broad baseline phases remain open unless their full acceptance criteria have evidence.

## Conversation and draft planning

- [x] Durable model chat and structured draft planning, scoped to a project conversation.
- [x] Provider selection, persisted request review, usage, safe errors and interruption.
- [x] Setup-readiness checklist and chat-only provider configuration without a worker.
- [x] Migration/restart/concurrency/atomicity and browser acceptance checks.
- [x] Final Windows executable: model chat, structured plans, setup readiness and existing repair/tray regression acceptance.
- [ ] Full configuration editor, streaming replies, plan-to-build approval workflow and document/file delivery.

## Flexible 3D workspace

- [x] Interactive 3D core and separate core/system-map views.
- [x] Bounded tabs: create, switch, reorder, minimize, restore, close and keyboard navigation.
- [x] Preserve visited tab drafts across switching/minimization; restore tab metadata after restart.
- [x] Card/panel popouts, native sizing/minimize/maximize/fullscreen and show-all controls.
- [x] Save/restore window geometry with disconnected-monitor recovery.
- [x] Final native acceptance: simultaneous independent panels, native controls and saved/offscreen restoration.
- [ ] Full internal docking/tiled-panel editor, named layout profiles and installer delivery.


## Versioned specification workflow - 2026-10-15

- [x] Persist versioned specification bundles from completed project plans.
- [x] Review and approve an exact document checksum; supersede older approvals.
- [x] Bind an optional approved specification to selected-file repair proposals and reject stale handoffs.
- [ ] Author complete architecture/design/security specifications from richer requirements.
- [ ] Add explicit document file export and the general new-file project build loop.


## Specification revision and delivery - 2026-10-15

- [x] Immutable owner-authored document revisions with parent provenance, CAS and request deduplication.
- [x] Add optional architecture/design/development/API/security documents without fabricating content.
- [x] Native approved-document delivery, manifest integrity and verified non-overwriting repeat export.
- [ ] General new-file project builds and packaging remain open; bounded source delivery is completed below.


## Reviewed new-file coding - 2026-10-15

- [x] Explicit absent targets, non-overwriting create operation and additions in diff evidence.
- [x] Model proposal validation, stale-absence rejection and approval-controlled creation/test workflow.
- [x] Real missing-module baseline failure followed by protected passing test in a temporary execution copy.
- [ ] General greenfield scaffold generation, model-authored test governance and multi-iteration debugging remain open.

## Reviewed source delivery - 2026-10-15

- [x] Register separate source targets and bind reviewed manifests to physical source/snapshot configuration.
- [x] Require passing protected tests, matching tested inputs/profile and final diff evidence.
- [x] Prepare idempotent source tasks with separate current-policy approval and worker execution.
- [x] Reject stale source/snapshot/profile, revoked grants and reconfigured targets.
- [x] Preserve original bytes and durable recovery journals; report partial writes without automatic replay.
- [x] Complete backend/API, browser, Rust and actual Windows acceptance using generated fixtures.
- [ ] General Git revision delivery, automatic recovery and unattended source writes remain outside this milestone.


## Unattended assignments requirement - 2026-10-15

- [x] Verify and complete bounded reviewed source delivery as a prerequisite; unattended source writes remain disabled.
- [x] Implement a durable accepted-run assignment state machine and automatic authorized-step progression.
- [x] Separate hidden runner lifecycle from dashboard closure; add pause/resume/cancel and graceful background stop.
- [x] Persist claims/attempts, idempotent creation, conservative crash accounting and step/deadline bounds.
- [x] Provide assignment configuration and persistent progress/evidence summaries in the dashboard.
- [x] Add bounded model/test repair cycles, explicit call reservations and exact proposal review.
- [ ] Add broader goal decomposition, generic tool planning, provider backoff and token/currency budgets.
- [ ] Add scheduled start times, morning notifications and a real overnight soak test.
- [ ] Add mobile notifications/control and future remote executor support.

### Model-backed repair acceptance - 2026-10-15

- [x] Migrate schema 10 to 11 without losing existing assignments/history.
- [x] Require explicit selected-context/model consent and call/cycle/step/time limits.
- [x] Verify the protected baseline before generation; use zero calls for a passing baseline.
- [x] Bind test diagnostics to current inputs/profile/task outcome and confirmed cleanup.
- [x] Review exact context/response hashes; automatic acceptance requires explicit opt-in and full policy.
- [x] Demonstrate failed first repair -> verified failing retest -> revised proposal -> passing final run.
- [x] Reserve calls before dispatch; recover ready responses without another call and block unknown outcomes.
- [x] Share dispatch exclusion/recovery with accepted-run assignments; preserve role/control boundaries.
- [x] Verify native goal-to-reviewed-delivery workflow using deterministic provider fixtures.
- [x] Correct responsive form/checkbox overflow and keep progress visible after queuing.
- [ ] General greenfield builds, protected-test authoring, currency caps and production deployment remain outside this phase.

### Bounded runner acceptance - 2026-10-15

- [x] Migrate SQLite 9 to 10 without losing conversation/run history.
- [x] Scope controller creation/control separately from worker ticks; default host disablement.
- [x] Preserve approval waits without repeated attempt/event churn or paid generation.
- [x] Block uncertain claims without replay; keep reserved budget after crash.
- [x] Verify single-project dispatch, pause/restart/cancel, revoked/rejected permissions and budget limits.
- [x] Complete actual hidden-process/native desktop acceptance, including heartbeat after desktop exit.
- [ ] Acceptance: an assigned fixture continues with the dashboard closed, survives a restart, does not duplicate effects, respects approvals/budgets and reports tested output.


## Shared ELK logging and E2E suite projects - 2026-10-15

Owner-requested roadmap additions. Both are planned independent reusable projects; folders, repositories, infrastructure and production integrations are not created by this checklist update. Proposed names: skyra-observability and skyra-e2e-suite. Existing skyra-quality remains the cross-project quality dashboard/evidence/release-gate coordinator; existing skyra-incident-service remains incident intake and remediation coordination.

### skyra-observability: centralized ELK logging

Planning update 2026-10-15: the owner selected two new projects. Their six-document specifications now exist in [Observability](../../skyra-observability/README.md) and [E2E Suite](../../skyra-e2e-suite/README.md), with detailed phase tasks and database proposals. Runtime implementation, compatibility/version decisions, shared contract agreement and product integration remain pending; the following implementation checklist is not marked complete by documentation alone.

- [ ] OBS-01: Define PRD, architecture, data/retention model and service contracts before implementation; confirm Elastic component versions, compatibility, licensing and hosting requirements.
- [ ] OBS-02: Define shared structured log fields, severity and error taxonomy for each product/service. Include ECS-aligned service/environment/version/trace fields plus project, request, test-run and deployment correlation metadata.
- [ ] OBS-03: Implement language-appropriate logging adapters and a collector/ingestion pipeline, with Elasticsearch storage/search and Kibana dashboards; evaluate where Logstash is needed.
- [ ] OBS-04: Separate development, staging and production data, credentials/access, retention and capacity controls. Redact secrets and sensitive client/employee content before ingestion.
- [ ] OBS-05: Add per-project/environment dashboards for errors, trends, affected releases, request/trace investigation and ingestion health; identify silent collector failures too.
- [ ] OBS-06: Configure deduplicated error/availability alerts, severity, ownership, notification routing and incident lifecycle integration with skyra-incident-service.
- [ ] OBS-07: Connect Jarvis through scoped APIs for log investigation and evidence-backed incident analysis. Treat logs as untrusted data; no automatic source change or production release authority follows from an alert.
- [ ] OBS-08: Validate with seeded development errors, cross-service correlation, production-safe synthetic failures, redaction checks, retention/restore and alert recovery; distinguish test alerts from real incidents.

### skyra-e2e-suite: reusable E2E and visual test execution

- [ ] E2E-01: Define reusable runner/configuration contracts and product-specific test packs; inventory existing tests and integrate with skyra-quality rather than duplicate its dashboard, evidence store or release-gate logic.
- [ ] E2E-02: Establish Playwright/TypeScript execution for browser products, API-assisted setup and controlled test data. Keep native Jarvis application checks as a separate appropriate harness.
- [ ] E2E-03: Add development/staging suites for critical user journeys, authentication/roles, integration flows, responsive layouts and supported browsers. Include pre-merge and pre-release execution.
- [ ] E2E-04: Add visual regression checks with expected/actual/diff screenshots, deterministic rendering and explicit review of baseline changes; never silently approve new baselines.
- [ ] E2E-05: Publish pass/fail/skipped/flaky status, failing steps, error details, screenshots, videos where useful, Playwright traces and relevant console/network evidence to skyra-quality.
- [ ] E2E-06: Preserve initial failures and retry history, classify likely product/test/infrastructure faults and link every run to project, environment, build/revision and deployment. Correlate test-run/request/trace IDs with observability logs.
- [ ] E2E-07: Implement on-demand, CI/CD, scheduled and post-deployment runs with job isolation, concurrency limits, cancellation and artifact access/retention policies. Scrub secrets/session data from artifacts where applicable.
- [ ] E2E-08: Define a separate production-safe smoke/synthetic pack using isolated test tenants/accounts and controlled cleanup. Production writes, payments, messages and customer-data mutations require explicit test design/authorization; full destructive regression belongs in isolated environments.
- [ ] E2E-09: Integrate failing-test alerts with skyra-incident-service and Jarvis. Jarvis can inspect approved artifacts/logs, investigate a cause and prepare/test a fix within assignment permissions; release approval remains separate.
- [ ] E2E-10: Keep unit/integration coverage, vulnerability scanning and performance/load checks as explicit quality capabilities. Passing E2E tests alone is not coverage or security certification.

### Delivery order and acceptance

- [ ] Define common project/environment/build/test-run/incident identifiers and event contracts first, then instrument one representative development project.
- [ ] Demonstrate one vertical slice: seeded error -> searchable correlated logs -> E2E failure -> visible evidence -> deduplicated incident -> Jarvis investigation -> reviewed fix -> passing rerun.
- [ ] Expand reusable test packs/logging adapters to other development projects; configure production observability before broad production test scheduling.
- [ ] Verify missing telemetry, runner failure and flaky tests remain visible; green status must distinguish passed, skipped, blocked and not-run checks.
- [ ] Add both systems as honest configured/available/planned nodes in Jarvis, with deep links to logging and quality dashboards plus scoped capabilities.
- [ ] Enable bounded overnight regression and incident investigation through the planned unattended runner, with approval/budget controls and a morning summary.

Do not modify ERP, Skyra Platform, QR or the company website as part of this planning update. Their integration is future separately scoped work.

## New-project scaffold foundation - 2026-10-15

- [x] Host-owned Python JSON-function template linked to an intact approved specification.
- [x] Deterministic complete-file review with destination/profile/interpreter checksum binding.
- [x] Nine initial documents with approved-content preservation and default provenance.
- [x] Protected acceptance contract, intentionally failing stub and isolated selected-file snapshot.
- [x] Exclusive Windows publication, existing-project refusal and inspectable interrupted staging.
- [x] Inert registration handoff; real protected baseline -> model repair -> passing retest/diff -> separate approved delivery fixture.
- [x] Desktop scaffold file review, explicit consent, creation and receipt recovery.
- [x] Fixed-template registration and handoff into scoped Build jobs; arbitrary registry editor remains deferred.
- [x] Website/HTTP host template and multi-file implementation; richer independent acceptance remains deferred.
- [ ] Larger real-project evaluation, dependency/install governance, security/coverage integration and overnight soak.


## Integrated project-building milestone - 2026-10-15

- [x] Connect reviewed scaffold creation to durable registration without per-project JSON merges.
- [x] Require exact native-command consent and separate version-checked resource grants.
- [x] Add website/HTTP host template with real protected request tests and editable HTML.
- [x] Bind registered profile/interpreter and protect contract/transport against generic writes.
- [x] Integrate scoped bounded repair jobs and separately reviewed final delivery.
- [x] Verify restart restore, failed-first repair, passing second repair and reviewed source delivery in integration tests.
- [x] Complete final production Windows acceptance; record evidence in project memory and owning DEVELOPMENT.md.
- [ ] Evaluate larger real projects, governed dependencies, independent coverage/security and overnight soak.


## Unattended operations milestone - 2026-10-16

- [x] Schema-13 immutable outcome snapshots with transactional event capture and current-outcome migration backfill.
- [x] Quiet repeated waits, persistent acknowledgement, owner/controller scope and paginated history.
- [x] Current work/deadline/budget visibility, Activity unread indicator and saved project library.
- [x] Reopen registered build/delivery workflows without re-entering scaffold details.
- [x] Unit/API migration, rollback, scope, deduplication, evidence and browser recovery checks.
- [x] Complete production native acceptance including a queued repair after dashboard exit/worker restart and outcome recovery after dashboard reopen.
- [x] One-time scheduled starts are implemented below; recurrence, remote/mobile notifications, Windows startup/wake behavior and overnight soak remain future work.


## Scheduled background builds - 2026-10-16

- [x] Add one-time bounded start time/window to existing build jobs without changing immediate-job behavior.
- [x] Persist future next_due and planned-start-relative runtime deadline.
- [x] Bind selected inputs/specification through pending first-baseline approval; refuse stale/missed starts without execution.
- [x] Preserve not-before on pause/resume and idempotent request recovery after time/input changes.
- [x] Add schema-14 scoped request-contact persistence with guarded completion, migration and honest UI.
- [x] Verify scheduling, cancellation, restart, approval waits, role separation and local-time review in unit/API/browser tests.
- [x] Complete native scheduled execution with dashboard closed, proof of worker contact before due and zero early work, then reopened outcome.
- [ ] Recurrence, schedule editing, wake/login startup, remote notifications and full overnight soak remain pending.


## Active development plan - coding agent and Jarvis identity - 2026-10-16

This section is the current priority order and supersedes older next-step lists. Items are planned unless checked. Existing schema-14 capabilities remain implemented; this plan does not claim a general coding agent already exists. The owner requests continuous development, no staging/committing/pushing and no commit messages. Do not pause at small tasks or routine milestone boundaries; ask only when a material unanswered question blocks safe progress. Maintain the original documents in place.

### Milestone A - usable coding agent and durable sessions (first priority)

- [ ] Audit current repair, conversation and runner storage; document message/tool/evidence relationships and recovery gaps before changing schema.
- [ ] Add repository inspection and bounded context retrieval behind project/resource grants. Inventory structure, identify technology/build entry points, read/search relevant files, expose omitted context and preserve file hashes. Exclude credentials, generated dependencies and links outside approved roots.
- [x] Introduce feature-building mode without requiring a failing baseline. A passing baseline is reference evidence, not proof that requested work is implemented. Preserve the repair mode and protected acceptance tests.
- [x] Add reviewed snapshot refresh/source-revision continuity after delivery. Preserve old baseline evidence and detect owner/source edits; never silently rebase hashes to bypass delivery conflicts.
- [ ] Add durable streaming/progress events and measured context-retrieval latency; keep incomplete streamed output distinct from a validated final response.
- [ ] Persist implementation plans, task dependencies, assumptions, acceptance criteria, progress and concise decision summaries. Model-generated plans cannot authorize tools or override owner requirements.
- [x] Support reviewed multi-file edits and explicitly selected absent creation targets inside approved workspaces, preserving conflict checks, protected files, bounded diffs and separate source delivery. Arbitrary path selection by the model remains pending; keep modules focused and reuse existing capabilities.
- [ ] Add governed technology-specific install/build/test commands and development-server lifecycle. Record lockfile/dependency changes, command intent/results, timeouts and cleanup. Dependency installation and arbitrary shell execution are distinct authorities. Include explicit long-build profiles: the original 300-second cap has been replaced with explicitly bounded longer native profiles and parent supervision, but technology-specific build/dependency environments remain pending; preserve bounded cleanup/cancellation and existing short-test limits.
- [ ] Implement inspect -> plan -> act -> verify -> revise iteration with meaningful stop conditions, stale-context recovery, cancellation, budgets and independently verified completion.
- [ ] Add provider capability discovery and model-specific structured/tool adapters. Benchmark Gemini/Groq candidates on identical tasks before selecting defaults. Model availability and account quotas are runtime facts, not permanent assumptions in prompts.
- [ ] Persist quota backoff/resume, exact model provenance and provider-switch consent; no silent paid fallback or automatic replay of an uncertain external operation.
- [ ] Exercise durable sessions through crash/restart, context compaction, long conversations, interrupted model/tool calls, approval changes and project switching. Original history remains retrievable; compaction is a derived view.
- [ ] Gate: complete a new feature across multiple files, detect a deliberate defect using independent checks, repair it, recover after restart without duplicate effects, and present inspectable code/test evidence.

### Milestone B - supervised internal project 1

- [ ] Use Jarvis itself to build a small internal task tracker with persistence, validation and follow-up features. Keep scope bounded so this evaluation does not delay visual testing.
- [ ] Define architecture and acceptance tests before generation; record immutable task inputs, selected model/skill versions, tool events, changes, failures and manual interventions.
- [ ] Independently review functionality, architecture, duplication, security, accessibility and visible behaviour. Agent-written tests complement independently maintained acceptance tests.
- [ ] Classify failures as model/context/tool/session/policy/test/infrastructure issues; fix the agent when appropriate, then rerun the failed task and representative earlier tasks.
- [ ] Gate: label exactly which code Jarvis produced and which changes the supervising developer made. Do not count manual rescue as autonomous completion.

### Milestone C - supervised internal project 2: reusable visual testing engine

- [ ] Build skyra-e2e-suite using the coding agent: TypeScript/Playwright execution with versioned request/result contracts and isolated browser contexts.
- [ ] Accept project/environment identifiers and explicitly configured local/deployed HTTP(S) base URLs. Keep test credentials as secret references, not plain-text test steps.
- [ ] Support navigate, fill, click and explicit URL/text/visibility assertions with bounded waits, stable locators and actionable failing-step evidence.
- [ ] Preserve per-attempt outcomes, screenshots, traces, console/network diagnostics and cleanup/cancellation evidence. Distinguish failed, flaky, blocked, skipped and not-run.
- [ ] Introduce visual expected/actual/diff evidence with deterministic viewport/browser metadata and explicit owner approval of baselines. An agent must not approve its own visual changes as the baseline.
- [ ] Expose the same engine through a local CLI and versioned API; Jarvis uses an adapter over that contract. MCP can be added as a transport later, without duplicating execution logic.
- [ ] Gate: an independent fixture demonstrates successful login flow, intentional failure, bad selector, unavailable URL, timeout, cancellation and secret-safe artifacts.

### Milestone D - supervised internal project 3: testing dashboard

- [ ] Build the focused skyra-quality dashboard using Jarvis. Register projects and named local/staging/production environments with base URLs such as http://localhost:4200.
- [ ] Provide case/step editor, suites, manual run/cancel, live progress, run history and failed-step/artifact review. Never permit dashboard test input to become arbitrary host code.
- [ ] Use skyra-e2e-suite as the single execution engine for dashboard and Jarvis. Dashboard operation must not depend on Jarvis being open.
- [ ] Start with a local worker able to reach laptop localhost. A future hosted dashboard needs an authenticated local worker for laptop URLs; server-side localhost is not the user's laptop.
- [ ] Independently assess all three projects, compare quality/speed/intervention metrics, fix agent regressions and rerun the common evaluation suite.
- [ ] Gate: register a fixture project, run the same case manually and from Jarvis, inspect the same result contract, and demonstrate local plus deployed-URL configuration. Apply to the article client project only after internal validation and separately scoped project access.

### Parallel workstream - Jarvis branding, glossy surfaces and honest orb states

- [ ] Audit current UI states and consolidate shared typography/colour/spacing/surface/motion tokens. Preserve existing tabs, workflow organisation, resizable native windows and saved arrangements.
- [ ] Apply deep navy readable surfaces with restrained cyan/violet identity, glass reflections and subtle gloss. Long code/log/conversation content remains high contrast. Bundle licensed fonts locally; do not depend on runtime font CDNs.
- [ ] Create a reusable orb presentation component and tested activity resolver. States: offline, idle, listening, planning, coding, testing, speaking, approval required, blocked/failed and completed. Status comes from real scoped activity, never timers pretending progress.
- [ ] Keep activity scope visible; a foreground conversation and background build may coexist. Speaking is driven by actual playback amplitude only when an audio pipeline exists; do not simulate voice readiness.
- [ ] Add accessible status labels, keyboard/focus treatment, reduced motion/transparency and hidden-window animation suspension. Use progressive effects with solid-surface fallback.
- [ ] Gate: inspect screenshots and interactions at narrow/large widths and detached windows; verify contrast, reduced preferences and correct activity transitions. No unsupported subsystem may appear connected.

### Evaluation and release discipline

Completion means requirements independently demonstrated, not a model reporting success or all agent-authored tests passing. Track task completion, acceptance failures, elapsed active/wall time, tokens/calls, retries, manual interventions, session recovery and architecture/security findings. Retain initial failures and attribution. Do not promise superiority over other tools without comparable measurements.

Use unit tests for boundaries/state, integration tests for persistence/providers/tools, independent end-to-end fixtures for agent tasks and real Windows acceptance for native behaviour. Deterministic fixtures establish regressions; controlled real-model runs establish actual model performance and must remain labelled separately. Preserve configured privacy/usage permissions and never commit runtime sessions, secrets or artifacts.

Deferred behind the coding/testing priority: broader ELK integration, incident automation, recurring schedules, mobile pairing, local-model hardware support and hosted operation. Existing approved controls remain intact. ERP, QR, Skyra Platform and the company website stay outside this work.

### Continuation implementation checkpoint - 2026-10-16

- [x] Add reviewed storage primitive for a separate snapshot generation, preserving historical evidence and rejecting selected-source drift.
- [x] Connect generation lineage to durable registration and explicit owner review without rebinding historical resources or automatically granting permissions.
- [x] Verify two tested deliveries across distinct generations with registry restart using the actual worker/Windows executor; verify controller API roles/status/catalog and native registration plus dashboard-restart recovery independently. These deterministic fixtures establish continuity, not real-model project performance.

### Conversation provenance checkpoint

- [x] Link explicitly selected build jobs to same-project conversation history without copying messages or changing model context.
- [x] Add foreign-key-backed storage, cursor-bounded history and inspection of cycle/model/run/delivery/generation references.
- [x] Complete final production/native verification of linked history after dashboard restart; accepted evidence: .runtime/desktop-native-1792146653029/review.json.
- [ ] Broader session work remains: model-driven tool/repository retrieval, coherent interactive coding turns, context compaction, supervised real-model internal projects and long-build supervision. An execution-history link alone does not complete those gates.

### Bounded retrieval checkpoint

- [x] Add opt-in local retrieval over an approved snapshot candidate scope, with whole-file budget, retained protected tests, omissions and content-addressed read evidence.
- [x] Bind retrieval to each coding cycle; recover completed reads, reject stale omitted candidates, and prevent patches outside supplied model context.
- [x] Add desktop mode/consent controls and shared retrieval evidence review in proposal screens; link read tasks into coding history.
- [x] Complete final packaged Windows acceptance of retrieval on both failed-first/successful-second cycles; .runtime/desktop-native-1792148593369/review.json passed.
- [ ] Model-driven repository/tool selection, semantic retrieval, arbitrary new paths, dependency installation and long-build supervision remain pending. Do not count lexical snapshot selection as those capabilities.


### Explicit conversational coding context checkpoint

- [x] Audit existing conversation/model-turn and job-link storage; reuse model_turns.context for immutable derived history instead of duplicating jobs/messages.
- [x] Capture owned, bounded, explicitly requested history with recorded-status references, goal excerpts/checksums and request identity.
- [x] Add per-request desktop opt-in and saved-context inspection; preserve ordinary request compatibility and separate execution permissions.
- [x] Complete final browser/Windows packaged acceptance; .runtime/desktop-native-1792150134459/review.json passed.
- [ ] General interactive coding sessions, derived context compaction, streaming progress, model-directed tool iteration and supervised real-model project builds remain open.


### Supervised long execution and background fairness

- [x] Add explicit longer native timeouts while retaining existing profile hashes, short defaults and owner-enabled execution.
- [x] Supervise parent/task leases, deadlines and ownership; retain no-replay and exact cancellation/cleanup evidence.
- [x] Add bounded independent project polling and shared observed supervision timing in build/assignment screens.
- [x] Reuse strict response/usage/failure validation across conversation and coding generation.
- [x] Complete real 610-second acceptance across former timeout/lease limits; packaged long-supervision acceptance passed at .runtime/desktop-native-1792152229866/review.json. Retain interrupted evidence.
- [ ] Governed technology-specific dependencies/build outputs and development-server lifecycle remain open.

### Real-provider coding calibration and edit reliability

- [x] Diagnose real provider failures without storing raw invalid responses in production; expose bounded validation codes.
- [x] Introduce host-bound versioned edits, preserve legacy request identity and canonical exact review/worker checks.
- [x] Verify CRLF handling, protected creation, instruction/schema freshness, restart and full native retests in regression.
- [x] Exercise Gemini and Groq on generated internal task-store foundations; independently review code and expose gaps beyond supplied tests.
- [x] Add explicit versioned persistence-integrity/review guidance and strengthen corruption/type/whitespace/root-container checks.
- [x] Complete final packaged native acceptance for host-bound desktop builds: .runtime/desktop-native-1792401762949/review.json.
- [x] Establish an independently accepted task-store foundation calibration (Gemini v5).
- [ ] Establish supervised multi-revision real-provider repair evidence and browser-reviewed task-board completion.
- [ ] Build and review the three planned internal projects; no calibration fixture counts as a completed project.

### Supervised application evidence and next integration work — 2026-10-19

- [x] Build a four-file task-board application using the coding runtime and reused agent-authored persistence; manually inspect every accepted model revision.
- [x] Demonstrate real-provider failed-test repair, controller rejection of a wrong correction, unchanged-output rejection and a later accepted correction; retain all call/evidence records.
- [x] Independently verify 16 protected tests and ten browser checks over verified execution copies. This is an evaluation application, not full product promotion.
- [x] Add explicit configured reasoning depth, immutable settings, reported reasoning counts and private-thought exclusion for the verified Gemini adapter.
- [x] Bind independent findings to current source/test evidence before creating a separately bounded revision job.
- [ ] Generalize supervised application execution into the governed reusable E2E runner and product/project configuration.
- [ ] Integrate durable interactive coding plans, model-directed tools, session compaction and full project promotion; the three complete internal-product milestone remains open.
- [ ] Complete the Jarvis activity/identity workstream with real scoped orb states and shared glossy design tokens.

### Activity/identity integration checkpoint

- [x] Add owned, consistent count-only activity projection with live-lease and pending-request distinctions.
- [x] Add pure scoped resolver, concurrent activity disclosure, missing/foreign-host fallback and recorded observation time.
- [x] Apply shared glossy surfaces and state-coloured sphere presentation while preserving rotation, tabs and native controls.
- [x] Verify 53 browser checks and Core privacy/ownership/state checks; keep initial failures attributable.
- [x] Complete actual Windows minimize/recovery acceptance and final packaged visual inspection (.runtime/desktop-native-1792407281506).
- [x] Add shared build/proposal selection with frozen revision pins, changed-guidance consent reset and schedule/dispatch guards; persisted pins independently verified in final native acceptance.
- [ ] Voice playback/listening, audio-driven speaking, event-linked completion and licensed bundled font assets remain future work.

### Reviewed model failure recovery

- [x] Distinguish incomplete/output-limited responses and retain validated token counts without partial output.
- [x] Read conversation coding history consistently during concurrent runner updates.
- [x] Add explicit controller-only recovery within original budgets, immutable failure history, current input/skill checks and durable retry identity.
- [x] Add dashboard exact-proposal review, fresh consent, budget disclosure and fixed native route. Browser and focused integration checks passed.
- [x] Complete full regressions and final rebuilt Windows acceptance for failure/review/new call/retest (.runtime/desktop-native-1792425288344).
- [ ] Automatic backoff/retry policies remain unimplemented; general interactive coding tools and full supervised products remain open.

### Node/TypeScript supervised foundation checkpoint

- [x] Exercise real installed Node through reviewed multi-file jobs, restart and syntax-error repair with deterministic providers.
- [x] Add protected strict TypeScript calibration, executable/version admission and independent current-input test identities.
- [x] Use real Gemini/Groq proposals to build the E2E target-profile foundation; preserve output-limit, behavior and compiler failures.
- [x] Have the agent refactor independently identified duplication/unsafe typing; preserve passing behavior and verify exact provenance.
- [x] Expose the reviewed Node/TypeScript library template, owner-configured toolchain and native acceptance (.runtime/desktop-native-1792430552451).
- [ ] Build the E2E step/execution engine and dashboard through the agent; no full product is counted by target validation alone.

## Commercial coding-tool delivery plan - 2026-10-20

- [x] Record the standalone commercial product goal and shared engine/host boundaries.
- [x] Implement and regression-test existing-project import, reviewed registration, original-document preservation and Node compiler bindings.
- [x] Finish updated packaged Windows acceptance for existing-project import (.runtime/desktop-native-1792443916615).
- [x] Introduce the reusable bounded inspection tool port over existing task/evidence/policy contracts.
- [ ] Add the model-driven session planner and durable session/checkpoint events over the tool port.
- [ ] Add inspect/search/read/propose/test/revise progression, bounded model calls, exact approvals, cancellation and uncertain-call recovery.
- [ ] Add context checkpoints/compaction, selected-file expansion review and session restart/export verification.
- [ ] Add governed acceptance/bootstrap for documentation-only projects and dependency/dev-server lifecycle.
- [ ] Build the reusable E2E execution product using the coding tool; independently review code, tests and failure recovery.
- [ ] Build the test-management/dashboard product using the same tool and E2E engine; validate local and deployed targets.
- [ ] Complete and independently review a third internal product; publish internal task-quality/latency/call-budget evidence.
- [ ] Deliver standalone coding desktop/CLI packaging, onboarding, credentials, signed updates and support diagnostics.
- [ ] Implement hosted tenant isolation, entitlements/usage accounting and commercial beta operations before accepting customer-hosted workloads.
- [ ] Confirm final coding-product brand and release packaging before public distribution.


## Owner priority: real E2E product and professional coding workspace - 2026-10-20

The real skyra-e2e-suite is the next coding-agent workload. Do not assign unrelated demonstration applications. Reuse the delivered target foundation; advance pack validation, Playwright execution, report/CLI and independent visual/failure acceptance. Fix agent defects found during this work and retain attribution/session evidence.

The coding product needs its own desktop workspace: native project-folder selection with explicit trust/resource grants, a project/session sidebar, durable chat/tool/history across restart, model selection and supported effort settings, file/context inspection, editor/diff review, tests/results, cancellation and background status. Jarvis's current orchestration panels are not the finished commercial coding interface. Use one engine and persisted session contracts rather than duplicating coding behavior into a visual shell. Actual folder-picker/session-workspace implementation remains pending.
