"""Deterministic source-tree receipts; excludes generated target and Git metadata."""
import hashlib
import json
import os
import stat
from pathlib import Path


def snapshot(root):
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError('source root must be a directory')
    files = []
    for directory, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(name for name in dirs if name not in ('target', '.git'))
        for name in dirs:
            if (Path(directory) / name).is_symlink():
                raise ValueError('source directory symlinks are not supported')
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
                for chunk in iter(lambda: stream.read(1 << 20), b''):
                    digest.update(chunk)
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
