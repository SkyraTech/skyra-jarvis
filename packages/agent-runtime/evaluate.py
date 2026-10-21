"""Supervised online coding calibration over generated internal fixtures only.

Preparation makes at most one model call and stops before accepting any code.
Resume uses exact persisted hashes; an explicitly configured second call can repair a failed retest.
Every generated revision stops for independent supervisor review before execution.
"""
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
from jarvis_core.build_jobs import BuildJobs, checksum
from jarvis_runtime import RepairRuntime
from jarvis_runtime.providers import OnlineProvider
from jarvis_runtime.skills import persistence_skills, http_skills, contract_skills
from jarvis_runtime.calibration import TASK_BOARD_GOAL, TASK_BOARD_CONTRACT, feedback_goal
from jarvis_runtime import node_calibration
from skyra_coding import FileWorker, Workspace
from skyra_coding.native import NativeExecutor, NativeProfile
from skyra_coding.templates import SERVER


class RecordedProvider(OnlineProvider):
    """Raw output is captured only for this generated, nonsecret evaluation fixture."""
    directory = None

    def complete(self, system, context, schema):
        from jarvis_runtime.responses import failure_code, failure_usage
        started = time.monotonic()
        identifier = str(time.time_ns())
        record = {'provider':self.provider, 'model':self.model, 'attempt':identifier, 'thinking_level':self.thinking_level}
        try:
            text, usage = super().complete(system, context, schema)
            if isinstance(text, str) and len(text.encode()) <= 64000:
                path = 'model-response-'+identifier+'.txt'
                (self.directory / path).write_text(text, encoding='utf-8')
                (self.directory / 'model-response.txt').write_text(text, encoding='utf-8')
                record['response_path'] = path
            record.update(state='returned', usage=usage)
            return text, usage
        except Exception as exc:
            record.update(state='failed', error=failure_code(exc,'provider_failure',provider_failure=True))
            usage=failure_usage(exc)
            if usage is not None:record['usage']=usage
            raise
        finally:
            record['elapsed_seconds'] = round(time.monotonic()-started,3)
            (self.directory / ('model-call-'+identifier+'.json')).write_text(json.dumps(record,indent=2),encoding='utf-8')


