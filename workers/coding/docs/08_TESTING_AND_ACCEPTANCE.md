# Skyra Coding Worker — Testing and Acceptance

## Maintained specification — current status

Updated 2026-10-15. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented: selected-file snapshots, guarded patch/create operations, owner-enabled native Windows tests, online-model repair jobs, bounded hidden-runner progression, native desktop review and separately approved source delivery. Approved-specification scaffolds create bounded Python JSON-function projects through the desktop or owner command with protected examples. Website/full-service scaffolds, a trusted registry editor, Git branch/revision delivery and currency budgets remain pending. Native execution carries Windows account privileges; optional Docker isolation is not live-verified.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](../../../docs/ARCHITECTURE.md)
- [Current functionality and implementation boundaries](../../../docs/FUNCTIONALITY.md)
- [Current milestone and verification summary](../../../docs/DEVELOPMENT.md)

Prepared: 2026-10-14. Requirement/design baseline. Use the maintained current-status section above to distinguish implemented work from planned work.

## Project acceptance matrix

| ID | Required outcome | Evidence status |
|---|---|---|
| AC-01 | Paths, symlinks and subprocesses cannot access resources beyond the configured execution boundary | Not executed |
| AC-02 | Unrelated user changes are excluded from delivery | Not executed |
| AC-03 | Timeout and cancel terminate owned descendant processes | Not executed |
| AC-04 | Active Git locks are never deleted automatically | Not executed |
| AC-05 | A failed test cannot be converted to success by changing the gate definition | Not executed |
| AC-06 | No direct production push or deploy occurs without the applicable grant | Not executed |

## Requirement traceability

Each requirement must receive one or more concrete test IDs. The matrix above captures critical scenarios but does not imply exhaustive feature coverage.

| Requirement | Behavior to verify | Test mapping |
|---|---|---|
| FR-01 | Repository registration and isolated workspaces per run | Unassigned; required before implementation completion |
| FR-02 | Read/search/edit/patch capabilities restricted to granted workspaces | Unassigned; required before implementation completion |
| FR-03 | Explicit branch/base revision and selected-file change delivery | Unassigned; required before implementation completion |
| FR-04 | Process supervision, timeouts, cancellation and process-tree cleanup | Unassigned; required before implementation completion |
| FR-05 | Build/test execution with captured outputs and resource metrics | Unassigned; required before implementation completion |
| FR-06 | Structured diffs, test artifacts and reproducible environment manifests | Unassigned; required before implementation completion |
| FR-07 | Separate release/deployment actions governed by policy | Unassigned; required before implementation completion |

## Test layers

- Unit: domain decisions, policy evaluation, state transitions, parsing and failure classification.
- Contract: input/output examples, error shape, consumer compatibility and event schemas.
- Integration: real isolated storage, adapter behavior, credentials scoping, retries and provider sandbox where available.
- End-to-end: authorized user workflow through actual boundaries; Playwright where a browser/UI is involved and Windows process tests for desktop launches.
- Recovery/security: crash between intent and dispatch, duplicate events, expired leases, denied scopes, cross-tenant attempts, stale approvals and secret redaction.

For package-only projects, independent consumer tests replace server/deployment tests. Provider tests must use approved test accounts; do not send messages, publish content or incur charges against arbitrary live users.

## Release gate

Record commit, tool/dependency versions, test command, environment, timestamps, result and artifact links. All required checks must pass or carry an explicitly reviewed exception. Track line and branch coverage separately; establish project thresholds from the first trustworthy baseline and protect critical paths with direct behavioral tests. A high coverage percentage alone is not acceptance.

Dependency and vulnerability findings are triaged by severity, exploitability and reachability. No unreviewed critical/high finding in the release scope. Active DAST requires an owned, explicitly selected target; baseline scans and active attacks are different operations. Quality runners must isolate untrusted code and cap runtime/resource usage.

The initial documentation pass ran no runtime tests; later implementation evidence is recorded in the current-status references above. Future reports must distinguish simulated providers, local integration and production-like verification.

## Model proposal integration

The controller can now accept a validated Gemini/Groq proposal into this worker's existing repair workflow. The runtime selects context/skills and validates patches; this worker retains protected-test, policy/approval, native-execution and evidence gates. Acceptance does not execute a task. General building and autonomous scheduling remain pending. See the owning Jarvis architecture/development records for schema 6, API and verified fixture evidence.


## Reviewed new-file coding - 2026-10-15

Checks cover declared-only creation, path/case/prefix conflicts, existing-file refusal, exact write approval, durable reload/diff, missing static verification, absent protected-test rejection, model unselected-target refusal, stale-absence refusal, approved-specification supersession and retry deduplication after creation. Runtime acceptance executes a real missing-module failing baseline and passing protected retest. Native fixture now exercises a reviewed new module through three approvals and verifies the original source has no generated file. Final counts/evidence are recorded in DEVELOPMENT.md.

## Approved-specification scaffolds - 2026-10-15

The scaffold suite covers approved specification/owner integrity, deterministic no-effect preview, contract data/limits/types, nine-document provenance, path/device/executable/junction guards, interpreter drift, exact review, exclusive publication, staging/audit failures and owner-command behavior. Native integration verifies failing stub -> deterministic repair -> passing protected retest/diff -> separate source approval/delivery. See the owning DEVELOPMENT.md for current counts and boundaries.

## Desktop scaffold workflow - 2026-10-15

Verify disabled host, controller/project ownership, arbitrary renderer field refusal, stale approval/hash rejection, explicit UI consent and edited-plan invalidation. Simulate uncertain create then recover through receipt without retry. Validate narrow layout, malformed JSON, missing audit and receipt tampering. Native fixture checks real file publication, nine-document preservation and disabled execution draft; exact results belong in the owning DEVELOPMENT.md.


## Integrated project-building milestone - 2026-10-15

Regression evidence: 275 distinct passing checks plus one existing Windows symlink-privilege skip; deterministic providers only. New integration verifies schema-11 migration, owner/role scope, exact/idempotent registration, restart restore, tampered metadata isolation, weaker-profile refusal, protected server writes, changed interpreter before generation, invalid HTTP contracts, actual GET/POST acceptance, failed first model repair, successful second repair and independent ask-mode delivery. Browser tests exercise explicit registration/permission/model consents and host-disabled refusal. Final Windows acceptance and rendered delivered-site evidence belong in the canonical DEVELOPMENT.md.
