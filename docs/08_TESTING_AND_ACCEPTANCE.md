# Jarvis Orchestration Core — Testing and Acceptance

## Maintained specification — current status

Updated 2026-10-16. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented and verified: durable core, authenticated local API, selected-file worker, owner-enabled native Windows tests, repair workflows and bounded Gemini/Groq repair proposals with versioned skill context and controller review. Native desktop control, flexible 3D/tabbed/multi-window workspace, model-backed conversation, structured draft planning and setup-readiness guidance are implemented. Reviewed function and website/HTTP templates connect desktop creation, durable registration, explicit grants, bounded repair jobs and separate source delivery. The Activity operations center adds durable outcomes, acknowledgement, saved project recovery and recorded runner contact. Build jobs support one-time scheduled starts with input/specification admission guards; final native acceptance is recorded in DEVELOPMENT.md. General autonomous building, a registry/configuration editor, installer/update delivery and mobile pairing remain pending.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](ARCHITECTURE.md)
- [Current functionality and implementation boundaries](FUNCTIONALITY.md)
- [Current milestone and verification summary](DEVELOPMENT.md)

Prepared: 2026-10-14. Requirement/design baseline. Use the maintained current-status section above to distinguish implemented work from planned work.

## Project acceptance matrix

| ID | Required outcome | Evidence status |
|---|---|---|
| AC-01 | Two simultaneous conversations cannot read each other's private context | Not executed |
| AC-02 | Restart while waiting for approval preserves the pending action without executing it | Not executed |
| AC-03 | A changed proposed action invalidates an earlier approval | Not executed |
| AC-04 | An interrupted external operation is reconciled before a retry | Not executed |
| AC-05 | Plan mode does not begin implementation; build mode binds to a reviewed specification version | Not executed |
| AC-06 | A taught fact can be inspected, revised and forgotten, including its derived search entries | Not executed |
| AC-07 | A disconnected PC is reported unavailable on mobile; jobs are not falsely marked running | Not executed |
| AC-08 | Stopping a workflow cancels descendants and records workers that did not acknowledge | Not executed |

## Requirement traceability

Each requirement must receive one or more concrete test IDs. The matrix above captures critical scenarios but does not imply exhaustive feature coverage.

| Requirement | Behavior to verify | Test mapping |
|---|---|---|
| FR-01 | Isolated projects, conversations, branches and versioned project specifications | Unassigned; required before implementation completion |
| FR-02 | Plan-only workflow generating the appropriate project documents before an explicit build instruction | Unassigned; required before implementation completion |
| FR-03 | Persistent task graphs with delegation, checkpoints, cancellation, restart reconciliation and acceptance evidence | Unassigned; required before implementation completion |
| FR-04 | Configurable read-only, ask, selected-actions, scoped full-access and custom permission policies | Unassigned; required before implementation completion |
| FR-05 | Memory Centre for explicit teachings, provenance, revisions, conflict handling and forgetting | Unassigned; required before implementation completion |
| FR-06 | Skills and capability discovery, online model routing and MCP client integration | Unassigned; required before implementation completion |
| FR-07 | Mobile commands and approvals through Telegram first; dedicated mobile interface after platform decision | Unassigned; required before implementation completion |
| FR-08 | Technical and business incident playbooks; known local rules work without model connectivity | Unassigned; required before implementation completion |

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

## Bounded repair acceptance evidence

The runtime suite checks local schema/patch constraints, protected tests, stale hashes/context, policy revocation, model error sanitization, request idempotency, interrupted restart without replay, concurrent single dispatch, late response suppression, atomic handoff rollback, migration preserving conversations, HTTP roles and ask-mode approval preservation. Two live providers produced fixture patches that passed real Windows baseline/repair/retest/diff gates. See the development tracker for exact counts and ignored JSON evidence. These small fixtures do not establish general coding quality, production isolation or superiority to other agents.

## Desktop acceptance evidence

