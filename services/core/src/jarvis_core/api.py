"""Authenticated local control API. It does not execute model-supplied code."""

from contextlib import closing
import asyncio
from dataclasses import dataclass
import hashlib
import hmac
import json
from pathlib import Path
import re
import sqlite3
import sys
from typing import Annotated, Literal
import uuid

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from .store import Core, Conflict, Denied


@dataclass(frozen=True)
class Credential:
    token_sha256: str
    actor: str
    role: Literal['controller', 'agent', 'worker']
    projects: frozenset[str] = frozenset()

    def __post_init__(self):
        if not isinstance(self.token_sha256, str) or not re.fullmatch(r'[a-f0-9]{64}', self.token_sha256):
            raise ValueError('Credential must contain a SHA-256 token digest')
        if not isinstance(self.actor, str) or not self.actor.strip() or self.role not in {'controller', 'agent', 'worker'}:
            raise ValueError('Invalid credential identity')
        if self.role != 'controller' and not self.projects:
            raise ValueError('Agent and worker credentials need explicit projects')
        if not isinstance(self.projects, frozenset) or not all(isinstance(p, str) and p for p in self.projects):
            raise ValueError('Invalid project scope')


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


Text = Annotated[str, Field(min_length=1, max_length=256)]


class ProjectInput(Input):
    name: Text


class PolicyInput(Input):
    mode: Literal['read_only', 'ask', 'full']
    resources: list[Text] = Field(max_length=200)
    expected_version: int | None = Field(default=None, ge=1)


class MessageInput(Input):
    role: Literal['user', 'assistant', 'tool']
    content: str = Field(max_length=100_000)
    request_id: Text


class ModelTurnInput(Input):
    provider: Text
    mode: Literal['chat', 'plan']
    content: str = Field(min_length=1, max_length=8000)
    request_id: Text


class SpecificationInput(Input):
    source_turn: Text
    expected_version: int = Field(ge=0)
    request_id: Text


class SpecificationApproval(Input):
    expected_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')


class ScaffoldName(Input):
    name: str = Field(pattern=r'^[a-z][a-z0-9-]{1,47}$')


class ScaffoldPreview(ScaffoldName, SpecificationApproval):
    contract: dict
    template: Literal['python-json-function-v1', 'python-web-service-v1'] = 'python-json-function-v1'


class ScaffoldCreate(ScaffoldPreview):
    expected_plan_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')


class RegistrationPreview(ScaffoldName):
    expected_plan_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')


class RegistrationCreate(RegistrationPreview):
    expected_registration_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    allow_native_execution: bool


class SpecificationRevision(SpecificationApproval):
    documents: dict[str, str] = Field(min_length=4, max_length=9)
    expected_version: int = Field(ge=1)
    request_id: Text


class TaskInput(Input):
    action: Literal['read', 'write', 'execute']
    resource: Text
    payload: dict
    request_id: Text


class DecisionInput(Input):
    approve: bool


class LeaseInput(Input):
    lease_token: Text


class CompletionInput(LeaseInput):
    evidence: list[Text] = Field(min_length=1, max_length=100)
    success: bool = True


class ReconcileInput(Input):
    outcome: Literal['retry', 'succeeded', 'failed', 'cancelled']
    evidence: list[Text] = Field(min_length=1, max_length=100)


class DeliveryTargetInput(Input):
    target: Text


class DeliveryInput(DeliveryTargetInput):
    expected_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    request_id: Text


class AssignmentInput(Input):
    run: Text
    goal: str = Field(min_length=1, max_length=2000)
    max_steps: int = Field(ge=1, le=100)
    duration_seconds: int = Field(ge=60, le=604800)
    request_id: Text


class AssignmentControl(Input):
    action: Literal['pause', 'resume', 'cancel']


class RunnerTick(Input):
    project: Text


class BuildJobInput(Input):
    resource: Text
    profile: Text
    provider: Text
    goal: str = Field(min_length=1, max_length=8000)
    files: list[Text] = Field(min_length=1, max_length=20)
    skills: list[Text] = Field(max_length=5)
    max_calls: int = Field(ge=1, le=8)
    max_cycles: int = Field(ge=1, le=8)
    max_steps: int = Field(ge=1, le=100)
    duration_seconds: int = Field(ge=60, le=604800)
    auto_accept: bool
    allow_model_calls: bool
    request_id: Text
    specification: Text | None = None


class BuildReview(Input):
    context_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    response_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')


class CodingRunInput(Input):
    resource: Text
    profile: Text
    patches: list[dict] = Field(min_length=1,max_length=10)
    request_id: Text


