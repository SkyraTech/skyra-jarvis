# Jarvis Orchestration Core — Testing and Acceptance

## Maintained specification — current status

Updated 2026-10-15. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented and verified: durable core, authenticated local API, selected-file worker, owner-enabled native Windows tests, repair workflows and bounded Gemini/Groq repair proposals with versioned skill context and controller review. Native desktop control, flexible 3D/tabbed/multi-window workspace, model-backed conversation, structured draft planning and setup-readiness guidance are implemented. General autonomous building, a full configuration editor, installer/update delivery and mobile pairing remain pending.

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

## Unattended assignments

Assignment checks cover automatic protected repair completion, approval waits without budget/attempt churn, pause/resume/cancel across restart, rejected approval, host disablement, resource revocation, deadline and step limits, exclusive project dispatch, request deduplication and conservative interrupted-claim accounting. Schema tests preserve history/runs while migrating version 9 to 10; older version simulation fixtures remove the new tables before rerunning the full migration chain.

Runner checks cover user-bound worker credential loading, fixed loopback transport, redirect refusal, safe error status, OS-owned profile locking and stop markers. Launcher checks distinguish a supervisor-owned Core from dashboard ownership. Browser tests exercise assignment controls and disabled-host behavior. Native acceptance is extended to queue an assignment and use the actual hidden worker process for every coding advance, with explicit UI approvals, then verify the worker heartbeat continues after the desktop process exits. Final actual outcomes/counts belong in DEVELOPMENT.md; these scenarios do not establish a full overnight soak or arbitrary autonomous project building.
