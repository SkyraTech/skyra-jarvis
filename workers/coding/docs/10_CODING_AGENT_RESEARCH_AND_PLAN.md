# Coding agent: research, performance architecture and proof plan

Research date: 2026-10-14. Status: proposed design; no implementation or comparative benchmark has been run. This extends the coding-worker requirements. The complete coding agent combines Jarvis core, agent runtime, coding worker and quality verification; the worker alone is not the agent.

## Public evidence

| Tool | Documented mechanism | Design lesson |
|---|---|---|
| Claude Code | An iterative context/action/verification loop, extended by skills, hooks, MCP and subagents. | Build a reliable tool loop and explicit context management before multiplying specialists. |
| Codex | App Server provides a bidirectional protocol, threads/turns, streamed notifications and approval requests. | Separate the execution engine from desktop/mobile presentation; represent progress as typed events. |
| OpenCode | Headless HTTP server, OpenAPI-generated SDK and event streams; optional language-server diagnostics. | A coding engine can serve several clients. Enable code intelligence according to measured usefulness. |
| Antigravity | Agent tools, parallel conversations and reviewable artifacts including plans, diffs and browser recordings. | Make intermediate deliverables inspectable and connect visual verification to the task. |
| Cursor | Its published fast-apply research describes a specialized edit model and speculative decoding. | Edit application can be optimized separately from reasoning; custom inference performance is not automatically available through ordinary model APIs. |

These sources establish public behavior and selected architectural details, not complete private internals. Cursor's article is historical research, not a current universal speed benchmark. No claim that Jarvis already matches or exceeds these tools is justified.