class ProposalInput(Input):
    specification: Text | None = None
    resource: Text
    profile: Text
    provider: Text
    goal: str = Field(min_length=1, max_length=8000)
    files: list[Text] = Field(min_length=1, max_length=20)
    skills: list[Text] = Field(default_factory=list, max_length=5)
    request_id: Text


def error(code, status, request_id):
    return JSONResponse({'error': {'code': code, 'request_id': request_id}}, status_code=status)


class LocalBoundary:
    """Reject remote/browser callers and authenticate before reading request bodies."""

    def __init__(self, app, credentials, max_body=131_072):
        self.app, self.credentials, self.max_body = app, tuple(credentials), max_body

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            if scope['type'] == 'websocket':
                await send({'type': 'websocket.close', 'code': 1008})
                return
            return await self.app(scope, receive, send)
        request_id = uuid.uuid4().hex
        scope.setdefault('state', {})['request_id'] = request_id

        async def safe_send(message):
            if message['type'] == 'http.response.start':
                message['headers'] = list(message.get('headers', [])) + [
                    (b'cache-control', b'no-store'), (b'x-content-type-options', b'nosniff'),
                    (b'x-request-id', request_id.encode()),
                ]
            await send(message)

        async def reject(code, status):
            await error(code, status, request_id)(scope, receive, safe_send)

        headers = scope.get('headers', [])
        values = lambda key: [v for k, v in headers if k.lower() == key]
        if (scope.get('client') or ('', 0))[0] not in {'127.0.0.1', '::1'}:
            return await reject('local_only', 403)
        hosts = values(b'host')
        if len(hosts) != 1 or not re.fullmatch(rb'(localhost|127\.0\.0\.1|\[::1\])(:[0-9]{1,5})?', hosts[0]):
            return await reject('invalid_host', 400)
        if values(b'origin') or values(b'sec-fetch-site'):
            return await reject('browser_access_disabled', 403)
        authorization = values(b'authorization')
        if len(authorization) != 1 or not authorization[0].startswith(b'Bearer '):
            return await reject('unauthenticated', 401)
        token = authorization[0][7:]
        if not re.fullmatch(rb'[A-Za-z0-9_-]{32,256}', token):
            return await reject('unauthenticated', 401)
        digest = hashlib.sha256(token).hexdigest()
        principal = None
        for candidate in self.credentials:
            if hmac.compare_digest(candidate.token_sha256, digest):
                principal = candidate
        if principal is None:
            return await reject('unauthenticated', 401)
        scope['state']['principal'] = principal
        if scope.get('query_string') and any(k in scope['query_string'].lower() for k in (b'token', b'authorization')):
            return await reject('credential_in_query', 400)
        lengths = values(b'content-length')
        if len(lengths) > 1 or (lengths and not re.fullmatch(rb'[0-9]+', lengths[0])):
            return await reject('invalid_length', 400)
        if lengths and (len(lengths[0]) > 9 or int(lengths[0]) > self.max_body):
            return await reject('body_too_large', 413)
        body = bytearray()
        deadline = asyncio.get_running_loop().time() + 10
        while True:
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                return await reject('request_timeout', 408)
            try:
                chunk = await asyncio.wait_for(receive(), timeout=remaining)
            except TimeoutError:
                return await reject('request_timeout', 408)
            if chunk['type'] == 'http.disconnect':
                return
            body.extend(chunk.get('body', b''))
            if len(body) > self.max_body:
                return await reject('body_too_large', 413)
            if not chunk.get('more_body', False):
                break
        if body and values(b'content-type') != [b'application/json']:
            return await reject('json_required', 415)
        if body:
            try:
                # Reject nonstandard numeric constants and duplicate object keys.
                def pairs(items):
                    result = {}
                    for key, value in items:
                        if key in result:
                            raise ValueError('Duplicate key')
                        result[key] = value
                    return result
                def invalid(_):
                    raise ValueError('Non-finite JSON number')
                json.loads(body, object_pairs_hook=pairs, parse_constant=invalid)
            except (ValueError, RecursionError):
                return await reject('invalid_json', 400)

        delivered = False
        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {'type': 'http.request', 'body': bytes(body), 'more_body': False}
            return await receive()
        await self.app(scope, replay, safe_send)


