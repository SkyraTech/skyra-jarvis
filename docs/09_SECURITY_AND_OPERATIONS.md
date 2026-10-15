# Jarvis Orchestration Core — Security and Operations

## Maintained specification — current status

Updated 2026-10-15. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented and verified: durable core, authenticated local API, selected-file worker, owner-enabled native Windows tests, repair workflows and bounded Gemini/Groq repair proposals with versioned skill context and controller review. Native desktop control, flexible 3D/tabbed/multi-window workspace, model-backed conversation, structured draft planning and setup-readiness guidance are implemented. A reviewed owner-operated Python function scaffold feeds existing model repair jobs. General autonomous building, a scaffold/configuration editor, installer/update delivery and mobile pairing remain pending.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](ARCHITECTURE.md)
- [Current functionality and implementation boundaries](FUNCTIONALITY.md)
- [Current milestone and verification summary](DEVELOPMENT.md)

Prepared: 2026-10-14. Requirement/design baseline. Use the maintained current-status section above to distinguish implemented work from planned work.

## Trust boundaries

User/agent input, webpages, repository text, messages, documents and external MCP output are untrusted data. They cannot change system policy or authorize a tool. Enforce actor, tenant, project, account and resource scope server-side. Child jobs can narrow permissions but cannot expand them.

## Permission modes

Support read-only, ask-before-action, selected-action grants, scoped full access and custom policies. Full access is bounded by its configured resources and actor; it does not mean global administrator. Approval binds normalized action/payload hash, resource, account, policy version, approver and expiry. Recheck before execution and invalidate on changes or revocation. Preserve immutable audit records for decisions and outcomes.

## Secrets and remote access

Use OS-protected credentials on Windows and a managed secret store when hosted; encrypt sensitive durable tokens, restrict file permissions and rotate/revoke connections. Never include secrets in prompts, logs, URLs, process arguments or frontend bundles. OAuth uses verified state/PKCE where applicable, strict redirects and minimum scopes. Webhooks verify signatures and replay windows.

Local loopback is not automatically trusted: authenticated IPC/API and origin checks are required. Mobile control uses revocable pairing and encrypted transport; do not expose an unauthenticated desktop port to the Internet. Choose remote connectivity after threat review. Report local-machine offline state honestly; always-on intake/alerts require a hosted component.

## Data lifecycle

Separate operational state, conversations, curated memory, audit events and artifacts. Define retention by data class and organization policy before launch; support export and permitted deletion including search indexes and derived copies. Audit retention and legal/business requirements may differ from conversation deletion. Backups use restricted access and encryption; test restoration into an isolated environment. Never commit live credentials or customer fixtures.

## Operations and recovery

Expose readiness and liveness separately, with sanitized dependency status. Correlate logs/metrics/traces using run and request IDs. Alert on sustained failures, queue age, lease expiry, provider throttling and credential expiry; deduplicate alerts and define escalation ownership. Structured logs avoid message bodies by default.

Deploy/release candidates include exact versions, migrations, rollback constraints and evidence. Prefer reversible application changes; database rollback requires an explicit data-preservation plan. On incident: contain within preauthorized policy, collect evidence, reproduce in isolation, prepare fix, run quality gates, request the configured release decision, then observe results. Do not label a fix production-ready solely because an agent generated it.

## Project-specific decisions

- Mobile OS and companion-app approach are unconfirmed
- Production-release policies and per-project budgets require configuration
- Existing memory data needs an explicit non-destructive migration/export plan

Package-only projects apply supply-chain/release controls and consumer tests; they do not need invented runtime endpoints or operational databases.

## Model generation operations

Provider access is controller initiated and uses explicit environment key references. No SDK automatic retries, key cycling, provider fallback or model tool execution. Selection is bounded but may contain embedded secrets; review before export. Selected source/goals persist in private SQLite and go to the chosen provider under its account policies. No private reasoning or raw SDK errors are retained. Usage is token metadata, not an enforced monetary budget. Interrupted calls may still incur cost; create a new request only after review. Trusted native execution retains account privileges. Never expose the loopback API as mobile/hosted transport.

