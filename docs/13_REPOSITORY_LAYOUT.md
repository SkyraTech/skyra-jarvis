# Jarvis repository layout

Updated 2026-10-14. Local structure consolidated; no runtime code migration or GitHub publication performed.

```text
skyra-jarvis/
  .git/                      Existing repository, preserved
  apps/desktop/              Desktop specifications
  packages/agent-runtime/    Runtime specifications
  workers/coding/            Coding specifications and research
  docs/                      Core/product documents
  main.py                    Existing entry point, unchanged
  core/                      Existing Python modules, unchanged
  services/                  Existing model adapters, unchanged
  tools/                     Existing local/API tools, unchanged
  config/                    Existing runtime configuration, unchanged
  integrations/              Existing Telegram integration, unchanged
  static/                    Existing interface assets, unchanged
```

Do not initialize Git repositories inside apps, packages or workers. Do not move the existing Python files merely to match a proposed tree: imports, static assets, launchers and state paths need a tested migration together. Current launch commands still target the same files.

The previous desktop, runtime and coding-worker top-level folders were moved here with their full documentation, including the coding-agent research plan. No content was discarded. Their historical titles identify component responsibilities, not separate repository requirements.

Shared contracts and foundation packages stay in the independent Service Contracts repository because commercial products also need them. Jarvis uses versioned packages/APIs; it must not make those reusable services depend on its desktop or core.

The [workspace repository catalogue](../../REPOSITORIES.md) records all separate project boundaries. The [ecosystem map](../../skyra-service-contracts/docs/10_ECOSYSTEM_ARCHITECTURE.md) records component interactions. This layout supersedes older separate-folder proposals in component architecture documents.
