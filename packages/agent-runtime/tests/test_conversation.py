"""Conversation persistence, paid-call deduplication and planning boundaries."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import threading
import subprocess
import os
import socket
import time
import urllib.request
import unittest
import sqlite3
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
for source in ('services/core/src', 'workers/coding/src', 'packages/agent-runtime/src'):
    sys.path.insert(0, str(REPO / source))
from fastapi.testclient import TestClient
from jarvis_core import Core, Conflict, Denied
from jarvis_core.api import Credential, create_app
from jarvis_runtime.conversation import ConversationRuntime, validate_response


def plan_response():
    return {'reply': 'Draft plan for owner review.', 'plan': {
        'title': 'Client website', 'overview': 'Build and validate the agreed website.',
        'requirements': ['Responsive website'], 'deliverables': ['Website and deployment guide'],
        'phases': [{'title': 'Build', 'tasks': ['Implement approved pages'],
                    'acceptance': ['Keyboard navigation and tests pass']}],
        'risks': ['Content not yet supplied'], 'questions': ['Who supplies brand assets?']}}


class Provider:
    model = 'fixture'
    def __init__(self):
        self.calls = 0
        self.callback = None
        self.response = None
    def complete(self, system, context, schema):
        self.calls += 1
        self.context = json.loads(context)
        if self.callback:
            self.callback()
        return self.response or json.dumps(plan_response() if self.context['mode'] == 'plan' else {'reply': 'Hello from Jarvis.'}), {'total_tokens': 25}


class ConversationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / 'core.sqlite3'
        self.core = Core(self.db)
        self.project = self.core.create_project('owner', 'Chat')
        self.conversation = self.core.create_conversation('owner', self.project)
        self.provider = Provider()
        self.runtime = ConversationRuntime({'fixture': self.provider})
    def tearDown(self):
        self.core.close()
        self.temp.cleanup()
    def create(self, **kwargs):
        return self.runtime.create(self.core, 'owner', self.conversation,
            **dict({'provider': 'fixture', 'mode': 'chat', 'content': 'Help plan a website.', 'request_id': 'one'}, **kwargs))
    def test_durable_chat_atomic_messages_and_no_replay(self):
        turn = self.create()
        self.assertEqual(turn, self.create())
        self.assertEqual(0, self.provider.calls)
        result = self.runtime.generate(self.core, 'owner', turn)
        self.assertEqual('completed', result['state'])
        self.assertEqual({'total_tokens': 25}, result['usage'])
        self.assertEqual(64, len(result['context_sha256']))
        self.assertEqual(['user', 'assistant'], [m['role'] for m in self.core.messages('owner', self.conversation)])
        self.core.close(); self.core = Core(self.db)
        self.runtime.generate(self.core, 'owner', turn)
        self.assertEqual(1, self.provider.calls)
        self.assertEqual(2, len(self.core.messages('owner', self.conversation)))
    def test_plan_persisted_without_tasks_or_permissions(self):
        turn = self.create(mode='plan')
        result = self.runtime.generate(self.core, 'owner', turn)
        self.assertEqual(plan_response(), result['response'])
        self.assertIn('plan', self.provider.context['schema']['properties'])
        self.assertEqual(0, self.core.db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0])
        self.assertEqual('read_only', self.core._owned('owner', self.project)['mode'])
        self.assertEqual([], json.loads(self.core._owned('owner', self.project)['resources']))
    def test_idempotency_conflict_and_active_conversation_lock(self):
        turn = self.create()
        with self.assertRaises(Conflict): self.create(content='Other content')
        with self.assertRaises(Conflict): self.create(request_id='two')
        self.runtime.interrupt(self.core, 'owner', turn)
        self.assertNotEqual(turn, self.create(request_id='two'))
    def test_interruption_discards_late_output(self):
        turn = self.create()
        self.provider.callback = lambda: self.runtime.interrupt(self.core, 'owner', turn)
        result = self.runtime.generate(self.core, 'owner', turn)
        self.assertEqual('interrupted', result['state'])
        self.assertIsNone(result['response'])
        self.assertEqual(1, len(self.core.messages('owner', self.conversation)))
    def test_generating_survives_restart_without_billable_retry(self):
        turn = self.create()
        self.core.db.execute("UPDATE model_turns SET state='generating' WHERE id=?", (turn,))
        self.core.close(); self.core = Core(self.db)
        self.assertEqual('generating', self.runtime.generate(self.core, 'owner', turn)['state'])
        self.assertEqual(0, self.provider.calls)
        self.runtime.interrupt(self.core, 'owner', turn)
    def test_provider_failure_redacted_and_not_retried(self):
        turn = self.create()
        def fail(): raise RuntimeError('secret-api-key and full prompt')
        self.provider.callback = fail
        result = self.runtime.generate(self.core, 'owner', turn)
        self.assertEqual('generation_failed', result['error'])
        self.assertNotIn('secret-api', json.dumps(result))
        self.runtime.generate(self.core, 'owner', turn)
        self.assertEqual(1, self.provider.calls)
    def test_invalid_response_never_appended(self):
        for i, response in enumerate(['{"reply":"x","tool":"execute"}', '{"reply":"x","reply":"y"}', '{"reply":NaN}', '{"reply":""}', 'x'*48001]):
            with self.subTest(response=response[:40]):
                self.provider.response = response
                result = self.runtime.generate(self.core, 'owner', self.create(request_id=str(i)))
                self.assertEqual('invalid_model_response', result['error'])
        self.assertEqual(5, len(self.core.messages('owner', self.conversation)))
    def test_bounded_contiguous_context_with_omission_count(self):
        for i in range(45):
            self.core.append_message('owner', self.conversation, 'user', ('context'+str(i))*1500, str(i))
        result = self.runtime.get(self.core, 'owner', self.create())
        context = result['context']
        self.assertLessEqual(len(json.dumps(context, ensure_ascii=True).encode()), 48000)
        self.assertEqual(45, context['omitted_messages']+len(context['history']))
        self.assertEqual(45, context['history'][-1]['id'])
    def test_unicode_context_bound(self):
        for i in range(20): self.core.append_message('owner', self.conversation, 'user', '\U0001f680'*3000, str(i))
        with self.assertRaises(ValueError): self.create(content='\U0001f680'*8000)
        result = self.runtime.get(self.core, 'owner', self.create(content='\U0001f680'*1000))
        self.assertLessEqual(len(json.dumps(result['context']).encode()), 48000)
    def test_provider_change_and_ownership(self):
        turn = self.create()
        with self.assertRaises(Denied): self.runtime.get(self.core, 'other', turn)
        self.provider.model = 'changed'
        with self.assertRaises(Conflict): self.runtime.generate(self.core, 'owner', turn)
        self.provider.model = 'fixture'
        self.provider.provider = 'different-provider'
        with self.assertRaises(Conflict): self.runtime.generate(self.core, 'owner', turn)
        self.assertEqual(0, self.provider.calls)
    def test_plan_schema_rejects_incomplete_or_executable_fields(self):
        for key in ('requirements', 'phases', 'deliverables'):
            data = plan_response(); data['plan'][key] = []
            with self.assertRaises(ValueError): validate_response(json.dumps(data), 'plan')
        data = plan_response(); data['plan']['command'] = 'execute'
        with self.assertRaises(ValueError): validate_response(json.dumps(data), 'plan')
    def test_migration_from_six_preserves_conversation(self):
        self.core.append_message('owner', self.conversation, 'user', 'Preserve me', 'old')
        self.core.db.execute('DROP TABLE model_turns')
        self.core.db.execute('PRAGMA user_version=6')
        self.core.close(); self.core = Core(self.db)
        self.assertEqual(7, self.core.db.execute('PRAGMA user_version').fetchone()[0])
        self.assertEqual('Preserve me', self.core.messages('owner', self.conversation)[0]['content'])
        self.create()
    def test_parallel_generate_dispatches_once(self):
        turn = self.create()
        entered, release = threading.Event(), threading.Event()
        self.provider.callback = lambda: (entered.set(), release.wait(5))
        errors = []
        def run():
            try:
                core = Core(self.db)
                try: self.runtime.generate(core, 'owner', turn)
                finally: core.close()
            except Exception as exc: errors.append(exc)
        thread = threading.Thread(target=run); thread.start()
        try:
            self.assertTrue(entered.wait(5))
            self.assertEqual('generating', self.runtime.generate(self.core, 'owner', turn)['state'])
        finally:
            release.set(); thread.join(5)
        self.assertEqual([], errors)
        self.assertEqual(1, self.provider.calls)
    def test_instruction_change_rejects_dispatch(self):
        turn = self.create()
        with patch('jarvis_runtime.conversation.SYSTEM', 'Changed instructions'):
            with self.assertRaises(Conflict): self.runtime.generate(self.core, 'owner', turn)
        with patch('jarvis_runtime.conversation.CHAT_SCHEMA', {}):
            with self.assertRaises(Conflict): self.runtime.generate(self.core, 'owner', turn)
        self.assertEqual(0, self.provider.calls)

    def test_assistant_append_and_state_are_atomic(self):
        turn = self.create()
        self.core.db.execute("CREATE TRIGGER reject_assistant BEFORE INSERT ON messages WHEN NEW.role='assistant' BEGIN SELECT RAISE(ABORT,'fixture'); END")
        with self.assertRaises(sqlite3.IntegrityError): self.runtime.generate(self.core, 'owner', turn)
        self.assertEqual('generating', self.runtime.get(self.core, 'owner', turn)['state'])
        self.assertEqual(1, len(self.core.messages('owner', self.conversation)))
        self.core.db.execute('DROP TRIGGER reject_assistant')
        self.runtime.generate(self.core, 'owner', turn)
        self.assertEqual(1, self.provider.calls)
        self.runtime.interrupt(self.core, 'owner', turn)

    def test_history_and_interrupt_available_without_provider_configuration(self):
        turn = self.create()
        token = 'c'*40
        credentials = [Credential(hashlib.sha256(token.encode()).hexdigest(), 'owner', 'controller')]
        with TestClient(create_app(self.db, credentials), base_url='http://127.0.0.1', client=('127.0.0.1',123)) as client:
            headers = {'Authorization':'Bearer '+token}
            self.assertEqual(1, len(client.get(f'/v1/conversations/{self.conversation}/model-turns', headers=headers).json()['turns']))
            self.assertEqual(turn, client.get(f'/v1/model-turns/{turn}', headers=headers).json()['id'])
            self.assertEqual('interrupted',client.post(f'/v1/model-turns/{turn}/interrupt',headers=headers).json()['state'])
            self.assertEqual(503,client.post(f'/v1/model-turns/{turn}/generate',headers=headers).status_code)

    def test_real_launcher_supports_runtime_without_workspace(self):
        token = 'x'*40
        auth = Path(self.temp.name) / 'auth.json'
        config = Path(self.temp.name) / 'runtime.json'
        auth.write_text(json.dumps([{'token_sha256': hashlib.sha256(token.encode()).hexdigest(), 'actor': 'owner', 'role': 'controller'}]))
        config.write_text(json.dumps({'providers': [{'name':'fixture','provider':'gemini','model':'fixture-model','api_key_env':'JARVIS_CHAT_TEST_KEY','timeout':1,'max_output_tokens':256}], 'skills':[]}))
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
        process = subprocess.Popen([sys.executable, '-I', str(REPO/'services/core/run.py'), '--auth-config',str(auth),'--database',str(self.db),'--runtime-config',str(config),'--port',str(port)],
            env=dict(os.environ,JARVIS_CHAT_TEST_KEY='fixture-not-real'),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        try:
            result=None
            for _ in range(100):
                if process.poll() is not None: self.fail('Chat-only launcher exited before readiness')
                try:
                    request=urllib.request.Request(f'http://127.0.0.1:{port}/v1/setup',headers={'Authorization':'Bearer '+token})
                    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
                    with opener.open(request,timeout=1) as response: result=json.load(response)
                    break
                except OSError: time.sleep(.1)
            self.assertIsNotNone(result)
            self.assertFalse(result['repair_available'])
            self.assertEqual('fixture-model',result['conversation']['providers'][0]['model'])
        finally:
            process.terminate(); process.wait(timeout=10)

    def test_api_controller_only_without_worker(self):
        owner, agent, other = 'o'*40, 'a'*40, 'b'*40
        credentials = [Credential(hashlib.sha256(token.encode()).hexdigest(), actor, role, scope)
            for token, actor, role, scope in [(owner, 'owner', 'controller', frozenset()),
                (agent, 'owner', 'agent', frozenset({self.project})), (other, 'other', 'controller', frozenset())]]
        with TestClient(create_app(self.db, credentials, conversation_runtime=self.runtime), base_url='http://127.0.0.1', client=('127.0.0.1',123)) as client:
            headers = {'Authorization':'Bearer '+owner}
            setup = client.get('/v1/setup', headers=headers).json()
            self.assertFalse(setup['repair_available'])
            self.assertEqual(['chat','plan'], setup['conversation']['modes'])
            path = f'/v1/conversations/{self.conversation}/model-turns'
            body = {'provider':'fixture','mode':'chat','content':'Hi','request_id':'api'}
            self.assertEqual(403, client.post(path, json=body, headers={'Authorization':'Bearer '+agent}).status_code)
            self.assertEqual(403, client.post(path, json=body, headers={'Authorization':'Bearer '+other}).status_code)
            turn = client.post(path,json=body,headers=headers).json()['turn_id']
            self.assertEqual(1,len(client.get(path,headers=headers).json()['turns']))
            result = client.post(f'/v1/model-turns/{turn}/generate',headers=headers)
            self.assertEqual('completed',result.json()['state'])
            self.assertEqual(403,client.get(f'/v1/model-turns/{turn}',headers={'Authorization':'Bearer '+other}).status_code)

if __name__ == '__main__': unittest.main()
