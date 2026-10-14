# Skyra Agent Runtime — Design System

Prepared: 2026-10-14. Status: proposed implementation baseline. User requirements are captured here; technical choices remain subject to implementation validation.

## Principles

Show capability, readiness, progress and evidence truthfully. Make permission boundaries visible. Prefer readable dense information over decorative animation. Preserve drafts and selection through reconnects. Never present a disconnected service as available.

### Operator-facing presentation contract

This project does not require a standalone dashboard in MVP. Its capabilities appear in Jarvis or a subscribing product. Jarvis uses its dedicated design; ERP and QR may use Skyra Platform under their own scope.

Expose a readable capability name, provider/account label, connection status, permission scope, job state, timestamps, artifact references and sanitized error/recovery guidance. Use host UI typography, palette and spacing; do not ship a conflicting UI kit. Render state with text and icons as well as color. Support keyboard access and screen-reader labels in any later operator component. Example states: disconnected, needs authorization, ready, queued, running, waiting for approval, succeeded, failed and cancelled. Unknown delivery outcomes must be shown explicitly.

## Required interaction states

Provide loading, empty, partial, stale/offline, permission-denied, approval-required, successful and failed states wherever an operation is exposed. Cancellation requested and cancellation confirmed are distinct. An external operation with uncertain outcome remains unresolved until reconciled. Error messages name the next safe step and a support correlation ID.

## Validation

Test keyboard-only navigation, focus restoration after dialogs, text scaling, contrast and reduced motion. Visual snapshots complement behavior tests. Backend-only projects validate presentation payloads through consumer fixtures; they do not need invented UI screenshots. Final visual approval and branding remain pending implementation review.
