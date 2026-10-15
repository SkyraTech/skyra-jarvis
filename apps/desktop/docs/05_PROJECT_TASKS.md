# Jarvis Windows Desktop — Project Tasks

## Maintained specification — current status

Updated 2026-10-15. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented Windows control slice: dedicated React Flow subsystem canvas, project permissions, proposal review, approvals, coding checkpoints/evidence, stored conversations and recent events; Tauri Rust bridge, DPAPI credentials, hidden launcher and tray lifecycle. Release executable builds; native acceptance is recorded in the owning development tracker. Model chat, structured draft plans, setup-readiness and the flexible 3D/tabbed/multi-window workspace are implemented. Installer, signed updates, mobile pairing, configuration editing and automatic workflow scheduling remain pending. The legacy UI stays separate.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](../../../docs/ARCHITECTURE.md)
- [Current functionality and implementation boundaries](../../../docs/FUNCTIONALITY.md)
- [Current milestone and verification summary](../../../docs/DEVELOPMENT.md)

Prepared: 2026-10-14. Requirement/design baseline. Use the maintained current-status section above to distinguish implemented work from planned work.

## Planning baseline

Broad phase tasks below require their own acceptance evidence; implemented milestone summaries above take precedence over older baseline status. Existing prototype code may satisfy a task only after it is checked against the target acceptance criteria. Assign a named owner and estimate before starting; dates are not invented here.

## Phase 1: Validate Tauri packaging, sidecars and authenticated IPC on Windows

- [ ] JARVIS_DESKTOP-P1-01: Define scope, affected requirements and failure cases for this phase.
- [ ] JARVIS_DESKTOP-P1-02: Implement: validate Tauri packaging, sidecars and authenticated IPC on Windows.
- [ ] JARVIS_DESKTOP-P1-03: Run relevant contract, integration and acceptance checks; attach evidence.
- [ ] JARVIS_DESKTOP-P1-04: Review permissions, recovery and documentation; record completion in memory.

Exit gate: implementation is demonstrated against its mapped requirements; failures and follow-up work are recorded. No phase is complete merely because its files exist.

## Phase 2: Implement the design tokens, shell and subsystem registry canvas

- [ ] JARVIS_DESKTOP-P2-01: Define scope, affected requirements and failure cases for this phase.
- [ ] JARVIS_DESKTOP-P2-02: Implement: implement the design tokens, shell and subsystem registry canvas.
- [ ] JARVIS_DESKTOP-P2-03: Run relevant contract, integration and acceptance checks; attach evidence.
- [ ] JARVIS_DESKTOP-P2-04: Review permissions, recovery and documentation; record completion in memory.

Exit gate: implementation is demonstrated against its mapped requirements; failures and follow-up work are recorded. No phase is complete merely because its files exist.

## Phase 3: Build chat, run timeline, artifacts, approvals and memory views

- [ ] JARVIS_DESKTOP-P3-01: Define scope, affected requirements and failure cases for this phase.
- [ ] JARVIS_DESKTOP-P3-02: Implement: build chat, run timeline, artifacts, approvals and memory views.
- [ ] JARVIS_DESKTOP-P3-03: Run relevant contract, integration and acceptance checks; attach evidence.
- [ ] JARVIS_DESKTOP-P3-04: Review permissions, recovery and documentation; record completion in memory.

Exit gate: implementation is demonstrated against its mapped requirements; failures and follow-up work are recorded. No phase is complete merely because its files exist.

## Phase 4: Add notifications, tray, autostart, pairing and diagnostics

- [ ] JARVIS_DESKTOP-P4-01: Define scope, affected requirements and failure cases for this phase.
- [ ] JARVIS_DESKTOP-P4-02: Implement: add notifications, tray, autostart, pairing and diagnostics.
- [ ] JARVIS_DESKTOP-P4-03: Run relevant contract, integration and acceptance checks; attach evidence.
- [ ] JARVIS_DESKTOP-P4-04: Review permissions, recovery and documentation; record completion in memory.

Exit gate: implementation is demonstrated against its mapped requirements; failures and follow-up work are recorded. No phase is complete merely because its files exist.

## Phase 5: Verify accessibility, installation, updates, recovery and packaged builds