TypeScript and production assets build. Eleven Playwright cases cover disconnected browser isolation, labelled preview/canvas truth, patch review, exact-action rejection, text-safe conversation saving, run cancellation, explicit context selection, modal focus, project dialog routing, narrow layout and version-aware policy controls. The cancellation case verifies late responses cannot revive a cancelled run while a request is pending. Core checks cover dashboard owner/role boundaries and stale policy versions. DPAPI/launcher tests cover protected state, refusal to overwrite, hidden child flags, ownership and redirect rejection. Native Rust routing checks reject arbitrary URL/shell actions, invalid IDs and token-field injection. Record the real Windows release flow separately in the owning development tracker; fixture-only tests do not prove native integration or general model quality.

## Conversation and draft planning

Acceptance includes provider selection, stored notes, safe text rendering, chat replies/usage, structured plan sections, failure without replay, missing providers, active interruption and late-output suppression. Runtime tests cover migration from schema 6, byte-bounded contiguous history with omission counts, Unicode size rejection, immutable instruction hashes, concurrent single dispatch, restart uncertainty and atomic assistant-message/state writes. Native acceptance uses deterministic providers only; separate explicitly authorized live probes use fictional prompts.

## Flexible 3D workspace

Workspace acceptance covers keyboard/pointer-accessible 3D rotation, reduced-motion orbit, tab draft preservation/minimization/reordering/reload, corrupt preference recovery, focus mode, separate core/map views, card popouts and small-window overflow. Rust checks cover fixed panel targets, project/label validation, duplicate/versioned arrangement rejection and missing/negative monitor coordinates. Native acceptance must verify actual independent WebView windows, size/minimize/maximize/fullscreen, saved arrangement recreation and offscreen recovery in addition to the existing repair/chat/plan/tray flow.

Final native acceptance uses a fresh fixture-specific WebView2 user-data folder as well as fixture credentials/database, and verifies that profile isolation before reporting success. Connection badges may be hidden by responsive styles; actual project selection and stored history verify connectivity in narrow child windows.


## Versioned specification workflow - 2026-10-15

Specification checks cover exact-checksum approval, idempotent publication, conflicting versions, owner and project boundaries, controller-only API, supersession, stale repair rejection and preservation of completed plans through migration 7 to 8. Browser acceptance covers plan publication, document inspection, approval and repair selection. The native acceptance harness exercises real Core-backed specification publication and approval in an isolated fixture; final evidence is recorded in DEVELOPMENT.md.


## Specification revision and delivery - 2026-10-15

Revision checks cover immutable parent lineage, request deduplication, stale-version/checksum conflicts, owner boundaries, mandatory filenames/content/byte bounds and migration 8 to 9. Export checks cover approved-only API access, canonical SHA-256, literal file bytes, idempotent verification and refusal to overwrite tampered files. Browser acceptance covers added architecture documents, independent approval, conflicting-save draft retention and modal focus restoration. Final suite/native evidence belongs in DEVELOPMENT.md.


## Reviewed new-file coding - 2026-10-15

Checks cover declared-only creation, path/case/prefix conflicts, existing-file refusal, exact write approval, durable reload/diff, missing static verification, absent protected-test rejection, model unselected-target refusal, stale-absence refusal, approved-specification supersession and retry deduplication after creation. Runtime acceptance executes a real missing-module failing baseline and passing protected retest. Native fixture now exercises a reviewed new module through three approvals and verifies the original source has no generated file. Final counts/evidence are recorded in DEVELOPMENT.md.

## Reviewed source delivery - 2026-10-15

