import difflib
import json
import os
import stat
from pathlib import Path


def reject_source_link(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return  # Keep the existing missing-root diagnostic below.
    reparse = getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0)
    if stat.S_ISLNK(info.st_mode) or reparse:
        raise ValueError(f'unsupported source tree link: {path}')


def tree_inventory(root):
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
            info = path.lstat()
            if stat.S_ISREG(info.st_mode):
                files[path.relative_to(root).as_posix()] = (path.read_bytes(),
                    '100755' if info.st_mode & 0o111 else '100644')
            elif not stat.S_ISDIR(info.st_mode):
                raise ValueError(f'unsupported special source file: {path}')
    return dict(sorted(files.items()))


def tree_files(root):
    return {name: value[0] for name, value in tree_inventory(root).items()}


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
    a, b = tree_inventory(base), tree_inventory(new)
    out = []
    for rel in sorted(set(a) | set(b)):
        left, right = a.get(rel), b.get(rel)
        x, xm = left if left is not None else (None, None)
        y, ym = right if right is not None else (None, None)
        if left == right:
            continue
        quoted_a = quote_path(f'a/{prefix}/{rel}')
        quoted_b = quote_path(f'b/{prefix}/{rel}')
        out.append(f'diff --git {quoted_a} {quoted_b}\n')
        if x is None:
            out.append(f'new file mode {ym}\n')
        elif y is None:
            out.append(f'deleted file mode {xm}\n')
        elif xm != ym:
            out.extend([f'old mode {xm}\n', f'new mode {ym}\n'])
        if x == y:
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
