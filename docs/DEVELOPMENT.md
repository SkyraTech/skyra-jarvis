# Jarvis Orchestration Core — Development

Last maintained: 2026-10-14. This is the cross-milestone summary; the initial task and memory documents are also retained and maintained. Keep architecture and implementation decisions in [ARCHITECTURE.md](ARCHITECTURE.md), requirements in [FUNCTIONALITY.md](FUNCTIONALITY.md).

## Current status

Implemented and verified: durable core, authenticated local API, selected-file worker, owner-enabled native Windows test execution and controller-supplied repair workflows. New desktop and model-generated repairs are not yet implemented.

## Completed major milestones

| Milestone | Evidence | Status |
|---|---|---|
| Durable core and scoped policy | Persistence, approvals, leases, state/event rollback tests | Implemented |
| Authenticated local API | Controller/agent/worker separation, request boundaries, migration tests | Implemented |
| Selected-file operations | Scope/stale/hash/evidence tests; original source preserved | Implemented |
| Trusted native repair workflow | Real failing baseline, approved patch, passing retest and diff; Job Object cleanup | Implemented |

Latest code verification: 38 core/API tests and 33 worker/execution/workflow tests passed; one symlink test skipped because the Windows account could not create it. Docker behavior has contract tests only, not live engine verification. HTTPX/Starlette TestClient deprecation remains known. Current consolidation is a documentation change, not new runtime acceptance.

```powershell
.\venv\Scripts\python.exe -m unittest discover -s services/core/tests -v
.\venv\Scripts\python.exe -m unittest discover -s workers/coding/tests -v
```

## Next major milestone

- [ ] Model-driven planning and patch generation with controlled provider access.
- [ ] Structured skills/context retrieval and evaluation tasks; measure time to verified completion.
- [ ] Windows control interface connected to core, approvals, runs and artifacts.
- [ ] Preserve interruption/restart and explicit native-access labels through integration.

## Remaining product phases

- [ ] New curated teaching memory, provenance/revisions/forgetting and specification binding.
- [ ] Employee roles, selected/custom grants and OS-protected credential provisioning/rotation.
- [ ] Hidden desktop supervisor/tray/install/update behavior and secure mobile pairing.
- [ ] Real isolated backend verification, branch/revision/new-file delivery and parallel conflict handling.
- [ ] Google/document, messaging/social and media workflows with provider-side evidence.
- [ ] Quality/incident integrations and hosted migration/backup recovery.

The owner revoked the earlier exposed token. Current local remotes are clean; config/memory were untracked without deleting local data. Historical secret review remains a separate task. Do not restage runtime data or credentials.

## Development and review rules

- Scope changes to a requirement and meaningful acceptance evidence. Keep providers/storage in adapters and policy outside model logic.
- Prefer reproducible dependency/formatter/type-check configuration. Validate versions before upgrades; no rewrite merely for language uniformity.
- Use structured errors, bounded timeouts, cancellation and retry classification. Label mocks explicitly; they cannot establish production acceptance.
- Review scope, migrations, credentials, failure/recovery behavior and logs. Model agreement is not independent verification.
- Keep product-owned tests with the product. Quality tools aggregate evidence; they do not replace tests with a coverage percentage.
- Do not stage, commit or push. The owner reviews and commits manually. Complete a substantial milestone, inspect Git status/diffs, provide one appropriate commit message, and wait for owner confirmation before the next milestone.
- Update the initial nine project documents and these current implementation references in place as relevant. Add architecture decisions/change rows here or in architecture; do not create per-task Markdown reports. Detailed execution artifacts belong in runtime storage and Git retains document history.

## Documentation checkpoint

2026-10-14: initial specifications are retained alongside consolidated current architecture/functionality/development references; only redundant per-work reports are removed. Current vs proposed schema/capabilities are separated. No application code or runtime data changed by consolidation.

## Initial specification set

Retain and update the original nine documents. They describe product requirements, system architecture, development rules, design, tasks, memory, API/events, testing/acceptance and security/operations. These current overview files supplement them; they do not replace them.

- [Product requirements](01_PRODUCT_REQUIREMENTS.md)
- [System architecture](02_SYSTEM_ARCHITECTURE.md)
- [Development rules](03_DEVELOPMENT_RULES.md)
- [Design system](04_DESIGN_SYSTEM.md)
- [Project tasks](05_PROJECT_TASKS.md)
- [Project memory](06_PROJECT_MEMORY.md)
- [API and event contracts](07_API_AND_EVENTS.md)
- [Testing and acceptance](08_TESTING_AND_ACCEPTANCE.md)
- [Security and operations](09_SECURITY_AND_OPERATIONS.md)
