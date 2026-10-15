"""Reviewed source writes, separately registered and bound to real tested input hashes."""
from dataclasses import asdict
import json
import os
from pathlib import Path
import tempfile

from jarvis_core import Conflict, Denied
from .workspace import BoundaryError, checked, read_bytes, digest, relative


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def checksum(value):
    return digest(encoded(value).encode())


class Delivery:
    def __init__(self, worker, targets=()):
        self.worker=worker
        self.targets={}
        for entry in targets:
            if set(entry)!={'project_id','resource_id','workspace_resource','directory'}:
                raise ValueError('Invalid delivery target')
            key=(entry['project_id'],entry['resource_id'])
            workspace_key=(entry['project_id'],entry['workspace_resource'])
            source=Path(entry['directory'])
            if (key in self.targets or key in worker.workspaces or workspace_key not in worker.workspaces
                    or not source.is_absolute() or not source.is_dir()):
                raise ValueError('Explicit distinct source target and workspace required')
            source=source.resolve()
            for protected in [worker.evidence_root,*[w.directory for w in worker.workspaces.values()]]:
                if source.is_relative_to(protected) or protected.is_relative_to(source):
                    raise ValueError('Delivery source must be outside worker state')
            if any(source.is_relative_to(value[1]) or value[1].is_relative_to(source)
                   for value in self.targets.values()):
                raise ValueError('Delivery registrations cannot overlap')
            self.targets[key]=(entry['workspace_resource'],source)

    def binding(self, core, actor, project, target):
        policy=core._owned(actor,project)
        if target not in json.loads(policy['resources']):
            raise Denied('Source resource outside grants')
        binding=self.targets.get((project,target))
        if binding is None or binding[0] not in json.loads(policy['resources']):
            raise Denied('Source target or workspace unavailable')
        return self.worker.workspaces[(project,binding[0])],binding

    def preview(self, core, actor, run_id, target, source_check=True):
        from .workflow import CodingWorkflow
        run=CodingWorkflow(self.worker).get(core,actor,run_id)
        workspace,(resource,source)=self.binding(core,actor,run['project'],target)
        if run['state']!='ready_for_review' or resource!=run['resource'] or not all(r['expectation_met'] for r in run['results']):
            raise Conflict('A completed verified coding run is required')
        test_index=max(i for i,step in enumerate(run['steps']) if step['action']=='execute')
        result=run['results'][test_index]
        test=self.worker.evidence(result['evidence'][0])
        profile=self.worker.sandbox.profiles.get(run['steps'][test_index]['payload']['profile']) if self.worker.sandbox else None
        if profile is not None:
            self.worker.profile(run['project'], run['resource'], profile.name)
        hashes={name:workspace.read(name)['sha256'] for name in workspace.selected}
        report=test.get('result',{})
        if (profile is None or test.get('task_id')!=result['task_id'] or test.get('operation')!='test'
                or report.get('kind') not in {'native_test','container_test'} or report.get('passed') is not True
                or report.get('exit_code')!=0 or report.get('cleanup_confirmed') is not True or report.get('termination') is not None
                or report.get('input_hashes')!=hashes or report.get('profile_sha256')!=checksum(asdict(profile))):
            raise Conflict('Snapshot or test profile differs from verified inputs')
        final=run['results'][-1]
        evidence=self.worker.evidence(final['evidence'][0])
        changes=workspace.diff()
        if evidence.get('task_id')!=final['task_id'] or evidence.get('operation')!='diff' or evidence.get('result')!=changes:
            raise Conflict('Diff evidence changed')
        if not 1<=len(changes['changes'])<=10:
            raise Conflict('Delivery requires 1..10 changed files')
        if any(change['path'] in profile.protected_paths for change in changes['changes']):
            raise Conflict('Protected tests cannot be delivered')
        plan={'operation':'deliver','run':run_id,'target':target,'workspace':resource,
              'target_binding_sha256':checksum({'source':os.path.normcase(str(source)),
                                               'snapshot':os.path.normcase(str(workspace.directory))}),
              'inputs':hashes,'baseline':workspace.original_hashes,'changes':changes['changes'],
              'profile_sha256':report['profile_sha256']}
        if len(encoded(plan).encode())>128000:
            raise ValueError('Delivery review exceeds 128 KB')
        if source_check:self.check_source(source,plan['baseline'])
        return {'plan':plan,'sha256':checksum(plan)}

    @staticmethod
    def check_source(source, baseline):
        for name,expected in baseline.items():
            path=checked(source,name)
            actual=digest(read_bytes(source,name)) if path.exists() else 'absent'
            if actual!=expected:raise Conflict('Source differs from snapshot baseline')

    def prepare(self, core, actor, run_id, target, expected_sha256, request_id):
        from .workflow import CodingWorkflow
        run=CodingWorkflow(self.worker).get(core,actor,run_id)
        self.binding(core,actor,run['project'],target)
        prior=core.db.execute('SELECT task FROM task_requests WHERE project=? AND request_id=?',(run['project'],'delivery:'+request_id)).fetchone()
        if prior:
            task=core.task(actor,prior['task']);plan=json.loads(task['payload'])
            if plan.get('run')!=run_id or plan.get('target')!=target or checksum(plan)!=expected_sha256:
                raise Conflict('Delivery request reused')
        else:
            preview=self.preview(core,actor,run_id,target)
            if preview['sha256']!=expected_sha256:raise Conflict('Review current delivery manifest')
            task_id=core.create_task(actor,run['project'],'write',target,preview['plan'],'delivery:'+request_id)
            task=core.task(actor,task_id)
        with core.transaction():
            if not core.db.execute("SELECT 1 FROM events WHERE project=? AND kind='delivery.prepared' AND subject=?",(run['project'],task['id'])).fetchone():
                core._event(run['project'],'delivery.prepared',task['id'])
        return self.status(core,actor,task['id'])

    def status(self, core, actor, task_id):
        task=core.task(actor,task_id)
        plan=json.loads(task['payload'])
        if plan.get('operation')!='deliver':raise Denied('Not a source delivery task')
        return {'id':task_id,'run':plan['run'],'target':task['resource'],'state':task['state'],
                'sha256':checksum(plan),'evidence':json.loads(task['evidence'] or '[]')}

    def list(self, core, actor, run_id):
        from .workflow import CodingWorkflow
        run=CodingWorkflow(self.worker).get(core,actor,run_id)
        rows=core.db.execute("SELECT id FROM tasks WHERE project=? AND json_extract(payload,'$.operation')='deliver' AND json_extract(payload,'$.run')=? ORDER BY rowid DESC LIMIT 100",(run['project'],run_id))
        return [self.status(core,actor,row['id']) for row in rows]

    def apply(self, core, actor, intent):
        plan=json.loads(intent['payload'])
        if (intent['action']!='write' or plan.get('target')!=intent['resource']
                or not core.db.execute("SELECT 1 FROM events WHERE project=? AND kind='delivery.prepared' AND subject=?",(intent['project'],intent['id'])).fetchone()):
            raise Denied('Controller-prepared source delivery required')
        journal=None;written=[]
        try:
            workspace,(_,source)=self.binding(core,actor,intent['project'],intent['resource'])
            current=self.preview(core,actor,plan['run'],intent['resource'])
            if current['plan']!=plan:raise Conflict('Delivery manifest changed')
            journal=self.worker.evidence_root/('delivery-'+intent['id'])
            journal.mkdir(exist_ok=False)
            record={'task':intent['id'],'manifest_sha256':checksum(plan),'state':'prepared','written':[],'plan':plan}
            def save():
                data=encoded(record).encode()
                fd,temp=tempfile.mkstemp(prefix='.journal-',dir=journal)
                try:
                    with os.fdopen(fd,'wb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
                    os.replace(temp,journal/'journal.json')
                finally:
                    if os.path.exists(temp):os.unlink(temp)
            # Preserve every changed original before the first source effect.
            for change in plan['changes']:
                if change['before_sha256']!='absent':
                    backup=journal/'before'/relative(change['path']);backup.parent.mkdir(parents=True,exist_ok=True)
                    with backup.open('xb') as stream:stream.write(read_bytes(source,change['path']));stream.flush();os.fsync(stream.fileno())
            save()
            for change in plan['changes']:
                core._lease(actor,intent['id'],intent['lease_token'])
                name=change['path'];self.check_source(source,{name:change['before_sha256']})
                content=read_bytes(workspace.root,name)
                if digest(content)!=change['sha256']:raise Conflict('Snapshot changed during delivery')
                record['state']='applying';record['next']=name;save()
                target=checked(source,name);target.parent.mkdir(parents=True,exist_ok=True);target=checked(source,name)
                if change['before_sha256']=='absent':
                    with target.open('xb') as stream:stream.write(content);stream.flush();os.fsync(stream.fileno())
                else:
                    fd,temp=tempfile.mkstemp(prefix='.jarvis-deliver-',dir=target.parent)
                    try:
                        with os.fdopen(fd,'wb') as stream:stream.write(content);stream.flush();os.fsync(stream.fileno())
                        self.check_source(source,{name:change['before_sha256']});os.replace(temp,target)
                    finally:
                        if os.path.exists(temp):os.unlink(temp)
                written.append(name);record['written']=list(written);record['next']=None;save()
            record['state']='delivered';save()
            return {'passed':True,'state':'delivered','manifest_sha256':checksum(plan),'written':written,'recovery_record':journal.name}
        except (OSError,ValueError,Conflict,Denied):
            # No automatic overwrite, rollback, or replay after an uncertain multi-file effect.
            if journal is not None and journal.exists() and 'record' in locals():
                record['state']='blocked_or_partial'
                record['written']=list(written)
                try:save()
                except OSError:pass  # The last durable next/write record remains authoritative.
            return {'passed':False,'state':'blocked_or_partial','written':written,
                    'recovery_record':journal.name if journal else None}
