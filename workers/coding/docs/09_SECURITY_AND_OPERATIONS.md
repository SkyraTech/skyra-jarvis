# Skyra Coding Worker — Security and Operations

## Maintained specification — current status

Updated 2026-10-16. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented: selected-file snapshots, guarded patch/create operations, owner-enabled native Windows tests, online-model repair jobs, bounded hidden-runner progression, native desktop review and separately approved source delivery. Approved-specification scaffolds create bounded Python JSON-function projects through the desktop or owner command with protected examples. Website/full-service scaffolds, a trusted registry editor, Git branch/revision delivery and currency budgets remain pending. Native execution carries Windows account privileges; optional Docker isolation is not live-verified.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](../../../docs/ARCHITECTURE.md)
- [Current functionality and implementation boundaries](../../../docs/FUNCTIONALITY.md)
- [Current milestone and verification summary](../../../docs/DEVELOPMENT.md)

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

- Git worktrees alone do not provide process or filesystem isolation
- Windows-native and container execution support different toolchains
- Isolation technology is an implementation gate, not a command-blacklist assumption

Package-only projects apply supply-chain/release controls and consumer tests; they do not need invented runtime endpoints or operational databases.


## Reviewed new-file coding - 2026-10-15

Creation targets are trusted host configuration. Models cannot expand the selection, create protected tests, pick commands or overwrite existing files. Creation uses exclusive binary open, flush and fsync inside the existing guarded action transaction. File effects cannot roll back with SQLite: a crash or I/O failure after creation remains uncertain and requires reconciliation; do not automatically replay or overwrite. Native execution retains Windows account access and is not OS isolation.

## Approved-specification scaffolds - 2026-10-15

Use the scaffold command only as trusted host maintenance against an existing private database. Keep review artifacts private. Apply only an inspected exact plan checksum. Existing destinations are never overwritten; interrupted staging is retained and post-publication audit errors require manual reconciliation. Registration drafts have owner_enabled=false; explicitly merge/configure/grant resources before use. No automatic dependency install, Git operation, deployment or protected-test rewriting is allowed.

## Desktop scaffold workflow - 2026-10-15

Desktop creation requires an explicitly configured existing absolute scaffold_root in trusted launcher configuration. Default is null/off; no real private setting is auto-changed. Root/interpreter cannot come from the renderer. On uncertainty inspect the initial receipt, reconcile missing audit and retain staging for manual inspection. Creation does not register resources, enable model/execution or authorize source delivery.


## Integrated project-building milestone - 2026-10-15

Native command execution retains the Windows account privileges and must be host-enabled plus explicitly consented. New bootstrap keeps scaffold_root null and scaffold_execution_enabled false; actual private configs are untouched. Durable rows bind the initial manifest, fixed profile and interpreter bytes. Creation/registration never grants resources, provider consent, source delivery or deployment. Uncertain filesystem/audit effects and damaged registrations require explicit reconciliation; do not retry automatically. The generated server binds loopback; tests/examples do not provide production security certification.


## Unattended operations milestone - 2026-10-16

The inbox stores bounded goal/state/scope/budget/evidence references, excluding test stdout, provider context and secrets. Treat displayed goals/evidence as untrusted text. Acknowledgement is owner-scoped and never authorization. Immutable completion means tested review readiness at that time, not current source freshness or production deployment. Background operation still requires a running PC/Core/runner, current grants/consent and budgets; no Windows service/login/wake task or external messages are configured.


## Scheduled background builds - 2026-10-16

Schedules are one-time admission intents, not Windows wake/startup tasks or recurrence. The PC/Core/worker must remain running. File/spec drift blocks before the first baseline, including during approval waits; protected profile/interpreter/provider bindings and current permissions remain enforced. Missed starts fail; schedules cannot extend their immutable budgets or authorize release. Request-contact timestamps reflect authenticated Core communication, not PID/liveness certainty. No credentials or model context are added to contact records.
