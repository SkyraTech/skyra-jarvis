import os
from pathlib import Path
import sys
import tempfile
import time
import unittest

REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'workers/coding/src'))
from skyra_coding import Workspace,BoundaryError
from skyra_coding.native import NativeExecutor,NativeProfile
from skyra_coding.execution import DockerSandbox,TestProfile,SandboxUnavailable


@unittest.skipUnless(os.name=='nt','Windows process-tree supervisor')
class NativeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.source=self.root/'source';self.source.mkdir()

    def tearDown(self):self.temp.cleanup()

    def prepare(self,code,timeout=10):
        (self.source/'test_program.py').write_text(code,encoding='utf-8')
        workspace=Workspace.snapshot(self.source,self.root/'run',['test_program.py'])
        profile=NativeProfile('fixture',(sys.executable,'-I','-B','test_program.py'),('test_program.py',),timeout)
        return workspace,NativeExecutor([profile],owner_enabled=True)

    def test_native_requires_explicit_owner_setting(self):
        with self.assertRaises(ValueError):NativeExecutor([])

    def test_real_process_passes_and_does_not_inherit_secret(self):
        self.addCleanup(lambda:os.environ.pop('JARVIS_FIXTURE_SECRET',None))
        os.environ['JARVIS_FIXTURE_SECRET']='do-not-inherit'
        w,runner=self.prepare('import os\nassert "JARVIS_FIXTURE_SECRET" not in os.environ\nprint("real-test-passed")\n')
        report=runner.run(w,'fixture')
        self.assertTrue(report['passed'],report)
        self.assertFalse(report['os_isolation'])
        self.assertIn('real-test-passed',report['output'])

    def test_real_nonzero_exit_is_failure(self):
        w,runner=self.prepare('raise AssertionError("expected fixture failure")\n')
        report=runner.run(w,'fixture')
        self.assertFalse(report['passed']);self.assertNotEqual(0,report['exit_code'])
        self.assertIsNone(report['termination']);self.assertTrue(report['cleanup_confirmed'])

    def test_protected_test_tampering_prevents_execution(self):
        w,runner=self.prepare('print("original")')
        (w.root/'test_program.py').write_text('print("tampered")',encoding='utf-8')
        with self.assertRaises(BoundaryError):runner.run(w,'fixture')

    def test_timeout_terminates_child_process_tree(self):
        marker=self.root/'child-survived'
        child=f'import time;from pathlib import Path;print("grandchild-started",flush=True);time.sleep(2);Path({str(marker)!r}).write_text("bad")'
        code=f'import subprocess,sys,time\nsubprocess.Popen([sys.executable,"-I","-c",{child!r}])\ntime.sleep(30)\n'
        w,runner=self.prepare(code,timeout=1)
        report=runner.run(w,'fixture')
        self.assertEqual('timeout',report['termination'],report)
        self.assertTrue(report['cleanup_confirmed'])
        self.assertIn('grandchild-started',report['output'])
        time.sleep(1.2)
        self.assertFalse(marker.exists())

    def test_poll_cancellation_stops_process(self):
        w,runner=self.prepare('import time\nprint("running",flush=True)\ntime.sleep(30)')
        calls=0
        def poll():
            nonlocal calls
            calls+=1
            if calls>3:raise PermissionError('cancelled')
        report=runner.run(w,'fixture',poll)
        self.assertEqual('authorization_or_cancellation',report['termination'])
        self.assertTrue(report['cleanup_confirmed'])

    def test_output_is_bounded(self):
        w,runner=self.prepare('print("x"*400000)')
        report=runner.run(w,'fixture')
        self.assertFalse(report['passed'])
        self.assertEqual('output_limit',report['termination'])
        self.assertLessEqual(len(report['output']),262144)


class DockerContracts(unittest.TestCase):
    def test_image_must_be_immutable(self):
        with self.assertRaises(ValueError):TestProfile('unit','python:latest',('python','-m','unittest'),('test.py',))

    def test_container_has_no_host_privilege_or_network(self):
        profile=TestProfile('unit','sha256:'+'a'*64,('python','-m','unittest'),('test.py',))
        sandbox=DockerSandbox([profile],executable='not-executed')
        args=sandbox.create_args(profile,Path.cwd(),'jarvis-fixture')
        for required in ['--pull=never','--network=none','--read-only','--cap-drop=ALL','--security-opt=no-new-privileges']:
            self.assertIn(required,args)
        self.assertNotIn('--privileged',args)
        self.assertNotIn('/var/run/docker.sock',' '.join(args))


if __name__=='__main__':unittest.main()
