# Skyra Coding Worker — System Architecture

Repository boundary: `skyra-jarvis/workers/coding` inside `skyra-jarvis`. Older standalone folder names in the proposed structure below identify the component only; use the current monorepo location.

Prepared: 2026-10-14. Status: proposed implementation baseline. User requirements are captured here; technical choices remain subject to implementation validation.

## Responsibility and stack

Executes scoped repository tasks in isolated workspaces, returns patches and build evidence, and supports implementation, debugging and review without inheriting unrestricted host access.

Python worker with structured process/Git adapters; OS-enforced execution isolation selected through a Windows spike. Linux container workers may be added for compatible tasks. Node toolchains execute inside the task environment.

This is a target architecture, not a claim that these dependencies are already installed. Preserve useful adapters and migrate behind tests; a language rewrite is not a prerequisite to proving the first complete workflow. Select exact supported patch versions at implementation time, record them in manifests/lockfiles and verify their official support policies.

## High-level flow

Authorized caller → transport validation → policy check → application operation → owned persistence/job lease → provider or isolated worker → result/artifact → audit event.

Long-running operations return job IDs and support status, cancellation and replay. Provider webhooks are authenticated and deduplicated before changing domain state. MCP maps to the same operations; it does not replace the API, scheduler or policy engine.

## Data ownership

This project owns its domain state and migrations. Other projects use its API/events; direct reads or writes to its database are forbidden. Credentials are references to a protected store, never ordinary domain fields.

Domain concepts: Workspace, RepositoryGrant, BaseRevision, PatchArtifact, CommandExecution, ProcessLease, DeliveryManifest.

Local Jarvis uses SQLite with migrations and durable event/checkpoint records, plus file artifacts referenced by ID/checksum. JSONL is an export/log format, not the sole job state database. Hosted service state uses separately owned PostgreSQL schemas/databases as justified. A broker is introduced only with a proven delivery need; outbox/inbox and idempotency remain required. No shared writable SQLite file over a network.

## Collaborating projects

- [skyra-service-contracts](../../../../skyra-service-contracts/README.md)
- [skyra-service-foundation](../../../../skyra-service-contracts/packages/foundation/README.md)
- [skyra-github-service](../../../../skyra-github-service/README.md)
- [skyra-quality](../../../../skyra-quality/README.md)

These are collaboration relationships, not an instruction to create circular package imports or require every service at startup. Use contracts and readiness discovery; unavailable optional capabilities remain visible but disabled.

## Proposed folder structure

```text
skyra-coding-worker/
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

- Git worktrees alone do not provide process or filesystem isolation
- Windows-native and container execution support different toolchains
- Isolation technology is an implementation gate, not a command-blacklist assumption
