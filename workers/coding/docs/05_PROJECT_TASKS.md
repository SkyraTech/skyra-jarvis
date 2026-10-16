# Skyra Coding Worker — Project Tasks

## Maintained specification — current status

Updated 2026-10-16. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented: selected-file snapshots, guarded patch/create operations, owner-enabled native Windows tests, online-model repair jobs, bounded hidden-runner progression, native desktop review and separately approved source delivery. Approved-specification scaffolds create bounded Python JSON-function projects through the desktop or owner command with protected examples. Website/full-service scaffolds, a trusted registry editor, Git branch/revision delivery and currency budgets remain pending. Native execution carries Windows account privileges; optional Docker isolation is not live-verified.

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
- [ ] General greenfield scaffold generation, model-authored test governance and multi-iteration debugging remain open.

## Reviewed source delivery - 2026-10-15

- [x] Separate trusted source registration and manifest binding to tested inputs/profile and target configuration.
- [x] Controller preparation, current-policy source approval and worker-only execution.
- [x] Conflict rejection, original-byte backups and durable partial-write journals without automatic replay.
- [x] Backend/API, browser, Rust and native Windows fixture acceptance; exact evidence in owning DEVELOPMENT.md.
- [ ] Durable unattended goal progression and Git branch/revision delivery remain future work.

## Approved-specification scaffolds - 2026-10-15

- [x] Approved-specification template, complete checksum-bound file review and exclusive publication.
- [x] Nine-document preservation/default provenance and protected failing acceptance scaffold.
- [x] Owner command with inert registry handoff and Windows boundary/failure tests.
- [x] Real native goal-to-tested-implementation and separately approved source-delivery fixture.
- [x] Desktop creation/review/receipt workflow within an explicitly configured root.
- [ ] Trusted registry editor, website/HTTP templates, broader project generation and independent quality checks.

## Desktop scaffold workflow - 2026-10-15

- [x] Host-configured desktop scaffold availability and fixed controller preview/create/status routes.
- [x] Complete file review, explicit consent, edited-plan invalidation and duplicate-dispatch guard.
- [x] Receipt recovery, missing-audit visibility and no automatic filesystem replay.
- [x] API, launcher, browser/bridge and real Windows acceptance coverage.
- [ ] Trusted registration editor/automatic handoff and broader website/service templates.


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
