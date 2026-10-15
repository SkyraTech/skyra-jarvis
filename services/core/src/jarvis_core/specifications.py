"""Immutable project document snapshots. Approval grants no execution permissions."""

import hashlib
import json

from .store import Conflict, Denied, encode, identifier


def documents(plan):
    """Render model text as inert Markdown; filenames are fixed by the host."""
    def items(values):
        return '\n'.join('- ' + value.replace('\n', '\n  ') for value in values) or '- None specified.'

    phases = '\n\n'.join(
        f"## Phase {i + 1}: {phase['title']}\n\n{items(phase['tasks'])}\n\n"
        f"### Acceptance criteria\n\n{items(phase['acceptance'])}"
        for i, phase in enumerate(plan['phases']))
    return {
        '01_PRODUCT_REQUIREMENTS.md': f"# {plan['title']}\n\n{plan['overview']}\n\n## Requirements\n\n{items(plan['requirements'])}\n\n## Deliverables\n\n{items(plan['deliverables'])}\n",
        '05_PROJECT_TASKS.md': f"# Development plan\n\n{phases}\n",
        '08_TESTING_AND_ACCEPTANCE.md': '# Acceptance criteria\n\n' + '\n\n'.join(
            f"## {phase['title']}\n\n{items(phase['acceptance'])}" for phase in plan['phases']) + '\n',
        '06_PROJECT_MEMORY.md': f"# Planning record\n\nStatus: specification snapshot; implementation has not started.\n\n## Risks and assumptions\n\n{items(plan['risks'])}\n\n## Open questions\n\n{items(plan['questions'])}\n",
    }


def list_specs(core, actor, project):
    core._owned(actor, project)
    return [dict(row) for row in core.db.execute(
        'SELECT id,version,source_turn,sha256,state,created,approved FROM project_specs WHERE project=? ORDER BY version DESC LIMIT 100', (project,))]


def get(core, actor, spec):
    row = core.db.execute('SELECT * FROM project_specs WHERE id=?', (spec,)).fetchone()
    if row is None:
        raise Denied('Specification unavailable')
    core._owned(actor, row['project'])
    result = dict(row)
    result['documents'] = json.loads(result['documents'])
    return result


def publish(core, actor, project, source_turn, expected_version, request_id):
    if type(expected_version) is not int or expected_version < 0 or not request_id.strip():
        raise ValueError('Version and request ID required')
    digest = hashlib.sha256(encode([source_turn, expected_version]).encode()).hexdigest()
    with core.transaction():
        core._owned(actor, project)
        previous = core.db.execute('SELECT id,digest FROM project_specs WHERE project=? AND request_id=?', (project, request_id)).fetchone()
        if previous:
            if previous['digest'] != digest:
                raise Conflict('Request ID reused with different specification')
            return get(core, actor, previous['id'])
        turn = core.model_turn(actor, source_turn)
        if turn['project'] != project or turn['mode'] != 'plan' or turn['state'] != 'completed':
            raise Conflict('A completed plan in this project is required')
        version = core.db.execute('SELECT COALESCE(MAX(version),0) FROM project_specs WHERE project=?', (project,)).fetchone()[0]
        if version != expected_version:
            raise Conflict('Specification changed; refresh before publishing')
        bundle = encode(documents(turn['response']['plan']))
        checksum = hashlib.sha256(bundle.encode()).hexdigest()
        spec = identifier()
        core.db.execute('INSERT INTO project_specs(id,project,version,source_turn,request_id,digest,sha256,documents,state,created,approved) VALUES(?,?,?,?,?,?,?,?,?,?,NULL)',
                        (spec, project, version + 1, source_turn, request_id, digest, checksum, bundle, 'draft', core.clock()))
        core._event(project, 'specification.published', spec)
    return get(core, actor, spec)


