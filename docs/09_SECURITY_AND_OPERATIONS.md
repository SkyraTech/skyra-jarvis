# Jarvis Orchestration Core — Security and Operations

Prepared: 2026-10-14. Status: proposed implementation baseline. User requirements are captured here; technical choices remain subject to implementation validation.

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
