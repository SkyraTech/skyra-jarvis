"""Create an isolated native acceptance fixture; no online requests or real project access."""
import argparse
import hashlib
import json
from pathlib import Path
import secrets
import sys

DESKTOP = Path(__file__).resolve().parents[1]
REPO = DESKTOP.parents[1]
sys.path.insert(0, str(DESKTOP))
for source in ('services/core/src', 'workers/coding/src', 'packages/agent-runtime/src'):
    sys.path.insert(0, str(REPO / source))
from bootstrap import initialize, protect
from jarvis_core import Core
from jarvis_runtime import RepairRuntime
from skyra_coding import Workspace, FileWorker
from skyra_coding.native import NativeExecutor, NativeProfile


class FixtureProvider:
    model = 'native-acceptance-fixture'

    def complete(self, system, context, schema):
        data = json.loads(context)
        if data.get('mode') in {'chat', 'plan'}:
            response = {'reply': 'Native fixture response, stored successfully.'}
            if data['mode'] == 'plan':
                response['plan'] = {'title': 'Native client website plan', 'overview': 'Draft for owner review.',
                    'requirements': ['Responsive website'], 'deliverables': ['Website and handover'],
                    'phases': [{'title': 'Build and test', 'tasks': ['Implement reviewed pages'], 'acceptance': ['Tests pass']}],
                    'risks': ['Content pending'], 'questions': ['Who approves the design?']}
            return json.dumps(response), {'total_tokens': 37}
        record = data['files'][0]
        return json.dumps({'summary': 'Fixture repair: return the protected test answer.', 'patches': [{
            'path': record['path'], 'expected_sha256': record['sha256'], 'old': '41', 'new': '42'}]}), {}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--port', type=int, required=True)
    args = parser.parse_args()
    root = initialize(args.directory, args.port)
    source = root / 'source'
    source.mkdir(); (source / 'tests').mkdir()
    (source / 'app.py').write_text('def answer():\n    return 41\n', encoding='utf-8')
    (source / 'tests/test_app.py').write_text('import sys,unittest\nfrom pathlib import Path\nsys.path.insert(0,str(Path(__file__).resolve().parents[1]))\nfrom app import answer\nclass AnswerTest(unittest.TestCase):\n    def test_answer(self):self.assertEqual(42,answer())\n', encoding='utf-8')
    workspace = Workspace.snapshot(source, root / 'snapshot', ['app.py', 'tests/test_app.py'])
    profile = NativeProfile('fixture-unit', (sys.executable, '-I', '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v'), ('tests/test_app.py',), 20)
    core = Core(root / 'core.sqlite3')
    try:
        project = core.create_project('local-owner', 'Native acceptance fixture')
        core.set_policy('local-owner', project, 'ask', ['workspace:fixture'])
        worker = FileWorker({(project, 'workspace:fixture'): workspace}, root / 'evidence', NativeExecutor([profile], owner_enabled=True))
        runtime = RepairRuntime(worker, {'fixture': FixtureProvider()})
        proposal = runtime.create(core, 'local-owner', project, 'workspace:fixture', profile.name, 'fixture',
                                  'Fixture only: satisfy the protected test without changing tests.', ['app.py', 'tests/test_app.py'], [], 'native-fixture')
        assert runtime.generate(core, 'local-owner', proposal)['state'] == 'ready'
    finally: core.close()
    token = secrets.token_urlsafe(32)
    auth_path = root / 'auth.json'
    auth = json.loads(auth_path.read_text())
    auth.append({'token_sha256': hashlib.sha256(token.encode()).hexdigest(), 'actor': 'local-owner', 'role': 'worker', 'projects': [project]})
    auth_path.write_text(json.dumps(auth), encoding='utf-8')
    desktop_path = root / 'desktop.json'
    desktop = json.loads(desktop_path.read_text())
    desktop['worker_token_dpapi'] = protect(token)
    desktop_path.write_text(json.dumps(desktop), encoding='utf-8')
    workspace_config = {'evidence_root': str(root / 'evidence'), 'workspaces': [{'project_id': project, 'resource_id': 'workspace:fixture', 'directory': str(root / 'snapshot')}],
        'execution': {'mode': 'native_trusted', 'owner_enabled': True, 'profiles': [{'name': profile.name, 'argv': list(profile.argv), 'protected_paths': list(profile.protected_paths), 'timeout': profile.timeout}]}}
    (root / 'workspaces.json').write_text(json.dumps(workspace_config), encoding='utf-8')
    # Registration supports reviewing the persisted deterministic proposal. Generate is never called by this test.
    runtime_config = {'providers': [{'name': 'fixture', 'provider': 'gemini', 'model': FixtureProvider.model, 'api_key_env': 'JARVIS_NATIVE_TEST_KEY', 'timeout': 1, 'max_output_tokens': 256}], 'skills': []}
    (root / 'runtime.json').write_text(json.dumps(runtime_config), encoding='utf-8')
    config_path = root / 'launcher.json'
    config = json.loads(config_path.read_text())
    config.update(workspace_config=str(root / 'workspaces.json'), runtime_config=str(root / 'runtime.json'))
    config_path.write_text(json.dumps(config), encoding='utf-8')
    print(json.dumps({'project': project, 'proposal': proposal, 'state': str(root)}))


if __name__ == '__main__': main()
