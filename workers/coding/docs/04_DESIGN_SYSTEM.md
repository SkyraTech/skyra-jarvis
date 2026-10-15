# Skyra Coding Worker — Design System

## Maintained specification — current status

Updated 2026-10-14. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented: selected-file snapshots, guarded file operations, explicitly owner-enabled native Windows test execution and durable controller-supplied repair workflows. Online-model patch generation, branch/revision delivery and the new desktop are pending. Native execution carries Windows account privileges; Docker isolation is optional and not live-verified.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](../../../docs/ARCHITECTURE.md)
- [Current functionality and implementation boundaries](../../../docs/FUNCTIONALITY.md)
- [Current milestone and verification summary](../../../docs/DEVELOPMENT.md)

Prepared: 2026-10-14. Requirement/design baseline. Use the maintained current-status section above to distinguish implemented work from planned work.

## Principles

Show capability, readiness, progress and evidence truthfully. Make permission boundaries visible. Prefer readable dense information over decorative animation. Preserve drafts and selection through reconnects. Never present a disconnected service as available.

### Operator-facing presentation contract

This project does not require a standalone dashboard in MVP. Its capabilities appear in Jarvis or a subscribing product. Jarvis uses its dedicated design; ERP and QR may use Skyra Platform under their own scope.

Expose a readable capability name, provider/account label, connection status, permission scope, job state, timestamps, artifact references and sanitized error/recovery guidance. Use host UI typography, palette and spacing; do not ship a conflicting UI kit. Render state with text and icons as well as color. Support keyboard access and screen-reader labels in any later operator component. Example states: disconnected, needs authorization, ready, queued, running, waiting for approval, succeeded, failed and cancelled. Unknown delivery outcomes must be shown explicitly.

## Required interaction states

Provide loading, empty, partial, stale/offline, permission-denied, approval-required, successful and failed states wherever an operation is exposed. Cancellation requested and cancellation confirmed are distinct. An external operation with uncertain outcome remains unresolved until reconciled. Error messages name the next safe step and a support correlation ID.

## Validation

Test keyboard-only navigation, focus restoration after dialogs, text scaling, contrast and reduced motion. Visual snapshots complement behavior tests. Backend-only projects validate presentation payloads through consumer fixtures; they do not need invented UI screenshots. Final visual approval and branding remain pending implementation review.


## Reviewed new-file coding - 2026-10-15

Proposal review distinguishes New file target from selected existing source and protected tests. Show New file (must not exist) plus the complete proposed content. The workspace selection dialog labels explicitly allowed creation targets; normal task approvals remain visible in Approvals.
