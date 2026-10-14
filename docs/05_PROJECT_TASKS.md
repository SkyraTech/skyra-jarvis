# Jarvis Orchestration Core — Project Tasks

Prepared: 2026-10-14. Status: proposed implementation baseline. User requirements are captured here; technical choices remain subject to implementation validation.

## Planning baseline

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

API checkpoint (2026-10-14): 38 core/API tests passed. SQLite v1→v2 migration preserves existing projects; task retries are idempotent across app restart. No model execution, command executor or desktop wiring was introduced. See [local API integration guide](../services/core/API.md). Development pauses here for the owner's manual review/commit before worker integration.

See [implementation evidence and limits](14_CORE_BASELINE_IMPLEMENTATION.md). CORE-001 is local hygiene, not a claim of completed credential revocation or history cleanup.

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
