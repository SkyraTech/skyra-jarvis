"""Explicit loopback-only launcher. No credentials are accepted on the command line."""

import argparse
import json
import os
from pathlib import Path
import sys
import sqlite3

sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))


def main():
    parser = argparse.ArgumentParser(description='Jarvis authenticated local core')
    parser.add_argument('--auth-config', type=Path, required=True,
                        help='JSON credential registry containing SHA-256 digests only')
    parser.add_argument('--database', type=Path)
    parser.add_argument('--workspace-config', type=Path,
                        help='Optional trusted snapshot registry for the file worker')
    parser.add_argument('--port', type=int, default=8010)
    parser.add_argument('--runtime-config', type=Path,
                        help='Optional trusted provider/skill registry; environment key names only')
    parser.add_argument('--enable-unattended', action='store_true',
                        help='Owner-enabled bounded assignment progression; does not grant task permissions')
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error('Port must be between 1024 and 65535')
    # Use private per-user app data, not the synced repository, for durable state.
    local_data = os.environ.get('LOCALAPPDATA')
    if args.database is None and not local_data:
        parser.error('Set --database explicitly when LOCALAPPDATA is unavailable')
    database = args.database or Path(local_data) / 'Skyra' / 'Jarvis' / 'core.sqlite3'
    from jarvis_core.api import Credential, create_app
    import uvicorn
    try:
        registry = json.loads(args.auth_config.read_text(encoding='utf-8'))
        if not isinstance(registry, list) or not registry:
            raise ValueError('Invalid registry')
        credentials = []
        for entry in registry:
            if not isinstance(entry, dict) or set(entry) - {'token_sha256', 'actor', 'role', 'projects'}:
                raise ValueError('Invalid entry')
            if not isinstance(entry.get('projects', []), list):
                raise ValueError('Projects must be a list')
            credentials.append(Credential(entry['token_sha256'], entry['actor'], entry['role'],
                                          frozenset(entry.get('projects', []))))
        file_worker = None
        if args.workspace_config:
            sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'workers/coding/src'))
            from skyra_coding import Workspace, FileWorker
            config = json.loads(args.workspace_config.read_text(encoding='utf-8'))
            if not isinstance(config,dict) or not {'evidence_root','workspaces'}<=set(config) or set(config)-{'evidence_root','workspaces','execution','delivery_targets'}:
                raise ValueError('Invalid workspace config')
            registrations = {}
            for entry in config['workspaces']:
                if set(entry)!={'project_id','resource_id','directory'}:
                    raise ValueError('Invalid workspace registration')
                key = (entry['project_id'],entry['resource_id'])
                if key in registrations or not all(isinstance(x,str) and x for x in key):
                    raise ValueError('Duplicate or invalid workspace registration')
                if not Path(entry['directory']).is_absolute():
                    raise ValueError('Workspace paths must be absolute')
                registrations[key] = Workspace(entry['directory'])
            if not registrations or not Path(config['evidence_root']).is_absolute():
                raise ValueError('Absolute evidence root and registrations required')
            sandbox=None
            if 'execution' in config:
                from skyra_coding.execution import DockerSandbox,TestProfile
                execution=config['execution']
                if not isinstance(execution,dict):
                    raise ValueError('Invalid execution config')
                mode=execution.get('mode','docker')
                if mode=='native_trusted':
                    from skyra_coding.native import NativeExecutor,NativeProfile
                    if set(execution)!={'mode','owner_enabled','profiles'} or execution['owner_enabled'] is not True:
                        raise ValueError('Explicit native permission required')
                    profiles=[]
                    for profile in execution['profiles']:
                        if set(profile)!={'name','argv','protected_paths','timeout'}:
                            raise ValueError('Invalid native profile')
                        if not isinstance(profile['argv'],list) or not isinstance(profile['protected_paths'],list):
                            raise ValueError('Invalid native argument lists')
                        profiles.append(NativeProfile(profile['name'],tuple(profile['argv']),tuple(profile['protected_paths']),profile['timeout']))
                    sandbox=NativeExecutor(profiles,owner_enabled=True)
                elif mode=='docker':
                    if set(execution)-{'mode','context','profiles'} or not {'context','profiles'}<=set(execution):
                        raise ValueError('Invalid Docker config')
                    profiles=[]
                    for profile in execution['profiles']:
                        if set(profile)!={'name','image','argv','protected_paths','timeout'}:
                            raise ValueError('Invalid profile')
                        if not isinstance(profile['argv'],list) or not isinstance(profile['protected_paths'],list):
                            raise ValueError('Invalid profile argument lists')
                        profiles.append(TestProfile(profile['name'],profile['image'],tuple(profile['argv']),tuple(profile['protected_paths']),profile['timeout']))
                    sandbox=DockerSandbox(profiles,context=execution['context'])
                else:raise ValueError('Unknown execution mode')
            file_worker = FileWorker(registrations,config['evidence_root'],sandbox=sandbox,delivery_targets=config.get('delivery_targets',[]))
        repair_runtime = None
        conversation_runtime = None
        if args.runtime_config:
            # Shared runtime package imports coding contracts even for chat-only configuration.
            sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'workers/coding/src'))
            sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'packages/agent-runtime/src'))
            from jarvis_runtime import RepairRuntime, Skill
            from jarvis_runtime.providers import load_providers
            runtime_config = json.loads(args.runtime_config.read_text(encoding='utf-8'))
            if not isinstance(runtime_config,dict) or set(runtime_config)!={'providers','skills'}:
                raise ValueError('Invalid runtime config')
            if not isinstance(runtime_config['skills'],list) or len(runtime_config['skills'])>50:
                raise ValueError('Invalid skill registry')
            skills=[]
            for entry in runtime_config['skills']:
                if not isinstance(entry,dict) or set(entry)!={'name','version','instructions'}:
                    raise ValueError('Invalid skill')
                skills.append(Skill(**entry))
            from jarvis_runtime.conversation import ConversationRuntime
            providers = load_providers(runtime_config['providers'])
            conversation_runtime = ConversationRuntime(providers)
            if file_worker is not None:
                repair_runtime = RepairRuntime(file_worker, providers, skills)
        app = create_app(database, credentials,file_worker=file_worker,repair_runtime=repair_runtime,conversation_runtime=conversation_runtime,unattended_enabled=args.enable_unattended)
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error):
        parser.error('Unable to load valid credential registry or initialize local state; details withheld')
    uvicorn.run(app, host='127.0.0.1', port=args.port, proxy_headers=False,
                access_log=False, log_level='warning', limit_concurrency=32, timeout_keep_alive=5)


if __name__ == '__main__':
    main()