## Native control operations

Use per-user local app data and DPAPI ciphertext for desktop controller/worker tokens. Provider keys stay in explicit host environment variables. No renderer token storage, generic shell/filesystem/HTTP plugin or relaxed browser CORS/Origin policy is introduced. Host bridge is loopback-only, proxy/redirect/retry disabled and bounded. Bootstrap refuses existing state; its defaults enable no online calls or native execution. The development release still depends on the configured local Python core; no installer/autostart/updater or hosted/mobile endpoint is deployed. Tray Exit can interrupt active work; inspect durable state and reconcile uncertainty before retrying. Native trusted execution retains Windows account access.

## Conversation and draft planning

Only authenticated controllers can export conversation context to a configured model. Context contains at most 30 recent complete messages and 48 KB encoded JSON; oversized current requests are rejected rather than silently truncated. Provider keys stay in the trusted host environment. Raw provider errors and invalid output are not persisted. Interrupted requests may still be billed externally, but late responses cannot add messages or plans. Plans grant no resource, execution or publication authority. Read-only project policy still permits explicit conversation requests, since that mode restricts workspace actions rather than online billing.

## Flexible 3D workspace

Layouts contain only UI metadata, never tokens, message bodies, prompts or executable requests. Browser preview does not create native windows or call the Core. Native windows inherit the same trusted bridge; opening another window grants no new project/resource permissions. Closing a panel/tab leaves durable requests intact; cancellation remains an explicit task action. Restore only local built-in panels from bounded validated arrangements, clamp geometry onto connected monitor work areas and preserve main-window tray ownership. Use Show all windows to restore minimized panels before saving an arrangement.


## Versioned specification workflow - 2026-10-15

Specification approval is a review record, not a permission grant. The page renders documents as plain text and never executes Markdown/HTML. Filenames are host-defined; no new filesystem or shell command is exposed. Publication/approval use SQLite transactions and project-owner checks. Superseded specifications cannot authorize new repair generation/acceptance. Existing accepted runs require explicit cancellation; no implicit rollback of running work is promised. No API keys or production conversations are used by fixture tests.


## Specification revision and delivery - 2026-10-15

The renderer cannot provide export paths or file bytes. Export root defaults to Documents/Skyra/Jarvis/exports; optional absolute JARVIS_EXPORT_ROOT is trusted host configuration whose parent must exist. Output is staged in a newly created directory, files use create_new and sync_all, and a rename publishes the bundle. Existing version folders must match manifest and document bytes; altered exports fail without overwrite. Known Windows reparse points are rejected for directories/files within the export root. Same-account filesystem race isolation and physical-disk power-loss certification are not claimed. Export is a point-in-time approved snapshot and grants no execution authority.


## Reviewed new-file coding - 2026-10-15

Creation targets are trusted host configuration. Models cannot expand the selection, create protected tests, pick commands or overwrite existing files. Creation uses exclusive binary open, flush and fsync inside the existing guarded action transaction. File effects cannot roll back with SQLite: a crash or I/O failure after creation remains uncertain and requires reconciliation; do not automatically replay or overwrite. Native execution retains Windows account access and is not OS isolation.

## Source-delivery operations - 2026-10-15

Register source roots only through trusted host configuration, with separately granted source and workspace resources. Review the manifest and source diff before preparation. A changed source baseline, snapshot, test profile or target path invalidates the reviewed operation. Source permissions do not authorize staging, commits, pushes or production deployment.

Delivery journals and original-byte backups live in evidence_root/delivery-<task>/ and can contain private source; apply the same private storage, backup and retention policy as snapshots. If blocked_or_partial, interrupted, or an uncertain outcome is reported, stop dependent work. Read journal.json, including written and next, compare all changed source files against before/after checksums, and inspect before/ backups. Preserve later owner edits. Recovery is explicit manual reconciliation; neither restarting Jarvis nor clicking advance rolls back or retries a terminal delivery. There is no automatic all-files atomicity guarantee. Local native testing and delivery require a trusted host and cooperating single writer.

## Model-job consent, scope and recovery

