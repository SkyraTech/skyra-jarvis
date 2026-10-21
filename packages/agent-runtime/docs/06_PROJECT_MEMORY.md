# Skyra Agent Runtime — Project Memory

## Maintained specification — current status

Updated 2026-10-15. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Implemented first repair runtime: explicit Gemini/Groq adapters, bounded selected-file context, versioned trusted skill loading, durable proposals and controller acceptance into tested coding runs. Durable chat and structured draft planning are also implemented without requiring a coding worker. General execution planning, skill discovery, teaching memory and autonomous scheduling remain pending. Legacy adapters remain separate.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](../../../docs/ARCHITECTURE.md)
- [Current functionality and implementation boundaries](../../../docs/FUNCTIONALITY.md)
- [Current milestone and verification summary](../../../docs/DEVELOPMENT.md)

## Current verification

Runtime acceptance now includes deterministic policy/context/restart tests and real online Gemini/Groq fixture repairs followed by native Windows baseline failure, patch, passing retest and diff. This verifies bounded repair integration only; broader agent capabilities remain planned.

## Completed work

Initial requirements, architecture, development/design standards, task plan, API direction, testing and security specifications are retained. Implementation remains at the status stated above.

## Pending work and next milestone

- LangGraph must pass restart and approval-spike tests before adoption
- Provider retention and usage behaviour vary by account
- A saved procedure is not trained model weights or guaranteed reasoning

Follow the component task document and the owning project development tracker. Assign an owner and verify relevant acceptance checks before marking a task complete.

## Maintenance rules

Update this memory for current status, decisions, blockers and next work. Update the other initial documents when their requirements/design/contracts change; keep the detailed implemented database architecture reference aligned with code. Do not generate a new report per task. Git retains historical revisions. The owner stages/commits/pushes manually. Continue authorized development without routine commit checkpoints; do not supply commit messages unless requested. Ask only when a material uncertainty requires owner input.

## Current repair milestone memory

Completed 2026-10-14: bounded model proposals, skill context, schema 6, controller review and tested native handoff. Live Gemini 3.5 Flash Lite and Groq Qwen 3.8 27B repairs reached ready_for_review with original source intact. Earlier Gemini 2.5 calls failed HTTP 404; no silent fallback/retry. Detailed counts, evidence and limitations are in the owning development tracker. Pending: Windows control UI, general builder, teaching memory and scheduling. No staging, commits or pushes performed by the assistant.

## Conversation and draft planning

Current conversation/planning status: schema 7, deterministic tests and live Gemini chat/Groq draft-plan checks implemented. A Groq schema-prompt issue was caught by the live probe and corrected; failed requests remain terminal. Exact native release proof and full counts live in the owning development tracker. No staging, commits or pushes. Next: trusted configuration editing and explicit plan-to-build handoff.


## Versioned specification workflow - 2026-10-15

RepairRuntime.create accepts an optional approved specification ID. The same-project version/checksum/documents are embedded in immutable model context and included under the existing context-size limit. Approval freshness is checked before generation, after provider completion and at acceptance; supersession blocks pending handoffs. Publication is an offline Core operation sourced from completed planning turns. General new-file builds remain pending. Exact schema, endpoints and verification are maintained in the owning Jarvis ARCHITECTURE.md and DEVELOPMENT.md.


## Specification revision and delivery - 2026-10-15

Owner-authored revisions preserve immutable document history and parent provenance through Core schema 9. Reviewed approved bundles can be exported through a bounded native command into a dedicated version folder, with no path/content authority in the renderer. Repair context freshness still checks approved version identity; general building remains pending. Exact revision/export contracts, limits, native storage and verification are maintained in the owning Jarvis ARCHITECTURE.md and DEVELOPMENT.md.


## Reviewed new-file coding - 2026-10-15

Registered workspaces may contain explicit absent creation targets. Proposal context/review identifies these targets and full proposed file content. The existing controller acceptance, resource grants, protected tests and exact action policy still apply. Freshness checks reject unexpected files, and exclusive creation prevents overwrite. The current workflow requires pre-existing protected tests and a failing baseline; general greenfield building remains pending. See the owning ARCHITECTURE.md and DEVELOPMENT.md for the exact manifest/API contracts and current verification.


## Coding-agent foundation - 2026-10-16

Additive feature mode is implemented through durable build jobs, proposal context and guarded run plans, with desktop mode selection and fresh consent on mode changes. Selected-snapshot inventory and bounded line-read tools are implemented in the coding worker. Session audit confirms retained chat messages/model turns and separately retained coding execution history; unified conversational coding sessions remain pending. See the root ARCHITECTURE.md/FUNCTIONALITY.md and DEVELOPMENT.md for exact boundaries and verification. Final foundation verification passed: 321 regression checks plus one existing skip and full native acceptance in .runtime/desktop-native-1792135557383/review.json (zero live model calls). Broader repository discovery, arbitrary new paths, governed dependency tooling and three real supervised projects are not yet delivered.

