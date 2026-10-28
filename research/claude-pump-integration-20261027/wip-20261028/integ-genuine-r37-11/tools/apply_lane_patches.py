#!/usr/bin/env python3
"""apply_lane_patches.py <crate dir> <delivery name> [...]
Applies g04-based lane deliveries (patch.diff = diff -ruN W/base/g04/pump <lane src>) to the composite's genuine stage,
after round3.py. Headers are rewritten to a/<rel> b/<rel> (rel = path inside the crate) and applied with
`patch -p1 --forward --batch`; a dry run comes first, and any hunk that does not apply aborts with the reject list
(those deliveries are then ported by hand into round3.py)."""
import re, subprocess, sys, tempfile
from pathlib import Path
W = Path('/Users/shawwalters/Documents/Codex/2026-10-24/claude-pump-work')
crate = Path(sys.argv[1]).resolve()
for name in sys.argv[2:]:
    if name.endswith('.patch') or name.endswith('.diff'):      # a patch file (git-style a/ b/ paths or lane format)
        pf = Path(name) if name.startswith('/') else Path(__file__).resolve().parent / name
        txt = pf.read_text()
    else:
        txt = (W / 'deliveries' / name / 'patch.diff').read_text()
    out = []
    for line in txt.split('\n'):
        if line.startswith('diff '):
            continue
        m = re.match(r'^(---|\+\+\+) (\S+)(.*)$', line)
        if m:
            p = m.group(2)
            if p.startswith(('a/', 'b/')):
                rel = p[2:]
            elif '/pump/' in p and m.group(1) == '---':
                rel = p.split('/pump/', 1)[1]
            else:
                rel = re.split(r'/src/(?=(src|idls|recovered|Cargo)\b)', p, maxsplit=1)
                rel = p[len(rel[0]) + 5:] if len(rel) > 1 else p.split('/src/', 1)[-1]
            out.append(f"{m.group(1)} {'a' if m.group(1) == '---' else 'b'}/{rel}")
        else:
            out.append(line)
    tf = Path(tempfile.mkstemp(suffix='.diff')[1]); tf.write_text('\n'.join(out))
    dry = subprocess.run(['patch', '-p1', '--forward', '--batch', '--dry-run', '-d', str(crate), '-i', str(tf)], capture_output=True, text=True)
    if dry.returncode != 0:
        print(f'{name}: DOES NOT APPLY\n' + dry.stdout[-3000:]); sys.exit(1)
    r = subprocess.run(['patch', '-p1', '--forward', '--batch', '-d', str(crate), '-i', str(tf)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout
    print(f'{Path(name).name}: applied ({sum(1 for l in out if l.startswith("+++ "))} files)')
