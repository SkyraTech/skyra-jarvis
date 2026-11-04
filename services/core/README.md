# Jarvis Core

Durable state, scoped policy, authenticated local API and repair-workflow persistence. Specifications belong to the Jarvis project.

## Initial project documents — retain and maintain

- [Product requirements](../../docs/01_PRODUCT_REQUIREMENTS.md)
- [System architecture](../../docs/02_SYSTEM_ARCHITECTURE.md)
- [Development rules](../../docs/03_DEVELOPMENT_RULES.md)
- [Design system](../../docs/04_DESIGN_SYSTEM.md)
- [Project tasks](../../docs/05_PROJECT_TASKS.md)
- [Project memory](../../docs/06_PROJECT_MEMORY.md)
- [API and event contracts](../../docs/07_API_AND_EVENTS.md)
- [Testing and acceptance](../../docs/08_TESTING_AND_ACCEPTANCE.md)
- [Security and operations](../../docs/09_SECURITY_AND_OPERATIONS.md)

## Optional coding-service adapter

The reusable delegation capability is maintained in sibling skyra-coding-agent/services/coding. From the Jarvis repository, install it into the configured environment with:

    .\venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation --no-index -e ..\skyra-coding-agent\services\coding

This source installation was verified with the current installed build tooling and downloads no dependencies. Restart the configured core to load it; do not create a new database or delete private state. Schema 16 preserves existing state and adds delegated connection/job provenance. Missing packages report unavailable rather than enabling submission.

The controller must register a separate coding_agent credential with exact project scopes in the private auth registry and approve its connection. Existing general agent or worker credentials cannot be reused for this port. Never place tokens in a prompt or renderer. Capability installation does not enable a provider, grant, paid call or runner. The existing hidden background core/runner must be explicitly configured for UI-independent execution. Connection creation/revocation and task client usage are documented in the separate product README/architecture; its native UI and natural-language router are still pending. The explicit ConversationCodingTool/dispatcher now records durable command receipts and observations without UI automation; the existing chat composer is not yet wired to it.

## Local LogHub Python pilot

Jarvis Core and the hidden runner use the installed Skyra Python SDK, not the Node SDK or an SDK source-folder import. From the Jarvis repository root:

```powershell
.\venv\Scripts\python.exe -m pip install -r services/core/requirements-api.txt
# Required when replacing an older schema-only wheel with the same1.0.0 version:
.\venv\Scripts\python.exe -m pip install --no-deps --force-reinstall vendor/skyra_logger-1.0.0-py3-none-any.whl
```

The pilot wheel is built from a temporary snapshot of current LogHub Python source; the SDK repository was not edited. SHA256:6f9fdb21f6ccd1e171b8c7af8f4a4908814654b1523bcba43b5f050199ba6131; size47,189 bytes. The older available distribution was schema-only and did not export create_skyra_logger, so it is not used. This is a local verified artifact, not a newly published package release. jsonschema4.26.0 is pinned in API requirements; other transitive dependencies are not fully locked.

Operational events use project skyra-jarvis, service jarvis-core or jarvis-runner, explicit local environment and unique process instance IDs. Logs are below <database-parent>/logs or <runner-state>/logs, following project/environment/service/instance/UTC-segment hierarchy. They do not replace canonical activity events, SQLite sessions or chat history. Successful mutation requests, failed requests, application lifecycle and runner dispatch are observed; routine successful GET polling is omitted. No frontend browser SDK or legacy voice logger migration is included.

Disable with --no-logging on services/core/run.py or services/runner/run.pyw. Library/test app factories remain unchanged and do not create loggers automatically. The internal observability adapter owns one SDK root, a bounded512-event queue, background delivery and bounded best-effort flush/close. Missing SDK or storage failure is nonfatal; diagnostics() exposes numeric error/drop/shutdown-timeout counters. SDK canonical validation occurs for each Python event; no nonexistent validationMode option is assumed. The SDK may emit its own local filesystem diagnostics to stderr on failure; no raw application exception, prompt, source, headers/body, token or credential is forwarded by this integration.

Restart an existing Core/runner process to load the Python changes. No production state or running user service was reset. This pilot does not ship logs to a central collector, add a logging dashboard, persist every coding-engine event, or log the native Rust host. Retention, Windows ACL administration and exact durable loss accounting remain separate work.

API correlation is emitted as skyra.business.core_request_id, reusing Core's generated response x-request-id. The SDK reserves request_id, so that name is not used as a custom business field. Headers themselves are never logged.
