# Skyra Coding Worker — Design System

## Maintained specification — current status

Updated 2026-10-15. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented: selected-file snapshots, guarded patch/create operations, owner-enabled native Windows tests, online-model repair jobs, bounded hidden-runner progression, native desktop review and separately approved source delivery. Approved-specification scaffolds create bounded Python JSON-function projects through the desktop or owner command with protected examples. Website/full-service scaffolds, a trusted registry editor, Git branch/revision delivery and currency budgets remain pending. Native execution carries Windows account privileges; optional Docker isolation is not live-verified.

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

## Desktop scaffold workflow - 2026-10-15

Use a labelled expandable scaffold section inside specification review. Keep file contents inert in bounded code blocks, show document provenance/destination/checksums, and use a compact review checkbox. Wrap long paths/hashes in narrow windows. Use a named status region for receipts and alerts for errors; failed/uncertain creation must remain visible.


## Integrated project-building milestone - 2026-10-15

The specification screen uses one continuous expandable workflow: complete file/provenance review, receipt, exact registration review, native-command consent, separate permission review, scoped Build jobs and final delivery. Show disabled-host/reconciliation states honestly. Grant mode affects every granted project resource and must be explicit. Discard stale consent when reviewed inputs change. Preserve responsive fieldsets without inherited clipping and suppress stale delivery readiness when a new job starts.
