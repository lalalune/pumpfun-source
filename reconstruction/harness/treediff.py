import difflib
import json
import os
import stat
from pathlib import Path


class SourceBytes(bytes):
    def __new__(cls, data, executable):
        value = super().__new__(cls, data)
        value.executable = executable
        return value


def reject_source_link(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    reparse = getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0)
    if stat.S_ISLNK(info.st_mode) or reparse:
        raise ValueError(f'unsupported source tree link: {path}')


def tree_files(root):
    root = Path(root)
    reject_source_link(root)
    if not root.exists():
        raise FileNotFoundError(f'source tree does not exist: {root}')
    if not root.is_dir():
        raise NotADirectoryError(f'source tree is not a directory: {root}')
    files = {}
    def scan_error(error):
        raise error

    # Fail on inaccessible/disappearing directories instead of certifying an
    # incomplete tree. Inspect links before walk can descend into them.
    for directory, directories, names in os.walk(root, followlinks=False, onerror=scan_error):
        for name in sorted(directories + names):
            path = Path(directory) / name
            reject_source_link(path)
            if path.is_file():
                files[path.relative_to(root).as_posix()] = SourceBytes(
                    path.read_bytes(), bool(path.stat().st_mode & 0o111))
    return dict(sorted(files.items()))


def diff_lines(data):
    """Unified diff lines end only at LF; other text separators are source bytes."""
    if data is None:
        return []
    parts = data.decode().split('\n')
    return [part + '\n' for part in parts[:-1]] + ([parts[-1]] if parts[-1] else [])


def quote_path(path):
    """Git C-quoted pathname, with octal escapes for arbitrary UTF-8 bytes."""
    return '"' + ''.join(chr(b) if 32 <= b < 127 and b not in (34, 92)
                         else '\\%03o' % b for b in path.encode('utf-8')) + '"'


def tree_diff(base, new, prefix='programs/pump'):
    """Deterministic unified diff of two crate trees (text files), pure Python."""
    a, b = tree_files(base), tree_files(new)
    out = []
    for rel in sorted(set(a) | set(b)):
        x, y = a.get(rel), b.get(rel)
        old_mode = '100755' if getattr(x, 'executable', False) else '100644'
        new_mode = '100755' if getattr(y, 'executable', False) else '100644'
        if x == y and old_mode == new_mode:
            continue
        quoted_a = quote_path(f'a/{prefix}/{rel}')
        quoted_b = quote_path(f'b/{prefix}/{rel}')
        out.append(f'diff --git {quoted_a} {quoted_b}\n')
        if x is None:
            out.append(f'new file mode {new_mode}\n')
        elif y is None:
            out.append(f'deleted file mode {old_mode}\n')
        elif old_mode != new_mode:
            out.append(f'old mode {old_mode}\nnew mode {new_mode}\n')
        if x is not None and y is not None and x == y:
            continue
        if (x is None and y == b'') or (x == b'' and y is None):
            # Unified text hunks cannot represent an empty file's existence.
            if x is None:
                out.append('index 0000000..e69de29\n')
            else:
                out.append('index e69de29..0000000\n')
            continue
        xl = None
        try:
            xl = diff_lines(x)
            yl = diff_lines(y)
        except UnicodeDecodeError:
            # Either side can fail after the other has already decoded.
            xl = None
        fa = quoted_a if x is not None else '/dev/null'
        fb = quoted_b if y is not None else '/dev/null'
        if xl is None:
            out.append(f'Binary files {fa} and {fb} differ\n')
            continue
        for line in difflib.unified_diff(xl, yl, fa, fb, n=3):
            out.append(line if line.endswith('\n') else line + '\n\\ No newline at end of file\n')
    return ''.join(out)
