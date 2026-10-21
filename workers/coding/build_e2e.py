"""Supervise actual E2E-product coding through Jarvis, with review before every patch."""
import argparse
import json
from pathlib import Path
import sys
import time
import hashlib

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO.parent / 'skyra-e2e-suite'
for directory in ('services/core/src', 'workers/coding/src', 'packages/agent-runtime/src'):
    sys.path.insert(0, str(REPO / directory))
from jarvis_core import Core
from jarvis_core.build_jobs import BuildJobs, checksum as review_checksum
from jarvis_runtime import RepairRuntime, node_calibration
from jarvis_runtime.providers import OnlineProvider
from jarvis_runtime.skills import persistence_skills, contract_skills
from skyra_coding import FileWorker, Workspace
from skyra_coding.native import NativeExecutor, NativeProfile
from skyra_coding.scaffold import checksum, _parent
from skyra_coding.toolchains import verify_typescript

MODEL = 'gemini-3.5-flash-lite'


class SourceWindowProvider:
    """Reduce outgoing source text only; runtime still validates against full admitted files."""
    def __init__(self, provider, root, views):
        self.provider_impl=provider; self.root=root; self.views=views
    def __getattr__(self,name): return getattr(self.provider_impl,name)
    def project(self, context):
        data=json.loads(context); records=[]
        paths={record['path'] for record in data['files']}
        if not isinstance(self.views,dict) or not set(self.views)<=paths:
            raise ValueError('Source view paths must be admitted')
        for record in data['files']:
            current=dict(record); ranges=self.views.get(record['path'],[])
            lines=record['content'].splitlines(keepends=True); chunks=[]
            for bounds in ranges:
                if (not isinstance(bounds,list) or len(bounds)!=2 or any(type(x)is not int for x in bounds)
                        or not 1<=bounds[0]<=bounds[1]<=len(lines)):
                    raise ValueError('Source view range must bind existing lines')
                chunks.append({'start_line':bounds[0],'end_line':bounds[1],
                               'content':''.join(lines[bounds[0]-1:bounds[1]])})
            current['content']=''; current['source_view']='excerpts_only' if chunks else 'metadata_only'
            current['excerpts']=chunks; records.append(current)
        data['files']=records
        projected=json.dumps(data,separators=(',',':'),ensure_ascii=False,allow_nan=False)
        if len(projected.encode())>24000: raise ValueError('Outgoing source view exceeds reviewed24KB cap')
        return projected
    def complete(self, system, context, schema):
        projected=self.project(context)
        entry={'kind':'reviewed_outgoing_source_view','full_context_sha256':review_checksum(json.loads(context)),
               'sent_context_sha256':review_checksum(json.loads(projected)),
               'views_sha256':review_checksum(self.views),'bytes':len(projected.encode()),
               'extra_instruction':'host source excerpt guidance; no tools or scope expansion'}
        folder=self.root/'source-views';folder.mkdir(exist_ok=True)
        (folder/(str(time.time_ns())+'.json')).write_text(json.dumps(entry,indent=2),encoding='utf-8')
        return self.provider_impl.complete(system+'\nFile excerpts are partial views of admitted source, not complete files. Use unique exact old text from one excerpt. Never replace a whole file with joined excerpts. Metadata-only records grant no additional edit or read scope. The host validates every patch against full original source and protected tests.',projected,schema)