CONTRACT = '''import sys,unittest,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tasks import TaskStore
import storage
class Contract(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'tasks.json'
        self.store=TaskStore(self.path)
    def tearDown(self):self.temp.cleanup()
    def test_create_and_restart(self):
        item=self.store.create('  Plan website  ')
        self.assertEqual('Plan website',item['title']);self.assertIs(item['completed'],False)
        self.assertIsInstance(item['id'],str);self.assertTrue(item['id'])
        self.assertEqual([item],TaskStore(self.path).list())
    def test_unique_ids_and_complete(self):
        one=self.store.create('One');two=self.store.create('Two')
        self.assertNotEqual(one['id'],two['id'])
        item=self.store.complete(one['id']);self.assertIs(item['completed'],True)
        self.assertEqual([item,two],TaskStore(self.path).list())
        self.assertEqual(item,self.store.complete(one['id']))
    def test_invalid_titles(self):
        for title in ('','   ',None,7,'x'*201):
            with self.subTest(title=type(title).__name__):
                with self.assertRaises(ValueError):self.store.create(title)
        self.assertEqual([],self.store.list())
    def test_unknown_task_does_not_write(self):
        self.store.create('Existing');before=self.path.read_bytes()
        with self.assertRaises(KeyError):self.store.complete('missing')
        self.assertEqual(before,self.path.read_bytes())
    def test_corrupt_store_is_not_silently_reset(self):
        self.path.write_text('broken',encoding='utf-8')
        with self.assertRaises(ValueError):TaskStore(self.path).list()
        self.assertEqual('broken',self.path.read_text(encoding='utf-8'))
    def test_returned_objects_do_not_mutate_persistence(self):
        item=self.store.create('Original');item['title']='Changed'
        rows=self.store.list();rows[0]['completed']=True
        self.assertEqual('Original',self.store.list()[0]['title'])
        self.assertIs(self.store.list()[0]['completed'],False)
    def test_invalid_record_schema_is_rejected_without_writing(self):
        import json
        bad=[{}, {'id':7,'title':'A','completed':False},
             {'id':'x','title':'','completed':False},
             {'id':'x','title':' A ','completed':False},
             {'id':'x','title':'   ','completed':False},
             {'id':'x','title':'A','completed':0},
             {'id':'x','title':'A','completed':False,'extra':True}]
        for row in bad:
            with self.subTest(row=row):
                text=json.dumps([row]);self.path.write_text(text,encoding='utf-8')
                with self.assertRaises(ValueError):self.store.list()
                with self.assertRaises(ValueError):self.store.create('Do not overwrite')
                self.assertEqual(text,self.path.read_text(encoding='utf-8'))
    def test_invalid_root_container_is_not_missing_data(self):
        for text in ('null','{}','true','42','"text"'):
            with self.subTest(text=text):
                self.path.write_text(text,encoding='utf-8')
                with self.assertRaises(ValueError):self.store.list()
                with self.assertRaises(ValueError):self.store.create('Preserve')
                self.assertEqual(text,self.path.read_text(encoding='utf-8'))
    def test_duplicate_persisted_identifiers_are_corruption(self):
        import json
        item={'id':'duplicate','title':'A','completed':False}
        text=json.dumps([item,item]);self.path.write_text(text,encoding='utf-8')
        with self.assertRaises(ValueError):self.store.list()
        with self.assertRaises(ValueError):self.store.complete('duplicate')
        self.assertEqual(text,self.path.read_text(encoding='utf-8'))
if __name__=='__main__':unittest.main()
'''
GOAL = '''Implement this bounded internal task-store foundation, not a finished application.
Use only Python standard library. Implement TaskStore(path) in tasks.py with create(title),
list(), and complete(id). Records contain unique string id, trimmed title (1..200 chars),
and boolean completed. Persist across instances, keep insertion order, return independent
record copies, and make completion idempotent. Reject invalid titles with ValueError and
unknown ids with KeyError without writing. Reject corrupt persisted data without resetting it.
Create storage.py for reusable JSON persistence; tasks.py must use its helpers rather than
duplicate serialization. Handle a missing store as empty and use an atomic save. Do not
accept persisted records unless they have exactly id/title/completed, nonempty unique
string ids, valid already-trimmed title strings of 1..200 characters and actual bool
completion flags. Reject any invalid record or duplicate id with ValueError before writes.
Do not change protected tests or add dependencies, shell/network actions or other files.
Return exact patches/creation content. Passing these tests is not full project acceptance.'''


def connect(root, provider):
    core = Core(root / 'core.sqlite3')
    workspace = Workspace(root / 'snapshot')
    config = json.loads((root / 'evaluation.json').read_text(encoding='utf-8'))
    profile = node_calibration.profile(config) if config.get('task')=='e2e-targets-v1' else NativeProfile(
        'contract', (sys.executable, '-I', '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v'),
        tuple(config.get('protected_paths', ['tests/test_contract.py'])), 30 if config.get('foundation') else 20)
    worker = FileWorker({(config['project'], 'workspace:evaluation'): workspace}, root / 'evidence',
                        NativeExecutor([profile], owner_enabled=True))
    runtime = RepairRuntime(worker, {'evaluated': provider}, skills=persistence_skills()+http_skills()+contract_skills())
    return core, runtime, BuildJobs(runtime), config


def checked_root(path):
    root = path.resolve()
    if not root.is_relative_to((REPO / '.runtime').resolve()) or not root.name.startswith('coding-evaluation-'):
        raise ValueError('Use a generated evaluation under this repository runtime root')
    return root


def browser_inputs(path, job_id=None):
    return tested_inputs(path,job_id,task='task-board-v1')


