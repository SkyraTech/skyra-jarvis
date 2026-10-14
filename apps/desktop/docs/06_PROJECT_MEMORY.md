# Jarvis Windows Desktop — Project Memory

## Maintained specification — current status

Updated 2026-10-14. This is one of the nine initial project documents and must be retained and updated in place. Remove only redundant per-work reports; do not replace or delete the initial specification set.

Planned component. No new Tauri application, workflow canvas, installer or tray supervisor has been implemented. The legacy UI is a separate prototype.

The following references hold the detailed current implementation; requirements and proposed designs below must not be read as already built:

- [Current architecture and database design](../../../docs/ARCHITECTURE.md)
- [Current functionality and implementation boundaries](../../../docs/FUNCTIONALITY.md)
- [Current milestone and verification summary](../../../docs/DEVELOPMENT.md)

## Current verification

No component runtime acceptance is claimed by this document restoration. Use the owning project milestone reference above for evidence; it must not be attributed to an unimplemented component.

## Completed work

Initial requirements, architecture, development/design standards, task plan, API direction, testing and security specifications are retained. Implementation remains at the status stated above.

## Pending work and next milestone

- Tauri packaging and Rust toolchain must be proven before UI expansion
- Windows native interactions need tests beyond browser-only Playwright
- Code signing and update distribution ownership are undecided

Follow the component task document and the owning project development tracker. Assign an owner and verify relevant acceptance checks before marking a task complete.

## Maintenance rules

Update this memory for current status, decisions, blockers and next work. Update the other initial documents when their requirements/design/contracts change; keep the detailed implemented database architecture reference aligned with code. Do not generate a new report per task. Git retains historical revisions. The owner stages/commits/pushes manually; the assistant reports a substantial verified milestone and waits for confirmation before proceeding.