class AuditedProvider:
    """Retain bounded received model text locally; never retain provider exceptions."""
    def __init__(self, provider, root):
        self.provider_impl = provider
        self.audit_root = root / 'model-responses'

    def __getattr__(self, name):
        return getattr(self.provider_impl, name)

    def complete(self, system, context, schema):
        try:
            response, usage = self.provider_impl.complete(system, context, schema)
        except Exception as error:
            # Retain only bounded public retry metadata, never exception/body text.
            if getattr(error, 'status_code', None) == 400:
                body = getattr(error, 'body', None)
                detail = body.get('error', body) if isinstance(body, dict) else {}
                code = detail.get('code') if isinstance(detail, dict) else None
                allowed = {'json_validate_failed', 'context_length_exceeded', 'model_decommissioned'}
                folder = self.audit_root.parent / 'provider-status'
                folder.mkdir(exist_ok=True)
                (folder / (str(time.time_ns()) + '.json')).write_text(json.dumps({
                    'kind': 'provider_request_rejected', 'status': 400,
                    'code': code if isinstance(code, str) and code in allowed else None,
                    'automatic_retry': False}), encoding='utf-8')
            if getattr(error, 'status_code', None) == 429:
                headers = getattr(getattr(error, 'response', None), 'headers', {})
                value = headers.get('retry-after') if hasattr(headers, 'get') else None
                retry = None
                if isinstance(value, str) and len(value) <= 12:
                    try:
                        seconds = float(value)
                        if 0 <= seconds <= 86400:
                            retry = seconds
                    except ValueError:
                        pass
                folder = self.audit_root.parent / 'provider-status'
                folder.mkdir(exist_ok=True)
                (folder / (str(time.time_ns()) + '.json')).write_text(json.dumps({
                    'kind': 'provider_rate_limit', 'status': 429,
                    'retry_after_seconds': retry,
                    'automatic_retry': False}), encoding='utf-8')
            raise
        if isinstance(response, str):
            raw = response.encode('utf-8')
            digest = hashlib.sha256(raw).hexdigest()
            record = {'kind': 'untrusted_model_response', 'model': self.model,
                'context_sha256': review_checksum(json.loads(context)),
                'text_sha256': digest, 'bytes': len(raw), 'digest_only': len(raw) > 131072}
            if not record['digest_only']: record['text'] = response
            self.audit_root.mkdir(exist_ok=True)
            target = self.audit_root / (str(time.time_ns()) + '-' + digest[:16] + '.json')
            with target.open('x', encoding='utf-8') as stream:
                json.dump(record, stream, ensure_ascii=False)
        return response, usage
GOAL = '''Implement the actual Skyra E2E product's version-1 declarative Playwright pack validator.
Create only src/pack.ts, exporting validatePack(input: unknown): Pack. Import Pack,
Step, Selector and other types from protected src/contracts.ts with type-only imports.
Reuse record/text/onlyKeys from the already agent-authored src/guards.ts; do not
duplicate those validators. Do not modify existing source, tests or configuration.

Accept exactly version/project/name/cases. version is integer literal 1; project
is trimmed nonempty text <=100, name <=200. cases has 1..50 ordinary array entries.
Each case accepts exactly id/name/steps: id matches [a-z][a-z0-9-]{0,63}, is unique
within the pack, name is trimmed nonempty <=200, and steps has 1..50 entries.
Reject malformed arrays, holes and unexpected own keys; use Reflect.ownKeys where
needed. Returned data must be detached and input must remain unchanged.

Supported exact step variants are specified by Step. goto accepts only action/path:
path is a string beginning with a single /, <=2048 raw characters; reject // prefixes,
backslashes and ASCII control/DEL characters before any normalization. Preserve the
path/query exactly; do not call browsers, resolve URLs, read files or run commands.
click/expectVisible accept only action/locator. fill/expectText additionally require
value: string <=4000 characters, including empty and whitespace, preserved exactly.

Locators are exactly {by:'role',value:Role,name:string} or
{by:'label'|'text'|'testId',value:string}. Use the supported Role union; locator value
and role name are trimmed nonempty text <=200. No arbitrary CSS/scripts/commands.
Reject wrong runtime types, unknown fields, symbols and exotic record prototypes.
Error messages must not echo input values. Supplied tests are examples; implement
the whole contract and use small reusable helpers. Strict erasable TypeScript,
no any or unsafe assertions to bypass checking. A model summary must not claim
tests passed. This is a real product component, not a calibration application.'''



def provider_settings(config):
    choice = config.get('online_provider', 'gemini')
    if choice not in {'gemini', 'groq'}:
        raise ValueError('Explicit supported provider required')
    return {'provider':choice, 'model':MODEL if choice=='gemini' else 'qwen/qwen3.8-27b',
            'key_env':'GEMINI_API_KEY_1' if choice=='gemini' else 'GROQ_API_KEY_1',
            'thinking_level':'medium' if choice=='gemini' else None,
            'normal_output_tokens':8192 if choice=='gemini' else 2048, 'extended_output_tokens':32768 if choice=='gemini' else 4096}