def tested_inputs(path, job_id=None, *, task):
    """Read-only admission for reviewed, tested generated application code."""
    root = checked_root(path)
    config = json.loads((root / 'evaluation.json').read_text(encoding='utf-8'))
    if (task not in {'task-board-v1','e2e-targets-v1'} or config.get('task')!=task
            or (task=='task-board-v1' and not config.get('foundation'))):
        raise ValueError('The requested evaluation contract is required')
    class NoCalls:
        provider = config['provider']
        model = config['model']
        def complete(self, *args): raise AssertionError('Browser admission cannot call a model')
    core, runtime, jobs, _ = connect(root, NoCalls())
    try:
        job = jobs.get(core,'owner',job_id) if job_id else jobs.list(core, 'owner', config['project'])[0]
        if job['project'] != config['project'] or job['state'] != 'completed':
            raise ValueError('A reviewed passing retest in this project is required')
        run = runtime.workflow.get(core, 'owner', job['run'])
        tests = [r for r in run['results'] if r['state']=='succeeded' and core.task('owner',r['task_id'])['action']=='execute']
        if not tests: raise ValueError('Protected retest evidence required')
        reference = tests[-1]['evidence'][0]
        report = runtime.worker.evidence(reference)['result']
        workspace = runtime.worker.workspaces[(config['project'],'workspace:evaluation')]
        verified=jobs.diagnostic(core,'owner',job,tests[-1]['task_id'])
        profile_digest=report['profile_sha256']
        hashes = {p:workspace.read(p)['sha256'] for p in workspace.selected}
        if verified['exit_code']!=0:
            raise ValueError('Tested application inputs or profile changed')
        return {'root':str(root),'files':str(workspace.root),'job':job['id'],'run':job['run'],
                'input_hashes':hashes,'test_evidence':reference,'profile_sha256':profile_digest,
                'completed_project':False}
    finally: core.close()



