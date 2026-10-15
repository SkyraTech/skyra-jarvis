# Skyra Agent Runtime — API and Events

## Maintained specification — current status

Updated 2026-10-15. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented first repair runtime: explicit Gemini/Groq adapters, bounded selected-file context, versioned trusted skill loading, durable proposals and controller acceptance into tested coding runs. Durable chat and structured draft planning are also implemented without requiring a coding worker. General execution planning, skill discovery, teaching memory and autonomous scheduling remain pending. Legacy adapters remain separate.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](../../../docs/ARCHITECTURE.md)
- [Current functionality and implementation boundaries](../../../docs/FUNCTIONALITY.md)
- [Current milestone and verification summary](../../../docs/DEVELOPMENT.md)

Prepared: 2026-10-14. Requirement/design baseline. Use the maintained current-status section above to distinguish implemented work from planned work.

## Proposed surface

These are draft contracts for implementation, not a list of currently working endpoints. Publish machine-readable OpenAPI/JSON Schema before integrating consumers.

| Operation | Intended behavior |
|---|---|
| `POST /v1/executions` | Accept a signed/scoped task envelope and return execution ID |
| `GET /v1/executions/{id}` | Return execution status and checkpoint version |
| `POST /v1/executions/{id}/resume` | Resume a checkpoint using validated inputs |
| `POST /v1/executions/{id}/cancel` | Request cooperative cancellation |
| `GET /v1/skills` | List validated skill metadata and compatibility |

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
  "producer": "skyra-agent-runtime",
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

## Implemented repair API/events

Controller-only: GET `/v1/runtime/capabilities`; POST `/v1/projects/{project}/repair-proposals`; POST `/v1/repair-proposals/{proposal}/generate`, `/accept`, `/interrupt`. GET `/v1/repair-proposals/{proposal}` allows controller or owned/project-scoped agent. Worker access denied. Schema comes from the API source/controller OpenAPI. Creation requires resource/profile/provider/goal/files/request_id; skills optional. Events: `repair_proposal.created`, `.generating`, `.ready`, `.failed`, `.interrupted`, `.accepted`. They contain subject IDs, not source/keys. Generation persists its outcome before response; clients read status after a transport timeout and never blindly resend a new request.

## Native review consumer

The Windows desktop now consumes proposal detail/generate/accept/interrupt through an allowlisted Rust bridge. Generation is explicit; interruption can be sent independently while the generation call is pending. No controller token or provider key reaches the renderer. The runtime remains the source of proposal state and suppresses late interrupted output; no model/tool authority is added by the UI.

## Conversation and draft planning

Controller-only routes: GET /v1/setup; POST /v1/conversations/{id}/model-turns with provider/mode/content/request_id; GET the same collection (100 recent metadata records); GET /v1/model-turns/{id}; POST its /generate and /interrupt actions. Create persists a user message and snapshot but makes no provider call. Generate dispatches once. Existing message pagination remains unchanged. Events: model_turn.created, .generating, .completed, .failed and .interrupted; user/assistant appends also emit message.appended.
