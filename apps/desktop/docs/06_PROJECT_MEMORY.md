# Jarvis Windows Desktop — Project Memory

## Maintained specification — current status

Updated 2026-10-16. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented Windows control slice: dedicated React Flow subsystem canvas, project permissions, proposal review, approvals, coding checkpoints/evidence, stored conversations and recent events; Tauri Rust bridge, DPAPI credentials, hidden launcher and tray lifecycle. Release executable builds; native acceptance is recorded in the owning development tracker. Model chat, structured draft plans, setup-readiness and the flexible 3D/tabbed/multi-window workspace are implemented. Reviewed specification-to-scaffold creation and receipt recovery are implemented within a trusted host root. Installer, signed updates, mobile pairing, registry/configuration editing and automatic workflow scheduling remain pending. The legacy UI stays separate.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](../../../docs/ARCHITECTURE.md)
- [Current functionality and implementation boundaries](../../../docs/FUNCTIONALITY.md)
- [Current milestone and verification summary](../../../docs/DEVELOPMENT.md)

## Current verification

Current operations-center verification: schema 13, 53 Core/API and 42 browser checks passed, with all 289 regression checks passing (one existing symlink-privilege skip); final Windows acceptance passed with evidence below. The final complete totals and executable evidence in DEVELOPMENT.md supersede historical milestone counts below.

## Completed work

Initial requirements, architecture, development/design standards, task plan, API direction, testing and security specifications are retained. Implementation remains at the status stated above.

## Pending work and next milestone

- Rust/MSVC prerequisites and portable Tauri release compilation are proven; installer packaging remains pending
- Native repair, tray and single-instance acceptance complement production-browser tests; see the owning development tracker for the exact release evidence
- Code signing and update distribution ownership are undecided

Follow the component task document and the owning project development tracker. Assign an owner and verify relevant acceptance checks before marking a task complete.

## Maintenance rules

Update this memory for current status, decisions, blockers and next work. Update the other initial documents when their requirements/design/contracts change; keep the detailed implemented database architecture reference aligned with code. Do not generate a new report per task. Git retains historical revisions. The owner stages/commits/pushes manually; the assistant reports a substantial verified milestone and waits for confirmation before proceeding.

## Windows control milestone memory

The first control slice now has source and a release executable: dedicated subsystem canvas, permission review, proposal/approval/run/evidence screens, stored history and recent events. Controller/worker tokens are DPAPI protected and retained by the native host. The hidden Python launcher is ownership-aware; closing hides to tray, while explicit Exit ends the application. Existing nine documents are retained and updated. Exact verification/artifact details and remaining native checks live in the owning development tracker; no staging, commits or pushes were performed by the assistant.

## Conversation and draft planning

Current conversation/planning status: schema 7, deterministic tests and live Gemini chat/Groq draft-plan checks implemented. A Groq schema-prompt issue was caught by the live probe and corrected; failed requests remain terminal. Exact native release proof and full counts live in the owning development tracker. No staging, commits or pushes. Next: trusted configuration editing and explicit plan-to-build handoff.

## Flexible 3D workspace

The flexible workspace phase adds a 3D core, tab shell and independent native panels. Tab metadata is automatically restored; visited tab drafts survive switching/minimization within the session but are not persisted across application restart or tab closure. Saved native window arrangements are restored explicitly from Arrange. The main window closes to tray; child windows close independently. Detailed verification and final release evidence belong to the owning development tracker. No legacy assistant code or user data was removed.


## Versioned specification workflow - 2026-10-15

Conversations supports versioned project specifications with plain-text document review and explicit checksum approval. The repair dialog offers an optional approved-specification link. Rust exposes four fixed controller actions; it adds no filesystem or execution capability. Core schema is now 8. Backend invariants and native acceptance evidence are maintained in the owning Jarvis ARCHITECTURE.md and DEVELOPMENT.md. General new-file builds and document export remain pending.


## Specification revision and delivery - 2026-10-15

Owner-authored revisions preserve immutable document history and parent provenance through Core schema 9. Reviewed approved bundles can be exported through a bounded native command into a dedicated version folder, with no path/content authority in the renderer. Repair context freshness still checks approved version identity; general building remains pending. Exact revision/export contracts, limits, native storage and verification are maintained in the owning Jarvis ARCHITECTURE.md and DEVELOPMENT.md.


## Reviewed new-file coding - 2026-10-15

