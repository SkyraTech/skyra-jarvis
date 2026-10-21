"""Bounded read-only tool batches for the upcoming interactive coding engine.

Uses existing durable tasks, permissions and evidence. This adapter grants no
model calls, writes, commands, expanded file scope or automatic progression.
"""
import json
from dataclasses import asdict

from jarvis_core import Conflict, Denied
from .scaffold import checksum
from .workspace import BoundaryError


def validate_requests(workspace, requests):
    if type(requests) is not list or not 1 <= len(requests) <= 4:
        raise BoundaryError('Inspection requires 1..4 bounded read-only requests')
    checked = []
    for request in requests:
        if type(request) is not dict:
            raise BoundaryError('Inspection request must be an object')
        operation = request.get('operation')
        if operation == 'inventory' and set(request) == {'operation'}:
            pass
        elif operation == 'read_lines' and set(request) == {'operation', 'path', 'start', 'count'}:
            if (type(request['path']) is not str or request['path'] not in workspace.selected
                    or type(request['start']) is not int or not 1 <= request['start'] <= 1_000_000
                    or type(request['count']) is not int or not 1 <= request['count'] <= 200):
                raise BoundaryError('Select bounded lines from an admitted file')
            if workspace.read(request['path'])['sha256'] == 'absent':
                raise BoundaryError('Cannot inspect lines of an absent file')
        elif operation == 'search' and set(request) == {'operation', 'query'}:
            if type(request['query']) is not str or not 1 <= len(request['query']) <= 256:
                raise BoundaryError('Inspection search requires 1..256 characters')
        else:
            raise BoundaryError('Unsupported inspection operation or fields')
        detached = json.loads(json.dumps(request))
        if detached in checked:
            raise BoundaryError('Duplicate inspection request')
        checked.append(detached)
    return checked

class InspectionTools:
    def __init__(self, worker):
        self.worker = worker

    def _binding(self, core, actor, project, resource, profile):
        policy = core._owned(actor, project)
        if resource not in json.loads(policy['resources']):
            raise Denied('Inspection resource is outside current grants')
        workspace = self.worker.workspaces.get((project, resource))
        if workspace is None:
            raise Denied('Inspection workspace unavailable')
        fixed = self.worker.profile(project, resource, profile)
        hashes = {path: workspace.read(path)['sha256'] for path in workspace.selected}
        return workspace, {'project': project, 'resource': resource, 'profile': profile,
                           'profile_sha256': checksum(asdict(fixed)), 'inputs': hashes}

    def preview(self, core, actor, project, resource, profile, requests, request_id=None):
        if request_id is not None and (type(request_id) is not str or not 1 <= len(request_id) <= 256
                                       or any(ord(c) < 32 for c in request_id)):
            raise BoundaryError('Bounded explicit inspection request identity required')
        workspace, binding = self._binding(core, actor, project, resource, profile)
        plan = {'version': 1, 'operation': 'inspect-selected-snapshot',
                **binding, 'requests': validate_requests(workspace, requests)}
        if request_id is not None:
            plan['request_id'] = request_id
        return {'plan': plan, 'sha256': checksum(plan), 'read_only': True,
                'source_repository_complete': False}

    def _validate(self, core, actor, plan, expected_sha256):
        fields = {'version', 'operation', 'project', 'resource', 'profile', 'profile_sha256', 'inputs', 'requests'}
        if (type(plan) is not dict or set(plan) not in (fields, fields | {'request_id'}) or type(plan['version']) is not int
                or plan['version'] != 1 or plan['operation'] != 'inspect-selected-snapshot'
                or any(type(plan[key]) is not str or not 1 <= len(plan[key]) <= 256
                       for key in ('project', 'resource', 'profile'))
                or type(plan['inputs']) is not dict or checksum(plan) != expected_sha256):
            raise BoundaryError('Exact reviewed inspection plan required')
        plan = json.loads(json.dumps(plan))
        current = self.preview(core, actor, plan['project'], plan['resource'], plan['profile'], plan['requests'],
                               request_id=plan.get('request_id'))
        if current['plan'] != plan:
            raise Conflict('Inspection input or profile changed')
        return current

    def prepare(self, core, actor, plan, expected_sha256):
        plan = self._validate(core, actor, plan, expected_sha256)['plan']
        payload = {'operation': 'inspect', 'requests': plan['requests'], 'expected_inputs': plan['inputs']}
        task = core.create_task(actor, plan['project'], 'read', plan['resource'], payload,
                                'inspection:' + expected_sha256)
        return {'sha256': expected_sha256, 'task': task, 'read_only': True}

    def _task(self, core, actor, plan, sha256):
        row = core.db.execute('SELECT task FROM task_requests WHERE project=? AND request_id=?',
                              (plan['project'], 'inspection:' + sha256)).fetchone()
        if row is None:
            raise Conflict('Prepare the inspection batch first')
        task = core.task(actor, row['task'])
        if (task['action'] != 'read' or task['resource'] != plan['resource']
                or json.loads(task['payload']) != {'operation': 'inspect', 'requests': plan['requests'],
                                                  'expected_inputs': plan['inputs']}):
            raise Conflict('Inspection task identity changed')
        return task

    def step(self, core, actor, plan, expected_sha256):
        plan = self._validate(core, actor, plan, expected_sha256)['plan']
        task = self._task(core, actor, plan, expected_sha256)
        if task['state'] != 'succeeded':
            if task['state'] != 'queued':
                raise Conflict('Inspection requires explicit task recovery')
            lease = core.start(actor, task['id'])
            self.worker.perform(core, actor, task['id'], lease['lease_token'])
        return self.results(core, actor, plan, expected_sha256)

    def results(self, core, actor, plan, expected_sha256):
        plan = self._validate(core, actor, plan, expected_sha256)['plan']
        task = self._task(core, actor, plan, expected_sha256)
        if task['state'] != 'succeeded':
            return {'sha256': expected_sha256, 'complete': False, 'task': task['id'], 'results': [],
                    'state': task['state'], 'recovery_required': task['state'] != 'queued'}
        references = json.loads(task['evidence'] or '[]')
        if len(references) != 1:
            raise Conflict('Inspection evidence unavailable')
        evidence = self.worker.evidence(references[0])
        result = evidence.get('result', {})
        if (evidence.get('task_id') != task['id'] or evidence.get('operation') != 'inspect'
                or result.get('input_hashes') != plan['inputs']
                or result.get('requests') != plan['requests']):
            raise Conflict('Inspection evidence does not match its task or inputs')
        self._validate(core, actor, plan, expected_sha256)
        return {'sha256': expected_sha256, 'complete': True, 'task': task['id'],
                'state': task['state'], 'recovery_required': False,
                'evidence': references[0], 'results': result['results'],
                'source_repository_complete': False}
