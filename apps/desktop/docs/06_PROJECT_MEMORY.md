# Jarvis Windows Desktop — Project Memory

## Maintained specification — current status

Updated 2026-10-16. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented Windows control slice: dedicated React Flow subsystem canvas, project permissions, proposal review, approvals, coding checkpoints/evidence, stored conversations and recent events; Tauri Rust bridge, DPAPI credentials, hidden launcher and tray lifecycle. Release executable builds; native acceptance is recorded in the owning development tracker. Model chat, structured draft plans, setup-readiness and the flexible 3D/tabbed/multi-window workspace are implemented. Reviewed specification-to-scaffold creation and receipt recovery are implemented within a trusted host root. Installer, signed updates, mobile pairing, registry/configuration editing and automatic workflow scheduling remain pending. The legacy UI stays separate.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](../../../docs/ARCHITECTURE.md)
- [Current functionality and implementation boundaries](../../../docs/FUNCTIONALITY.md)
- [Current milestone and verification summary](../../../docs/DEVELOPMENT.md)

## Current verification

Current scheduled-build verification: schema 14; Core/API 57, browser 44 and scheduling/contact checks pass. All 308 distinct regression checks passed plus one existing skip; final native verification passed and is recorded below and in DEVELOPMENT.md; historical milestone counts below remain historical.

## Completed work

Initial requirements, architecture, development/design standards, task plan, API direction, testing and security specifications are retained. Implementation remains at the status stated above.

## Pending work and next milestone

- Rust/MSVC prerequisites and portable Tauri release compilation are proven; installer packaging remains pending
- Native repair, tray and single-instance acceptance complement production-browser tests; see the owning development tracker for the exact release evidence
- Code signing and update distribution ownership are undecided

Follow the component task document and the owning project development tracker. Assign an owner and verify relevant acceptance checks before marking a task complete.

## Maintenance rules

Update this memory for current status, decisions, blockers and next work. Update the other initial documents when their requirements/design/contracts change; keep the detailed implemented database architecture reference aligned with code. Do not generate a new report per task. Git retains historical revisions. The owner stages/commits/pushes manually. Continue authorized development without routine commit checkpoints; do not supply commit messages unless requested. Ask only when a material uncertainty requires owner input.

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


## Scheduled background builds - 2026-10-16

Current milestone is scheduled background builds and recorded runner contact, starting from clean owner-pushed a59e166. Core schema is 14. Thirteen scheduled workflow tests and four contact/migration tests passed; all 44 browser checks passed. All 308 distinct regression checks passed plus one existing skip; final native evidence passed and is recorded below and in DEVELOPMENT.md. No paid model calls, new dependencies, private user settings, staging, commits, pushes or deployments.


Final native acceptance passed: .runtime\desktop-native-1792127556356\review.json. The rebuilt executable embeds /assets/index-2L0Ez0vW.js. Visual review confirms checkbox/consent text alignment in native-scheduled-review.png. Actual worker contact occurred before due with zero steps/no baseline/zero model calls; the first dispatch was 0.921 seconds after the scheduled timestamp. With the dashboard closed, the restarted hidden worker completed baseline/model repair/protected retest/diff using one deterministic call slot and added no source-delivery task. Reopened Jarvis displayed and acknowledged the saved outcome. Existing website/API/mobile rendering, approvals/delivery, specification/export, DPAPI, window controls/arrangements and tray/single-instance checks also passed. All fixture processes were cleaned up; zero live paid calls. This is a short scheduled-start/restart test, not a full overnight soak.


## Coding-agent foundation - 2026-10-16

