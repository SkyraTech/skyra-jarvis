"""Existing source admission preserves owner files and exact reviewed scope."""
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'services/core/src'))
sys.path.insert(0, str(REPO / 'workers/coding/src'))
from skyra_coding.admission import ProjectAdmission
from skyra_coding.workspace import BoundaryError, Workspace


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'; self.source.mkdir()
        self.state = self.root / 'state'; self.state.mkdir()
        (self.source / 'requirements.md').write_bytes(b'# Owner requirements\r\n')
        (self.source / '.env').write_text('NEVER_COPY=secret', encoding='utf-8')
        self.admission = ProjectAdmission({'internal-project': self.source}, self.state)
        self.args = ('internal-project', 'generation-one', ['requirements.md'], ['src/main.ts'])

    def test_review_and_repeat_preserve_source_and_absent_baselines(self):
        review = self.admission.preview(*self.args)
        self.assertEqual([], list(self.state.iterdir()))
        result = self.admission.materialize(*self.args, expected_sha256=review['sha256'])
        self.assertEqual(result, self.admission.materialize(*self.args, expected_sha256=review['sha256']))
        workspace = Workspace(result['snapshot'])
        self.assertEqual('absent', workspace.read('src/main.ts')['sha256'])
        self.assertEqual(b'# Owner requirements\r\n', (self.source / 'requirements.md').read_bytes())
        self.assertFalse((self.source / 'src').exists())
        self.assertEqual({'requirements.md', 'src/main.ts'}, set(workspace.selected))
        self.assertFalse(result['execution_enabled'])
        self.assertFalse(result['source_repository_complete'])

    def test_changed_existing_or_new_target_rejects_before_reservation(self):
        review = self.admission.preview(*self.args)
        (self.source / 'requirements.md').write_text('Owner changed this', encoding='utf-8')
        with self.assertRaises(BoundaryError):
            self.admission.materialize(*self.args, expected_sha256=review['sha256'])
        self.assertEqual([], list(self.state.iterdir()))
        (self.source / 'src').mkdir(); (self.source / 'src/main.ts').write_text('Owner code')
        with self.assertRaises(BoundaryError): self.admission.preview(*self.args)

    def test_unapproved_roots_secrets_overlap_and_ambiguous_paths_rejected(self):
        for source, files, creates in [('unknown', ['requirements.md'], []),
                ([], ['requirements.md'], []), ('internal-project', ['.env'], []),
                ('internal-project', ['../source/requirements.md'], []),
                ('internal-project', ['requirements.md'], ['REQUIREMENTS.md']),
                ('internal-project', [], ['src', 'src/main.ts'])]:
            with self.subTest(files=files, creates=creates):
                with self.assertRaises(BoundaryError):
                    self.admission.preview(source, 'generation-one', files, creates)
        with self.assertRaises(BoundaryError):
            ProjectAdmission({'internal-project': self.source}, self.source)
        with self.assertRaises(BoundaryError):
            ProjectAdmission({'internal-project': self.source, 'second-name': self.source}, self.state)

    def test_snapshot_or_receipt_tampering_is_not_recovered_as_success(self):
        review = self.admission.preview(*self.args)
        result = self.admission.materialize(*self.args, expected_sha256=review['sha256'])
        snapshot = Path(result['snapshot'])
        (snapshot / 'files/requirements.md').write_text('Changed')
        with self.assertRaises(BoundaryError): self.admission.receipt('generation-one', review['sha256'])
        (snapshot / 'files/requirements.md').write_bytes(b'# Owner requirements\r\n')
        receipt = snapshot.parent / 'admission.json'
        record = json.loads(receipt.read_text()); record['plan']['source'] = 'unknown'
        receipt.write_text(json.dumps(record))
        with self.assertRaises(BoundaryError): self.admission.receipt('generation-one', review['sha256'])

    def test_source_change_during_snapshot_retains_partial_state_without_receipt(self):
        review = self.admission.preview(*self.args)
        original = Workspace.snapshot
        def changed(*args, **kwargs):
            result = original(*args, **kwargs)
            (self.source / 'requirements.md').write_text('Concurrent owner edit')
            return result
        with patch.object(Workspace, 'snapshot', side_effect=changed):
            with self.assertRaises(BoundaryError):
                self.admission.materialize(*self.args, expected_sha256=review['sha256'])
        target = self.state / 'generation-one'
        self.assertTrue((target / 'snapshot').is_dir())
        self.assertFalse((target / 'admission.json').exists())
        self.assertEqual('Concurrent owner edit', (self.source / 'requirements.md').read_text())

    def test_reviewed_intent_cannot_replace_an_existing_admission(self):
        review = self.admission.preview(*self.args)
        self.admission.materialize(*self.args, expected_sha256=review['sha256'])
        args = ('internal-project', 'generation-one', ['requirements.md'], ['other.ts'])
        changed = self.admission.preview(*args)
        with self.assertRaises(BoundaryError):
            self.admission.materialize(*args, expected_sha256=changed['sha256'])

    def test_owner_cli_reviews_then_applies_without_execution_or_source_changes(self):
        host = self.root / 'host.json'
        host.write_text(json.dumps({'sources': {'internal-project': str(self.source)},
                                   'snapshot_root': str(self.state)}))
        request = self.root / 'request.json'
        request.write_text(json.dumps(dict(zip(('source', 'name', 'files', 'create_paths'), self.args))))
        review = self.root / 'review.json'
        command = [sys.executable, str(REPO / 'workers/coding/admit_project.py'),
                   '--host-config', str(host), '--request', str(request)]
        completed = subprocess.run([*command, '--review', str(review)], capture_output=True, text=True, timeout=20)
        self.assertEqual(0, completed.returncode, completed.stderr)
        original_review = review.read_bytes()
        repeated = subprocess.run([*command, '--review', str(review)], capture_output=True, text=True, timeout=20)
        self.assertEqual(2, repeated.returncode)
        self.assertEqual(original_review, review.read_bytes())
        receipt = subprocess.run([*command, '--apply', '--expected-sha256', json.loads(original_review)['sha256']],
                                 capture_output=True, text=True, timeout=20)
        self.assertEqual(0, receipt.returncode, receipt.stderr)
        self.assertTrue(json.loads(receipt.stdout)['admitted'])
        self.assertFalse(json.loads(receipt.stdout)['execution_enabled'])
        self.assertFalse((self.source / 'src').exists())

    def test_owner_cli_refuses_to_write_review_into_source(self):
        host = self.root / 'host.json'
        host.write_text(json.dumps({'sources': {'internal-project': str(self.source)},
                                   'snapshot_root': str(self.state)}))
        request = self.root / 'request.json'
        request.write_text(json.dumps(dict(zip(('source', 'name', 'files', 'create_paths'), self.args))))
        completed = subprocess.run([sys.executable, str(REPO / 'workers/coding/admit_project.py'),
            '--host-config', str(host), '--request', str(request), '--review', str(self.source / 'review.json')],
            capture_output=True, text=True, timeout=20)
        self.assertEqual(2, completed.returncode)
        self.assertFalse((self.source / 'review.json').exists())
