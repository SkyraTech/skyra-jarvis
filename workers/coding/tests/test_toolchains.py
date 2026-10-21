"""Host identity validation is separate from model or renderer configuration."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'workers/coding/src'))
from skyra_coding import BoundaryError
from skyra_coding.toolchains import verify_typescript,inspect_typescript


class ToolchainTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name);self.node=root/'node.exe';self.compiler=root/'tsc.exe'
        self.node.write_bytes(b'identity fixture, never executed');self.compiler.write_bytes(b'compiler identity fixture')
        self.config={'node':str(self.node),'compiler':str(self.compiler),
            'node_sha256':hashlib.sha256(self.node.read_bytes()).hexdigest(),
            'compiler_sha256':hashlib.sha256(self.compiler.read_bytes()).hexdigest(),
            'node_version':'v24.21.0','compiler_version':'Version 7.0.2'}

    def test_verification_is_detached_and_never_executes_the_fixture(self):
        verified=verify_typescript(self.config)
        self.assertEqual(self.config,verified);self.assertIsNot(self.config,verified)
        verified['node_version']='v99.0.0'
        self.assertEqual('v24.21.0',self.config['node_version'])

    def test_changed_node_or_compiler_rejects_the_previously_reviewed_identity(self):
        for path in (self.node,self.compiler):
            original=path.read_bytes();path.write_bytes(original+b'changed')
            with self.assertRaises(BoundaryError):verify_typescript(self.config)
            path.write_bytes(original)

    def test_unbounded_malformed_or_unreviewed_toolchains_fail_closed(self):
        for patch in ({'node':'node.exe'},{'node_sha256':'A'*64},{'compiler_sha256':True},
            {'node_version':'v22.1.0'},{'compiler_version':'Version '+'1'*1000},
            {'node_version':'private-version-secret'},{'extra':'not permitted'}):
            with self.subTest(fields=list(patch)):
                with self.assertRaises(BoundaryError) as caught:verify_typescript({**self.config,**patch})
                self.assertNotIn('private-version-secret',str(caught.exception))
        for value in (None,[],{},'configuration'):
            with self.assertRaises(BoundaryError):verify_typescript(value)

    def test_inspection_requires_explicit_owner_authority_before_any_process(self):
        for consent in (False,None,1):
            with self.assertRaises(BoundaryError):inspect_typescript(str(self.node),str(self.compiler),owner_enabled=consent)


if __name__=='__main__':unittest.main()
