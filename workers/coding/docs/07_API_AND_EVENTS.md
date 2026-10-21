# Skyra Coding Worker â€” API and Events

## Maintained specification â€” current status

Updated 2026-10-16. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

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

Long work returns `202` with `job_id` and a status resource. State transitions: queued â†’ running â†’ succeeded/failed/cancelled; approval waiting pauses execution and resume revalidates policy. Lease loss or crash triggers reconciliation before another owner dispatches external effects. Store retry attempt, deadline and cancellation acknowledgement.

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


## Unattended operations milestone - 2026-10-16

GET /v1/projects/{project}/operations?before=<event-id> returns at most 50 newest notices, unread count, next_before cursor, bounded current work, library and host_enabled. Host enablement is not a health claim. POST /v1/operations/{notice}/acknowledge preserves the first acknowledgement timestamp and cannot control jobs/tasks. Both routes require controller credentials and owner project scope. Dashboard operation_unread is read-only. Fixed Rust actions are operations and acknowledge_operation; no new worker execution route is exposed.


## Scheduled background builds - 2026-10-16

BuildJobInput now accepts optional start_at (integer UTC Unix seconds) and start_window_seconds (60..86400, default 900). Local UI converts the reviewed local time to UTC. New schedules must start in the future within seven days; existing identical request IDs recover saved intent rather than revalidating the now-past start. Only controller/owner creates/controls jobs. Worker runner/tick records scoped contact and dispatches existing eligible work. Operations returns runner_contact; neither that read model nor a notice grants action authority. No new renderer worker-execution route is exposed.


## Read-only inspection operations - 2026-10-16

Existing read tasks can carry {operation: inventory} or {operation: read_lines, path, start, count}. Exact payload fields and read authority are enforced by FileWorker. Inventory lists only selected snapshot paths, including absent creation targets, and explicitly disclaims complete source-repository coverage. read_lines accepts a 1-based positive start and 1..200 count, returns bounded whole-line text plus full-file hash and continuation metadata, and rejects unsafe/unselected/absent targets. Evidence uses the existing task report mechanism. These operations neither expand grants nor execute processes.

## Generation registration after delivery

Controller-only continuation-preview, continue and continuation-status routes under /v1/deliveries/{task} bind a successful source delivery to a newly named snapshot resource. The continue request requires the exact registration digest and explicit native-profile consent. scaffold.continued records registration; source writes still use separate deliver tasks/approvals. Existing schema-12 registration rows carry additive generation lineage fields under schema 14. See root ARCHITECTURE.md for restore/reconciliation and same-project source-alias rules.

## retrieve read operation

Exact payload: {operation: retrieve, query, paths, profile}; action=read. Query is 1..16000 characters; 1..100 unique paths must be in the snapshot and contain the profile's protected paths. Returns deterministic lexical-v1 whole-file selection, hashes for all candidates, omissions, query/profile checksums and incomplete-repository scope metadata. Current candidate text is limited to 10 MB; selected file records to 20/48,000 serialized bytes. No arbitrary file access, subprocess invocation or permission expansion. Runtime verifies the succeeded read's task/evidence against current deterministic results before use.

## Canonical edits and supervised execution â€” 2026-10-19

The runtime may canonicalize host-bound-v2 provider path/old/new edits to the immutable selected input hash and homogeneous source newline style. FileWorker still receives the existing exact path/expected_sha256/old/new contract and repeats its normal freshness, protected-path, exact unique-anchor and exclusive-create checks. Legacy edits remain exact. NativeProfile permits explicitly reviewed integer timeouts through 7200 seconds; its default and four-field digest stay unchanged. Per-dispatch parent supervision does not grant extra resources or source delivery permissions. See root ARCHITECTURE.md for lease, deadline and runner boundaries.

## Existing-project entry points

ProjectAdmission.preview/materialize/receipt separate review from source-preserving snapshot creation. binding restores the immutable baseline after later reviewed edits without rebasing source. ExistingProjectRegistry.preview_existing/register_existing reuse exact approved-specification registration and the existing registration table. Private load_host_config accepts bounded logical-root/profile/runtime metadata only. Controller HTTP endpoints are documented in the root API document. No installation, automatic grant, source write or model call is part of admission.

## Existing source interfaces

ProjectAdmission.preview/materialize/receipt separate review, snapshot creation and recovery. binding restores immutable provenance after later reviewed edits without rebasing source. ExistingProjectRegistry.preview_existing/register_existing use approved-specification registration with exact checksums and fixed host profiles. load_host_config accepts private bounded logical-root/profile/runtime metadata. Root API documentation lists controller routes. No grants, provider calls, source writes or installations occur during admission.

## Inspection tool port

InspectionTools.preview binds input hashes/profile and validates a batch; prepare creates one durable read task; step performs at most that task; results returns verified evidence while current grants and inputs match. FileWorker inspect is a read operation with exact requests and expected_inputs. Workspace.inspect captures selected records once and reuses existing inventory/search/line-read formatting. Ten focused tests cover authentication, read-only behavior, one-view consistency, restart, cancellation, stale results, strict types and raw-worker rejection of mutations. It is not the model-driven session loop.