## Coding provenance boundary

Core schema 15 links explicitly associated jobs to conversations. RepairRuntime input construction is unchanged: chat history is not silently included in coding model context. A regression marker verifies that stored conversation text is absent from deterministic provider input. This association is not context compaction or autonomous memory.

Final conversation-history acceptance passed: schema 15; 331 regression checks plus one existing skip; .runtime/desktop-native-1792146653029/review.json; frontend /assets/index-CIQju6OR.js. Conversation/job/test/delivery/generation provenance recovered through the actual native app after restart. No live provider calls or automatic history injection into model context. Full executable hash and earlier failures are recorded in root DEVELOPMENT.md.

## Retrieval-backed proposal context

RepairRuntime accepts an internal retrieval task reference from the job orchestrator. It validates scoped succeeded read evidence and current candidate/profile hashes, records immutable retrieval provenance in proposal context, and limits patches to files actually supplied. All-source prompt/context size and model-call accounting remain bounded. Unselected or stale omitted candidates cannot authorize edits. This is deterministic local retrieval, not a model-driven tool loop.


Final bounded-retrieval acceptance passed: .runtime/desktop-native-1792148593369/review.json; frontend /assets/index-bVS4q2e9.js. Both repair cycles retained independently verified retrieval evidence, and native history recovered it after restart. See root DEVELOPMENT.md for suite composition (340 distinct passes plus one skip), package hash and remaining limitations. Zero live model calls; no staging, commits or pushes.


Explicit follow-up context: ConversationRuntime can capture a three-job history snapshot on request, freeze it in context, bind inclusion to request identity and verify checksum/scope before provider dispatch. Existing message-history byte budget and paid-call deduplication apply. No schema migration, tool authority or automatic history inclusion. Final verification is recorded in root DEVELOPMENT.md.


Accepted explicit follow-up context package: .runtime/desktop-native-1792150134459/review.json; /assets/index-DzsQwtyN.js. Scoped history/checksum, actual model request and separate execution boundaries passed with zero live model calls. Runtime regression proves immutable snapshot recovery after Core restart. No staging, commits or pushes.


Supervised execution implementation is in progress: explicit long native limits, exact parent/task renewal, deadline/token-loss cleanup, bounded independent background project requests and observed timing display are implemented. Strict model response boundaries are shared. Final acceptance remains pending; see root DEVELOPMENT.md. Schema stays 15; no staging, commits, pushes or live calls.

## Active reliability work — 2026-10-19

Long native supervision and independent project polling are verified, including a real 610-second execution. Host-bound coding edits, safe validation diagnostics and supervised Gemini/Groq foundation trials are implemented; final packaged acceptance passed at .runtime/desktop-native-1792401762949/review.json. Retained provider-generated revisions failed independent corruption checks; a later Gemini foundation passed both protected and independent checks. The task-board application trial is in progress; no full internal product is accepted. Follow root DEVELOPMENT.md for exact evidence and retained failures; root ARCHITECTURE.md owns current contracts. Preserve initial documents and leave all Git staging/commits/pushes to the owner.

## Supervised application checkpoint — 2026-10-19

The task-board evaluation now passes protected and independent browser acceptance after recorded failures/rejections and an agent-authored correction. Explicit Gemini thinking configuration is frozen into request/job context and reported token counts; private thoughts are excluded. Root DEVELOPMENT.md records exact artifacts, 373 composed regression passes plus one existing skip, and limitations. The latest full GUI package remains Bk9XOfBc. General tools/sessions, reusable E2E product integration and Jarvis identity/orb work remain active. No source delivery or product promotion was claimed.

Runtime full 73-test suite passed (13.353s final) after typed incomplete/output-limit handling and validated usage preservation. Rejected responses never create partial patches/messages or trigger replay after restart. Explicit build recovery is a separate controller action with original budgets and exact provenance; automatic retry/backoff remains unimplemented. See root DEVELOPMENT.md.

Final runtime full 75 passed (12.299s). Added explicit data-contract-validation 1.1.0 and scoped hash-bound architecture review for synthetic E2E target development. Five new provider attempts bring retained total to 22. Gemini medium generated and refactored a target/guard foundation that passed strict compilation, nine protected tests and independent checks. Groq behavior/compiler failures and Gemini high output-limit evidence remain retained. No supervisor edits to generated implementation, model-weight training, product promotion or broad model superiority claim. See root DEVELOPMENT.md for exact identities/metrics.
