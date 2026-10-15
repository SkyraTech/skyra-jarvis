# Jarvis Orchestration Core — Development Rules

## Maintained specification — current status

Updated 2026-10-16. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented and verified: durable core, authenticated local API, selected-file worker, owner-enabled native Windows tests, repair workflows and bounded Gemini/Groq repair proposals with versioned skill context and controller review. Native desktop control, flexible 3D/tabbed/multi-window workspace, model-backed conversation, structured draft planning and setup-readiness guidance are implemented. Reviewed function and website/HTTP templates connect desktop creation, durable registration, explicit grants, bounded repair jobs and separate source delivery. The Activity operations center adds durable outcomes, acknowledgement and saved project recovery; final native acceptance is recorded in DEVELOPMENT.md. General autonomous building, a registry/configuration editor, installer/update delivery and mobile pairing remain pending.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](ARCHITECTURE.md)
- [Current functionality and implementation boundaries](FUNCTIONALITY.md)
- [Current milestone and verification summary](DEVELOPMENT.md)

Prepared: 2026-10-14. Requirement/design baseline. Use the maintained current-status section above to distinguish implemented work from planned work.

## General principles

- Implement one acceptance-tested vertical workflow before expanding capability count.
- Keep contracts, implementation and examples consistent. Mock/simulated output is explicitly labelled and cannot pass production acceptance.
- All new agent, API, mobile and MCP integrations must use the same server-side policy checks; legacy integrations are not automatically covered.
- Configuration is validated at startup. Never silently fall back to fake success or a different privileged account.
- Keep changes scoped and reviewable; preserve user files and migrations. No project deletion or mass rewrite without an explicit decision.

## Technology and coding standards

Python service; FastAPI/Pydantic; SQLite with migrations and WAL for local state; filesystem artifacts; online provider SDKs via the agent runtime. Hosted PostgreSQL migration is a separately tested future change.

Use formatter/linter configurations checked into the project; strict TypeScript for new TypeScript modules and typed Python boundaries with validated inputs. Pin reproducible dependencies, commit appropriate lockfiles and document upgrades. Supported versions are selected using upstream release/support information, not copied from old scaffolds. Do not mix package managers without a migration plan.

## Structure and execution rules

Business logic belongs in domain/application modules; provider calls and storage belong in adapters. Validate inputs at every trust boundary. Return structured errors with stable codes and correlation IDs. Use bounded timeouts, cancellation propagation and retry classification. Never log tokens or place secrets in command arguments. Worker commands must use argument arrays and scoped working directories, not interpolated shell strings.

## Changes and completion

Every task links to a requirement and acceptance check. Add meaningful unit/integration/contract tests according to behavior and risk. A passing build alone is insufficient. Update [memory](06_PROJECT_MEMORY.md) with evidence, current blockers and next action. Mark complete only after the stated exit criteria pass; model claims are not test evidence.

## Review and release

Review permissions, tenant boundaries, migrations, failure/retry behavior and logs. Record exact commit, tool versions and checks in release evidence. Production release is a distinct configured permission; creating a candidate or passing tests does not authorize deployment. Approval validity is rechecked immediately before the approved side effect.

## Repair runtime development rules

Keep provider logic outside permission/execution decisions. Require explicit selected context and trusted skill versions. Validate model JSON and exact patches locally. Do not retry uncertain billable generations or silently rotate keys/providers. Test malformed output, stale context, approvals, restart, concurrency and migration before claiming runtime acceptance. SDK contract mocks and real online fixture results must be labelled separately.

## Desktop implementation rules

Keep authority in core/native adapters, never browser state. No direct renderer fetch to the core, localStorage credentials, generic URL/shell bridge or unlabelled fake success. Lock dependencies and run TypeScript/build, formatter, Rust checks and appropriate UI/native acceptance. Preview fixtures cannot substitute for native/core evidence. Preserve cancellation access while long requests are pending. Host configuration remains trusted; no model-controlled path/command registration.

## Conversation and draft planning

Persist before paid dispatch. Allow only one active model turn per conversation and at most one dispatch per turn. Never replay generating/failed/interrupted/completed turns after restart. Freeze the trusted instruction version/hash and include the exact response schema in context for JSON-mode providers. Validate output before atomically storing the assistant message and completed state. Render returned content as text; it cannot select tools or change policy.

