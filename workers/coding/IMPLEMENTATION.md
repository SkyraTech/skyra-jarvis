# File-worker foundation

Current execution update: the owner selected trusted native Windows execution. The subsequent [execution/workflow checkpoint](EXECUTION_AND_WORKFLOWS.md) adds real test profiles, Job Object supervision and durable repair plans. The disabled-execution statements below describe the earlier file-only baseline, not the currently optional owner-enabled native backend.

Implemented 2026-10-14. This phase provides selected-file snapshots, guarded read/search/patch/diff/static-check operations, API dispatch and checksum-verified evidence. It does not execute repository code, install packages, stage, commit, push or deploy.

## Workspace lifecycle

The trusted host selects 1–100 UTF-8 text files, each at most 1 MiB and together at most 10 MiB. `Workspace.snapshot` copies them into a new directory outside the source tree, with a baseline and manifest separate from editable files. Existing destinations are refused. The source working tree, uncommitted changes, Git history and index remain untouched. Files not selected cannot be read or delivered through this worker.

Developer preparation from the Jarvis root:

```powershell
.\venv\Scripts\python.exe workers/coding/snapshot.py --source C:\path\to\project --destination C:\path\to\new-run --files src/app.py tests/test_app.py
```

Use a private per-user run directory. This does not create a Git branch or provide repository revision selection; manifest hashes bind the selected working-copy content. Git revision snapshots, new-file creation and delivery application are future work. The generated diff is returned for review; it is never automatically applied back to source.

## Trusted registration

The native host provides a mapping from `(project_id, resource_id)` to a prepared Workspace. Agent task payloads cannot register directories. The core developer launcher supports a separate `--workspace-config` file:

```json
{
  "evidence_root": "C:/private/jarvis/evidence",
  "workspaces": [
    {
      "project_id": "<existing project id>",
      "resource_id": "workspace:demo",
      "directory": "C:/private/jarvis/new-run"
    }
  ]
}
```

Protect writes to this configuration using OS account permissions. Evidence must be outside editable files. Each snapshot should be registered under a unique run resource. Current registration is static and reloads on server restart; dynamic desktop provisioning is later work.

## Task operations

Task requests still use the core API's required request ID, project and resource scope. Each operation has an exact field set:

| Operation | Task action | Payload fields |
|---|---|---|
| `read` | `read` | `operation`, `path` |
| `search` | `read` | `operation`, `query` (literal text, max 256 chars; max 100 hits) |
| `patch` | `write` | `operation`, `path`, `expected_sha256`, `old`, `new` |
| `diff` | `read` | `operation` |
| `verify` | `read` | `operation` |

Patch requires the current file hash and exactly one matching anchor. It preserves UTF-8 BOM where present and existing line endings outside replacement text. Stale or ambiguous replacements fail. Replacement is flushed then atomically substituted. Selected files must remain regular files without hard links, symlinks or Windows reparse points. Traversal, drive paths, alternate data streams, device names and known private configuration paths are denied.

`verify` parses Python and JSON without running either. Results explicitly identify `static_syntax`; unsupported file types do not count as passing. This is not a unit-test/build result and does not certify correct behavior.

## Authorization and evidence flow

1. Agent creates an immutable task intent.
2. Worker claims it through `/start`; write operations pause for a controller decision when policy requires approval.
3. Worker calls `POST /v1/tasks/{task}/perform` with the lease token.
4. Core rechecks ownership, current policy version, lease and state in a transaction before the short file operation. The adapter also checks project/resource registration and operation/action consistency.
5. Worker creates a checksum-addressed JSON report and core records success/failure with its reference. Failed static verification becomes a failed task.
6. Controller/authorized agent can fetch only attached evidence through `GET /v1/tasks/{task}/evidence/{checksum}`. Report integrity is checked on read.

File side effects and SQLite cannot form a distributed atomic transaction. If a crash or artifact-write failure occurs after an edit, the task stays uncertain and requires reconciliation; stale-hash protection prevents blindly repeating a patch. Policy/cancellation changes are serialized with these bounded file operations. Do not use this transaction mechanism for long-running processes. Local hostile processes running as the same OS user are outside this file adapter's security guarantee.

## Execution gate

Docker was not available during this phase. Arbitrary process execution is intentionally rejected, even with full-access task policy. A working directory and file checks do not isolate subprocesses. Before enabling build/test commands, implement and verify an OS/container boundary with no host credentials, controlled mounts/network, resource limits, process-tree cancellation and reproducible test profiles. That remains a required implementation gate, not a completed feature.

Existing direct shell tools in the legacy assistant were not migrated by this phase. This new file worker does not make them sandboxed.

## Verification

```powershell
.\venv\Scripts\python.exe -m unittest discover -s services/core/tests -v
.\venv\Scripts\python.exe -m unittest discover -s workers/coding/tests -v
```

Worker integration tests use real temporary snapshots, SQLite and in-process HTTP requests. They cover the approval/edit/verify/evidence path, source preservation, path and scope denial, hard links, stale hashes, changed baselines, failed verification, lease replay, policy revocation, report tampering and disabled process execution. The symlink test is skipped when the Windows account lacks permission to create a link; do not claim complete link/isolation certification from this suite.

Remaining: real process sandbox, code/test execution, dynamic workspace provisioning, revision/branch support, new-file creation, parallel snapshot write coordination, worker-host process supervision, model-driven task planning and production-quality artifact storage/access policies.
