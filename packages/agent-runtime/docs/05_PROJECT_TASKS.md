# Skyra Agent Runtime — Project Tasks

## Maintained specification — current status

Updated 2026-10-15. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented first repair runtime: explicit Gemini/Groq adapters, bounded selected-file context, versioned trusted skill loading, durable proposals and controller acceptance into tested coding runs. Durable chat and structured draft planning are also implemented without requiring a coding worker. General execution planning, skill discovery, teaching memory and autonomous scheduling remain pending. Legacy adapters remain separate.

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

## Completed bounded repair milestone

- [x] Explicit Gemini/Groq adapters and trusted startup registration.
- [x] Selected-file context and versioned skill checksums.
- [x] Durable proposals, request deduplication and no automatic generation replay.
- [x] Strict patch validation and atomic controller acceptance into coding runs.
- [x] Negative/restart/concurrency/migration/approval checks and two real online fixture repairs.
- [ ] Windows project/proposal/approval/run/evidence interface and subsystem canvas.
- [ ] General project planning, new-file delivery, scheduling and representative evaluations.

These completed items cover the bounded repair subset; broad baseline phases below remain open until all their acceptance criteria are met.

## Conversation and draft planning

- [x] Durable model chat and structured draft planning, scoped to a project conversation.
- [x] Provider selection, persisted request review, usage, safe errors and interruption.
- [x] Setup-readiness checklist and chat-only provider configuration without a worker.
- [x] Migration/restart/concurrency/atomicity and browser acceptance checks.
- [x] Final Windows executable: model chat, structured plans, setup readiness and existing repair/tray regression acceptance.
- [ ] Full configuration editor, streaming replies, plan-to-build approval workflow and document/file delivery.


## Versioned specification workflow - 2026-10-15

RepairRuntime.create accepts an optional approved specification ID. The same-project version/checksum/documents are embedded in immutable model context and included under the existing context-size limit. Approval freshness is checked before generation, after provider completion and at acceptance; supersession blocks pending handoffs. Publication is an offline Core operation sourced from completed planning turns. General new-file builds remain pending. Exact schema, endpoints and verification are maintained in the owning Jarvis ARCHITECTURE.md and DEVELOPMENT.md.
