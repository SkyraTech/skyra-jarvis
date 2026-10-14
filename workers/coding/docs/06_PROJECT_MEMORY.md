# Skyra Coding Worker — Project Memory

Last updated: 2026-10-14.

## Current status

2026-10-14 major update: owner-approved native Windows execution and durable controller-supplied repair workflows are implemented. Real test → patch → retest → review evidence passes on generated fixtures. Owner-enabled native execution carries Windows account privileges; it is not advertised as sandboxed. Docker adapter contract tests pass, but live Docker remains unverified/unavailable. Source snapshots/Git indexes remain untouched by execution. Verification: 71 total tests passed, one symlink test skipped; see [execution guide](../EXECUTION_AND_WORKFLOWS.md).

2026-10-14 file-worker foundation: implemented in `src/skyra_coding` with a developer snapshot CLI and optional trusted registry in the core launcher. Read/search/hash-checked patch/diff/static-syntax verification run through authenticated task leases and exact resource registration. Source repositories are not modified by worker operations; no staging/commit/push/deploy operation exists.

Verification: 38 core/API tests passed; worker suite ran 18 tests, with 17 passed and one symlink test skipped because the Windows account could not create links. Tests use temporary snapshots, SQLite, artifacts and in-process API calls; they do not execute untrusted source. An end-to-end fixture proves approval → edit → static check → evidence retrieval.

Process-isolation gate remains open: Docker is unavailable and arbitrary execution fails closed. Python/JSON parsing is static syntax checking, not running unit tests. Branch/revision snapshots, new files, process supervision and model-driven planning remain pending. See [implementation and limitations](../IMPLEMENTATION.md). Pause for owner's manual review/commit before the next phase.

Documentation baseline prepared; implementation of this target remains unverified. Documentation does not establish production readiness.

New documentation-only project. Replaces unsafe local shell/Git responsibilities currently mixed into Jarvis and the GitHub service.

## Completed in this documentation pass

- Captured product requirements, architecture, development rules and design guidance.
- Created phased tasks, interface proposals, testing criteria and security/operations guidance.
- Recorded baseline limitations and unresolved decisions without marking planned features built.

## In progress

No implementation task is claimed in progress by this documentation pass. Next assigned engineer should select a Phase 1 task and record owner, branch and evidence here.

## Decisions and assumptions

- Confirmed: Jarvis is Windows-first, remotely controllable, online-model-first, with persistent memory and configurable permissions.
- Confirmed: ERP, Skyra Platform and QR are excluded from this change; the article dashboard is handled separately.
- Proposed: the stack and service boundaries in the architecture document; exact versions and hosting selections require validation.
- No runtime, production, migration or security test has been executed as part of writing these documents.

## Blockers / open decisions

- Git worktrees alone do not provide process or filesystem isolation
- Windows-native and container execution support different toolchains
- Isolation technology is an implementation gate, not a command-blacklist assumption

## Next action

Start Phase 1 in [project tasks](05_PROJECT_TASKS.md). Inspect current source before estimating implementation. For new documentation-only folders, initialize implementation tooling only when that phase is authorized.

## Task history format

| Date | Task ID | Owner | State | Commit / evidence | Next action |
|---|---|---|---|---|---|
| 2026-10-14 | DOC-BASELINE | Documentation pass | Prepared | This document set; no runtime verification | Review and assign Phase 1 |

Append meaningful decisions and test results, not private reasoning or secrets. This file is curated engineering memory; runtime conversations, teachings, job events and audit records belong in the designated durable stores. Preserve provenance when summarizing earlier work.
