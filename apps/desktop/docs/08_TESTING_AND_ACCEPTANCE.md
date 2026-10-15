# Jarvis Windows Desktop — Testing and Acceptance

## Maintained specification — current status

Updated 2026-10-15. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented Windows control slice: dedicated React Flow subsystem canvas, project permissions, proposal review, approvals, coding checkpoints/evidence, stored conversations and recent events; Tauri Rust bridge, DPAPI credentials, hidden launcher and tray lifecycle. Release executable builds; native acceptance is recorded in the owning development tracker. Model chat, structured draft plans, setup-readiness and the flexible 3D/tabbed/multi-window workspace are implemented. Reviewed specification-to-scaffold creation and receipt recovery are implemented within a trusted host root. Installer, signed updates, mobile pairing, registry/configuration editing and automatic workflow scheduling remain pending. The legacy UI stays separate.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](../../../docs/ARCHITECTURE.md)
- [Current functionality and implementation boundaries](../../../docs/FUNCTIONALITY.md)
- [Current milestone and verification summary](../../../docs/DEVELOPMENT.md)

Prepared: 2026-10-14. Requirement/design baseline. Use the maintained current-status section above to distinguish implemented work from planned work.

## Project acceptance matrix

| ID | Required outcome | Evidence status |
|---|---|---|
| AC-01 | Install, launch, crash recovery and updates produce no unexpected terminal window | Not executed |
| AC-02 | Closing the window leaves the runtime in the tray when configured; Quit has distinct behaviour | Not executed |
| AC-03 | Keyboard users can navigate every operation using the canvas or list view | Not executed |
| AC-04 | A reconnected window reconstructs the correct task state from the event cursor | Not executed |
| AC-05 | Credentials and arbitrary shell execution are unavailable to the renderer | Not executed |
| AC-06 | Approval UI shows target, exact change, policy, cost implications and expiry | Not executed |

## Requirement traceability

Each requirement must receive one or more concrete test IDs. The matrix above captures critical scenarios but does not imply exhaustive feature coverage.

| Requirement | Behavior to verify | Test mapping |
|---|---|---|
| FR-01 | Installable Windows application with system tray, explicit Quit and optional sign-in autostart | Unassigned; required before implementation completion |
| FR-02 | No visible console windows for background runtime, worker, update or recovery launches | Unassigned; required before implementation completion |
| FR-03 | Subsystem canvas showing capabilities, connection readiness and permission scope | Unassigned; required before implementation completion |
| FR-04 | Live runs with task dependencies, artifacts, evidence and drill-down diagnostics | Unassigned; required before implementation completion |
| FR-05 | Conversation browser, Memory Centre, approvals inbox and incident timeline | Unassigned; required before implementation completion |
| FR-06 | Pairing and management of mobile clients; visible online/offline status | Unassigned; required before implementation completion |
| FR-07 | Accessible keyboard navigation and a list alternative to the canvas | Unassigned; required before implementation completion |
| FR-08 | Restart/reconnect without duplicated commands or lost pending user input | Unassigned; required before implementation completion |

## Test layers

- Unit: domain decisions, policy evaluation, state transitions, parsing and failure classification.
- Contract: input/output examples, error shape, consumer compatibility and event schemas.
- Integration: real isolated storage, adapter behavior, credentials scoping, retries and provider sandbox where available.
- End-to-end: authorized user workflow through actual boundaries; Playwright where a browser/UI is involved and Windows process tests for desktop launches.
- Recovery/security: crash between intent and dispatch, duplicate events, expired leases, denied scopes, cross-tenant attempts, stale approvals and secret redaction.

For package-only projects, independent consumer tests replace server/deployment tests. Provider tests must use approved test accounts; do not send messages, publish content or incur charges against arbitrary live users.

## Release gate

Record commit, tool/dependency versions, test command, environment, timestamps, result and artifact links. All required checks must pass or carry an explicitly reviewed exception. Track line and branch coverage separately; establish project thresholds from the first trustworthy baseline and protect critical paths with direct behavioral tests. A high coverage percentage alone is not acceptance.

Dependency and vulnerability findings are triaged by severity, exploitability and reachability. No unreviewed critical/high finding in the release scope. Active DAST requires an owned, explicitly selected target; baseline scans and active attacks are different operations. Quality runners must isolate untrusted code and cap runtime/resource usage.

The initial documentation pass ran no runtime tests; later implementation evidence is recorded in the current-status references above. Future reports must distinguish simulated providers, local integration and production-like verification.

