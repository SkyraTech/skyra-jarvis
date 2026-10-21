# Jarvis Orchestration Core — Design System

## Maintained specification — current status

Updated 2026-10-16. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented and verified: durable core, authenticated local API, selected-file worker, owner-enabled native Windows tests, repair workflows and bounded Gemini/Groq repair proposals with versioned skill context and controller review. Native desktop control, flexible 3D/tabbed/multi-window workspace, model-backed conversation, structured draft planning and setup-readiness guidance are implemented. Reviewed function and website/HTTP templates connect desktop creation, durable registration, explicit grants, bounded repair jobs and separate source delivery. The Activity operations center adds durable outcomes, acknowledgement, saved project recovery and recorded runner contact. Build jobs support one-time scheduled starts with input/specification admission guards; final native acceptance is recorded in DEVELOPMENT.md. General autonomous building, a registry/configuration editor, installer/update delivery and mobile pairing remain pending.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](ARCHITECTURE.md)
- [Current functionality and implementation boundaries](FUNCTIONALITY.md)
- [Current milestone and verification summary](DEVELOPMENT.md)

Prepared: 2026-10-14. Requirement/design baseline. Use the maintained current-status section above to distinguish implemented work from planned work.

## Principles

Show capability, readiness, progress and evidence truthfully. Make permission boundaries visible. Prefer readable dense information over decorative animation. Preserve drafts and selection through reconnects. Never present a disconnected service as available.

### Jarvis visual foundation

Dedicated Jarvis design; do not import Skyra Platform UI. Proposed tokens: background #0B1220, surface #111C2F, raised surface #1B2940, primary text #F3F6FC, secondary text #B9C5D8, accent #75B8FF, success #72D6A0, warning #FFD166, error #FF8F9A. Verify contrast in actual component states before adoption.

Use Segoe UI/system sans for interface and Cascadia Code/system monospace for code. Type sizes: 12 metadata, 14 controls, 16 body, 20 section, 28 page title. Spacing scale: 4/8/12/16/24/32/48 px; 8 px control radius and 12 px panels. Focus rings remain visible; never encode status using color alone.

Primary shell: navigation rail, central subsystem/workflow canvas, inspector, conversation panel and approval inbox. A node shows name, available capability, readiness, current task and permission scope. Edges describe actual dependencies, not decorative activity. Provide zoom, fit, keyboard selection, searchable list alternative, minimap and reduced motion. Inspector exposes evidence/artifacts without exposing credentials.

Approval cards show exact action, target, account, cost/risk when known, expiry and scope. Changed actions require a fresh decision. Destructive decisions cannot be the default focused action. Mobile layouts prioritize approvals, run status and cancellation over editing large graphs.

## Required interaction states

Provide loading, empty, partial, stale/offline, permission-denied, approval-required, successful and failed states wherever an operation is exposed. Cancellation requested and cancellation confirmed are distinct. An external operation with uncertain outcome remains unresolved until reconciled. Error messages name the next safe step and a support correlation ID.

## Validation

Test keyboard-only navigation, focus restoration after dialogs, text scaling, contrast and reduced motion. Visual snapshots complement behavior tests. Backend-only projects validate presentation payloads through consumer fixtures; they do not need invented UI screenshots. Final visual approval and branding remain pending implementation review.

## Proposal review requirements — UI still pending

Display source selection, protected tests, provider/model, skill versions, patch diff, usage and context checksum. Distinguish planned/generating/ready/accepted/failed/interrupted from coding-run states. Separate Generate, Accept and task approval controls. Explain uncertain generation and native account access. A successful fixture is not a production-ready label. No desktop visuals were implemented in this milestone.

## Implemented visual foundation

Current dedicated palette: background #0B101A, surface #111925, border #263143, text #EEF3FC, muted #99A8BE, accent #96B8FF and mint #7DD3B6. Segoe UI/system sans and Cascadia Code/monospace; 4/8/12/16/24/32 spacing and 7–10 px control/panel radii. Shell uses company rail, workspace navigation, capability canvas and inspector; detailed screens use list/inspector panels. Nodes distinguish connected, configured, unavailable and planned; configured does not claim live provider health. A list alternative exposes subsystem details. Modals trap/restore focus and respect Escape; the narrow Windows layout keeps the inspector accessible. Full accessibility/branding approval remains a separate release gate.

## Conversation and draft planning

Conversations expose Store note only, Ask Jarvis and Create project plan modes, with explicit online-model selection and no default paid provider. Show request state, usage, safe errors, inspectable context/omissions and interruption independently of pending generation. Render plans with a draft label, requirements, deliverables, phases, acceptance criteria, risks and questions. Setup shows a read-only readiness checklist; it does not silently provision services.

