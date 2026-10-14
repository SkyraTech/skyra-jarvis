# Jarvis Windows Desktop — Testing and Acceptance

## Maintained specification — current status

Updated 2026-10-14. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Planned component. No new Tauri application, workflow canvas, installer or tray supervisor has been implemented. The legacy UI is a separate prototype.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](../../../docs/ARCHITECTURE.md)
- [Current functionality and implementation boundaries](../../../docs/FUNCTIONALITY.md)
- [Current milestone and verification summary](../../../docs/DEVELOPMENT.md)

Prepared: 2026-10-14. Requirement/design baseline. Use the maintained current-status section above to distinguish implemented work from planned work.

## Project acceptance matrix

| ID | Required outcome | Evidence status |
|---|---|---|
| AC-01 | Install, launch, crash recovery and updates produce no unexpected terminal window | Not executed |
| AC-02 | Closing the window leaves the runtime in the tray when configured; Quit has distinct behaviour | Not executed |
| AC-03 | Keyboard users can navigate every operation using the canvas or list view | Not executed |
| AC-04 | A reconnected window reconstructs the correct task state from the event cursor | Not executed |
| AC-05 | Credentials and arbitrary shell execution are unavailable to the renderer | Not executed |
| AC-06 | Approval UI shows target, exact change, policy, cost implications and expiry | Not executed |

## Requirement traceability

Each requirement must receive one or more concrete test IDs. The matrix above captures critical scenarios but does not imply exhaustive feature coverage.

| Requirement | Behavior to verify | Test mapping |
|---|---|---|
| FR-01 | Installable Windows application with system tray, explicit Quit and optional sign-in autostart | Unassigned; required before implementation completion |
| FR-02 | No visible console windows for background runtime, worker, update or recovery launches | Unassigned; required before implementation completion |
| FR-03 | Subsystem canvas showing capabilities, connection readiness and permission scope | Unassigned; required before implementation completion |
| FR-04 | Live runs with task dependencies, artifacts, evidence and drill-down diagnostics | Unassigned; required before implementation completion |
| FR-05 | Conversation browser, Memory Centre, approvals inbox and incident timeline | Unassigned; required before implementation completion |
| FR-06 | Pairing and management of mobile clients; visible online/offline status | Unassigned; required before implementation completion |
| FR-07 | Accessible keyboard navigation and a list alternative to the canvas | Unassigned; required before implementation completion |
| FR-08 | Restart/reconnect without duplicated commands or lost pending user input | Unassigned; required before implementation completion |

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
