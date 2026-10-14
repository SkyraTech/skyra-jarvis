# Jarvis Windows Desktop — Project Tasks

Prepared: 2026-10-14. Status: proposed implementation baseline. User requirements are captured here; technical choices remain subject to implementation validation.

## Planning baseline

All implementation tasks below are open. Existing prototype code may satisfy a task only after it is checked against the target acceptance criteria. Assign a named owner and estimate before starting; dates are not invented here.

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
