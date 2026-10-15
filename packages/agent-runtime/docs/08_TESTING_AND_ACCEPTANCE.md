# Skyra Agent Runtime — Testing and Acceptance

## Maintained specification — current status

Updated 2026-10-15. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented first repair runtime: explicit Gemini/Groq adapters, bounded selected-file context, versioned trusted skill loading, durable proposals and controller acceptance into tested coding runs. Durable chat and structured draft planning are also implemented without requiring a coding worker. General execution planning, skill discovery, teaching memory and autonomous scheduling remain pending. Legacy adapters remain separate.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](../../../docs/ARCHITECTURE.md)
- [Current functionality and implementation boundaries](../../../docs/FUNCTIONALITY.md)
- [Current milestone and verification summary](../../../docs/DEVELOPMENT.md)

Prepared: 2026-10-14. Requirement/design baseline. Use the maintained current-status section above to distinguish implemented work from planned work.

## Project acceptance matrix

| ID | Required outcome | Evidence status |
|---|---|---|
| AC-01 | A skill cannot grant itself tools outside the parent task permission envelope | Not executed |
| AC-02 | Fallback refuses models missing required vision, tools or schema capabilities | Not executed |
| AC-03 | A restart resumes from a checkpoint without blindly repeating completed side effects | Not executed |
| AC-04 | Child tasks cannot escape the parent project, budget or resource scope | Not executed |
| AC-05 | Evaluation failures remain failures even if the model claims success | Not executed |
| AC-06 | Provider secrets never enter persisted prompts or tool result logs | Not executed |

## Requirement traceability

Each requirement must receive one or more concrete test IDs. The matrix above captures critical scenarios but does not imply exhaustive feature coverage.

| Requirement | Behavior to verify | Test mapping |
|---|---|---|
| FR-01 | Versioned SKILL.md packages with required tools, resources and acceptance checks | Unassigned; required before implementation completion |
| FR-02 | Progressive loading of skill metadata and task-relevant content | Unassigned; required before implementation completion |
| FR-03 | Online model adapters for tool calling, structured output, vision and streaming | Unassigned; required before implementation completion |
| FR-04 | Persistent agent checkpoints and resumable task execution | Unassigned; required before implementation completion |
| FR-05 | Scoped child-task delegation with bounded concurrency and cancellation | Unassigned; required before implementation completion |
| FR-06 | Explicit planning/review/verification roles with shared task contracts | Unassigned; required before implementation completion |
| FR-07 | Token/cost accounting and capability-compatible provider fallback | Unassigned; required before implementation completion |
| FR-08 | Evaluation datasets for tool selection, permissions, recovery and completion claims | Unassigned; required before implementation completion |

## Test layers

- Unit: domain decisions, policy evaluation, state transitions, parsing and failure classification.
- Contract: input/output examples, error shape, consumer compatibility and event schemas.
- Integration: real isolated storage, adapter behavior, credentials scoping, retries and provider sandbox where available.
- End-to-end: authorized user workflow through actual boundaries; Playwright where a browser/UI is involved and Windows process tests for desktop launches.
- Recovery/security: crash between intent and dispatch, duplicate events, expired leases, denied scopes, cross-tenant attempts, stale approvals and secret redaction.

For package-only projects, independent consumer tests replace server/deployment tests. Provider tests must use approved test accounts; do not send messages, publish content or incur charges against arbitrary live users.

## Release gate

Record commit, tool/dependency versions, test command, environment, timestamps, result and artifact links. All required checks must pass or carry an explicitly reviewed exception. Track line and branch coverage separately; establish project thresholds from the first trustworthy baseline and protect critical paths with direct behavioral tests. A high coverage percentage alone is not acceptance.

Dependency and vulnerability findings are triaged by severity, exploitability and reachability. No unreviewed critical/high finding in the release scope. Active DAST requires an owned, explicitly selected target; baseline scans and active attacks are different operations. Quality runners must isolate untrusted code and cap runtime/resource usage.

The initial documentation pass ran no runtime tests; later implementation evidence is recorded in the current-status references above. Future reports must distinguish simulated providers, local integration and production-like verification.

## Bounded repair acceptance evidence

The runtime suite checks local schema/patch constraints, protected tests, stale hashes/context, policy revocation, model error sanitization, request idempotency, interrupted restart without replay, concurrent single dispatch, late response suppression, atomic handoff rollback, migration preserving conversations, HTTP roles and ask-mode approval preservation. Two live providers produced fixture patches that passed real Windows baseline/repair/retest/diff gates. See the development tracker for exact counts and ignored JSON evidence. These small fixtures do not establish general coding quality, production isolation or superiority to other agents.

## Conversation and draft planning

Acceptance includes provider selection, stored notes, safe text rendering, chat replies/usage, structured plan sections, failure without replay, missing providers, active interruption and late-output suppression. Runtime tests cover migration from schema 6, byte-bounded contiguous history with omission counts, Unicode size rejection, immutable instruction hashes, concurrent single dispatch, restart uncertainty and atomic assistant-message/state writes. Native acceptance uses deterministic providers only; separate explicitly authorized live probes use fictional prompts.