Additive feature mode is implemented through durable build jobs, proposal context and guarded run plans, with desktop mode selection and fresh consent on mode changes. Selected-snapshot inventory and bounded line-read tools are implemented in the coding worker. Session audit confirms retained chat messages/model turns and separately retained coding execution history; unified conversational coding sessions remain pending. See the root ARCHITECTURE.md/FUNCTIONALITY.md and DEVELOPMENT.md for exact boundaries and verification. Final foundation verification passed: 321 regression checks plus one existing skip and full native acceptance in .runtime/desktop-native-1792135557383/review.json (zero live model calls). Broader repository discovery, arbitrary new paths, governed dependency tooling and three real supervised projects are not yet delivered.

## Reviewed snapshot generations - 2026-10-16

Successful deliveries from durable registrations expose a fresh-generation review with source hashes, protected paths, exact registration digest and native-profile consent. Changing the name clears review/consent. Status lookup recovers an uncertain request, and saved generations reopen through the project library. Registration does not grant resources. Existing tabs/windows/arrangements and source approval remain unchanged. Native acceptance is being verified against a rebuilt production executable.

Final reviewed-generation Windows acceptance passed: .runtime/desktop-native-1792139988614/review.json, frontend /assets/index-Dy57nEvJ.js. New generation registration and dashboard-restart recovery passed with no automatic grants or live model calls. Exact regression counts, executable hash and retained first partial-delivery failure are recorded in root DEVELOPMENT.md.

Latest accepted package: /assets/index-CALGME8x.js; .runtime/desktop-native-1792145403791/review.json passed. Saved-generation permissions are compact/aligned and remain explicit after restart; the final fresh-copy/source check also passed. See root DEVELOPMENT.md for the superseding executable hash, prior failures and exact validation scope.

## Conversation coding-history controls

Added an optional conversation selector to coding-job creation and a user-loaded, read-only history section in conversations. Changing the association clears consent. History is cursor-bounded, escapes goal text and shows existing cycle/model/run/delivery/generation references. It does not automatically retrieve coding records into model context. Native restart acceptance is being extended.

Final conversation-history acceptance passed: schema 15; 331 regression checks plus one existing skip; .runtime/desktop-native-1792146653029/review.json; frontend /assets/index-CIQju6OR.js. Conversation/job/test/delivery/generation provenance recovered through the actual native app after restart. No live provider calls or automatic history injection into model context. Full executable hash and earlier failures are recorded in root DEVELOPMENT.md.

## Opt-in retrieval controls

Coding jobs can choose direct selected files or local retrieval from approved snapshot candidates. Changing mode clears model/automatic/schedule consent. Shared RetrievalReview displays actual selected paths, protected markers, omissions and read/evidence references in both proposal views. Linked history shows per-cycle retrieval tasks. Browser acceptance passed; final packaged acceptance is pending.


Final bounded-retrieval acceptance passed: .runtime/desktop-native-1792148593369/review.json; frontend /assets/index-bVS4q2e9.js. Both repair cycles retained independently verified retrieval evidence, and native history recovered it after restart. See root DEVELOPMENT.md for suite composition (340 distinct passes plus one skip), package hash and remaining limitations. Zero live model calls; no staging, commits or pushes.


Conversation chat/planning now exposes an explicit per-request coding-history checkbox, cleared on send/conversation/mode/provider change. Saved context displays job count, historical-only interpretation and checksum. The history panel itself remains read-only and does not send data. Native acceptance passed with independent SQLite snapshot checks; see root DEVELOPMENT.md for exact scope.


Accepted explicit follow-up context package: .runtime/desktop-native-1792150134459/review.json; /assets/index-DzsQwtyN.js. Scoped history/checksum, actual model request and separate execution boundaries passed with zero live model calls. Runtime regression proves immutable snapshot recovery after Core restart. No staging, commits or pushes.


Supervised execution implementation is in progress: explicit long native limits, exact parent/task renewal, deadline/token-loss cleanup, bounded independent background project requests and observed timing display are implemented. Strict model response boundaries are shared. Final acceptance remains pending; see root DEVELOPMENT.md. Schema stays 15; no staging, commits, pushes or live calls.

## Active reliability work — 2026-10-19