def create_app(database, credentials, file_worker=None, repair_runtime=None, conversation_runtime=None, unattended_enabled=False, scaffold_root=None, scaffold_execution_enabled=False):
    credentials = tuple(credentials)
    if not credentials or not any(c.role == 'controller' for c in credentials):
        raise ValueError('A controller credential is required')
    if len({c.token_sha256 for c in credentials}) != len(credentials):
        raise ValueError('Credentials must be distinct')
    database = Path(database)
    if scaffold_root is not None:
        from skyra_coding.scaffold import _parent
        scaffold_root = _parent(scaffold_root)
    with closing(Core(database)):
        pass
    app = FastAPI(title='Jarvis Local Core', version='0.2.0', docs_url=None, redoc_url=None, openapi_url=None)
    if conversation_runtime is None and repair_runtime is not None:
        from jarvis_runtime.conversation import ConversationRuntime
        conversation_runtime = ConversationRuntime(repair_runtime.providers)
    registry = None
    if scaffold_root is not None:
        from skyra_coding.worker import FileWorker
        from skyra_coding.native import NativeExecutor
        from skyra_coding.registry import ScaffoldRegistry
        if file_worker is None:
            file_worker = FileWorker({}, scaffold_root / '.jarvis-evidence')
        registry = ScaffoldRegistry(file_worker, scaffold_root,
                                    scaffold_execution_enabled is True or isinstance(file_worker.sandbox, NativeExecutor))
        if repair_runtime is None and conversation_runtime is not None:
            from jarvis_runtime import RepairRuntime
            repair_runtime = RepairRuntime(file_worker, conversation_runtime.providers)
    workflow=None
    assignments=None
    from .build_jobs import BuildJobs
    builds=BuildJobs(repair_runtime)
    if file_worker is not None:
        from skyra_coding.workflow import CodingWorkflow
        workflow=CodingWorkflow(file_worker)
        from .assignments import Assignments
        assignments=Assignments(workflow)

    def principal(request, *roles):
        caller = request.state.principal
        if caller.role not in roles:
            raise Denied('Role is not permitted')
        return caller

    def project_scope(caller, project):
        if caller.role != 'controller' and project not in caller.projects:
            raise Denied('Project outside credential scope')

    async def use(operation):
        def run():
            with closing(Core(database)) as core:
                if registry is not None:
                    registry.sync(core)
                return operation(core)
        return await run_in_threadpool(run)

    def task_scope(core, caller, task):
        data = core.task(caller.actor, task)
        project_scope(caller, data['project'])
        data.pop('lease_token', None)
        return data

    @app.exception_handler(Denied)
    async def denied(request, exc):
        return error('forbidden', 403, request.state.request_id)

    @app.exception_handler(Conflict)
    async def conflict(request, exc):
        return error('conflict', 409, request.state.request_id)

    @app.exception_handler(ValueError)
    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        return error('invalid_input', 422, request.state.request_id)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request, exc):
        return error('http_error', exc.status_code, request.state.request_id)

    @app.exception_handler(sqlite3.Error)
    async def database_error(request, exc):
        return error('storage_unavailable', 503, request.state.request_id)

    @app.exception_handler(Exception)
    async def unexpected(request, exc):
        return error('internal_error', 500, request.state.request_id)

    @app.get('/v1/health')
    async def health():
        return {'status': 'ready', 'version': '0.2.0'}

    @app.get('/v1/openapi.json')
    async def schema(request: Request):
        principal(request, 'controller')
        return app.openapi()

    @app.post('/v1/projects', status_code=201)
    async def create_project(body: ProjectInput, request: Request):
        caller = principal(request, 'controller')
        return {'project_id': await use(lambda c: c.create_project(caller.actor, body.name))}

    @app.get('/v1/projects')
    async def projects(request: Request):
        caller = principal(request, 'controller', 'agent', 'worker')
        data = await use(lambda c: c.projects(caller.actor))
        return {'projects': [p for p in data if caller.role == 'controller' or p['id'] in caller.projects]}

    @app.get('/v1/setup')
    async def setup(request: Request):
        principal(request, 'controller')
        return {'core': True, 'conversation': conversation_runtime.capabilities() if conversation_runtime else {
                    'providers': [], 'modes': [], 'tools_enabled': False, 'automatic_retry': False},
                'repair_available': repair_runtime is not None,
                'scaffolds': {'available': scaffold_root is not None, 'template': 'python-json-function-v1',
                              'registration_enabled': registry.enabled if registry else False},
                'worker': file_worker.capabilities() if file_worker else {'execution_available': False, 'profiles': []},
                'configuration_source': 'trusted_local_files', 'restart_required_for_config': True}

    @app.get('/v1/projects/{project}/dashboard')
    async def dashboard(project: str, request: Request):
        caller = principal(request, 'controller')
        def read(c):
            policy = c._owned(caller.actor, project)
            resources = json.loads(policy['resources'])
            conversations = [dict(r) for r in c.db.execute(
                'SELECT c.id,COUNT(m.id) AS message_count FROM conversations c LEFT JOIN messages m ON m.conversation=c.id WHERE c.project=? GROUP BY c.id ORDER BY c.rowid DESC LIMIT 100', (project,))]
            approvals = [dict(r) for r in c.db.execute(
                "SELECT a.id,a.task,a.expires,a.version,a.digest,t.action,t.resource,t.state AS task_state FROM approvals a JOIN tasks t ON t.id=a.task WHERE t.project=? AND a.state='pending' ORDER BY a.rowid DESC LIMIT 100", (project,))]
            for approval in approvals:
                approval['decidable'] = (approval['expires'] > c.clock() and approval['version'] == policy['version']
                                         and approval['task_state'] == 'waiting_approval')
            proposals = [dict(r) for r in c.db.execute(
                'SELECT id,state,resource,profile,provider,model,usage,error,run,created FROM repair_proposals WHERE project=? ORDER BY rowid DESC LIMIT 100', (project,))]
            for proposal in proposals:
                proposal['usage'] = json.loads(proposal['usage']) if proposal['usage'] else None
            workspaces = []
            if file_worker:
                for (owner_project, resource), workspace in file_worker.workspaces.items():
                    if owner_project == project and resource in resources:
                        workspaces.append({'resource': resource, 'files': list(workspace.selected), 'create_paths': list(workspace.create_paths)})
            return {'project': {'id': project, 'name': policy['name'], 'mode': policy['mode'],
                                'version': policy['version'], 'resources': resources},
                    'delivery_targets': [{'resource': key[1], 'workspace': binding[0]} for key,binding in file_worker.delivery.targets.items() if key[0]==project and key[1] in resources] if file_worker else [],
                    'conversations': conversations, 'approvals': approvals, 'proposals': proposals,
                    'runs': workflow.list(c, caller.actor, project) if workflow else [],
                    'workspaces': workspaces,
                    'registered_resources': sorted(resource for (owner_project, resource) in {**file_worker.workspaces,**file_worker.delivery.targets} if owner_project == project) if file_worker else [],
                    'worker': file_worker.capabilities() if file_worker else {'execution_available': False, 'profiles': []},
                    'runtime': repair_runtime.capabilities() if repair_runtime else {'providers': conversation_runtime.capabilities()['providers'] if conversation_runtime else [], 'skills': [], 'automatic_execution': False},
                    'events': [dict(r) for r in c.db.execute('SELECT * FROM events WHERE project=? ORDER BY id DESC LIMIT 50', (project,))],
                    'server_time': c.clock(), 'limits': {'recent_items': 100, 'events': 50}}
        return await use(read)

    @app.put('/v1/projects/{project}/policy')
    async def policy(project: str, body: PolicyInput, request: Request):
        caller = principal(request, 'controller')
        await use(lambda c: c.set_policy(caller.actor, project, body.mode, body.resources, body.expected_version))
        return {'updated': True}

    @app.get('/v1/projects/{project}/specifications')
    async def specifications(project: str, request: Request):
        from .specifications import list_specs
        caller = principal(request, 'controller')
        return {'specifications': await use(lambda c: list_specs(c, caller.actor, project))}

    @app.post('/v1/projects/{project}/specifications', status_code=201)
    async def publish_specification(project: str, body: SpecificationInput, request: Request):
        from .specifications import publish
        caller = principal(request, 'controller')
        return await use(lambda c: publish(c, caller.actor, project, **body.model_dump()))

    @app.get('/v1/specifications/{spec}')
    async def specification(spec: str, request: Request):
        from .specifications import get
        caller = principal(request, 'controller')
        return await use(lambda c: get(c, caller.actor, spec))

    @app.post('/v1/specifications/{spec}/approve')
    async def approve_specification(spec: str, body: SpecificationApproval, request: Request):
        from .specifications import approve
        caller = principal(request, 'controller')
        return await use(lambda c: approve(c, caller.actor, spec, body.expected_sha256))

    @app.post('/v1/specifications/{spec}/revisions', status_code=201)
    async def revise_specification(spec: str, body: SpecificationRevision, request: Request):
        from .specifications import revise
        caller = principal(request, 'controller')
        return await use(lambda c: revise(c, caller.actor, spec, **body.model_dump()))

    @app.post('/v1/specifications/{spec}/export')
    async def export_specification(spec: str, body: SpecificationApproval, request: Request):
        from .specifications import prepare_export
        caller = principal(request, 'controller')
        return await use(lambda c: prepare_export(c, caller.actor, spec, body.expected_sha256))

    def scaffold_operation(core, caller, spec, body, operation):
        from .specifications import get
        get(core, caller.actor, spec)
        if scaffold_root is None:
            raise Denied('Scaffold creation is disabled by the host')
        from skyra_coding.scaffold import preview, materialize, receipt, checksum
        values = body.model_dump()
        if operation == 'status':
            return receipt(core, caller.actor, spec, scaffold_root, values['name'])
        args = dict(specification=spec, parent=scaffold_root, python=sys.executable, **values)
        if operation == 'preview':
            plan = preview(core, caller.actor, **args)
            return {'plan': plan, 'plan_sha256': checksum(plan)}
        return materialize(core, caller.actor, **args)

    @app.post('/v1/specifications/{spec}/scaffolds/preview')
    async def preview_scaffold(spec: str, body: ScaffoldPreview, request: Request):
        caller = principal(request, 'controller')
        return await use(lambda c: scaffold_operation(c, caller, spec, body, 'preview'))

    @app.post('/v1/specifications/{spec}/scaffolds/create', status_code=201)
    async def create_scaffold(spec: str, body: ScaffoldCreate, request: Request):
        caller = principal(request, 'controller')
        return await use(lambda c: scaffold_operation(c, caller, spec, body, 'create'))

    @app.post('/v1/specifications/{spec}/scaffolds/status')
    async def scaffold_status(spec: str, body: ScaffoldName, request: Request):
        caller = principal(request, 'controller')
        return await use(lambda c: scaffold_operation(c, caller, spec, body, 'status'))

    @app.post('/v1/specifications/{spec}/scaffolds/registration-preview')
    async def registration_preview(spec: str, body: RegistrationPreview, request: Request):
        caller = principal(request, 'controller')
        if registry is None: raise Denied('Scaffolds disabled')
        return await use(lambda c: registry.preview(c, caller.actor, spec, **body.model_dump()))

    @app.post('/v1/specifications/{spec}/scaffolds/register', status_code=201)
    async def register_scaffold(spec: str, body: RegistrationCreate, request: Request):
        caller = principal(request, 'controller')
        if registry is None: raise Denied('Scaffolds disabled')
        return await use(lambda c: registry.register(c, caller.actor, spec, **body.model_dump()))

    @app.post('/v1/specifications/{spec}/scaffolds/registration')
    async def scaffold_registration(spec: str, body: ScaffoldName, request: Request):
        caller = principal(request, 'controller')
        if registry is None: raise Denied('Scaffolds disabled')
        return await use(lambda c: registry.get(c, caller.actor, spec, **body.model_dump()))

    @app.post('/v1/projects/{project}/conversations', status_code=201)
    async def conversation(project: str, request: Request):
        caller = principal(request, 'controller', 'agent')
        project_scope(caller, project)
        return {'conversation_id': await use(lambda c: c.create_conversation(caller.actor, project))}

    @app.post('/v1/conversations/{conversation}/messages', status_code=201)
    async def message(conversation: str, body: MessageInput, request: Request):
        caller = principal(request, 'controller', 'agent')
        if caller.role == 'agent' and body.role == 'user':
            raise Denied('Agent cannot impersonate user')
        def append(c):
            project_scope(caller, c.conversation_project(caller.actor, conversation))
            return c.append_message(caller.actor, conversation, body.role, body.content, body.request_id)
        return {'message_id': await use(append)}

    @app.post('/v1/conversations/{conversation}/model-turns', status_code=201)
    async def create_turn(conversation: str, body: ModelTurnInput, request: Request):
        caller = principal(request, 'controller')
        if conversation_runtime is None: raise StarletteHTTPException(status_code=503)
        turn = await use(lambda c: conversation_runtime.create(c, caller.actor, conversation, **body.model_dump()))
        return {'turn_id': turn}

    @app.get('/v1/conversations/{conversation}/model-turns')
    async def list_turns(conversation: str, request: Request):
        caller = principal(request, 'controller')
        return {'turns': await use(lambda c: c.model_turns(caller.actor, conversation))}

    @app.get('/v1/model-turns/{turn}')
    async def get_turn(turn: str, request: Request):
        caller = principal(request, 'controller')
        return await use(lambda c: c.model_turn(caller.actor, turn))

    @app.post('/v1/model-turns/{turn}/generate')
    async def generate_turn(turn: str, request: Request):
        caller = principal(request, 'controller')
        if conversation_runtime is None: raise StarletteHTTPException(status_code=503)
        return await use(lambda c: conversation_runtime.generate(c, caller.actor, turn))

    @app.post('/v1/model-turns/{turn}/interrupt')
    async def interrupt_turn(turn: str, request: Request):
        caller = principal(request, 'controller')
        return await use(lambda c: c.interrupt_model_turn(caller.actor, turn))

    @app.get('/v1/conversations/{conversation}/messages')
    async def messages(conversation: str, request: Request, after: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=200)):
        caller = principal(request, 'controller', 'agent')
        def read(c):
            project_scope(caller, c.conversation_project(caller.actor, conversation))
            return c.messages(caller.actor, conversation, after, limit)
        return {'messages': await use(read)}

    @app.post('/v1/projects/{project}/tasks', status_code=201)
    async def create_task(project: str, body: TaskInput, request: Request):
        caller = principal(request, 'controller', 'agent')
        project_scope(caller, project)
        return {'task_id': await use(lambda c: c.create_task(caller.actor, project, body.action, body.resource, body.payload, body.request_id))}

    @app.get('/v1/tasks/{task}')
    async def task(task: str, request: Request):
        caller = principal(request, 'controller', 'agent', 'worker')
        return await use(lambda c: task_scope(c, caller, task))

    @app.post('/v1/tasks/{task}/start')
    async def start(task: str, request: Request):
        caller = principal(request, 'worker')
        def claim(c):
            task_scope(c, caller, task)
            return c.start(caller.actor, task)
        return await use(claim)

    @app.post('/v1/tasks/{task}/heartbeat')
    async def heartbeat(task: str, body: LeaseInput, request: Request):
        caller = principal(request, 'worker')
        def beat(c):
            task_scope(c, caller, task)
            c.heartbeat(caller.actor, task, body.lease_token)
        await use(beat)
        return {'renewed': True}

    @app.post('/v1/tasks/{task}/perform')
    async def perform(task: str, body: LeaseInput, request: Request):
        caller = principal(request, 'worker')
        if file_worker is None:
            raise StarletteHTTPException(status_code=503)
        def dispatch(c):
            task_scope(c,caller,task)
            try:return file_worker.perform(c,caller.actor,task,body.lease_token)
            except RuntimeError:
                raise StarletteHTTPException(status_code=503) from None
        return await use(dispatch)

    @app.get('/v1/workers/capabilities')
    async def worker_capabilities(request: Request):
        principal(request,'controller','agent','worker')
        if file_worker is None:return {'execution_available':False,'profiles':[]}
        return await use(lambda c:file_worker.capabilities())

    @app.get('/v1/runtime/capabilities')
    async def runtime_capabilities(request: Request):
        principal(request, 'controller')
        return repair_runtime.capabilities() if repair_runtime else {'providers': [], 'skills': [], 'automatic_execution': False}

    @app.post('/v1/projects/{project}/repair-proposals', status_code=201)
    async def create_proposal(project: str, body: ProposalInput, request: Request):
        caller = principal(request, 'controller')
        if repair_runtime is None: raise StarletteHTTPException(status_code=503)
        proposal = await use(lambda c: repair_runtime.create(c, caller.actor, project, **body.model_dump()))
        return {'proposal_id': proposal}

    @app.get('/v1/repair-proposals/{proposal}')
    async def get_proposal(proposal: str, request: Request):
        caller = principal(request, 'controller', 'agent')
        if repair_runtime is None: raise StarletteHTTPException(status_code=503)
        def read(c):
            result = repair_runtime.get(c, caller.actor, proposal)
            project_scope(caller, result['project'])
            return result
        return await use(read)

    @app.post('/v1/repair-proposals/{proposal}/generate')
    async def generate_proposal(proposal: str, request: Request):
        caller = principal(request, 'controller')
        if repair_runtime is None: raise StarletteHTTPException(status_code=503)
        return await use(lambda c: repair_runtime.generate(c, caller.actor, proposal))

    @app.post('/v1/repair-proposals/{proposal}/accept')
    async def accept_proposal(proposal: str, request: Request):
        caller = principal(request, 'controller')
        if repair_runtime is None: raise StarletteHTTPException(status_code=503)
        return await use(lambda c: repair_runtime.accept(c, caller.actor, proposal))

    @app.post('/v1/repair-proposals/{proposal}/interrupt')
    async def interrupt_proposal(proposal: str, request: Request):
        caller = principal(request, 'controller')
        if repair_runtime is None: raise StarletteHTTPException(status_code=503)
        return await use(lambda c: repair_runtime.interrupt(c, caller.actor, proposal))

    @app.post('/v1/projects/{project}/coding-runs',status_code=201)
    async def create_coding_run(project: str,body: CodingRunInput,request: Request):
        caller=principal(request,'controller')
        if workflow is None:raise StarletteHTTPException(status_code=503)
        run=await use(lambda c:workflow.create(c,caller.actor,project,body.resource,body.profile,body.patches,body.request_id))
        return {'run_id':run}

    @app.get('/v1/projects/{project}/coding-runs')
    async def list_coding_runs(project: str,request: Request):
        caller=principal(request,'controller','agent','worker')
        project_scope(caller,project)
        if workflow is None:raise StarletteHTTPException(status_code=503)
        return {'runs':await use(lambda c:workflow.list(c,caller.actor,project))}

    @app.get('/v1/coding-runs/{run}')
    async def get_coding_run(run: str,request: Request):
        caller=principal(request,'controller','agent','worker')
        if workflow is None:raise StarletteHTTPException(status_code=503)
        def read(c):
            result=workflow.get(c,caller.actor,run)
            project_scope(caller,result['project'])
            return result
        return await use(read)

    @app.post('/v1/coding-runs/{run}/advance')
    async def advance_coding_run(run: str,request: Request):
        caller=principal(request,'worker')
        if workflow is None:raise StarletteHTTPException(status_code=503)
        def advance(c):
            result=workflow.get(c,caller.actor,run)
            project_scope(caller,result['project'])
            try:return workflow.advance(c,caller.actor,run)
            except RuntimeError:raise StarletteHTTPException(status_code=503) from None
        return await use(advance)

    @app.post('/v1/coding-runs/{run}/delivery-preview')
    async def delivery_preview(run: str, body: DeliveryTargetInput, request: Request):
        caller=principal(request,'controller')
        if file_worker is None:raise StarletteHTTPException(status_code=503)
        return await use(lambda c:file_worker.delivery.preview(c,caller.actor,run,body.target))

    @app.get('/v1/projects/{project}/assignments')
    async def list_assignments(project: str, request: Request):
        caller=principal(request,'controller')
        if assignments is None:raise StarletteHTTPException(status_code=503)
        return {'enabled':unattended_enabled, 'assignments':await use(lambda c:assignments.list(c,caller.actor,project))}

    @app.post('/v1/projects/{project}/assignments',status_code=201)
    async def create_assignment(project: str, body: AssignmentInput, request: Request):
        caller=principal(request,'controller')
        if assignments is None or not unattended_enabled:raise StarletteHTTPException(status_code=503)
        return await use(lambda c:assignments.create(c,caller.actor,project,**body.model_dump()))

    @app.post('/v1/assignments/{assignment}/control')
    async def control_assignment(assignment: str, body: AssignmentControl, request: Request):
        caller=principal(request,'controller')
        if assignments is None or (body.action=='resume' and not unattended_enabled):raise StarletteHTTPException(status_code=503)
        return await use(lambda c:assignments.control(c,caller.actor,assignment,body.action))

    @app.post('/v1/runner/tick')
    async def runner_tick(body: RunnerTick, request: Request):
        caller=principal(request,'worker')
        project_scope(caller,body.project)
        if assignments is None or not unattended_enabled:raise StarletteHTTPException(status_code=503)
        def tick(c):
            from .dispatch import recover, lane
            recovered=recover(c,caller.actor,body.project)
            if lane(c,body.project)=='build' and repair_runtime is not None:
                result=builds.tick(c,caller.actor,body.project)
            else:
                result=assignments.tick(c,caller.actor,body.project)
            result['recovered']+=recovered
            return result
        return await use(tick)

    @app.get('/v1/projects/{project}/build-jobs')
    async def list_build_jobs(project: str, request: Request):
        caller=principal(request,'controller')
        return {'enabled':unattended_enabled and repair_runtime is not None,
                'jobs':await use(lambda c:builds.list(c,caller.actor,project))}

    @app.post('/v1/projects/{project}/build-jobs',status_code=201)
    async def create_build_job(project: str, body: BuildJobInput, request: Request):
        caller=principal(request,'controller')
        if not unattended_enabled or repair_runtime is None:raise StarletteHTTPException(status_code=503)
        return await use(lambda c:builds.create(c,caller.actor,project,**body.model_dump()))

    @app.get('/v1/build-jobs/{job}')
    async def build_job(job: str, request: Request):
        caller=principal(request,'controller')
        return await use(lambda c:builds.get(c,caller.actor,job))

    @app.post('/v1/build-jobs/{job}/control')
    async def control_build_job(job: str, body: AssignmentControl, request: Request):
        caller=principal(request,'controller')
        if repair_runtime is None or (body.action=='resume' and not unattended_enabled):raise StarletteHTTPException(status_code=503)
        return await use(lambda c:builds.control(c,caller.actor,job,body.action))

    @app.post('/v1/build-jobs/{job}/accept-proposal')
    async def accept_build_proposal(job: str, body: BuildReview, request: Request):
        caller=principal(request,'controller')
        if repair_runtime is None or not unattended_enabled:raise StarletteHTTPException(status_code=503)
        return await use(lambda c:builds.accept(c,caller.actor,job,**body.model_dump()))

    @app.get('/v1/coding-runs/{run}/deliveries')
    async def deliveries(run: str, request: Request):
        caller=principal(request,'controller')
        if file_worker is None:raise StarletteHTTPException(status_code=503)
        return {'deliveries':await use(lambda c:file_worker.delivery.list(c,caller.actor,run))}

    @app.post('/v1/coding-runs/{run}/deliveries',status_code=201)
    async def prepare_delivery(run: str, body: DeliveryInput, request: Request):
        caller=principal(request,'controller')
        if file_worker is None:raise StarletteHTTPException(status_code=503)
        return await use(lambda c:file_worker.delivery.prepare(c,caller.actor,run,**body.model_dump()))

    @app.post('/v1/deliveries/{task}/advance')
    async def advance_delivery(task: str, request: Request):
        caller=principal(request,'worker')
        if file_worker is None:raise StarletteHTTPException(status_code=503)
        def advance(c):
            data=task_scope(c,caller,task)
            file_worker.delivery.status(c,caller.actor,task)
            if data['state'] in {'queued','waiting_approval'}:
                claim=c.start(caller.actor,task)
                if claim['state']=='running':file_worker.perform(c,caller.actor,task,claim['lease_token'])
            return file_worker.delivery.status(c,caller.actor,task)
        return await use(advance)

    @app.post('/v1/coding-runs/{run}/cancel')
    async def cancel_coding_run(run: str,request: Request):
        caller=principal(request,'controller')
        if workflow is None:raise StarletteHTTPException(status_code=503)
        return await use(lambda c:workflow.cancel(c,caller.actor,run))

    @app.get('/v1/tasks/{task}/evidence/{checksum}')
    async def evidence(task: str, checksum: str, request: Request):
        caller = principal(request,'controller','agent')
        if file_worker is None:
            raise StarletteHTTPException(status_code=503)
        def read(c):
            data = task_scope(c,caller,task)
            reference = 'sha256:'+checksum
            if reference not in json.loads(data['evidence'] or '[]'):
                raise Denied('Artifact does not belong to task')
            return file_worker.evidence(reference)
        return await use(read)

    @app.post('/v1/tasks/{task}/complete')
    async def complete(task: str, body: CompletionInput, request: Request):
        caller = principal(request, 'worker')
        def finish(c):
            task_scope(c, caller, task)
            c.complete(caller.actor, task, body.lease_token, body.evidence, body.success)
        await use(finish)
        return {'recorded': True}

    @app.post('/v1/tasks/{task}/cancel')
    async def cancel(task: str, request: Request):
        caller = principal(request, 'controller')
        await use(lambda c: c.cancel(caller.actor, task))
        return {'recorded': True}

    @app.get('/v1/approvals/{approval}')
    async def approval(approval: str, request: Request):
        caller = principal(request, 'controller')
        return await use(lambda c: c.approval(caller.actor, approval))

    @app.post('/v1/approvals/{approval}/decision')
    async def decide(approval: str, body: DecisionInput, request: Request):
        caller = principal(request, 'controller')
        await use(lambda c: c.decide(caller.actor, approval, body.approve))
        return {'recorded': True}

    @app.post('/v1/projects/{project}/recover')
    async def recover(project: str, request: Request):
        caller = principal(request, 'controller')
        return {'recovered': await use(lambda c: c.recover_expired(caller.actor, project))}

    @app.post('/v1/tasks/{task}/reconcile')
    async def reconcile(task: str, body: ReconcileInput, request: Request):
        caller = principal(request, 'controller')
        await use(lambda c: c.reconcile(caller.actor, task, body.outcome, body.evidence))
        return {'recorded': True}

    @app.get('/v1/projects/{project}/events')
    async def events(project: str, request: Request, after: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=200)):
        caller = principal(request, 'controller', 'agent', 'worker')
        project_scope(caller, project)
        return {'events': await use(lambda c: c.events(caller.actor, project, after, limit))}

    app.add_middleware(LocalBoundary, credentials=credentials)
    return app