Generated fixtures verify real failing-baseline/repair/passing-retest evidence before delivery. Regressions cover baseline conflicts, changed snapshots/test profiles, revoked resource grants, reconfigured physical targets, overlapping state refusal, request deduplication, separate ask-mode approval, controller-versus-worker API roles, failed replacements and partial multi-file effects without replay. Browser scenarios require manifest review before preparation and reject unregistered source selection. Rust route checks reserve execution for the worker credential. Native acceptance extends the existing new-file flow with a separate source write approval and evidence inspection, then checks the generated source gained the tested file. All source writes target generated fixtures, not developer projects. Current counts and actual native outcome belong in DEVELOPMENT.md.

## Model-backed repair-job acceptance

Generated native fixtures exercise baseline -> deterministic model -> reviewed patch -> protected retest -> final diff, including a first failed patch followed by a second successful repair using updated source hashes and failing output. Verify passing baseline performs zero model calls; call/cycle/step limits stop dispatch; creation requires explicit consent; full policy plus per-job opt-in is necessary for automatic acceptance; ask mode requires exact response/context review and separate action approvals.

Failure checks cover stale test inputs, provider/profile changes, permission downgrade, rejected baseline approval, interrupted proposal, failed provider request, cancellation during generation and unknown billable dispatch after restart. Calls stay charged and late output cannot revive cancelled work. Recovery of a durably ready response must not reserve or issue another call. API tests isolate worker execution from controller creation/review, and retained metadata stays readable without runtime configuration. Migration 10 to 11 preserves existing assignments; prior migration fixtures remove the new tables when simulating older versions.

Browser tests cover consent gating, host-disabled execution, exact proposal display and controls. Native acceptance queues a fresh repair job, approves its initial baseline, generates through the acceptance-only provider, explicitly reviews the exact generated new file, completes the protected workflow and performs separately approved source delivery. Its hidden runner remains active after desktop exit. These fixtures make zero live paid calls and do not certify arbitrary greenfield builds or production security. Final counts and actual native evidence belong in DEVELOPMENT.md.

## Unattended assignments

Assignment checks cover automatic protected repair completion, approval waits without budget/attempt churn, pause/resume/cancel across restart, rejected approval, host disablement, resource revocation, deadline and step limits, exclusive project dispatch, request deduplication and conservative interrupted-claim accounting. Schema tests preserve history/runs while migrating version 9 to 10; older version simulation fixtures remove the new tables before rerunning the full migration chain.

Runner checks cover user-bound worker credential loading, fixed loopback transport, redirect refusal, safe error status, OS-owned profile locking and stop markers. Launcher checks distinguish a supervisor-owned Core from dashboard ownership. Browser tests exercise assignment controls and disabled-host behavior. Native acceptance is extended to queue an assignment and use the actual hidden worker process for every coding advance, with explicit UI approvals, then verify the worker heartbeat continues after the desktop process exits. Final actual outcomes/counts belong in DEVELOPMENT.md; these scenarios do not establish a full overnight soak or arbitrary autonomous project building.

## New-project scaffold acceptance - 2026-10-15

Fixture checks cover owner/approval/document integrity, deterministic side-effect-free preview, contract limits/depth/finite JSON, inert injection-like text, boolean/number comparison, preservation/default provenance, path/device/executable and Windows junction refusal, changed-interpreter invalidation, exact review, existing-directory refusal, publication races and interrupted staging/audit failure. Owner-command checks cover successful review/create, disabled execution draft, malformed/missing input and error output without traceback.

Real native integration starts with an approved structured plan, creates a fresh failing scaffold, then runs a deterministic provider through existing Build jobs to protected-test success and ready_for_review. Source remains the stub until a distinct source-write approval delivers the implementation. Protected acceptance files remain unchanged. No live paid model calls, new browser UI, deployment or security certification are implied. See DEVELOPMENT.md for exact current results.

## Desktop scaffold verification - 2026-10-15

Added controller-role/ownership, disabled-host setup, extra renderer path/executable refusal, fixed host binding, exact create hash, approval downgrade, receipt recovery/audit gap and malformed receipt tests. Launcher coverage verifies default null root and hidden forwarding from trusted configuration. Browser cases cover explicit review consent, edited-plan invalidation, uncertain outcomes without retry, receipt lookup, disabled setup, malformed JSON and narrow layout. The first full browser run had one selector error: a named role=status region was queried as region; corrected the test to query its actual role and the rerun passed.

