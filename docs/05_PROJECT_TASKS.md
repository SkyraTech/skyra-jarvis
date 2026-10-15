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
