# Jarvis Orchestration Core — Development Rules

Prepared: 2026-10-14. Status: proposed implementation baseline. User requirements are captured here; technical choices remain subject to implementation validation.

## General principles

- Implement one acceptance-tested vertical workflow before expanding capability count.
- Keep contracts, implementation and examples consistent. Mock/simulated output is explicitly labelled and cannot pass production acceptance.
- All agent, API, mobile and MCP callers go through the same server-side policy checks.
- Configuration is validated at startup. Never silently fall back to fake success or a different privileged account.
- Keep changes scoped and reviewable; preserve user files and migrations. No project deletion or mass rewrite without an explicit decision.

## Technology and coding standards

Python service; FastAPI/Pydantic; SQLite with migrations and WAL for local state; filesystem artifacts; online provider SDKs via the agent runtime. Hosted PostgreSQL migration is a separately tested future change.

Use formatter/linter configurations checked into the project; strict TypeScript for new TypeScript modules and typed Python boundaries with validated inputs. Pin reproducible dependencies, commit appropriate lockfiles and document upgrades. Supported versions are selected using upstream release/support information, not copied from old scaffolds. Do not mix package managers without a migration plan.

## Structure and execution rules

Business logic belongs in domain/application modules; provider calls and storage belong in adapters. Validate inputs at every trust boundary. Return structured errors with stable codes and correlation IDs. Use bounded timeouts, cancellation propagation and retry classification. Never log tokens or place secrets in command arguments. Worker commands must use argument arrays and scoped working directories, not interpolated shell strings.

## Changes and completion

Every task links to a requirement and acceptance check. Add meaningful unit/integration/contract tests according to behavior and risk. A passing build alone is insufficient. Update [memory](06_PROJECT_MEMORY.md) with evidence, current blockers and next action. Mark complete only after the stated exit criteria pass; model claims are not test evidence.

## Review and release

Review permissions, tenant boundaries, migrations, failure/retry behavior and logs. Record exact commit, tool versions and checks in release evidence. Production release is a distinct configured permission; creating a candidate or passing tests does not authorize deployment. Approval validity is rechecked immediately before the approved side effect.
