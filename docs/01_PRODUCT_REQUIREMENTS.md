# Jarvis Orchestration Core — Product Requirements

## Maintained specification — current status

Updated 2026-10-15. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented and verified: durable core, authenticated local API, selected-file worker, owner-enabled native Windows tests, repair workflows and bounded Gemini/Groq repair proposals with versioned skill context and controller review. Native desktop control, flexible 3D/tabbed/multi-window workspace, model-backed conversation, structured draft planning and setup-readiness guidance are implemented. General autonomous building, a full configuration editor, installer/update delivery and mobile pairing remain pending.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](ARCHITECTURE.md)
- [Current functionality and implementation boundaries](FUNCTIONALITY.md)
- [Current milestone and verification summary](DEVELOPMENT.md)

Prepared: 2026-10-14. Requirement/design baseline. Use the maintained current-status section above to distinguish implemented work from planned work.

## Product overview

An internal, persistent coordinator that turns owner requests into versioned plans, delegated tasks, verified deliverables and reviewable incident fixes. Runs on Windows first; supports remote workers and future hosted operation through explicit migration.

## Problem and current baseline

Existing Python assistant at bd6be5f has voice, Telegram, model failover, memory and direct tool execution. It lacks the target durable task and permission architecture. Inspection found an unimported change_ui_state call, shared conversation history and simulated UI streaming. Earlier syntax checks passed; this is not runtime acceptance.

Existing prototypes do not establish production readiness. The objective is a reusable, testable boundary with explicit ownership and verifiable outcomes.

## Target users and goals

Primary users: Skyra owner and authorized employees; consuming applications and delegated agents act under those users' scoped identities. Commercial customers use separately branded products rather than inheriting internal Jarvis privileges.

Success means the capabilities below pass recorded acceptance checks, survive expected failures and expose enough evidence for a human to review the result.

## Core requirements / MVP

- **FR-01:** Isolated projects, conversations, branches and versioned project specifications
- **FR-02:** Plan-only workflow generating the appropriate project documents before an explicit build instruction
- **FR-03:** Persistent task graphs with delegation, checkpoints, cancellation, restart reconciliation and acceptance evidence
- **FR-04:** Configurable read-only, ask, selected-actions, scoped full-access and custom permission policies
- **FR-05:** Memory Centre for explicit teachings, provenance, revisions, conflict handling and forgetting
- **FR-06:** Skills and capability discovery, online model routing and MCP client integration
- **FR-07:** Mobile commands and approvals through Telegram first; dedicated mobile interface after platform decision
- **FR-08:** Technical and business incident playbooks; known local rules work without model connectivity

## Boundaries

This project delivers its declared capabilities only. No automatic production release, account creation, purchase or broader permission is implied by an AI plan. Article-dashboard implementation, ERP, Skyra Platform and QR changes are outside this documentation initiative. Future local models and hosted Jarvis must preserve the same authorization contracts.

## User journey

An authorized caller selects a capability and resource scope, submits validated input, receives either a result or a durable job reference, follows progress and retrieves evidence. Policy may require an exact-action approval before execution. Failures present recovery guidance without claiming success.

## Acceptance and unresolved decisions

See [testing](08_TESTING_AND_ACCEPTANCE.md) for release evidence and [tasks](05_PROJECT_TASKS.md) for implementation sequence.

- Mobile OS and companion-app approach are unconfirmed
- Production-release policies and per-project budgets require configuration
- Existing memory data needs an explicit non-destructive migration/export plan

## Accepted bounded repair requirement

The first model capability is a repair proposal from explicitly selected source and protected tests. Support both configured Gemini and Groq. A human/controller reviews before handoff; existing task policy governs execution. This does not satisfy general autonomous project building, teaching memory or unattended incident repair.

## Implemented Windows control requirements

Deliver a native internal control centre with an n8n-style subsystem map, clear unavailable states and exact-action review. This slice covers project/policy selection, repair proposals, approval inbox, coding checkpoints/evidence, durable conversation display and activity. It does not yet provide autonomous project generation, automatic chat replies, workflow authoring, mobile pairing or connected third-party services.

## Conversation and draft planning

Online conversation and draft planning are implemented as distinct modes alongside local notes. The owner explicitly chooses a registered provider/model. Plans contain requirements, deliverables, ordered phases/tasks/acceptance, risks and open questions. This does not authorize execution or claim that files, builds or deployments were completed. A coding worker is optional for chat/planning.

## Flexible 3D workspace

The Windows workspace now presents Jarvis as an interactive 3D CSS core alongside the existing subsystem workflow map. Owners can keep up to eight tabs per window, minimize/restore/reorder them, and open built-in panels in up to eight additional native windows. Windows support independent movement between monitors, edge resizing, explicit width/height, minimize, maximize and fullscreen. Core, map, conversations, coding, approvals and other built-in panels remain representations of current capabilities, not new agent permissions.
