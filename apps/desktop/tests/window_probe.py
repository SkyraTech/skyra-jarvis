"""Inspect/close only a caller-owned Jarvis acceptance process, using actual Win32 visibility."""
import argparse
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import time


def probe(pid, close=False):
    user = ctypes.WinDLL('user32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle: raise ValueError('Acceptance process unavailable')
    try:
        name = ctypes.create_unicode_buffer(32768)
        size = wintypes.DWORD(len(name))
        if not kernel.QueryFullProcessImageNameW(handle, 0, name, ctypes.byref(size)) or Path(name.value).name.lower() != 'jarvis-desktop.exe':
            raise ValueError('Probe is restricted to Jarvis acceptance processes')
        callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        user.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
        user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        user.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        user.IsWindowVisible.argtypes = [wintypes.HWND]
        user.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        def visible():
            windows = []
            @callback_type
            def collect(window, _):
                owner = wintypes.DWORD()
                user.GetWindowThreadProcessId(window, ctypes.byref(owner))
                if owner.value == pid:
                    title = ctypes.create_unicode_buffer(512)
                    user.GetWindowTextW(window, title, len(title))
                    if title.value.startswith('Jarvis') and user.IsWindowVisible(window): windows.append(window)
                return True
            user.EnumWindows(collect, 0)
            return windows
        before = visible()
        posted = bool(close and before and user.PostMessageW(before[0], 0x0010, 0, 0))
        if posted:
            for _ in range(30):
                if not visible(): break
                time.sleep(.1)
        after = visible()
        exit_code = wintypes.DWORD()
        kernel.GetExitCodeProcess(handle, ctypes.byref(exit_code))
        return {'before_visible': len(before), 'close_posted': posted, 'after_visible': len(after), 'alive': exit_code.value == 259}
    finally: kernel.CloseHandle(handle)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--close', action='store_true')
    args = parser.parse_args()
    print(json.dumps(probe(args.pid, args.close)))
