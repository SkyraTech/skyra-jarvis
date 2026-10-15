# Jarvis Windows Desktop — System Architecture

## Maintained specification — current status

Updated 2026-10-15. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented Windows control slice: dedicated React Flow subsystem canvas, project permissions, proposal review, approvals, coding checkpoints/evidence, stored conversations and recent events; Tauri Rust bridge, DPAPI credentials, hidden launcher and tray lifecycle. Release executable builds; native acceptance is recorded in the owning development tracker. Model chat, structured draft plans, setup-readiness and the flexible 3D/tabbed/multi-window workspace are implemented. Reviewed specification-to-scaffold creation and receipt recovery are implemented within a trusted host root. Installer, signed updates, mobile pairing, registry/configuration editing and automatic workflow scheduling remain pending. The legacy UI stays separate.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](../../../docs/ARCHITECTURE.md)
- [Current functionality and implementation boundaries](../../../docs/FUNCTIONALITY.md)
- [Current milestone and verification summary](../../../docs/DEVELOPMENT.md)

Repository boundary: `skyra-jarvis/apps/desktop` inside `skyra-jarvis`. Older standalone folder names in the proposed structure below identify the component only; use the current monorepo location.

Prepared: 2026-10-14. Requirement/design baseline. Use the maintained current-status section above to distinguish implemented work from planned work.

## Responsibility and stack

The dedicated Windows control centre for Jarvis: a workflow canvas of available subsystems, live task graphs, conversation panels, approvals, memory and incidents. Uses its own UI design, not Skyra Platform components.

Tauri 2 release line with a minimal Rust shell; React/TypeScript/Vite; React Flow; TanStack Query for server state; Zustand for transient canvas state. Exact versions must pass a packaged Windows compatibility spike.

This is a target architecture, not a claim that these dependencies are already installed. Preserve useful adapters and migrate behind tests; a language rewrite is not a prerequisite to proving the first complete workflow. Select exact supported patch versions at implementation time, record them in manifests/lockfiles and verify their official support policies.

## High-level flow

Authorized caller → transport validation → policy check → application operation → owned persistence/job lease → provider or isolated worker → result/artifact → audit event.

Long-running operations return job IDs and support status, cancellation and replay. Provider webhooks are authenticated and deduplicated before changing domain state. MCP maps to the same operations; it does not replace the API, scheduler or policy engine.

## Data ownership

The Jarvis core owns durable conversations, runs, approvals and memory. Desktop owns only local presentation preferences and transient UI state; reconnect by replaying core events.

Domain concepts: WindowLayout, CanvasLayout, ViewPreference, DevicePairingReference, NotificationPreference.

Local Jarvis uses SQLite with migrations and durable event/checkpoint records, plus file artifacts referenced by ID/checksum. JSONL is an export/log format, not the sole job state database. Hosted service state uses separately owned PostgreSQL schemas/databases as justified. A broker is introduced only with a proven delivery need; outbox/inbox and idempotency remain required. No shared writable SQLite file over a network.

## Collaborating projects

- [skyra-jarvis](../../../README.md)
- [skyra-service-contracts](../../../../skyra-service-contracts/README.md)

These are collaboration relationships, not an instruction to create circular package imports or require every service at startup. Use contracts and readiness discovery; unavailable optional capabilities remain visible but disabled.

## Proposed folder structure

```text
skyra-jarvis-desktop/
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

- Tauri packaging and Rust toolchain must be proven before UI expansion
- Windows native interactions need tests beyond browser-only Playwright
- Code signing and update distribution ownership are undecided

## Implemented desktop architecture

React/TypeScript/Vite/React Flow runs inside a Tauri Rust host. No Skyra Platform UI package is imported. Native allowlisted commands use fixed loopback endpoints and host-held DPAPI credentials; the page has no bearer token, filesystem or shell plugin. A controller-only dashboard view assembles recent scoped state. Separate worker credentials advance runs; controller credentials approve/cancel. Refer to the owning architecture for exact versions, request bounds, config, launch lifecycle and unchanged SQLite schema 6.

## Conversation and draft planning

ConversationRuntime is separate from RepairRuntime and shares the explicit Gemini/Groq provider adapters. SQLite migration 7 adds model_turns with immutable context/response snapshots and message links. Core owns authenticated reads/interruption even when providers are removed. See the owning architecture for all columns, indexes and transaction boundaries.

## Flexible 3D workspace

Workspace owns bounded tab metadata and active-tab routing; App owns each visited tab’s project/selection state. Unvisited restored tabs mount lazily and inactive tabs pause dashboard polling. Native workspace.rs validates built-in panel names and project IDs, creates local WebviewUrl::App windows, and controls only the calling window plus explicit save/restore/show-all operations. The existing Bridge/DPAPI credentials and Core API remain shared. No SQLite migration or new service is added. See the owning architecture for persistence details.


## Versioned specification workflow - 2026-10-15

Conversations supports versioned project specifications with plain-text document review and explicit checksum approval. The repair dialog offers an optional approved-specification link. Rust exposes four fixed controller actions; it adds no filesystem or execution capability. Core schema is now 8. Backend invariants and native acceptance evidence are maintained in the owning Jarvis ARCHITECTURE.md and DEVELOPMENT.md. General new-file builds and document export remain pending.


## Specification revision and delivery - 2026-10-15

Owner-authored revisions preserve immutable document history and parent provenance through Core schema 9. Reviewed approved bundles can be exported through a bounded native command into a dedicated version folder, with no path/content authority in the renderer. Repair context freshness still checks approved version identity; general building remains pending. Exact revision/export contracts, limits, native storage and verification are maintained in the owning Jarvis ARCHITECTURE.md and DEVELOPMENT.md.


## Reviewed new-file coding - 2026-10-15

Registered workspaces may contain explicit absent creation targets. Proposal context/review identifies these targets and full proposed file content. The existing controller acceptance, resource grants, protected tests and exact action policy still apply. Freshness checks reject unexpected files, and exclusive creation prevents overwrite. The current workflow requires pre-existing protected tests and a failing baseline; general greenfield building remains pending. See the owning ARCHITECTURE.md and DEVELOPMENT.md for the exact manifest/API contracts and current verification.

## Desktop scaffold workflow - 2026-10-15

ScaffoldPanel uses fixed controller bridge routes for preview/create/status. Core binds the trusted root and its interpreter, regenerates the exact reviewed plan and publishes exclusively through skyra_coding.scaffold. Receipt inspection checks path/plan/specification/project and the existing creation event. No schema/dependency change; registration remains manual. Full details are in the owning ARCHITECTURE.md.


## Integrated project-building milestone - 2026-10-15

Current schema is 12: scaffold_registrations stores immutable project/specification/name/directory bindings, reviewed plan/config hashes, selected scope, original manifest, profile/interpreter identity and timestamp. Registration is restored additively into live maps on Core operations/restart. Damaged entries are isolated for reconciliation. The protected website transport uses standard-library loopback HTTP; selected implementation files remain editable. See the owning canonical architecture for fields and authority boundaries.