Long native supervision and independent project polling are verified, including a real 610-second execution. Host-bound coding edits, safe validation diagnostics and supervised Gemini/Groq foundation trials are implemented; final packaged acceptance passed at .runtime/desktop-native-1792401762949/review.json. Retained provider-generated revisions failed independent corruption checks; a later Gemini foundation passed both protected and independent checks. The task-board application trial is in progress; no full internal product is accepted. Follow root DEVELOPMENT.md for exact evidence and retained failures; root ARCHITECTURE.md owns current contracts. Preserve initial documents and leave all Git staging/commits/pushes to the owner.

## Supervised application checkpoint — 2026-10-19

The task-board evaluation now passes protected and independent browser acceptance after recorded failures/rejections and an agent-authored correction. Explicit Gemini thinking configuration is frozen into request/job context and reported token counts; private thoughts are excluded. Root DEVELOPMENT.md records exact artifacts, 373 composed regression passes plus one existing skip, and limitations. The latest full GUI package remains Bk9XOfBc. General tools/sessions, reusable E2E product integration and Jarvis identity/orb work remain active. No source delivery or product promotion was claimed.

Latest accepted activity/skill package is _Hd93h4q (.runtime/desktop-native-1792407281506/review.json). Actual visible/minimized motion, pinned skill records, restart/background work and flexible windows passed. Owner-reviewed failed-generation recovery is now implemented and all 58 browser checks plus 17 Rust tests passed; its subsequent production package/native gate is in progress. See root DEVELOPMENT.md for exact artifact identities, retained failures and limitations. Voice and general interactive coding remain open.

The expanded CRgwuSVg package passed .runtime/desktop-native-1792425288344/review.json, including actual failed-generation review/consent, preserved original budgets and independently checked retry results. The recovery screen was visually inspected. New strict TypeScript calibration is currently CLI/worker evidence; no claim that the desktop already offers a Node toolchain editor or completed E2E dashboard.

Latest accepted package: /assets/index-crxWSZFL.js, .runtime/desktop-native-1792430552451/review.json. TypeScript source creation, explicit registration/grants, coding through the hidden runner, persisted Node/compiler hashes and independent output passed alongside previous native flows. Source stayed unchanged before separate delivery. The earlier wrong-plan fixture failure is retained; current-request preflight passed. Browser final 60 passed serially; prior matcher/shared-dist/network failures are recorded in root DEVELOPMENT.md. No actual private host setting was changed.

## Commercial coding direction and accepted import milestone - 2026-10-20

The owner confirmed a commercial standalone coding product with a shared engine used by Jarvis. The existing architecture/requirements/task documents now hold its product boundaries and release sequence; no separate per-work report was created.

Existing-project import is accepted in the rebuilt Windows app at .runtime/desktop-native-1792443916615/review.json. Asset /assets/index-BAIaC2YV.js, executable 5,144,064 bytes, SHA-256 c867957194fa74781959ff2d38bee6b3d739bc39d24fa4724d9d46b3e0cd30c2. Native acceptance verifies a separately reviewed imported TypeScript build and preserved original source/requirements; focused integration also verifies imported Python delivery and continuation across restart without new grants.

Reusable read-only inspection tooling is implemented with authenticated scoped API access, one captured input view, durable task/evidence recovery and explicit new intents after cancellation. Ordinary Chat and the model-driven session planner are not connected to this port yet. Interactive sessions, checkpoint/compaction, documentation-only bootstrap, the full E2E engine/dashboard and standalone commercial packaging remain pending. No complete internal product has been promoted and no hosted customer workload is enabled.

Current composed regression: 461 distinct passes plus one existing Windows privilege skip. Core63; worker223+skip (full223-case suite plus one final new focused case); runtime76; bootstrap7; fixture preflight2; runner9; Rust17; browser64. No new real provider calls; prior calibration total stays22. All36 initial documents remain; staged files and tracked deletions are zero.
