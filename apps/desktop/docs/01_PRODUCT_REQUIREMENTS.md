# Jarvis Windows Desktop — Product Requirements

## Maintained specification — current status

Updated 2026-10-15. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented Windows control slice: dedicated React Flow subsystem canvas, project permissions, proposal review, approvals, coding checkpoints/evidence, stored conversations and recent events; Tauri Rust bridge, DPAPI credentials, hidden launcher and tray lifecycle. Release executable builds; native acceptance is recorded in the owning development tracker. Model chat, structured draft plans and a setup-readiness checklist are implemented. Installer, signed updates, mobile pairing, configuration editing and automatic workflow scheduling remain pending. The legacy UI stays separate.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](../../../docs/ARCHITECTURE.md)
- [Current functionality and implementation boundaries](../../../docs/FUNCTIONALITY.md)
- [Current milestone and verification summary](../../../docs/DEVELOPMENT.md)

Prepared: 2026-10-14. Requirement/design baseline. Use the maintained current-status section above to distinguish implemented work from planned work.

## Product overview

The dedicated Windows control centre for Jarvis: a workflow canvas of available subsystems, live task graphs, conversation panels, approvals, memory and incidents. Uses its own UI design, not Skyra Platform components.

## Problem and current baseline

Initial baseline: documentation-only project at the time of specification; current implementation status is stated above. No application shell, installer or UI implementation exists here yet.

Existing prototypes do not establish production readiness. The objective is a reusable, testable boundary with explicit ownership and verifiable outcomes.

## Target users and goals

Primary users: Skyra owner and authorized employees; consuming applications and delegated agents act under those users' scoped identities. Commercial customers use separately branded products rather than inheriting internal Jarvis privileges.

Success means the capabilities below pass recorded acceptance checks, survive expected failures and expose enough evidence for a human to review the result.

## Core requirements / MVP

- **FR-01:** Installable Windows application with system tray, explicit Quit and optional sign-in autostart
- **FR-02:** No visible console windows for background runtime, worker, update or recovery launches
- **FR-03:** Subsystem canvas showing capabilities, connection readiness and permission scope
- **FR-04:** Live runs with task dependencies, artifacts, evidence and drill-down diagnostics
- **FR-05:** Conversation browser, Memory Centre, approvals inbox and incident timeline
- **FR-06:** Pairing and management of mobile clients; visible online/offline status
- **FR-07:** Accessible keyboard navigation and a list alternative to the canvas
- **FR-08:** Restart/reconnect without duplicated commands or lost pending user input

## Boundaries

This project delivers its declared capabilities only. No automatic production release, account creation, purchase or broader permission is implied by an AI plan. Article-dashboard implementation, ERP, Skyra Platform and QR changes are outside this documentation initiative. Future local models and hosted Jarvis must preserve the same authorization contracts.

## User journey

An authorized caller selects a capability and resource scope, submits validated input, receives either a result or a durable job reference, follows progress and retrieves evidence. Policy may require an exact-action approval before execution. Failures present recovery guidance without claiming success.

## Acceptance and unresolved decisions

See [testing](08_TESTING_AND_ACCEPTANCE.md) for release evidence and [tasks](05_PROJECT_TASKS.md) for implementation sequence.

- Tauri packaging and Rust toolchain must be proven before UI expansion
- Windows native interactions need tests beyond browser-only Playwright
- Code signing and update distribution ownership are undecided

## Implemented Windows control requirements

Deliver a native internal control centre with an n8n-style subsystem map, clear unavailable states and exact-action review. This slice covers project/policy selection, repair proposals, approval inbox, coding checkpoints/evidence, durable conversation display and activity. It does not yet provide autonomous project generation, automatic chat replies, workflow authoring, mobile pairing or connected third-party services.

## Conversation and draft planning

Online conversation and draft planning are implemented as distinct modes alongside local notes. The owner explicitly chooses a registered provider/model. Plans contain requirements, deliverables, ordered phases/tasks/acceptance, risks and open questions. This does not authorize execution or claim that files, builds or deployments were completed. A coding worker is optional for chat/planning.