## Flexible 3D workspace

Native panel creation must never accept arbitrary URLs, paths, HTML or caller-chosen labels. Allow only built-in panels and exact project identifiers, with eight additional windows maximum. Treat layouts as bounded untrusted preferences: validate versions, field types, duplicate IDs, sizes and monitor reachability. UI tab/window actions must not replay requests, approve tools or cancel durable work. Keep hidden tab drafts in memory; do not put conversation bodies or credentials in layout storage.


## Versioned specification workflow - 2026-10-15

Publish only completed plans from the same owned project. Use fixed document names, canonical JSON hashing and compare-and-set version publication. Approvals must identify the exact immutable bundle. Treat document text as inert task data. Specification approval must never grant execution permissions, select commands or bypass resource grants. Preserve all nine initial project documents.


## Specification revision and delivery - 2026-10-15

Never edit an existing specification payload in place. Revisions require the parent checksum and expected latest project version. Keep exact bundle validation and idempotency inside the Core. Native export must take no renderer-supplied path or content, verify approved Core data, reject reparse points below its root and never overwrite an existing export.


## Reviewed new-file coding - 2026-10-15

Never infer new-file authority from a model-selected path. Require a registered creation target, verify absence at generation/acceptance and use exclusive creation at execution. Preserve original source, immutable baseline and protected test hashes. Retry deduplication must recover an existing run even after its new file has been created.

## Governed model jobs

Reserve a model-call slot durably before dispatch; never refund unknown billing or silently retry a generating record after restart. Reuse a durably ready response only after freshness validation and explicit resume. No provider fallback or key rotation may be inferred from a failure. Report call slots separately from currency/usage estimates.

Require explicit controller consent for selected-context sharing and immutable per-job limits. Automatic proposal acceptance needs both per-job opt-in and current full policy. Otherwise bind review to exact context/response checksums, then preserve independent task approvals. Treat test diagnostics as untrusted data; validate task/profile/input hashes, outcome consistency and cleanup before they can trigger generation. Preserve failed cycles and protected tests. Both scheduler lanes must share project-level exclusion and recovery. Original-source delivery, Git operations and production release remain separate authorities.

Exercise paid-dispatch uncertainty, late cancellation, stale evidence, role/scope boundaries and migration preservation with deterministic providers and generated fixtures. Do not require live paid calls to prove control flow. Keep task/memory/architecture records accurate and preserve the initial documentation set.

## Scaffold development rules - 2026-10-15

Keep templates host-owned and versioned. Treat specifications and contract examples as data; do not evaluate supplied test code or install hooks. Bind the reviewed specification, all planned files, destination, profile and interpreter checksum. Fail on existing destinations or changed approval; retain interrupted staging for inspection. Preserve all nine initial documents and identify generated defaults. Keep registration/native enablement and source-delivery approval separate from scaffold creation. Do not expose the maintenance command as an autonomous model tool.

## Desktop scaffold rules - 2026-10-15

Expose only fixed controller routes and host-owned roots/executables. Revalidate the approved spec and exact plan at creation; never trust renderer-supplied files or commands. Input/spec changes must discard review consent. Prevent double submission and never auto-retry uncertain filesystem effects. Recover through read-only receipt inspection, showing audit gaps. Keep registry merging, execution grants, model consent and source delivery separate.


## Integrated project-building milestone - 2026-10-15

Deliver coherent vertical milestones, including failure/recovery, regression tests and native acceptance; do not stop or propose commits for supporting components. Never stage, commit or push. Preserve all nine initial documents and update existing canonical documents in place. Keep creation, registration, host command consent, policy grants, provider sharing and delivery independent. Bind interpreter/profile/protected inputs before model calls, execution and delivery. Do not introduce arbitrary renderer paths, shell commands or automatic uncertain retries.


## Unattended operations milestone - 2026-10-16

Record outcomes atomically with source state/events. Never derive authorization from a notice, acknowledgement or UI preference. Do not include model context, test stdout, credentials or arbitrary commands in notices. Read/acknowledge must work without execution providers. Maintain larger verified milestones and no stage/commit/push; preserve the nine initial documents. Distinguish host enablement from process health and real after-exit execution from heartbeat-only evidence.
