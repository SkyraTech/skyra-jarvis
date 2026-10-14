# Jarvis — Functionality

Last maintained: 2026-10-14. This is the canonical project requirement/capability reference. Current implementation and planned work are explicitly distinguished.

## Product and users

An internal, persistent coordinator that turns owner requests into versioned plans, delegated tasks, verified deliverables and reviewable incident fixes. Runs on Windows first; supports remote workers and future hosted operation through explicit migration.

Users: Skyra owner and authorized employees; service consumers act under scoped user/project/account identity. Commercial products stay independent of internal Jarvis privileges.

## Current implementation

Implemented and verified: durable core, authenticated local API, selected-file worker, owner-enabled native Windows test execution and controller-supplied repair workflows. New desktop and model-generated repairs are not yet implemented.

## Required capabilities

- Isolated projects, conversations, branches and versioned project specifications
- Plan-only workflow generating the appropriate project documents before an explicit build instruction
- Persistent task graphs with delegation, checkpoints, cancellation, restart reconciliation and acceptance evidence
- Configurable read-only, ask, selected-actions, scoped full-access and custom permission policies
- Memory Centre for explicit teachings, provenance, revisions, conflict handling and forgetting
- Skills and capability discovery, online model routing and MCP client integration
- Mobile commands and approvals through Telegram first; dedicated mobile interface after platform decision
- Technical and business incident playbooks; known local rules work without model connectivity

## Implemented capability matrix

| Area | Available behavior | Limit |
|---|---|---|
| Projects/conversations | Owner-scoped durable state, separate histories, idempotent messages | Employee roles and new chat UI pending. |
| Permissions | Controller/agent/worker credentials; read-only/ask/scoped full; exact approvals | Custom/selected grants and OS credential-store integration pending. |
| File work | Read/search/patch/diff/static checks on selected snapshots | No automatic source application, new-file creation or branch/revision delivery. |
| Native tests | Fixed owner-enabled profiles, real outputs, timeout/cancel/ordinary child cleanup | Trusted code runs with Windows account access. |
| Repair runs | Controller plan, baseline failure, approved patch, protected retest, diff/evidence | No model-generated patches or general autonomous builder yet. |
| Mobile/voice | Legacy Telegram/voice prototype | New authenticated core/desktop is not wired to it. |
| Persistent teaching | Legacy memory prototype | Curated teaching revisions, provenance and deletion are planned. |

## Jarvis Windows Desktop requirements

- Installable Windows application with system tray, explicit Quit and optional sign-in autostart
- No visible console windows for background runtime, worker, update or recovery launches
- Subsystem canvas showing capabilities, connection readiness and permission scope
- Live runs with task dependencies, artifacts, evidence and drill-down diagnostics
- Conversation browser, Memory Centre, approvals inbox and incident timeline
- Pairing and management of mobile clients; visible online/offline status
- Accessible keyboard navigation and a list alternative to the canvas
- Restart/reconnect without duplicated commands or lost pending user input

## Skyra Agent Runtime requirements

- Versioned SKILL.md packages with required tools, resources and acceptance checks
- Progressive loading of skill metadata and task-relevant content
- Online model adapters for tool calling, structured output, vision and streaming
- Persistent agent checkpoints and resumable task execution
- Scoped child-task delegation with bounded concurrency and cancellation
- Explicit planning/review/verification roles with shared task contracts
- Token/cost accounting and capability-compatible provider fallback
- Evaluation datasets for tool selection, permissions, recovery and completion claims

## Skyra Coding Worker requirements

- Repository registration and isolated workspaces per run
- Read/search/edit/patch capabilities restricted to granted workspaces
- Explicit branch/base revision and selected-file change delivery
- Process supervision, timeouts, cancellation and process-tree cleanup
- Build/test execution with captured outputs and resource metrics
- Structured diffs, test artifacts and reproducible environment manifests
- Separate release/deployment actions governed by policy

## Implemented local API

Task payload operations: `read(path)`, literal `search(query)`, `patch(path, expected_sha256, old, new)`, `diff`, static `verify`, and configured `test(profile)`. Operation/action consistency is enforced (`read`, `write`, `execute`). Profiles cannot be replaced with model-supplied shell strings. Messages, tasks and repair-run creation require request IDs in their current API schemas. Unknown fields and coerced values are rejected.

