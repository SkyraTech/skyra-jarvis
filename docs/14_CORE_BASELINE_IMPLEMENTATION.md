# Security and core baseline — implementation record

Date: 2026-10-14. This is a first implementation slice, not completion of the entire Jarvis core phase.

## Local Git hygiene

- Removed embedded HTTP credentials from origin URL configuration in Jarvis, browser, vision, GitHub, Google and social repositories. No push, commit, remote repository change or history rewrite performed.
- Removed `config/api_keys.json` and `memory.json` from Jarvis's index using cached removal. Both original files remain on disk with verified unchanged content. Their removals are staged; other work was not bulk-staged.
- Added ignore rules for private configuration, environment overrides and core runtime databases. Added a credential-free API-key configuration example; model names must be deliberately configured.
- Revocation/rotation of the exposed GitHub token remains required. A clean remote URL does not revoke a credential. Prior commits still contain the previously tracked files; publication remains blocked on a separate redacted history/secret review and any required remediation.

## New implementation

[Core module and integration contract](../services/core/README.md) describes the standard-library SQLite implementation. Projects, conversations, tasks, policy checks, approvals, events, leases and reconciliation are implemented and tested in isolation.

The existing assistant and its tools still follow their existing execution paths. They have not acquired the new policy enforcement merely because this module exists. Do not expose the legacy assistant to remote users or describe its tools as protected by this new module.

## Verification

Command: `python -m unittest discover -s services/core/tests -v` from the Jarvis repository root. Tests cover cross-actor denial, conversation isolation, durable messages/approvals, idempotency, policy revisions, scoped full access, approval expiry/replay, lease ownership, interrupted work, cancellation uncertainty and transactional rollback.

The initial sandbox run failed because Windows blocked access to temporary SQLite files. The same suite was rerun with approved permissions. Runtime dependencies were not installed and no existing user data was migrated. Test outcomes are recorded in project memory after execution.

Final result: **19 tests passed**. This validates the isolated state/policy module, not a complete running agent or operating-system sandbox.

## Next slice

Build an authenticated local control API around this core, with trusted approval/policy administration separated from model tools. Then connect one isolated read/edit/test worker. Add real artifact checks and end-to-end permission tests before connecting the legacy UI or any autonomous execution.
