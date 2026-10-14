# Skyra Agent Runtime — Project Tasks

Prepared: 2026-10-14. Status: proposed implementation baseline. User requirements are captured here; technical choices remain subject to implementation validation.

## Planning baseline

All implementation tasks below are open. Existing prototype code may satisfy a task only after it is checked against the target acceptance criteria. Assign a named owner and estimate before starting; dates are not invented here.

## Phase 1: Define execution envelopes, skill manifest extensions and model capability matrix

- [ ] AGENT_RUNTIME-P1-01: Define scope, affected requirements and failure cases for this phase.
- [ ] AGENT_RUNTIME-P1-02: Implement: define execution envelopes, skill manifest extensions and model capability matrix.
- [ ] AGENT_RUNTIME-P1-03: Run relevant contract, integration and acceptance checks; attach evidence.
- [ ] AGENT_RUNTIME-P1-04: Review permissions, recovery and documentation; record completion in memory.

Exit gate: implementation is demonstrated against its mapped requirements; failures and follow-up work are recorded. No phase is complete merely because its files exist.

## Phase 2: Build provider adapters and a checkpointed single-agent loop

- [ ] AGENT_RUNTIME-P2-01: Define scope, affected requirements and failure cases for this phase.
- [ ] AGENT_RUNTIME-P2-02: Implement: build provider adapters and a checkpointed single-agent loop.
- [ ] AGENT_RUNTIME-P2-03: Run relevant contract, integration and acceptance checks; attach evidence.
- [ ] AGENT_RUNTIME-P2-04: Review permissions, recovery and documentation; record completion in memory.

Exit gate: implementation is demonstrated against its mapped requirements; failures and follow-up work are recorded. No phase is complete merely because its files exist.

## Phase 3: Add delegation, budgets, cancellation and tool-result reconciliation

- [ ] AGENT_RUNTIME-P3-01: Define scope, affected requirements and failure cases for this phase.
- [ ] AGENT_RUNTIME-P3-02: Implement: add delegation, budgets, cancellation and tool-result reconciliation.
- [ ] AGENT_RUNTIME-P3-03: Run relevant contract, integration and acceptance checks; attach evidence.
- [ ] AGENT_RUNTIME-P3-04: Review permissions, recovery and documentation; record completion in memory.

Exit gate: implementation is demonstrated against its mapped requirements; failures and follow-up work are recorded. No phase is complete merely because its files exist.

## Phase 4: Implement repeatable evaluation suites and quality evidence integration

- [ ] AGENT_RUNTIME-P4-01: Define scope, affected requirements and failure cases for this phase.
- [ ] AGENT_RUNTIME-P4-02: Implement: implement repeatable evaluation suites and quality evidence integration.
- [ ] AGENT_RUNTIME-P4-03: Run relevant contract, integration and acceptance checks; attach evidence.
- [ ] AGENT_RUNTIME-P4-04: Review permissions, recovery and documentation; record completion in memory.

Exit gate: implementation is demonstrated against its mapped requirements; failures and follow-up work are recorded. No phase is complete merely because its files exist.

## Phase 5: Add local-model adapter interface tests; actual local inference remains future scope

- [ ] AGENT_RUNTIME-P5-01: Define scope, affected requirements and failure cases for this phase.
- [ ] AGENT_RUNTIME-P5-02: Implement: add local-model adapter interface tests; actual local inference remains future scope.
- [ ] AGENT_RUNTIME-P5-03: Run relevant contract, integration and acceptance checks; attach evidence.
- [ ] AGENT_RUNTIME-P5-04: Review permissions, recovery and documentation; record completion in memory.

Exit gate: implementation is demonstrated against its mapped requirements; failures and follow-up work are recorded. No phase is complete merely because its files exist.

## Dependencies and sequencing

- [skyra-service-contracts](../../../../skyra-service-contracts/README.md)
- [skyra-service-foundation](../../../../skyra-service-contracts/packages/foundation/README.md)
- [skyra-quality](../../../../skyra-quality/README.md)

Start with contracts and the smallest complete workflow. Agree interfaces early; do not wait for every neighboring project to be complete. Mock fixtures are useful for development but must be replaced with isolated integration evidence before release.

## Cross-cutting release checklist

- [ ] Acceptance matrix has evidence against a commit and environment.
- [ ] Permission, isolation, restart and duplicate-delivery cases pass where applicable.
- [ ] Secrets are protected and logs are sanitized.
- [ ] Backup/migration/recovery procedure is verified for stateful components.
- [ ] Owner reviews release candidate and the configured release policy permits the next action.
