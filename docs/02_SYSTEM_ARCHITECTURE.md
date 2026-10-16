# Jarvis Orchestration Core — System Architecture

## Maintained specification — current status

Updated 2026-10-16. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented and verified: durable core, authenticated local API, selected-file worker, owner-enabled native Windows tests, repair workflows and bounded Gemini/Groq repair proposals with versioned skill context and controller review. Native desktop control, flexible 3D/tabbed/multi-window workspace, model-backed conversation, structured draft planning and setup-readiness guidance are implemented. Reviewed function and website/HTTP templates connect desktop creation, durable registration, explicit grants, bounded repair jobs and separate source delivery. The Activity operations center adds durable outcomes, acknowledgement, saved project recovery and recorded runner contact. Build jobs support one-time scheduled starts with input/specification admission guards; final native acceptance is recorded in DEVELOPMENT.md. General autonomous building, a registry/configuration editor, installer/update delivery and mobile pairing remain pending.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](ARCHITECTURE.md)
- [Current functionality and implementation boundaries](FUNCTIONALITY.md)
- [Current milestone and verification summary](DEVELOPMENT.md)

Prepared: 2026-10-14. Requirement/design baseline. Use the maintained current-status section above to distinguish implemented work from planned work.

## Responsibility and stack

An internal, persistent coordinator that turns owner requests into versioned plans, delegated tasks, verified deliverables and reviewable incident fixes. Runs on Windows first; supports remote workers and future hosted operation through explicit migration.

Python service; FastAPI/Pydantic; SQLite with migrations and WAL for local state; filesystem artifacts; online provider SDKs via the agent runtime. Hosted PostgreSQL migration is a separately tested future change.

This is a target architecture, not a claim that these dependencies are already installed. Preserve useful adapters and migrate behind tests; a language rewrite is not a prerequisite to proving the first complete workflow. Select exact supported patch versions at implementation time, record them in manifests/lockfiles and verify their official support policies.

## High-level flow

Authorized caller → transport validation → policy check → application operation → owned persistence/job lease → provider or isolated worker → result/artifact → audit event.

Long-running operations return job IDs and support status, cancellation and replay. Provider webhooks are authenticated and deduplicated before changing domain state. MCP maps to the same operations; it does not replace the API, scheduler or policy engine.

## Data ownership

This project owns its domain state and migrations. Other projects use its API/events; direct reads or writes to its database are forbidden. Credentials are references to a protected store, never ordinary domain fields.

Domain concepts: Project, Conversation, Message, SpecificationVersion, Run, Task, Checkpoint, Approval, MemoryRevision, SkillInstallation, ActivityEvent, Schedule, ArtifactReference.

Local Jarvis uses SQLite with migrations and durable event/checkpoint records, plus file artifacts referenced by ID/checksum. JSONL is an export/log format, not the sole job state database. Hosted service state uses separately owned PostgreSQL schemas/databases as justified. A broker is introduced only with a proven delivery need; outbox/inbox and idempotency remain required. No shared writable SQLite file over a network.

## Collaborating projects

- [skyra-service-contracts](../../skyra-service-contracts/README.md)
- [skyra-service-foundation](../../skyra-service-contracts/packages/foundation/README.md)
- [skyra-agent-runtime](../packages/agent-runtime/README.md)
- [skyra-jarvis-desktop](../apps/desktop/README.md)
- [skyra-quality](../../skyra-quality/README.md)

These are collaboration relationships, not an instruction to create circular package imports or require every service at startup. Use contracts and readiness discovery; unavailable optional capabilities remain visible but disabled.

## Proposed folder structure

```text
skyra-jarvis/
README.md
src/
  domain/
  application/
  adapters/
  interfaces/
tests/
  unit/
  integration/
  acceptance/
docs/
```

Adapt existing folders incrementally; this document does not move source code. Keep provider SDK usage in adapters and business rules outside HTTP/MCP handlers.

## Failure and deployment model

Persist intent before dispatch; use bounded leases and heartbeats, reconcile uncertain external results, and never blindly retry a payment, publication, message or repository push. Workers are replaceable; ownership is explicit. Local user-session processes start hidden on Windows and shut down cleanly. Desktop must not depend on a visible terminal. Future hosted deployments need authenticated remote workers, independent health checks and tested backup/restore.

## Outstanding constraints

- Mobile OS and companion-app approach are unconfirmed
- Production-release policies and per-project budgets require configuration
- Existing memory data needs an explicit non-destructive migration/export plan

## Implemented repair integration

The new runtime lives in `packages/agent-runtime/src/jarvis_runtime`. It calls official Gemini/Groq adapters and stores proposals in the core-owned schema version 6. Controller acceptance atomically creates an existing coding run. See the consolidated architecture for exact columns, states, boundaries and configuration. LangGraph remains an optional future decision, not an installed requirement.

## Implemented desktop architecture

React/TypeScript/Vite/React Flow runs inside a Tauri Rust host. No Skyra Platform UI package is imported. Native allowlisted commands use fixed loopback endpoints and host-held DPAPI credentials; the page has no bearer token, filesystem or shell plugin. A controller-only dashboard view assembles recent scoped state. Separate worker credentials advance runs; controller credentials approve/cancel. Refer to the owning architecture for exact versions, request bounds, config, launch lifecycle and unchanged SQLite schema 6.

## Conversation and draft planning

ConversationRuntime is separate from RepairRuntime and shares the explicit Gemini/Groq provider adapters. SQLite migration 7 adds model_turns with immutable context/response snapshots and message links. Core owns authenticated reads/interruption even when providers are removed. See the owning architecture for all columns, indexes and transaction boundaries.

