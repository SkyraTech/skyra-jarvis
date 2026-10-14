# Skyra Agent Runtime — Project Memory

## Maintained specification — current status

Updated 2026-10-14. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Planned component. The new model-driven planning/patch engine and skill runtime are not implemented. Existing legacy model adapters do not establish integration with the new durable core.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](../../../docs/ARCHITECTURE.md)
- [Current functionality and implementation boundaries](../../../docs/FUNCTIONALITY.md)
- [Current milestone and verification summary](../../../docs/DEVELOPMENT.md)

## Current verification

No component runtime acceptance is claimed by this document restoration. Use the owning project milestone reference above for evidence; it must not be attributed to an unimplemented component.

## Completed work

Initial requirements, architecture, development/design standards, task plan, API direction, testing and security specifications are retained. Implementation remains at the status stated above.

## Pending work and next milestone

- LangGraph must pass restart and approval-spike tests before adoption
- Provider retention and usage behaviour vary by account
- A saved procedure is not trained model weights or guaranteed reasoning

Follow the component task document and the owning project development tracker. Assign an owner and verify relevant acceptance checks before marking a task complete.

## Maintenance rules

Update this memory for current status, decisions, blockers and next work. Update the other initial documents when their requirements/design/contracts change; keep the detailed implemented database architecture reference aligned with code. Do not generate a new report per task. Git retains historical revisions. The owner stages/commits/pushes manually; the assistant reports a substantial verified milestone and waits for confirmation before proceeding.
