"""Durable registration for admitted existing projects with host-fixed tests."""
from dataclasses import asdict

from jarvis_core import Conflict
from .native import NativeProfile
from .registry import ScaffoldRegistry
from .scaffold import checksum, destination
from .toolchains import executable_digest, runtime_fields, primary_digest
from .workspace import digest, read_bytes


def load_host_config(path, snapshot_root):
    """Read bounded private configuration; inspect hashes without project execution."""
    import json
    from pathlib import Path
    from .admission import ProjectAdmission
    from .scaffold import _parent
    path = Path(path)
    if not path.is_absolute():
        raise ValueError('Absolute host configuration path required')
    raw = read_bytes(_parent(path.parent), path.name)
    if len(raw) > 32768:
        raise ValueError('Existing project configuration exceeds 32KB')
    config = json.loads(raw)
    if type(config) is not dict or set(config) != {'sources'} or type(config['sources']) is not dict:
        raise ValueError('Existing project sources required')
    sources, profiles, runtimes = {}, {}, {}
    for source, value in config['sources'].items():
        if (type(value) is not dict or 'directory' not in value
                or set(value) - {'directory', 'profile', 'runtime_binding'}):
            raise ValueError('Invalid existing project source configuration')
        sources[source] = value['directory']
        if 'profile' in value:
            profile = value['profile']
            if (type(profile) is not dict or set(profile) != {'name', 'argv', 'protected_paths', 'timeout'}
                    or type(profile['name']) is not str or not 1 <= len(profile['name']) <= 128
                    or type(profile['argv']) is not list or type(profile['protected_paths']) is not list
                    or not all(type(p) is str for p in profile['protected_paths'])
                    or len(set(profile['protected_paths'])) != len(profile['protected_paths'])):
                raise ValueError('Exact host test profile required')
            profiles[source] = NativeProfile(profile['name'], tuple(profile['argv']),
                                             tuple(profile['protected_paths']), profile['timeout'])
            for protected in profile['protected_paths']:
                from .workspace import relative
                relative(protected)
        if 'runtime_binding' in value:
            if source not in profiles:
                raise ValueError('Runtime identity requires a host test profile')
            runtimes[source] = value['runtime_binding']
    admission = ProjectAdmission(sources, snapshot_root)
    # Validate all runtime identities before publishing any optional configuration.
    for source, value in runtimes.items():
        if type(value) is not dict or set(value) != {'runtime', 'executable_sha256'}:
            raise ValueError('Exact host runtime identity required')
        candidate = {**value, 'profile': json.loads(json.dumps(asdict(profiles[source])))}
        if primary_digest(candidate) != executable_digest(profiles[source].argv[0]):
            raise ValueError('Reviewed host executable identity changed')
    return admission.sources, profiles, runtimes


class ExistingProjectRegistry(ScaffoldRegistry):
    """Reuse registration storage, grants and delivery without source rebinding.

    Profiles and optional Node identities come from host configuration, never
    from a model or request body.
    """

    def __init__(self, worker, admission, profiles, enabled=False, runtime_bindings=None):
        super().__init__(worker, admission.root, enabled)
        if (type(profiles) is not dict or not set(profiles) <= set(admission.sources)
                or not all(isinstance(profile, NativeProfile) for profile in profiles.values())):
            raise ValueError('Host-fixed admitted-source test profiles required')
        self.admission = admission
        self.profiles = dict(profiles)
        self.runtime_bindings = dict(runtime_bindings or {})
        if not set(self.runtime_bindings) <= set(profiles):
            raise ValueError('Runtime bindings require a matching host profile')
        for source in self.runtime_bindings:
            self._runtime(source, profiles[source])

    def _runtime(self, source, profile):
        import json
        value = self.runtime_bindings.get(source)
        if value is None:
            return {'runtime': {'kind': 'fixed-executable-v1'},
                    'executable_sha256': executable_digest(profile.argv[0])}
        if type(value) is not dict or set(value) != {'runtime', 'executable_sha256'}:
            raise ValueError('Exact host runtime identity required')
        candidate = {**value, 'profile': json.loads(json.dumps(asdict(profile)))}
        return runtime_fields(candidate)

    def register_existing(self, core, actor, spec, name, expected_plan_sha256,
                          expected_registration_sha256, allow_native_execution):
        return self._register(core, actor, spec, name, expected_plan_sha256,
            expected_registration_sha256, allow_native_execution, self.preview_existing)

    def preview_existing(self, core, actor, spec, name, expected_plan_sha256):
        from jarvis_core.specifications import get
        specification = get(core, actor, spec)
        if specification['state'] != 'approved':
            raise Conflict('Approved specification required for existing project registration')
        self.admission.receipt(name, expected_plan_sha256)
        plan, workspace = self.admission.binding(name, expected_plan_sha256)
        profile = self.profiles.get(plan['source'])
        if profile is None or not set(profile.protected_paths) <= set(plan['files']):
            raise Conflict('Existing protected tests and a host-fixed profile are required')
        config = {'kind': 'existing-project', 'project': specification['project'],
                  'specification': spec, 'name': name,
                  'directory': str(destination(self.root, name)),
                  'plan_sha256': expected_plan_sha256,
                  'workspace': 'workspace:' + name, 'source': 'source:' + name,
                  'source_directory': plan['source_directory'], 'host_source': plan['source'],
                  'selected': list(workspace.selected), 'profile': asdict(profile),
                  'manifest_sha256': digest(read_bytes(workspace.directory, 'manifest.json')),
                  **self._runtime(plan['source'], profile)}
        # Canonical JSON detaches tuples and matches durable registration shape.
        import json
        config = json.loads(json.dumps(config))
        self._candidate(config)
        return {'registration': config, 'registration_sha256': checksum(config), 'enabled': self.enabled}

    def _source(self, config, target):
        if config.get('kind') != 'existing-project':
            return super()._source(config, target)
        plan, workspace = self.admission.binding(config['name'], config['plan_sha256'])
        profile = self.profiles.get(plan['source'])
        if (profile is None or checksum(asdict(profile)) != checksum(config['profile'])
                or config['host_source'] != plan['source']
                or config['source_directory'] != plan['source_directory']
                or config['selected'] != list(workspace.selected)
                or checksum(self._runtime(plan['source'], profile)) != checksum(runtime_fields(config))):
            raise Conflict('Reviewed host source or test profile changed')
        return self.admission.sources[plan['source']]
