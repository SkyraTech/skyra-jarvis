import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from importlib.machinery import SourceFileLoader
import sys

DESKTOP = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('desktop_bootstrap', DESKTOP / 'bootstrap.py')
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)
sys.path.insert(0, str(DESKTOP))
launcher_loader = SourceFileLoader('desktop_launcher', str(DESKTOP / 'launch.pyw'))
launcher_spec = importlib.util.spec_from_loader(launcher_loader.name, launcher_loader)
launcher = importlib.util.module_from_spec(launcher_spec)
launcher_loader.exec_module(launcher)


@unittest.skipUnless(os.name == 'nt', 'Windows DPAPI')
class BootstrapTests(unittest.TestCase):
    def test_dpapi_round_trip_and_invalid_ciphertext(self):
        token = 'fixture-token-' + 'a' * 32
        encrypted = bootstrap.protect(token)
        self.assertNotIn(token, encrypted)
        self.assertEqual(token, bootstrap.protect(encrypted, decrypt=True))
        with self.assertRaises(Exception): bootstrap.protect('invalid', decrypt=True)

    def test_initialization_preserves_existing_state_and_enables_no_providers(self):
        with tempfile.TemporaryDirectory() as temp:
            root = bootstrap.initialize(Path(temp) / 'private', 18010)
            desktop = json.loads((root / 'desktop.json').read_text())
            auth = json.loads((root / 'auth.json').read_text())
            token = bootstrap.protect(desktop['controller_token_dpapi'], decrypt=True)
            self.assertTrue(len(token) >= 32)
            self.assertNotIn(token, (root / 'auth.json').read_text())
            self.assertNotIn(token, (root / 'desktop.json').read_text())
            self.assertIsNone(desktop['worker_token_dpapi'])
            self.assertEqual('controller', auth[0]['role'])
            config = json.loads((root / 'launcher.json').read_text())
            self.assertIsNone(config['workspace_config'])
            self.assertIsNone(config['runtime_config'])
            with self.assertRaises(ValueError): bootstrap.initialize(root)

    def launch_fixture(self, root):
        state = bootstrap.initialize(root / 'state', 18011)
        executable = root / 'fixture.exe'
        executable.touch()
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'{"status":"ready"}'
        return state, executable, response

    def test_launcher_hides_children_and_stops_only_the_core_it_started(self):
        with tempfile.TemporaryDirectory() as temp:
            state, executable, response = self.launch_fixture(Path(temp))
            core, app = MagicMock(), MagicMock()
            core.poll.return_value = None
            opener = MagicMock()
            opener.open.side_effect = [launcher.urllib.error.URLError('not ready'), response]
            with patch.object(launcher.urllib.request, 'build_opener', return_value=opener), patch.object(launcher.subprocess, 'Popen', side_effect=[core, app]) as spawn:
                launcher.launch(state, executable)
            self.assertEqual(2, spawn.call_count)
            self.assertTrue(all(call.kwargs['creationflags'] == launcher.subprocess.CREATE_NO_WINDOW for call in spawn.call_args_list))
            self.assertTrue(all('shell' not in call.kwargs for call in spawn.call_args_list))
            core.terminate.assert_called_once()
            app.wait.assert_called_once()

    def test_launcher_preserves_an_existing_core_and_blocks_redirects(self):
        with tempfile.TemporaryDirectory() as temp:
            state, executable, response = self.launch_fixture(Path(temp))
            opener, app = MagicMock(), MagicMock()
            opener.open.return_value = response
            with patch.object(launcher.urllib.request, 'build_opener', return_value=opener), patch.object(launcher.subprocess, 'Popen', return_value=app) as spawn:
                launcher.launch(state, executable)
            self.assertEqual(1, spawn.call_count)
            app.terminate.assert_not_called()
            self.assertIsNone(launcher.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://example.com'))

    def test_enabled_ui_delegates_core_ownership_to_hidden_supervisor(self):
        with tempfile.TemporaryDirectory() as temp:
            state, executable, response = self.launch_fixture(Path(temp))
            config = json.loads((state/'launcher.json').read_text())
            config['unattended_enabled'] = True
            (state/'launcher.json').write_text(json.dumps(config))
            supervisor, app, opener = MagicMock(), MagicMock(), MagicMock()
            supervisor.poll.return_value = None
            opener.open.side_effect = [launcher.urllib.error.URLError('not ready'), response]
            with patch.object(launcher.urllib.request, 'build_opener', return_value=opener), patch.object(launcher.subprocess, 'Popen', side_effect=[supervisor, app]) as spawn:
                launcher.launch(state, executable)
            self.assertIn('--background', spawn.call_args_list[0].args[0])
            supervisor.terminate.assert_not_called()
            supervisor.kill.assert_not_called()
            app.wait.assert_called_once()

    def test_background_mode_requires_owner_enablement(self):
        with tempfile.TemporaryDirectory() as temp:
            state, executable, _ = self.launch_fixture(Path(temp))
            with self.assertRaises(ValueError): launcher.launch(state, executable, background=True)


if __name__ == '__main__': unittest.main()
