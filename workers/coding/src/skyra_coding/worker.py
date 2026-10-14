"""Guarded file operations; arbitrary process execution is disabled."""

import hashlib
import json
from pathlib import Path
import re

from .workspace import BoundaryError


class FileWorker:
    def __init__(self, workspaces, evidence_root):
        # Trusted host configuration only: (project ID, logical resource ID) -> Workspace.
        self.workspaces = dict(workspaces)
        if len({w.directory for w in self.workspaces.values()}) != len(self.workspaces):
            raise BoundaryError('A snapshot cannot be shared across run resources')
        self.evidence_root = Path(evidence_root).resolve()
        self.evidence_root.mkdir(parents=True,exist_ok=True)
        for workspace in self.workspaces.values():
            if self.evidence_root.is_relative_to(workspace.directory):
                raise BoundaryError('Evidence must be outside snapshot state')

    def perform(self, core, actor, task, token):
        def operation(intent):
            try:
                workspace = self.workspaces[(intent['project'],intent['resource'])]
            except KeyError:
                raise BoundaryError('Workspace not registered') from None
            payload = json.loads(intent['payload'])
            op = payload.get('operation')
            schemas = {'read':({'operation','path'},'read'),
                       'patch':({'operation','path','expected_sha256','old','new'},'write'),
                       'diff':({'operation'},'read'), 'verify':({'operation'},'read'),
                       'search':({'operation','query'},'read')}
            if op not in schemas:
                raise BoundaryError('Unsupported operation; process execution disabled')
            fields, action = schemas[op]
            if set(payload) != fields or intent['action'] != action:
                raise BoundaryError('Operation/action contract mismatch')
            if op == 'read':
                result = workspace.read(payload['path'])
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
            report = json.dumps({'task_id':task,'operation':op,'result':result},sort_keys=True,ensure_ascii=False).encode('utf-8')
            report_hash = hashlib.sha256(report).hexdigest()
            # Exclusive content-addressed artifact; never overwrite another run's evidence.
            artifact = self.evidence_root / (report_hash+'.json')
            try:
                with artifact.open('xb') as stream:
                    stream.write(report)
            except FileExistsError:
                if artifact.read_bytes() != report:
                    raise BoundaryError('Artifact conflict')
            passed = result.get('passed',True)
            return {'result':result,'evidence':['sha256:'+report_hash],'success':passed}
        return core.perform_guarded(actor,task,token,operation)

    def evidence(self, reference):
        if not re.fullmatch('sha256:[a-f0-9]{64}',reference):
            raise BoundaryError('Invalid artifact reference')
        data = (self.evidence_root/(reference[7:]+'.json')).read_bytes()
        if hashlib.sha256(data).hexdigest() != reference[7:]:
            raise BoundaryError('Artifact checksum mismatch')
        return json.loads(data)