## Flexible 3D workspace

Jarvis has a cyan/blue 3D orbital core on the overview and a separate Core view; it supports pointer/keyboard rotation, optional orbit animation and reduced-motion preferences. Preserve the system map as a separate workspace view. Persistent top tabs and Arrange controls stay visible while content scrolls within the available viewport. Focus layout hides navigation; dedicated native windows retain standard Windows title bars and snap/resize behavior. Maintain readable cards and no horizontal page overflow at tested small-window sizes.


## Versioned specification workflow - 2026-10-15

Conversations now includes a Project specifications section. Display version, draft/approved/superseded status, full checksum and expandable plain-text Markdown documents. Save and approve are distinct explicit actions. The repair dialog offers an optional approved-specification selection; it still requires a goal, provider, workspace, files and test profile.


## Specification revision and delivery - 2026-10-15

The specification review card adds Edit as new revision and Export approved documents. The editor is a focus-contained modal with a document selector, plain-text Markdown textarea and optional standard-document creation/removal. Conflicts preserve edits and show the error inside the editor. Approval and export remain explicit separate actions.


## Reviewed new-file coding - 2026-10-15

Proposal review distinguishes New file target from selected existing source and protected tests. Show New file (must not exist) plus the complete proposed content. The workspace selection dialog labels explicitly allowed creation targets; normal task approvals remain visible in Approvals.

## Reviewed source delivery - 2026-10-15

Completed coding runs show a distinct Deliver to project source section. Present only registered logical targets, then require Review source delivery before showing Prepare reviewed delivery. Review displays the manifest checksum, changed paths, new-file versus replacement intent and expandable diff text. Delivery history shows task state and evidence inspection; advancement is disabled for terminal tasks or missing worker credentials. Ask-mode source approval uses the existing exact-action Approvals screen. Explain that source conflicts block delivery and partial multi-file writes may require manual recovery; never display a failed or partial result as successful delivery.

## Model-backed repair jobs

Build jobs is a built-in tab/window panel. Configuration uses a responsive two-column form (one column for narrow windows), explicit selected-context checkboxes and separate call/cycle/step/time budgets. Context selection must not overflow horizontally; checkbox controls keep their intrinsic compact width with wrapping labels. Collapse configuration after queuing so current progress stays visible, while allowing another job to be configured explicitly.

Require an unchecked model-sharing consent control and make automatic acceptance unavailable without full policy. Present call slots as reservations, not currency estimates. Job cards distinguish stage from state, display budget usage/current cycle/deadline and provide explicit pause/resume/cancel. Review shows the immutable response and both checksums before Accept reviewed job repair; render all content as escaped plain text. Final run evidence/source delivery remains in Coding runs. Use the existing Jarvis palette and typography; no Skyra Platform dependency.

## Unattended assignments

Assignments is a built-in panel supporting the existing tab/window arrangement model. Its form selects an accepted active run, goal, step budget and time limit. Show host enablement separately from runner process health. Cards display state, pending control, budget usage, deadline, updated timestamp and expandable evidence summary. Pause, Resume and Cancel are explicit state-aware controls. Preserve visible blocked/budget-limited outcomes; do not style them as successful completion. Explain checkpoint pause/deadline behavior and retained uncertain budget slots. Poll only active visible panels; the worker progresses independently. The tray label distinguishes exiting the dashboard from background work.

## Scaffold review interaction - 2026-10-15

Use an expandable section in the specification card, with labelled project-name/JSON inputs, setup state, clear file accordions and visible checksum/destination provenance. Review consent is a compact checkbox with a separate create button. Long paths, JSON and hashes wrap within narrow panels; bounded code areas scroll. Show creation outcome in a named status region and errors as alerts. Editing input clears the previous review. Do not imply a passing product test or enabled execution from successful creation.

Scaffold fieldsets use continuous document flow with no inherited fixed-height internal scroll box. Only long code blocks have bounded scrolling. Narrow-panel acceptance checks both horizontal overflow and a form content height that fits its own box, so consent and file sections are reached through the normal panel scroll.


## Integrated project-building milestone - 2026-10-15

The specification screen uses one continuous expandable workflow: complete file/provenance review, receipt, exact registration review, native-command consent, separate permission review, scoped Build jobs and final delivery. Show disabled-host/reconciliation states honestly. Grant mode affects every granted project resource and must be explicit. Discard stale consent when reviewed inputs change. Preserve responsive fieldsets without inherited clipping and suppress stale delivery readiness when a new job starts.


## Unattended operations milestone - 2026-10-16