## Flexible 3D workspace

Workspace owns bounded tab metadata and active-tab routing; App owns each visited tab’s project/selection state. Unvisited restored tabs mount lazily and inactive tabs pause dashboard polling. Native workspace.rs validates built-in panel names and project IDs, creates local WebviewUrl::App windows, and controls only the calling window plus explicit save/restore/show-all operations. The existing Bridge/DPAPI credentials and Core API remain shared. No SQLite migration or new service is added. See the owning architecture for persistence details.


## Versioned specification workflow - 2026-10-15

SQLite migration 8 adds project_specs for owner-scoped immutable document bundles, per-project versions, source-turn provenance, idempotent publication and exact-checksum approval. Repair context optionally embeds the approved version and rechecks its approval before model dispatch, after response and at acceptance. The full schema and transaction details are maintained in ARCHITECTURE.md.


## Specification revision and delivery - 2026-10-15

SQLite migration 9 adds nullable project_specs.parent_spec referencing project_specs.id. Controller revision and export-preparation routes retain owner checks. Native export obtains canonical documents from the authenticated Core, verifies SHA-256 and writes only fixed filenames into a dedicated version folder. Full contracts and storage layout are in ARCHITECTURE.md.


## Reviewed new-file coding - 2026-10-15

Workspace manifest version 2 records explicit create_paths and absent baseline hashes while retaining version-1 reads. Runtime proposals use the existing response shape with expected_sha256="absent", old="" and full content in new. Acceptance compiles these into exact create operations. SQLite remains schema 9; no new service or database migration is introduced.


## Unattended assignments requirement - 2026-10-15

Source-delivery prerequisite: the worker now supports a separately registered source resource, controller-prepared manifest, tested-input/profile checksums and source/snapshot binding. Existing Core tasks/approvals/events hold durable intent; private filesystem journals retain backups and partial-write progress. Schema remains 9. Exact contracts and recovery boundaries are maintained in [ARCHITECTURE.md](ARCHITECTURE.md#reviewed-source-delivery-architecture---2026-10-15).

Planned: separate the desktop UI lifecycle from a durable per-user background runner. SQLite stores goals, execution state, checkpoints, approvals and evidence. A scheduler claims work with leases and heartbeats, dispatches bounded tool/model steps, verifies outcomes and continues authorized steps until complete, blocked, cancelled or budget-limited. Initially retain the user context needed for existing DPAPI credentials; do not assume a LocalSystem Windows service can decrypt user-bound secrets. Later support remote executors with explicit capabilities and pairing. This architecture is proposed, not implemented or verified.

### Model-job extension

Schema 11 adds build_jobs, build_cycles and build_attempts without rewriting prior assignments or history. A second scheduler lane uses the same hidden runner/project dispatch exclusion to execute baseline, generation, review and existing coding-run stages. RepairRuntime receives bounded task-bound diagnostics and reports a response checksum for exact review. Provider calls reserve a durable slot before dispatch; a saved ready response is reusable, while generating after restart remains uncertain. Only verified failing retests may initiate another cycle. Full configuration/state/contract details are maintained in ARCHITECTURE.md.

### Implemented first executor

SQLite migration 10 now adds assignments and assignment_attempts. services/runner/run.pyw is a hidden per-user worker calling the scoped tick API. A claim advances an accepted coding run once and records its evidence/progress. Current mode supports checkpoint pause/cancel, approval waits, step/time bounds, conservative crash accounting and explicit recovery. Background launcher ownership separates it from the UI. Paid model generation, iterative replanning/debugging and remote execution remain proposed. See the canonical architecture for exact columns, state transitions and limits.

## Specification-to-scaffold handoff - 2026-10-15

The owner host command uses the existing specification store and event log, without a migration beyond schema 11. A deterministic exact-hash review precedes exclusive Windows publication of source/snapshot/document/registration artifacts. Protected JSON examples seed existing coding jobs; no repair-baseline rule is weakened. Registration is an inert draft until separately enabled. See ARCHITECTURE.md for the layout, receipt/provenance and filesystem/audit reconciliation limits.


## Integrated project-building milestone - 2026-10-15

Current schema is 12: scaffold_registrations stores immutable project/specification/name/directory bindings, reviewed plan/config hashes, selected scope, original manifest, profile/interpreter identity and timestamp. Registration is restored additively into live maps on Core operations/restart. Damaged entries are isolated for reconciliation. The protected website transport uses standard-library loopback HTTP; selected implementation files remain editable. See the owning canonical architecture for fields and authority boundaries.


## Unattended operations milestone - 2026-10-16

Core schema 13 owns operation_notices with an immutable bounded snapshot and optional acknowledgement timestamp. Notice creation shares the source event transaction; repeated identical attention states are deduplicated. The library projects existing scaffold_registrations and live host/grant state without new filesystem authority. Fixed controller routes provide inbox/status/library and acknowledge-only writes. See canonical ARCHITECTURE.md for columns, indexes, migration and limits.


## Scheduled background builds - 2026-10-16

Schema 14 adds runner_contacts(project primary key/FK, attempt, started, finished nullable, outcome). Each authenticated scoped worker tick records a request attempt before dispatch and a guarded response/error afterward; an older response cannot overwrite a newer request. Existing build_jobs JSON gains optional schedule(start_at,start_by,inputs_sha256,specification_sha256). next_due persists the future time; deadline is planned start plus duration. Legacy immediate jobs retain their existing configuration/digest semantics. See canonical architecture for admission and replay details.
