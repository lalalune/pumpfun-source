#!/usr/bin/env python3
"""apply_l06_patches.py <genuine crate dir> <delivery> [...]
Round-4 lanes deliver line-neutral patches against W/base/L06/pump (= integ-layout-r37-06, a PADDED tree). For the genuine
stage only their code changes are wanted: for every file the patch touches, the patched L06 file and the L06 file are both
pad-stripped (coordfiles `// layout-pad(N): ...` blocks and coordlib `// layout-pad: ...` blocks, marker + its blank lines)
and the resulting code-only change is merged into the genuine file with `git merge-file` (base = stripped L06,
ours = genuine, theirs = stripped patched). New files are added pad-stripped. Any conflict aborts with a report."""
import re, subprocess, sys, tempfile
from pathlib import Path
W = Path('/Users/shawwalters/Documents/Codex/2026-10-24/claude-pump-work')
L06 = W / 'base/L06/pump'
CF = re.compile(r'^\s*// layout-pad\((\d+)\): aligns the next Source site with the original line\s*$')
CL = re.compile(r'^\s*// layout-pad: aligns the next Source site with the original lib\.rs line\s*$')

def strip(text):
    lines = text.split('\n'); out = []; k = 0
    while k < len(lines):
        m = CF.match(lines[k])
        if m:
            n = int(m.group(1)); k += 1; j = 1
            while j < n and k < len(lines) and lines[k].strip() == '':
                k += 1; j += 1
            continue
        if CL.match(lines[k]):
            k += 1
            while k < len(lines) and lines[k].strip() == '':
                k += 1
            continue
        out.append(lines[k]); k += 1
    return '\n'.join(out)

def files_in(patch):
    res = []
    for m in re.finditer(r'^\+\+\+ (\S+)', patch, re.M):
        p = m.group(1)
        rel = p[2:] if p.startswith('b/') else re.split(r'/src/(?=(?:src|idls|recovered|Cargo)\b)', p, maxsplit=1)[-1]
        res.append(rel)
    return res

crate = Path(sys.argv[1]).resolve()
for name in sys.argv[2:]:
    patch = (W / 'deliveries' / name / 'patch.diff').read_text()
    tmp = Path(tempfile.mkdtemp())
    rels = files_in(patch)
    for rel in rels:
        (tmp / 'l06' / rel).parent.mkdir(parents=True, exist_ok=True)
        src = L06 / rel
        (tmp / 'l06' / rel).write_text(src.read_text() if src.exists() else '')
    # apply the lane patch to the L06 copies (headers rewritten to a/<rel> b/<rel>)
    out = []
    for line in patch.split('\n'):
        if line.startswith('diff '):
            continue
        m = re.match(r'^(---|\+\+\+) (\S+)', line)
        if m:
            rel = files_in('+++ ' + m.group(2))[0] if m.group(1) == '+++' else None
            out.append(line if rel is None else f'+++ b/{rel}')
            if m.group(1) == '---':
                out[-1] = '--- a/__PLACEHOLDER__'
            continue
        out.append(line)
    # fix --- headers to match the following +++ header
    for i, l in enumerate(out):
        if l == '--- a/__PLACEHOLDER__':
            nxt = next(x for x in out[i + 1:] if x.startswith('+++ b/'))
            out[i] = '--- a/' + nxt[6:]
    pf = tmp / 'p.diff'; pf.write_text('\n'.join(out) + '\n')
    r = subprocess.run(['patch', '-p1', '--batch', '--forward', '-d', str(tmp / 'l06'), '-i', str(pf)], capture_output=True, text=True)
    assert r.returncode == 0, (name, r.stdout[-2000:])
    for rel in rels:
        base_t = strip((L06 / rel).read_text()) if (L06 / rel).exists() else ''
        theirs_t = strip((tmp / 'l06' / rel).read_text())
        g = crate / rel
        ours_t = g.read_text() if g.exists() else ''
        if not (L06 / rel).exists():
            g.parent.mkdir(parents=True, exist_ok=True); g.write_text(theirs_t); print(f'{name}: new file {rel}'); continue
        fb, fo, ft = tmp / 'b', tmp / 'o', tmp / 't'
        fb.write_text(base_t); fo.write_text(ours_t); ft.write_text(theirs_t)
        m = subprocess.run(['git', 'merge-file', '-p', str(fo), str(fb), str(ft)], capture_output=True, text=True)
        if m.returncode != 0:
            print(f'{name}: CONFLICT in {rel} ({m.returncode} hunks)'); sys.exit(1)
        g.write_text(m.stdout)
        print(f'{name}: merged code change into {rel}')
