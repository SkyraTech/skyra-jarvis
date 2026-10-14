# Jarvis Windows Desktop — Project Memory

Last updated: 2026-10-14.

## Current status

Documentation baseline prepared; implementation of this target remains unverified. Documentation does not establish production readiness.

New documentation-only project. No application shell, installer or UI implementation exists here yet.

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

- Tauri packaging and Rust toolchain must be proven before UI expansion
- Windows native interactions need tests beyond browser-only Playwright
- Code signing and update distribution ownership are undecided

## Next action

Start Phase 1 in [project tasks](05_PROJECT_TASKS.md). Inspect current source before estimating implementation. For new documentation-only folders, initialize implementation tooling only when that phase is authorized.

## Task history format

| Date | Task ID | Owner | State | Commit / evidence | Next action |
|---|---|---|---|---|---|
| 2026-10-14 | DOC-BASELINE | Documentation pass | Prepared | This document set; no runtime verification | Review and assign Phase 1 |

Append meaningful decisions and test results, not private reasoning or secrets. This file is curated engineering memory; runtime conversations, teachings, job events and audit records belong in the designated durable stores. Preserve provenance when summarizing earlier work.
