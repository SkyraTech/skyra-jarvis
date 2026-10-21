"""Reviewed production scaffold paths; real compiler/tests, deterministic implementation fixture."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import socket
import time
import urllib.request
import unittest
from unittest.mock import patch

import test_scaffold
from jarvis_core import Core,Denied
from jarvis_core.api import Credential,create_app
from fastapi.testclient import TestClient
from jarvis_core.build_jobs import BuildJobs
from jarvis_runtime import RepairRuntime,node_calibration
from skyra_coding import FileWorker,BoundaryError
from skyra_coding.scaffold import preview,materialize,checksum
from skyra_coding.node_templates import TEMPLATE,portable_numbers
from skyra_coding.registry import ScaffoldRegistry
from skyra_coding.toolchains import executable_digest


@unittest.skipUnless(os.name=='nt' and shutil.which('node'),'Windows and installed Node required')
class NodeScaffoldTests(unittest.TestCase):
    setUp=test_scaffold.ScaffoldTests.setUp

    def prepare(self):
        self.tools=node_calibration.toolchain()
        args={**self.args,'template':TEMPLATE,'node_toolchain':self.tools}
        self.plan=preview(self.core,'owner',**args)
        self.created=materialize(self.core,'owner',**args,expected_plan_sha256=checksum(self.plan))
        self.worker=FileWorker({},self.root/'evidence')
        self.registry=ScaffoldRegistry(self.worker,self.root,enabled=True)
        reviewed=self.registry.preview(self.core,'owner',self.spec,self.args['name'],checksum(self.plan))
        self.registration=self.registry.register(self.core,'owner',self.spec,self.args['name'],checksum(self.plan),
            reviewed['registration_sha256'],True)['registration']
        return self.registration

    def test_node_creation_is_separately_configured_and_preserves_approved_documents(self):
        with self.assertRaises(BoundaryError):preview(self.core,'owner',**self.args,template=TEMPLATE)
        self.assertFalse((self.root/self.args['name']).exists())
        registration=self.prepare()
        self.assertNotIn('python_sha256',self.plan);self.assertNotIn('python_sha256',registration)
        self.assertEqual(self.tools['node_sha256'],registration['executable_sha256'])
        self.assertEqual(self.tools,registration['runtime']['toolchain'])
        self.assertEqual('read_only',self.core._owned('owner',self.project)['mode'])
        self.assertEqual([],json.loads(self.core._owned('owner',self.project)['resources']))
        for name,content in self.documents.items():self.assertEqual(content,self.plan['files']['docs/'+name])
        self.assertIn('Strict TypeScript',self.plan['files']['docs/02_SYSTEM_ARCHITECTURE.md'])
        self.assertEqual({self.tools['compiler']:self.tools['compiler_sha256']},
            self.worker.toolchain_bindings[(self.project,registration['workspace'])])

    def build_project(self):
        registration=self.prepare();workspace=self.worker.workspaces[(self.project,registration['workspace'])]
        self.core.set_policy('owner',self.project,'full',[registration['workspace']])
        class Provider:
            provider='fixture';model='node-scaffold-fixture';timeout=1;max_output_tokens=1000
            calls=0
            def complete(provider,system,context,schema):
                provider.calls+=1
                record=next(f for f in json.loads(context)['files'] if f['path']=='src/main.ts')
                return json.dumps({'summary':'Implement the reviewed numeric doubling contract','patches':[{
                    'path':'src/main.ts','old':record['content'],
                    'new':'import type { JsonValue } from "./types.ts";\nexport function handle(value: JsonValue): JsonValue {\n  if (typeof value !== "number") throw new TypeError("Number required");\n  return value * 2;\n}\n'}]}),{'total_tokens':80}
        provider=Provider();runtime=RepairRuntime(self.worker,{'fixture':provider});jobs=BuildJobs(runtime)
        now=[1000.];self.core.clock=lambda:now[0]
        job=jobs.create(self.core,'owner',self.project,registration['workspace'],registration['profile']['name'],'fixture',
            'Implement the approved doubling contract.',registration['selected'],[],1,1,30,3600,False,True,'node-build',
            mode='feature',edit_protocol='host-bound-v2',expected_skills={})
        for _ in range(10):
            now[0]+=6;result=jobs.tick(self.core,'owner',self.project)['build_job']
            if result and result['state']=='waiting_review':break
        self.assertEqual('waiting_review',result['state'],result)
        proposal=runtime.get(self.core,'owner',result['proposal'])
        jobs.accept(self.core,'owner',job['id'],proposal['context_sha256'],proposal['response_sha256'])
        self.core.close();self.core=Core(self.database,clock=lambda:now[0])
        self.addCleanup(self.core.close)
        restored=FileWorker({},self.root/'evidence')
        restored_registry=ScaffoldRegistry(restored,self.root,enabled=True);restored_registry.sync(self.core)
        runtime=RepairRuntime(restored,{'fixture':provider});jobs=BuildJobs(runtime)
        for _ in range(12):
            now[0]+=6;result=jobs.tick(self.core,'owner',self.project)['build_job']
            if result and result['state'] in {'completed','failed','blocked'}:break
        self.assertEqual('completed',result['state'],result);self.assertEqual(1,provider.calls)
        self.assertIn('Implementation pending',(Path(registration['directory'])/'source/src/main.ts').read_text())
        self.assertIn('return value * 2',workspace.read('src/main.ts')['content'])
        with patch('skyra_coding.worker.executable_digest',side_effect=lambda path:
                   '0'*64 if str(path)==self.tools['compiler'] else executable_digest(path)):
            with self.assertRaises(BoundaryError):restored.profile(self.project,registration['workspace'],registration['profile']['name'])
        return registration,result

    def test_registered_node_project_builds_retests_and_restores_without_source_mutation(self):
        self.build_project()

    def test_node_toolchain_survives_reviewed_delivery_and_continuation_without_new_grants(self):
        registration,result=self.build_project()
        self.core.set_policy('owner',self.project,'full',[registration['workspace'],registration['source']])
        delivery=self.worker.delivery
        review=delivery.preview(self.core,'owner',result['run'],registration['source'])
        task=delivery.prepare(self.core,'owner',result['run'],registration['source'],review['sha256'],'node-delivery')['id']
        lease=self.core.start('owner',task);self.worker.perform(self.core,'owner',task,lease['lease_token'])
        self.assertEqual('succeeded',self.core.task('owner',task)['state'])
        continued=self.registry.continuation_preview(self.core,'owner',task,'node-next')
        self.registry.continue_project(self.core,'owner',task,'node-next',continued['registration_sha256'],True)
        saved=json.loads(self.core.db.execute("SELECT config FROM scaffold_registrations WHERE name='node-next'").fetchone()[0])
        self.assertNotIn('python_sha256',saved)
        self.assertEqual(registration['runtime'],saved['runtime'])
        grants=json.loads(self.core._owned('owner',self.project)['resources'])
        self.assertNotIn(saved['workspace'],grants);self.assertNotIn(saved['source'],grants)
        self.assertEqual(self.tools['compiler_sha256'],self.worker.toolchain_bindings[(self.project,saved['workspace'])][self.tools['compiler']])

    def test_node_api_cannot_accept_renderer_tool_paths_or_bypass_host_disable(self):
        token='controller_'+'z'*40
        credentials=[Credential(hashlib.sha256(token.encode()).hexdigest(),'owner','controller')]
        body={'name':'node-api','expected_sha256':self.spec_hash,'contract':self.args['contract'],'template':TEMPLATE}
        with TestClient(create_app(self.database,credentials,scaffold_root=self.root),
            base_url='http://127.0.0.1',client=('127.0.0.1',50000)) as client:
            headers={'Authorization':'Bearer '+token}
            url='/v1/specifications/'+self.spec+'/scaffolds/preview'
            self.assertEqual(403,client.post(url,json=body,headers=headers).status_code)
            self.assertEqual(422,client.post(url,json={**body,'node_toolchain':{}},headers=headers).status_code)
            setup=client.get('/v1/setup',headers=headers).json()
            self.assertNotIn(TEMPLATE,setup['scaffolds']['templates'])

    def test_node_examples_reject_unsafe_numeric_precision_without_changing_python_contracts(self):
        for value in (9007199254740992,2**2000,float('inf'),float('nan')):
            with self.assertRaises(BoundaryError):portable_numbers({'input':value})

    def test_owner_inspection_cli_writes_only_new_configuration_and_enables_no_project(self):
        tools=node_calibration.toolchain();output=self.root/'reviewed-toolchain.json'
        command=[sys.executable,str(test_scaffold.ROOT/'workers/coding/inspect_toolchain.py'),
            '--node',tools['node'],'--compiler',tools['compiler'],'--output',str(output)]
        result=subprocess.run(command,capture_output=True,text=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
        self.assertEqual(0,result.returncode,result.stderr)
        self.assertEqual(tools,json.loads(output.read_text(encoding='utf-8')))
        self.assertIs(json.loads(result.stdout)['project_execution_enabled'],False)
        before=output.read_bytes()
        repeated=subprocess.run(command,capture_output=True,text=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
        self.assertEqual(1,repeated.returncode);self.assertEqual(before,output.read_bytes())

    def test_invalid_optional_toolchain_does_not_prevent_authenticated_core_startup(self):
        token='controller_'+'q'*40
        auth=self.root/'auth.json';bad=self.root/'invalid-node.json'
        auth.write_text(json.dumps([{'token_sha256':hashlib.sha256(token.encode()).hexdigest(),
            'actor':'owner','role':'controller','projects':[]}]),encoding='utf-8')
        bad.write_text('{"invalid":"not a toolchain"}',encoding='utf-8')
        with socket.socket() as listener:
            listener.bind(('127.0.0.1',0));port=listener.getsockname()[1]
        process=subprocess.Popen([sys.executable,str(test_scaffold.ROOT/'services/core/run.py'),
            '--database',str(self.database),'--auth-config',str(auth),'--node-toolchain-config',str(bad),'--existing-project-config',str(bad),'--port',str(port)],
            stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            payload=None
            for _ in range(80):
                if process.poll() is not None:self.fail('Optional toolchain failure stopped Core')
                try:
                    request=urllib.request.Request(f'http://127.0.0.1:{port}/v1/setup',headers={'Authorization':'Bearer '+token})
                    with urllib.request.urlopen(request,timeout=1) as response:payload=json.load(response)
                    break
                except OSError:time.sleep(.1)
            self.assertIsNotNone(payload)
            self.assertEqual('requires_review',payload['scaffolds']['node_toolchain_status'])
            self.assertNotIn(TEMPLATE,payload['scaffolds']['templates'])
            self.assertEqual('requires_review',payload['existing_projects']['status'])
            self.assertFalse(payload['existing_projects']['available'])
        finally:
            process.terminate()
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)


if __name__=='__main__':unittest.main()
