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

SITE_HTML = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Native client site</title></head><body><main><h1>Native site ready</h1></main></body></html>\n'
SITE_APP = '''from pathlib import Path
def handle(value):
    if value["path"] == "/":
        return {"status":200,"content_type":"text/html; charset=utf-8","body":Path("index.html").read_text(encoding="utf-8")}
    return {"status":200,"content_type":"application/json","body":'{"status":"ok"}'}
'''


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
                if 'TypeScript library' in data.get('request',''):
                    response['plan']={'title':'Native TypeScript library','overview':'An internal strict TypeScript JSON library.',
                        'requirements':['handle(null) returns 42'],'deliverables':['Strict TypeScript ES module'],
                        'phases':[{'title':'Build','tasks':['Implement the approved typed JSON function'],
                            'acceptance':['Strict compilation and protected Node examples pass']}],
                        'risks':[],'questions':[]}
            return json.dumps(response), {'total_tokens': 37}
        def coding_response(value, usage):
            if data.get('edit_protocol') == 'host-bound-v2':
                for edit in value['patches']:
                    edit.pop('expected_sha256', None)
            return json.dumps(value), usage
        records = {item['path']: item for item in data['files']}
        if 'src/main.ts' in records:
            return coding_response({'summary':'Implement the approved TypeScript acceptance example','patches':[{
                'path':'src/main.ts','expected_sha256':records['src/main.ts']['sha256'],
                'old':'throw new Error("Implementation pending");','new':'return 42;'}]}, {'total_tokens':41})
        if data.get('goal') == 'Recover known fixture generation failure':
            if not data.get('diagnostics',{}).get('generation_retry'):
                return 'Fixture incomplete JSON {', {'total_tokens':11}
            record=next(item for item in data['files'] if not item['protected'])
            return coding_response({'summary':'Update the reviewed reusable status label','patches':[{
                'path':record['path'],'expected_sha256':record['sha256'],
                'old':'"Skyra ready"','new':'"Skyra recovered"'}]}, {'total_tokens':13})
        if 'server.py' in records and 'index.html' in records:
            first = 'NotImplementedError' in records['app.py']['content']
            replacements = {'index.html': 'Wrong first implementation\n' if first else SITE_HTML}
            if first: replacements['app.py'] = SITE_APP
            return coding_response({'summary': 'Implement reviewed website, then repair failed HTTP acceptance',
                'patches': [{'path': path, 'expected_sha256': records[path]['sha256'],
                             'old': records[path]['content'], 'new': content}
                            for path, content in replacements.items()]}, {'total_tokens': 90})
        record = next(record for record in data['files'] if not record['protected'])
        if data.get('mode') == 'feature':
            return coding_response({'summary':'Add a reusable status label while preserving answer', 'patches':[{
                'path':record['path'],'expected_sha256':record['sha256'],'old':record['content'],
                'new':record['content']+'\ndef status_label():\n    return "Skyra ready"\n'}]}, {'total_tokens':42})
        return coding_response({'summary': 'Fixture repair: return the protected test answer.', 'patches': [{
            'path': record['path'], 'expected_sha256': record['sha256'], 'old': '' if record['sha256']=='absent' else '41', 'new': 'def answer():\n    return 42\n' if record['sha256']=='absent' else '42'}]}, {})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--port', type=int, required=True)
    args = parser.parse_args()
    root = initialize(args.directory, args.port)
    (root / 'scaffolds').mkdir()
    source = root / 'source'
    source.mkdir(); (source / 'tests').mkdir()
    (source / 'app.py').write_text('def answer():\n    return 41\n', encoding='utf-8')
    (source / 'tests/test_app.py').write_text('import sys,unittest\nfrom pathlib import Path\nsys.path.insert(0,str(Path(__file__).resolve().parents[1]))\nfrom feature import answer\nclass AnswerTest(unittest.TestCase):\n    def test_answer(self):self.assertEqual(42,answer())\n', encoding='utf-8')
    workspace = Workspace.snapshot(source, root / 'snapshot', ['tests/test_app.py'], ['feature.py'])
    profile = NativeProfile('fixture-unit', (sys.executable, '-I', '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v'), ('tests/test_app.py',), 20)
    core = Core(root / 'core.sqlite3')
    try:
        project = core.create_project('local-owner', 'Native acceptance fixture')
        core.set_policy('local-owner', project, 'ask', ['workspace:fixture', 'source:fixture'])
        worker = FileWorker({(project, 'workspace:fixture'): workspace}, root / 'evidence', NativeExecutor([profile], owner_enabled=True))
        runtime = RepairRuntime(worker, {'fixture': FixtureProvider()})
        proposal = runtime.create(core, 'local-owner', project, 'workspace:fixture', profile.name, 'fixture',
                                  'Fixture only: satisfy the protected test without changing tests.', ['feature.py', 'tests/test_app.py'], [], 'native-fixture')
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
        'delivery_targets': [{'project_id': project, 'resource_id': 'source:fixture', 'workspace_resource': 'workspace:fixture', 'directory': str(source)}],
        'execution': {'mode': 'native_trusted', 'owner_enabled': True, 'profiles': [{'name': profile.name, 'argv': list(profile.argv), 'protected_paths': list(profile.protected_paths), 'timeout': profile.timeout}]}}
    (root / 'workspaces.json').write_text(json.dumps(workspace_config), encoding='utf-8')
    (root / 'runner.json').write_text(json.dumps({'projects': [project], 'interval_seconds': 2}), encoding='utf-8')
    # Registration supports reviewing the persisted deterministic proposal. Generate is never called by this test.
    runtime_config = {'providers': [{'name': 'fixture', 'provider': 'gemini', 'model': FixtureProvider.model, 'api_key_env': 'JARVIS_NATIVE_TEST_KEY', 'timeout': 1, 'max_output_tokens': 256}], 'skills': [{'builtin':'acceptance-review'}]}
    (root / 'runtime.json').write_text(json.dumps(runtime_config), encoding='utf-8')
    config_path = root / 'launcher.json'
    config = json.loads(config_path.read_text())
    from jarvis_runtime.node_calibration import toolchain
    toolchain_path=root/'node-toolchain.json'
    tools=toolchain()
    toolchain_path.write_text(json.dumps(tools,indent=2),encoding='utf-8')
    config['node_toolchain_config']=str(toolchain_path)
    from skyra_coding.node_templates import plan as node_plan
    existing=root/'existing-node';existing.mkdir()
    original_document='# Existing owner requirements\nReturn 42; preserve this document.\n'
    existing_plan=node_plan({'project':project,'id':'fixture-existing-source','sha256':'a'*64,
        'documents':{'01_PRODUCT_REQUIREMENTS.md':original_document}},existing,'fixture-existing-node',
        {'cases':[{'name':'answer','input':None,'output':42}]},tools)
    for name,content in existing_plan['files'].items():
        target=existing/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(content,encoding='utf-8')
    existing_files=[*existing_plan['selected'],'docs/01_PRODUCT_REQUIREMENTS.md']
    existing_config=root/'existing-projects.json'
    existing_config.write_text(json.dumps({'sources':{'existing-node':{'directory':str(existing),
        'profile':{**existing_plan['profile'],'name':'fixture-existing-node',
            'protected_paths':[*existing_plan['profile']['protected_paths'],'docs/01_PRODUCT_REQUIREMENTS.md']},
        'runtime_binding':{key:existing_plan[key] for key in ('runtime','executable_sha256')}}}}),encoding='utf-8')
    config['existing_project_config']=str(existing_config)
    config.update(workspace_config=str(root / 'workspaces.json'), runtime_config=str(root / 'runtime.json'))
    config_path.write_text(json.dumps(config), encoding='utf-8')
    print(json.dumps({'project': project, 'proposal': proposal, 'state': str(root),'existing_files':existing_files}))


if __name__ == '__main__': main()
