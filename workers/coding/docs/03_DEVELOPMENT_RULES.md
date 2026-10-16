# Skyra Coding Worker — Development Rules

## Maintained specification — current status

Updated 2026-10-16. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented: selected-file snapshots, guarded patch/create operations, owner-enabled native Windows tests, online-model repair jobs, bounded hidden-runner progression, native desktop review and separately approved source delivery. Approved-specification scaffolds create bounded Python JSON-function projects through the desktop or owner command with protected examples. Website/full-service scaffolds, a trusted registry editor, Git branch/revision delivery and currency budgets remain pending. Native execution carries Windows account privileges; optional Docker isolation is not live-verified.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](../../../docs/ARCHITECTURE.md)
- [Current functionality and implementation boundaries](../../../docs/FUNCTIONALITY.md)
- [Current milestone and verification summary](../../../docs/DEVELOPMENT.md)

Prepared: 2026-10-14. Requirement/design baseline. Use the maintained current-status section above to distinguish implemented work from planned work.

## General principles

- Implement one acceptance-tested vertical workflow before expanding capability count.
- Keep contracts, implementation and examples consistent. Mock/simulated output is explicitly labelled and cannot pass production acceptance.
- All new agent, API, mobile and MCP integrations must use the same server-side policy checks; legacy integrations are not automatically covered.
- Configuration is validated at startup. Never silently fall back to fake success or a different privileged account.
- Keep changes scoped and reviewable; preserve user files and migrations. No project deletion or mass rewrite without an explicit decision.

## Technology and coding standards

Python worker with structured process/Git adapters; OS-enforced execution isolation selected through a Windows spike. Linux container workers may be added for compatible tasks. Node toolchains execute inside the task environment.

Use formatter/linter configurations checked into the project; strict TypeScript for new TypeScript modules and typed Python boundaries with validated inputs. Pin reproducible dependencies, commit appropriate lockfiles and document upgrades. Supported versions are selected using upstream release/support information, not copied from old scaffolds. Do not mix package managers without a migration plan.

## Structure and execution rules

Business logic belongs in domain/application modules; provider calls and storage belong in adapters. Validate inputs at every trust boundary. Return structured errors with stable codes and correlation IDs. Use bounded timeouts, cancellation propagation and retry classification. Never log tokens or place secrets in command arguments. Worker commands must use argument arrays and scoped working directories, not interpolated shell strings.

## Changes and completion

Every task links to a requirement and acceptance check. Add meaningful unit/integration/contract tests according to behavior and risk. A passing build alone is insufficient. Update [memory](06_PROJECT_MEMORY.md) with evidence, current blockers and next action. Mark complete only after the stated exit criteria pass; model claims are not test evidence.

## Review and release

Review permissions, tenant boundaries, migrations, failure/retry behavior and logs. Record exact commit, tool versions and checks in release evidence. Production release is a distinct configured permission; creating a candidate or passing tests does not authorize deployment. Approval validity is rechecked immediately before the approved side effect.


## Reviewed new-file coding - 2026-10-15

Never infer new-file authority from a model-selected path. Require a registered creation target, verify absence at generation/acceptance and use exclusive creation at execution. Preserve original source, immutable baseline and protected test hashes. Retry deduplication must recover an existing run even after its new file has been created.

## Approved-specification scaffolds - 2026-10-15

Do not accept generated shell commands or arbitrary test code in scaffolds. Render bounded owner JSON examples through host templates, bind all contents/destination/profile/interpreter bytes to the exact review, and preserve protected tests during implementation. Do not overwrite existing directories, silently enable native execution, grant permissions, stage, commit or deploy. Preserve initial documents; identify host defaults.

## Desktop scaffold workflow - 2026-10-15

Reject renderer filesystem paths, executables and files. Gate creation on exact preview and explicit consent; clear both on edited inputs/specification changes. Prevent duplicate requests and never auto-retry uncertain creation. Show receipt/audit results and keep registry/execution/model/delivery authority separate.


## Integrated project-building milestone - 2026-10-15

Deliver coherent vertical milestones, including failure/recovery, regression tests and native acceptance; do not stop or propose commits for supporting components. Never stage, commit or push. Preserve all nine initial documents and update existing canonical documents in place. Keep creation, registration, host command consent, policy grants, provider sharing and delivery independent. Bind interpreter/profile/protected inputs before model calls, execution and delivery. Do not introduce arbitrary renderer paths, shell commands or automatic uncertain retries.


## Unattended operations milestone - 2026-10-16

Record outcomes atomically with source state/events. Never derive authorization from a notice, acknowledgement or UI preference. Do not include model context, test stdout, credentials or arbitrary commands in notices. Read/acknowledge must work without execution providers. Maintain larger verified milestones and no stage/commit/push; preserve the nine initial documents. Distinguish host enablement from process health and real after-exit execution from heartbeat-only evidence.


## Scheduled background builds - 2026-10-16

Do not dispatch before the persisted due time or silently run a missed schedule. Validate current selected snapshot hashes and approved specification before the first baseline, including while awaiting its approval. Pause/resume must preserve not-before; changes require cancel/new review. A repeated identical scheduled create recovers the existing job even after its time/files change, without executing or replaying model calls. Record worker contact as communication evidence, never as a process-health attestation. No staging, commit, push or private setup changes.