## Desktop acceptance evidence

TypeScript and production assets build. Eleven Playwright cases cover disconnected browser isolation, labelled preview/canvas truth, patch review, exact-action rejection, text-safe conversation saving, run cancellation, explicit context selection, modal focus, project dialog routing, narrow layout and version-aware policy controls. The cancellation case verifies late responses cannot revive a cancelled run while a request is pending. Core checks cover dashboard owner/role boundaries and stale policy versions. DPAPI/launcher tests cover protected state, refusal to overwrite, hidden child flags, ownership and redirect rejection. Native Rust routing checks reject arbitrary URL/shell actions, invalid IDs and token-field injection. Record the real Windows release flow separately in the owning development tracker; fixture-only tests do not prove native integration or general model quality.

## Conversation and draft planning

Acceptance includes provider selection, stored notes, safe text rendering, chat replies/usage, structured plan sections, failure without replay, missing providers, active interruption and late-output suppression. Runtime tests cover migration from schema 6, byte-bounded contiguous history with omission counts, Unicode size rejection, immutable instruction hashes, concurrent single dispatch, restart uncertainty and atomic assistant-message/state writes. Native acceptance uses deterministic providers only; separate explicitly authorized live probes use fictional prompts.

## Flexible 3D workspace

Workspace acceptance covers keyboard/pointer-accessible 3D rotation, reduced-motion orbit, tab draft preservation/minimization/reordering/reload, corrupt preference recovery, focus mode, separate core/map views, card popouts and small-window overflow. Rust checks cover fixed panel targets, project/label validation, duplicate/versioned arrangement rejection and missing/negative monitor coordinates. Native acceptance must verify actual independent WebView windows, size/minimize/maximize/fullscreen, saved arrangement recreation and offscreen recovery in addition to the existing repair/chat/plan/tray flow.

Final native acceptance uses a fresh fixture-specific WebView2 user-data folder as well as fixture credentials/database, and verifies that profile isolation before reporting success. Connection badges may be hidden by responsive styles; actual project selection and stored history verify connectivity in narrow child windows.


## Versioned specification workflow - 2026-10-15

Conversations supports versioned project specifications with plain-text document review and explicit checksum approval. The repair dialog offers an optional approved-specification link. Rust exposes four fixed controller actions; it adds no filesystem or execution capability. Core schema is now 8. Backend invariants and native acceptance evidence are maintained in the owning Jarvis ARCHITECTURE.md and DEVELOPMENT.md. General new-file builds and document export remain pending.


## Specification revision and delivery - 2026-10-15

Owner-authored revisions preserve immutable document history and parent provenance through Core schema 9. Reviewed approved bundles can be exported through a bounded native command into a dedicated version folder, with no path/content authority in the renderer. Repair context freshness still checks approved version identity; general building remains pending. Exact revision/export contracts, limits, native storage and verification are maintained in the owning Jarvis ARCHITECTURE.md and DEVELOPMENT.md.


## Reviewed new-file coding - 2026-10-15

Registered workspaces may contain explicit absent creation targets. Proposal context/review identifies these targets and full proposed file content. The existing controller acceptance, resource grants, protected tests and exact action policy still apply. Freshness checks reject unexpected files, and exclusive creation prevents overwrite. The current workflow requires pre-existing protected tests and a failing baseline; general greenfield building remains pending. See the owning ARCHITECTURE.md and DEVELOPMENT.md for the exact manifest/API contracts and current verification.

## Desktop scaffold workflow - 2026-10-15

Verify disabled host, controller/project ownership, arbitrary renderer field refusal, stale approval/hash rejection, explicit UI consent and edited-plan invalidation. Simulate uncertain create then recover through receipt without retry. Validate narrow layout, malformed JSON, missing audit and receipt tampering. Native fixture checks real file publication, nine-document preservation and disabled execution draft; exact results belong in the owning DEVELOPMENT.md.


## Integrated project-building milestone - 2026-10-15

Regression evidence: 275 distinct passing checks plus one existing Windows symlink-privilege skip; deterministic providers only. New integration verifies schema-11 migration, owner/role scope, exact/idempotent registration, restart restore, tampered metadata isolation, weaker-profile refusal, protected server writes, changed interpreter before generation, invalid HTTP contracts, actual GET/POST acceptance, failed first model repair, successful second repair and independent ask-mode delivery. Browser tests exercise explicit registration/permission/model consents and host-disabled refusal. Final Windows acceptance and rendered delivered-site evidence belong in the canonical DEVELOPMENT.md.