- [ ] JARVIS_DESKTOP-P5-01: Define scope, affected requirements and failure cases for this phase.
- [ ] JARVIS_DESKTOP-P5-02: Implement: verify accessibility, installation, updates, recovery and packaged builds.
- [ ] JARVIS_DESKTOP-P5-03: Run relevant contract, integration and acceptance checks; attach evidence.
- [ ] JARVIS_DESKTOP-P5-04: Review permissions, recovery and documentation; record completion in memory.

Exit gate: implementation is demonstrated against its mapped requirements; failures and follow-up work are recorded. No phase is complete merely because its files exist.

## Dependencies and sequencing

- [skyra-jarvis](../../../README.md)
- [skyra-service-contracts](../../../../skyra-service-contracts/README.md)

Start with contracts and the smallest complete workflow. Agree interfaces early; do not wait for every neighboring project to be complete. Mock fixtures are useful for development but must be replaced with isolated integration evidence before release.

## Cross-cutting release checklist

- [ ] Acceptance matrix has evidence against a commit and environment.
- [ ] Permission, isolation, restart and duplicate-delivery cases pass where applicable.
- [ ] Secrets are protected and logs are sanitized.
- [ ] Backup/migration/recovery procedure is verified for stateful components.
- [ ] Owner reviews release candidate and the configured release policy permits the next action.

## Windows control slice checkpoint

- [x] Dedicated subsystem canvas and explicit unavailable/planned states.
- [x] Project/policy controls with exact grants and optimistic policy version checking.
- [x] Proposals, approval inbox, run checkpoints/evidence, stored conversations and events.
- [x] Native allowlisted bridge, DPAPI provisioning and hidden launcher ownership tests.
- [x] Production UI build and thirteen browser acceptance cases.
- [x] Confirm/record native end-to-end release acceptance in the owning development tracker (2026-10-15).
- [ ] Configuration editing, controlled project build loops and executable workflow authoring.
- [ ] Packaged backend, installer/signing/updates, login startup/mobile pairing and crash supervisor.

The broad baseline phases remain open unless their full acceptance criteria have evidence.

## Conversation and draft planning

- [x] Durable model chat and structured draft planning, scoped to a project conversation.
- [x] Provider selection, persisted request review, usage, safe errors and interruption.
- [x] Setup-readiness checklist and chat-only provider configuration without a worker.
- [x] Migration/restart/concurrency/atomicity and browser acceptance checks.
- [x] Final Windows executable: model chat, structured plans, setup readiness and existing repair/tray regression acceptance.
- [ ] Full configuration editor, streaming replies, plan-to-build approval workflow and document/file delivery.

## Flexible 3D workspace

- [x] Interactive 3D core and separate core/system-map views.
- [x] Bounded tabs: create, switch, reorder, minimize, restore, close and keyboard navigation.
- [x] Preserve visited tab drafts across switching/minimization; restore tab metadata after restart.
- [x] Card/panel popouts, native sizing/minimize/maximize/fullscreen and show-all controls.
- [x] Save/restore window geometry with disconnected-monitor recovery.
- [x] Final native acceptance: simultaneous independent panels, native controls and saved/offscreen restoration.
- [ ] Full internal docking/tiled-panel editor, named layout profiles and installer delivery.


## Versioned specification workflow - 2026-10-15

Conversations supports versioned project specifications with plain-text document review and explicit checksum approval. The repair dialog offers an optional approved-specification link. Rust exposes four fixed controller actions; it adds no filesystem or execution capability. Core schema is now 8. Backend invariants and native acceptance evidence are maintained in the owning Jarvis ARCHITECTURE.md and DEVELOPMENT.md. General new-file builds and document export remain pending.


## Specification revision and delivery - 2026-10-15

Owner-authored revisions preserve immutable document history and parent provenance through Core schema 9. Reviewed approved bundles can be exported through a bounded native command into a dedicated version folder, with no path/content authority in the renderer. Repair context freshness still checks approved version identity; general building remains pending. Exact revision/export contracts, limits, native storage and verification are maintained in the owning Jarvis ARCHITECTURE.md and DEVELOPMENT.md.


## Reviewed new-file coding - 2026-10-15

Registered workspaces may contain explicit absent creation targets. Proposal context/review identifies these targets and full proposed file content. The existing controller acceptance, resource grants, protected tests and exact action policy still apply. Freshness checks reject unexpected files, and exclusive creation prevents overwrite. The current workflow requires pre-existing protected tests and a failing baseline; general greenfield building remains pending. See the owning ARCHITECTURE.md and DEVELOPMENT.md for the exact manifest/API contracts and current verification.
