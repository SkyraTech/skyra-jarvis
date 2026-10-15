# Skyra Coding Worker

Component of `skyra-jarvis`. Implemented: selected-file snapshots, explicitly allowed new-file targets, guarded patch/create operations, owner-enabled native Windows tests and durable review/approval workflows. The online runtime and native desktop integrate with this worker. General greenfield building, iterative debugging and original-source delivery remain pending. Native execution carries Windows account privileges; optional Docker isolation is not live-verified.

## Initial project documents — retain and maintain

- [Product requirements](docs/01_PRODUCT_REQUIREMENTS.md)
- [System architecture](docs/02_SYSTEM_ARCHITECTURE.md)
- [Development rules](docs/03_DEVELOPMENT_RULES.md)
- [Design system](docs/04_DESIGN_SYSTEM.md)
- [Project tasks](docs/05_PROJECT_TASKS.md)
- [Project memory](docs/06_PROJECT_MEMORY.md)
- [API and event contracts](docs/07_API_AND_EVENTS.md)
- [Testing and acceptance](docs/08_TESTING_AND_ACCEPTANCE.md)
- [Security and operations](docs/09_SECURITY_AND_OPERATIONS.md)


## Explicit new-file targets

Supply existing protected tests and owner-approved absent target paths when preparing a snapshot outside the original project:

```powershell
.\venv\Scripts\python.exe workers/coding/snapshot.py --source C:/trusted-project --destination C:/jarvis-workspace --files tests/test_feature.py --create feature.py
```

Register that snapshot through the existing trusted workspace configuration. In the desktop, select the creation target, review the proposed whole file and accept the coding run. The workflow expects the protected baseline to fail before creation, then requires a passing retest. Original source is preserved. See the owning architecture for manifest v2 and absence/reconciliation semantics.
