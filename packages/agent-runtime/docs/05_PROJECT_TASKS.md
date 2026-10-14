# Skyra Agent Runtime — Project Tasks

## Maintained specification — current status

Updated 2026-10-14. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Planned component. The new model-driven planning/patch engine and skill runtime are not implemented. Existing legacy model adapters do not establish integration with the new durable core.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](../../../docs/ARCHITECTURE.md)
- [Current functionality and implementation boundaries](../../../docs/FUNCTIONALITY.md)
- [Current milestone and verification summary](../../../docs/DEVELOPMENT.md)

Prepared: 2026-10-14. Requirement/design baseline. Use the maintained current-status section above to distinguish implemented work from planned work.

## Planning baseline

Broad phase tasks below require their own acceptance evidence; implemented milestone summaries above take precedence over older baseline status. Existing prototype code may satisfy a task only after it is checked against the target acceptance criteria. Assign a named owner and estimate before starting; dates are not invented here.

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
