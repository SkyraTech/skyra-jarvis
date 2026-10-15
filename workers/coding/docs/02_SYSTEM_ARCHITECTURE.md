# Skyra Coding Worker — System Architecture

## Maintained specification — current status

Updated 2026-10-15. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented: selected-file snapshots, guarded patch/create operations, owner-enabled native Windows tests, online-model repair jobs, bounded hidden-runner progression, native desktop review and separately approved source delivery. Approved-specification scaffolds create bounded Python JSON-function projects through the desktop or owner command with protected examples. Website/full-service scaffolds, a trusted registry editor, Git branch/revision delivery and currency budgets remain pending. Native execution carries Windows account privileges; optional Docker isolation is not live-verified.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](../../../docs/ARCHITECTURE.md)
- [Current functionality and implementation boundaries](../../../docs/FUNCTIONALITY.md)
- [Current milestone and verification summary](../../../docs/DEVELOPMENT.md)

Repository boundary: `skyra-jarvis/workers/coding` inside `skyra-jarvis`. Older standalone folder names in the proposed structure below identify the component only; use the current monorepo location.

Prepared: 2026-10-14. Requirement/design baseline. Use the maintained current-status section above to distinguish implemented work from planned work.

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

## Model proposal integration

The controller can now accept a validated Gemini/Groq proposal into this worker's existing repair workflow. The runtime selects context/skills and validates patches; this worker retains protected-test, policy/approval, native-execution and evidence gates. Acceptance does not execute a task. General building and autonomous scheduling remain pending. See the owning Jarvis architecture/development records for schema 6, API and verified fixture evidence.


## Reviewed new-file coding - 2026-10-15

Workspace manifest version 2 records explicit create_paths and absent baseline hashes while retaining version-1 reads. Runtime proposals use the existing response shape with expected_sha256="absent", old="" and full content in new. Acceptance compiles these into exact create operations. SQLite remains schema 9; no new service or database migration is introduced.

## Approved-specification scaffolds - 2026-10-15

skyra_coding.scaffold provides deterministic review and exclusive Windows publication. Source contains all nine initial documents, identified approved/default provenance, app.py and protected contract/tests. Existing Workspace snapshots and fixed native profiles feed Build jobs. An inert registration draft requires owner enablement. SQLite remains schema 11; scaffold.created uses the existing event log. See the owning ARCHITECTURE.md for receipt, path guards and post-publication audit-failure reconciliation.

## Desktop scaffold workflow - 2026-10-15

ScaffoldPanel uses fixed controller bridge routes for preview/create/status. Core binds the trusted root and its interpreter, regenerates the exact reviewed plan and publishes exclusively through skyra_coding.scaffold. Receipt inspection checks path/plan/specification/project and the existing creation event. No schema/dependency change; registration remains manual. Full details are in the owning ARCHITECTURE.md.


## Integrated project-building milestone - 2026-10-15

Current schema is 12: scaffold_registrations stores immutable project/specification/name/directory bindings, reviewed plan/config hashes, selected scope, original manifest, profile/interpreter identity and timestamp. Registration is restored additively into live maps on Core operations/restart. Damaged entries are isolated for reconciliation. The protected website transport uses standard-library loopback HTTP; selected implementation files remain editable. See the owning canonical architecture for fields and authority boundaries.
