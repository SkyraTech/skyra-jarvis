"""Windows process-tree supervision. Job Objects are not a security sandbox."""

import ctypes as C
from ctypes import wintypes as W
import time


class BasicLimits(C.Structure):
    _fields_=[('process_time',C.c_int64),('job_time',C.c_int64),('flags',W.DWORD),
              ('min_working_set',C.c_size_t),('max_working_set',C.c_size_t),
              ('active_limit',W.DWORD),('affinity',C.c_size_t),('priority',W.DWORD),('scheduling',W.DWORD)]


class ExtendedLimits(C.Structure):
    _fields_=[('basic',BasicLimits),('io',C.c_uint64*6),('process_memory',C.c_size_t),
              ('job_memory',C.c_size_t),('peak_process_memory',C.c_size_t),('peak_job_memory',C.c_size_t)]


class Accounting(C.Structure):
    _fields_=[('times',C.c_int64*4),('page_faults',W.DWORD),('total',W.DWORD),('active',W.DWORD),('terminated',W.DWORD)]


class ThreadEntry(C.Structure):
    _fields_=[('size',W.DWORD),('usage',W.DWORD),('thread',W.DWORD),('process',W.DWORD),
              ('base_priority',W.LONG),('delta_priority',W.LONG),('flags',W.DWORD)]


class WindowsJob:
    def __init__(self):
        self.k=C.WinDLL('kernel32',use_last_error=True)
        definitions={
            'CreateJobObjectW':([C.c_void_p,W.LPCWSTR],W.HANDLE),
            'SetInformationJobObject':([W.HANDLE,C.c_int,C.c_void_p,W.DWORD],W.BOOL),
            'QueryInformationJobObject':([W.HANDLE,C.c_int,C.c_void_p,W.DWORD,C.c_void_p],W.BOOL),
            'TerminateJobObject':([W.HANDLE,W.UINT],W.BOOL),
            'OpenProcess':([W.DWORD,W.BOOL,W.DWORD],W.HANDLE),
            'AssignProcessToJobObject':([W.HANDLE,W.HANDLE],W.BOOL),
            'CloseHandle':([W.HANDLE],W.BOOL),
            'CreateToolhelp32Snapshot':([W.DWORD,W.DWORD],W.HANDLE),
            'Thread32First':([W.HANDLE,C.POINTER(ThreadEntry)],W.BOOL),
            'Thread32Next':([W.HANDLE,C.POINTER(ThreadEntry)],W.BOOL),
            'OpenThread':([W.DWORD,W.BOOL,W.DWORD],W.HANDLE),
            'ResumeThread':([W.HANDLE],W.DWORD),
        }
        for name,(args,result) in definitions.items():
            function=getattr(self.k,name);function.argtypes=args;function.restype=result
        self.handle=self.k.CreateJobObjectW(None,None)
        if not self.handle:raise C.WinError(C.get_last_error())
        limits=ExtendedLimits()
        limits.basic.flags=0x2000|0x200|0x8  # kill-on-close, job memory, active processes
        limits.basic.active_limit=64
        limits.job_memory=1024*1024*1024
        if not self.k.SetInformationJobObject(self.handle,9,C.byref(limits),C.sizeof(limits)):
            self.k.CloseHandle(self.handle);self.handle=None
            raise C.WinError(C.get_last_error())

    def attach_and_resume(self,pid):
        process=self.k.OpenProcess(0x100|0x1,False,pid)
        if not process:raise C.WinError(C.get_last_error())
        try:
            if not self.k.AssignProcessToJobObject(self.handle,process):
                raise C.WinError(C.get_last_error())
        finally:self.k.CloseHandle(process)
        snapshot=self.k.CreateToolhelp32Snapshot(0x4,0)
        if snapshot==C.c_void_p(-1).value:raise C.WinError(C.get_last_error())
        try:
            entry=ThreadEntry();entry.size=C.sizeof(entry)
            found=self.k.Thread32First(snapshot,C.byref(entry))
            while found:
                if entry.process==pid:
                    thread=self.k.OpenThread(0x2,False,entry.thread)
                    if not thread:raise C.WinError(C.get_last_error())
                    try:
                        if self.k.ResumeThread(thread)==0xffffffff:raise C.WinError(C.get_last_error())
                        return
                    finally:self.k.CloseHandle(thread)
                found=self.k.Thread32Next(snapshot,C.byref(entry))
            raise OSError('Suspended process main thread not found')
        finally:self.k.CloseHandle(snapshot)

    def stop(self):
        if not self.handle:return False
        confirmed=False
        try:
            if not self.k.TerminateJobObject(self.handle,1):return False
            deadline=time.monotonic()+5
            while time.monotonic()<deadline:
                accounting=Accounting()
                if not self.k.QueryInformationJobObject(self.handle,1,C.byref(accounting),C.sizeof(accounting),None):break
                if accounting.active==0:confirmed=True;break
                time.sleep(0.02)
            return confirmed
        finally:
            self.k.CloseHandle(self.handle);self.handle=None
