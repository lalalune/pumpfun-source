"""Integrity check for the fees100 run archive (manifest, no symlinks/special files). Stdlib only."""
from pathlib import Path
import hashlib, json, sys
if not __debug__:
    raise RuntimeError('do not run under python -O')
HERE = Path(__file__).resolve().parent
sha = lambda b: hashlib.sha256(b).hexdigest()
paths = list(HERE.rglob('*'))
assert not any(p.is_symlink() for p in paths), 'symlink in packet'
assert all(p.is_dir() or p.is_file() for p in paths), 'special file in packet'
actual = {p.relative_to(HERE).as_posix(): sha(p.read_bytes()) for p in paths if p.is_file() and p.relative_to(HERE).as_posix() != 'manifest.json'}
assert actual == json.loads((HERE / 'manifest.json').read_text()), 'manifest mismatch'
print(json.dumps({'files': len(actual), 'verified': True}))
