# Skyra Agent Runtime — Testing and Acceptance

Prepared: 2026-10-14. Status: proposed implementation baseline. User requirements are captured here; technical choices remain subject to implementation validation.

## Project acceptance matrix

| ID | Required outcome | Evidence status |
|---|---|---|
| AC-01 | A skill cannot grant itself tools outside the parent task permission envelope | Not executed |
| AC-02 | Fallback refuses models missing required vision, tools or schema capabilities | Not executed |
| AC-03 | A restart resumes from a checkpoint without blindly repeating completed side effects | Not executed |
| AC-04 | Child tasks cannot escape the parent project, budget or resource scope | Not executed |
| AC-05 | Evaluation failures remain failures even if the model claims success | Not executed |
| AC-06 | Provider secrets never enter persisted prompts or tool result logs | Not executed |

## Requirement traceability

Each requirement must receive one or more concrete test IDs. The matrix above captures critical scenarios but does not imply exhaustive feature coverage.

| Requirement | Behavior to verify | Test mapping |
|---|---|---|
| FR-01 | Versioned SKILL.md packages with required tools, resources and acceptance checks | Unassigned; required before implementation completion |
| FR-02 | Progressive loading of skill metadata and task-relevant content | Unassigned; required before implementation completion |
| FR-03 | Online model adapters for tool calling, structured output, vision and streaming | Unassigned; required before implementation completion |
| FR-04 | Persistent agent checkpoints and resumable task execution | Unassigned; required before implementation completion |
| FR-05 | Scoped child-task delegation with bounded concurrency and cancellation | Unassigned; required before implementation completion |
| FR-06 | Explicit planning/review/verification roles with shared task contracts | Unassigned; required before implementation completion |
| FR-07 | Token/cost accounting and capability-compatible provider fallback | Unassigned; required before implementation completion |
| FR-08 | Evaluation datasets for tool selection, permissions, recovery and completion claims | Unassigned; required before implementation completion |

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
