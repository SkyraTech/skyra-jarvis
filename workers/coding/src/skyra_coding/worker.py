"""Guarded file operations; arbitrary process execution is disabled."""

import hashlib
import json
from pathlib import Path
import re
import time

from .workspace import BoundaryError
from .execution import SandboxUnavailable


class FileWorker:
    def __init__(self, workspaces, evidence_root, sandbox=None, delivery_targets=()):
        # Trusted host configuration only: (project ID, logical resource ID) -> Workspace.
        self.workspaces = dict(workspaces)
        self.profile_bindings = {}
        self.interpreter_bindings = {}
        self.sandbox=sandbox
        if len({w.directory for w in self.workspaces.values()}) != len(self.workspaces):
            raise BoundaryError('A snapshot cannot be shared across run resources')
        self.evidence_root = Path(evidence_root).resolve()
        self.evidence_root.mkdir(parents=True,exist_ok=True)
        for workspace in self.workspaces.values():
            if self.evidence_root.is_relative_to(workspace.directory):
                raise BoundaryError('Evidence must be outside snapshot state')

        from .delivery import Delivery
        self.delivery=Delivery(self,delivery_targets)

    def perform(self, core, actor, task, token):
        intent=core.task(actor,task)
        if json.loads(intent['payload']).get('operation')=='deliver':
            return core.perform_guarded(actor,task,token,lambda intent:self._report(task,'deliver',self.delivery.apply(core,actor,intent)))
        if json.loads(intent['payload']).get('operation')=='test':
            return self._execute(core,actor,task,token)
        def operation(intent):
            try:
                workspace = self.workspaces[(intent['project'],intent['resource'])]
            except KeyError:
                raise BoundaryError('Workspace not registered') from None
            payload = json.loads(intent['payload'])
            op = payload.get('operation')
            schemas = {'read':({'operation','path'},'read'),
                       'patch':({'operation','path','expected_sha256','old','new'},'write'),
                       'create':({'operation','path','content'},'write'),
                       'diff':({'operation'},'read'), 'verify':({'operation'},'read'),
                       'search':({'operation','query'},'read')}
            if op not in schemas:
                raise BoundaryError('Unsupported operation; process execution disabled')
            fields, action = schemas[op]
            if set(payload) != fields or intent['action'] != action:
                raise BoundaryError('Operation/action contract mismatch')
            bound = self.profile_bindings.get((intent['project'], intent['resource']))
            if op in {'patch', 'create'} and bound and payload['path'] in self.profile(intent['project'], intent['resource'], bound).protected_paths:
                raise BoundaryError('Registered acceptance and transport files are protected')
            if op == 'read':
                result = workspace.read(payload['path'])
            elif op == 'create':
                result=workspace.create(payload['path'],payload['content'])
            elif op == 'patch':
                if not isinstance(payload['expected_sha256'],str) or not re.fullmatch('[a-f0-9]{64}',payload['expected_sha256']):
                    raise BoundaryError('Expected content hash required')
                result = workspace.patch(payload['path'],payload['expected_sha256'],payload['old'],payload['new'])
            elif op == 'diff':
                result = workspace.diff()
            elif op == 'search':
                result = workspace.search(payload['query'])
            else:
                result = workspace.verify()
            return self._report(task,op,result)
        return core.perform_guarded(actor,task,token,operation)

    def _report(self,task,operation,result):
        report=json.dumps({'task_id':task,'operation':operation,'result':result},sort_keys=True,ensure_ascii=False).encode('utf-8')
        checksum=hashlib.sha256(report).hexdigest()
        artifact=self.evidence_root/(checksum+'.json')
        try:
            with artifact.open('xb') as stream:stream.write(report);stream.flush()
        except FileExistsError:
            if artifact.read_bytes()!=report:raise BoundaryError('Artifact conflict')
        return {'result':result,'evidence':['sha256:'+checksum],'success':result.get('passed',True)}

    def _execute(self,core,actor,task,token):
        intent=core.task(actor,task)
        payload=json.loads(intent['payload'])
        if intent['action']!='execute' or set(payload)!={'operation','profile'}:
            raise BoundaryError('Fixed-profile execution intent required')
        if self.sandbox is None:
            raise SandboxUnavailable('No execution backend configured')
        self.profile(intent['project'], intent['resource'], payload['profile'])
        workspace=self.workspaces.get((intent['project'],intent['resource']))
        if workspace is None:raise BoundaryError('Workspace not registered')
        # Preflight before recording dispatch; no arbitrary fallback if offline.
        self.sandbox.probe()
        core.begin_execution(actor,task,token)
        last_heartbeat=0.0
        def poll():
            nonlocal last_heartbeat
            core._lease(actor,task,token)
            now=time.monotonic()
            if now-last_heartbeat>=1:
                core.heartbeat(actor,task,token);last_heartbeat=now
        try:
            result=self.sandbox.run(workspace,payload['profile'],poll)
        except Exception:
            # An uncertain create/start must not be silently retried.
            result={'kind':'container_test','passed':False,'termination':'execution_uncertain',
                    'cleanup_confirmed':False,'profile':payload['profile']}
        report=self._report(task,'test',result)
        report['state']=core.settle_execution(actor,task,token,report['evidence'],report['success'],result['cleanup_confirmed'])
        return report

    def profile(self, project, resource, name):
        bound = self.profile_bindings.get((project, resource))
        if bound is not None and bound != name:
            raise BoundaryError('Use the reviewed profile bound to this workspace')
        if self.sandbox is None or name not in self.sandbox.profiles:
            raise BoundaryError('Registered execution profile required')
        profile = self.sandbox.profiles[name]
        expected = self.interpreter_bindings.get((project, resource))
        if expected and hashlib.sha256(Path(profile.argv[0]).read_bytes()).hexdigest() != expected:
            raise BoundaryError('Reviewed interpreter changed; reconcile registration')
        return profile

    def capabilities(self):
        if self.sandbox is None:return {'execution_available':False,'profiles':[]}
        try:self.sandbox.probe();available=True
        except (SandboxUnavailable,ValueError):available=False
        return {'execution_available':available,'profiles':sorted(self.sandbox.profiles)}

    def evidence(self, reference):
        if not re.fullmatch('sha256:[a-f0-9]{64}',reference):
            raise BoundaryError('Invalid artifact reference')
        data = (self.evidence_root/(reference[7:]+'.json')).read_bytes()
        if hashlib.sha256(data).hexdigest() != reference[7:]:
            raise BoundaryError('Artifact checksum mismatch')
        return json.loads(data)
