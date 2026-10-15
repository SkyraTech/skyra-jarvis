# Skyra Agent Runtime — Product Requirements

## Maintained specification — current status

Updated 2026-10-15. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented first repair runtime: explicit Gemini/Groq adapters, bounded selected-file context, versioned trusted skill loading, durable proposals and controller acceptance into tested coding runs. Durable chat and structured draft planning are also implemented without requiring a coding worker. General execution planning, skill discovery, teaching memory and autonomous scheduling remain pending. Legacy adapters remain separate.

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

## Accepted bounded repair requirement

The first model capability is a repair proposal from explicitly selected source and protected tests. Support both configured Gemini and Groq. A human/controller reviews before handoff; existing task policy governs execution. This does not satisfy general autonomous project building, teaching memory or unattended incident repair.

## Conversation and draft planning

Online conversation and draft planning are implemented as distinct modes alongside local notes. The owner explicitly chooses a registered provider/model. Plans contain requirements, deliverables, ordered phases/tasks/acceptance, risks and open questions. This does not authorize execution or claim that files, builds or deployments were completed. A coding worker is optional for chat/planning.
