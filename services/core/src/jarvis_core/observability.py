"""Internal LogHub pilot. Operational events never replace canonical activity/history."""
import os
from pathlib import Path
import queue
import re
import threading
import uuid


EVENTS = frozenset({
    'application.started', 'application.startup.failed', 'application.shutdown',
    'http.request.completed', 'http.request.failed',
    'runner.started', 'runner.stopped', 'runner.dispatch.completed', 'runner.dispatch.failed',
    'runner.status.failed',
})


class LogHub:
    """One process-owned root with bounded, best-effort off-thread delivery."""
    def __init__(self, directory, *, service='jarvis-core', environment='local', enabled=True):
        if service not in {'jarvis-core', 'jarvis-runner'}:
            raise ValueError('Unsupported logging service')
        if environment not in {'local', 'development', 'test', 'staging', 'production'}:
            raise ValueError('Unsupported logging environment')
        self.directory = Path(directory)
        self.service, self.environment = service, environment
        self.instance = f'process-{os.getpid()}-{uuid.uuid4()}'
        self._queue = queue.Queue(maxsize=512)
        self._lock = threading.Lock()
        self._closed = False
        self._counts = {'errors': 0, 'dropped': 0, 'shutdown_timeouts': 0}
        self._thread = None
        if enabled:
            self._thread = threading.Thread(target=self._work, daemon=True, name='jarvis-loghub')
            try:
                self._thread.start()
            except RuntimeError:
                self._thread = None
                self._count('errors')

    def _count(self, key, amount=1):
        with self._lock:
            self._counts[key] += amount

    def diagnostics(self):
        with self._lock:
            return dict(self._counts)

    def event(self, action, **fields):
        if action not in EVENTS or self._closed or self._thread is None:
            return
        safe = {}
        for key, value in fields.items():
            if key in {'project_id', 'core_request_id'} and isinstance(value, str) and re.fullmatch(r'[a-f0-9-]{32,36}', value):
                safe[key] = value
            elif key == 'method' and isinstance(value, str) and value in {'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'}:
                safe[key] = value
            elif key == 'status_code' and type(value) is int and 100 <= value <= 599:
                safe[key] = value
            elif key == 'route' and isinstance(value, str) and re.fullmatch(r'/v1/(?:[a-z-]+|\{[a-z_]+\})(?:/(?:[a-z-]+|\{[a-z_]+\}))*', value):
                safe[key] = value
        try:
            self._queue.put_nowait(('event', action, safe))
        except queue.Full:
            self._count('dropped')

    def _work(self):
        sdk = None
        try:
            from skyra_logger import create_skyra_logger
            sdk = create_skyra_logger(
                project_id='skyra-jarvis', service_name=self.service,
                environment=self.environment, instance_id=self.instance,
                transport={'type': 'file', 'directory': str(self.directory)},
                on_error=lambda _error: self._count('errors'),
                on_drop=lambda count, _reason: self._count('dropped', count),
            )
        except Exception:
            self._count('errors')
        while True:
            kind, value, fields = self._queue.get()
            try:
                if kind == 'event' and sdk is not None:
                    failed = value.endswith('failed')
                    sdk.log('error' if failed else 'info', value,
                            {'action': value, 'outcome': 'failure' if failed else 'success',
                             'component': self.service, **fields})
                elif kind == 'event':
                    self._count('dropped')
                elif kind in {'flush', 'close'}:
                    if sdk is not None:
                        getattr(sdk, kind)(timeout=1.0)
            except Exception:
                self._count('errors')
            finally:
                self._queue.task_done()
                if kind in {'flush', 'close'}:
                    value.set()
            if kind == 'close':
                return

    def _control(self, kind):
        if self._thread is None:
            return
        done = threading.Event()
        try:
            self._queue.put((kind, done, {}), timeout=0.1)
        except queue.Full:
            self._count('shutdown_timeouts')
            return
        if not done.wait(2.0):
            self._count('shutdown_timeouts')

    def flush(self):
        if not self._closed:
            self._control('flush')

    def close(self):
        if not self._closed:
            self._closed = True
            self._control('close')


class LoggedApplication:
    """ASGI observer; credentials, URLs, headers and bodies are never inspected."""
    def __init__(self, app, logger):
        self.app, self.logger = app, logger

    async def __call__(self, scope, receive, send):
        status = None

        async def observed_send(message):
            nonlocal status
            await send(message)
            if message['type'] == 'http.response.start':
                status = message['status']
            elif message['type'] == 'lifespan.startup.complete':
                self.logger.event('application.started')
            elif message['type'] == 'lifespan.startup.failed':
                self.logger.event('application.startup.failed')
            elif message['type'] == 'lifespan.shutdown.complete':
                self.logger.event('application.shutdown')
        try:
            await self.app(scope, receive, observed_send)
        finally:
            if scope['type'] == 'http' and status is not None:
                method = scope.get('method')
                if status >= 400 or method in {'POST', 'PUT', 'PATCH', 'DELETE'}:
                    self.logger.event('http.request.failed' if status >= 400 else 'http.request.completed',
                                      method=method, status_code=status,
                                      core_request_id=scope.get('state', {}).get('request_id', ''),
                                      route=getattr(scope.get('route'), 'path', ''))
