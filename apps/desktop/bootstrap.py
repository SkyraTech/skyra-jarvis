"""Provision private local state. No online models or native execution enabled by default."""
import argparse
import base64
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys


class Blob(ctypes.Structure):
    _fields_ = [('length', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]


def protect(value, decrypt=False):
    if os.name != 'nt':
        raise RuntimeError('Windows DPAPI required')
    raw = base64.b64decode(value, validate=True) if decrypt else value.encode('utf-8')
    buffer = ctypes.create_string_buffer(raw)
    source = Blob(len(raw), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    output = Blob()
    crypt32 = ctypes.WinDLL('crypt32', use_last_error=True)
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    if decrypt:
        function = crypt32.CryptUnprotectData
        function.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    else:
        function = crypt32.CryptProtectData
        function.argtypes = [ctypes.POINTER(Blob), wintypes.LPCWSTR, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    function.restype = wintypes.BOOL
    if not function(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(output)):
        raise RuntimeError('Unable to access Windows protected storage')
    try:
        result = ctypes.string_at(output.data, output.length)
    finally:
        kernel32.LocalFree(output.data)
    return result.decode('utf-8') if decrypt else base64.b64encode(result).decode('ascii')


def initialize(directory, port=8010):
    root = Path(directory).resolve()
    if root.exists():
        raise ValueError('Use a new private state directory; existing state is never overwritten')
    if type(port) is not int or not 1024 <= port <= 65535:
        raise ValueError('Invalid local port')
    token = secrets.token_urlsafe(32)
    protected = protect(token)
    root.mkdir(parents=True)
    repo = Path(__file__).resolve().parents[2]
    auth = [{'token_sha256': hashlib.sha256(token.encode()).hexdigest(), 'actor': 'local-owner', 'role': 'controller', 'projects': []}]
    (root / 'auth.json').write_text(json.dumps(auth, indent=2), encoding='utf-8')
    (root / 'desktop.json').write_text(json.dumps({'port': port, 'controller_token_dpapi': protected, 'worker_token_dpapi': None}, indent=2), encoding='utf-8')
    (root / 'launcher.json').write_text(json.dumps({'python': sys.executable, 'core_script': str(repo / 'services/core/run.py'),
        'auth_config': str(root / 'auth.json'), 'database': str(root / 'core.sqlite3'), 'port': port,
        'workspace_config': None, 'runtime_config': None, 'node_toolchain_config':None,'existing_project_config':None,'scaffold_root': None, 'scaffold_execution_enabled': False}, indent=2), encoding='utf-8')
    return root


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=Path(os.environ.get('LOCALAPPDATA', '.')) / 'Skyra/Jarvis')
    parser.add_argument('--port', type=int, default=8010)
    args = parser.parse_args()
    root = initialize(args.directory, args.port)
    print('Initialized private Jarvis state:', root)
    print('Default policy is read-only; no execution or online providers were enabled.')


if __name__ == '__main__':
    main()
