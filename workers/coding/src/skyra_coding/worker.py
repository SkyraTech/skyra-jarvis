"""Guarded file operations; arbitrary process execution is disabled."""

import hashlib
import json
from pathlib import Path
import re
import time

from .workspace import BoundaryError
from .execution import SandboxUnavailable
from .toolchains import executable_digest


class FileWorker:
    def __init__(self, workspaces, evidence_root, sandbox=None, delivery_targets=()):
        # Trusted host configuration only: (project ID, logical resource ID) -> Workspace.
        self.workspaces = dict(workspaces)
        self.profile_bindings = {}
        self.interpreter_bindings = {}
        self.toolchain_bindings = {}
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

    def perform(self, core, actor, task, token, supervise=None):
        intent=core.task(actor,task)
        if json.loads(intent['payload']).get('operation')=='deliver':
            return core.perform_guarded(actor,task,token,lambda intent:self._report(task,'deliver',self.delivery.apply(core,actor,intent)))
        if json.loads(intent['payload']).get('operation')=='test':
            return self._execute(core,actor,task,token,supervise)
        def operation(intent):
            try:
                workspace = self.workspaces[(intent['project'],intent['resource'])]
            except KeyError:
                raise BoundaryError('Workspace not registered') from None
            payload = json.loads(intent['payload'])
            op = payload.get('operation')
            schemas = {'read':({'operation','path'},'read'),
                       'inventory':({'operation'},'read'),
                       'read_lines':({'operation','path','start','count'},'read'),
                       'retrieve':({'operation','query','paths','profile'},'read'),
                       'patch':({'operation','path','expected_sha256','old','new'},'write'),
                       'create':({'operation','path','content'},'write'),
                       'diff':({'operation'},'read'), 'verify':({'operation'},'read'),
                       'search':({'operation','query'},'read')}
            schemas['inspect'] = ({'operation', 'requests', 'expected_inputs'}, 'read')
            if op not in schemas:
                raise BoundaryError('Unsupported operation; process execution disabled')
            fields, action = schemas[op]
            if set(payload) != fields or intent['action'] != action:
                raise BoundaryError('Operation/action contract mismatch')
            bound = self.profile_bindings.get((intent['project'], intent['resource']))
            if op in {'patch', 'create'} and bound and payload['path'] in self.profile(intent['project'], intent['resource'], bound).protected_paths:
                raise BoundaryError('Registered acceptance and transport files are protected')
            if op == 'retrieve':
                if not isinstance(payload['profile'],str): raise BoundaryError('Registered profile name required')
                profile = self.profile(intent['project'], intent['resource'], payload['profile'])
                result = workspace.retrieve(payload['query'], payload['paths'], profile.protected_paths)
                from dataclasses import asdict
                from .delivery import checksum
                result['profile_sha256'] = checksum(asdict(profile))
            elif op == 'inspect':
                result = workspace.inspect(payload['requests'], payload['expected_inputs'])
            elif op == 'inventory':
                result = workspace.inventory()
                protected=self.profile(intent['project'],intent['resource'],bound).protected_paths if bound else ()
                for record in result['files']:record['protected']=record['path'] in protected
            elif op == 'read_lines':
                result = workspace.read_lines(payload['path'],payload['start'],payload['count'])
            elif op == 'read':
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

    def _execute(self,core,actor,task,token,supervise=None):
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
        heartbeat_due=0.0
        supervision_stop=None
        def poll():
            nonlocal last_heartbeat, heartbeat_due, supervision_stop
            if supervise:
                from jarvis_core.dispatch import DispatchStopped
                try: supervise()
                except DispatchStopped as exc:
                    supervision_stop=exc.reason
                    raise
            core._lease(actor,task,token)
            now=time.monotonic()
            if now-last_heartbeat>=1 or core.clock()>=heartbeat_due:
                core.heartbeat(actor,task,token);last_heartbeat=now;heartbeat_due=core.clock()+1
        try:
            result=self.sandbox.run(workspace,payload['profile'],poll)
        except Exception:
            # An uncertain create/start must not be silently retried.
            result={'kind':'container_test','passed':False,'termination':'execution_uncertain',
                    'cleanup_confirmed':False,'profile':payload['profile']}
        if supervision_stop:
            result['supervision_stop']=supervision_stop
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
        if expected and executable_digest(profile.argv[0]) != expected:
            raise BoundaryError('Reviewed interpreter changed; reconcile registration')
        for path,checksum in self.toolchain_bindings.get((project,resource),{}).items():
            if executable_digest(path)!=checksum:
                raise BoundaryError('Reviewed toolchain changed; reconcile registration')
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
