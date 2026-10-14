# Jarvis Orchestration Core — Project Memory

Last updated: 2026-10-14.

## Current status

2026-10-14 API checkpoint: authenticated FastAPI control API implemented in `services/core/src/jarvis_core/api.py`. Controller credentials exclusively administer projects, policy, approvals, cancellation/reconciliation; agent/worker credentials are bound to explicit project IDs. Lease tokens are hidden in task reads. Added loopback-only developer launcher, request limits, sanitized errors, paginated replay, generated controller-only schema and transactional SQLite v1→v2 task-idempotency migration.

Final suite: **38 tests passed**, run with `venv/Scripts/python.exe -m unittest discover -s services/core/tests -v`. Verification used real temporary SQLite databases and in-process API requests; no live network listener, external provider or legacy-data migration. The installed Starlette test client emits an HTTPX deprecation warning; this is documented in the API guide and does not cause test failures.

Owner confirmed exposed-token revocation. The earlier foundation was manually committed by the owner as `82845a6`. This API phase remains unstaged/uncommitted by the assistant. Next phase is isolated coding-worker integration, after owner review and manual commit. Existing assistant/UI still use their original execution paths. Refer to [API guide](../services/core/API.md).

2026-10-14 implementation update: the first durable core slice is built in `services/core/src/jarvis_core`. All 19 tests passed using `python -m unittest discover -s services/core/tests -v` with approved normal temporary-file access. Coverage includes state/event rollback, concurrent claims, permission revocation, approval expiry/replay, restart persistence and explicit reconciliation. No model or provider calls were made. This supersedes the older documentation-only status below for this slice only.

Local remote URLs were stripped of embedded credentials in six in-scope repositories. Jarvis's `config/api_keys.json` and `memory.json` were removed from the Git index and preserved on disk. Those removals are staged; no commit/push/history rewrite occurred. Credential rotation and historical secret review remain outstanding.

Next: authenticated local control API, followed by isolated tool execution and end-to-end policy checks. Employee roles, curated teaching memory, artifacts verification, model routing integration and desktop wiring remain open. The legacy assistant still uses its original execution path.

See [implementation record](14_CORE_BASELINE_IMPLEMENTATION.md) and [core integration contract](../services/core/README.md).

2026-10-14 repository organization: documentation-only desktop, runtime and coding worker folders moved into this repository. Relative links updated. Existing Python source, launchers, Git HEAD/index and runtime state were preserved. No new implementation, deployment or runtime test is claimed. See [repository layout](13_REPOSITORY_LAYOUT.md).

Earlier documentation baseline: implementation was unverified at that point. The update above records the subsequent tested slice; the overall target is not production-ready.

Existing Python assistant at bd6be5f has voice, Telegram, model failover, memory and direct tool execution. It lacks the target durable task and permission architecture. Inspection found an unimported change_ui_state call, shared conversation history and simulated UI streaming. Earlier syntax checks passed; this is not runtime acceptance.

## Completed in this documentation pass

- Captured product requirements, architecture, development rules and design guidance.
- Created phased tasks, interface proposals, testing criteria and security/operations guidance.
- Recorded baseline limitations and unresolved decisions without marking planned features built.

## In progress

Current API phase is complete at its review checkpoint. No worker/model execution task is claimed complete. Wait for the owner's manual commit confirmation before starting the next phase.

## Decisions and assumptions

- Confirmed: Jarvis is Windows-first, remotely controllable, online-model-first, with persistent memory and configurable permissions.
- Confirmed: ERP, Skyra Platform and QR are excluded from this change; the article dashboard is handled separately.
- Proposed: the stack and service boundaries in the architecture document; exact versions and hosting selections require validation.
- No runtime, production, migration or security test has been executed as part of writing these documents.

## Blockers / open decisions

- Mobile OS and companion-app approach are unconfirmed
- Production-release policies and per-project budgets require configuration
- Existing memory data needs an explicit non-destructive migration/export plan

## Next action

Start Phase 1 in [project tasks](05_PROJECT_TASKS.md). Inspect current source before estimating implementation. For new documentation-only folders, initialize implementation tooling only when that phase is authorized.

## Task history format

| Date | Task ID | Owner | State | Commit / evidence | Next action |
|---|---|---|---|---|---|
| 2026-10-14 | DOC-BASELINE | Documentation pass | Prepared | This document set; no runtime verification | Review and assign Phase 1 |

Append meaningful decisions and test results, not private reasoning or secrets. This file is curated engineering memory; runtime conversations, teachings, job events and audit records belong in the designated durable stores. Preserve provenance when summarizing earlier work.
