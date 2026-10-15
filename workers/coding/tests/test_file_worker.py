import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

REPO=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(REPO/'services/core/src'))
sys.path.insert(0,str(REPO/'workers/coding/src'))
from fastapi.testclient import TestClient
from jarvis_core import Core, Conflict, Denied
from jarvis_core.api import Credential,create_app
from skyra_coding import Workspace,FileWorker,BoundaryError


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.source=self.root/'source';self.source.mkdir()
        (self.source/'app.py').write_bytes(b'def answer():\r\n    return 41\r\n')
        (self.source/'unrelated.txt').write_text('user changes',encoding='utf-8')
        self.workspace=Workspace.snapshot(self.source,self.root/'snapshot',['app.py'])
        self.core=Core(self.root/'core.sqlite3')
        self.project=self.core.create_project('owner','Demo')
        self.core.set_policy('owner',self.project,'full',['workspace:demo'])
        self.worker=FileWorker({(self.project,'workspace:demo'):self.workspace},self.root/'artifacts')

    def tearDown(self):
        self.core.close();self.temp.cleanup()

    def run_task(self,payload,action='read'):
        task=self.core.create_task('owner',self.project,action,'workspace:demo',payload)
        token=self.core.start('owner',task)['lease_token']
        return task,self.worker.perform(self.core,'owner',task,token)

    def test_explicit_new_file_creation_is_non_overwriting_and_durable(self):
        workspace=Workspace.snapshot(self.source,self.root/'new-snapshot',['app.py'],['features/new.py'])
        self.assertEqual('absent',workspace.read('features/new.py')['sha256'])
        self.assertFalse(workspace.verify()['passed'])
        self.assertEqual([],workspace.diff()['changes'])
        workspace.create('features/new.py','def answer():\n    return 42\n')
        restored=Workspace(workspace.directory)
        self.assertIn('return 42',restored.read('features/new.py')['content'])
        self.assertEqual('absent',restored.diff()['changes'][0]['before_sha256'])
        self.assertIn('/dev/null',restored.diff()['changes'][0]['patch'])
        self.assertTrue(restored.verify()['passed'])
        with self.assertRaises(FileExistsError):restored.create('features/new.py','overwrite')
        with self.assertRaises(BoundaryError):restored.create('other.py','not selected')
        self.assertFalse((self.source/'features/new.py').exists())

    def test_creation_snapshot_rejects_existing_alias_and_unsafe_targets(self):
        for targets in [['app.py'],['new.py','NEW.py'],['file','file/child.py'],['../escape.py'],['.env'],['test?.py']]:
            with self.subTest(targets=targets),self.assertRaises(BoundaryError):
                Workspace.snapshot(self.source,self.root/'invalid',['app.py'],targets)
        self.assertFalse((self.root/'invalid').exists())

    def test_creation_task_requires_exact_write_approval(self):
        workspace=Workspace.snapshot(self.source,self.root/'creation',['app.py'],['new.py'])
        worker=FileWorker({(self.project,'workspace:demo'):workspace},self.root/'new-evidence')
        self.core.set_policy('owner',self.project,'ask',['workspace:demo'])
        task=self.core.create_task('owner',self.project,'write','workspace:demo',{'operation':'create','path':'new.py','content':'answer = 42\n'})
        waiting=self.core.start('owner',task)
        self.assertEqual('waiting_approval',waiting['state'])
        self.assertFalse((workspace.root/'new.py').exists())
        self.core.decide('owner',waiting['approval_id'],True)
        claim=self.core.start('owner',task)
        result=worker.perform(self.core,'owner',task,claim['lease_token'])
        self.assertEqual('create',worker.evidence(result['evidence'][0])['operation'])
        self.assertEqual('answer = 42\n',workspace.read('new.py')['content'])

    def test_snapshot_preserves_source_and_delivers_selected_diff(self):
        before=self.workspace.read('app.py')['sha256']
        task,result=self.run_task({'operation':'patch','path':'app.py','expected_sha256':before,'old':'return 41','new':'return 42'},'write')
        self.assertIn('return 41',(self.source/'app.py').read_text())
        self.assertEqual('user changes',(self.source/'unrelated.txt').read_text())
        self.assertEqual(['app.py'],[d['path'] for d in self.workspace.diff()['changes']])
        self.assertIn(b'\r\n', (self.workspace.root/'app.py').read_bytes())
        self.assertEqual('succeeded',self.core.task('owner',task)['state'])
        self.assertEqual('patch',self.worker.evidence(result['evidence'][0])['operation'])

    def test_paths_secrets_and_unselected_files_are_denied(self):
        for name in ['../app.py','/app.py','C:/app.py','app.py:stream','sub\\app.py','.git/config','.env','NUL','unrelated.txt']:
            with self.subTest(name=name):
                with self.assertRaises(BoundaryError):self.workspace.read(name)

    def test_stale_patch_does_not_overwrite_user_edit(self):
        before=self.workspace.read('app.py')['sha256']
        (self.workspace.root/'app.py').write_text('user_edit = 9',encoding='utf-8')
        with self.assertRaises(BoundaryError):self.workspace.patch('app.py',before,'return 41','return 42')
        self.assertEqual('user_edit = 9',self.workspace.read('app.py')['content'])

    def test_repeated_anchor_and_changed_baseline_are_rejected(self):
        (self.workspace.root/'app.py').write_text('x=1\nx=1\n',encoding='utf-8')
        with self.assertRaises(BoundaryError):self.workspace.patch('app.py',self.workspace.read('app.py')['sha256'],'x=1','x=2')
        (self.workspace.baseline/'app.py').write_text('tampered',encoding='utf-8')
        with self.assertRaises(BoundaryError):self.workspace.diff()

    def test_hardlinked_file_is_rejected(self):
        os.link(self.source/'app.py',self.source/'linked.py')
        with self.assertRaises(BoundaryError):Workspace.snapshot(self.source,self.root/'hardlinks',['linked.py'])

    def test_symlink_is_rejected(self):
        try:os.symlink(self.source/'app.py',self.workspace.root/'link.py')
        except OSError:self.skipTest('OS account cannot create symlinks')
        self.workspace.selected=(*self.workspace.selected,'link.py')
        with self.assertRaises(BoundaryError):self.workspace.read('link.py')

    def test_syntax_verification_never_executes_code(self):
        marker=self.root/'executed'
        (self.workspace.root/'app.py').write_text(f'from pathlib import Path\nPath({str(marker)!r}).write_text("executed")\n',encoding='utf-8')
        _,result=self.run_task({'operation':'verify'})
        self.assertTrue(result['result']['passed']);self.assertFalse(marker.exists())

    def test_failed_verification_is_failed_task(self):
        (self.workspace.root/'app.py').write_text('def invalid(',encoding='utf-8')
        task,result=self.run_task({'operation':'verify'})
        self.assertFalse(result['success']);self.assertEqual('failed',self.core.task('owner',task)['state'])

    def test_operation_cannot_disguise_write_as_read(self):
        task=self.core.create_task('owner',self.project,'read','workspace:demo',
            {'operation':'patch','path':'app.py','expected_sha256':self.workspace.read('app.py')['sha256'],'old':'41','new':'42'})
        token=self.core.start('owner',task)['lease_token']
        with self.assertRaises(BoundaryError):self.worker.perform(self.core,'owner',task,token)
        self.assertIn('41',self.workspace.read('app.py')['content'])

    def test_process_execution_fails_closed(self):
        task=self.core.create_task('owner',self.project,'execute','workspace:demo',{'operation':'execute','command':'anything'})
        token=self.core.start('owner',task)['lease_token']
        with self.assertRaises(BoundaryError):self.worker.perform(self.core,'owner',task,token)

    def test_completion_cannot_be_replayed(self):
        task=self.core.create_task('owner',self.project,'read','workspace:demo',{'operation':'read','path':'app.py'})
        token=self.core.start('owner',task)['lease_token']
        self.worker.perform(self.core,'owner',task,token)
        with self.assertRaises(Conflict):self.worker.perform(self.core,'owner',task,token)

    def test_policy_revoked_before_effect_blocks_edit(self):
        task=self.core.create_task('owner',self.project,'write','workspace:demo',
            {'operation':'patch','path':'app.py','expected_sha256':self.workspace.read('app.py')['sha256'],'old':'41','new':'42'})
        token=self.core.start('owner',task)['lease_token']
        self.core.set_policy('owner',self.project,'read_only',[])
        with self.assertRaises(Denied):self.worker.perform(self.core,'owner',task,token)
        self.assertIn('41',self.workspace.read('app.py')['content'])

    def test_search_is_scoped(self):
        _,result=self.run_task({'operation':'search','query':'return'})
        self.assertEqual('app.py',result['result']['hits'][0]['path'])

    def test_artifact_tampering_detected(self):
        _,result=self.run_task({'operation':'diff'})
        reference=result['evidence'][0]
        (self.root/'artifacts'/(reference[7:]+'.json')).write_text('tampered',encoding='utf-8')
        with self.assertRaises(BoundaryError):self.worker.evidence(reference)

    def test_snapshot_cannot_be_shared_between_resources(self):
        with self.assertRaises(BoundaryError):
            FileWorker({(self.project,'workspace:a'):self.workspace,(self.project,'workspace:b'):self.workspace},self.root/'other-evidence')

    def test_unsupported_files_do_not_pass_verification(self):
        (self.source/'app.js').write_text('const value = 1;',encoding='utf-8')
        workspace=Workspace.snapshot(self.source,self.root/'javascript',['app.js'])
        self.assertFalse(workspace.verify()['passed'])
        self.assertEqual('unsupported',workspace.verify()['files'][0]['status'])

    def test_missing_adapter_does_not_fall_back_to_host_execution(self):
        token='worker_'+'x'*40
        controller='controller_'+'x'*40
        credentials=[Credential(hashlib.sha256(controller.encode()).hexdigest(),'owner','controller'),
                     Credential(hashlib.sha256(token.encode()).hexdigest(),'owner','worker',frozenset({self.project}))]
        app=create_app(self.root/'core.sqlite3',credentials)
        with TestClient(app,base_url='http://127.0.0.1',client=('127.0.0.1',50000)) as client:
            response=client.post('/v1/tasks/unknown/perform',headers={'Authorization':'Bearer '+token},json={'lease_token':'none'})
            self.assertEqual(503,response.status_code)

    def test_api_approval_edit_verify_and_evidence_workflow(self):
        self.core.set_policy('owner',self.project,'ask',['workspace:demo'])
        tokens={role:role+'_'+'a'*40 for role in ['controller','agent','worker']}
        credentials=[Credential(hashlib.sha256(value.encode()).hexdigest(),'owner',role,
                    frozenset() if role=='controller' else frozenset({self.project})) for role,value in tokens.items()]
        app=create_app(self.root/'core.sqlite3',credentials,file_worker=self.worker)
        with TestClient(app,base_url='http://127.0.0.1',client=('127.0.0.1',50000)) as client:
            def call(method,path,role='controller',body=None):
                return client.request(method,path,headers={'Authorization':'Bearer '+tokens[role]},json=body)
            before=self.workspace.read('app.py')['sha256']
            payload={'operation':'patch','path':'app.py','expected_sha256':before,'old':'41','new':'42'}
            response=call('POST',f'/v1/projects/{self.project}/tasks','agent',{'action':'write','resource':'workspace:demo','payload':payload,'request_id':'edit'})
            task=response.json()['task_id']
            approval=call('POST',f'/v1/tasks/{task}/start','worker').json()['approval_id']
            self.assertIn('41',self.workspace.read('app.py')['content'])
            self.assertEqual(200,call('POST',f'/v1/approvals/{approval}/decision',body={'approve':True}).status_code)
            token=call('POST',f'/v1/tasks/{task}/start','worker').json()['lease_token']
            self.assertEqual(403,call('POST',f'/v1/tasks/{task}/perform','agent',{'lease_token':token}).status_code)
            done=call('POST',f'/v1/tasks/{task}/perform','worker',{'lease_token':token})
            self.assertEqual(200,done.status_code,done.text)
            checksum=done.json()['evidence'][0][7:]
            self.assertEqual(200,call('GET',f'/v1/tasks/{task}/evidence/{checksum}','agent').status_code)
            other=self.core.create_task('owner',self.project,'read','workspace:demo',{'operation':'diff'})
            self.assertEqual(403,call('GET',f'/v1/tasks/{other}/evidence/{checksum}','agent').status_code)
            verified=call('POST',f'/v1/projects/{self.project}/tasks','agent',{'action':'read','resource':'workspace:demo','payload':{'operation':'verify'},'request_id':'check'}).json()['task_id']
            lease=call('POST',f'/v1/tasks/{verified}/start','worker').json()['lease_token']
            checked=call('POST',f'/v1/tasks/{verified}/perform','worker',{'lease_token':lease})
            self.assertTrue(checked.json()['result']['passed'])


if __name__=='__main__':unittest.main()
