# Jarvis Orchestration Core — Design System

## Maintained specification — current status

Updated 2026-10-14. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented and verified: durable core, authenticated local API, selected-file worker, owner-enabled native Windows test execution and controller-supplied repair workflows. New desktop and model-generated repairs are not yet implemented.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](ARCHITECTURE.md)
- [Current functionality and implementation boundaries](FUNCTIONALITY.md)
- [Current milestone and verification summary](DEVELOPMENT.md)

Prepared: 2026-10-14. Requirement/design baseline. Use the maintained current-status section above to distinguish implemented work from planned work.

## Principles

Show capability, readiness, progress and evidence truthfully. Make permission boundaries visible. Prefer readable dense information over decorative animation. Preserve drafts and selection through reconnects. Never present a disconnected service as available.

### Jarvis visual foundation

Dedicated Jarvis design; do not import Skyra Platform UI. Proposed tokens: background #0B1220, surface #111C2F, raised surface #1B2940, primary text #F3F6FC, secondary text #B9C5D8, accent #75B8FF, success #72D6A0, warning #FFD166, error #FF8F9A. Verify contrast in actual component states before adoption.

Use Segoe UI/system sans for interface and Cascadia Code/system monospace for code. Type sizes: 12 metadata, 14 controls, 16 body, 20 section, 28 page title. Spacing scale: 4/8/12/16/24/32/48 px; 8 px control radius and 12 px panels. Focus rings remain visible; never encode status using color alone.

Primary shell: navigation rail, central subsystem/workflow canvas, inspector, conversation panel and approval inbox. A node shows name, available capability, readiness, current task and permission scope. Edges describe actual dependencies, not decorative activity. Provide zoom, fit, keyboard selection, searchable list alternative, minimap and reduced motion. Inspector exposes evidence/artifacts without exposing credentials.

Approval cards show exact action, target, account, cost/risk when known, expiry and scope. Changed actions require a fresh decision. Destructive decisions cannot be the default focused action. Mobile layouts prioritize approvals, run status and cancellation over editing large graphs.

## Required interaction states

Provide loading, empty, partial, stale/offline, permission-denied, approval-required, successful and failed states wherever an operation is exposed. Cancellation requested and cancellation confirmed are distinct. An external operation with uncertain outcome remains unresolved until reconciled. Error messages name the next safe step and a support correlation ID.

## Validation

Test keyboard-only navigation, focus restoration after dialogs, text scaling, contrast and reduced motion. Visual snapshots complement behavior tests. Backend-only projects validate presentation payloads through consumer fixtures; they do not need invented UI screenshots. Final visual approval and branding remain pending implementation review.