def independent_review(path):
    root = checked_root(path)
    config = json.loads((root / 'evaluation.json').read_text(encoding='utf-8'))
    if config.get('foundation'):
        raise ValueError('Task-board acceptance also requires separate browser review')
    class NoCalls:
        provider = config['provider']
        model = config['model']
        timeout = 90
        max_output_tokens = 4096
        def complete(self, *args): raise AssertionError('Independent review cannot call a model')
    core, runtime, jobs, _ = connect(root, NoCalls())
    try:
        job = jobs.list(core, 'owner', config['project'])[0]
        if job['state'] != 'completed': raise ValueError('A tested, reviewed coding result is required')
        run = runtime.workflow.get(core, 'owner', job['run'])
        tests = [r for r in run['results'] if r['state']=='succeeded' and core.task('owner', r['task_id'])['action']=='execute']
        if not tests: raise ValueError('Successful protected retest required')
        worker = runtime.worker
        report = worker.evidence(tests[-1]['evidence'][0])['result']
        workspace = worker.workspaces[(config['project'], 'workspace:evaluation')]
        verified=jobs.diagnostic(core,'owner',job,tests[-1]['task_id'])
        if verified['exit_code']!=0:
            raise ValueError('Tested code changed before independent review')
        script = '''import sys,json,tempfile
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from tasks import TaskStore
r={'id':'x','title':'A','completed':False}
rows=[{},dict(r,id=7),dict(r,title=''),dict(r,title=' A '),dict(r,title='   '),dict(r,completed=0),dict(r,extra=True)]
texts=[json.dumps([v]) for v in rows]+['null','{}','true','42','"text"']
bad=[]
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'tasks.json'
 for i,text in enumerate(texts):
  for op in ('list','create'):
   p.write_text(text,encoding='utf-8')
   try:getattr(TaskStore(p),op)(*(['Keep'] if op=='create' else []))
   except ValueError:pass
   else:bad.append([i,op])
   if p.read_text(encoding='utf-8')!=text:bad.append([i,'modified'])
print(json.dumps({'invalid_data_accepted':bad}))
assert not bad
'''
        name = 'independent-record-schema-v3'
        if config.get('task')=='e2e-targets-v1':name,profile=node_calibration.independent_profile(config)
        else:profile=NativeProfile(name, (sys.executable, '-I', '-B', '-c', script), ('tests/test_contract.py',), 20)
        worker.sandbox.profiles[name] = profile
        from dataclasses import asdict
        request_id=name+':'+checksum([report['input_hashes'],asdict(profile)])
        task = core.create_task('owner', config['project'], 'execute', 'workspace:evaluation',
                                {'operation':'test','profile':name}, request_id)
        state = core.task('owner', task)['state']
        if state == 'queued':
            lease = core.start('owner', task)
            worker.perform(core, 'owner', task, lease['lease_token'])
        elif state not in {'succeeded','failed'}: raise ValueError('Reconcile the existing independent test first')
        row = core.task('owner', task)
        independent = worker.evidence(json.loads(row['evidence'])[0])['result']
        import hashlib
        from dataclasses import asdict
        profile_digest = hashlib.sha256(json.dumps(asdict(worker.sandbox.profiles[name]),sort_keys=True,separators=(',',':')).encode()).hexdigest()
        if (independent['profile_sha256'] != profile_digest
                or independent['input_hashes'] != {p:workspace.read(p)['sha256'] for p in workspace.selected}):
            raise ValueError('Independent review inputs or test profile changed')
        result = {'task':task, 'passed':row['state']=='succeeded' and independent['passed'] and independent['cleanup_confirmed'],
                  'profile_sha256':independent['profile_sha256'], 'input_hashes':independent['input_hashes'], 'state':row['state'], 'evidence':json.loads(row['evidence']),
                  'model_calls':0, 'supervisor_authored':True, 'completed_project':False}
        previous=root/'independent-review.json'
        if previous.exists():
            saved=json.loads(previous.read_text(encoding='utf-8'))
            (root/('independent-review-'+saved['task']+'.json')).write_text(json.dumps(saved,indent=2),encoding='utf-8')
        (root/('independent-review-'+task+'.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
        previous.write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps(result, indent=2))
    finally: core.close()


def main(args):
    if args.browser_inputs:
        print(json.dumps(browser_inputs(args.browser_inputs),indent=2))
        return
    if args.independent_review:
        if args.resume: raise ValueError('Choose accept or independent review')
        independent_review(args.independent_review)
        return
    if not args.allow_model_calls:
        raise ValueError('Explicit --allow-model-calls is required; no implicit online calls')
    values = os.environ
    if args.env_file:
        from dotenv import dotenv_values
        values = {**dotenv_values(args.env_file), **os.environ}
    if args.e2e_targets and args.foundation:raise ValueError('Choose one evaluation task')
    provider = RecordedProvider(args.provider, args.model, values.get(args.key_env, ''), timeout=90,
                                max_output_tokens=8192 if args.foundation or args.e2e_targets else 4096, thinking_level=args.thinking_level)
    revision = None
    if args.resume or args.revise:
        if args.resume and args.revise: raise ValueError('Choose proposal acceptance or independent-review revision')
        if args.revise:
            review_path = args.revise.resolve()
            if not review_path.is_relative_to((REPO/'.runtime').resolve()):
                raise ValueError('Use an internal evaluation review')
            report = json.loads(review_path.read_text(encoding='utf-8'))
            root = checked_root(Path(report['inputs']['root']))
            if not review_path.is_relative_to(root): raise ValueError('Review must belong to its evaluation')
            scope=report.get('scope')
            expected = tested_inputs(root,report['inputs']['job'],task='e2e-targets-v1') if scope=='internal-e2e-target-review-v1' else browser_inputs(root,report['inputs']['job'])
            feedback = feedback_goal(report,expected,scope=scope)
            import hashlib
            digest = hashlib.sha256(json.dumps(report,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            revision = (feedback,digest)
        else:
            root = checked_root(args.resume)
        saved = json.loads((root / 'evaluation.json').read_text(encoding='utf-8'))
        provider.max_output_tokens = saved.get('max_output_tokens', 4096)
    else:
        foundation = None
        if args.foundation:
            foundation = checked_root(args.foundation)
            independent_review(foundation)
            if json.loads((foundation / 'independent-review.json').read_text(encoding='utf-8')).get('passed') is not True:
                raise ValueError('A current independently accepted foundation is required')
        root = REPO / '.runtime' / ('coding-evaluation-' + args.provider + '-' + str(time.time_ns()))
        source = root / 'source'
        (source / 'tests').mkdir(parents=True)
        selected = ['tasks.py', 'tests/test_contract.py']
        absent = ['storage.py']
        protected = ['tests/test_contract.py']
        node_fixture=None
        if args.e2e_targets:
            node_fixture=node_calibration.prepare(source)
            selected=node_fixture['selected'];protected=node_fixture['protected'];absent=node_fixture['absent']
        elif foundation:
            for path in ('tasks.py','storage.py','tests/test_contract.py'):
                (source / path).write_bytes((foundation / 'snapshot' / 'files' / path).read_bytes())
            (source / 'server.py').write_text(SERVER, encoding='utf-8')
            (source / 'tests/test_http.py').write_text(TASK_BOARD_CONTRACT, encoding='utf-8')
            selected = ['tasks.py','storage.py','server.py','tests/test_contract.py','tests/test_http.py']
            protected = selected.copy()
            absent = ['app.py','index.html','app.js','styles.css']
        else:
            (source / 'tasks.py').write_text('class TaskStore:\n    def __init__(self,path):\n        raise NotImplementedError("Implement the approved task-store contract")\n', encoding='utf-8')
            (source / 'tests/test_contract.py').write_text(CONTRACT, encoding='utf-8')
        Workspace.snapshot(source, root / 'snapshot', selected, absent)
        initial = Core(root / 'core.sqlite3')
        project = initial.create_project('owner', 'Internal E2E target calibration' if node_fixture else 'Internal task-board calibration' if foundation else 'Internal task-store calibration')
        conversation = initial.create_conversation('owner', project)
        initial.set_policy('owner', project, 'full', ['workspace:evaluation'])
        initial.close()
        (root / 'evaluation.json').write_text(json.dumps({'project': project, 'conversation': conversation, 'provider': args.provider, 'model': args.model,
            'task': 'e2e-targets-v1' if node_fixture else 'task-board-v1' if foundation else 'task-store-foundation-v5',
            **({'node_toolchain':node_fixture['toolchain']} if node_fixture else {}),
            'foundation': str(foundation) if foundation else None,
            'goal': node_calibration.GOAL if node_fixture else TASK_BOARD_GOAL if foundation else GOAL,
            'files': selected + absent, 'protected_paths': protected,
            'edit_protocol': 'host-bound-v2', 'max_calls': args.max_calls,
            'max_output_tokens': provider.max_output_tokens,
            'agent_authored_paths': absent if node_fixture or foundation else ['tasks.py', 'storage.py'],
            'skills': [s.record() for s in (persistence_skills()[1:]+http_skills()+contract_skills() if node_fixture else persistence_skills())],
            'supervisor_authored_paths': protected if node_fixture else ['server.py','tests/test_http.py'] if foundation else ['tests/test_contract.py'],
            'reused_agent_authored_paths': ['tasks.py','storage.py'] if foundation else [],
            'completed_project': False}), encoding='utf-8')
    provider.directory = root
    core, runtime, jobs, config = connect(root, provider)
    try:
        if config['provider'] != args.provider or config['model'] != args.model:
            raise ValueError('Keep the exact evaluation provider/model')
        prior = jobs.list(core, 'owner', config['project'])
        if revision:
            goal = config['goal']+'\nIndependent review SHA-256: '+revision[1]+'\n'+revision[0]
            revision_skills=persistence_skills()[1:]+http_skills()+contract_skills() if config.get('task')=='e2e-targets-v1' else persistence_skills()+http_skills()
            job = jobs.create(core,'owner',config['project'],'workspace:evaluation','contract','evaluated',
                goal,config['files'],[s.name for s in revision_skills],1,1,20,1800,
                False,True,'review-'+revision[1]+'-'+str(provider.thinking_level or 'default'),mode='feature',edit_protocol='host-bound-v2',
                conversation=config.get('conversation'),expected_skills={s.name:s.record()['sha256'] for s in revision_skills})
        else:
            selected_skills=persistence_skills()[1:]+http_skills()+contract_skills() if config.get('task')=='e2e-targets-v1' else persistence_skills()
            job = prior[0] if prior else jobs.create(core, 'owner', config['project'], 'workspace:evaluation', 'contract',
            'evaluated', config.get('goal',GOAL), config.get('files',['tasks.py', 'storage.py', 'tests/test_contract.py']),
            [s.name for s in selected_skills], config.get('max_calls',1), config.get('max_calls',1), 40, 1800,
            False, True, 'evaluation-v1', mode='feature', edit_protocol='host-bound-v2',
            conversation=config.get('conversation'),expected_skills={s.name:s.record()['sha256'] for s in selected_skills})
        if args.resume:
            if job['state'] != 'waiting_review': raise ValueError('Only a reviewed waiting proposal may resume')
            proposal = runtime.get(core, 'owner', job['proposal'])
            if proposal['context'].get('generation',{}).get('thinking_level') != args.thinking_level:
                raise ValueError('Keep the exact reviewed thinking level')
            jobs.accept(core, 'owner', job['id'], proposal['context_sha256'], proposal['response_sha256'])
        started = time.monotonic()
        for _ in range(24):
            result = jobs.tick(core, 'owner', config['project'])['build_job']
            if result: job = result
            if job['state'] not in {'queued','running'}: break
            time.sleep(1.05)
        result = {'provider': args.provider, 'model': args.model, 'task': config['task'], 'state': job['state'],
                  'phase': job['phase'], 'job': job['id'], 'proposal': job['proposal'], 'run': job['run'],
                  'calls_reserved': job['calls'], 'steps': job['steps'], 'summary': job['summary'],
                  'elapsed_this_invocation_seconds': round(time.monotonic()-started, 3),
                  'completed_project': False, 'conversation':config.get('conversation'), 'artifacts': str(root)}
        result['total_calls_reserved'] = sum(item['calls'] for item in jobs.list(core,'owner',config['project']))
        if job['proposal']:
            result['validation_failure'] = runtime.get(core, 'owner', job['proposal'])['validation_failure']
        (root / ('accepted-result.json' if args.resume else 'prepared-result.json')).write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps(result, indent=2), flush=True)
    finally: core.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider', choices=['gemini','groq'])
    parser.add_argument('--model')
    parser.add_argument('--key-env')
    parser.add_argument('--env-file', type=Path)
    parser.add_argument('--allow-model-calls', action='store_true')
    parser.add_argument('--max-calls', type=int, choices=[1,2], default=1)
    parser.add_argument('--resume', type=Path)
    parser.add_argument('--independent-review', type=Path)
    parser.add_argument('--foundation', type=Path, help='Build the task-board application on an independently accepted generated foundation')
    parser.add_argument('--browser-inputs', type=Path, help='Read-only hash-verified browser acceptance admission')
    parser.add_argument('--revise', type=Path, help='Prepare one bounded revision from a current failed independent browser review')
    parser.add_argument('--thinking-level', choices=['minimal','low','medium','high'])
    parser.add_argument('--e2e-targets', action='store_true',help='Supervise a strict TypeScript E2E target validator using installed tools')
    try: main(parser.parse_args())
    except Exception as exc:
        print(json.dumps({'error': 'evaluation_requires_review', 'error_type': type(exc).__name__}), file=sys.stderr)
        raise SystemExit(1)
