# Jarvis Windows Desktop — System Architecture

## Maintained specification — current status

Updated 2026-10-14. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Planned component. No new Tauri application, workflow canvas, installer or tray supervisor has been implemented. The legacy UI is a separate prototype.

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