Native acceptance extends the existing isolated real Windows app harness with approved-specification file review, disabled-until-consent creation, receipt lookup, on-disk nine-document preservation and disabled execution draft. Deterministic providers only; no private user setting, live paid call or real product source is used. Exact executable and native artifacts are recorded in DEVELOPMENT.md after final acceptance.

Native screenshot review caught an inherited 200px fieldset height that functional clicks could still scroll through. The scoped style now removes that nested clipping area. Browser and native geometry assertions cover both form height and horizontal width; all four scaffold browser cases reran successfully after the fix.


## Integrated project-building milestone - 2026-10-15

Regression evidence: 275 distinct passing checks plus one existing Windows symlink-privilege skip; deterministic providers only. New integration verifies schema-11 migration, owner/role scope, exact/idempotent registration, restart restore, tampered metadata isolation, weaker-profile refusal, protected server writes, changed interpreter before generation, invalid HTTP contracts, actual GET/POST acceptance, failed first model repair, successful second repair and independent ask-mode delivery. Browser tests exercise explicit registration/permission/model consents and host-disabled refusal. Final Windows acceptance and rendered delivered-site evidence belong in the canonical DEVELOPMENT.md.


## Unattended operations milestone - 2026-10-16

Verify immutable snapshots survive later job changes/restart; repeated identical waits remain quiet; new distinct outcomes become unread; acknowledgements cannot change jobs, tasks, policy or calls; rollback removes state/event/notice together; 50-item keyset pages do not overlap; migration 12 retains history/backfills current attention outcomes. Verify assignment evidence references without stdout. Browser tests cover acknowledgement reload, disabled host/deadline layout and saved-project reopening. Native acceptance must prove actual queued work after desktop exit, not just a live heartbeat.


## Scheduled background builds - 2026-10-16

Verify zero tasks/attempts/calls before due, exact persisted next_due/deadline, restart completion, missed-window failure, edited inputs/specification blocking, cancellation, pause/resume not-before and idempotent create recovery. Confirm pending baseline approval keeps input binding while admitted approval waits may extend beyond start window within runtime deadline. Contact tests distinguish idle/busy/stale/restart, cross-owner access and older-completion races; API tests separate controller schedule authority from worker ticks. Browser date fixtures normalize zero seconds to Chromium canonical datetime-local syntax. Native must prove actual contact before due plus zero early baseline/steps/calls, then completion after due without source delivery.


## Coding-agent graduation gates - 2026-10-16 (planned)

