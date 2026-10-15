# Jarvis Orchestration Core — Design System

## Maintained specification — current status

Updated 2026-10-15. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented and verified: durable core, authenticated local API, selected-file worker, owner-enabled native Windows tests, repair workflows and bounded Gemini/Groq repair proposals with versioned skill context and controller review. Native desktop control, model-backed conversation, structured draft planning and setup-readiness guidance are implemented. General autonomous building, a full configuration editor, installer/update delivery and mobile pairing remain pending.

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

## Proposal review requirements — UI still pending

Display source selection, protected tests, provider/model, skill versions, patch diff, usage and context checksum. Distinguish planned/generating/ready/accepted/failed/interrupted from coding-run states. Separate Generate, Accept and task approval controls. Explain uncertain generation and native account access. A successful fixture is not a production-ready label. No desktop visuals were implemented in this milestone.

## Implemented visual foundation

Current dedicated palette: background #0B101A, surface #111925, border #263143, text #EEF3FC, muted #99A8BE, accent #96B8FF and mint #7DD3B6. Segoe UI/system sans and Cascadia Code/monospace; 4/8/12/16/24/32 spacing and 7–10 px control/panel radii. Shell uses company rail, workspace navigation, capability canvas and inspector; detailed screens use list/inspector panels. Nodes distinguish connected, configured, unavailable and planned; configured does not claim live provider health. A list alternative exposes subsystem details. Modals trap/restore focus and respect Escape; the narrow Windows layout keeps the inspector accessible. Full accessibility/branding approval remains a separate release gate.

## Conversation and draft planning

Conversations expose Store note only, Ask Jarvis and Create project plan modes, with explicit online-model selection and no default paid provider. Show request state, usage, safe errors, inspectable context/omissions and interruption independently of pending generation. Render plans with a draft label, requirements, deliverables, phases, acceptance criteria, risks and questions. Setup shows a read-only readiness checklist; it does not silently provision services.
