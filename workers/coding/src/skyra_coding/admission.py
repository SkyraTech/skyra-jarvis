"""Review existing host-approved sources without granting execution authority."""
import json
from pathlib import Path

from .scaffold import _parent, checksum, destination
from .workspace import BoundaryError, Workspace, checked, digest, read_bytes, relative


class ProjectAdmission:
    """Host supplies logical roots; callers select files, never filesystem roots.

    This creates selected snapshots only. Registration, protected acceptance
    commands, grants, model calls and source delivery remain separate decisions.
    """

    def __init__(self, sources, snapshot_root):
        if type(sources) is not dict or not sources or len(sources) > 100:
            raise BoundaryError('Provide 1..100 host-approved sources')
        self.root = _parent(snapshot_root)
        self.sources = {}
        for name, directory in sources.items():
            destination(self.root, name)  # Same bounded logical slug contract.
            source = _parent(directory)
            if source == self.root or self.root.is_relative_to(source) or source.is_relative_to(self.root):
                raise BoundaryError('Source and admission state must be separate')
            if source in self.sources.values():
                raise BoundaryError('Source cannot have multiple logical identities')
            self.sources[name] = source

    def preview(self, source, name, files, create_paths=()):
        if type(source) is not str or source not in self.sources:
            raise BoundaryError('Source is not host-approved')
        destination(self.root, name)
        if type(files) is not list or type(create_paths) not in (list, tuple):
            raise BoundaryError('Explicit existing and absent file lists required')
        selected = [*files, *create_paths]
        if (not 1 <= len(selected) <= 100 or not all(type(p) is str for p in selected)
                or len({p.casefold() for p in selected}) != len(selected)):
            raise BoundaryError('Select 1..100 unique paths')
        for path in selected:
            relative(path)
            if any(other.casefold().startswith(path.casefold() + '/') for other in selected):
                raise BoundaryError('Selected paths conflict')
        # Recheck host root ancestry on every review, including replacements.
        root = _parent(self.sources[source])
        contents = {path: read_bytes(root, path) for path in files}
        if sum(map(len, contents.values())) > 10_485_760:
            raise BoundaryError('Selected source exceeds total size limit')
        for path in create_paths:
            target = checked(root, path)
            if target.exists() or target.is_symlink():
                raise BoundaryError('Creation target already exists')
        plan = {'version': 1, 'operation': 'admit-selected-project', 'source': source,
                'name': name, 'source_directory': str(root), 'files': list(files),
                'create_paths': list(create_paths),
                'input_hashes': {**{p: digest(data) for p, data in contents.items()},
                                 **{p: 'absent' for p in create_paths}},
                'source_repository_complete': False}
        return {'plan': plan, 'sha256': checksum(plan),
                'files': [{'path': p, 'sha256': plan['input_hashes'][p],
                           'content': contents[p].decode('utf-8-sig') if p in contents else '',
                           'exists': p in contents} for p in selected],
                'execution_enabled': False}

    def materialize(self, source, name, files, create_paths=(), *, expected_sha256):
        review = self.preview(source, name, files, create_paths)
        if review['sha256'] != expected_sha256:
            raise BoundaryError('Review the current source selection before admission')
        target = destination(self.root, name)
        if target.exists():
            return self.receipt(name, expected_sha256)
        # Reserve exclusively; a partial failure remains inspectable and is never
        # silently deleted or reused as a completed admission.
        target.mkdir(exist_ok=False)
        workspace = Workspace.snapshot(self.sources[source], target / 'snapshot', files, create_paths)
        if workspace.original_hashes != review['plan']['input_hashes']:
            raise BoundaryError('Source changed during admission; reconciliation required')
        # No source write has occurred. Reject late changes, including absent paths.
        if self.preview(source, name, files, create_paths)['sha256'] != expected_sha256:
            raise BoundaryError('Source changed during admission; reconciliation required')
        with (target / 'admission.json').open('x', encoding='utf-8') as stream:
            json.dump({'plan': review['plan'], 'sha256': expected_sha256}, stream, sort_keys=True)
        return self.receipt(name, expected_sha256)

    def binding(self, name, expected_sha256):
        """Restore immutable admission identity, allowing later reviewed edits.

        Source freshness is checked by delivery; it must not be silently rebased
        here after the owner or a completed delivery changes the source tree.
        """
        target = destination(self.root, name)
        record = json.loads(read_bytes(target, 'admission.json'))
        if (set(record) != {'plan', 'sha256'} or record['sha256'] != expected_sha256
                or checksum(record['plan']) != expected_sha256 or record['plan']['name'] != name):
            raise BoundaryError('Admission receipt differs from reviewed intent')
        plan = record['plan']
        if (plan['source'] not in self.sources
                or str(_parent(self.sources[plan['source']])) != plan['source_directory']):
            raise BoundaryError('Host source binding changed')
        workspace = Workspace(target / 'snapshot')
        if (workspace.original_hashes != plan['input_hashes']
                or list(workspace.selected) != [*plan['files'], *plan['create_paths']]
                or list(workspace.create_paths) != plan['create_paths']):
            raise BoundaryError('Admission state changed; reconciliation required')
        workspace.diff()  # Validate original baseline bytes even after edits.
        return plan, workspace

    def receipt(self, name, expected_sha256):
        plan, workspace = self.binding(name, expected_sha256)
        current = self.preview(plan['source'], name, plan['files'], plan['create_paths'])
        if current['sha256'] != expected_sha256 or workspace.diff()['changes']:
            raise BoundaryError('Admission state changed; reconciliation required')
        return {'admitted': True, 'sha256': expected_sha256,
                'snapshot': str(workspace.directory), 'execution_enabled': False,
                'source_repository_complete': False}
