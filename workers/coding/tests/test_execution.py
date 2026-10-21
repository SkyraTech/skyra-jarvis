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

    def test_absent_target_cannot_count_as_a_protected_test(self):
        workspace=Workspace.snapshot(self.source,self.root/'new-target',[],['test_program.py'])
        profile=NativeProfile('fixture',(sys.executable,'-I','-c','print("must not run")'),('test_program.py',),10)
        runner=NativeExecutor([profile],owner_enabled=True)
        with self.assertRaises(BoundaryError):runner.run(workspace,'fixture')

    def test_native_requires_explicit_owner_setting(self):
        with self.assertRaises(ValueError):NativeExecutor([])

    def test_long_native_profile_is_explicit_and_keeps_legacy_hash_shape(self):
        from dataclasses import asdict
        for timeout in (301, 900, 7200):
            profile=NativeProfile('reviewed-build',(sys.executable,'-I','-c','print("ok")'),('test_program.py',),timeout)
            self.assertEqual(timeout,asdict(profile)['timeout'])
            self.assertEqual({'name','argv','protected_paths','timeout'},set(asdict(profile)))
        for timeout in (True, 1.5, 0, 7201, '600'):
            with self.assertRaises(ValueError): NativeProfile('bad',(sys.executable,),('test_program.py',),timeout)

    def test_long_profile_still_runs_protected_command_without_extra_authority(self):
        w,runner=self.prepare('print("long-profile-fixture")',timeout=900)
        report=runner.run(w,'fixture')
        self.assertTrue(report['passed'],report)
        self.assertTrue(report['cleanup_confirmed'])
        self.assertFalse(report['os_isolation'])

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
        ready=self.root/'child-started'
        release=self.root/'release-child'
        # Cold Windows interpreter startup is not the timeout behaviour under test.
        # Require proof the grandchild started, then release its write only after
        # the job reports cleanup. A surviving child would write the marker.
        child=(f'import time;from pathlib import Path;Path({str(ready)!r}).write_text("ready");'
               'print("grandchild-started",flush=True)\n'
               f'while not Path({str(release)!r}).exists(): time.sleep(0.05)\n'
               f'Path({str(marker)!r}).write_text("bad")')
        code=f'import subprocess,sys,time\nsubprocess.Popen([sys.executable,"-I","-c",{child!r}])\ntime.sleep(30)\n'
        w,runner=self.prepare(code,timeout=10)
        report=runner.run(w,'fixture')
        self.assertEqual('timeout',report['termination'],report)
        self.assertTrue(report['cleanup_confirmed'])
        self.assertTrue(ready.exists(),report)
        self.assertIn('grandchild-started',report['output'])
        release.write_text('release',encoding='utf-8')
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
