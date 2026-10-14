# Jarvis Orchestration Core — Project Memory

## Maintained specification — current status

Updated 2026-10-14. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented and verified: durable core, authenticated local API, selected-file worker, owner-enabled native Windows test execution and controller-supplied repair workflows. New desktop and model-generated repairs are not yet implemented.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](ARCHITECTURE.md)
- [Current functionality and implementation boundaries](FUNCTIONALITY.md)
- [Current milestone and verification summary](DEVELOPMENT.md)

## Current verification

Latest executable verification: 38 core/API tests and 33 worker/execution/workflow tests passed; one symlink test skipped because Windows could not create it. The real generated repair demo reproduced a failing test, applied the controller-supplied patch, passed the protected retest and produced a diff without changing source. Docker has contract tests only; no live isolation certification. Documentation restoration does not rerun or expand runtime acceptance.

## Completed work

The durable core/API, file worker and trusted native repair workflow milestones are implemented. Controller plans and native account access remain explicit.

## Pending work and next milestone

- Mobile OS and companion-app approach are unconfirmed
- Production-release policies and per-project budgets require configuration
- Existing memory data needs an explicit non-destructive migration/export plan

Next: online-model planning and patch generation, structured skills/context and the new Windows interface. Custom/employee grants, curated teaching memory, mobile pairing and hosted operation remain pending.

## Maintenance rules

Update this memory for current status, decisions, blockers and next work. Update the other initial documents when their requirements/design/contracts change; keep the detailed implemented database architecture reference aligned with code. Do not generate a new report per task. Git retains historical revisions. The owner stages/commits/pushes manually; the assistant reports a substantial verified milestone and waits for confirmation before proceeding.
