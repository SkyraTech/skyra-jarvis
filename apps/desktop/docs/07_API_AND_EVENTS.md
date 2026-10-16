# Jarvis Windows Desktop — API and Events

## Maintained specification — current status

Updated 2026-10-16. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented Windows control slice: dedicated React Flow subsystem canvas, project permissions, proposal review, approvals, coding checkpoints/evidence, stored conversations and recent events; Tauri Rust bridge, DPAPI credentials, hidden launcher and tray lifecycle. Release executable builds; native acceptance is recorded in the owning development tracker. Model chat, structured draft plans, setup-readiness and the flexible 3D/tabbed/multi-window workspace are implemented. Reviewed specification-to-scaffold creation and receipt recovery are implemented within a trusted host root. Installer, signed updates, mobile pairing, registry/configuration editing and automatic workflow scheduling remain pending. The legacy UI stays separate.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](../../../docs/ARCHITECTURE.md)
- [Current functionality and implementation boundaries](../../../docs/FUNCTIONALITY.md)
- [Current milestone and verification summary](../../../docs/DEVELOPMENT.md)

Prepared: 2026-10-14. Requirement/design baseline. Use the maintained current-status section above to distinguish implemented work from planned work.

## Proposed surface

These are draft contracts for implementation, not a list of currently working endpoints. Publish machine-readable OpenAPI/JSON Schema before integrating consumers.

| Operation | Intended behavior |
|---|---|
| `IPC runtime.start` | Start the packaged backend without a console; return health state |
| `IPC runtime.stop` | Request graceful shutdown and surface active-task consequences |
| `IPC artifact.open` | Open only an authorized artifact ID, not an arbitrary supplied path |
| `Client GET /v1/capabilities` | Render the backend registry; do not infer readiness from installed code |
| `Client GET /v1/runs/{id}/events` | Render replayable events and recover after reconnect |

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
  "producer": "skyra-jarvis-desktop",
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

## Desktop integration contracts

GET `/v1/projects/{project}/dashboard` is controller-only, owner-checked and bounded. It returns policy/resources, conversation counts, proposal metadata, run summaries, pending approval validity, permitted workspace selections, registered logical resources, capabilities, recent events and server time. It returns no tokens, leases or content/payload bodies. GET details/messages/evidence use existing owned routes. PUT project policy accepts optional `expected_version`; desktop sends the reviewed version and handles conflict. Native bridge validates action/IDs/checksums and reserves worker authority for advance. UI creates no new event types; existing core operations emit durable events.

## Conversation and draft planning

Controller-only routes: GET /v1/setup; POST /v1/conversations/{id}/model-turns with provider/mode/content/request_id; GET the same collection (100 recent metadata records); GET /v1/model-turns/{id}; POST its /generate and /interrupt actions. Create persists a user message and snapshot but makes no provider call. Generate dispatches once. Existing message pagination remains unchanged. Events: model_turn.created, .generating, .completed, .failed and .interrupted; user/assistant appends also emit message.appended.

## Flexible 3D workspace

New native commands: open_panel(view, project?) and workspace_action(action, width?, height?). open_panel accepts only Overview, Jarvis core, System map, Repair proposals, Coding runs, Approvals, Conversations, Activity and Setup. Workspace actions are minimize, maximize toggle, fullscreen toggle, resize, show_all, save and restore. No generic URL/window/shell/filesystem command is exposed. Main and host-created panel-* windows can use the existing allowlisted Core bridge; project/owner checks remain enforced by the server.


## Versioned specification workflow - 2026-10-15

Conversations supports versioned project specifications with plain-text document review and explicit checksum approval. The repair dialog offers an optional approved-specification link. Rust exposes four fixed controller actions; it adds no filesystem or execution capability. Core schema is now 8. Backend invariants and native acceptance evidence are maintained in the owning Jarvis ARCHITECTURE.md and DEVELOPMENT.md. General new-file builds and document export remain pending.


## Specification revision and delivery - 2026-10-15

Owner-authored revisions preserve immutable document history and parent provenance through Core schema 9. Reviewed approved bundles can be exported through a bounded native command into a dedicated version folder, with no path/content authority in the renderer. Repair context freshness still checks approved version identity; general building remains pending. Exact revision/export contracts, limits, native storage and verification are maintained in the owning Jarvis ARCHITECTURE.md and DEVELOPMENT.md.


## Reviewed new-file coding - 2026-10-15

Registered workspaces may contain explicit absent creation targets. Proposal context/review identifies these targets and full proposed file content. The existing controller acceptance, resource grants, protected tests and exact action policy still apply. Freshness checks reject unexpected files, and exclusive creation prevents overwrite. The current workflow requires pre-existing protected tests and a failing baseline; general greenfield building remains pending. See the owning ARCHITECTURE.md and DEVELOPMENT.md for the exact manifest/API contracts and current verification.

## Desktop scaffold workflow - 2026-10-15

Native actions preview_scaffold/create_scaffold/scaffold_status map to controller POST /v1/specifications/{spec}/scaffolds/preview|create|status. Preview/create accept slug, contract and specification hash; create also needs exact plan hash. Status accepts slug only. Root/interpreter/files are host-owned. Setup exposes scaffold availability; schema 11 and scaffold.created stay unchanged.


## Integrated project-building milestone - 2026-10-15

Controller-only scaffold registration-preview/register/registration routes accept fixed name, expected plan hash, expected registration hash and explicit native consent as appropriate; extra paths/commands are rejected. The Rust bridge exposes fixed matching actions. Preview/create accepts only the two enumerated host template IDs. Registration writes scaffold.registered; resource grants remain the existing expected-version policy API, jobs remain existing bounded APIs and delivery retains its independent exact-action authority. Agent/worker credentials cannot register scaffolds.


## Unattended operations milestone - 2026-10-16

GET /v1/projects/{project}/operations?before=<event-id> returns at most 50 newest notices, unread count, next_before cursor, bounded current work, library and host_enabled. Host enablement is not a health claim. POST /v1/operations/{notice}/acknowledge preserves the first acknowledgement timestamp and cannot control jobs/tasks. Both routes require controller credentials and owner project scope. Dashboard operation_unread is read-only. Fixed Rust actions are operations and acknowledge_operation; no new worker execution route is exposed.


## Scheduled background builds - 2026-10-16

BuildJobInput now accepts optional start_at (integer UTC Unix seconds) and start_window_seconds (60..86400, default 900). Local UI converts the reviewed local time to UTC. New schedules must start in the future within seven days; existing identical request IDs recover saved intent rather than revalidating the now-past start. Only controller/owner creates/controls jobs. Worker runner/tick records scoped contact and dispatches existing eligible work. Operations returns runner_contact; neither that read model nor a notice grants action authority. No new renderer worker-execution route is exposed.
