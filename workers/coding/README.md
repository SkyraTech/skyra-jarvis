# Skyra Coding Worker

Repository update (2026-10-14): this component now belongs to `skyra-jarvis` at `skyra-jarvis/workers/coding`. Do not create a separate GitHub repository for `skyra-coding-worker`. Specifications were preserved; implementation is still pending.

Executes scoped repository tasks in isolated workspaces, returns patches and build evidence, and supports implementation, debugging and review without inheriting unrestricted host access.

## Current status

2026-10-14 larger checkpoint: [trusted native execution and durable repair workflows](EXECUTION_AND_WORKFLOWS.md) now support real test → approved patch → retest → diff/evidence. Native mode is explicitly owner-enabled for trusted projects and carries Windows account access. Docker remains optional and unverified locally. The controller supplies plans; model-generated repairs and desktop integration are pending.

2026-10-14: the [file-worker foundation](IMPLEMENTATION.md) is implemented and connected to the core API when a trusted snapshot registry is supplied. It supports selected-file read/search/patch/diff and static Python/JSON checks with evidence. Arbitrary process/test execution remains disabled pending a verified OS/container sandbox.

Started as a documentation-only component. The file worker is now implemented; migration of local shell/Git responsibilities from the legacy assistant/GitHub service remains pending.

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
- [Coding-agent research and performance plan](docs/10_CODING_AGENT_RESEARCH_AND_PLAN.md)

## Ecosystem

[Project boundaries and build order](../../../skyra-service-contracts/docs/10_ECOSYSTEM_ARCHITECTURE.md).
