# Jarvis Orchestration Core — Project Memory

## Maintained specification — current status

Updated 2026-10-16. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented and verified: durable core, authenticated local API, selected-file worker, owner-enabled native Windows tests, repair workflows and bounded Gemini/Groq repair proposals with versioned skill context and controller review. Native desktop control, flexible 3D/tabbed/multi-window workspace, model-backed conversation, structured draft planning and setup-readiness guidance are implemented. Reviewed function and website/HTTP templates connect desktop creation, durable registration, explicit grants, bounded repair jobs and separate source delivery. The Activity operations center adds durable outcomes, acknowledgement and saved project recovery; final native acceptance is recorded in DEVELOPMENT.md. General autonomous building, a registry/configuration editor, installer/update delivery and mobile pairing remain pending.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](ARCHITECTURE.md)
- [Current functionality and implementation boundaries](FUNCTIONALITY.md)
- [Current milestone and verification summary](DEVELOPMENT.md)

## Current verification

Current operations-center verification: schema 13, 53 Core/API and 42 browser checks passed, with all 289 regression checks passing (one existing symlink-privilege skip); final Windows acceptance passed with evidence below. The final complete totals and executable evidence in DEVELOPMENT.md supersede historical milestone counts below.

## Completed work

The durable core/API, file worker and trusted native repair workflow milestones are implemented. Controller plans and native account access remain explicit.

## Pending work and next milestone

- Mobile OS and companion-app approach are unconfirmed
- Production-release policies and per-project budgets require configuration
- Existing memory data needs an explicit non-destructive migration/export plan

Next: online-model planning and patch generation, structured skills/context and the new Windows interface. Custom/employee grants, curated teaching memory, mobile pairing and hosted operation remain pending.

## Maintenance rules

Update this memory for current status, decisions, blockers and next work. Update the other initial documents when their requirements/design/contracts change; keep the detailed implemented database architecture reference aligned with code. Do not generate a new report per task. Git retains historical revisions. The owner stages/commits/pushes manually; the assistant reports a substantial verified milestone and waits for confirmation before proceeding.

## Current repair milestone memory

Completed 2026-10-14: bounded model proposals, skill context, schema 6, controller review and tested native handoff. Live Gemini 3.5 Flash Lite and Groq Qwen 3.8 27B repairs reached ready_for_review with original source intact. Earlier Gemini 2.5 calls failed HTTP 404; no silent fallback/retry. Detailed counts, evidence and limitations are in the owning development tracker. Pending: Windows control UI, general builder, teaching memory and scheduling. No staging, commits or pushes performed by the assistant.

## Windows control milestone memory

The first control slice now has source and a release executable: dedicated subsystem canvas, permission review, proposal/approval/run/evidence screens, stored history and recent events. Controller/worker tokens are DPAPI protected and retained by the native host. The hidden Python launcher is ownership-aware; closing hides to tray, while explicit Exit ends the application. Existing nine documents are retained and updated. Exact verification/artifact details and remaining native checks live in the owning development tracker; no staging, commits or pushes were performed by the assistant.

## Conversation and draft planning

Current conversation/planning status: schema 7, deterministic tests and live Gemini chat/Groq draft-plan checks implemented. A Groq schema-prompt issue was caught by the live probe and corrected; failed requests remain terminal. Exact native release proof and full counts live in the owning development tracker. No staging, commits or pushes. Next: trusted configuration editing and explicit plan-to-build handoff.

## Flexible 3D workspace

The flexible workspace phase adds a 3D core, tab shell and independent native panels. Tab metadata is automatically restored; visited tab drafts survive switching/minimization within the session but are not persisted across application restart or tab closure. Saved native window arrangements are restored explicitly from Arrange. The main window closes to tray; child windows close independently. Detailed verification and final release evidence belong to the owning development tracker. No legacy assistant code or user data was removed.


## Versioned specification workflow - 2026-10-15

Current database version is 8. Specification publication and approval, document review and optional approved-specification repair context are implemented. Four document types are rendered deterministically from completed planning output; repository documents are not overwritten. New draft versions preserve previous approval until a newer version is approved. Approval supersedes pending older handoffs, while already accepted coding runs keep their existing explicit cancellation and task approvals.


## Specification revision and delivery - 2026-10-15

Current schema is 9. Specification document revisions and native file export are implemented. Previous snapshots and approvals are preserved; saving a revision creates a new draft. Approving it supersedes older approval. Documents are delivered under Documents/Skyra/Jarvis/exports/<project>/v<version>-<specification>, unless the trusted host configures an export root. No repository documentation or original source is overwritten.


## Reviewed new-file coding - 2026-10-15

New-file coding support is implemented with pre-existing protected tests and owner-declared paths. Snapshot files, not original project files, receive generated content. Manifest v2 supports absence provenance and v1 remains readable. Prior revision/export work is still present and was uncommitted at phase start; the user explicitly authorized continuing. No staging, commits or pushes performed.


## Unattended assignments requirement - 2026-10-15

