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


class MessageInput(Input):
    role: Literal['user', 'assistant', 'tool']
    content: str = Field(max_length=100_000)
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


class CodingRunInput(Input):
    resource: Text
    profile: Text
    patches: list[dict] = Field(min_length=1,max_length=10)
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


def create_app(database, credentials, file_worker=None):
    credentials = tuple(credentials)
    if not credentials or not any(c.role == 'controller' for c in credentials):
        raise ValueError('A controller credential is required')
    if len({c.token_sha256 for c in credentials}) != len(credentials):
        raise ValueError('Credentials must be distinct')
    database = Path(database)
    with closing(Core(database)):
        pass
    app = FastAPI(title='Jarvis Local Core', version='0.2.0', docs_url=None, redoc_url=None, openapi_url=None)
    workflow=None
    if file_worker is not None:
        from skyra_coding.workflow import CodingWorkflow
        workflow=CodingWorkflow(file_worker)

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

    @app.put('/v1/projects/{project}/policy')
    async def policy(project: str, body: PolicyInput, request: Request):
        caller = principal(request, 'controller')
        await use(lambda c: c.set_policy(caller.actor, project, body.mode, body.resources))
        return {'updated': True}

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
