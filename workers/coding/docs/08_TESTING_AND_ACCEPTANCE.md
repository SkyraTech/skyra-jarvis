# Skyra Coding Worker — Testing and Acceptance

Prepared: 2026-10-14. Status: proposed implementation baseline. User requirements are captured here; technical choices remain subject to implementation validation.

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

No runtime tests were performed by this documentation pass. Future reports must distinguish simulated providers, local integration and production-like verification.