def approve(core, actor, spec, expected_sha256):
    with core.transaction():
        data = get(core, actor, spec)
        if data['sha256'] != expected_sha256:
            raise Conflict('Review the exact specification before approving')
        latest = core.db.execute('SELECT MAX(version) FROM project_specs WHERE project=?', (data['project'],)).fetchone()[0]
        if data['version'] != latest or data['state'] == 'superseded':
            raise Conflict('Only the latest specification can be approved')
        if data['state'] == 'draft':
            core.db.execute("UPDATE project_specs SET state='superseded' WHERE project=? AND state='approved'", (data['project'],))
            core.db.execute("UPDATE project_specs SET state='approved',approved=? WHERE id=?", (core.clock(), spec))
            core._event(data['project'], 'specification.approved', spec)
    return get(core, actor, spec)


DOCUMENT_NAMES = (
    '01_PRODUCT_REQUIREMENTS.md', '02_SYSTEM_ARCHITECTURE.md',
    '03_DEVELOPMENT_RULES.md', '04_DESIGN_SYSTEM.md', '05_PROJECT_TASKS.md',
    '06_PROJECT_MEMORY.md', '07_API_AND_EVENTS.md', '08_TESTING_AND_ACCEPTANCE.md',
    '09_SECURITY_AND_OPERATIONS.md',
)
REQUIRED_DOCUMENTS = {DOCUMENT_NAMES[i] for i in (0, 4, 5, 7)}


def validate_documents(bundle):
    if (not isinstance(bundle, dict) or not REQUIRED_DOCUMENTS <= set(bundle)
            or set(bundle) - set(DOCUMENT_NAMES)
            or any(not isinstance(text, str) or not text.strip() or '\x00' in text
                   or len(text.encode()) > 24000 for text in bundle.values())
            or len(encode(bundle).encode()) > 64000):
        raise ValueError('Use supported nonempty Markdown documents within the bundle limit')
    return encode(bundle)


def revise(core, actor, spec, documents, expected_sha256, expected_version, request_id):
    bundle = validate_documents(documents)
    if type(expected_version) is not int or expected_version < 1 or not isinstance(request_id, str) or not request_id.strip():
        raise ValueError('Latest version and request ID required')
    digest = hashlib.sha256(encode(['revision', spec, expected_sha256, expected_version, documents]).encode()).hexdigest()
    with core.transaction():
        parent = get(core, actor, spec)
        prior = core.db.execute('SELECT id,digest FROM project_specs WHERE project=? AND request_id=?', (parent['project'], request_id)).fetchone()
        if prior:
            if prior['digest'] != digest:
                raise Conflict('Request ID reused with different revision')
            return get(core, actor, prior['id'])
        latest = core.db.execute('SELECT MAX(version) FROM project_specs WHERE project=?', (parent['project'],)).fetchone()[0]
        if parent['sha256'] != expected_sha256 or latest != expected_version:
            raise Conflict('Specification changed; refresh before revising')
        if documents == parent['documents']:
            raise Conflict('Revision must change at least one document')
        revised = identifier()
        core.db.execute('INSERT INTO project_specs VALUES(?,?,?,?,?,?,?,?,?,?,NULL,?)',
                        (revised, parent['project'], latest + 1, parent['source_turn'], request_id,
                         digest, hashlib.sha256(bundle.encode()).hexdigest(), bundle, 'draft', core.clock(), spec))
        core._event(parent['project'], 'specification.revised', revised)
    return get(core, actor, revised)


def prepare_export(core, actor, spec, expected_sha256):
    with core.transaction():
        data = get(core, actor, spec)
        if data['state'] != 'approved' or data['sha256'] != expected_sha256:
            raise Conflict('Export requires the reviewed approved specification')
        bundle = validate_documents(data['documents'])
        if hashlib.sha256(bundle.encode()).hexdigest() != data['sha256']:
            raise Conflict('Specification integrity check failed')
        core._event(data['project'], 'specification.export_prepared', spec)
        return {'id': spec, 'project': data['project'], 'version': data['version'],
                'sha256': data['sha256'], 'canonical_documents': bundle,
                'approved': data['approved'], 'prepared': core.clock(), 'parent_spec': data['parent_spec']}
