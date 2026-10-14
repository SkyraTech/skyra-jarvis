# Jarvis Orchestration Core — Product Requirements

Prepared: 2026-10-14. Status: proposed implementation baseline. User requirements are captured here; technical choices remain subject to implementation validation.

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
