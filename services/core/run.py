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
    parser.add_argument('--port', type=int, default=8010)
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
        app = create_app(database, credentials)
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error):
        parser.error('Unable to load valid credential registry or initialize local state; details withheld')
    uvicorn.run(app, host='127.0.0.1', port=args.port, proxy_headers=False,
                access_log=False, log_level='warning', limit_concurrency=32, timeout_keep_alive=5)


if __name__ == '__main__':
    main()
