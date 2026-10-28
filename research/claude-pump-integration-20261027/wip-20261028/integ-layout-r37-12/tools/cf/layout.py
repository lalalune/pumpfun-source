#!/usr/bin/env python3
"""layout.py - position Anchor/Rust `Source {filename, line}` sites on the original binary's lines.

coordfiles lane (round 2).  Idempotent and re-runnable after other lanes' changes:

    layout.py apply --src <crate dir> --sitemap <sitemap.json> [--out <crate dir>] [--files a.rs,b.rs]
    layout.py plan  --src <crate dir> --sitemap <sitemap.json>
    layout.py strip --src <crate dir> [--out <crate dir>]     # remove every layout pad (undo)

Input sitemap (see mksitemap.py, which derives it from a candidate build + window pairing):
    {"anchors": [{"file": "buy_v2.rs",              # path relative to <crate>/src
                  "pattern": "^#\\[derive\\(Accounts\\)\\]$",   # regex on the stripped line text
                  "context": "pub struct BuyV2\\b",   # optional regex that must match within +-3 lines
                  "nth": 0,                           # occurrence among lines matching pattern(+context)
                  "target": 129,                      # original Source line
                  "weight": 100, "label": "gain:0xa9eb8"}, ...]}

Mechanics (synthetic layout, honestly labelled): before the anchor's item header (attributes / doc
comments directly above it) a pad block is inserted:
    // layout-pad(N): aligns the next Source site with the original line
followed by N-1 blank lines.  Existing pad blocks are stripped first, so applying twice is a no-op.
When an anchor must move UP, blank lines (outside literals) between it and the previous anchor are
removed (nearest first).  Anchors that would invert order are dropped by a max-weight chain and
reported; nothing else in the file changes.
"""
import argparse, json, re, shutil, sys
from collections import defaultdict
from pathlib import Path

PAD_RE = re.compile(r'^\s*// layout-pad\((\d+)\): aligns the next Source site with the original line\s*$')


def pad_block(n):
    return [f'// layout-pad({n}): aligns the next Source site with the original line'] + [''] * (n - 1)


# ----------------------------------------------------------------------------- lexing
def starts_inside(text):
    """per line: True if the line starts inside a string literal or block comment."""
    res = [False]
    i, n = 0, len(text)
    state = 'code'; depth = 0; raw_hashes = 0
    while i < n:
        ch = text[i]
        if ch == '\n':
            if state == 'line':
                state = 'code'
            res.append(state != 'code')
            i += 1; continue
        if state == 'code':
            if text.startswith('//', i):
                state = 'line'; i += 2; continue
            if text.startswith('/*', i):
                state = 'block'; depth = 1; i += 2; continue
            m = re.match(r'b?r(#*)"', text[i:i + 70])
            if m and (i == 0 or not (text[i - 1].isalnum() or text[i - 1] == '_')):
                state = 'raw'; raw_hashes = len(m.group(1)); i += len(m.group(0)); continue
            if ch == '"':
                state = 'str'; i += 1; continue
            if ch == "'":
                m = re.match(r"'(\\(x[0-9a-fA-F]{2}|u\{[0-9a-fA-F]+\}|.)|[^\\'\n])'", text[i:i + 14])
                i += len(m.group(0)) if m else 1
                continue
            i += 1; continue
        if state == 'line':
            i += 1; continue
        if state == 'block':
            if text.startswith('/*', i):
                depth += 1; i += 2; continue
            if text.startswith('*/', i):
                depth -= 1; i += 2
                if depth == 0:
                    state = 'code'
                continue
            i += 1; continue
        if state == 'str':
            if ch == '\\':
                i += 2; continue
            if ch == '"':
                state = 'code'
            i += 1; continue
        if state == 'raw':
            if ch == '"' and text[i + 1:i + 1 + raw_hashes] == '#' * raw_hashes:
                state = 'code'; i += 1 + raw_hashes; continue
            i += 1; continue
    return res


def strip_pads(lines):
    out = []
    k = 0
    while k < len(lines):
        m = PAD_RE.match(lines[k])
        if m:
            n = int(m.group(1)); k += 1; j = 1
            while j < n and k < len(lines) and lines[k].strip() == '':
                k += 1; j += 1
            continue
        out.append(lines[k]); k += 1
    return out


# ----------------------------------------------------------------------------- locating
def locate(lines, a):
    pat = re.compile(a['pattern'])
    ctx = re.compile(a['context']) if a.get('context') else None
    hits = []
    for i, l in enumerate(lines):
        if pat.search(l.strip()):
            if ctx and not any(ctx.search(lines[j].strip()) for j in range(max(0, i - 3), min(len(lines), i + 4))):
                continue
            hits.append(i + 1)
    nth = a.get('nth', 0)
    return hits[nth] if nth < len(hits) else None


