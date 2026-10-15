# Skyra Coding Worker — Project Tasks

## Maintained specification — current status

Updated 2026-10-15. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented: selected-file snapshots, guarded file operations, explicitly owner-enabled native Windows test execution and durable controller-supplied repair workflows. Online-model patch generation, branch/revision delivery and the new desktop are pending. Native execution carries Windows account privileges; Docker isolation is optional and not live-verified.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](../../../docs/ARCHITECTURE.md)
- [Current functionality and implementation boundaries](../../../docs/FUNCTIONALITY.md)
- [Current milestone and verification summary](../../../docs/DEVELOPMENT.md)

Prepared: 2026-10-14. Requirement/design baseline. Use the maintained current-status section above to distinguish implemented work from planned work.

## Planning baseline

## Executable repair workflow checkpoint — 2026-10-14

- [x] NATIVE-01: Implement explicitly enabled trusted Windows profiles and process-tree supervision.
- [x] NATIVE-02: Verify real test failures/passes, timeout, child termination, cancellation and output caps.
- [x] RUN-01: Implement persistent fail/patch/retest/diff pipeline and controller-only plans.
- [x] RUN-02: Verify approvals, restart checkpoints, protected tests, evidence gates and run idempotency.
- [x] RUN-03: Produce a repeatable demo review bundle without changing source/Git state.
- [ ] ISOLATION-01: Verify real Docker/OS isolation. Native mode has the account's file/network access.

See [maintained architecture](../../../docs/ARCHITECTURE.md#worker-and-execution-boundaries). This completes trusted native workflow execution; it does not mark stronger security isolation, model planning, Git branch delivery or deployment complete.

## File-worker foundation checkpoint — 2026-10-14

- [x] FILE-001: Prepare bounded selected-file snapshots without changing source files or Git state.
- [x] FILE-002: Implement scoped read/search, hash-checked exact patches, baseline diffs and static verification.
- [x] FILE-003: Connect trusted workspace registration and lease-guarded operations to the authenticated core API.
- [x] FILE-004: Store checksum-addressed reports and restrict evidence retrieval to the owning task/project.
- [x] FILE-005: Run adversarial/integration checks and core regression suite; document limitations.
- [ ] EXEC-001: Provision and verify an OS/container process boundary before enabling build/test commands.

Earlier file-only checkpoint: 38 core and 17 worker tests passed, with one symlink skip. It initially left execution disabled. The later native milestone above enabled owner-approved fixed test profiles for trusted projects. Stronger OS isolation, branch/revision delivery, parallel workers and release phases remain open; see [current architecture](../../../docs/ARCHITECTURE.md).

The [coding-engine performance direction](../../../docs/ARCHITECTURE.md#coding-engine-performance-direction--planned) covers benchmarking, context retrieval, model routing and performance validation. Those performance/model tasks supplement the worker phases below and remain planned.

Broad phase tasks below require their own acceptance evidence; implemented milestone summaries above take precedence over older baseline status. Existing prototype code may satisfy a task only after it is checked against the target acceptance criteria. Assign a named owner and estimate before starting; dates are not invented here.

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

## Model proposal integration

The controller can now accept a validated Gemini/Groq proposal into this worker's existing repair workflow. The runtime selects context/skills and validates patches; this worker retains protected-test, policy/approval, native-execution and evidence gates. Acceptance does not execute a task. General building and autonomous scheduling remain pending. See the owning Jarvis architecture/development records for schema 6, API and verified fixture evidence.


## Reviewed new-file coding - 2026-10-15

- [x] Explicit absent targets, non-overwriting create operation and additions in diff evidence.
- [x] Model proposal validation, stale-absence rejection and approval-controlled creation/test workflow.
- [x] Real missing-module baseline failure followed by protected passing test in a temporary execution copy.
- [ ] General greenfield scaffold generation, model-authored test governance, multi-iteration debugging and source delivery remain open.