Follow the [active development plan](05_PROJECT_TASKS.md#active-development-plan---coding-agent-and-jarvis-identity---2026-10-16). Supervise the agent through the task tracker, E2E engine and Quality dashboard. Give bounded tasks with independent criteria before generation; record agent-authored vs supervising-developer changes. Inspect architecture, functionality, security, duplicated logic, dependency choices and visible output. Keep failure evidence even if a later retry passes.

Session matrix: normal reopen; process crash before dispatch/after effect/before recording result; duplicate request; expired/revoked approval; provider timeout and 429; context compaction; concurrent windows; switching projects; stale source; cancellation; budget exhaustion. Verify no lost committed messages, duplicate effects, silent paid/provider fallback or leaked context. Use deterministic failures for regression and separately labelled controlled online runs for actual model performance. Test restart invariants in storage and the real Windows application.

Do not graduate based only on agent-authored tests, self-review or another model's agreement. Compare identical tasks/configurations across model candidates and record task success, acceptance failures, elapsed time, usage, retries and manual interventions. Require architecture/code review and independent tests for all three project evaluations. A visual baseline is owner-reviewed; the agent cannot silently approve its own screenshot as expected output.


### Feature-mode and inspection regression coverage - 2026-10-16

Verify passing baseline -> model-generated multi-file/new-file implementation -> protected passing retest -> reviewable diff, including restart between baseline and generation. Preserve repair-mode no-call behaviour, request identity, scheduled not-before and unknown-mode rejection. Contradictory execution evidence or unconfirmed cleanup blocks generation/advancement. Inspect selected inventory, absent creation paths, line numbers/UTF-8/line endings, hashes, continuation, oversized lines, unselected paths and revoked grants. Native acceptance independently invokes the generated fixture function and verifies persisted feature mode, one call and baseline exit zero; fixtures are not a real-model quality benchmark.

The native timeout regression fixture now proves grandchild startup, uses a ten-second test profile and releases a survivor write only after cleanup. This removes the one-second cold-start assumption while retaining actual timeout, output, cleanup and no-surviving-child assertions. Production executor timeouts are unchanged.

## Snapshot generation acceptance

Independent worker integration must complete two tested deliveries from separate generations with a registry restart between them and preserve the first diff. Verify unchanged grants, exact/idempotent registration, absent-target promotion, source drift, changed historical evidence, failed-copy invalidation, protected files and interpreter binding. HTTP checks reject agent/worker calls, missing consent, wrong digest and arbitrary filesystem inputs. Browser checks require consent, invalidate it after edited names and recover saved status. Native checks exercise the actual bridge, inspect SQLite and snapshot bytes independently, and reopen the generation after dashboard restart. Deterministic task fixtures do not establish real online-model performance.


## Bounded retrieval acceptance

Verify large candidate scopes remain within file/byte limits and retain protected files; reject unsafe, duplicate or unselected paths and required-only context. A completed read must recover without duplicate dispatch. Mutating even an omitted candidate blocks provider use; a provider patch to an omitted file is rejected without changing workspace bytes. Passing repair baselines and exhausted step budgets dispatch neither retrieval nor models. Failed retests must preserve old context references and create a fresh read for the next cycle. Browser checks require renewed consent on mode changes and inspect selected/omitted evidence. Final native acceptance independently checks per-cycle task/evidence/proposal bindings and reopened history. Accepted evidence: .runtime/desktop-native-1792148593369/review.json. These fixtures do not measure online-model coding quality.


## Explicit follow-up history context acceptance

Verify default absence, strict boolean input, controller-only/owned conversation scope, newest-three whole-job selection, goal excerpt/checksum markers and retained pagination. Same request retries must preserve the original snapshot after new jobs or restart; toggled inclusion conflicts. Snapshot tampering blocks provider dispatch. No tasks/permissions are created. Browser checks cover unchecked defaults, mode reset, post-send reset and saved-context inspection. Packaged acceptance must include actual two-cycle job history and independently verify the persisted checksum/references. Deterministic fixtures establish behaviour only.

## Host-bound edits and supervised online calibration — 2026-10-19

Verify legacy digest compatibility, strict protocol values, three-field provider edits, host-bound immutable hashes, absent creation, conservative LF/CRLF handling, mixed-line exactness, instruction/schema freshness and safe diagnostic persistence. Full Windows acceptance independently checks persisted protocol and canonical review hashes; current evidence is .runtime/desktop-native-1792401762949/review.json. Long supervision separately passed a real 610.335-second single execution beyond the former lease boundary.

Real-provider evaluation must preserve failures, count reserved calls including HTTP failures, stop proposed code for inspection, retain protected tests and run independent negative checks. A passed protected retest is not feature completeness. The Gemini v5 task-store foundation passed nine protected tests plus independently hash-bound corrupted-record/root-container checks. Follow DEVELOPMENT.md for failed predecessors and exact artifacts. The next task-board trial reuses that generated persistence foundation and protected host transport, tests actual loopback HTTP/parallel writes, then requires independent browser checks before product acceptance. No client project or production deployment is used.
