import difflib
from pathlib import Path


def tree_files(root):
    root = Path(root)
    if not root.exists():
        raise FileNotFoundError(f'source tree does not exist: {root}')
    if not root.is_dir():
        raise NotADirectoryError(f'source tree is not a directory: {root}')
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob('*')) if p.is_file()}


def diff_lines(data):
    """Unified diff lines end only at LF; other text separators are source bytes."""
    if data is None:
        return []
    parts = data.decode().split('\n')
    return [part + '\n' for part in parts[:-1]] + ([parts[-1]] if parts[-1] else [])


def tree_diff(base, new, prefix='programs/pump'):
    """Deterministic unified diff of two crate trees (text files), pure Python."""
    a, b = tree_files(base), tree_files(new)
    out = []
    for rel in sorted(set(a) | set(b)):
        x, y = a.get(rel), b.get(rel)
        if x == y:
            continue
        xl = diff_lines(x)
        yl = diff_lines(y)
        fa = f'a/{prefix}/{rel}' if x is not None else '/dev/null'
        fb = f'b/{prefix}/{rel}' if y is not None else '/dev/null'
        for line in difflib.unified_diff(xl, yl, fa, fb, n=3):
            out.append(line if line.endswith('\n') else line + '\n\\ No newline at end of file\n')
    return ''.join(out)
