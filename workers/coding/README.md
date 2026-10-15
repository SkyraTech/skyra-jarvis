# Skyra Coding Worker

Component of `skyra-jarvis`. Implemented: selected-file snapshots, explicitly allowed new-file targets, guarded patch/create operations, owner-enabled native Windows tests and durable review/approval workflows. The online runtime and native desktop integrate with this worker. Separately reviewed source delivery is implemented; bounded model-driven repair is implemented, and the first reviewed function scaffold is available through an owner host command. General website/service generation remains pending. Native execution carries Windows account privileges; optional Docker isolation is not live-verified.

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

## Create a reviewed new-project scaffold

The first template creates a Python JSON function project, not an HTTP server or website. Use this trusted owner maintenance command from the Jarvis repository root against an existing private Core database. A specification must already be approved in Jarvis. Choose an existing private local parent without links/reparse points, an unused lowercase child slug and an existing absolute Python .exe. Do not expose this command as a model tool.

Prepare an owner-authored request JSON outside the repository (replace every placeholder):

```json
{
  "specification": "<approved-specification-id>",
  "expected_sha256": "<approved-specification-sha256>",
  "parent": "C:/private/jarvis-projects",
  "name": "client-service",
  "python": "C:/absolute/path/to/python.exe",
  "contract": {
    "cases": [
      {"name": "positive", "input": 3, "output": 6},
      {"name": "negative", "input": -2, "output": -4}
    ]
  }
}
```

The reviewed specification must describe the intended behavior; these examples illustrate a doubling function. Contract limits: 1..32 unique named inputs, finite JSON data, maximum depth 10 and 16KB total. The generated API is app.handle(value), returning JSON-compatible output. Tests compare JSON values, including boolean versus numeric type differences.

```powershell
.\venv\Scripts\python.exe workers/coding/scaffold.py --database C:/private/core.sqlite3 --actor owner --request C:/private/scaffold-request.json --review C:/private/scaffold-review.json
```

Inspect plan.files, contract, document_provenance, destination, profile, python_sha256 and limitations in the review JSON. Copy its exact plan_sha256 into the apply command. Review files are created exclusively and never overwritten.

```powershell
.\venv\Scripts\python.exe workers/coding/scaffold.py --database C:/private/core.sqlite3 --actor owner --request C:/private/scaffold-request.json --apply --expected-plan-sha256 <reviewed-plan-sha256>
```

The new child contains source/, snapshot/, review.json and scaffold.json. All nine initial documents are included: approved documents are preserved exactly; identified host defaults fill missing originals. The initial app.py raises NotImplementedError. tests/test_acceptance.py and acceptance.json are protected baseline files. scaffold.json is an immutable creation receipt, not live build status.

Review registration_draft in scaffold.json. It intentionally sets owner_enabled=false. Merge its workspace, profile and source-delivery registrations into your existing private host configuration; do not replace unrelated registrations. Explicitly enable trusted native execution, grant the exact workspace/source resources through project policy, and restart the configured Core. Creation itself does not change permissions, start a process, install a dependency or call a model.

In Build jobs, choose the new workspace, scaffold-acceptance profile, approved specification and all three selected files, then provide the implementation goal and explicit provider consent/budgets. Default proposal review and task approvals still apply. Passing example tests reaches review readiness; source/app.py remains the stub until separately reviewed source delivery. Examples alone do not prove full requirement coverage or security.

Existing destinations, changed approval/plan/interpreter bytes and linked parents are refused. Failed staging retains its private .jarvis-scaffold-* review receipt. Filesystem publication and SQLite audit are not atomic together: if publication succeeds before an audit failure, inspect the published scaffold.json and reconcile manually; a repeat create refuses the directory. No automatic cleanup, overwrite, Git operation or deployment occurs. Desktop scaffold creation and broader website/service templates remain future work.
