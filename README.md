# Jarvis — Product Monorepo

## Repository components

- [Desktop application](apps/desktop/README.md) — Windows UI and workflow canvas.
- [Agent runtime](packages/agent-runtime/README.md) — model routing, skills and execution.
- [Coding worker](workers/coding/README.md) — isolated development tasks and verification evidence.
- Core/backend — existing Python code remains at its original paths pending a tested packaging migration; core documents are indexed below.

These components share this Git repository but can run as separate processes. The component folders currently contain specifications, not completed applications. See [repository layout](docs/13_REPOSITORY_LAYOUT.md).

An internal, persistent coordinator that turns owner requests into versioned plans, delegated tasks, verified deliverables and reviewable incident fixes. Runs on Windows first; supports remote workers and future hosted operation through explicit migration.

## Current status

Current larger milestone: [trusted native coding workflows](workers/coding/EXECUTION_AND_WORKFLOWS.md) execute real protected tests, apply controller-specified repairs, retest and deliver diffs/evidence. Verification: 71 passed, one OS-dependent symlink test skipped. Native mode requires explicit owner enablement; model-driven patch generation and the new desktop interface remain pending.

2026-10-14: the [durable core](services/core/README.md) and [authenticated local API](services/core/API.md) are implemented; 38 core/API tests pass. They are not yet connected to the existing assistant, desktop or coding executor. See project memory for the current review checkpoint and remaining work.

The [file-worker foundation](workers/coding/IMPLEMENTATION.md) now adds selected-file snapshots and approved file operations through that API. Static checks and checksum evidence are verified; arbitrary code/build/test execution remains disabled. Combined verification: 55 passed, one OS-dependent symlink test skipped.

Existing Python assistant at bd6be5f has voice, Telegram, model failover, memory and direct tool execution. It lacks the target durable task and permission architecture. Inspection found an unimported change_ui_state call, shared conversation history and simulated UI streaming. Earlier syntax checks passed; this is not runtime acceptance.

This documentation describes the target. It does not claim implementation, deployment or passing runtime tests. No source code was changed in the documentation reset.

## Documents

- [Product requirements](docs/01_PRODUCT_REQUIREMENTS.md)
- [System architecture](docs/02_SYSTEM_ARCHITECTURE.md)
- [Development rules](docs/03_DEVELOPMENT_RULES.md)
- [Design system](docs/04_DESIGN_SYSTEM.md)
- [Project tasks](docs/05_PROJECT_TASKS.md)
- [Project memory](docs/06_PROJECT_MEMORY.md)
- [API and event contracts](docs/07_API_AND_EVENTS.md)
- [Testing and acceptance](docs/08_TESTING_AND_ACCEPTANCE.md)
- [Security and operations](docs/09_SECURITY_AND_OPERATIONS.md)

## Ecosystem

[Project boundaries and build order](../skyra-service-contracts/docs/10_ECOSYSTEM_ARCHITECTURE.md).
