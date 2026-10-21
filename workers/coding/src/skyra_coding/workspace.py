"""Selected-file snapshots. This is a data boundary, not a process sandbox."""

import ast
import difflib
import hashlib
import json
import os
import re
from pathlib import Path, PurePosixPath
import stat
import tempfile


def canonical_edit(content, old, new):
    """Preserve a homogeneous source newline style; leave mixed files exact."""
    if '\n' not in content:
        return old, new
    if '\r' not in content:
        return old.replace('\r\n', '\n'), new.replace('\r\n', '\n')
    if content.count('\n') == content.count('\r\n') and '\r' not in content.replace('\r\n', ''):
        return (old.replace('\r\n', '\n').replace('\n', '\r\n'),
                new.replace('\r\n', '\n').replace('\n', '\r\n'))
    return old, new


class BoundaryError(ValueError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def relative(name):
    if not isinstance(name, str) or not name or any(c in name for c in '\\:<>"|?*'):
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
        if manifest.get('version') not in (1,2):
            raise BoundaryError('Unsupported manifest')
        self.selected = tuple(manifest['files'])
        for name in self.selected:
            relative(name)
        self.original_hashes = manifest['hashes']
        self.create_paths = tuple(manifest.get('create_paths', []))
        if (len(self.selected)>100 or len({name.casefold() for name in self.selected})!=len(self.selected)
                or not set(self.create_paths)<=set(self.selected)
                or set(self.original_hashes)!=set(self.selected)
                or any(self.original_hashes[name]!='absent' for name in self.create_paths)):
            raise BoundaryError('Invalid selected-file manifest')

    @classmethod
    def snapshot(cls, source, destination, files, create_paths=()):
        source, destination = Path(source).resolve(), Path(destination).absolute()
        selected = [*files, *create_paths]
        if not source.is_dir() or not selected or len(selected)>100 or len({name.casefold() for name in selected})!=len(selected):
            raise BoundaryError('Select 1..100 unique files')
        if destination.resolve().is_relative_to(source):
            raise BoundaryError('Snapshot must be outside source')
        for name in selected:
            relative(name)
            if any(other.casefold().startswith(name.casefold()+'/') for other in selected):
                raise BoundaryError('Selected paths conflict')
        for name in create_paths:
            target = checked(source,name)
            if target.exists() or target.is_symlink():
                raise BoundaryError('Creation target already exists')
        # Validate all source files before creating the destination.
        contents = {name: read_bytes(source, name) for name in files}
        if sum(map(len, contents.values())) > 10_485_760:
            raise BoundaryError('Snapshot exceeds total size limit')
        destination.mkdir(parents=False, exist_ok=False)
        hashes = {name: "absent" for name in create_paths}
        (destination/"files").mkdir()
        (destination/"baseline").mkdir()
        for name, data in contents.items():
            for group in ('files', 'baseline'):
                path = destination / group / relative(name)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            hashes[name] = digest(data)
        (destination / 'manifest.json').write_text(json.dumps({'version':2 if create_paths else 1,'files':selected,'hashes':hashes,'create_paths':list(create_paths)}, sort_keys=True), encoding='utf-8')
        return cls(destination)

    def _selected(self, name):
        relative(name)
        if name not in self.selected:
            raise BoundaryError('File not selected for this run')

    def read(self, name):
        self._selected(name)
        if name in self.create_paths and not checked(self.root,name).exists():
            return {'path':name, 'sha256':'absent', 'content':'', 'exists':False}
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

    def create(self, name, content):
        self._selected(name)
        if name not in self.create_paths or not isinstance(content,str) or not content or len(content.encode('utf-8'))>1_048_576:
            raise BoundaryError('Explicit creation target and nonempty bounded content required')
        target=checked(self.root,name)
        target.parent.mkdir(parents=True,exist_ok=True)
        target=checked(self.root,name)
        with target.open('xb') as stream:
            stream.write(content.encode('utf-8'));stream.flush();os.fsync(stream.fileno())
        return {'path':name,'before_sha256':'absent','sha256':digest(content.encode('utf-8'))}

    def execution_snapshot(self, destination):
        present=[name for name in self.selected if self.read(name)['sha256']!='absent']
        return Workspace.snapshot(self.root,destination,present)

    def continuation_review(self, source):
        """Review selected source bytes against this generation's delivered result.

        This does not grant registration, execution or delivery authority.
        """
        source = Path(source).resolve()
        if (not source.is_dir() or source.is_relative_to(self.directory)
                or self.directory.is_relative_to(source)):
            raise BoundaryError('Continuation source must be separate from snapshot')
        self.diff()  # Old baseline evidence must still be intact.
        hashes = {}
        for name in self.selected:
            expected = self.read(name)['sha256']
            path = checked(source, name)
            actual = digest(read_bytes(source, name)) if path.exists() else 'absent'
            if actual != expected:
                raise BoundaryError('Source differs from reviewed snapshot result')
            hashes[name] = actual
        review = {'version': 1, 'operation': 'snapshot_continuation',
                  'source': os.path.normcase(str(source)),
                  'previous_snapshot': os.path.normcase(str(self.directory)),
                  'previous_manifest_sha256': digest(read_bytes(self.directory, 'manifest.json')),
                  'files': list(self.selected), 'hashes': hashes}
        encoded = json.dumps(review, sort_keys=True, separators=(',', ':')).encode()
        return {'review': review, 'sha256': digest(encoded)}

    def continue_snapshot(self, source, destination, expected_review_sha256):
        """Create a new generation without rebasing historical evidence in place."""
        review = self.continuation_review(source)
        if review['sha256'] != expected_review_sha256:
            raise BoundaryError('Review the exact continuation inputs')
        destination = Path(destination).absolute()
        if (destination.resolve().is_relative_to(self.directory)
                or self.directory.is_relative_to(destination.resolve())):
            raise BoundaryError('Continuation destination must be separate from previous snapshot')
        present = [name for name in self.selected if review['review']['hashes'][name] != 'absent']
        absent = [name for name in self.selected if review['review']['hashes'][name] == 'absent']
        result = Workspace.snapshot(source, destination, present, absent)
        # A source edit between review and copy must never yield a usable generation.
        try:
            if (result.original_hashes != review['review']['hashes']
                    or self.continuation_review(source)['sha256'] != expected_review_sha256):
                raise BoundaryError('Source changed during continuation')
            (destination / 'continuation.json').write_text(
                json.dumps(review, sort_keys=True), encoding='utf-8')
        except (OSError, ValueError):
            # Retain bytes for diagnosis, but prevent loading a failed generation.
            (destination / 'manifest.json').unlink(missing_ok=True)
            raise
        return result

    def diff(self):
        result = []
        for name in self.selected:
            if name in self.create_paths:
                if checked(self.baseline,name).exists():
                    raise BoundaryError('Creation baseline changed')
                current=self.read(name)
                if current['sha256']!='absent':
                    result.append({'path':name,'before_sha256':'absent','sha256':current['sha256'],
                                   'patch':''.join(difflib.unified_diff([],current['content'].splitlines(keepends=True),fromfile='/dev/null',tofile='b/'+name))})
                continue
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
            record=self.read(name)
            if record['sha256']=='absent':
                results.append({'path':name,'status':'missing'});continue
            content = record['content']
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

    def inventory(self, _records=None):
        """Describe approved snapshot paths only; never traverse the source repository."""
        files=[]; directories=set()
        for name in sorted(self.selected,key=str.casefold):
            record=self.read(name) if _records is None else _records[name]
            content=record['content']
            files.append({'path':name,'sha256':record['sha256'],
                          'exists':record['sha256']!='absent',
                          'content_bytes':len(content.encode('utf-8')),
                          'lines':len(content.splitlines())})
            parent=PurePosixPath(name).parent
            while parent!=PurePosixPath('.'):
                directories.add(parent.as_posix());parent=parent.parent
        return {'scope':'selected_snapshot','files':files,'directories':sorted(directories),
                'source_repository_complete':False}

    def retrieve(self, query, paths, required_paths=()):
        """Deterministic whole-file retrieval within an explicitly approved scope."""
        if (not isinstance(query, str) or not 1 <= len(query) <= 16000
                or not isinstance(paths, list) or not 1 <= len(paths) <= 100
                or not all(isinstance(path, str) for path in paths) or len(set(paths)) != len(paths)
                or not set(required_paths) <= set(paths)):
            raise BoundaryError('Bounded query, unique candidate scope and protected files required')
        for path in paths: self._selected(path)
        terms = sorted(set(re.findall(r'[a-z_][a-z0-9_]{1,63}', query.casefold())))[:100]
        records = {}; total = 0
        for path in paths:
            record = self.read(path); total += len(record['content'].encode())
            if total > 10_485_760: raise BoundaryError('Retrieval scope exceeds total size limit')
            records[path] = record
        def rank(path):
            name = path.casefold(); content = records[path]['content'].casefold()
            score = sum((50 if term in name else 0) + min(content.count(term), 5) for term in terms)
            return (-score, path.casefold())
        ordered = sorted(set(required_paths), key=str.casefold)
        ordered += sorted((path for path in paths if path not in required_paths), key=rank)
        chosen = []; omitted = []; size = 2
        for path in ordered:
            record = records[path]
            cost = len(json.dumps(record, sort_keys=True, separators=(',', ':')).encode()) + (1 if chosen else 0)
            reason = 'file_limit' if len(chosen) >= 20 else 'context_budget' if size + cost > 48000 else None
            if reason:
                if path in required_paths:
                    raise BoundaryError('Protected context exceeds retrieval budget')
                omitted.append({'path': path, 'reason': reason})
            else:
                chosen.append(record); size += cost
        if not any(record['path'] not in required_paths for record in chosen):
            raise BoundaryError('Retrieval requires at least one editable context file')
        return {'algorithm': 'lexical-v1', 'scope': 'selected_snapshot', 'files': chosen,
                'input_hashes': {path: records[path]['sha256'] for path in paths},
                'omitted': omitted, 'query_sha256': digest(query.encode()),
                'source_repository_complete': False}

    def read_lines(self, name, start, count, _records=None):
        """Bounded whole-line context with the full file hash for guarded edits."""
        if type(start) is not int or start<1 or type(count) is not int or not 1<=count<=200:
            raise BoundaryError('Select a positive line and 1..200 lines')
        record=self.read(name) if _records is None else _records[name]
        if record['sha256']=='absent':
            raise BoundaryError('Cannot read lines of an absent creation target')
        lines=record['content'].splitlines(keepends=True)
        if start>len(lines)+1:raise BoundaryError('Line starts beyond end of file')
        result=[];size=0
        for number in range(start,min(start+count,len(lines)+1)):
            text=lines[number-1];length=len(text.encode('utf-8'))
            if size+length>16000:
                if not result:raise BoundaryError('Line exceeds context limit; use a different file')
                break
            result.append({'line':number,'text':text});size+=length
        following=start+len(result)
        return {'path':name,'sha256':record['sha256'],'start':start,'lines':result,
                'total_lines':len(lines),'truncated':following<=len(lines),
                'next_line':following if following<=len(lines) else None}

    def search(self, query, _records=None):
        if not isinstance(query,str) or not query or len(query)>256:
            raise BoundaryError('Search requires 1..256 characters')
        hits=[]
        for name in self.selected:
            record=self.read(name) if _records is None else _records[name]
            for number,line in enumerate(record['content'].splitlines(),1):
                if query in line:
                    hits.append({'path':name,'line':number,'text':line[:256]})
                    if len(hits)==100:
                        return {'hits':hits,'truncated':True}
        return {'hits':hits,'truncated':False}

    def inspect(self, requests, expected_inputs):
        """Run bounded reads over one captured, hash-verified selected-file view."""
        from .inspection import validate_requests
        requests = validate_requests(self, requests)
        if type(expected_inputs) is not dict or set(expected_inputs) != set(self.selected):
            raise BoundaryError('Exact selected inspection input hashes required')
        records = {}; size = 0
        for path in self.selected:
            record = self.read(path)
            if record['sha256'] != expected_inputs[path]:
                raise BoundaryError('Inspection input changed')
            size += len(record['content'].encode('utf-8'))
            if size > 10_485_760:
                raise BoundaryError('Inspection snapshot exceeds size limit')
            records[path] = record
        results = []
        for request in requests:
            operation = request['operation']
            if operation == 'inventory':
                result = self.inventory(_records=records)
            elif operation == 'search':
                result = self.search(request['query'], _records=records)
            else:
                result = self.read_lines(request['path'], request['start'], request['count'], _records=records)
            results.append({'operation': operation, 'result': result})
        return {'input_hashes': {path: record['sha256'] for path, record in records.items()},
                'requests': requests, 'results': results, 'source_repository_complete': False}