New model jobs require controller identity, explicit allow_model_calls=true, selected context and fixed call/cycle/step/time limits. Host unattended enablement and an existing provider registration are also required. Automatic proposal acceptance requires per-job opt-in plus current full policy; ask mode cannot silently enable it. Protected tests and commands remain host-defined. Validation covers structure/scope/freshness, not arbitrary generated-code security. Native execution retains the configured Windows account's privileges.

Test output can contain sensitive application information. Sharing consent includes selected files, the selected specification and bounded verified diagnostics. Do not assume all output can be scrubbed automatically; prepare trusted test data and logging policies before using real customer projects. Diagnostic content is untrusted data and cannot grant commands/resources. No raw provider exception or invalid response is recorded as executable instructions.

Schema 11 preserves existing state and adds jobs/cycles/attempts. Back up private state before migration. Unknown billable calls retain their reserved slot; provider failure or invalid output does not trigger fallback, key rotation or automatic retry. A generating proposal after restart blocks resume until inspected/interrupted. A response already ready in SQLite can resume without another call. Cancellation suppresses late output but may not stop provider billing. Currency/organization-wide spending limits are not implemented; the job exposes bounded call slots and reported usage instead.

Pause/cancel controls operate at existing checkpoints. Changed selected source after a failing baseline, modified protected tests, changed profile/provider bindings and superseded specifications block new work rather than expanding context. Existing accepted runs retain their original execution/cancellation boundaries. All model jobs end before original-source delivery; no stage/commit/push/deploy authority follows from a passing test.

## Hidden assignment runner operations - 2026-10-15

Keep unattended_enabled off until trusted workspaces, fixed test profiles and a project-scoped DPAPI worker credential are configured. Assignment creation is explicit owner authorization for bounded progression of an accepted run, not a new permission grant. Ask mode waits for each required decision; full mode permits existing granted actions. No source delivery, provider generation or Git operation is dispatched by this runner.

Back up private SQLite before migration 10. New assignment/attempt tables retain goals, state and evidence references; apply the existing private-state access/retention policy. Heartbeat status contains safe state/project IDs, not tokens or raw exception details. Private runner.json must not carry API key values or arbitrary URLs. Transport is loopback-only with proxies/redirects disabled. The same Windows user profile must decrypt its worker credential; a service-account migration is not supported.

Pause takes effect after an admitted step; cancel requests task cancellation through existing supervision. Deadlines are checked between steps. A crash after dispatch retains a budget charge and becomes blocked after its 600-second claim expires. Inspect the coding task, cleanup state, attempt and evidence before resuming; uncertain external effects are not automatically retried. Relaunch restores queued work, not permission to replay a live/uncertain task. Stop the runner using pythonw launch.pyw --stop-background; allow the current bounded step to finish. This stops only its supervisor-owned Core, so a desktop using that Core becomes disconnected. Closing/exiting only the dashboard leaves an independently owned runner active. Do not suspend/shut down the PC expecting local jobs to continue.

## Scaffold operations - 2026-10-15

Run workers/coding/scaffold.py only as a trusted owner maintenance command against the existing private Core database. It does not authenticate an external caller and must not be offered to models or remote users. Review JSON contains specification content and planned files; keep it in private local storage. Choose an existing local parent without links/reparse points and a new child slug. Never point creation at an existing project.

Review the complete JSON plan and checksum before --apply. The generated scaffold.json registration_draft leaves native owner_enabled false and does not grant resources or alter private configuration. Merge only intended registrations into existing host configuration, explicitly enable trusted execution, grant exact workspace/source scopes and restart the configured Core before using Build jobs. Do not replace other project registrations. Native processes run with the Windows account privileges.

If staging fails, inspect the private .jarvis-scaffold-* directory and its review receipt; there is no automatic cleanup/replay. If publication succeeds but its audit transaction fails, the published scaffold.json remains the receipt and repeat creation refuses the destination. Reconcile manually instead of retrying filesystem effects or deleting a project. Creation is not a deployment or implementation-success event. Existing separate source-delivery journals and review rules still apply.
