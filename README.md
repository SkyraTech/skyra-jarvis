# Jarvis

An internal, persistent coordinator that turns owner requests into versioned plans, delegated tasks, verified deliverables and reviewable incident fixes. Runs on Windows first; supports remote workers and future hosted operation through explicit migration.

Implemented and verified: durable core, authenticated local API, selected-file worker, owner-enabled native Windows tests, repair workflows and bounded Gemini/Groq repair proposals with versioned skill context and controller review. Native desktop control, model-backed conversation, structured draft planning and setup-readiness guidance are implemented. General autonomous building, a full configuration editor, installer/update delivery and mobile pairing remain pending.

## Maintained documentation

- [Architecture, database and implementation decisions](docs/ARCHITECTURE.md)
- [Functionality and requirements](docs/FUNCTIONALITY.md)
- [Development status, tasks and verification](docs/DEVELOPMENT.md)

[Repository catalogue](../REPOSITORIES.md).

## Initial project documents — retain and maintain

- [Product requirements](docs/01_PRODUCT_REQUIREMENTS.md)
- [System architecture](docs/02_SYSTEM_ARCHITECTURE.md)
- [Development rules](docs/03_DEVELOPMENT_RULES.md)
- [Design system](docs/04_DESIGN_SYSTEM.md)
- [Project tasks](docs/05_PROJECT_TASKS.md)
- [Project memory](docs/06_PROJECT_MEMORY.md)
- [API and event contracts](docs/07_API_AND_EVENTS.md)
- [Testing and acceptance](docs/08_TESTING_AND_ACCEPTANCE.md)
- [Security and operations](docs/09_SECURITY_AND_OPERATIONS.md)

The native desktop now includes explicit online chat, structured draft project planning and a setup-readiness checklist. Conversations can use configured providers without a coding worker. Plans remain reviewable data; approved plan-to-build handoff and configuration editing are the next development work. See the maintained functionality and development references above.
