# Skyra Coding Worker — Project Memory

## Maintained specification — current status

Updated 2026-10-14. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented: selected-file snapshots, guarded file operations, explicitly owner-enabled native Windows test execution and durable controller-supplied repair workflows. Online-model patch generation, branch/revision delivery and the new desktop are pending. Native execution carries Windows account privileges; Docker isolation is optional and not live-verified.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](../../../docs/ARCHITECTURE.md)
- [Current functionality and implementation boundaries](../../../docs/FUNCTIONALITY.md)
- [Current milestone and verification summary](../../../docs/DEVELOPMENT.md)

## Current verification

Latest executable verification: 38 core/API tests and 33 worker/execution/workflow tests passed; one symlink test skipped because Windows could not create it. The real generated repair demo reproduced a failing test, applied the controller-supplied patch, passed the protected retest and produced a diff without changing source. Docker has contract tests only; no live isolation certification. Documentation restoration does not rerun or expand runtime acceptance.

## Completed work

The durable core/API, file worker and trusted native repair workflow milestones are implemented. Controller plans and native account access remain explicit.

## Pending work and next milestone

- Git worktrees alone do not provide process or filesystem isolation
- Windows-native and container execution support different toolchains
- Isolation technology is an implementation gate, not a command-blacklist assumption

Next: online-model planning and patch generation, structured skills/context and the new Windows interface. Custom/employee grants, curated teaching memory, mobile pairing and hosted operation remain pending.

## Maintenance rules

Update this memory for current status, decisions, blockers and next work. Update the other initial documents when their requirements/design/contracts change; keep the detailed implemented database architecture reference aligned with code. Do not generate a new report per task. Git retains historical revisions. The owner stages/commits/pushes manually; the assistant reports a substantial verified milestone and waits for confirmation before proceeding.
