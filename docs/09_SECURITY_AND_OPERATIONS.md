# Jarvis Orchestration Core — Security and Operations

## Maintained specification — current status

Updated 2026-10-15. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented and verified: durable core, authenticated local API, selected-file worker, owner-enabled native Windows tests, repair workflows and bounded Gemini/Groq repair proposals with versioned skill context and controller review. Native desktop control, flexible 3D/tabbed/multi-window workspace, model-backed conversation, structured draft planning and setup-readiness guidance are implemented. General autonomous building, a full configuration editor, installer/update delivery and mobile pairing remain pending.

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
