# Skyra Agent Runtime — Product Requirements

## Maintained specification — current status

Updated 2026-10-14. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Planned component. The new model-driven planning/patch engine and skill runtime are not implemented. Existing legacy model adapters do not establish integration with the new durable core.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](../../../docs/ARCHITECTURE.md)
- [Current functionality and implementation boundaries](../../../docs/FUNCTIONALITY.md)
- [Current milestone and verification summary](../../../docs/DEVELOPMENT.md)

Prepared: 2026-10-14. Requirement/design baseline. Use the maintained current-status section above to distinguish implemented work from planned work.

## Product overview

Reusable execution machinery for planner, coding, research, document, review and incident-investigation roles. Skills guide work; durable workers execute it under centrally issued scope and budgets.

## Problem and current baseline

New documentation-only extraction target. Current Jarvis model and tool code may be reused only after contract and behaviour tests.

Existing prototypes do not establish production readiness. The objective is a reusable, testable boundary with explicit ownership and verifiable outcomes.

## Target users and goals

Primary users: Skyra owner and authorized employees; consuming applications and delegated agents act under those users' scoped identities. Commercial customers use separately branded products rather than inheriting internal Jarvis privileges.

Success means the capabilities below pass recorded acceptance checks, survive expected failures and expose enough evidence for a human to review the result.

## Core requirements / MVP

- **FR-01:** Versioned SKILL.md packages with required tools, resources and acceptance checks
- **FR-02:** Progressive loading of skill metadata and task-relevant content
- **FR-03:** Online model adapters for tool calling, structured output, vision and streaming
- **FR-04:** Persistent agent checkpoints and resumable task execution
- **FR-05:** Scoped child-task delegation with bounded concurrency and cancellation
- **FR-06:** Explicit planning/review/verification roles with shared task contracts
- **FR-07:** Token/cost accounting and capability-compatible provider fallback
- **FR-08:** Evaluation datasets for tool selection, permissions, recovery and completion claims

## Boundaries

This project delivers its declared capabilities only. No automatic production release, account creation, purchase or broader permission is implied by an AI plan. Article-dashboard implementation, ERP, Skyra Platform and QR changes are outside this documentation initiative. Future local models and hosted Jarvis must preserve the same authorization contracts.

## User journey

An authorized caller selects a capability and resource scope, submits validated input, receives either a result or a durable job reference, follows progress and retrieves evidence. Policy may require an exact-action approval before execution. Failures present recovery guidance without claiming success.

## Acceptance and unresolved decisions

See [testing](08_TESTING_AND_ACCEPTANCE.md) for release evidence and [tasks](05_PROJECT_TASKS.md) for implementation sequence.

- LangGraph must pass restart and approval-spike tests before adoption
- Provider retention and usage behaviour vary by account
- A saved procedure is not trained model weights or guaranteed reasoning
