import difflib
from pathlib import Path


def tree_files(root):
    root = Path(root)
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob('*')) if p.is_file()}


def tree_diff(base, new, prefix='programs/pump'):
    """Deterministic unified diff of two crate trees (text files), pure Python."""
    a, b = tree_files(base), tree_files(new)
    out = []
    for rel in sorted(set(a) | set(b)):
        x, y = a.get(rel), b.get(rel)
        if x == y:
            continue
        xl = x.decode().splitlines(keepends=True) if x is not None else []
        yl = y.decode().splitlines(keepends=True) if y is not None else []
        fa = f'a/{prefix}/{rel}' if x is not None else '/dev/null'
        fb = f'b/{prefix}/{rel}' if y is not None else '/dev/null'
        for line in difflib.unified_diff(xl, yl, fa, fb, n=3):
            out.append(line if line.endswith('\n') else line + '\n\\ No newline at end of file\n')
    return ''.join(out)
