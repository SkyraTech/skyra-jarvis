# Skyra Agent Runtime — Design System

## Maintained specification — current status

Updated 2026-10-15. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented first repair runtime: explicit Gemini/Groq adapters, bounded selected-file context, versioned trusted skill loading, durable proposals and controller acceptance into tested coding runs. Durable chat and structured draft planning are also implemented without requiring a coding worker. General execution planning, skill discovery, teaching memory and autonomous scheduling remain pending. Legacy adapters remain separate.

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

## Proposal review requirements — UI still pending

Display source selection, protected tests, provider/model, skill versions, patch diff, usage and context checksum. Distinguish planned/generating/ready/accepted/failed/interrupted from coding-run states. Separate Generate, Accept and task approval controls. Explain uncertain generation and native account access. A successful fixture is not a production-ready label. No desktop visuals were implemented in this milestone.

## Conversation and draft planning

Conversations expose Store note only, Ask Jarvis and Create project plan modes, with explicit online-model selection and no default paid provider. Show request state, usage, safe errors, inspectable context/omissions and interruption independently of pending generation. Render plans with a draft label, requirements, deliverables, phases, acceptance criteria, risks and questions. Setup shows a read-only readiness checklist; it does not silently provision services.


## Reviewed new-file coding - 2026-10-15

Registered workspaces may contain explicit absent creation targets. Proposal context/review identifies these targets and full proposed file content. The existing controller acceptance, resource grants, protected tests and exact action policy still apply. Freshness checks reject unexpected files, and exclusive creation prevents overwrite. The current workflow requires pre-existing protected tests and a failing baseline; general greenfield building remains pending. See the owning ARCHITECTURE.md and DEVELOPMENT.md for the exact manifest/API contracts and current verification.
