import importlib.util
from importlib.machinery import SourceFileLoader
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import MagicMock, patch

SCRIPT = Path(__file__).resolve().parents[1]/'run.pyw'
loader = SourceFileLoader('jarvis_background_runner', str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
runner = importlib.util.module_from_spec(spec)
loader.exec_module(runner)


@unittest.skipUnless(os.name == 'nt', 'Windows runner and DPAPI')
class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.state = Path(self.temp.name)
        self.project = 'a'*32
        self.config = {'projects': [self.project], 'interval_seconds': 2}
        (self.state/'runner.json').write_text(json.dumps(self.config))
        (self.state/'desktop.json').write_text(json.dumps({'port': 18010, 'worker_token_dpapi': runner.protect('worker-test-'+'z'*40)}))

    def tearDown(self): self.temp.cleanup()

    def test_private_configuration_uses_only_worker_credential(self):
        config, port, token = runner.configuration(self.state)
        self.assertEqual(self.config, config); self.assertEqual(18010, port)
        self.assertTrue(token.startswith('worker-test-'))
        self.assertNotIn(token, (self.state/'desktop.json').read_text())

    def test_loop_reports_safe_status_and_honors_stop_file(self):
        statuses = []
        with patch.object(runner, 'tick', return_value={'assignment': None}) as tick, patch.object(runner, 'write_status', side_effect=lambda state, value: statuses.append(value)):
            runner.run(self.state, once=True)
            self.assertEqual(1, tick.call_count)
        self.assertEqual('idle', statuses[0]['projects'][0]['state'])
        self.assertEqual('stopped', statuses[-1]['state'])
        (self.state/'runner.stop').touch()
        with patch.object(runner, 'tick') as tick:
            runner.run(self.state, once=True)
            tick.assert_not_called()

    def test_single_profile_lock_prevents_duplicate_runner(self):
        import msvcrt
        with (self.state/'runner.lock').open('w+b') as lock:
            lock.write(b'0'); lock.flush(); lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            try:
                with self.assertRaises(OSError): runner.run(self.state, once=True)
            finally:
                lock.seek(0); msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)

    def test_http_transport_is_fixed_loopback_post_and_redirects_are_denied(self):
        response = MagicMock(); response.__enter__.return_value.read.return_value = b'{"assignment":null}'
        opener = MagicMock(); opener.open.return_value = response
        runner.tick(opener, 18010, 'fixture-token', self.project)
        request = opener.open.call_args.args[0]
        self.assertEqual(7260, opener.open.call_args.kwargs['timeout'])
        self.assertEqual('http://127.0.0.1:18010/v1/runner/tick', request.full_url)
        self.assertEqual('POST', request.method)
        self.assertEqual({'project': self.project}, json.loads(request.data))
        self.assertIsNone(runner.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://example.com'))

    def test_connection_failures_do_not_write_raw_error_or_token(self):
        statuses = []
        with patch.object(runner, 'tick', side_effect=OSError('sensitive-error-detail')), patch.object(runner, 'write_status', side_effect=lambda state, value: statuses.append(value)):
            runner.run(self.state, once=True)
        self.assertNotIn('sensitive-error-detail', json.dumps(statuses))
        self.assertIn('connection_or_response_unavailable', json.dumps(statuses))

    def test_configuration_rejects_unknown_fields_and_unbounded_polling(self):
        for value in ({**self.config, 'url': 'https://example.com'}, {**self.config, 'interval_seconds': 0},
                      {**self.config, 'projects': ['../outside']}):
            (self.state/'runner.json').write_text(json.dumps(value))
            with self.assertRaises(ValueError): runner.configuration(self.state)


class DispatcherTests(unittest.TestCase):
    def test_long_project_does_not_block_other_projects_or_duplicate_inflight(self):
        release=threading.Event(); started=threading.Event(); calls=[]; lock=threading.Lock()
        def operation(project):
            with lock:calls.append(project)
            if project=='long':started.set();release.wait(5)
            return {'build_job':{'state':'completed'}}
        dispatcher=runner.ProjectDispatcher(['long','short'],operation)
        try:
            dispatcher.poll();self.assertTrue(started.wait(2))
            deadline=time.monotonic()+2
            while 'short' not in dispatcher.last and time.monotonic()<deadline:
                time.sleep(.02);dispatcher.poll()
            self.assertEqual('completed',dispatcher.last['short']['state'])
            self.assertEqual(1,calls.count('long'))
            self.assertIn('long',dispatcher.active)
        finally:release.set()

    def test_dispatch_slots_are_bounded_and_round_robin_is_fair(self):
        release=threading.Event(); calls=[];lock=threading.Lock()
        def operation(project):
            with lock:calls.append(project)
            release.wait(5);return {'assignment':None}
        dispatcher=runner.ProjectDispatcher([str(i) for i in range(9)],operation)
        try:
            dispatcher.poll();self.assertEqual(4,len(dispatcher.active))
            for _ in range(3):dispatcher.poll()
            self.assertEqual(4,len(dispatcher.active));self.assertEqual(4,len(set(calls)))
            release.set();deadline=time.monotonic()+3
            while len(set(calls))<9 and time.monotonic()<deadline:
                time.sleep(.02);dispatcher.poll()
            self.assertEqual(9,len(set(calls)))
        finally:release.set()

    def test_dispatch_failure_status_does_not_expose_raw_exception(self):
        result=runner.outcome(lambda project:(_ for _ in ()).throw(ValueError('private-token')), 'p')
        self.assertEqual('connection_or_response_unavailable',result['state'])
        self.assertNotIn('private-token',json.dumps(result))
        with self.assertRaises(ValueError):runner.ProjectDispatcher([],lambda p:None)
        with self.assertRaises(ValueError):runner.ProjectDispatcher(['p','p'],lambda p:None)


if __name__ == '__main__': unittest.main()