The owner clarified that Jarvis must work continuously on an assignment while the owner sleeps. Treat unattended goal execution as a core product requirement. Current durable coding steps are manually advanced; no unattended runner exists yet. The source-delivery phase currently has draft backend/UI changes and tested-input hash metadata. Its next test/edit command was not executed because automatic approval review could not complete due to a usage limit. Source-delivery tests, target-reconfiguration binding checks, UI verification and final native acceptance remain pending; do not claim this phase complete or apply it to real sources. Previous 170-test evidence belongs to the last completed new-file phase.


## Shared logging and E2E roadmap decision - 2026-10-15

The owner requested two additional reusable projects: ELK logging for finding runtime errors and E2E suites with visible failures for development and production. Recorded proposed names skyra-observability and skyra-e2e-suite, with full planning checklists in 05_PROJECT_TASKS.md. Existing skyra-quality is specification-only and already owns quality orchestration; integrate test execution/evidence with it rather than duplicate its dashboard/gates. Existing skyra-incident-service remains the incident coordinator. No new folder/repository, installation, product integration or deployment was performed. ERP, Platform, QR and company website remain untouched. Source-delivery draft verification remains pending as previously recorded.

### Subsequent project documentation - 2026-10-15

The owner explicitly selected new skyra-observability and skyra-e2e-suite projects. Both folders now contain README indexes and six initial documents: requirements, architecture including proposed metadata tables, development rules, design system, phased tasks and project memory. This supersedes the earlier no-folder state above. No runtime implementation, Git initialization, dependency installation, integration or deployment was performed. Quality and Incident plans remain preserved; their responsibilities are referenced rather than duplicated. Jarvis source-delivery verification remains pending independently. No staging, commits or pushes performed.

## Reviewed source delivery completed - 2026-10-15

The earlier draft verification blocker is superseded. Reviewed source delivery is implemented and verified, including target-path binding, tested-input/profile provenance, separate source approval, idempotent preparation, conflict refusal, backups and partial-write journals. Native acceptance delivered a tested new file only to a generated fixture source; no real product source target was used. Current SQLite remains schema 9. Exact evidence and limitations are in DEVELOPMENT.md. The unattended runner remains unimplemented and is the next development priority after owner review/commit. No staging, commits or pushes performed.

## Bounded unattended runner completed - 2026-10-15

The first runner is now implemented: explicit owner assignments advance accepted coding runs through existing protected-test/write/diff checkpoints. SQLite schema 10 stores assignments and attempts. Hidden per-user worker transport uses project-scoped DPAPI credentials and a separate host-enabled API; the launcher can give Core ownership to a background supervisor independently of the dashboard. Pause/resume/cancel, graceful stop, quiet approval waits, step/deadline bounds and conservative interrupted-dispatch accounting are implemented. Summary/evidence persist for later inspection.

Native acceptance used the actual runner process, three coding approvals and a separate source-delivery approval, then confirmed a new heartbeat after terminating the desktop. No paid model calls or real product source writes occurred. This is accepted-run progression, not a general website builder or iterative model debugger. Scheduled start times, provider spend budgets, morning notifications, remote execution and a full overnight soak remain pending. Source-delivery checkpoint c4fec01 was present during development; this task did not stage, commit or push. The owner requested larger continuous milestones and commit messages only for substantial verified changes.

## Governed model repair jobs completed - 2026-10-15

Schema 11 adds build_jobs, build_cycles and build_attempts while retaining existing assignments/history. Jobs now start from an owner repair goal, selected snapshot/profile/provider/context and explicit model-sharing/call consent. The initial protected baseline gates generation; passing tests consume zero calls. Verified failed retests can initiate another bounded repair cycle using updated files and retained evidence. Exact proposal review is default; automatic acceptance requires explicit per-job opt-in and current full policy. Call slots reserve before generation and unknown outcomes never replay automatically. Ready responses can recover without another call.

The hidden runner shares project exclusion/recovery across accepted-run and model-job lanes. Build jobs provides responsive configuration, call/cycle/step/time budgets, context/consent controls, exact response review and progress summaries. Source delivery remains separate. Native acceptance completed a selected missing module through four task approvals, an exact proposal review and a separate source-write approval, then verified the worker outlived the dashboard. Deterministic providers only; no live paid call or real product source write occurred. Full cycle history is available through job detail API. General greenfield scaffolding, protected-test authoring, currency budgets, notifications and overnight soak remain pending. Initial documents were preserved and updated in place. No staging, commits or pushes performed.

## Approved-specification scaffold foundation - 2026-10-15

Completed the owner-operated Python JSON-function scaffold: approved specification verification, bounded owner examples, exact complete-file/destination/profile/interpreter review, nine-document preservation/default provenance and exclusive Windows source/snapshot publication. Protected tests fail on the initial stub. Existing model jobs implement the snapshot, pass protected retests and stop for review; a distinct source approval delivers changes. Registration drafts disable execution and do not grant resources or invoke a provider.

All five Python suites passed: 203 checks plus one existing symlink privilege skip. Eighteen scaffold checks cover native end-to-end handoff, owner commands, path/junction guards and interruption/reconciliation behavior. No paid model requests, dependency updates, schema changes, private setup changes, staging, commits or pushes. Existing GUI release evidence is unchanged. Next: desktop scaffold/setup experience, website/service templates and broader independent acceptance/quality validation. Source documentation remains in the initial documents and owning architecture/functionality/development files.

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
