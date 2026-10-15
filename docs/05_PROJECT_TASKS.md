# Jarvis Orchestration Core — Project Tasks

## Maintained specification — current status

Updated 2026-10-15. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented and verified: durable core, authenticated local API, selected-file worker, owner-enabled native Windows tests, repair workflows and bounded Gemini/Groq repair proposals with versioned skill context and controller review. Native desktop control, flexible 3D/tabbed/multi-window workspace, model-backed conversation, structured draft planning and setup-readiness guidance are implemented. General autonomous building, a full configuration editor, installer/update delivery and mobile pairing remain pending.

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
- [ ] Add broader goal decomposition, iterative model repair, provider backoff and call/token/spend reservations.
- [ ] Add scheduled start times, morning notifications and a real overnight soak test.
- [ ] Add mobile notifications/control and future remote executor support.

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
