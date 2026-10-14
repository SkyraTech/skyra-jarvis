# Skyra Coding Worker — Product Requirements

Prepared: 2026-10-14. Status: proposed implementation baseline. User requirements are captured here; technical choices remain subject to implementation validation.

## Product overview

Executes scoped repository tasks in isolated workspaces, returns patches and build evidence, and supports implementation, debugging and review without inheriting unrestricted host access.

## Problem and current baseline

New documentation-only project. Replaces unsafe local shell/Git responsibilities currently mixed into Jarvis and the GitHub service.

Existing prototypes do not establish production readiness. The objective is a reusable, testable boundary with explicit ownership and verifiable outcomes.

## Target users and goals

Primary users: Skyra owner and authorized employees; consuming applications and delegated agents act under those users' scoped identities. Commercial customers use separately branded products rather than inheriting internal Jarvis privileges.

Success means the capabilities below pass recorded acceptance checks, survive expected failures and expose enough evidence for a human to review the result.

## Core requirements / MVP

- **FR-01:** Repository registration and isolated workspaces per run
- **FR-02:** Read/search/edit/patch capabilities restricted to granted workspaces
- **FR-03:** Explicit branch/base revision and selected-file change delivery
- **FR-04:** Process supervision, timeouts, cancellation and process-tree cleanup
- **FR-05:** Build/test execution with captured outputs and resource metrics
- **FR-06:** Structured diffs, test artifacts and reproducible environment manifests
- **FR-07:** Separate release/deployment actions governed by policy

## Boundaries

This project delivers its declared capabilities only. No automatic production release, account creation, purchase or broader permission is implied by an AI plan. Article-dashboard implementation, ERP, Skyra Platform and QR changes are outside this documentation initiative. Future local models and hosted Jarvis must preserve the same authorization contracts.

## User journey

An authorized caller selects a capability and resource scope, submits validated input, receives either a result or a durable job reference, follows progress and retrieves evidence. Policy may require an exact-action approval before execution. Failures present recovery guidance without claiming success.

## Acceptance and unresolved decisions

See [testing](08_TESTING_AND_ACCEPTANCE.md) for release evidence and [tasks](05_PROJECT_TASKS.md) for implementation sequence.

- Git worktrees alone do not provide process or filesystem isolation
- Windows-native and container execution support different toolchains
- Isolation technology is an implementation gate, not a command-blacklist assumption
