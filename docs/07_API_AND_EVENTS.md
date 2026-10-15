# Jarvis Orchestration Core — API and Events

## Maintained specification — current status

Updated 2026-10-15. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented and verified: durable core, authenticated local API, selected-file worker, owner-enabled native Windows tests, repair workflows and bounded Gemini/Groq repair proposals with versioned skill context and controller review. Native desktop control, flexible 3D/tabbed/multi-window workspace, model-backed conversation, structured draft planning and setup-readiness guidance are implemented. General autonomous building, a full configuration editor, installer/update delivery and mobile pairing remain pending.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](ARCHITECTURE.md)
- [Current functionality and implementation boundaries](FUNCTIONALITY.md)
- [Current milestone and verification summary](DEVELOPMENT.md)

Prepared: 2026-10-14. Requirement/design baseline. Use the maintained current-status section above to distinguish implemented work from planned work.

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

## Implemented repair API/events

Controller-only: GET `/v1/runtime/capabilities`; POST `/v1/projects/{project}/repair-proposals`; POST `/v1/repair-proposals/{proposal}/generate`, `/accept`, `/interrupt`. GET `/v1/repair-proposals/{proposal}` allows controller or owned/project-scoped agent. Worker access denied. Schema comes from the API source/controller OpenAPI. Creation requires resource/profile/provider/goal/files/request_id; skills optional. Events: `repair_proposal.created`, `.generating`, `.ready`, `.failed`, `.interrupted`, `.accepted`. They contain subject IDs, not source/keys. Generation persists its outcome before response; clients read status after a transport timeout and never blindly resend a new request.

## Desktop integration contracts

GET `/v1/projects/{project}/dashboard` is controller-only, owner-checked and bounded. It returns policy/resources, conversation counts, proposal metadata, run summaries, pending approval validity, permitted workspace selections, registered logical resources, capabilities, recent events and server time. It returns no tokens, leases or content/payload bodies. GET details/messages/evidence use existing owned routes. PUT project policy accepts optional `expected_version`; desktop sends the reviewed version and handles conflict. Native bridge validates action/IDs/checksums and reserves worker authority for advance. UI creates no new event types; existing core operations emit durable events.

## Conversation and draft planning

Controller-only routes: GET /v1/setup; POST /v1/conversations/{id}/model-turns with provider/mode/content/request_id; GET the same collection (100 recent metadata records); GET /v1/model-turns/{id}; POST its /generate and /interrupt actions. Create persists a user message and snapshot but makes no provider call. Generate dispatches once. Existing message pagination remains unchanged. Events: model_turn.created, .generating, .completed, .failed and .interrupted; user/assistant appends also emit message.appended.

## Flexible 3D workspace

New native commands: open_panel(view, project?) and workspace_action(action, width?, height?). open_panel accepts only Overview, Jarvis core, System map, Repair proposals, Coding runs, Approvals, Conversations, Activity and Setup. Workspace actions are minimize, maximize toggle, fullscreen toggle, resize, show_all, save and restore. No generic URL/window/shell/filesystem command is exposed. Main and host-created panel-* windows can use the existing allowlisted Core bridge; project/owner checks remain enforced by the server.


## Versioned specification workflow - 2026-10-15

Controller-only endpoints: GET/POST /v1/projects/{project}/specifications; GET /v1/specifications/{id}; POST /v1/specifications/{id}/approve. Publication body: source_turn, expected_version (0 for the first version), request_id. Approval body: expected_sha256. Lists contain at most 100 metadata records; exact detail returns documents. Repair proposal creation accepts optional specification ID. Events: specification.published and specification.approved. Publication is an offline operation with no model call.


## Specification revision and delivery - 2026-10-15

Controller POST /v1/specifications/{id}/revisions accepts documents, expected_sha256, expected_version and request_id; returns a new specification (201). POST /v1/specifications/{id}/export accepts expected_sha256 and returns approved canonical documents plus provenance, not an arbitrary-path write. Events: specification.revised and specification.export_prepared. Native command export_specification(id, expected_sha256) performs the bounded local write and returns directory/files/existing.


## Reviewed new-file coding - 2026-10-15

Existing proposal/coding-run APIs carry new-file entries as {path, expected_sha256:"absent", old:"", new:<full content>}. Worker task payload is exactly {operation:"create",path,content}, action write. Dashboard workspace metadata adds create_paths. Existing task/run events and content-addressed create evidence are used; evidence references remain real SHA-256 hashes. The string absent denotes file nonexistence, never a content hash.

## Reviewed source delivery - 2026-10-15

Controller POST /v1/coding-runs/{run}/delivery-preview accepts target and returns plan/sha256. Controller POST /v1/coding-runs/{run}/deliveries accepts target, expected_sha256 and request_id; returns task status (201). GET on the latter path lists up to 100 deliveries for the owned run. Worker POST /v1/deliveries/{task}/advance starts only queued/waiting-approval tasks under the existing task policy. Controller credentials cannot execute this route, and agent credentials cannot prepare source delivery. Existing approval-decision and task-evidence APIs apply.

Status includes id, run, target, state, manifest sha256 and evidence references. Dashboard adds delivery_targets with logical resource/workspace pairs; physical paths remain trusted host configuration. Event delivery.prepared supplements existing task/approval events. Source task payload operation deliver is controller-prepared and includes tested inputs, baseline, change set, profile checksum and target binding checksum. Fixed native bridge actions are delivery_preview, prepare_delivery, deliveries and advance_delivery; only advance_delivery selects the worker credential.
