"""Durable owner-reviewed scaffold registrations; additions never rebind resources."""
from dataclasses import asdict
import json
import os
from pathlib import Path
import threading

from jarvis_core import Conflict, Denied
from jarvis_core.store import identifier
from .native import NativeExecutor, NativeProfile
from .scaffold import checksum, destination, receipt, _parent
from .workspace import BoundaryError, Workspace, digest, read_bytes
from .toolchains import runtime_fields,primary_digest,secondary_bindings


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
        if digest(executable.read_bytes()) != primary_digest(plan):
            raise Conflict('Reviewed interpreter changed')
        config = {'project': plan['project'], 'specification': spec, 'name': name,
                  'directory': str(target), 'plan_sha256': expected_plan_sha256,
                  'workspace': 'workspace:' + name, 'source': 'source:' + name,
                  'selected': list(workspace.selected), 'profile': profile,
                  'manifest_sha256': digest(read_bytes(target / 'snapshot', 'manifest.json')),
                  **runtime_fields(plan)}
        self._candidate(config)
        return {'registration': config, 'registration_sha256': checksum(config), 'enabled': self.enabled}

    def register(self, core, actor, spec, name, expected_plan_sha256, expected_registration_sha256, allow_native_execution):
        return self._register(core, actor, spec, name, expected_plan_sha256,
                              expected_registration_sha256, allow_native_execution, self.preview)

    def _register(self, core, actor, spec, name, expected_plan_sha256, expected_registration_sha256,
                  allow_native_execution, preview):
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
            review = preview(core, actor, spec, name, expected_plan_sha256)
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

    def continuation_status(self, core, actor, task, name):
        delivery = core.task(actor, task)
        destination(self.root, name)
        row = core.db.execute('SELECT * FROM scaffold_registrations WHERE project=? AND name=?',
                              (delivery['project'], name)).fetchone()
        if row is None:
            return {'registered': False, 'enabled': self.enabled}
        config = json.loads(row['config'])
        if config.get('delivery_task') != task:
            raise Conflict('Generation name already belongs to different work')
        return self.get(core, actor, row['specification'], name)

    def continuation_preview(self, core, actor, task, name):
        intent = core.task(actor, task)
        plan = json.loads(intent['payload'])
        if (intent['state'] != 'succeeded' or intent['action'] != 'write'
                or plan.get('operation') != 'deliver' or plan.get('target') != intent['resource']
                or not core.db.execute("SELECT 1 FROM events WHERE project=? AND kind='delivery.prepared' AND subject=?",
                                       (intent['project'], task)).fetchone()):
            raise Conflict('A successful reviewed source delivery is required')
        workspace, (_, source) = self.worker.delivery.binding(core, actor, intent['project'], intent['resource'])
        # Revalidate tested inputs and profile, without expecting the old source baseline.
        current = self.worker.delivery.preview(core, actor, plan['run'], intent['resource'], source_check=False)
        references = json.loads(intent['evidence'] or '[]')
        evidence = self.worker.evidence(references[0]) if len(references) == 1 else {}
        report = evidence.get('result', {})
        if (current['plan'] != plan or evidence.get('task_id') != task or evidence.get('operation') != 'deliver'
                or report.get('passed') is not True or report.get('state') != 'delivered'
                or report.get('manifest_sha256') != current['sha256']
                or report.get('written') != [change['path'] for change in plan['changes']]):
            raise Conflict('Successful delivery evidence and unchanged tested snapshot required')
        parent = None
        for row in core.db.execute('SELECT config FROM scaffold_registrations WHERE project=? ORDER BY rowid',
                                   (intent['project'],)):
            candidate = json.loads(row['config'])
            if candidate['workspace'] == plan['workspace']:
                parent = candidate; break
        if parent is None:
            raise Denied('Continuation requires a durably registered project')
        from jarvis_core.specifications import get
        if get(core, actor, parent['specification'])['state'] != 'approved':
            raise Conflict('An approved specification is required')
        target = destination(self.root, name)
        if name == parent['name']:
            raise Conflict('Choose a distinct generation name')
        if ((intent['project'], 'workspace:' + name) in self.worker.workspaces
                or (intent['project'], 'source:' + name) in self.worker.delivery.targets):
            raise Conflict('Generation resources already exist')
        lineage = workspace.continuation_review(source)
        selected = [p for p in workspace.selected if lineage['review']['hashes'][p] != 'absent']
        absent = [p for p in workspace.selected if lineage['review']['hashes'][p] == 'absent']
        manifest = {'version': 2 if absent else 1, 'files': selected + absent,
                    'hashes': lineage['review']['hashes'], 'create_paths': absent}
        config = {**parent, 'kind': 'continuation', 'name': name, 'directory': str(target),
                  'workspace': 'workspace:' + name, 'source': 'source:' + name,
                  'selected': selected + absent, 'delivery_task': task,
                  'previous_workspace': parent['workspace'], 'previous_source': parent['source'],
                  'source_directory': str(source), 'lineage': lineage,
                  'manifest_sha256': digest(json.dumps(manifest, sort_keys=True).encode())}
        return {'registration': config, 'registration_sha256': checksum(config), 'enabled': self.enabled}

    def continue_project(self, core, actor, task, name, expected_registration_sha256, allow_native_execution):
        if not self.enabled or allow_native_execution is not True:
            raise Denied('Explicit host and owner native execution consent required')
        with self.lock:
            with core.transaction():
                prior = self.continuation_status(core, actor, task, name)
                if prior['registered']:
                    if prior['registration_sha256'] != expected_registration_sha256:
                        raise Conflict('Continuation request reused with different intent')
                    return prior
                if core.db.execute('SELECT COUNT(*) FROM scaffold_registrations').fetchone()[0] >= 500:
                    raise Conflict('Registration capacity reached')
                review = self.continuation_preview(core, actor, task, name)
                if review['registration_sha256'] != expected_registration_sha256:
                    raise Conflict('Review the exact continuation registration')
                config = review['registration']; target = Path(config['directory'])
                if target.exists():
                    # An uncertain previous write is adopted only with its complete exact receipt.
                    try:
                        saved = json.loads(read_bytes(target, 'registration.json'))
                    except (OSError, ValueError):
                        raise Conflict('Incomplete generation requires reconciliation') from None
                    if saved != review:
                        raise Conflict('Existing generation requires reconciliation')
                else:
                    target.mkdir()
                    previous = self.worker.workspaces[(config['project'], config['previous_workspace'])]
                    previous.continue_snapshot(config['source_directory'], target / 'snapshot', config['lineage']['sha256'])
                    (target / 'registration.json').write_text(json.dumps(review, sort_keys=True), encoding='utf-8')
                candidate, _, _ = self._candidate(config)
                previous = self.worker.workspaces[(config['project'], config['previous_workspace'])]
                if (candidate.diff()['changes'] or previous.continuation_review(config['source_directory']) != config['lineage']):
                    raise Conflict('Fresh generation or source changed before registration')
                core.db.execute('INSERT INTO scaffold_registrations VALUES(?,?,?,?,?,?,?,?,?)',
                                (identifier(), config['project'], config['specification'], name, str(target),
                                 config['plan_sha256'], expected_registration_sha256,
                                 json.dumps(config, sort_keys=True), core.clock()))
                core._event(config['project'], 'scaffold.continued', name)
            self.sync(core)
        return self.continuation_status(core, actor, task, name)

    def _source(self, config, target):
        return target / 'source'

    def _candidate(self, config):
        target = destination(self.root, config['name'])
        if str(target) != config['directory']:
            raise Conflict('Registration root changed')
        _parent(target); _parent(target / 'snapshot')
        source = self._source(config, target)
        if config.get('kind') == 'continuation':
            parent_key = (config['project'], config['previous_source'])
            previous = self.worker.delivery.targets.get(parent_key)
            if (previous is None or previous[0] != config['previous_workspace']
                    or str(previous[1]) != config['source_directory']):
                raise Conflict('Previous generation must be restored first')
            source = previous[1]
            lineage = json.loads(read_bytes(target / 'snapshot', 'continuation.json'))
            previous_workspace = self.worker.workspaces[(config['project'], config['previous_workspace'])]
            if (lineage != config['lineage'] or lineage['review']['previous_snapshot'] != os.path.normcase(str(previous_workspace.directory))
                    or lineage['review']['previous_manifest_sha256'] != digest(read_bytes(previous_workspace.directory, 'manifest.json'))
                    or lineage['review']['hashes'] != Workspace(target / 'snapshot').original_hashes):
                raise Conflict('Continuation lineage changed')
        _parent(source)
        if digest(read_bytes(target / 'snapshot', 'manifest.json')) != config['manifest_sha256']:
            raise Conflict('Registered snapshot manifest changed')
        workspace = Workspace(target / 'snapshot')
        workspace.diff()  # Validate immutable baseline bytes and path boundaries.
        profile = NativeProfile(config['profile']['name'], tuple(config['profile']['argv']),
                                tuple(config['profile']['protected_paths']), config['profile']['timeout'])
        if digest(Path(profile.argv[0]).read_bytes()) != primary_digest(config):
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
                        'workspace_resource': config['workspace'], 'directory': str(source)})
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
                                                    (config['project'], config['workspace']): primary_digest(config)}
                self.worker.toolchain_bindings = {**self.worker.toolchain_bindings,
                    (config['project'],config['workspace']):secondary_bindings(config)}
                # Publish the new workspace last; existing keys are never rebound.
                self.worker.workspaces = {**self.worker.workspaces, (config['project'], config['workspace']): workspace}
                self.loaded.add(row['id'])
