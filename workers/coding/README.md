# Skyra Coding Worker

Component of `skyra-jarvis`. Implemented: selected-file snapshots, explicitly allowed new-file targets, guarded patch/create operations, owner-enabled native Windows tests and durable review/approval workflows. The online runtime and native desktop integrate with this worker. Separately reviewed source delivery is implemented; general greenfield building and iterative debugging remain pending. Native execution carries Windows account privileges; optional Docker isolation is not live-verified.

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

## Reviewed delivery to original source

Add a trusted host registration to the existing workspace configuration (substitute actual IDs and an absolute source directory):

```json
"delivery_targets": [
  {"project_id": "<project-id>", "resource_id": "source:project",
   "workspace_resource": "workspace:project", "directory": "C:/trusted-project"}
]
```

This is a property of the existing configuration object, not a complete configuration. The source must be outside snapshot/evidence state. Grant both logical resources in project policy. After a run passes its protected retest and reaches ready_for_review, use Review source delivery, inspect the diff/checksum, then prepare and advance the separate source write. Ask mode requires its own exact-action approval. Stale source/snapshot/profile or reconfigured target bindings block delivery.

Saved originals and journal.json are under the private evidence directory's delivery-<task> folder. Partial multi-file effects require manual reconciliation; no automatic rollback, retry, Git operation or deployment is performed. See [architecture](../../docs/ARCHITECTURE.md#reviewed-source-delivery-architecture---2026-10-15) and [operations](../../docs/09_SECURITY_AND_OPERATIONS.md#source-delivery-operations---2026-10-15).
