# Jarvis Orchestration Core — Project Memory

## Maintained specification — current status

Updated 2026-10-15. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented and verified: durable core, authenticated local API, selected-file worker, owner-enabled native Windows tests, repair workflows and bounded Gemini/Groq repair proposals with versioned skill context and controller review. Native desktop control, flexible 3D/tabbed/multi-window workspace, model-backed conversation, structured draft planning and setup-readiness guidance are implemented. A reviewed owner-operated Python function scaffold feeds existing model repair jobs. General autonomous building, a scaffold/configuration editor, installer/update delivery and mobile pairing remain pending.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](ARCHITECTURE.md)
- [Current functionality and implementation boundaries](FUNCTIONALITY.md)
- [Current milestone and verification summary](DEVELOPMENT.md)

## Current verification

Current scaffold-phase verification: 203 Python tests passed and one existing Windows symlink-privilege test skipped: core/API 42, worker/scaffold/jobs 101 passed plus one skip, model runtime 48, desktop bootstrap 6 and hidden runner 6. The scaffold suite adds 18 checks, including native creation, model/test repair and separately approved delivery. The unchanged desktop retains the previous phase's 16 Rust and 34 browser checks and native release evidence; those GUI suites were not rerun for this host-only change. No live paid calls or dependency/schema changes were required. SQLite remains version 11. The existing HTTPX/Starlette TestClient deprecation remains known.

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