Sources: [Claude Code architecture](https://code.claude.com/docs/en/how-claude-code-works), [Codex App Server](https://learn.chatgpt.com/docs/app-server), [OpenCode server](https://opencode.ai/docs/server/), [OpenCode LSP](https://opencode.ai/docs/lsp/), [Antigravity agents](https://antigravity.google/docs/agent/), [Antigravity artifacts](https://antigravity.google/docs/artifacts), [Cursor fast-apply research](https://cursor.com/blog/instant-apply).

## Product objective

Optimize time to a correct, verified change on Skyra's actual projects, with dependable permissions, low supervision and resumability. General superiority over every competing tool is an aspiration, not an initial acceptance criterion. Skyra-specific knowledge and service integration are useful differentiation, but still require evaluation.

Required modes: Ask (read-only), Plan (documents and reviewable implementation plan), Build (authorized edits and tests), Debug (reproduce and fix), Review (inspect without edits unless requested). Permission policy is separate from mode. Fast, balanced and thorough execution profiles adjust effort and verification scheduling without bypassing security or required release checks.

## Architecture inside the proposed Jarvis monorepo

```text
Desktop / mobile client
        |
Jarvis core: identity, projects, runs, approvals, events, memory
        |
Agent runtime: model adapters, context, skills, coding loop
        |
Coding worker: scoped files, search, patches, Git, processes
        |
Quality: independent evidence and required release checks
```

Desktop and runtime are separate responsibilities, not necessarily separate repositories. A proposed consolidation places desktop under apps/desktop, core under services/core, runtime under packages/agent-runtime and coding under workers/coding. Subsequent repository organization moved desktop, runtime and coding specifications into these locations; existing executable core code remains at its original paths. Do not create another top-level coding-agent project.

Avoid routing every local file read through several remote services. Use direct typed calls within a process and authenticated local IPC across the execution boundary. Keep an API boundary for remote workers. Native operations run hidden on Windows, with captured output visible in Jarvis when requested.

Retain the proposed Python runtime/worker and TypeScript desktop initially. Use mature search and Git tools; add Rust code only for native integration or a measured bottleneck. Changing language does not by itself reduce model latency or unnecessary reasoning rounds.

## Performance requirements

1. **Persistent execution:** keep model HTTP connections and useful workspace services warm. Bound idle resource usage; a persistent process does not mean continually calling a model.
2. **Focused context:** start with repository instructions, task scope, Git status and targeted searches. Use ripgrep, symbol lookup and optional syntax indexes. Invalidate caches by file content/version. Never treat an old index as current evidence.
3. **Selective memory:** retrieve relevant verified conventions and decisions with provenance. Keep conversational history separate from code facts. Load skill bodies and tool schemas on demand rather than attaching all integrations to every request.
4. **Adaptive models:** select a model/effort profile using measured task complexity and outcomes. Allow manual override. Avoid a routing model call for every trivial action. Do not silently switch providers when data-sharing policy forbids it.
5. **Reliable edits:** support exact replacements and patches with expected-content hashes; reject stale edits. Preserve encoding/newlines and user modifications. Choose edit formats per model using evaluations, not an assumption that one format is always best. Never apply incomplete streamed tool arguments.
6. **Concurrent independent work:** batch independent reads and checks. Delegate only genuinely separable tasks. Use worktrees and file ownership to prevent competing edits; worktrees are not security sandboxes. Integrate changes and rerun affected checks before completion.
7. **Early diagnostics:** run fast syntax/type/targeted tests after coherent edits; run required broader checks before claiming completion. Reuse build caches only with valid dependency/environment keys. Expand testing when impact is uncertain.
8. **Honest streaming:** stream text, tool start/finish, diffs and test progress promptly. Separate local acknowledgement from first useful model response. Throttle rendering of high-volume logs without discarding stored evidence.
9. **Crash recovery:** persist task intent/checkpoints, reconcile pending effects after restart and propagate cancellation to child processes. Scope any retry to known-safe operations; interrupted pushes or external publications need reconciliation.
10. **Measure the bottleneck:** trace retrieval, model queue/first-token/generation, tool duration, approval waits, tests and UI rendering. Report approval time separately from machine execution time.

These are proposed engineering choices. General API guidance supports reducing unnecessary requests/output, parallelizing independent steps and using deterministic code where appropriate: [OpenAI latency optimization](https://developers.openai.com/api/docs/guides/latency-optimization).

## Differentiation worth building

- Repository-specific skills describing actual Skyra standards, with positive and negative test fixtures.
- Requirement → task → code diff → test evidence → release candidate traceability.
- Recoverable multi-hour work with desktop/mobile steering and explicit state when a worker is offline.
- Reusable Google, messaging, social and document service access under the same policy.
- Incident reproduction and regression evidence before proposing a production fix.
- Project memory that can be inspected, corrected and forgotten; no automatic promotion of every model guess to a durable fact.

Do not add a planner, critic and reviewer model call to every small edit. Use deeper review for ambiguity, consequential changes or failed verification. Independent tests are stronger evidence than agreement between agents alone.

## Benchmark and acceptance plan

Build a versioned evaluation set of at least 30 tasks spanning small edits, multi-file features, unfamiliar-code discovery, failing tests, refactors and browser-visible fixes. Use approved fixtures or isolated snapshots, not live customer operations. Keep holdout tasks separate from optimization tasks.

For each run, record repository commit, dirty-state policy, tool/model versions, effort, permissions, prompt, provider, network conditions, cache state, elapsed time, token usage and cost. Start each agent on the same snapshot. Use independent acceptance tests and reviewer checks; retain failures and timeouts. Repeat tasks to expose variability. Compare the same model where possible to isolate harness improvements, and compare complete products separately where model equivalence is unavailable.

| Metric | Definition / proposed gate |
|---|---|
| Local responsiveness | Proposed p95 acknowledgement under 150 ms on a documented reference machine; not model answer latency. |
| First useful response | First task-relevant answer/action, excluding canned status messages; baseline and report p50/p95 by task class. |
| First valid edit | First coherent applied change that passes its immediate syntax/format validation. |
| Verified completion | End-to-end duration until independent acceptance passes; primary speed metric. |
| Correctness | Accepted outcomes / all attempted tasks, including failures and timeouts. |
| Efficiency | Cost per accepted task, retries, unnecessary edits and human interventions. |
| Reliability | Recovery/cancellation scenarios pass, stale edits rejected and no duplicate external effects in fault-injection tests. |
| Permission integrity | No unauthorized operation succeeds in the defined adversarial suite. |

A provisional improvement goal is 20% lower median verified-completion time against the selected baseline without lower acceptance rate or higher policy failures; report p95 and confidence/variance as well. This is a target, not a measured promise. If the sample cannot establish an improvement, report that limitation instead of claiming superiority.

## Development sequence

- [ ] CA-01: Build benchmark fixtures, independent tests and trace schema before performance claims.
- [ ] CA-02: Prove one complete read → edit → test → repair → evidence workflow in an isolated Windows-compatible workspace.
- [ ] CA-03: Add streaming, interruption, restart recovery and exact-action policy enforcement.
- [ ] CA-04: Compare targeted search, optional LSP, context caching and edit strategies; retain measured improvements.
- [ ] CA-05: Add model profiles, lazy skills and dependency-aware parallel execution with merge checks.
- [ ] CA-06: Add project-document workflows, browser evidence and service integrations.
- [ ] CA-07: Run repeated held-out comparisons and publish actual strengths, weaknesses and cost/performance results.

Existing coding engines may be evaluated behind replaceable adapters to establish a working baseline quickly. Verify supported interfaces, applicable licenses and authentication constraints before embedding. Jarvis owns task policy and evidence regardless of backend. Choose reuse versus a custom engine from measured results; do not commit to a costly fork based solely on feature lists.