def chain(pts):
    """pts: [(cur, target, weight, label)] -> (kept sorted by cur, dropped)."""
    byc = defaultdict(list)
    for c, t, w, lab in pts:
        byc[c].append((t, w, lab))
    merged, dropped = [], []
    for c, lst in byc.items():
        tw = defaultdict(int); labs = defaultdict(list)
        for t, w, lab in lst:
            tw[t] += w; labs[t].append(lab)
        best = max(tw, key=lambda t: tw[t])
        merged.append((c, best, tw[best], labs[best]))
        for t in tw:
            if t != best:
                dropped.append((c, t, labs[t], 'same current line, different target'))
    merged.sort()
    n = len(merged)
    if not n:
        return [], dropped
    best = [m[2] for m in merged]; prev = [-1] * n
    for i in range(n):
        for j in range(i):
            if merged[j][1] < merged[i][1] and best[j] + merged[i][2] > best[i]:
                best[i] = best[j] + merged[i][2]; prev[i] = j
    i = max(range(n), key=lambda k: best[k])
    keep = set()
    while i >= 0:
        keep.add(i); i = prev[i]
    for k, m in enumerate(merged):
        if k not in keep:
            dropped.append((m[0], m[1], m[3], 'order inversion'))
    return [merged[k] for k in sorted(keep)], dropped


HEADER = re.compile(r'^\s*(#\[|#!\[|///|//!)')


def solve(lines, pts):
    """lines: pad-stripped file lines; pts: chain-ordered [(cur, target, w, labels)].
    returns (new_lines, rows)."""
    inside = starts_inside('\n'.join(lines))
    out, rows = [], []
    prev_c, prev_t = 0, 0
    for c, t, w, labs in pts:
        seg = list(range(prev_c + 1, c))           # 1-based lines strictly between anchors
        have = len(seg); need = t - prev_t - 1
        seg_lines = [lines[i - 1] for i in seg]
        seg_inside = [inside[i - 1] for i in seg]
        anchor_line = lines[c - 1]
        status = 'ok'
        if need < 0:
            status = 'FAIL target not after previous anchor'
        elif need > have:
            add = need - have
            ins = len(seg_lines)
            # go up to the start of the statement / item that contains the anchor: cross lines that
            # do not terminate a statement (continuations, `if .. {` / fn signatures, attributes,
            # doc and plain comments); stop below a line ending in `;` / `}` / `,`, a blank line,
            # or the previous anchor.
            while ins > 0 and not seg_inside[ins - 1]:
                above = seg_lines[ins - 1].strip()
                if above == '' or re.search(r'[;},]\s*(//.*)?$', above) and not HEADER.match(seg_lines[ins - 1]):
                    break
                ins -= 1
            # never start a pad inside a literal / block comment
            unsafe = lambda ix: seg_inside[ix] if ix < len(seg_lines) else inside[c - 1]
            while ins > 0 and unsafe(ins):
                ins -= 1
            if unsafe(ins):
                status = 'FAIL no safe insertion point'
            else:
                seg_lines[ins:ins] = pad_block(add)
                seg_inside[ins:ins] = [False] * add
                status = f'+{add}'
        elif need < have:
            rm = have - need; removed = 0
            ix = len(seg_lines) - 1
            while ix >= 0 and removed < rm:
                nxt_inside = seg_inside[ix + 1] if ix + 1 < len(seg_lines) else inside[c - 1]
                if seg_lines[ix].strip() == '' and not seg_inside[ix] and not nxt_inside:
                    del seg_lines[ix]; del seg_inside[ix]; removed += 1
                ix -= 1
            # token-preserving joins (last resort): append a line to the one above it.  Never joins a
            # line holding `//` (it would comment out the rest) or a doc comment / literal continuation.
            joined = 0
            # pass 1 joins continuation lines (the upper line does not end a statement), pass 2 any line
            for pass_ in ((1, 2) if w >= 10 else ()):   # pre-positioning anchors (weight < 10) never join lines
                ix = len(seg_lines) - 1
                while removed < rm and ix >= 0:
                    nxt = seg_lines[ix + 1] if ix + 1 < len(seg_lines) else anchor_line
                    nxt_inside = seg_inside[ix + 1] if ix + 1 < len(seg_lines) else inside[c - 1]
                    cur = seg_lines[ix]
                    if (not seg_inside[ix] and not nxt_inside and cur.strip() and '//' not in cur
                            and not re.match(r'\s*(///|//!)', nxt)
                            and (pass_ == 2 or not re.search(r'[;}]\s*$', cur))):
                        merged = cur.rstrip() + ' ' + nxt.lstrip()
                        if ix + 1 < len(seg_lines):
                            seg_lines[ix] = merged
                            del seg_lines[ix + 1]; del seg_inside[ix + 1]
                        else:
                            anchor_line = merged
                            del seg_lines[ix]; del seg_inside[ix]
                        removed += 1; joined += 1
                        ix = min(ix, len(seg_lines) - 1)
                        continue
                    ix -= 1
            status = (f'-{removed}' + (f' ({joined} joins)' if joined else '')) if removed == rm else f'FAIL could only remove {removed}/{rm} lines'
        if status.startswith('FAIL'):
            if w < 10:
                # a pre-positioning anchor that cannot be met is skipped entirely: its line simply joins the
                # next segment, so it can never push a stronger anchor off its target
                rows.append({'line': c, 'target': t, 'now': None, 'action': 'SKIP ' + status, 'labels': labs})
                continue
            seg_lines = [lines[i - 1] for i in seg]
            anchor_line = lines[c - 1]
        out += seg_lines + [anchor_line]
        rows.append({'line': c, 'target': t, 'now': len(out), 'action': status, 'labels': labs})
        prev_c, prev_t = c, len(out)
    out += lines[prev_c:]
    return out, rows


