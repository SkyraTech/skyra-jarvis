# Trusted native execution and durable repair workflows

Completed checkpoint: 2026-10-14. The owner explicitly selected native Windows execution for trusted Skyra projects. Docker/remote infrastructure is optional. No software was installed, Git changes staged/committed/pushed, or existing project code executed during verification.

## What works now

The worker can run a fixed test profile on a selected-file execution copy. A durable repair run reproduces a failure, applies controller-specified patches, reruns the same protected test profile, and produces evidence plus a diff. The result is `ready_for_review`, not automatic deployment or a universal production-readiness claim.

Plans are supplied by the controller in this phase. Online-model planning, autonomous patch generation, chat/desktop integration and broader language/toolchain profiles remain separate work. The code/test/repair execution loop itself now runs real processes, rather than just parsing syntax.

## Native mode and supervision

Native execution uses the owning Windows account's privileges. It does not isolate host files, network or other accounts' resources accessible to that account. Selected snapshots keep normal working-copy changes separate, but a program can still deliberately access other host paths. Enable this mode only for trusted projects and approved test profiles.

`NativeExecutor` requires `owner_enabled=True`. Commands use a fixed absolute executable and argument tuple, `shell=False`, a fresh execution copy and a reduced environment. Tokens/API keys are not automatically inherited, but code running under the account can still read files that account can access. Execution output is saved as private local evidence; there is no claim of universal secret redaction.

Windows starts each process suspended and assigns it to a Job Object before resuming it. The job caps total committed memory at 1 GiB and active processes at 64, and kills associated descendants on cleanup. Processes launch without a console window. Wall timeout, cancellation/policy polling and a 256 KiB output cap are enforced. Test-profile tuning and resource settings are implementation defaults, not hardware-capacity assumptions.

Job Objects supervise ordinary child process trees; they are not a security boundary. Trusted programs can invoke OS services that launch unrelated processes outside the job. Unknown cleanup or lost ownership leaves work interrupted and requiring reconciliation. Host crash handling, stronger isolation and service-launched descendants are not certified by these tests.

## Native configuration

Extend the trusted workspace registry passed to `services/core/run.py --workspace-config`:

```json
{
  "evidence_root": "C:/private/jarvis/evidence",
  "workspaces": [
    {
      "project_id": "<existing-project-id>",
      "resource_id": "workspace:run-1",
      "directory": "C:/private/jarvis/prepared-snapshot"
    }
  ],
  "execution": {
    "mode": "native_trusted",
    "owner_enabled": true,
    "profiles": [
      {
        "name": "python-unit",
        "argv": ["C:/path/to/python.exe", "-B", "-m", "unittest", "discover", "-s", "tests", "-v"],
        "protected_paths": ["tests/test_app.py"],
        "timeout": 120
      }
    ]
  }
}
```

This is a template; select real paths and test commands for the trusted project. All test dependencies must already exist in the chosen environment. This worker does not install dependencies automatically. The owner controls profile definitions, protected test paths and backend mode; agents cannot submit executable arguments or alter that registry through the API. Profile changes require a server restart.

Native backend availability and profile names appear in `GET /v1/workers/capabilities`. Individual tests use immutable `{"operation":"test","profile":"python-unit"}` task payloads with action `execute`. They still require the project's policy grant and an exact approval in ask mode.

## Durable repair API

Controller creates `POST /v1/projects/{project}/coding-runs` with:

```json
{
  "resource": "workspace:run-1",
  "profile": "python-unit",
  "request_id": "repair-request-1",
  "patches": [
    {
      "path": "app.py",
      "expected_sha256": "<current-file-hash>",
      "old": "return 41",
      "new": "return 42"
    }
  ]
}
```

Agent/worker credentials cannot create this controller-approved plan. Agents may inspect assigned runs; worker credentials call `POST /v1/coding-runs/{run}/advance`. Each advance handles one step and returns durable progress. With ask policy, execution and writes wait for controller approval through the existing approval API. A host scheduler/native client may call advance again after review; no always-on scheduler was added in this phase.

The sequence is fixed: failing baseline test → 1–10 explicit patches → passing retest using the same profile → diff. Plans cannot patch protected tests. A runtime failure, cancellation, timeout or unknown cleanup does not qualify as the expected initial test failure. Only exact task-bound execution evidence qualifies for the final passing gate. A failed repair stops before `ready_for_review`.

`GET /v1/projects/{project}/coding-runs` discovers the most recent 100 runs. `GET /v1/coding-runs/{run}` returns plan/progress/results; controller cancellation uses `/cancel`. Run creation is idempotent per project/request ID; altered plans with the same key conflict. Only one active run may use a project/resource at a time.

SQLite migrations to schema 5 add execution-attempt ownership, durable run state and request deduplication. A lease cannot dispatch twice, including after reconnect/restart. Unknown effects require reconciliation, not automatic rerun. Checkpoint recovery has been tested between completed steps; active native processes and external side effects after a machine crash still need reconciliation.

## Repeatable demonstration

From the Jarvis root:

```powershell
.\venv\Scripts\python.exe workers/coding/repair_demo.py --directory .runtime/my-new-repair-demo
```

Destination must be new. This runs only a generated trusted fixture, creates its own source/snapshot/database/evidence, and writes `review.json`. It deliberately uses a full-access policy for that generated fixture. Separate API integration tests verify ask/approval behavior.

Verified demonstration: `.runtime/repair-demo-20261014/review.json`, run `8424c00f7f084a079524c31e312e661d`. Baseline failed, patch succeeded, the same unit test passed, and only `app.py` appeared in the diff. Original source remained unchanged. Runtime artifacts are ignored by Git.

## Optional Docker backend

Docker support is prepared but not live-tested on this PC. It requires an already-installed local Linux-container engine, a reviewed image pinned by digest and owner-defined profiles. The adapter forbids automatic image pulling and host-shell fallback. It uses a read-only selected-file mount, no network, dropped capabilities, no-new-privileges, non-root user and resource limits. Cleanup verifies an attempt-specific container label before removing only that container.

Only Docker argument/policy contract tests ran. Container isolation, engine compatibility and real Docker cleanup are not certified until integration tests run against an actual engine. Container creation with an unknown outcome may require operator reconciliation; the implementation never globally prunes containers or other work.

## Verification and next milestone

Core/API: 38 tests passed. Worker/execution/workflow: 34 tests ran, 33 passed and one symlink test skipped due to OS permissions. Total: **71 passed, one skipped**. Real native tests cover pass/fail exit codes, output caps, reduced environment, protected test tampering, timeout child-process cleanup, cancellation, restart checkpoints and the controller/approval API pipeline. The HTTPX test-client deprecation warning remains documented.

Next major milestone: model-driven planning and patch generation through this execution boundary, structured skills/context retrieval and a usable Windows control interface. Preserve native mode labels and permissions; do not silently enable it for unfamiliar repositories.

References: [Windows Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects), [Job memory/process limits](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information), [Docker runtime controls](https://docs.docker.com/engine/containers/run/).
