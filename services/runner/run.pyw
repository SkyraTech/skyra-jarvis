"""Hidden per-user assignment runner. Requires explicit private configuration."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import queue
import threading
import time
import urllib.error
import urllib.request

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO/'apps/desktop'))
from bootstrap import protect
sys.path.insert(0, str(REPO/'services/core/src'))
from jarvis_core.observability import LogHub


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def configuration(state):
    config = json.loads((state/'runner.json').read_text(encoding='utf-8'))
    desktop = json.loads((state/'desktop.json').read_text(encoding='utf-8'))
    if (set(config) != {'projects', 'interval_seconds'} or not isinstance(config['projects'], list)
            or not 1 <= len(config['projects']) <= 100
            or len(set(config['projects'])) != len(config['projects'])
            or not all(isinstance(p, str) and len(p) == 32 and all(c in '0123456789abcdef' for c in p) for p in config['projects'])
            or type(config['interval_seconds']) is not int or not 2 <= config['interval_seconds'] <= 60
            or type(desktop['port']) is not int or not 1024 <= desktop['port'] <= 65535):
        raise ValueError('Invalid runner configuration')
    token = protect(desktop['worker_token_dpapi'], decrypt=True)
    return config, desktop['port'], token


def write_status(state, status):
    """Best-effort observation only; readers must never stop dispatch on Windows."""
    temp = None
    try:
        fd, temp = tempfile.mkstemp(prefix='.runner-status-', dir=state)
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(status, stream); stream.flush(); os.fsync(stream.fileno())
        for delay in (0, .01, .025, .05, .1):
            if delay: time.sleep(delay)
            try:
                os.replace(temp, state/'runner-status.json')
                return True
            except PermissionError:
                continue
        return False
    except OSError:
        return False
    finally:
        if temp:
            try: os.unlink(temp)
            except OSError: pass


def tick(opener, port, token, project):
    request = urllib.request.Request(f'http://127.0.0.1:{port}/v1/runner/tick',
        data=json.dumps({'project': project}).encode(), method='POST',
        headers={'Authorization': 'Bearer '+token, 'Content-Type': 'application/json'})
    with opener.open(request, timeout=7260) as response:
        payload = response.read(262145)
        if len(payload) > 262144: raise ValueError('Runner response exceeds limit')
        return json.loads(payload)


def approved_projects(opener, port, token):
    """Read-only discovery; failures retain the last explicit project set."""
    request = urllib.request.Request(f'http://127.0.0.1:{port}/v1/runner/projects', headers={'Authorization': 'Bearer '+token})
    try:
        with opener.open(request, timeout=2) as response:
            payload = response.read(32769)
        if len(payload) > 32768: return None
        value = json.loads(payload)
        rows = value.get('projects') if isinstance(value, dict) else None
        if (not isinstance(rows, list) or len(rows) > 100 or len(set(rows)) != len(rows)
                or not all(isinstance(p, str) and len(p) == 32 and all(c in '0123456789abcdef' for c in p) for p in rows)):
            return None
        return rows
    except (OSError, ValueError, TypeError): return None


def outcome(operation, project):
    try:
        result = operation(project)
        assignment = result.get('delivery') or result.get('assignment') or result.get('build_job')
        return {'project': project, 'state': assignment['state'] if assignment else 'idle'}
    except urllib.error.HTTPError as exc:
        return {'project': project, 'state': 'http_'+str(exc.code)}
    except Exception:
        # Unknown transport/response failures are uncertain, never replay here.
        return {'project': project, 'state': 'connection_or_response_unavailable'}


class ProjectDispatcher:
    """Bounded independent project requests; one in flight per project."""
    def __init__(self, projects, operation):
        if not projects or len(projects) > 100 or len(set(projects)) != len(projects) or not callable(operation):
            raise ValueError('Unique bounded projects and dispatcher required')
        self.projects = tuple(projects)
        self.operation = operation
        self.active = {}
        self.results = queue.Queue(maxsize=4)
        self.last = {}
        self.cursor = 0

    def _request(self, project):
        self.results.put(outcome(self.operation, project))

    def update_projects(self, projects):
        if not isinstance(projects, list) or len(projects)>100 or len(set(projects))!=len(projects):
            raise ValueError('Unique bounded projects required')
        if tuple(projects) != self.projects:
            self.projects=tuple(projects);self.cursor=0

    def poll(self):
        while True:
            try: result = self.results.get_nowait()
            except queue.Empty: break
            project = result['project']
            self.active.pop(project, None)
            self.last[project] = result
        for _ in range(len(self.projects)):
            if len(self.active) >= 4: break
            project = self.projects[self.cursor]
            self.cursor = (self.cursor + 1) % len(self.projects)
            if project in self.active: continue
            thread = threading.Thread(target=self._request, args=(project,), daemon=True)
            self.active[project] = thread
            thread.start()
        return [{'project': p, 'state': 'dispatching', 'last_outcome': self.last.get(p, {}).get('state')} if p in self.active
                else self.last.get(p, {'project': p, 'state': 'queued'}) for p in self.projects]


def run(state, once=False, logger=None):
    import msvcrt
    state = Path(state).resolve()
    config, port, token = configuration(state)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    def dispatch(project):
        local = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        try:
            result = tick(local, port, token, project)
            if logger: logger.event('runner.dispatch.completed', project_id=project)
            return result
        except Exception:
            if logger: logger.event('runner.dispatch.failed', project_id=project)
            raise
    dispatcher = ProjectDispatcher(config['projects'], dispatch)
    # OS-owned lock is released on process death; no stale PID-based ownership guesses.
    with (state/'runner.lock').open('a+b') as lock:
        lock.seek(0, 2)
        if lock.tell() == 0: lock.write(b'0'); lock.flush()
        lock.seek(0); msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        if logger: logger.event('runner.started')
        try:
            while not (state/'runner.stop').exists():
                discovered = approved_projects(opener, port, token)
                if discovered is not None: dispatcher.update_projects(discovered)
                if once:
                    outcomes = []
                    for project in dispatcher.projects:
                        if (state/'runner.stop').exists(): break
                        outcomes.append(outcome(dispatch, project))
                else:
                    outcomes = dispatcher.poll()
                if write_status(state, {'state': 'running', 'pid': os.getpid(), 'at': time.time(), 'projects': outcomes}) is False:
                    if logger: logger.event('runner.status.failed')
                if once: break
                until = time.monotonic()+config['interval_seconds']
                while time.monotonic() < until and not (state/'runner.stop').exists(): time.sleep(.25)
        finally:
            if logger: logger.event('runner.stopped')
            if write_status(state, {'state': 'stopped', 'pid': os.getpid(), 'at': time.time()}) is False:
                if logger: logger.event('runner.status.failed')
            lock.seek(0); msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', required=True, type=Path)
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--no-logging', action='store_true')
    args = parser.parse_args()
    logging = LogHub(args.state/'logs', service='jarvis-runner', enabled=not args.no_logging)
    try:
        run(args.state, args.once, logger=logging)
    except Exception:
        logging.event('application.startup.failed')
        # No tokens, selected source, model data or raw exception details in logs.
        sys.stderr.write('Runner startup failed; check private configuration, lock and Core readiness.\n')
        raise SystemExit(1)
    finally:
        logging.close()
