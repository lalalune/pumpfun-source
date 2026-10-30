"""Source-tree receipts; excludes the crate-root target directory and Git metadata."""
import hashlib
import json
import os
import stat
from pathlib import Path


if os.name == 'nt':
    import ctypes
    from ctypes import wintypes
    import msvcrt

    class _FileBasicInfo(ctypes.Structure):
        _fields_ = [('CreationTime', ctypes.c_longlong),
                    ('LastAccessTime', ctypes.c_longlong),
                    ('LastWriteTime', ctypes.c_longlong),
                    ('ChangeTime', ctypes.c_longlong),
                    ('FileAttributes', wintypes.DWORD)]

    _get_basic_info = ctypes.WinDLL('kernel32', use_last_error=True).GetFileInformationByHandleEx
    _get_basic_info.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    _get_basic_info.restype = wintypes.BOOL


def _windows_change_time(descriptor):
    # Python 3.12 st_ctime is creation time on Windows, not metadata-change time.
    if os.name != 'nt':
        return None
    information = _FileBasicInfo()
    handle = msvcrt.get_osfhandle(descriptor)
    if not _get_basic_info(handle, 0, ctypes.byref(information), ctypes.sizeof(information)):
        raise ctypes.WinError(ctypes.get_last_error())
    return information.ChangeTime


def snapshot(root):
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError('source root must be a directory')
    files = []
    def scan_error(error):
        raise error

    for directory, dirs, names in os.walk(root, followlinks=False, onerror=scan_error):
        dirs[:] = sorted(name for name in dirs if name != '.git')
        for name in dirs:
            entry = Path(directory) / name
            if entry.is_symlink() or entry.is_junction():
                raise ValueError('source directory symlinks and other directory links are not supported')
        if Path(directory) == root:
            dirs[:] = [name for name in dirs if name != 'target']
        for name in sorted(names):
            if name == '.git':
                continue
            path = Path(directory) / name
            before = path.lstat()
            if not stat.S_ISREG(before.st_mode):
                raise ValueError(f'source input is not a regular file: {path.relative_to(root)}')
            digest = hashlib.sha256()
            with path.open('rb') as stream:
                opened = os.fstat(stream.fileno())
                if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
                    raise ValueError('source input changed while opening')
                change_time = _windows_change_time(stream.fileno())
                for chunk in iter(lambda: stream.read(1 << 20), b''):
                    digest.update(chunk)
                if _windows_change_time(stream.fileno()) != change_time:
                    raise ValueError(f'source input changed while hashing: {path.relative_to(root)}')
            after = path.lstat()
            identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
            if identity(before) != identity(after):
                raise ValueError(f'source input changed while hashing: {path.relative_to(root)}')
            files.append({'path': path.relative_to(root).as_posix(), 'bytes': before.st_size,
                          'executable': bool(before.st_mode & 0o111), 'sha256': digest.hexdigest()})
    files.sort(key=lambda row: row['path'])
    encoded = json.dumps(files, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    return {'schema': 'pump-source-inputs-v1', 'sha256': hashlib.sha256(encoded).hexdigest(), 'files': files}


def assert_unchanged(root, expected):
    actual = snapshot(root)
    if actual != expected:
        before = {row['path']: row for row in expected['files']}
        after = {row['path']: row for row in actual['files']}
        changed = sorted(path for path in before.keys() | after.keys() if before.get(path) != after.get(path))
        raise ValueError('source inputs changed during staging: ' + ', '.join(changed[:10]))
