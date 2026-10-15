import hashlib
import secrets
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sqlite3

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from fastapi.testclient import TestClient
from jarvis_core import Core
from jarvis_core.api import Credential, create_app


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / 'core.sqlite3'
        c = Core(self.database)
        self.project = c.create_project('owner', 'Allowed')
        self.other = c.create_project('owner', 'Other')
        c.set_policy('owner', self.project, 'ask', ['workspace:demo'])
        c.close()
        self.tokens = {role: secrets.token_urlsafe(32) for role in ['controller', 'agent', 'worker', 'outsider']}
        self.credentials = [Credential(hashlib.sha256(token.encode()).hexdigest(),
                           'other-owner' if role == 'outsider' else 'owner',
                           'controller' if role == 'outsider' else role,
                           frozenset() if role in {'controller', 'outsider'} else frozenset({self.project}))
                           for role, token in self.tokens.items()]
        self.app = create_app(self.database, self.credentials)
        self.client = TestClient(self.app, base_url='http://127.0.0.1', client=('127.0.0.1', 50000))

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def call(self, method, path, role='controller', **kwargs):
        headers = {'Authorization': 'Bearer '+self.tokens[role], **kwargs.pop('headers', {})}
        return self.client.request(method, path, headers=headers, **kwargs)

    def task(self, action='write', request_id=None):
        response = self.call('POST', f'/v1/projects/{self.project}/tasks', 'agent', json={
            'action': action, 'resource': 'workspace:demo', 'payload': {'file': 'demo.py'},
            'request_id': request_id or secrets.token_hex(8)})
        self.assertEqual(201, response.status_code, response.text)
        return response.json()['task_id']

    def test_every_route_needs_header_authentication(self):
        for path in ['/v1/health', '/v1/projects', '/v1/openapi.json', '/docs']:
            self.assertEqual(401, self.client.get(path).status_code)
        self.assertEqual(401, self.client.get('/v1/health?token='+self.tokens['controller']).status_code)
        self.assertEqual(401, self.client.get('/v1/health', headers={'Authorization': 'Bearer invalid'}).status_code)

    def test_browser_origin_and_untrusted_host_are_rejected(self):
        self.assertEqual(403, self.call('GET', '/v1/health', headers={'Origin': 'https://evil.example'}).status_code)
        self.assertEqual(403, self.call('GET', '/v1/health', headers={'Origin': 'null'}).status_code)
        self.assertEqual(400, self.call('GET', '/v1/health', headers={'Host': 'evil.example'}).status_code)

    def test_remote_client_and_forwarded_headers_do_not_grant_access(self):
        with TestClient(self.app, base_url='http://127.0.0.1', client=('198.51.100.1', 50000)) as remote:
            response = remote.get('/v1/health', headers={'Authorization': 'Bearer '+self.tokens['controller'], 'X-Forwarded-For': '127.0.0.1'})
            self.assertEqual(403, response.status_code)

    def test_agent_cannot_change_policy_or_create_project(self):
        self.assertEqual(403, self.call('PUT', f'/v1/projects/{self.project}/policy', 'agent',
                         json={'mode': 'full', 'resources': ['workspace:demo']}).status_code)
        self.assertEqual(403, self.call('POST', '/v1/projects', 'agent', json={'name': 'Escalation'}).status_code)

    def test_project_scope_and_actor_boundary(self):
        listing = self.call('GET', '/v1/projects', 'agent').json()['projects']
        self.assertEqual([self.project], [p['id'] for p in listing])
        self.assertEqual(403, self.call('GET', f'/v1/projects/{self.other}/events', 'agent').status_code)
        self.assertEqual(403, self.call('GET', f'/v1/projects/{self.project}/events', 'outsider').status_code)

    def test_approval_cannot_be_self_issued_and_task_cannot_self_complete(self):
        t = self.task()
        self.assertEqual(403, self.call('POST', f'/v1/tasks/{t}/start', 'agent').status_code)
        response = self.call('POST', f'/v1/tasks/{t}/start', 'worker')
        self.assertEqual(200, response.status_code, response.text)
        a = response.json()['approval_id']
        for role in ['agent', 'worker']:
            self.assertEqual(403, self.call('POST', f'/v1/approvals/{a}/decision', role, json={'approve': True}).status_code)
        review = self.call('GET', f'/v1/approvals/{a}').json()
        self.assertEqual('write', review['task']['action'])
        self.assertEqual(200, self.call('POST', f'/v1/approvals/{a}/decision', json={'approve': True}).status_code)
        claimed = self.call('POST', f'/v1/tasks/{t}/start', 'worker').json()
        lease = claimed['lease_token']
        for role in ['agent', 'controller', 'worker']:
            self.assertNotIn(lease, self.call('GET', f'/v1/tasks/{t}', role).text)
        body = {'lease_token': lease, 'evidence': ['artifact:tests'], 'success': True}
        self.assertEqual(403, self.call('POST', f'/v1/tasks/{t}/complete', 'agent', json=body).status_code)
        self.assertEqual(200, self.call('POST', f'/v1/tasks/{t}/complete', 'worker', json=body).status_code)
        self.assertEqual('succeeded', self.call('GET', f'/v1/tasks/{t}').json()['state'])

    def test_task_retry_is_idempotent_across_app_restart(self):
        t = self.task(request_id='same-request')
        self.client.close()
        self.client = TestClient(create_app(self.database, self.credentials), base_url='http://127.0.0.1', client=('127.0.0.1',50000))
        self.assertEqual(t, self.task(request_id='same-request'))
        r = self.call('POST', f'/v1/projects/{self.project}/tasks', 'agent', json={
            'action': 'execute', 'resource': 'workspace:demo', 'payload': {}, 'request_id': 'same-request'})
        self.assertEqual(409, r.status_code)

    def test_policy_revocation_prevents_claim_after_approval(self):
        t = self.task()
        a = self.call('POST', f'/v1/tasks/{t}/start', 'worker').json()['approval_id']
        self.call('POST', f'/v1/approvals/{a}/decision', json={'approve': True})
        self.call('PUT', f'/v1/projects/{self.project}/policy', json={'mode': 'read_only', 'resources': ['workspace:demo']})
        self.assertEqual(403, self.call('POST', f'/v1/tasks/{t}/start', 'worker').status_code)

    def test_message_roles_and_content_validation(self):
        c = self.call('POST', f'/v1/projects/{self.project}/conversations').json()['conversation_id']
        body = {'role': 'user', 'content': 'private-test-content', 'request_id': 'message-1'}
        self.assertEqual(403, self.call('POST', f'/v1/conversations/{c}/messages', 'agent', json=body).status_code)
        self.assertEqual(201, self.call('POST', f'/v1/conversations/{c}/messages', json=body).status_code)
        self.assertEqual(403, self.call('GET', f'/v1/conversations/{c}/messages', 'worker').status_code)
        body['actor'] = 'someone-else'
        response = self.call('POST', f'/v1/conversations/{c}/messages', json=body)
        self.assertEqual(422, response.status_code)
        self.assertNotIn('private-test-content', response.text)

    def test_strict_boolean_decision_and_sanitized_errors(self):
        t = self.task()
        a = self.call('POST', f'/v1/tasks/{t}/start', 'worker').json()['approval_id']
        response = self.call('POST', f'/v1/approvals/{a}/decision', json={'approve': 'true'})
        self.assertEqual(422, response.status_code)
        self.assertEqual(response.headers['x-request-id'], response.json()['error']['request_id'])
        self.assertEqual('no-store', response.headers['cache-control'])

    def test_oversized_and_malformed_requests(self):
        self.assertEqual(413, self.call('POST', '/v1/projects', content=b'x'*131073,
                         headers={'Content-Type': 'application/json'}).status_code)
        for content in ['{"name":"first","name":"second"}', '{"name":NaN}', '{broken']:
            self.assertEqual(400, self.call('POST', '/v1/projects', content=content,
                             headers={'Content-Type': 'application/json'}).status_code)
        self.assertEqual(415, self.call('POST', '/v1/projects', content='name=demo',
                         headers={'Content-Type': 'application/x-www-form-urlencoded'}).status_code)

    def test_duplicate_authorization_headers_rejected(self):
        response = self.client.get('/v1/health', headers=[('Authorization','Bearer '+self.tokens['controller']),
                                  ('Authorization','Bearer '+self.tokens['agent'])])
        self.assertEqual(401, response.status_code)

    def test_event_replay_is_bounded_and_schema_is_protected(self):
        self.task('read')
        response = self.call('GET', f'/v1/projects/{self.project}/events?limit=1', 'agent')
        events = response.json()['events']
        self.assertEqual(1, len(events))
        next_events = self.call('GET', f'/v1/projects/{self.project}/events?after={events[0]["id"]}', 'agent').json()['events']
        self.assertTrue(all(e['id'] > events[0]['id'] for e in next_events))
        self.assertEqual(422, self.call('GET', f'/v1/projects/{self.project}/events?limit=100000').status_code)
        self.assertEqual(403, self.call('GET', '/v1/openapi.json', 'agent').status_code)
        self.assertIn('/v1/projects', self.call('GET', '/v1/openapi.json').json()['paths'])

    def test_storage_error_does_not_leak_paths_or_credentials(self):
        with patch.object(Core, 'projects', side_effect=sqlite3.OperationalError('secret-database-path')):
            response = self.call('GET', '/v1/projects')
        self.assertEqual(503, response.status_code)
        self.assertNotIn('secret-database-path', response.text)

    def test_reconciliation_and_cancel_are_controller_only(self):
        t = self.task('read')
        for role in ['agent', 'worker']:
            self.assertEqual(403, self.call('POST', f'/v1/tasks/{t}/cancel', role).status_code)
            self.assertEqual(403, self.call('POST', f'/v1/projects/{self.project}/recover', role).status_code)
            self.assertEqual(403, self.call('POST', f'/v1/tasks/{t}/reconcile', role,
                             json={'outcome': 'retry', 'evidence': ['report']}).status_code)

    def test_credential_registry_fails_closed(self):
        with self.assertRaises(ValueError): create_app(self.database, [])
        with self.assertRaises(ValueError): create_app(self.database, [self.credentials[0],self.credentials[0]])
        with self.assertRaises(ValueError): Credential('0'*64, 'owner', 'agent')
        with self.assertRaises(ValueError): Credential('not-a-hash', 'owner', 'controller')

    def test_chunked_body_limit_without_content_length(self):
        chunks = iter([b'x' * 70_000, b'y' * 70_000])
        response = self.call('POST', '/v1/projects', content=chunks,
                             headers={'Content-Type': 'application/json'})
        self.assertEqual(413, response.status_code)

    def test_workers_cannot_inspect_other_projects_task(self):
        core = Core(self.database)
        try:
            task = core.create_task('owner', self.other, 'read', 'workspace:demo', {})
        finally:
            core.close()
        self.assertEqual(403, self.call('GET', f'/v1/tasks/{task}', 'worker').status_code)
        self.assertEqual(403, self.call('POST', f'/v1/tasks/{task}/start', 'worker').status_code)


    def test_dashboard_is_controller_only_and_has_no_tokens_or_private_task_payload(self):
        task = self.task()
        self.call('POST', f'/v1/tasks/{task}/start', 'worker')
        path = f'/v1/projects/{self.project}/dashboard'
        self.assertEqual(403, self.call('GET', path, 'agent').status_code)
        self.assertEqual(403, self.call('GET', path, 'worker').status_code)
        self.assertEqual(403, self.call('GET', path, 'outsider').status_code)
        response = self.call('GET', path)
        self.assertEqual(200, response.status_code, response.text)
        data = response.json()
        self.assertEqual('ask', data['project']['mode'])
        self.assertEqual(['workspace:demo'], data['project']['resources'])
        self.assertTrue(data['approvals'][0]['decidable'])
        self.assertNotIn('lease_token', response.text)
        self.assertNotIn('payload', response.text)
        self.assertEqual([], data['workspaces'])
        self.assertEqual([], data['runtime']['providers'])

    def test_permission_update_checks_the_reviewed_version(self):
        path = f'/v1/projects/{self.project}/policy'
        body = {'mode': 'full', 'resources': ['workspace:demo'], 'expected_version': 2}
        self.assertEqual(403, self.call('PUT', path, 'agent', json=body).status_code)
        self.assertEqual(200, self.call('PUT', path, json=body).status_code)
        self.assertEqual(409, self.call('PUT', path, json=body).status_code)
        dashboard = self.call('GET', f'/v1/projects/{self.project}/dashboard').json()
        self.assertEqual(3, dashboard['project']['version'])
        self.assertEqual('full', dashboard['project']['mode'])

    def test_dashboard_invalidates_old_approvals_and_separates_project_history(self):
        task = self.task()
        self.call('POST', f'/v1/tasks/{task}/start', 'worker')
        c = Core(self.database)
        try:
            conversation = c.create_conversation('owner', self.project)
            c.append_message('owner', conversation, 'user', 'PRIVATE_BODY', 'message-1')
            c.create_conversation('owner', self.other)
            c.set_policy('owner', self.project, 'ask', ['workspace:demo'])
        finally: c.close()
        response = self.call('GET', f'/v1/projects/{self.project}/dashboard')
        data = response.json()
        self.assertFalse(data['approvals'][0]['decidable'])
        self.assertEqual([{'id': conversation, 'message_count': 1}], data['conversations'])
        self.assertNotIn('PRIVATE_BODY', response.text)
        other = self.call('GET', f'/v1/projects/{self.other}/dashboard').json()
        self.assertEqual([], other['approvals'])


if __name__ == '__main__':
    unittest.main()
