"""Explicit opt-in online repair fixture. One paid request; no production source or Git edits."""

import argparse
import json
import os
from pathlib import Path
import sys
import time

REPO = Path(__file__).resolve().parents[2]
for source in ('services/core/src', 'workers/coding/src', 'packages/agent-runtime/src'):
    sys.path.insert(0, str(REPO / source))

from jarvis_core import Core
from jarvis_runtime import RepairRuntime, Skill
from jarvis_runtime.providers import OnlineProvider
from skyra_coding import Workspace, FileWorker
from skyra_coding.native import NativeExecutor, NativeProfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True, help='New fixture/evidence directory')
    parser.add_argument('--provider', choices=('gemini', 'groq'), required=True)
    parser.add_argument('--model', required=True)
    parser.add_argument('--api-key-env', required=True, help='Key environment variable name, never its value')
    parser.add_argument('--env-file', type=Path, help='Explicit opt-in legacy environment file; requires python-dotenv')
    parser.add_argument('--allow-live-call', action='store_true', required=True,
                        help='Authorize one online request with generated fixture context only')
    args = parser.parse_args()
    key = os.environ.get(args.api_key_env, '')
    if args.env_file:
        from dotenv import dotenv_values
        key = key or dotenv_values(args.env_file).get(args.api_key_env, '')
    if not key:
        parser.error('Selected environment key is unavailable; value withheld')
    provider = OnlineProvider(args.provider, args.model, key, timeout=45, max_output_tokens=4096)
    root = args.directory.resolve()
    root.mkdir(parents=True, exist_ok=False)
    source = root / 'source'
    source.mkdir()
    (source / 'tests').mkdir()
    (source / 'app.py').write_text('def answer():\n    return 41\n', encoding='utf-8')
    (source / 'tests/test_app.py').write_text(
        'import sys,unittest\nfrom pathlib import Path\nsys.path.insert(0,str(Path(__file__).resolve().parents[1]))\n'
        'from app import answer\nclass AnswerTest(unittest.TestCase):\n    def test_answer(self):self.assertEqual(42,answer())\n', encoding='utf-8')
    workspace = Workspace.snapshot(source, root / 'snapshot', ['app.py', 'tests/test_app.py'])
    profile = NativeProfile('fixture-unit', (sys.executable, '-I', '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v'),
                            ('tests/test_app.py',), 20)
    core = Core(root / 'core.sqlite3')
    try:
        project = core.create_project('fixture-owner', 'Online repair fixture')
        core.set_policy('fixture-owner', project, 'full', ['workspace:fixture'])
        worker = FileWorker({(project, 'workspace:fixture'): workspace}, root / 'evidence',
                            NativeExecutor([profile], owner_enabled=True))
        runtime = RepairRuntime(worker, {args.provider: provider}, [Skill('repair', '1',
            'Inspect source and protected tests. Propose the smallest source repair. Do not edit tests.')])
        proposal = runtime.create(core, 'fixture-owner', project, 'workspace:fixture', profile.name,
            args.provider, 'Fix answer() to satisfy the supplied protected unit test.',
            ['app.py', 'tests/test_app.py'], ['repair'], 'online-fixture')
        started = time.monotonic()
        data = runtime.generate(core, 'fixture-owner', proposal)
        generation_seconds = round(time.monotonic() - started, 3)
        run = None
        if data['state'] == 'ready':
            # This opt-in script accepts generated fixtures only, never arbitrary project changes.
            accepted = runtime.accept(core, 'fixture-owner', proposal)
            for _ in range(len(runtime.workflow.get(core, 'fixture-owner', accepted['run'])['steps'])):
                run = runtime.workflow.advance(core, 'fixture-owner', accepted['run'])
                if run['state'] in {'failed', 'ready_for_review', 'cancelled', 'blocked', 'waiting_approval'}:
                    break
        result = {'provider': args.provider, 'model': args.model, 'proposal_id': proposal,
                  'proposal_state': data['state'], 'generation_seconds': generation_seconds,
                  'usage': data['usage'], 'error': data['error'], 'run_id': run['id'] if run else None,
                  'run_state': run['state'] if run else None, 'steps': run['results'] if run else [],
                  'source_preserved': (source / 'app.py').read_text().endswith('return 41\n'),
                  'mode': 'native_trusted', 'os_isolation': False}
        (root / 'review.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps(result, indent=2))
        if result['run_state'] != 'ready_for_review':
            raise SystemExit(1)
    finally:
        core.close()


if __name__ == '__main__':
    main()
