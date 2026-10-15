"""Acceptance-only core: replace all outbound model calls with deterministic fixtures."""
from pathlib import Path
import runpy
import sys

REPO = Path(__file__).resolve().parents[3]
for source in ('services/core/src', 'workers/coding/src', 'packages/agent-runtime/src'):
    sys.path.insert(0, str(REPO / source))
from jarvis_runtime.providers import OnlineProvider
from native_fixture import FixtureProvider

def complete(self, system, context, schema):
    if self.model != FixtureProvider.model:
        raise ValueError('Native test forbids non-fixture providers')
    return FixtureProvider.complete(self, system, context, schema)

OnlineProvider.complete = complete
runpy.run_path(str(REPO / 'services/core/run.py'), run_name='__main__')
