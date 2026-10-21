"""Hidden Windows launcher. Close hides to tray; Exit closes an owned core process."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request

from bootstrap import protect


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def launch(state, executable, background=False):
    state, executable = Path(state).resolve(), Path(executable).resolve()
    config = json.loads((state / 'launcher.json').read_text(encoding='utf-8'))
    desktop = json.loads((state / 'desktop.json').read_text(encoding='utf-8'))
    port = config['port']
    if type(port) is not int or not 1024 <= port <= 65535 or desktop['port'] != port or (not background and not executable.is_file()):
        raise ValueError('Invalid local launcher configuration')
    if background and config.get('unattended_enabled') is not True:
        raise ValueError('Background execution must be explicitly enabled')
    if background:
        (state/'runner.stop').unlink(missing_ok=True)
    token = protect(desktop['controller_token_dpapi'], decrypt=True)
    health = urllib.request.Request(f'http://127.0.0.1:{port}/v1/health', headers={'Authorization': 'Bearer ' + token})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    def ready():
        try:
            with opener.open(health, timeout=1) as response:
                return json.loads(response.read(4096)).get('status') == 'ready'
        except urllib.error.HTTPError:
            raise RuntimeError('Another local service or credential mismatch blocks this port') from None
        except (urllib.error.URLError, TimeoutError):
            return False
    owned = None
    log = None
    try:
        if not ready():
            if config.get('unattended_enabled') is True and not background:
                # The background supervisor owns Core; exiting the UI cannot terminate it.
                supervisor = subprocess.Popen([config['python'], str(Path(__file__).resolve()), '--state', str(state), '--background'],
                                              stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                              creationflags=subprocess.CREATE_NO_WINDOW)
                for _ in range(100):
                    if supervisor.poll() is not None: raise RuntimeError('Background supervisor startup failed')
                    if ready(): break
                    time.sleep(.1)
                else: raise RuntimeError('Background Core did not become ready')
            else:
                owned = start_core(config, state)
                for _ in range(100):
                    if owned.poll() is not None: raise RuntimeError('Core startup failed')
                    if ready(): break
                    time.sleep(.1)
                else: raise RuntimeError('Core did not become ready')
        env = dict(os.environ, JARVIS_DESKTOP_CONFIG=str(state / 'desktop.json'))
        command = ([config['python'], str(Path(__file__).resolve().parents[2]/'services/runner/run.pyw'), '--state', str(state)]
                   if background else [str(executable)])
        app = subprocess.Popen(command, env=env, creationflags=subprocess.CREATE_NO_WINDOW)
        if background and owned is not None:
            while app.poll() is None:
                if owned.poll() is not None:
                    app.terminate()
                    try: app.wait(timeout=5)
                    except subprocess.TimeoutExpired: app.kill(); app.wait(timeout=5)
                    raise RuntimeError('Background Core exited; restart and inspect assignments')
                time.sleep(.25)
        else:
            app.wait()
    finally:
        if owned is not None and owned.poll() is None:
            owned.terminate()
            try: owned.wait(timeout=5)
            except subprocess.TimeoutExpired:
                owned.kill(); owned.wait(timeout=5)
        if log: log.close()


def start_core(config, state):
    argv = [config['python'], config['core_script'], '--auth-config', config['auth_config'],
            '--database', config['database'], '--port', str(config['port'])]
    for key, flag in [('workspace_config', '--workspace-config'), ('runtime_config', '--runtime-config'), ('scaffold_root', '--scaffold-root'),('node_toolchain_config','--node-toolchain-config'),('existing_project_config','--existing-project-config')]:
        if config.get(key): argv += [flag, config[key]]
    if config.get('unattended_enabled') is True: argv += ['--enable-unattended']
    if config.get('scaffold_execution_enabled') is True: argv += ['--enable-scaffold-execution']
    with (state/'core-stderr.log').open('ab') as log:
        return subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=log,
                                creationflags=subprocess.CREATE_NO_WINDOW)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, default=Path(os.environ.get('LOCALAPPDATA', '.')) / 'Skyra/Jarvis')
    parser.add_argument('--executable', type=Path, default=Path(__file__).parent / 'src-tauri/target/release/jarvis-desktop.exe')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--background', action='store_true', help='Own a hidden Core/runner independently of the desktop')
    mode.add_argument('--stop-background', action='store_true', help='Stop the hidden runner after its active step')
    args = parser.parse_args()
    try:
        if args.stop_background:
            (args.state.resolve()/'runner.stop').touch()
        else:
            launch(args.state, args.executable, args.background)
    except Exception:
        ctypes.windll.user32.MessageBoxW(None, 'Jarvis could not start. Check the private connection configuration, core log and local port. Credentials and error details are withheld.', 'Jarvis startup', 0x10)


if __name__ == '__main__': main()
