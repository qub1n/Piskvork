"""Launch a suspended Windows process in a kill-on-close, memory-limited job.

All descendants inherit the job; no process-name based cleanup is used.
"""
import ctypes as C
from ctypes import wintypes as W
import subprocess
import time



def process_affinity():
    kernel = C.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.restype = W.HANDLE
    kernel.GetProcessAffinityMask.argtypes = [W.HANDLE, C.POINTER(C.c_size_t), C.POINTER(C.c_size_t)]
    process, system = C.c_size_t(), C.c_size_t()
    if not kernel.GetProcessAffinityMask(kernel.GetCurrentProcess(), C.byref(process), C.byref(system)):
        raise C.WinError(C.get_last_error())
    return process.value


def run(command, cwd, timeout, memory_bytes=1073741824, affinity_mask=1, cancel_event=None, job_memory_bytes=None, observe=None):
    if cancel_event is not None and cancel_event.is_set():
        raise RuntimeError('match cancelled after worker failure')
    if not hasattr(C, 'WinDLL'):
        raise RuntimeError('tournament execution requires Windows')
    kernel = C.WinDLL('kernel32', use_last_error=True)
    class IO(C.Structure):
        _fields_ = [(n, C.c_ulonglong) for n in ('read_ops', 'write_ops', 'other_ops', 'read_bytes', 'write_bytes', 'other_bytes')]
    class BASIC(C.Structure):
        _fields_ = [('process_time', C.c_longlong), ('job_time', C.c_longlong), ('flags', W.DWORD),
                    ('min_ws', C.c_size_t), ('max_ws', C.c_size_t), ('active', W.DWORD),
                    ('affinity', C.c_size_t), ('priority', W.DWORD), ('scheduling', W.DWORD)]
    class LIMIT(C.Structure):
        _fields_ = [('basic', BASIC), ('io', IO), ('process_memory', C.c_size_t),
                    ('job_memory', C.c_size_t), ('peak_process', C.c_size_t), ('peak_job', C.c_size_t)]
    class START(C.Structure):
        _fields_ = [('cb', W.DWORD), ('reserved', W.LPWSTR), ('desktop', W.LPWSTR), ('title', W.LPWSTR),
                    ('x', W.DWORD), ('y', W.DWORD), ('xsize', W.DWORD), ('ysize', W.DWORD),
                    ('xchars', W.DWORD), ('ychars', W.DWORD), ('fill', W.DWORD), ('flags', W.DWORD),
                    ('show', W.WORD), ('reserved_size', W.WORD), ('reserved2', C.POINTER(C.c_byte)),
                    ('stdin', W.HANDLE), ('stdout', W.HANDLE), ('stderr', W.HANDLE)]
    class PROCESS(C.Structure):
        _fields_ = [('process', W.HANDLE), ('thread', W.HANDLE), ('pid', W.DWORD), ('tid', W.DWORD)]
    signatures = {
        'CreateJobObjectW': ([C.c_void_p, W.LPCWSTR], W.HANDLE),
        'SetInformationJobObject': ([W.HANDLE, C.c_int, C.c_void_p, W.DWORD], W.BOOL),
        'CreateProcessW': ([W.LPCWSTR, W.LPWSTR, C.c_void_p, C.c_void_p, W.BOOL, W.DWORD,
                            C.c_void_p, W.LPCWSTR, C.POINTER(START), C.POINTER(PROCESS)], W.BOOL),
        'AssignProcessToJobObject': ([W.HANDLE, W.HANDLE], W.BOOL),
        'ResumeThread': ([W.HANDLE], W.DWORD),
        'WaitForSingleObject': ([W.HANDLE, W.DWORD], W.DWORD),
        'GetExitCodeProcess': ([W.HANDLE, C.POINTER(W.DWORD)], W.BOOL),
        'TerminateProcess': ([W.HANDLE, W.UINT], W.BOOL),
        'CloseHandle': ([W.HANDLE], W.BOOL),
    }
    for name, (args, result) in signatures.items():
        fn = getattr(kernel, name)
        fn.argtypes, fn.restype = args, result
    def check(ok):
        if not ok:
            raise C.WinError(C.get_last_error())
    job = kernel.CreateJobObjectW(None, None)
    check(job)
    process = PROCESS()
    try:
        limits = LIMIT()
        # KILL_ON_JOB_CLOSE | PROCESS_MEMORY | AFFINITY. One logical CPU;
        # memory is per process (manager also constrained), not job total.
        limits.basic.flags = 0x2000 | 0x100 | 0x10
        limits.basic.affinity = affinity_mask
        limits.process_memory = memory_bytes
        if job_memory_bytes is not None:
            if type(job_memory_bytes) is not int or job_memory_bytes <= 0:
                raise ValueError('job memory limit must be a positive integer')
            limits.basic.flags |= 0x200  # JOB_OBJECT_LIMIT_JOB_MEMORY
            limits.job_memory = job_memory_bytes
        check(kernel.SetInformationJobObject(job, 9, C.byref(limits), C.sizeof(limits)))
        start = START()
        start.cb, start.flags, start.show = C.sizeof(start), 1, 0
        check(kernel.CreateProcessW(None, C.create_unicode_buffer(subprocess.list2cmdline(command)),
                                   None, None, False, 0x4 | 0x08000000, None, str(cwd),
                                   C.byref(start), C.byref(process)))
        try:
            check(kernel.AssignProcessToJobObject(job, process.process))
        except Exception:
            kernel.TerminateProcess(process.process, 1)
            raise
        if kernel.ResumeThread(process.thread) == 0xffffffff:
            raise C.WinError(C.get_last_error())
        deadline = time.monotonic() + timeout
        while True:
            if cancel_event is not None and cancel_event.is_set():
                raise RuntimeError('match cancelled after worker failure')
            status = kernel.WaitForSingleObject(process.process, 50)
            if status != 258:
                break
            if observe is not None: observe(process.pid)
            if time.monotonic() >= deadline:
                raise TimeoutError(f'manager exceeded {timeout} seconds')
        if status != 0:
            raise C.WinError(C.get_last_error())
        code = W.DWORD()
        check(kernel.GetExitCodeProcess(process.process, C.byref(code)))
        return code.value
    finally:
        kernel.CloseHandle(job)  # also kills hung or surviving descendants
        for handle in (process.thread, process.process):
            if handle:
                kernel.CloseHandle(handle)
