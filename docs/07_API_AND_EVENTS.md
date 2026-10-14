# Jarvis Orchestration Core — API and Events

Prepared: 2026-10-14. Status: proposed implementation baseline. User requirements are captured here; technical choices remain subject to implementation validation.

## Proposed surface

These are draft contracts for implementation, not a list of currently working endpoints. Publish machine-readable OpenAPI/JSON Schema before integrating consumers.

| Operation | Intended behavior |
|---|---|
| `POST /v1/projects` | Create a project boundary; return project ID |
| `POST /v1/conversations/{id}/messages` | Append idempotent message and optionally create a run |
| `POST /v1/runs` | Create a run against an explicit specification and policy version; return 202 |
| `POST /v1/approvals/{id}/decisions` | Authorize the exact pending action hash, or reject it |
| `POST /v1/runs/{id}/cancel` | Persist cancellation and request worker acknowledgement |
| `GET /v1/runs/{id}/events` | Replay ordered events from cursor and stream new events |
| `POST /v1/memories` | Store explicit teaching with scope and provenance |
| `GET /v1/capabilities` | List implemented, connected, ready and unavailable capabilities |

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
  "producer": "skyra-jarvis",
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
