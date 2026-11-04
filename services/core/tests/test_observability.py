import hashlib
import json
from pathlib import Path
import subprocess
import secrets
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from fastapi.testclient import TestClient
from jarvis_core.api import Credential, create_app
from jarvis_core.observability import LogHub, LoggedApplication
from skyra_logger import validate_log_event

REPO = Path(__file__).resolve().parents[3]


class ObservabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def records(self):
        result = []
        for path in self.root.rglob('*.jsonl'):
            text = path.read_text(encoding='utf-8')
            self.assertTrue(text.endswith('\n'))
            for line in text.splitlines():
                event = json.loads(line)
                self.assertEqual(validate_log_event(event), (True, []))
                self.assertEqual(event['skyra']['project_id'], 'skyra-jarvis')
                self.assertEqual(event['service']['environment'], 'test')
                self.assertIn(event['service']['node']['name'], str(path))
                result.append(event)
        return result

    def test_installed_artifact_and_private_canonical_events(self):
        wheel = REPO/'vendor/skyra_logger-1.0.0-py3-none-any.whl'
        self.assertEqual(hashlib.sha256(wheel.read_bytes()).hexdigest(),
                         '6f9fdb21f6ccd1e171b8c7af8f4a4908814654b1523bcba43b5f050199ba6131')
        logger = LogHub(self.root/'logs', environment='test')
        try:
            logger.event('runner.dispatch.failed', project_id='a'*32, password='NEVER-LOG',
                         token='NEVER-LOG', body='NEVER-LOG', route='/v1/secret?token=NEVER-LOG')
            logger.event('unknown-user-message', body='NEVER-LOG')
            logger.flush()
        finally:
            logger.close()
        events = self.records()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['skyra']['business'], {'project_id': 'a'*32})
        self.assertNotIn('NEVER-LOG', json.dumps(events))
        self.assertEqual(logger.diagnostics()['errors'], 0)
        logger.close()
        logger.event('application.started')
        self.assertEqual(len(self.records()), 1)

    def test_asgi_lifecycle_and_http_keep_responses_and_body_private(self):
        logger = LogHub(self.root/'logs', environment='test')
        token = secrets.token_urlsafe(32)
        credentials = [Credential(hashlib.sha256(token.encode()).hexdigest(), 'owner', 'controller')]
        app = create_app(self.root/'state.sqlite3', credentials)
        try:
            with TestClient(LoggedApplication(app, logger), base_url='http://127.0.0.1',
                            client=('127.0.0.1', 50000)) as client:
                denied = client.get('/v1/projects?password=SECRET-QUERY')
                self.assertEqual(denied.status_code, 401)
                created = client.post('/v1/projects', headers={'Authorization': 'Bearer '+token},
                                      json={'name': 'SECRET-CLIENT-NAME'})
                self.assertEqual(created.status_code, 201)
            logger.flush()
        finally:
            logger.close()
        events = self.records()
        actions = [event['event']['action'] for event in events]
        for action in ['application.started', 'application.shutdown', 'http.request.failed', 'http.request.completed']:
            self.assertIn(action, actions)
        for secret in [token, 'SECRET-QUERY', 'SECRET-CLIENT-NAME']:
            self.assertNotIn(secret, json.dumps(events))
        successful = next(e for e in events if e['event']['action'] == 'http.request.completed')
        self.assertEqual(successful['skyra']['business']['route'], '/v1/projects')
        self.assertEqual(successful['skyra']['business']['core_request_id'], created.headers['x-request-id'])

    def test_disabled_and_failed_storage_are_nonfatal(self):
        disabled = LogHub(self.root/'disabled', environment='test', enabled=False)
        disabled.event('application.started'); disabled.flush(); disabled.close()
        self.assertFalse((self.root/'disabled').exists())
        blocked = self.root/'blocked'; blocked.write_text('not a directory')
        logger = LogHub(blocked, environment='test')
        try:
            logger.event('application.started'); logger.flush()
        finally:
            logger.close()
        self.assertGreater(logger.diagnostics()['errors'], 0)

    def test_queue_overflow_is_bounded_and_reported(self):
        entered, release = threading.Event(), threading.Event()

        class SlowSDK:
            def log(self, *_args):
                entered.set(); release.wait(3)
            def flush(self, **_kwargs): pass
            def close(self, **_kwargs): pass

        with patch('skyra_logger.create_skyra_logger', return_value=SlowSDK()):
            logger = LogHub(self.root, environment='test')
            try:
                logger.event('application.started'); self.assertTrue(entered.wait(2))
                for _ in range(600): logger.event('application.started')
                self.assertGreater(logger.diagnostics()['dropped'], 0)
                self.assertLessEqual(logger._queue.qsize(), 512)
            finally:
                release.set(); logger.close()

    def test_stalled_flush_has_bounded_wait(self):
        release = threading.Event()

        class StalledSDK:
            def flush(self, **_kwargs): release.wait(4)
            def close(self, **_kwargs): pass

        with patch('skyra_logger.create_skyra_logger', return_value=StalledSDK()):
            logger = LogHub(self.root, environment='test')
            try:
                logger.flush()
                self.assertEqual(logger.diagnostics()['shutdown_timeouts'], 1)
            finally:
                release.set(); logger.close()

    def test_launcher_configuration_failure_logs_safely_and_can_disable(self):
        for disabled in [False, True]:
            directory = self.root/str(disabled)
            command = [sys.executable, str(REPO/'services/core/run.py'), '--auth-config',
                       str(self.root/'missing.json'), '--database', str(directory/'core.sqlite3')]
            if disabled: command.append('--no-logging')
            result = subprocess.run(command, capture_output=True, text=True, timeout=12)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn('Traceback', result.stderr)
            self.assertEqual(bool(list(directory.rglob('*.jsonl'))), not disabled)


if __name__ == '__main__':
    unittest.main()
