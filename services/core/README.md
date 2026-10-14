# Jarvis durable core

2026-10-14 update: the [authenticated local API](API.md) now wraps this core with controller/agent/worker separation and delegated project scopes. Schema version 2 adds idempotent task requests through a transactional migration from version 1. The legacy assistant and coding executor remain unconnected.

File-worker update: an optional [selected-file adapter](../../workers/coding/IMPLEMENTATION.md) now performs registered read/search/patch/diff/static checks through guarded task leases and evidence reports. Arbitrary process execution and the legacy assistant remain unconnected.

Implemented 2026-10-14 as a Python standard-library module. No model credentials or external services are needed to test it. It is not yet wired into the legacy assistant, desktop, Telegram or tool executor.

## Implemented

- SQLite schema version 1, foreign keys, WAL, full synchronization and transactional state/events.
- Owner-scoped projects and separate conversations; idempotent message insertion.
- Immutable task intents with action/resource/payload digests.
- Read-only, ask and full-access modes constrained to explicit resource IDs.
- Pending/approved/rejected/consumed approvals bound to exact task and policy version, with expiry.
- Exclusive worker claims, lease heartbeat, evidence references and cancellation state.
- Restart recovery of expired leases into an uncertain state requiring explicit reconciliation.
- Cursor-based activity replay; event bodies do not contain conversation content or credentials.

## Tests

From the Jarvis repository root:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s services/core/tests -v
```

Tests use fresh temporary SQLite databases, not existing Jarvis memory. No API calls, browser launches or model requests occur. The default temporary directory needs normal SQLite read/write permission.

## Host integration contract

The module is under `src/jarvis_core`; the development test suite adds that source directory explicitly. Packaging/installation and the authenticated transport are follow-up work.

`Core(database_path)` opens a caller-selected local database. Use a private per-user application-data directory outside a synced project folder for real operation. `close()` releases the connection. Do not share a Core instance across threads; separate connections coordinate claims through SQLite transactions.

The store itself trusts host-supplied actor IDs. The new local API authenticates these from its credential registry and reserves `set_policy`, `decide` and `reconcile` for the controller. One owner per project is supported; employee roles and custom resource/action grants remain unimplemented.

Resources are exact logical IDs such as `workspace:demo`, not filesystem sandbox rules. Future execution adapters must map IDs to verified directories/accounts, validate every tool input and enforce operating-system isolation. A returned lease is not an OS security boundary. Recheck the active policy before each side effect; already-started external operations cannot be undone by a database update.

Task intents cannot be changed through the public API. A revised action should be a new task and new approval. `start` claims work or returns an approval request; it does not execute commands. `complete` records evidence references but does not verify their authenticity. Quality tooling must independently produce and verify those artifacts before production readiness can be claimed.

## Recovery rules

Opening another connection never automatically steals work. `recover_expired` touches only expired running/cancelling leases. Interrupted tasks cannot restart until a trusted host records an externally verified reconciliation outcome. Cancellation with uncertain effects cannot be converted into automatic retry. This establishes durable intent and ownership; it does not promise exactly-once external side effects.

## Remaining work

User/employee identity and role management, credential provisioning/storage/rotation, selected/custom permission grants, durable teaching memory, artifact validation, specification versions, job/tool dispatch, actual cancellation acknowledgements, process isolation, model integration, desktop connection and migration from legacy data.
