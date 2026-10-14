# Skyra Coding Worker — Project Tasks

Prepared: 2026-10-14. Status: proposed implementation baseline. User requirements are captured here; technical choices remain subject to implementation validation.

## Planning baseline

The [coding-agent research and performance plan](10_CODING_AGENT_RESEARCH_AND_PLAN.md) adds CA-01 through CA-07 for benchmarking, context retrieval, model routing and performance validation. These supplement the worker tasks below; all remain open.

All implementation tasks below are open. Existing prototype code may satisfy a task only after it is checked against the target acceptance criteria. Assign a named owner and estimate before starting; dates are not invented here.

## Phase 1: Prove a Windows-compatible isolation boundary and workspace lifecycle

- [ ] CODING_WORKER-P1-01: Define scope, affected requirements and failure cases for this phase.
- [ ] CODING_WORKER-P1-02: Implement: prove a Windows-compatible isolation boundary and workspace lifecycle.
- [ ] CODING_WORKER-P1-03: Run relevant contract, integration and acceptance checks; attach evidence.
- [ ] CODING_WORKER-P1-04: Review permissions, recovery and documentation; record completion in memory.

Exit gate: implementation is demonstrated against its mapped requirements; failures and follow-up work are recorded. No phase is complete merely because its files exist.

## Phase 2: Implement file, patch and process tools with event capture

- [ ] CODING_WORKER-P2-01: Define scope, affected requirements and failure cases for this phase.
- [ ] CODING_WORKER-P2-02: Implement: implement file, patch and process tools with event capture.
- [ ] CODING_WORKER-P2-03: Run relevant contract, integration and acceptance checks; attach evidence.
- [ ] CODING_WORKER-P2-04: Review permissions, recovery and documentation; record completion in memory.

Exit gate: implementation is demonstrated against its mapped requirements; failures and follow-up work are recorded. No phase is complete merely because its files exist.

## Phase 3: Integrate test profiles, artifact upload and selected-change delivery

- [ ] CODING_WORKER-P3-01: Define scope, affected requirements and failure cases for this phase.
- [ ] CODING_WORKER-P3-02: Implement: integrate test profiles, artifact upload and selected-change delivery.
- [ ] CODING_WORKER-P3-03: Run relevant contract, integration and acceptance checks; attach evidence.
- [ ] CODING_WORKER-P3-04: Review permissions, recovery and documentation; record completion in memory.

Exit gate: implementation is demonstrated against its mapped requirements; failures and follow-up work are recorded. No phase is complete merely because its files exist.

## Phase 4: Add parallel workspaces, conflict handling and crash reconciliation

- [ ] CODING_WORKER-P4-01: Define scope, affected requirements and failure cases for this phase.
- [ ] CODING_WORKER-P4-02: Implement: add parallel workspaces, conflict handling and crash reconciliation.
- [ ] CODING_WORKER-P4-03: Run relevant contract, integration and acceptance checks; attach evidence.
- [ ] CODING_WORKER-P4-04: Review permissions, recovery and documentation; record completion in memory.

Exit gate: implementation is demonstrated against its mapped requirements; failures and follow-up work are recorded. No phase is complete merely because its files exist.

## Phase 5: Validate remote workers and controlled deployment adapters

- [ ] CODING_WORKER-P5-01: Define scope, affected requirements and failure cases for this phase.
- [ ] CODING_WORKER-P5-02: Implement: validate remote workers and controlled deployment adapters.
- [ ] CODING_WORKER-P5-03: Run relevant contract, integration and acceptance checks; attach evidence.
- [ ] CODING_WORKER-P5-04: Review permissions, recovery and documentation; record completion in memory.

Exit gate: implementation is demonstrated against its mapped requirements; failures and follow-up work are recorded. No phase is complete merely because its files exist.

## Dependencies and sequencing

- [skyra-service-contracts](../../../../skyra-service-contracts/README.md)
- [skyra-service-foundation](../../../../skyra-service-contracts/packages/foundation/README.md)
- [skyra-github-service](../../../../skyra-github-service/README.md)
- [skyra-quality](../../../../skyra-quality/README.md)

Start with contracts and the smallest complete workflow. Agree interfaces early; do not wait for every neighboring project to be complete. Mock fixtures are useful for development but must be replaced with isolated integration evidence before release.

## Cross-cutting release checklist

- [ ] Acceptance matrix has evidence against a commit and environment.
- [ ] Permission, isolation, restart and duplicate-delivery cases pass where applicable.
- [ ] Secrets are protected and logs are sanitized.
- [ ] Backup/migration/recovery procedure is verified for stateful components.
- [ ] Owner reviews release candidate and the configured release policy permits the next action.
