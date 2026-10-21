"""Reviewed host templates for new projects; never execute generated instructions.

The first template exposes a Python JSON function and owner-defined examples.
Examples are acceptance evidence for those cases, not product certification.
"""

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile

from .workspace import BoundaryError, Workspace, read_bytes, relative
from .templates import WEB_TEMPLATE, web_files
from .node_templates import TEMPLATE as NODE_TEMPLATE,plan as node_plan


TEMPLATE = 'python-json-function-v1'
TEST = 'tests/test_acceptance.py'
STUB = 'def handle(value):\n    """Implement the approved specification and acceptance contract."""\n    raise NotImplementedError("Implementation pending")\n'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def checksum(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def validate_contract(contract):
    if not isinstance(contract, dict) or set(contract) != {'cases'}:
        raise BoundaryError('A cases-only acceptance contract is required')
    cases = contract['cases']
    if not isinstance(cases, list) or not 1 <= len(cases) <= 32:
        raise BoundaryError('Provide 1..32 acceptance examples')

    def json_value(value, depth=0):
        if depth > 10:
            raise BoundaryError('Acceptance data is nested too deeply')
        if value is None or type(value) in (str, bool, int, float):
            return
        if type(value) is list:
            for child in value:
                json_value(child, depth + 1)
        elif type(value) is dict and all(type(key) is str for key in value):
            for child in value.values():
                json_value(child, depth + 1)
        else:
            raise BoundaryError('Acceptance values must be JSON data')

    labels, inputs = set(), set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {'name', 'input', 'output'}:
            raise BoundaryError('Each example requires name, input and output')
        label = case['name']
        if not isinstance(label, str) or not label.strip() or len(label) > 120 or any(ord(c) < 32 for c in label):
            raise BoundaryError('Use nonempty single-line example names within 120 characters')
        json_value(case['input']); json_value(case['output'])
        try:
            key = canonical(case['input'])
            canonical(case['output'])
        except (ValueError, OverflowError) as error:
            raise BoundaryError('Finite JSON acceptance data required') from error
        if label.casefold() in labels or key in inputs:
            raise BoundaryError('Example names and inputs must be unique')
        labels.add(label.casefold()); inputs.add(key)
    if len(canonical(contract).encode()) > 16000:
        raise BoundaryError('Acceptance contract exceeds 16KB')
    # Return a detached JSON value, never retain caller-owned mutable structures.
    return json.loads(canonical(contract))


def _parent(directory):
    path = Path(directory)
    if not path.is_absolute() or not path.is_dir():
        raise BoundaryError('An existing absolute parent directory is required')
    for candidate in (path, *path.parents):
        info = candidate.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise BoundaryError('Scaffold parent cannot contain links or reparse points')
    return path.resolve()


def destination(parent, name):
    if not isinstance(name, str) or not re.fullmatch(r'[a-z][a-z0-9-]{1,47}', name):
        raise BoundaryError('Use a 2..48 character lowercase project slug')
    relative(name)
    return _parent(parent) / name


def preview(core, actor, specification, expected_sha256, contract, parent, name, python, template=TEMPLATE,node_toolchain=None):
    """Pure review: no directories, permissions, jobs or provider calls are created."""
    from jarvis_core import specifications
    data = specifications.get(core, actor, specification)
    bundle = specifications.validate_documents(data['documents'])
    if (data['state'] != 'approved' or data['sha256'] != expected_sha256
            or hashlib.sha256(bundle.encode()).hexdigest() != expected_sha256):
        raise BoundaryError('An intact, exactly reviewed approved specification is required')
    target = destination(parent, name)
    if template==NODE_TEMPLATE:
        return node_plan(data,target,name,validate_contract(contract),node_toolchain)
    executable = Path(python)
    if not executable.is_absolute() or executable.suffix.lower() != '.exe' or not executable.is_file():
        raise BoundaryError('Select an existing absolute Python .exe')
    contract = validate_contract(contract)
    if template not in {TEMPLATE, WEB_TEMPLATE}:
        raise BoundaryError('Unsupported host template')
    serialized = canonical(contract)
    test = ('import json, sys, unittest\nfrom pathlib import Path\n'
            'sys.path.insert(0, str(Path(__file__).resolve().parents[1]))\n'
            'from app import handle\n\n'
            f'CASES = json.loads({serialized!r})["cases"]\n\n'
            'class AcceptanceTests(unittest.TestCase):\n'
            '    def test_contract(self):\n'
            '        for case in CASES:\n'
            '            with self.subTest(example=case["name"]):\n'
            '                actual = json.dumps(handle(case["input"]), sort_keys=True, separators=(",", ":"), allow_nan=False)\n'
            '                expected = json.dumps(case["output"], sort_keys=True, separators=(",", ":"), allow_nan=False)\n'
            '                self.assertEqual(expected, actual)\n')
    files = {'app.py': STUB, TEST: test, 'acceptance.json': serialized + '\n',
             **{'docs/' + key: value for key, value in data['documents'].items()}}
    # Preserve approved documents verbatim; defaults fill only missing originals.
    defaults = {
        '02_SYSTEM_ARCHITECTURE.md': '# System architecture\n\nPython standard-library function project. app.py exposes handle(value) for JSON-compatible input/output. Protected unittest examples live in tests/test_acceptance.py; acceptance.json records the reviewed contract. No network listener, database or deployment is included.\n',
        '03_DEVELOPMENT_RULES.md': '# Development rules\n\nImplement the approved specification within this template. Preserve protected acceptance tests and acceptance.json. Run the fixed acceptance profile before review. Changes to scope or expected outcomes require owner review. Do not commit or deploy automatically.\n',
        '04_DESIGN_SYSTEM.md': '# Design system\n\nThis function template has no user interface. Visual design, branding and accessibility decisions are pending a future interface scope.\n',
        '07_API_AND_EVENTS.md': '# API and events\n\nThe current local Python interface is app.handle(value), returning JSON-compatible data. acceptance.json defines reviewed input/output examples. HTTP APIs and events are not implemented.\n',
        '09_SECURITY_AND_OPERATIONS.md': '# Security and operations\n\nNo credentials are included. Native execution requires explicit owner configuration and runs with the Windows account privileges. Keep source delivery separate from snapshot edits. Passing example tests is not a security audit or production release approval.\n',
    }
    for key, value in defaults.items():
        files.setdefault('docs/' + key, value)
    selected = ['app.py', TEST, 'acceptance.json']
    protected = [TEST, 'acceptance.json']
    if template == WEB_TEMPLATE:
        files.update(web_files(contract, name))
        selected += ['server.py', 'index.html']
        protected.append('server.py')
        for document, content in {
            '02_SYSTEM_ARCHITECTURE.md': '# System architecture\n\nPython standard-library local website/HTTP service. Protected server.py binds only 127.0.0.1:8000 and routes GET/POST JSON request records through app.handle(value). index.html is editable website content. Tests start a real ephemeral loopback HTTP server. No dependency installation, public hosting or production authentication is included.\n',
            '04_DESIGN_SYSTEM.md': '# Design system\n\nBuild the approved responsive website in index.html. Include semantic structure, keyboard access and readable contrast. Specific branding and visual acceptance require owner review; HTTP examples alone do not certify design.\n',
            '07_API_AND_EVENTS.md': '# API and events\n\nRequest input: method (GET/POST), path, body (UTF-8 string). Response: status, content_type, body. Host transport is protected. Run python server.py locally after reviewed delivery, then visit http://127.0.0.1:8000. Public deployment and event integrations are outside this template.\n',
        }.items():
            if document not in data['documents']:
                files['docs/' + document] = content
    profile = {'name': 'scaffold-acceptance',
               'argv': [str(executable.resolve()), '-I', '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
               'protected_paths': protected, 'timeout': 30}
    return {'template': template, 'project': data['project'],
            'specification': specification, 'specification_sha256': data['sha256'],
            'destination': str(target), 'name': name, 'contract': contract,
            'files': files, 'selected': selected, 'profile': profile,
            'python_sha256': hashlib.sha256(executable.read_bytes()).hexdigest(),
            'document_provenance': {key: ('approved_specification' if key in data['documents'] else 'host_template')
                                    for key in specifications.DOCUMENT_NAMES},
            'limitations': ['Only the reviewed JSON examples are tested.',
                            ('Local HTTP transport only; no public deployment, dependency installation or Git operations.' if template == WEB_TEMPLATE else 'No HTTP server, deployment, dependency installation or Git operations.'),
                            'Filesystem publication and the SQLite audit event are not a shared atomic transaction.',
                            'Workspace registration and native execution require separate owner configuration.']}


def materialize(core, actor, specification, expected_sha256, contract, parent, name,
                python, expected_plan_sha256, template=TEMPLATE,node_toolchain=None):
    """Create an exclusive project bundle after an exact host-side review.

    Windows rename never replaces an existing directory. Failed staging is kept
    for inspection; no broad cleanup or partially published project is attempted.
    """
    if os.name != 'nt':
        raise BoundaryError('Scaffold publication currently requires Windows')
    with core.transaction():
        plan = preview(core, actor, specification, expected_sha256, contract, parent, name, python, template,node_toolchain)
        plan_sha = checksum(plan)
        if plan_sha != expected_plan_sha256:
            raise BoundaryError('Scaffold changed; review the exact plan before creating files')
        target = Path(plan['destination'])
        if target.exists() or target.is_symlink():
            raise BoundaryError('Scaffold destination already exists; existing projects are never overwritten')
        stage = Path(tempfile.mkdtemp(prefix='.jarvis-scaffold-', dir=target.parent))
        # Retain the exact review record if a staging write is interrupted.
        with (stage / 'review.json').open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(canonical({'plan_sha256': plan_sha, 'plan': plan}) + '\n')
        source = stage / 'source'; source.mkdir()
        for name, content in plan['files'].items():
            path = source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(content)
        workspace = Workspace.snapshot(source, stage / 'snapshot', plan['selected'])
        # Self-check before publication; generated tests are protected baseline files.
        syntax = workspace.verify()
        deferred={ 'src/main.ts','src/helpers.ts','src/types.ts','tests/acceptance.test.mjs','tests/run.mjs'} if template==NODE_TEMPLATE else {'index.html'} if template==WEB_TEMPLATE else set()
        if (any(item['status'] != 'passed' and not (item['path'] in deferred and item['status']=='unsupported') for item in syntax['files'])
                or workspace.diff()['changes']):
            raise BoundaryError('Scaffold verification failed; staging retained for inspection')
        registration = {'evidence_root': str(target / 'evidence'),
                        'workspaces': [{'project_id': plan['project'], 'resource_id': 'workspace:' + plan['name'],
                                        'directory': str(target / 'snapshot')}],
                        'execution': {'mode': 'native_trusted', 'owner_enabled': False, 'profiles': [plan['profile']]},
                        'delivery_targets': [{'project_id': plan['project'], 'resource_id': 'source:' + plan['name'],
                                              'workspace_resource': 'workspace:' + plan['name'],
                                              'directory': str(target / 'source')}]}
        manifest = {'plan_sha256': plan_sha, 'plan': plan, 'registration_draft': registration,
                    'initial_state': 'unimplemented', 'source_sha256': {key: hashlib.sha256(value.encode()).hexdigest()
                                                              for key, value in plan['files'].items()}}
        with (stage / 'scaffold.json').open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(canonical(manifest) + '\n')
        # Revalidate the parent immediately before the exclusive Windows rename.
        if _parent(parent) != target.parent:
            raise BoundaryError('Scaffold parent changed; staging retained')
        os.rename(stage, target)
        core._event(plan['project'], 'scaffold.created', canonical({
            'specification': specification, 'plan_sha256': plan_sha,
            'destination': str(target), 'template': template}))
        return {'directory': str(target), 'plan_sha256': plan_sha,
                'registration_draft': registration, 'state': 'unimplemented'}


def receipt(core, actor, specification, parent, name):
    """Recover an initial receipt after a lost create response; never replay writes."""
    from jarvis_core import specifications
    spec = specifications.get(core, actor, specification)
    target = destination(parent, name)
    if not target.exists():
        return {'exists': False}
    _parent(target)
    try:
        data = json.loads(read_bytes(target, 'scaffold.json'))
        plan = data['plan']
        if (checksum(plan) != data['plan_sha256'] or plan['specification'] != specification
                or plan['project'] != spec['project'] or plan['specification_sha256'] != spec['sha256']
                or plan['destination'] != str(target) or plan['name'] != name or plan['template'] not in {TEMPLATE, WEB_TEMPLATE,NODE_TEMPLATE}):
            raise BoundaryError('Scaffold receipt does not match the requested project')
    except (KeyError, TypeError, ValueError) as error:
        raise BoundaryError('Scaffold receipt is invalid; inspect it manually') from error
    subject = canonical({'specification': specification, 'plan_sha256': data['plan_sha256'],
                         'destination': str(target), 'template': plan['template']})
    recorded = core.db.execute("SELECT 1 FROM events WHERE project=? AND kind='scaffold.created' AND subject=?",
                               (spec['project'], subject)).fetchone() is not None
    return {'exists': True, 'directory': str(target), 'plan_sha256': data['plan_sha256'],
            'state': 'unimplemented', 'audit_recorded': recorded, 'registration_required': True}
