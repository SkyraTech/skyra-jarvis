"""Durable owner-reviewed scaffold registrations; additions never rebind resources."""
from dataclasses import asdict
import json
from pathlib import Path
import threading

from jarvis_core import Conflict, Denied
from jarvis_core.store import identifier
from .native import NativeExecutor, NativeProfile
from .scaffold import checksum, destination, receipt, _parent
from .workspace import BoundaryError, Workspace, digest, read_bytes


class ScaffoldRegistry:
    def __init__(self, worker, root, enabled=False):
        self.worker = worker
        self.root = _parent(root)
        self.enabled = enabled is True
        if worker.sandbox is not None and not isinstance(worker.sandbox, NativeExecutor):
            self.enabled = False
        self.lock = threading.RLock()
        self.loaded = set()
        self.errors = {}

    def preview(self, core, actor, spec, name, expected_plan_sha256):
        result = receipt(core, actor, spec, self.root, name)
        if not result.get('exists') or not result['audit_recorded'] or result['plan_sha256'] != expected_plan_sha256:
            raise Conflict('Reviewed creation receipt and audit required')
        target = destination(self.root, name)
        manifest = json.loads(read_bytes(target, 'scaffold.json'))
        plan = manifest['plan']
        workspace = Workspace(target / 'snapshot')
        if workspace.diff()['changes'] or set(workspace.selected) != set(plan['selected']):
            raise Conflict('Only an untouched reviewed scaffold can be registered')
        for path, content in plan['files'].items():
            if digest(read_bytes(target / 'source', path)) != digest(content.encode()):
                raise Conflict('Scaffold source changed before registration')
        for path in workspace.selected:
            if workspace.read(path)['sha256'] != digest(plan['files'][path].encode()):
                raise Conflict('Scaffold snapshot differs from reviewed files')
        profile = {**plan['profile'], 'name': 'scaffold-' + expected_plan_sha256[:16]}
        executable = Path(profile['argv'][0])
        if digest(executable.read_bytes()) != plan['python_sha256']:
            raise Conflict('Reviewed interpreter changed')
        config = {'project': plan['project'], 'specification': spec, 'name': name,
                  'directory': str(target), 'plan_sha256': expected_plan_sha256,
                  'workspace': 'workspace:' + name, 'source': 'source:' + name,
                  'selected': list(workspace.selected), 'profile': profile,
                  'manifest_sha256': digest(read_bytes(target / 'snapshot', 'manifest.json')),
                  'python_sha256': plan['python_sha256']}
        self._candidate(config)
        return {'registration': config, 'registration_sha256': checksum(config), 'enabled': self.enabled}

    def register(self, core, actor, spec, name, expected_plan_sha256, expected_registration_sha256, allow_native_execution):
        if not self.enabled or allow_native_execution is not True:
            raise Denied('Explicit host and owner native execution consent required')
        with core.transaction():
            from jarvis_core.specifications import get
            specification = get(core, actor, spec)
            # A repeat of the identical saved intent is a read, even after code changes.
            prior = core.db.execute('SELECT * FROM scaffold_registrations WHERE project=? AND name=?',
                                    (specification['project'], name)).fetchone()
            if prior:
                if (prior['specification'] != spec or prior['plan_sha256'] != expected_plan_sha256
                        or prior['config_sha256'] != expected_registration_sha256):
                    raise Conflict('Registration already exists with different intent')
                return self.get(core, actor, spec, name)
            if specification['state'] != 'approved':
                raise Conflict('Current approved specification required for new registration')
            if core.db.execute('SELECT COUNT(*) FROM scaffold_registrations').fetchone()[0] >= 500:
                raise Conflict('Registration capacity reached')
            review = self.preview(core, actor, spec, name, expected_plan_sha256)
            config = review['registration']
            if review['registration_sha256'] != expected_registration_sha256:
                raise Conflict('Review the exact registration')
            core.db.execute('INSERT INTO scaffold_registrations VALUES(?,?,?,?,?,?,?,?,?)',
                            (identifier(), config['project'], spec, name, config['directory'], expected_plan_sha256,
                             expected_registration_sha256, json.dumps(config, sort_keys=True), core.clock()))
            core._event(config['project'], 'scaffold.registered', name)
        self.sync(core)
        return self.get(core, actor, spec, name)

    def get(self, core, actor, spec, name):
        from jarvis_core.specifications import get
        data = get(core, actor, spec)
        row = core.db.execute('SELECT * FROM scaffold_registrations WHERE project=? AND specification=? AND name=?',
                              (data['project'], spec, name)).fetchone()
        if row is None:
            return {'registered': False, 'enabled': self.enabled}
        return {'registered': True, 'active': row['id'] in self.loaded, 'enabled': self.enabled,
                'reconciliation_required': row['id'] in self.errors, 'registration': json.loads(row['config']),
                'registration_sha256': row['config_sha256']}

    def _candidate(self, config):
        target = destination(self.root, config['name'])
        if str(target) != config['directory']:
            raise Conflict('Registration root changed')
        _parent(target); _parent(target / 'snapshot'); _parent(target / 'source')
        if digest(read_bytes(target / 'snapshot', 'manifest.json')) != config['manifest_sha256']:
            raise Conflict('Registered snapshot manifest changed')
        workspace = Workspace(target / 'snapshot')
        workspace.diff()  # Validate immutable baseline bytes and path boundaries.
        profile = NativeProfile(config['profile']['name'], tuple(config['profile']['argv']),
                                tuple(config['profile']['protected_paths']), config['profile']['timeout'])
        if digest(Path(profile.argv[0]).read_bytes()) != config['python_sha256']:
            raise Conflict('Registered interpreter changed')
        for path in profile.protected_paths:
            if workspace.read(path)['sha256'] != workspace.original_hashes.get(path):
                raise Conflict('Registered protected tests changed')
        key = (config['project'], config['workspace'])
        source_key = (config['project'], config['source'])
        if key in self.worker.workspaces or source_key in self.worker.delivery.targets:
            raise Conflict('Logical resource already registered')
        if any(workspace.directory == old.directory for old in self.worker.workspaces.values()):
            raise Conflict('Snapshot cannot be shared across registrations')
        profiles = dict(self.worker.sandbox.profiles) if self.worker.sandbox else {}
        if profile.name in profiles and asdict(profiles[profile.name]) != asdict(profile):
            raise Conflict('Profile name collision')
        # Validate delivery using a temporary candidate, without publishing mutations.
        from .worker import FileWorker
        targets = [{'project_id': p, 'resource_id': resource, 'workspace_resource': value[0], 'directory': str(value[1])}
                   for (p, resource), value in self.worker.delivery.targets.items()]
        targets.append({'project_id': config['project'], 'resource_id': config['source'],
                        'workspace_resource': config['workspace'], 'directory': str(target / 'source')})
        candidate = FileWorker({**self.worker.workspaces, key: workspace}, self.worker.evidence_root,
                               self.worker.sandbox, targets)
        return workspace, profile, candidate.delivery.targets

    def sync(self, core):
        # Short publication lock only; never hold it while models/tests execute.
        with self.lock:
            for row in core.db.execute('SELECT id,config,config_sha256 FROM scaffold_registrations ORDER BY rowid'):
                if row['id'] in self.loaded or row['id'] in self.errors:
                    continue
                try:
                    config = json.loads(row['config'])
                    if checksum(config) != row['config_sha256']:
                        raise Conflict('Registration integrity check failed')
                    workspace, profile, targets = self._candidate(config)
                except (ValueError, OSError, KeyError, TypeError):
                    self.errors[row['id']] = 'Registered files/configuration require reconciliation and Core restart'
                    continue
                profiles = dict(self.worker.sandbox.profiles) if self.worker.sandbox else {}
                profiles[profile.name] = profile
                if self.enabled:
                    if self.worker.sandbox is None:
                        self.worker.sandbox = NativeExecutor(list(profiles.values()), owner_enabled=True)
                    else:
                        self.worker.sandbox.profiles = profiles
                self.worker.delivery.targets = targets
                self.worker.profile_bindings = {**self.worker.profile_bindings,
                                                (config['project'], config['workspace']): profile.name}
                self.worker.interpreter_bindings = {**self.worker.interpreter_bindings,
                                                    (config['project'], config['workspace']): config['python_sha256']}
                # Publish the new workspace last; existing keys are never rebound.
                self.worker.workspaces = {**self.worker.workspaces, (config['project'], config['workspace']): workspace}
                self.loaded.add(row['id'])