Registered workspaces may contain explicit absent creation targets. Proposal context/review identifies these targets and full proposed file content. The existing controller acceptance, resource grants, protected tests and exact action policy still apply. Freshness checks reject unexpected files, and exclusive creation prevents overwrite. The current workflow requires pre-existing protected tests and a failing baseline; general greenfield building remains pending. See the owning ARCHITECTURE.md and DEVELOPMENT.md for the exact manifest/API contracts and current verification.

## Desktop scaffold review/create milestone - 2026-10-15

Implemented specification-screen review/create with owner-authored contract, complete file/provenance/profile/destination review and explicit consent. Input/spec changes invalidate approval; a synchronous gate prevents double dispatch. Creation is host-disabled by default and can use only an existing trusted scaffold_root and the Core interpreter. Fixed controller routes reject arbitrary renderer filesystem/executable fields and agent/worker roles.

Receipt lookup checks the exact project/specification/destination/plan and matching creation audit event without replaying file writes. Missing audit is visible for reconciliation; initial receipts do not claim current build/deployment status. New bootstrap configurations keep scaffold_root null. Trusted registration/profile merging, execution grants, provider consent and separate delivery approval remain distinct manual steps. Website/HTTP templates and registry editing remain next work.

Verification: 263 passing checks plus one existing symlink-privilege skip, with final native evidence maintained in the owning DEVELOPMENT.md. One browser locator incorrectly queried a status region as region; corrected its accessibility selector and the test passed. No paid model calls, dependency/schema updates, actual private setup changes, staging, commits or pushes. Initial documents were preserved and updated in place.

Final native evidence: .runtime/desktop-native-1792085731169/review.json with native-scaffold-review.png and native-scaffold-created.png. The final executable embeds /assets/index-PUdHEJrB.js and passed reviewed creation, receipt recovery/audit, nine-document preservation, disabled execution draft and continuous form geometry. Existing coding/delivery, native windows and worker-after-desktop-exit checks also passed; zero paid calls. Exact executable checksum and harness synchronization/layout findings are recorded in the owning DEVELOPMENT.md. No staging, commits, pushes or real private setup changes.


## Integrated project-building milestone - 2026-10-15

Current substantial milestone is the integrated project builder: durable schema-12 registration, separate permissions, website/HTTP template, bounded model repair and independent source delivery. Regression verification currently totals 275 passed plus one existing Windows symlink-privilege skip (core 42, worker 116, runtime 48, bootstrap 7, runner 6, Rust 16, browser 40). Targeted delivery/registry reruns also pass. Final production Windows acceptance passed; see the evidence below and owning DEVELOPMENT.md. No paid model calls, dependency changes, private user setup changes or Git mutations.


Final Windows acceptance passed: .runtime/desktop-native-1792088789462/review.json. The actual native UI/hidden runner created and durably registered a website/HTTP project, completed a deliberately failed first repair and successful second repair using two deterministic call slots, preserved original source until an independent ask-mode source approval, recovered the prepared delivery after navigation, and delivered the tested app.py/index.html. Installed Edge rendered the delivered page and verified its health API and 375px mobile viewport. Existing chat/planning, specification/export, DPAPI, independent window resize/maximize/fullscreen/minimize, saved/offscreen arrangements, tray/single-instance and worker heartbeat after desktop exit also passed. Fixture processes were cleaned up; zero live paid calls.


## Unattended operations milestone - 2026-10-16

Current milestone: unattended operations and saved-project recovery. Baseline b80fa45 was clean after the owner push. Schema 13 records bounded outcome snapshots, persistent acknowledge-only reads and a project library; build and delivery authorities remain unchanged. Core/API 53 and browser 42 checks pass so far. All 289 regression checks pass plus one existing skip; final native evidence is recorded below and in the canonical development record; no intermediate commit checkpoint is requested.


Final native acceptance passed: .runtime/desktop-native-1792090149082/review.json. The actual Windows app acknowledged and refreshed a persistent website outcome, reopened its registered project/build/delivery from the library, then queued a new failing fixture with the worker stopped. After dashboard exit, a restarted hidden worker completed baseline -> one reserved deterministic model call -> patch -> passing retest/diff. No source:fixture write task was added. The reopened dashboard displayed the completed outcome and acknowledged it. Website/API/mobile rendering, original review/approval/delivery gates, DPAPI, specification/export, independent native window controls/arrangements and tray/single-instance checks also passed. Fixture processes were cleaned up; zero live paid calls. This short restart/exit acceptance is not a full overnight soak or automatic scheduling test.