Repair-run creation requires `resource`, `profile`, `request_id` and 1–10 patches with `path`, `expected_sha256`, `old`, `new`. It is controller-only. Worker advance processes one step, preserves approval pauses and uses exact task-bound evidence. Statuses include planned/running/waiting approval/blocked/failed/cancelled/ready for review. Project/conversation creation still lacks request deduplication; clients must not blindly retry an unknown creation outcome.

All routes require authenticated local clients; role/scope rules are in architecture.

| Method | Route |
|---|---|
| GET | `/v1/health` |
| GET | `/v1/openapi.json` |
| POST | `/v1/projects` |
| GET | `/v1/projects` |
| PUT | `/v1/projects/{project}/policy` |
| POST | `/v1/projects/{project}/conversations` |
| POST | `/v1/conversations/{conversation}/messages` |
| GET | `/v1/conversations/{conversation}/messages` |
| POST | `/v1/projects/{project}/tasks` |
| GET | `/v1/tasks/{task}` |
| POST | `/v1/tasks/{task}/start` |
| POST | `/v1/tasks/{task}/heartbeat` |
| POST | `/v1/tasks/{task}/perform` |
| GET | `/v1/workers/capabilities` |
| POST | `/v1/projects/{project}/coding-runs` |
| GET | `/v1/projects/{project}/coding-runs` |
| GET | `/v1/coding-runs/{run}` |
| POST | `/v1/coding-runs/{run}/advance` |
| POST | `/v1/coding-runs/{run}/cancel` |
| GET | `/v1/tasks/{task}/evidence/{checksum}` |
| POST | `/v1/tasks/{task}/complete` |
| POST | `/v1/tasks/{task}/cancel` |
| GET | `/v1/approvals/{approval}` |
| POST | `/v1/approvals/{approval}/decision` |
| POST | `/v1/projects/{project}/recover` |
| POST | `/v1/tasks/{task}/reconcile` |
| GET | `/v1/projects/{project}/events` |

Core developer input schemas live in `services/core/src/jarvis_core/api.py`; generated OpenAPI is controller-only at `/v1/openapi.json`. Do not maintain a conflicting handwritten schema.

## Desktop design requirements — proposed

Dedicated Jarvis design; do not import Skyra Platform UI. Proposed tokens: background #0B1220, surface #111C2F, raised surface #1B2940, primary text #F3F6FC, secondary text #B9C5D8, accent #75B8FF, success #72D6A0, warning #FFD166, error #FF8F9A. Verify contrast in actual component states before adoption.

Use Segoe UI/system sans for interface and Cascadia Code/system monospace for code. Type sizes: 12 metadata, 14 controls, 16 body, 20 section, 28 page title. Spacing scale: 4/8/12/16/24/32/48 px; 8 px control radius and 12 px panels. Focus rings remain visible; never encode status using color alone.

Primary shell: navigation rail, central subsystem/workflow canvas, inspector, conversation panel and approval inbox. A node shows name, available capability, readiness, current task and permission scope. Edges describe actual dependencies, not decorative activity. Provide zoom, fit, keyboard selection, searchable list alternative, minimap and reduced motion. Inspector exposes evidence/artifacts without exposing credentials.

Approval cards show exact action, target, account, cost/risk when known, expiry and scope. Changed actions require a fresh decision. Destructive decisions cannot be the default focused action. Mobile layouts prioritize approvals, run status and cancellation over editing large graphs.

## Interface direction

## Acceptance requirements

- Two simultaneous conversations cannot read each other's private context
- Restart while waiting for approval preserves the pending action without executing it
- A changed proposed action invalidates an earlier approval
- An interrupted external operation is reconciled before a retry
- Plan mode does not begin implementation; build mode binds to a reviewed specification version
- A taught fact can be inspected, revised and forgotten, including its derived search entries
- A disconnected PC is reported unavailable on mobile; jobs are not falsely marked running
- Stopping a workflow cancels descendants and records workers that did not acknowledge

## Explicit boundaries and open decisions

- Mobile OS and companion-app approach are unconfirmed
- Production-release policies and per-project budgets require configuration
- Existing memory data needs an explicit non-destructive migration/export plan

A proposal, simulation or passing build does not authorize production release. Account connection, publication, money movement and employee/payroll actions obey their configured permission policies.

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