def connect(root, provider, extended_provider=None):
    cfg = json.loads((root / 'session.json').read_text(encoding='utf-8'))
    tools = verify_typescript(cfg['toolchain'])
    for entry in cfg['dependencies']:
        from skyra_coding.toolchains import executable_digest
        if executable_digest(entry['path']) != entry['sha256']:
            raise ValueError('Reviewed installed dependency changed')
    workspace = Workspace(root / 'snapshot')
    if cfg.get('source_views') is not None:
        preliminary = {'goal':cfg['goal'],'files':[
            {**workspace.read(path),'path':path,'protected':path in cfg['protected']} for path in cfg['files']]}
        SourceWindowProvider(provider,root,cfg['source_views']).project(json.dumps(preliminary))
    driver = cfg.get('test_driver', 'tests/run.mjs')
    if driver not in {'tests/run.mjs', 'tests/frontend-run.mjs'} or driver not in cfg['protected']:
        raise ValueError('Registered protected test driver required')
    profile = NativeProfile('e2e-product-tests', (tools['node'], driver, tools['compiler']),
                             tuple(cfg['protected']), cfg.get('execution_timeout', 90))
    worker = FileWorker({(cfg['project'], 'workspace:e2e'): workspace}, root / 'evidence',
        NativeExecutor([profile], owner_enabled=True), [{'project_id': cfg['project'],
            'resource_id': 'source:e2e', 'workspace_resource': 'workspace:e2e', 'directory': str(SOURCE)}])
    key = (cfg['project'], 'workspace:e2e')
    worker.profile_bindings[key] = profile.name
    worker.interpreter_bindings[key] = tools['node_sha256']
    worker.toolchain_bindings[key] = {tools['compiler']: tools['compiler_sha256'],
                                     **{entry['path']: entry['sha256'] for entry in cfg['dependencies']}}
    providers = {'online': provider}
    if extended_provider is not None: providers['online-extended'] = extended_provider
    runtime = RepairRuntime(worker, providers, skills=persistence_skills()[1:] + contract_skills())
    return Core(root / 'core.sqlite3'), runtime, BuildJobs(runtime), cfg


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resume', type=Path)
    parser.add_argument('--allow-model-calls', action='store_true')
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--accept-context-sha256')
    parser.add_argument('--accept-response-sha256')
    parser.add_argument('--deliver-sha256')
    parser.add_argument('--review-feedback', type=Path)
    parser.add_argument('--task-spec', type=Path, help='Supervisor-owned task scope for a fresh session')
    parser.add_argument('--retry-output-limit', action='store_true', help='Reviewed retry with 32768 output tokens on the same model')
    parser.add_argument('--failed-proposal')
    parser.add_argument('--failed-context-sha256')
    parser.add_argument('--review-unknown-generation', action='store_true', help='Explicit new counted attempt after an unknown pure model-request outcome')
    parser.add_argument('--retry-invalid-response', action='store_true', help='Review a completed malformed response and consume a new attempt within original limits')
    parser.add_argument('--tested-review-feedback', type=Path)
    parser.add_argument('--tested-run')
    parser.add_argument('--tested-inputs-sha256')
    parser.add_argument('--pending-review-feedback', type=Path)
    parser.add_argument('--pending-baseline-task')
    parser.add_argument('--pending-inputs-sha256')
    args = parser.parse_args()
    if args.prepare_only and args.allow_model_calls:
        parser.error('Preparation must not enable model calls')
    if args.resume and args.task_spec:
        parser.error('A resumed session retains its original task scope')
    if sum((args.retry_output_limit, args.review_unknown_generation, args.retry_invalid_response)) > 1:
        parser.error('Select exactly one generation recovery operation')
    class NoCalls:
        provider = 'gemini'; model = MODEL; thinking_level = 'medium'; timeout = 90; max_output_tokens = 8192
        def complete(self, *values): raise AssertionError('Model calls were not enabled')
    selected = {}
    if args.resume:
        reviewed_root = _parent(args.resume.absolute())
        if reviewed_root.parent != REPO / '.runtime' or not reviewed_root.name.startswith('e2e-product-'):
            raise ValueError('Use an existing E2E product session')
        selected = json.loads((reviewed_root / 'session.json').read_text(encoding='utf-8'))
    elif args.task_spec:
        selected = json.loads(args.task_spec.read_text(encoding='utf-8-sig'))
    settings = provider_settings(selected)
    provider = NoCalls()
    extended_provider = NoCalls()
    for entry, budget in ((provider, settings['normal_output_tokens']), (extended_provider, settings['extended_output_tokens'])):
        entry.provider = settings['provider']; entry.model = settings['model']
        entry.thinking_level = settings['thinking_level']; entry.max_output_tokens = budget
    if args.allow_model_calls:
        from dotenv import dotenv_values
        import os
        secret = os.environ.get(settings['key_env']) or dotenv_values(REPO / '.env').get(settings['key_env'])
        provider = OnlineProvider(settings['provider'], settings['model'], secret, timeout=90, max_output_tokens=settings['normal_output_tokens'], thinking_level=settings['thinking_level'])
        extended_provider = OnlineProvider(settings['provider'], settings['model'], secret, timeout=90, max_output_tokens=settings['extended_output_tokens'], thinking_level=settings['thinking_level'])
    if args.resume:
        root = _parent(args.resume.absolute())
        if root.parent != REPO / '.runtime' or not root.name.startswith('e2e-product-'):
            raise ValueError('Use an existing E2E product session')
    else:
        if not args.allow_model_calls and not args.prepare_only:
            raise ValueError('Choose offline preparation or explicit model-call consent')
        root = REPO / '.runtime' / ('e2e-product-' + str(time.time_ns())); root.mkdir()
        protected = ['src/types.ts', 'src/contracts.ts', 'src/guards.ts', 'src/target.ts',
            'tests/contract.test.mjs', 'tests/pack.test.mjs', 'tests/run.mjs', 'package.json',
            'tsconfig.json', '.skyra/execution-env.json', 'docs/01_PRODUCT_REQUIREMENTS.md']
        spec = json.loads(args.task_spec.read_text(encoding='utf-8')) if args.task_spec else {}
        protected = spec.get('protected', protected)
        edit_paths = spec.get('edit_paths', [])
        create_paths = spec.get('create_paths', ['src/pack.ts'])
        goal = spec.get('goal', GOAL)
        task = spec.get('task', 'e2e-pack-v1')
        provider_profile = spec.get('provider_profile', 'online')
        if provider_profile not in {'online', 'online-extended'}:
            raise ValueError('Choose a registered bounded provider profile')
        budgets = {name: spec.get(name, default) for name, default in
                   (('max_calls', 2), ('max_cycles', 2), ('max_steps', 40))}
        if any(type(value) is not int or not 1 <= value <= (100 if name == 'max_steps' else 8)
               for name, value in budgets.items()):
            raise ValueError('Bounded task budgets required')
        Workspace.snapshot(SOURCE, root / 'snapshot', [*protected, *edit_paths], create_paths)
        core = Core(root / 'core.sqlite3')
        try:
            project = core.create_project('owner', 'Skyra E2E Suite')
            core.set_policy('owner', project, 'full', ['workspace:e2e', 'source:e2e'])
            conversation = core.create_conversation('owner', project)
            core.append_message('owner', conversation, 'user', goal, 'product-task-request')
        finally: core.close()
        dependencies = json.loads((SOURCE / '.skyra/execution-env.json').read_text(encoding='utf-8'))['identities']
        cfg = {'project': project, 'conversation': conversation, 'goal': goal, 'protected': protected,
            'files': [*protected, *edit_paths, *create_paths], 'toolchain': node_calibration.toolchain(),
            'dependencies': dependencies, 'task': task, 'completed_project': False,
            'provider_profile': provider_profile,
            **budgets,
            'execution_timeout': spec.get('execution_timeout', 90),
            'test_driver': spec.get('test_driver', 'tests/run.mjs'),
            'online_provider': spec.get('online_provider', 'gemini'),
            **({'source_views':spec['source_views']} if 'source_views' in spec else {})}
        (root / 'session.json').write_text(json.dumps(cfg, indent=2), encoding='utf-8')
    if args.allow_model_calls:
        provider = AuditedProvider(provider, root)
        extended_provider = AuditedProvider(extended_provider, root)
        if selected.get('source_views') is not None:
            provider = SourceWindowProvider(provider,root,selected['source_views'])
            extended_provider = SourceWindowProvider(extended_provider,root,selected['source_views'])
    core, runtime, jobs, cfg = connect(root, provider, extended_provider)
    try:
        if args.prepare_only:
            workspace = runtime.worker.workspaces[(cfg['project'], 'workspace:e2e')]
            scope = {'root': str(root), 'state': 'prepared_without_model_calls', 'destination': 'Google Gemini API' if settings['provider']=='gemini' else 'Groq API',
                'model': settings['model'], 'thinking_level': settings['thinking_level'], 'maximum_model_calls': cfg.get('max_calls', 2),
                'max_output_tokens': runtime.providers[cfg.get('provider_profile', 'online')].max_output_tokens,
                'files': {path: workspace.read(path)['sha256'] for path in workspace.selected},
                'goal_sha256': checksum(cfg['goal']),
                'skills': {skill.name: skill.record()['sha256'] for skill in persistence_skills()[1:] + contract_skills()},
                'includes_local_build_path_metadata': True, 'includes_project_requirements': True,
                'model_calls': 0, 'build_job_created': False}
            scope['scope_sha256'] = checksum(scope)
            (root / 'payload-review.json').write_text(json.dumps(scope, indent=2), encoding='utf-8')
            print(json.dumps(scope, indent=2))
            return
        prior = jobs.list(core, 'owner', cfg['project'])
        if not prior and not args.allow_model_calls:
            raise ValueError('Explicit model-call approval required before creating the build job')
        skills = persistence_skills()[1:] + contract_skills()
        job = prior[0] if prior else jobs.create(core, 'owner', cfg['project'], 'workspace:e2e',
            'e2e-product-tests', cfg.get('provider_profile', 'online'), cfg['goal'], cfg['files'], [skill.name for skill in skills],
            cfg.get('max_calls', 2), cfg.get('max_cycles', 2), cfg.get('max_steps', 40),
            3600, False, True, cfg['task'], mode='feature', edit_protocol='host-bound-v2',
            conversation=cfg['conversation'], expected_skills={skill.name: skill.record()['sha256'] for skill in skills})
        if args.retry_output_limit:
            if not args.allow_model_calls:
                raise ValueError('Explicit remaining-call consent required')
            job = jobs.retry_generation(core, 'owner', job['id'], args.failed_proposal,
                args.failed_context_sha256, True, 'online-extended')
            core.append_message('owner', cfg['conversation'], 'assistant',
                'Reviewed completed output-limit failure. Retry on the same model/thinking with 32768 output tokens, within the original two-call budget.',
                'output-limit-review:' + args.failed_proposal)
        if args.review_unknown_generation:
            if not args.allow_model_calls or args.retry_output_limit:
                raise ValueError('Explicit new-call consent and separate unknown-outcome review required')
            job = jobs.retry_generation(core, 'owner', job['id'], args.failed_proposal,
                args.failed_context_sha256, True, acknowledge_unknown_outcome=True)
            core.append_message('owner', cfg['conversation'], 'assistant',
                'Reviewed unknown pure-generation outcome. Prior reservation remains spent and may have been billed; explicitly create one new proposal within the original call/deadline budget. No replay of the old proposal or external execution.',
                'unknown-generation-review:' + args.failed_proposal)
        if args.retry_invalid_response:
            if not args.allow_model_calls:
                raise ValueError('Explicit remaining-call consent required')
            failed = runtime.get(core, 'owner', args.failed_proposal)
            if failed['error'] != 'invalid_model_response':
                raise ValueError('Review a completed malformed model response only')
            job = jobs.retry_generation(core, 'owner', job['id'], args.failed_proposal,
                args.failed_context_sha256, True)
            core.append_message('owner', cfg['conversation'], 'assistant',
                'Reviewed completed malformed response: ' + str(failed.get('validation_failure'))
                + '. Correct the response format in one new counted attempt within the original job limits; no source was executed.',
                'invalid-response-review:' + args.failed_proposal)
        if args.tested_review_feedback:
            if not args.allow_model_calls:
                raise ValueError('Explicit new-call consent required for independent correction')
            feedback = args.tested_review_feedback.read_text(encoding='utf-8')
            job = jobs.request_tested_revision(core, 'owner', job['id'], args.tested_run,
                args.tested_inputs_sha256, feedback, True)
            core.append_message('owner', cfg['conversation'], 'assistant', feedback, 'tested-review:' + args.tested_run)
        if args.pending_review_feedback:
            feedback = args.pending_review_feedback.read_text(encoding='utf-8')
            job = jobs.review_pending_correction(core, 'owner', job['id'], args.pending_baseline_task,
                args.pending_inputs_sha256, feedback)
            core.append_message('owner', cfg['conversation'], 'assistant', feedback,
                'pending-review:' + args.pending_baseline_task)
        if args.accept_context_sha256 or args.accept_response_sha256:
            if args.review_feedback:
                if not args.allow_model_calls:
                    raise ValueError('Correction requires explicit approval for the remaining model call')
                feedback = args.review_feedback.read_text(encoding='utf-8')
                proposal_id = job['proposal']
                job = jobs.request_revision(core, 'owner', job['id'], proposal_id,
                    args.accept_context_sha256, args.accept_response_sha256, feedback, True)
                core.append_message('owner', cfg['conversation'], 'user', feedback, 'review:' + proposal_id)
            else:
                jobs.accept(core, 'owner', job['id'], args.accept_context_sha256, args.accept_response_sha256)
        elif args.review_feedback:
            raise ValueError('Review feedback requires exact context and response hashes')
        if args.allow_model_calls or args.accept_context_sha256:
            for _ in range(30):
                if not args.allow_model_calls and job['phase'] == 'propose':
                    break
                observed = jobs.tick(core, 'owner', cfg['project'])['build_job']
                if observed: job = observed
                if job['state'] not in {'queued', 'running'}: break
                time.sleep(1.05)
        job = jobs.get(core, 'owner', job['id'])
        result = {'root': str(root), 'job': job['id'], 'state': job['state'], 'phase': job['phase'],
                  'calls': job['calls'], 'summary': job['summary'], 'conversation': cfg['conversation'],
                  'completed_project': False}
        workspace = runtime.worker.workspaces[(cfg['project'], 'workspace:e2e')]
        result['inputs_sha256'] = review_checksum({path: workspace.read(path)['sha256'] for path in workspace.selected})
        result['baseline_task'] = job['baseline_task']
        if job['proposal']:
            proposal = runtime.get(core, 'owner', job['proposal'])
            result.update(proposal=proposal['id'], context_sha256=proposal['context_sha256'],
                response_sha256=proposal.get('response_sha256'), validation_failure=proposal.get('validation_failure'))
            if proposal['response']:
                (root / 'review.json').write_text(json.dumps(proposal['response'], indent=2), encoding='utf-8')
                core.append_message('owner', cfg['conversation'], 'assistant', proposal['response']['summary'], 'proposal:' + proposal['id'])
        if job['state'] == 'completed':
            workspace = runtime.worker.workspaces[(cfg['project'], 'workspace:e2e')]
            result['tested_inputs_sha256'] = review_checksum({path: workspace.read(path)['sha256'] for path in workspace.selected})
            review = runtime.worker.delivery.preview(core, 'owner', job['run'], 'source:e2e', source_check=False)
            result['delivery_sha256'] = review['sha256']
            if args.deliver_sha256:
                task = runtime.worker.delivery.prepare(core, 'owner', job['run'], 'source:e2e', args.deliver_sha256, cfg['task'] + '-source')
                if task['state'] == 'queued':
                    lease = core.start('owner', task['id']); runtime.worker.perform(core, 'owner', task['id'], lease['lease_token'])
                result['delivery'] = runtime.worker.delivery.status(core, 'owner', task['id'])
        (root / 'status.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps(result, indent=2))
    finally: core.close()


if __name__ == '__main__': main()
