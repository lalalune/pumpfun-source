import difflib
import json
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
        quoted_a = json.dumps(f'a/{prefix}/{rel}', ensure_ascii=False)
        quoted_b = json.dumps(f'b/{prefix}/{rel}', ensure_ascii=False)
        out.append(f'diff --git {quoted_a} {quoted_b}\n')
        if (x is None and y == b'') or (x == b'' and y is None):
            # Unified text hunks cannot represent an empty file's existence.
            if x is None:
                out.append('new file mode 100644\nindex 0000000..e69de29\n')
            else:
                out.append('deleted file mode 100644\nindex e69de29..0000000\n')
            continue
        xl = x.decode().splitlines(keepends=True) if x is not None else []
        yl = y.decode().splitlines(keepends=True) if y is not None else []
        fa = f'a/{prefix}/{rel}' if x is not None else '/dev/null'
        fb = f'b/{prefix}/{rel}' if y is not None else '/dev/null'
        for line in difflib.unified_diff(xl, yl, fa, fb, n=3):
            out.append(line if line.endswith('\n') else line + '\n\\ No newline at end of file\n')
    return ''.join(out)