def process(src, anchors, files=None, write_to=None):
    report = {'files': {}, 'missing': [], 'dropped': []}
    byfile = defaultdict(list)
    for a in anchors:
        byfile[a['file']].append(a)
    for rel in sorted(byfile):
        if files and rel not in files:
            continue
        f = src / 'src' / rel
        if not f.exists():
            report['missing'].append({'file': rel, 'why': 'no such file'})
            continue
        text = f.read_text()
        lines = strip_pads(text.split('\n'))
        pts = []
        for a in byfile[rel]:
            c = locate(lines, a)
            if c is None:
                report['missing'].append({'file': rel, 'label': a.get('label'), 'pattern': a['pattern']})
                continue
            pts.append((c, a['target'], a.get('weight', 100), a.get('label', '')))
        kept, dropped = chain(pts)
        for d in dropped:
            report['dropped'].append({'file': rel, 'line': d[0], 'target': d[1], 'labels': d[2], 'why': d[3]})
        new, rows = solve(lines, kept)
        report['files'][rel] = rows
        if write_to is not None:
            dst = write_to / 'src' / rel
            new_text = '\n'.join(new)
            if not dst.exists() or dst.read_text() != new_text:
                dst.write_text(new_text)
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['apply', 'plan', 'strip'])
    ap.add_argument('--src', type=Path, required=True, help='crate dir (Cargo.toml, src/)')
    ap.add_argument('--sitemap', type=Path, action='append', help='site map(s); anchors of several maps are merged')
    ap.add_argument('--out', type=Path, help='write the positioned crate here (default: in place)')
    ap.add_argument('--files', help='comma-separated subset of files (relative to src/)')
    ap.add_argument('--json', type=Path, help='write the report here')
    a = ap.parse_args()
    src = a.src.resolve()
    out = a.out.resolve() if a.out else src
    if a.out and out != src:
        if out.exists():
            shutil.rmtree(out)
        shutil.copytree(src, out, ignore=shutil.ignore_patterns('target'))
    if a.cmd == 'strip':
        for f in sorted((out / 'src').rglob('*.rs')):
            t = f.read_text(); n = '\n'.join(strip_pads(t.split('\n')))
            if n != t:
                f.write_text(n); print('stripped', f.relative_to(out))
        return
    anchors = []
    for smp in a.sitemap or []:
        sm = json.loads(smp.read_text())
        anchors += sm['anchors'] if isinstance(sm, dict) else sm
    files = set(a.files.split(',')) if a.files else None
    report = process(out, anchors, files, write_to=out if a.cmd == 'apply' else None)
    moved = 0
    for rel, rows in report['files'].items():
        off = [r for r in rows if r['action'] not in ('ok',)]
        moved += len(off)
        bad = [r for r in rows if r['now'] is not None and r['now'] != r['target']]
        print(f"{rel}: {len(rows)} anchors, {len(off)} moved, {len(bad)} off-target"
              + (': ' + ', '.join(f"{r['line']}->{r['target']}({r['action']})" for r in off[:8]) + (' ...' if len(off) > 8 else '') if off else ''))
        for r in bad:
            print(f"   OFF {rel}:{r['line']} target {r['target']} now {r['now']} {r['labels']} {r['action']}")
    for m in report['missing']:
        print('   MISSING', m)
    for d in report['dropped']:
        print('   DROPPED', d)
    if a.json:
        a.json.write_text(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