Use the existing Activity tab/window for Unattended operations: current work, immutable outcome inbox, registered project library and collapsible raw Core events. Show unread/acknowledged state, reason, reserved call/step budgets, deadline and review links. Display inactive/reconciliation/grant states honestly. Opening a saved workflow must not replay creation or grant consent. Keep wrapped scope/evidence and responsive action rows at narrow desktop widths.


## Scheduled background builds - 2026-10-16

Build jobs offers an explicit future-start checkbox, local date/time with visible browser time zone, allowed late-start minutes and a separate scheduling-conditions consent. Editing time/window invalidates that consent. Cards show scheduled state and planned/start-by dates. Activity shows recorded runner contact as never-seen/recent/in-progress/stale with last request/result, separately from host enablement, plus schedule dates on current work. Retain responsive controls, keyboard access and all existing model/approval/delivery boundaries.


## Active Jarvis identity direction - 2026-10-16 (planned)

Preserve dedicated Jarvis design and current workspace organisation; no Skyra Platform UI dependency. Consolidate competing historical palette proposals into one token set before component changes. Proposed semantic tokens: canvas #080E1A, solid surface #111B2D, raised surface #19263C, text #F2F6FF, muted text #B3C0D4, cyan #67E4F5, violet #B5A0FF, success #7DDBB1, warning #FFD080, error #FF9AAA. These are design targets, not contrast-certified implementation values. Verify foreground/background combinations in real states.

Gloss is progressive enhancement: subtle top-edge reflections, restrained gradients, thin luminous borders and blur on selected navigation/panel chrome. Solid opaque reading surfaces support code, logs and long conversations. Avoid glow behind small text. Central tokens define spacing, radius, shadow, opacity and motion; detached windows share them. Bundle an appropriately licensed interface font (Inter candidate) and code font locally after asset/license review; keep system fallbacks until included. Provide reduced-transparency and reduced-motion preferences, and graceful fallback when effects are unsupported.

Orb state presentation derives from actual activity with explicit scope. Connectivity offline is distinct from idle; listening/speaking require a real voice pipeline. Planning uses deliberate orbital motion, execution focused bands, testing measured scanning, approval a calm amber pulse, failure restrained warning and completion a brief event-linked accent. Concurrent activities remain visible as labels/counters rather than being hidden by a single animation. Do not infer model thinking from elapsed time or display private reasoning. A pure state resolver should specify precedence and be testable without rendering. Audio amplitude drives speaking only when actual playback exists. Stop continuous animation when the document is hidden and respect reduced motion without losing status information.

Acceptance: readability/contrast, keyboard focus and screen-reader status; narrow/large layouts; detached windows; actual state transitions; reduced preferences; no simulated progress; inspect actual rendered screenshots before marking visual polish complete.

## Implemented activity and glossy identity slice — 2026-10-19

Jarvis keeps its dedicated native UI and React Flow subsystem map; no Skyra Platform UI package was introduced. Shared surface tokens now provide a solid navy base, restrained top reflections and panel shadows. Accent cyan is #83DCF0; raised/solid tokens are #142237/#101B2B, with violet #B7A5F5. Typography uses Windows Segoe UI Variable Text/Segoe UI with local system fallbacks, without network fonts or redistributing Windows font files. Proposed licensed bundled fonts remain future work.

The existing reusable JarvisCore now receives a pure resolved activity presentation. States distinguish disconnected/unavailable activity, idle, review, stopping, protected test execution, source operations, pending coding/planning/chat responses, file inspection, blocked, paused and queued work. Review has priority, while concurrent testing, pending model responses and blocked items remain in text. Pending model responses are recorded requests, not proof of live reasoning or provider health. Scope and observation time are visible. Listening/speaking and event-linked completion animation remain unimplemented; the UI explicitly reports voice unavailable.

The sphere gains a restrained specular shell, state-coloured bands and distinct orbital speeds; test execution uses a dashed band, planning/chat a gentle reflection. Manual pause and keyboard/pointer rotation remain. Animation stops for hidden/minimized native windows, hidden documents and inactive workspace tabs; visible background panels may animate for multi-monitor layouts; reduced motion suppresses all orb animation. Reduced-transparency and forced-colour fallbacks preserve readable state labels. Ornament is not a progress percentage. Browser event tests are distinguished from the pending actual native-minimize acceptance; see DEVELOPMENT.md for final package verification.

Selected solid token pairs were measured: main text #EEF3FC/#101B2B 15.54:1; muted #99A8BE/#142237 6.62:1; cyan #83DCF0/#101B2B 11.09:1; planning violet #BAA4FF/#0C1726 8.44:1; review amber #F4CE83/#0C1726 12.01:1; blocked rose #F4A3AD/#0C1726 9.17:1. These are token calculations, not a certification of every composited/disabled state. Native visual inspection remains the package gate.
