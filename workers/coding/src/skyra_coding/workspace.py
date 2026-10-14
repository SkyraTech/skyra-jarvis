"""Selected-file snapshots. This is a data boundary, not a process sandbox."""

import ast
import difflib
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import tempfile


class BoundaryError(ValueError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def relative(name):
    if not isinstance(name, str) or not name or '\\' in name or ':' in name:
        raise BoundaryError('Invalid workspace-relative path')
    parts = name.split('/')
    if any(p in {'', '.', '..'} or p.endswith((' ', '.')) or any(ord(c) < 32 for c in p) for p in parts):
        raise BoundaryError('Invalid path segment')
    forbidden = {'.git', '.runtime', 'node_modules', 'venv', '.venv', 'credentials.json',
                 'token.json', 'memory.json', 'api_keys.json', 'core.sqlite3'}
    reserved = {'CON', 'PRN', 'AUX', 'NUL', *('COM'+str(i) for i in range(1,10)), *('LPT'+str(i) for i in range(1,10))}
    for p in parts:
        if p.lower() in forbidden or p.lower().startswith('.env') or p.upper().split('.')[0] in reserved:
            raise BoundaryError('Protected path')
        if Path(p).suffix.lower() in {'.pem', '.key', '.sqlite', '.sqlite3'}:
            raise BoundaryError('Protected file type')
    return Path(*PurePosixPath(name).parts)


def checked(root, name):
    path = root / relative(name)
    if not path.resolve().is_relative_to(root.resolve()):
        raise BoundaryError('Path escaped workspace')
    for part in [root, *list(path.relative_to(root).parents)[::-1]]:
        candidate = part if part == root else root / part
        if candidate.exists():
            info = candidate.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
                raise BoundaryError('Links and reparse points are forbidden')
    if path.exists() or path.is_symlink():
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise BoundaryError('File must be regular and unlinked')
    return path


def read_bytes(root, name):
    path = checked(root, name)
    if not path.exists():
        raise BoundaryError('Selected file unavailable')
    if path.stat().st_size > 1_048_576:
        raise BoundaryError('File exceeds size limit')
    with path.open('rb') as stream:
        info = os.fstat(stream.fileno())
        if info.st_nlink != 1 or info.st_size > 1_048_576:
            raise BoundaryError('Invalid open file')
        data = stream.read(1_048_577)
    if len(data) > 1_048_576:
        raise BoundaryError('File exceeds size limit')
    data.decode('utf-8-sig')
    return data


class Workspace:
    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        self.root = self.directory / 'files'
        self.baseline = self.directory / 'baseline'
        manifest = json.loads((self.directory / 'manifest.json').read_text(encoding='utf-8'))
        if manifest.get('version') != 1:
            raise BoundaryError('Unsupported manifest')
        self.selected = tuple(manifest['files'])
        for name in self.selected:
            relative(name)
        self.original_hashes = manifest['hashes']

    @classmethod
    def snapshot(cls, source, destination, files):
        source, destination = Path(source).resolve(), Path(destination).absolute()
        if not source.is_dir() or not files or len(files) > 100 or len(set(files)) != len(files):
            raise BoundaryError('Select 1..100 unique files')
        if destination.resolve().is_relative_to(source):
            raise BoundaryError('Snapshot must be outside source')
        # Validate all source files before creating the destination.
        contents = {name: read_bytes(source, name) for name in files}
        if sum(map(len, contents.values())) > 10_485_760:
            raise BoundaryError('Snapshot exceeds total size limit')
        destination.mkdir(parents=False, exist_ok=False)
        hashes = {}
        for name, data in contents.items():
            for group in ('files', 'baseline'):
                path = destination / group / relative(name)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            hashes[name] = digest(data)
        (destination / 'manifest.json').write_text(json.dumps({'version':1,'files':list(files),'hashes':hashes}, sort_keys=True), encoding='utf-8')
        return cls(destination)

    def _selected(self, name):
        relative(name)
        if name not in self.selected:
            raise BoundaryError('File not selected for this run')

    def read(self, name):
        self._selected(name)
        data = read_bytes(self.root, name)
        return {'path':name, 'sha256':digest(data), 'content':data.decode('utf-8-sig')}

    def patch(self, name, expected_sha256, old, new):
        self._selected(name)
        if not isinstance(old,str) or not old or not isinstance(new,str):
            raise BoundaryError('Exact nonempty old text and replacement required')
        data = read_bytes(self.root, name)
        if digest(data) != expected_sha256:
            raise BoundaryError('Stale file; reread before editing')
        text = data.decode('utf-8-sig')
        if text.count(old) != 1:
            raise BoundaryError('Patch anchor must occur exactly once')
        replacement = text.replace(old,new,1).encode('utf-8')
        if data.startswith(b'\xef\xbb\xbf'):
            replacement = b'\xef\xbb\xbf'+replacement
        if len(replacement) > 1_048_576:
            raise BoundaryError('Replacement exceeds size limit')
        target = checked(self.root,name)
        fd, temporary = tempfile.mkstemp(prefix='.jarvis-edit-',dir=target.parent)
        try:
            with os.fdopen(fd,'wb') as stream:
                stream.write(replacement)
                stream.flush()
                os.fsync(stream.fileno())
            if digest(read_bytes(self.root,name)) != expected_sha256:
                raise BoundaryError('File changed during edit')
            os.replace(temporary,target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return {'path':name,'before_sha256':expected_sha256,'sha256':digest(replacement)}

    def diff(self):
        result = []
        for name in self.selected:
            original = read_bytes(self.baseline,name)
            if digest(original) != self.original_hashes[name]:
                raise BoundaryError('Baseline evidence changed')
            current = read_bytes(self.root,name)
            if original != current:
                result.append({'path':name,'before_sha256':digest(original),'sha256':digest(current),
                               'patch':''.join(difflib.unified_diff(original.decode('utf-8-sig').splitlines(keepends=True),
                                                                 current.decode('utf-8-sig').splitlines(keepends=True),
                                                                 fromfile='a/'+name,tofile='b/'+name))})
        return {'changes':result}

    def verify(self):
        results = []
        for name in self.selected:
            content = self.read(name)['content']
            suffix = Path(name).suffix.lower()
            if suffix not in {'.py','.json'}:
                results.append({'path':name,'status':'unsupported'})
                continue
            try:
                ast.parse(content,filename=name) if suffix == '.py' else json.loads(content)
                results.append({'path':name,'status':'passed'})
            except (SyntaxError,ValueError,RecursionError):
                results.append({'path':name,'status':'failed'})
        # Unsupported files never count as verified success.
        return {'kind':'static_syntax','passed':all(r['status']=='passed' for r in results),'files':results}

    def search(self, query):
        if not isinstance(query,str) or not query or len(query)>256:
            raise BoundaryError('Search requires 1..256 characters')
        hits=[]
        for name in self.selected:
            for number,line in enumerate(self.read(name)['content'].splitlines(),1):
                if query in line:
                    hits.append({'path':name,'line':number,'text':line[:256]})
                    if len(hits)==100:
                        return {'hits':hits,'truncated':True}
        return {'hits':hits,'truncated':False}
