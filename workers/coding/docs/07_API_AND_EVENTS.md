# Skyra Coding Worker — API and Events

## Maintained specification — current status

Updated 2026-10-15. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented: selected-file snapshots, guarded patch/create operations, owner-enabled native Windows tests, online-model repair jobs, bounded hidden-runner progression, native desktop review and separately approved source delivery. Approved-specification scaffolds create bounded Python JSON-function projects through the desktop or owner command with protected examples. Website/full-service scaffolds, a trusted registry editor, Git branch/revision delivery and currency budgets remain pending. Native execution carries Windows account privileges; optional Docker isolation is not live-verified.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](../../../docs/ARCHITECTURE.md)
- [Current functionality and implementation boundaries](../../../docs/FUNCTIONALITY.md)
- [Current milestone and verification summary](../../../docs/DEVELOPMENT.md)

Prepared: 2026-10-14. Requirement/design baseline. Use the maintained current-status section above to distinguish implemented work from planned work.

## Proposed surface

These are draft contracts for implementation, not a list of currently working endpoints. Publish machine-readable OpenAPI/JSON Schema before integrating consumers.

| Operation | Intended behavior |
|---|---|
| `POST /v1/workspaces` | Create an isolated workspace from an authorized repository/ref |
| `POST /v1/workspaces/{id}/commands` | Execute a policy-checked command with limits; return job ID |
| `POST /v1/workspaces/{id}/patches` | Apply validated changes within the workspace |
| `GET /v1/workspaces/{id}/diff` | Return diff artifact and base/head revisions |
| `POST /v1/workspaces/{id}/deliveries` | Prepare selected changes for GitHub adapter delivery |

## Identity and validation

Carry request ID, authenticated actor, organization/project scope, action, resource and policy version. The server derives trusted identity from verified credentials; caller-supplied tenant IDs alone grant nothing. Validate schema and resource access before execution. Provider account selection must be explicit. Correlate delegated tasks with parent run and originating actor.

## Jobs, errors and retries

Long work returns `202` with `job_id` and a status resource. State transitions: queued → running → succeeded/failed/cancelled; approval waiting pauses execution and resume revalidates policy. Lease loss or crash triggers reconciliation before another owner dispatches external effects. Store retry attempt, deadline and cancellation acknowledgement.

Errors include stable code, sanitized message, request ID, retry classification and optional details. Distinguish validation, unauthenticated, denied, approval-required, rate-limited, unavailable and outcome-unknown. Do not leak provider credentials in raw exceptions.

Side-effecting requests use an idempotency key scoped to actor/account/operation, plus a canonical payload hash. Same key with different input is a conflict. Duplicate delivery returns the earlier result or current state. Retention of deduplication records must cover the supported retry window. Exactly-once external delivery must not be promised without provider support and reconciliation.

## Event envelope

```json
{
  "event_id": "unique-id",
  "event_type": "job.state_changed",
  "schema_version": "1.0",
  "occurred_at": "2026-10-14T00:00:00Z",
  "producer": "skyra-coding-worker",
  "organization_id": "scope-id",
  "project_id": "project-id",
  "correlation_id": "run-id",
  "causation_id": "request-or-event-id",
  "aggregate_id": "job-id",
  "sequence": 1,
  "payload": {"state": "queued"}
}
```

Example only: replace IDs with real values. Ordering is per aggregate, not global; consumers deduplicate event IDs and handle gaps. Publish owned state transitions with an outbox when crossing process boundaries. Store artifact references/checksums rather than large binary content in events.

## Compatibility and MCP

Additive optional fields may be minor changes; removals, changed meaning and new required inputs need a major version or explicit migration. Contract fixtures cover TypeScript and Python consumers. MCP tools expose only supported operations and preserve identity, scopes, idempotency and approval rules. Tool discovery is not authorization. Pin and review external MCP servers and their tool changes.

## Model proposal integration

The controller can now accept a validated Gemini/Groq proposal into this worker's existing repair workflow. The runtime selects context/skills and validates patches; this worker retains protected-test, policy/approval, native-execution and evidence gates. Acceptance does not execute a task. General building and autonomous scheduling remain pending. See the owning Jarvis architecture/development records for schema 6, API and verified fixture evidence.

## Native run consumer

The Windows desktop reads checkpoints and task-bound evidence, advances one step using a separate project-scoped worker credential, and sends cancellation via controller authority independently of a pending advance request. Owner policy changes include reviewed-version checks. Worker authorization, protected tests and uncertainty/reconciliation rules are unchanged.


## Reviewed new-file coding - 2026-10-15

Existing proposal/coding-run APIs carry new-file entries as {path, expected_sha256:"absent", old:"", new:<full content>}. Worker task payload is exactly {operation:"create",path,content}, action write. Dashboard workspace metadata adds create_paths. Existing task/run events and content-addressed create evidence are used; evidence references remain real SHA-256 hashes. The string absent denotes file nonexistence, never a content hash.

## Approved-specification scaffolds - 2026-10-15

Owner host command workers/coding/scaffold.py supports --review and checksum-bound --apply. Request fields: specification, expected_sha256, contract, parent, name, python. Controller-only fixed-root preview/create/status routes supplement the command; arbitrary renderer filesystem access is not introduced. scaffold.created records an initial creation receipt through existing project events, not a successful build/deployment. Registration drafts require separate trusted host configuration.

## Desktop scaffold workflow - 2026-10-15

Native actions preview_scaffold/create_scaffold/scaffold_status map to controller POST /v1/specifications/{spec}/scaffolds/preview|create|status. Preview/create accept slug, contract and specification hash; create also needs exact plan hash. Status accepts slug only. Root/interpreter/files are host-owned. Setup exposes scaffold availability; schema 11 and scaffold.created stay unchanged.


## Integrated project-building milestone - 2026-10-15

Controller-only scaffold registration-preview/register/registration routes accept fixed name, expected plan hash, expected registration hash and explicit native consent as appropriate; extra paths/commands are rejected. The Rust bridge exposes fixed matching actions. Preview/create accepts only the two enumerated host template IDs. Registration writes scaffold.registered; resource grants remain the existing expected-version policy API, jobs remain existing bounded APIs and delivery retains its independent exact-action authority. Agent/worker credentials cannot register scaffolds.
