# Skyra Coding Worker — Product Requirements

## Maintained specification — current status

Updated 2026-10-15. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented: selected-file snapshots, guarded patch/create operations, owner-enabled native Windows tests, online-model repair jobs, bounded hidden-runner progression, native desktop review and separately approved source delivery. An owner-operated approved-specification scaffold now creates a bounded Python JSON-function project with protected examples. Website/full-service scaffolds, a scaffold dashboard, Git branch/revision delivery and currency budgets remain pending. Native execution carries Windows account privileges; optional Docker isolation is not live-verified.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](../../../docs/ARCHITECTURE.md)
- [Current functionality and implementation boundaries](../../../docs/FUNCTIONALITY.md)
- [Current milestone and verification summary](../../../docs/DEVELOPMENT.md)

Prepared: 2026-10-14. Requirement/design baseline. Use the maintained current-status section above to distinguish implemented work from planned work.

## Product overview

Executes scoped repository tasks in isolated workspaces, returns patches and build evidence, and supports implementation, debugging and review without inheriting unrestricted host access.

## Problem and current baseline

Initial baseline: documentation-only project at the time of specification; current implementation status is stated above. Replaces unsafe local shell/Git responsibilities currently mixed into Jarvis and the GitHub service.

Existing prototypes do not establish production readiness. The objective is a reusable, testable boundary with explicit ownership and verifiable outcomes.

## Target users and goals

Primary users: Skyra owner and authorized employees; consuming applications and delegated agents act under those users' scoped identities. Commercial customers use separately branded products rather than inheriting internal Jarvis privileges.

Success means the capabilities below pass recorded acceptance checks, survive expected failures and expose enough evidence for a human to review the result.

## Core requirements / MVP

- **FR-01:** Repository registration and isolated workspaces per run
- **FR-02:** Read/search/edit/patch capabilities restricted to granted workspaces
- **FR-03:** Explicit branch/base revision and selected-file change delivery
- **FR-04:** Process supervision, timeouts, cancellation and process-tree cleanup
- **FR-05:** Build/test execution with captured outputs and resource metrics
- **FR-06:** Structured diffs, test artifacts and reproducible environment manifests
- **FR-07:** Separate release/deployment actions governed by policy

## Boundaries

This project delivers its declared capabilities only. No automatic production release, account creation, purchase or broader permission is implied by an AI plan. Article-dashboard implementation, ERP, Skyra Platform and QR changes are outside this documentation initiative. Future local models and hosted Jarvis must preserve the same authorization contracts.

## User journey

An authorized caller selects a capability and resource scope, submits validated input, receives either a result or a durable job reference, follows progress and retrieves evidence. Policy may require an exact-action approval before execution. Failures present recovery guidance without claiming success.

## Acceptance and unresolved decisions

See [testing](08_TESTING_AND_ACCEPTANCE.md) for release evidence and [tasks](05_PROJECT_TASKS.md) for implementation sequence.

- Git worktrees alone do not provide process or filesystem isolation
- Windows-native and container execution support different toolchains
- Isolation technology is an implementation gate, not a command-blacklist assumption


## Reviewed new-file coding - 2026-10-15

Implemented test-driven new-file additions inside registered selected-file workspaces. The owner must explicitly allow absent target paths, review generated content and accept the proposal. Current permission policy governs each write/test action. This is a bounded addition/repair workflow with pre-existing protected tests; unrestricted project scaffolding and source-folder delivery remain pending.

## Approved-specification scaffolds - 2026-10-15

Require exactly reviewed approved-specification scaffolds with owner-defined JSON examples, preserved initial documents, protected tests and a failing stub. Existing model jobs implement the stub; source delivery remains separate. The first function template is implemented through a host maintenance command; website/full-service templates and a native scaffold wizard remain pending.
