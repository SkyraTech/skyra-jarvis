# Skyra Agent Runtime — Development Rules

## Maintained specification — current status

Updated 2026-10-14. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Planned component. The new model-driven planning/patch engine and skill runtime are not implemented. Existing legacy model adapters do not establish integration with the new durable core.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](../../../docs/ARCHITECTURE.md)
- [Current functionality and implementation boundaries](../../../docs/FUNCTIONALITY.md)
- [Current milestone and verification summary](../../../docs/DEVELOPMENT.md)

Prepared: 2026-10-14. Requirement/design baseline. Use the maintained current-status section above to distinguish implemented work from planned work.

## General principles

- Implement one acceptance-tested vertical workflow before expanding capability count.
- Keep contracts, implementation and examples consistent. Mock/simulated output is explicitly labelled and cannot pass production acceptance.
- All new agent, API, mobile and MCP integrations must use the same server-side policy checks; legacy integrations are not automatically covered.
- Configuration is validated at startup. Never silently fall back to fake success or a different privileged account.
- Keep changes scoped and reviewable; preserve user files and migrations. No project deletion or mass rewrite without an explicit decision.

## Technology and coding standards

Python, FastAPI, Pydantic, a tested LangGraph release, official provider SDKs and pytest. Local checkpoint storage is namespaced and owned by this worker; orchestration records remain owned by Jarvis.

Use formatter/linter configurations checked into the project; strict TypeScript for new TypeScript modules and typed Python boundaries with validated inputs. Pin reproducible dependencies, commit appropriate lockfiles and document upgrades. Supported versions are selected using upstream release/support information, not copied from old scaffolds. Do not mix package managers without a migration plan.

## Structure and execution rules

Business logic belongs in domain/application modules; provider calls and storage belong in adapters. Validate inputs at every trust boundary. Return structured errors with stable codes and correlation IDs. Use bounded timeouts, cancellation propagation and retry classification. Never log tokens or place secrets in command arguments. Worker commands must use argument arrays and scoped working directories, not interpolated shell strings.

## Changes and completion

Every task links to a requirement and acceptance check. Add meaningful unit/integration/contract tests according to behavior and risk. A passing build alone is insufficient. Update [memory](06_PROJECT_MEMORY.md) with evidence, current blockers and next action. Mark complete only after the stated exit criteria pass; model claims are not test evidence.

## Review and release

Review permissions, tenant boundaries, migrations, failure/retry behavior and logs. Record exact commit, tool versions and checks in release evidence. Production release is a distinct configured permission; creating a candidate or passing tests does not authorize deployment. Approval validity is rechecked immediately before the approved side effect.
