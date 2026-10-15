# Jarvis Windows Desktop — Design System

## Maintained specification — current status

Updated 2026-10-15. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented Windows control slice: dedicated React Flow subsystem canvas, project permissions, proposal review, approvals, coding checkpoints/evidence, stored conversations and recent events; Tauri Rust bridge, DPAPI credentials, hidden launcher and tray lifecycle. Release executable builds; native acceptance is recorded in the owning development tracker. Model chat, structured draft plans, setup-readiness and the flexible 3D/tabbed/multi-window workspace are implemented. Reviewed specification-to-scaffold creation and receipt recovery are implemented within a trusted host root. Installer, signed updates, mobile pairing, registry/configuration editing and automatic workflow scheduling remain pending. The legacy UI stays separate.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](../../../docs/ARCHITECTURE.md)
- [Current functionality and implementation boundaries](../../../docs/FUNCTIONALITY.md)
- [Current milestone and verification summary](../../../docs/DEVELOPMENT.md)

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

## Implemented visual foundation

Current dedicated palette: background #0B101A, surface #111925, border #263143, text #EEF3FC, muted #99A8BE, accent #96B8FF and mint #7DD3B6. Segoe UI/system sans and Cascadia Code/monospace; 4/8/12/16/24/32 spacing and 7–10 px control/panel radii. Shell uses company rail, workspace navigation, capability canvas and inspector; detailed screens use list/inspector panels. Nodes distinguish connected, configured, unavailable and planned; configured does not claim live provider health. A list alternative exposes subsystem details. Modals trap/restore focus and respect Escape; the narrow Windows layout keeps the inspector accessible. Full accessibility/branding approval remains a separate release gate.

## Conversation and draft planning

Conversations expose Store note only, Ask Jarvis and Create project plan modes, with explicit online-model selection and no default paid provider. Show request state, usage, safe errors, inspectable context/omissions and interruption independently of pending generation. Render plans with a draft label, requirements, deliverables, phases, acceptance criteria, risks and questions. Setup shows a read-only readiness checklist; it does not silently provision services.

## Flexible 3D workspace

Jarvis has a cyan/blue 3D orbital core on the overview and a separate Core view; it supports pointer/keyboard rotation, optional orbit animation and reduced-motion preferences. Preserve the system map as a separate workspace view. Persistent top tabs and Arrange controls stay visible while content scrolls within the available viewport. Focus layout hides navigation; dedicated native windows retain standard Windows title bars and snap/resize behavior. Maintain readable cards and no horizontal page overflow at tested small-window sizes.


## Reviewed new-file coding - 2026-10-15

Registered workspaces may contain explicit absent creation targets. Proposal context/review identifies these targets and full proposed file content. The existing controller acceptance, resource grants, protected tests and exact action policy still apply. Freshness checks reject unexpected files, and exclusive creation prevents overwrite. The current workflow requires pre-existing protected tests and a failing baseline; general greenfield building remains pending. See the owning ARCHITECTURE.md and DEVELOPMENT.md for the exact manifest/API contracts and current verification.

## Desktop scaffold workflow - 2026-10-15

Use a labelled expandable scaffold section inside specification review. Keep file contents inert in bounded code blocks, show document provenance/destination/checksums, and use a compact review checkbox. Wrap long paths/hashes in narrow windows. Use a named status region for receipts and alerts for errors; failed/uncertain creation must remain visible.


## Integrated project-building milestone - 2026-10-15

The specification screen uses one continuous expandable workflow: complete file/provenance review, receipt, exact registration review, native-command consent, separate permission review, scoped Build jobs and final delivery. Show disabled-host/reconciliation states honestly. Grant mode affects every granted project resource and must be explicit. Discard stale consent when reviewed inputs change. Preserve responsive fieldsets without inherited clipping and suppress stale delivery readiness when a new job starts.
