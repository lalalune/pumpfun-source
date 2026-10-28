#!/usr/bin/env python3
"""import_round.py roundNN : copy a published Codex main-Pump round (primary source, ELFs, CHECKPOINT, inventory) from origin/main into base/roundNN via git show."""
import gzip, json, subprocess, sys
from pathlib import Path
SC = Path(__file__).resolve().parent.parent
REPO = '/Users/shawwalters/Documents/Codex/2026-10-24/pumpfun-source'
rnd = sys.argv[1]; pkg = f'repro/pump/main-contract-{rnd}-20261027'
git = lambda *a: subprocess.run(['git', '-C', REPO, *a], capture_output=True, check=True).stdout
dst = SC / 'base' / rnd
for f in git('ls-tree', '-r', '--name-only', 'origin/main', pkg + '/primary').decode().split():
    out = dst / 'pump' / f[len(pkg + '/primary/'):]
    out.parent.mkdir(parents=True, exist_ok=True); out.write_bytes(git('show', f'origin/main:{f}'))
for f, n in [('unstripped.so', 'codex-unstripped.so'), ('candidate.so', 'codex-candidate.so'), ('CHECKPOINT.json', 'CHECKPOINT.json')]:
    (dst / n).write_bytes(git('show', f'origin/main:{pkg}/{f}'))
(dst / 'codex-inventory.json').write_bytes(gzip.decompress(git('show', f'origin/main:{pkg}/inventory.json.gz')))
cp = json.loads((dst / 'CHECKPOINT.json').read_text())
print('imported', rnd, sum(1 for _ in (dst / 'pump').rglob('*') if _.is_file()), 'files', {k: cp.get(k) for k in ['normalized_windows', 'raw_windows']})
