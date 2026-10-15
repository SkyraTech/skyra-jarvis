# Skyra Agent Runtime

Component of `skyra-jarvis`. Implemented first repair runtime: explicit Gemini/Groq adapters, bounded selected-file context, versioned trusted skill loading, durable proposals and controller acceptance into tested coding runs. Durable chat and structured draft planning are also implemented without requiring a coding worker. General execution planning, skill discovery, teaching memory and autonomous scheduling remain pending. Legacy adapters remain separate.

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

## Runtime and configuration

Sources: `src/jarvis_runtime`; tests: `tests/test_runtime.py`. Configure the core launcher with `--runtime-config` and a private copy of [config.example.json](config.example.json), plus a trusted workspace registry. Keys must already be in explicitly named environment variables; the server does not auto-load `.env`.

Run offline tests from the Jarvis repository root:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s packages/agent-runtime/tests -v
```

The optional `live_demo.py` requires explicit provider/model/key-env/new-directory and `--allow-live-call`. `--env-file` explicitly enables existing legacy environment-file loading (requires python-dotenv already used by the legacy project). It sends only generated fixture data and auto-accepts that fixture. Online providers may charge even if generation fails validation. Full usage, schema and boundaries are maintained in the owning architecture/functionality/development documents.

## Conversation runtime

ConversationRuntime uses the same explicit provider adapter, without requiring a FileWorker. It persists one active request per conversation, a bounded history/schema/instruction snapshot, exact provider/model, usage, safe errors and validated chat or draft-plan responses. Core owns readable records/interruption even without active providers. Generating/terminal turns are never retried automatically. Plans do not create execution tasks.

The optional conversation_demo.py requires explicit provider/model/mode/key environment name, a new evidence directory and --allow-live-call. It makes one paid request with generated fictional context only and records JSON/SQLite evidence. Production secrets are never printed; raw provider failures are withheld. This probe does not provision real application credentials.
