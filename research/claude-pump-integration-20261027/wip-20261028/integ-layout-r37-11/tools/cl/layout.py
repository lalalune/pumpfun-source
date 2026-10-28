#!/usr/bin/env python3
"""layout.py (coordlib lane, round 2) - put lib.rs-origin Anchor/Rust `Source {filename, line}` sites on the
original binary's lines.

Scope: original Source sites whose path is programs/pump/src/lib.rs (72 sites / 45 windows of original.so).
The tool is idempotent and re-runnable on any later crate state (e.g. after other lanes' changes):

  1. build the crate (fastbuild.py) -> unstripped.so
  2. layout.py apply --src <crate> --cand <unstripped.so>     (or `plan` to only print, `sitemap` to write the table)
  3. rebuild + score. A build of the output yields an empty plan (all anchors on target).

How it works
  * Site map: every original lib.rs-site window is paired with our counterpart function, strongest first:
      callgraph  the window is called (same call slot) from a matched parent, or from a parent paired the same way
                 (instruction-level alignment of the parent bodies, ratio >= 0.5)
      closure    `|| error!(..)`-style callees of paired parents, aligned by error-code sequence in call order
      manual     explicit pairs in --pairs JSON (none needed on i1)
    Within a pair, sites are paired by slot order when both bodies are identical up to Source slots ("exact":
    fixing the coordinates matches the window), otherwise by error-code sequence ("pre": body still differs,
    the coordinates are pre-positioned for when the body is recovered).
  * Every paired site whose OUR path is src/lib.rs becomes an anchor (current line -> original line). Matched
    candidate functions with lib.rs sites are pinned. Source-pattern anchors (--patterns) cover items whose Source
    line is not visible in our build (declare_program! lines, sites the decoder cannot see).
  * Anchors are chained (max weight, strictly increasing current and target lines); for each anchor the region
    since the previous anchor is re-padded: existing pad blocks (a `// layout-pad` marker line + blank lines) are
    stripped, then a new pad block is inserted before the anchor's item header / attribute block (or blank and
    plain-comment lines are removed, or token-preserving line joins are made, when the region is too long).
  * Sites whose counterpart is in another file are reported as MOVE requirements (structure recovery, see
    tools/restructure.py); sites without a counterpart are reported as MISSING.

SYNTHETIC: the pad blocks are layout devices (blank lines behind a marker comment), not recovered source text.
"""
import argparse, difflib, hashlib, json, re, subprocess, sys
from collections import defaultdict, Counter
from pathlib import Path

SC = Path('/Users/shawwalters/Documents/Codex/2026-10-24/claude-pump-work')
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE / 'tools'), str(HERE)]
from an import load_orig, load_cand, matches, insn_offsets  # noqa
from cmap import build as build_cp, aligned_calls  # noqa

LIB = 'programs/pump/src/lib.rs'
PREFIX = 'programs/pump/'
PAD = '// layout-pad: aligns the next Source site with the original lib.rs line'
WEIGHT = {'pin': 10000, 'exact': 100, 'pattern': 500, 'pre': 10}  # patterns are explicit decisions: they win over automatic closure pairing
DEFAULT_PATTERNS = HERE / 'patterns.json'


def short(p):
    return p.replace('programs/pump/src/', '')


# ----------------------------------------------------------------------------- pairing
def pair_windows(O, C, M, manual=()):
    """returns {orig_start: (cand_addr, method)} for every original window with a lib.rs site that we can pair."""
    targets = sorted(st for st, w in O.items() if any(s['path'] == LIB for s in w['sites']))
    cp = build_cp(O, C, M)
    res = {}
    for st in targets:
        if st in M:
            continue  # already matched: nothing to do (its candidate sites get pinned)
        if st in cp:
            res[st] = (cp[st][0], 'callgraph ' + cp[st][1])
    byname = defaultdict(list)
    for a, f in C.items():
        byname[f['name']].append(a)
    for m in manual:
        st = int(m['orig'], 0)
        cands = sorted(byname.get(m['cand'], []), key=lambda a: [(s['path'], s['line'] or 0) for s in C[a]['sites']])
        if m.get('index', 0) < len(cands):
            res[st] = (cands[m.get('index', 0)], 'manual')
    # closures / site-bearing callees of paired parents, aligned by error-code signature in call order
    parents = {st: a for st, (a, how) in cp.items()}
    parents.update({st: a for st, (a, how) in res.items()})
    for st, ms in M.items():
        if len(ms) == 1:
            parents.setdefault(st, ms[0])
    want = set(targets) - set(res) - set(M)
    for po, pc in sorted(parents.items()):
        oc = [t for off, t in sorted(O[po]['calls']) if t in O and O[t]['sites']]
        cc = [t for off, t in sorted(C[pc]['calls']) if t in C and C[t]['sites']]
        oc = list(dict.fromkeys(oc)); cc = list(dict.fromkeys(cc))
        if not any(t in want for t in oc):
            continue
        # source order (path, first line) rather than call order: the compiler may call same-code closures out of
        # line order (orig buy calls 689 before 684), while both sources list them in statement order
        skey = lambda side: (lambda t: min((s['path'], s['line'] or 0) for s in side[t]['sites']))
        oc.sort(key=skey(O)); cc.sort(key=skey(C))
        sig_o = [tuple(s['code'] for s in O[t]['sites']) for t in oc]
        sig_c = [tuple(s['code'] for s in C[t]['sites']) for t in cc]
        sm = difflib.SequenceMatcher(None, sig_o, sig_c, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag != 'equal':
                continue
            for k in range(i2 - i1):
                t_o, t_c = oc[i1 + k], cc[j1 + k]
                if t_o in want and t_o not in res:
                    res[t_o] = (t_c, f'closure via {po:#x}')
    # unique same-shape candidate (identical up to Source slots), e.g. helpers whose callers are unpaired
    byshape = defaultdict(list)
    for a, f in C.items():
        if f['sites']:
            byshape[(f['bytes'], f['shape'])].append(a)
    used = {a for a, how in res.values()} | {a for ms in M.values() for a in ms}
    for st in targets:
        if st in res or st in M:
            continue
        cs = [a for a in byshape.get((O[st]['bytes'], O[st]['shape']), []) if a not in used]
        if len(cs) == 1:
            res[st] = (cs[0], 'shape-unique')
    return targets, res


def site_pairs(ow, cf):
    """pairs of (orig site, cand site) and the class ('exact' or 'pre')."""
    if ow['bytes'] == cf['bytes'] and ow['shape'] == cf['shape'] and len(ow['sites']) == len(cf['sites']):
        return list(zip(ow['sites'], cf['sites'])), 'exact'
    # dedupe (line, code) duplicates produced by code duplication, then align by code in line order
    def uniq(sl):
        seen, out = set(), []
        for s in sorted(sl, key=lambda s: (s['line'] or 0, s['slot'])):
            k = (s['path'], s['line'], s['code'])
            if k not in seen:
                seen.add(k); out.append(s)
        return out
    os_, cs_ = uniq(ow['sites']), uniq(cf['sites'])
    sm = difflib.SequenceMatcher(None, [s['code'] for s in os_], [s['code'] for s in cs_], autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            out += [(os_[i1 + k], cs_[j1 + k]) for k in range(i2 - i1)]
    return out, 'pre'


def enclosing_item(src_root, path, line):
    """nearest preceding item header in our source (for the site map)."""
    f = src_root / path[len(PREFIX):] if path.startswith(PREFIX) else None
    if not f or not f.exists() or not line:
        return None
    lines = f.read_text().split('\n')
    pat = re.compile(r'^\s*(?:#\[[^\]]*\]\s*)*(?:pub(?:\([^)]*\))?\s+)?(?:fn\s+(\w+)|struct\s+(\w+)|enum\s+(\w+)|impl\b[^{]*|mod\s+(\w+)|#\[(program|account|derive\(Accounts\))\])')
    for k in range(min(line, len(lines)) - 1, -1, -1):
        m = pat.match(lines[k])
        if m:
            return f'{short(path)}:{k + 1} ' + lines[k].strip()[:90]
    return None


def build_sitemap(O, C, M, src_root, manual=()):
    targets, pairs = pair_windows(O, C, M, manual)
    rows = []
    for st in targets:
        ow = O[st]
        lib_sites = [s for s in ow['sites'] if s['path'] == LIB]
        if st in M:
            for s in lib_sites:
                rows.append({'orig_window': hex(st), 'orig_bytes': ow['bytes'], 'orig_line': s['line'], 'code': s['code'],
                             'status': 'matched', 'ours': None, 'pair_method': 'normalized match'})
            continue
        if st not in pairs:
            for s in lib_sites:
                rows.append({'orig_window': hex(st), 'orig_bytes': ow['bytes'], 'orig_line': s['line'], 'code': s['code'],
                             'status': 'missing', 'ours': None, 'pair_method': None})
            continue
        a, how = pairs[st]
        cf = C[a]
        sp, cls = site_pairs(ow, cf)
        paired = {id(o): c for o, c in sp}
        for s in lib_sites:
            c = paired.get(id(s))
            ours = None
            if c is not None:
                ours = {'symbol': cf['name'], 'addr': hex(a), 'bytes': cf['bytes'], 'path': c['path'], 'line': c['line'],
                        'code': c['code'], 'item': enclosing_item(src_root, c['path'], c['line'])}
            status = ('exact' if cls == 'exact' else 'pre') if c is not None else 'unpaired-site'
            if c is not None and c['path'] != LIB:
                status += '+MOVE'
            rows.append({'orig_window': hex(st), 'orig_bytes': ow['bytes'], 'orig_line': s['line'], 'code': s['code'],
                         'status': status, 'ours': ours, 'pair_method': how,
                         'body': 'identical up to Source slots' if cls == 'exact' else f"differs ({cf['bytes']} B vs {ow['bytes']} B)"})
    rows.sort(key=lambda r: (r['orig_line'], r['orig_window']))
    return rows


# ----------------------------------------------------------------------------- anchors
def anchors_from(rows, O, C, M, src_text, patterns):
    anchors = []   # (cur_line, target, weight, label)
    for r in rows:
        o = r['ours']
        if not o or o['path'] != LIB or not o['line']:
            continue
        cls = 'exact' if r['status'].startswith('exact') else 'pre'
        anchors.append((o['line'], r['orig_line'], WEIGHT[cls], f"{cls}:{r['orig_window']}"))
    # pins: matched candidate functions keep their lib.rs sites
    for st, ms in M.items():
        for a in ms:
            for s in C[a]['sites']:
                if s['path'] == LIB and s['line']:
                    anchors.append((s['line'], s['line'], WEIGHT['pin'], f'pin:{st:#x}'))
    lines = src_text.split('\n')
    notes = []
    for p in patterns:
        rx = re.compile(p['pattern'])
        hits = [k + 1 for k, l in enumerate(lines) if rx.search(l)]
        if len(hits) == 1:
            anchors.append((hits[0], p['target'], WEIGHT['pattern'], 'pattern:' + p.get('label', p['pattern'][:30])))
        else:
            notes.append(f"pattern {p.get('label', p['pattern'])!r}: {len(hits)} hits, skipped")
    return anchors, notes


def chain(anchors):
    byc = defaultdict(list)
    for c, t, w, lab in anchors:
        byc[c].append((w, t, lab))
    pts, dropped = [], []
    for c, lst in byc.items():
        tw = defaultdict(int); labs = defaultdict(list)
        for w, t, lab in lst:
            tw[t] += w; labs[t].append(lab)
        best = max(tw, key=lambda t: tw[t])
        pts.append((c, best, tw[best], labs[best]))
        for t in tw:
            if t != best:
                dropped.append((c, t, labs[t], 'same-line conflict'))
    pts.sort()
    n = len(pts)
    if not n:
        return [], dropped
    best = [p[2] for p in pts]; prev = [-1] * n
    for i in range(n):
        for j in range(i):
            if pts[j][1] < pts[i][1] and best[j] + pts[i][2] > best[i]:
                best[i] = best[j] + pts[i][2]; prev[i] = j
    i = max(range(n), key=lambda k: best[k])
    keep = set()
    while i >= 0:
        keep.add(i); i = prev[i]
    for k, p in enumerate(pts):
        if k not in keep:
            dropped.append((p[0], p[1], p[3], 'order inversion'))
    return [pts[k] for k in sorted(keep)], dropped


# ----------------------------------------------------------------------------- source side
def lex_lines(text):
    """per line: (starts inside a string literal / block comment, ends with a line comment)."""
    res_start, res_tail = [], []
    i, n = 0, len(text)
    state = 'code'; depth = 0; raw_hashes = 0; cur_tail = False
    res_start.append(False)
    while i < n:
        ch = text[i]
        if ch == '\n':
            res_tail.append(cur_tail); cur_tail = False
            if state == 'linecomment':
                state = 'code'
            res_start.append(state != 'code')
            i += 1; continue
        if state == 'code':
            if text.startswith('//', i):
                state = 'linecomment'; cur_tail = True; i += 2; continue
            if text.startswith('/*', i):
                state = 'block'; depth = 1; i += 2; continue
            m = re.match(r'b?r(#*)"', text[i:i + 70])
            if m and (i == 0 or not (text[i - 1].isalnum() or text[i - 1] == '_')):
                state = 'raw'; raw_hashes = len(m.group(1)); i += len(m.group(0)); continue
            if ch == '"' or (ch == 'b' and text.startswith('b"', i) and (i == 0 or not (text[i - 1].isalnum() or text[i - 1] == '_'))):
                state = 'str'; i += 2 if ch == 'b' else 1; continue
            if ch == "'":
                m = re.match(r"'(\\(x[0-9a-fA-F]{2}|u\{[0-9a-fA-F]+\}|.)|[^\\'\n])'", text[i:i + 14])
                i += len(m.group(0)) if m else 1
                continue
            i += 1; continue
        if state == 'linecomment':
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
    res_tail.append(cur_tail)
    return list(zip(res_start, res_tail))


def is_blank(l):
    return l.strip() == ''


def is_plain_comment(l):
    s = l.strip()
    return s.startswith('//') and not s.startswith('///') and not s.startswith('//!')


def is_pad(l):
    return l.strip() == PAD


HEADER = re.compile(r'^\s*(#!?\[|///|//!|(pub(\([^)]*\))?\s+)?(unsafe\s+|const\s+|async\s+)*(fn|impl|struct|enum|mod|trait)\b.*\{\s*$)')


def strip_pads(seg, seglex):
    out, outlex = [], []
    k = 0
    while k < len(seg):
        if is_pad(seg[k]) and not seglex[k][0]:
            k += 1
            while k < len(seg) and is_blank(seg[k]) and not seglex[k][0]:
                k += 1
            continue
        out.append(seg[k]); outlex.append(seglex[k]); k += 1
    return out, outlex


def solve(text, pts):
    lines = text.split('\n')
    lex = lex_lines(text)
    out, rows = [], []
    prev_c, prev_t = 0, 0
    for c, t, w, labs in pts:
        if c > len(lines):
            rows.append((c, t, 'FAIL beyond EOF', labs)); continue
        seg = [lines[ln - 1] for ln in range(prev_c + 1, c)]
        seglex = [lex[ln - 1] for ln in range(prev_c + 1, c)]
        seg, seglex = strip_pads(seg, seglex)
        anchor_line, anchor_lex = lines[c - 1], lex[c - 1]
        need, have = t - prev_t - 1, len(seg)
        status = 'ok'
        if need < 0:
            status = 'FAIL target before previous anchor'
        elif need > have:
            add = need - have
            ins = len(seg)
            # move up past the anchor's header/attribute/doc lines (stay inside this region)
            while ins > 0 and HEADER.match(seg[ins - 1]) and not seglex[ins - 1][0]:
                ins -= 1
            def unsafe(ix):
                return seglex[ix][0] if ix < len(seg) else anchor_lex[0]
            while ins > 0 and unsafe(ins):
                ins -= 1
            if unsafe(ins):
                status = 'FAIL no safe insertion point'
            else:
                seg[ins:ins] = [PAD] + [''] * (add - 1)
                seglex[ins:ins] = [(False, True)] + [(False, False)] * (add - 1)
                status = f'+{add}'
        elif need < have:
            rm = have - need; removed = 0
            for pred in (is_blank, is_plain_comment):
                ix = len(seg) - 1
                while ix >= 0 and removed < rm:
                    nxt_unsafe = seglex[ix + 1][0] if ix + 1 < len(seg) else anchor_lex[0]
                    if pred(seg[ix]) and not seglex[ix][0] and not nxt_unsafe:
                        del seg[ix]; del seglex[ix]; removed += 1
                    ix -= 1
            ix = len(seg) - 1
            while removed < rm and ix >= 0:   # token-preserving joins
                nxt = seg[ix + 1] if ix + 1 < len(seg) else anchor_line
                nlex = seglex[ix + 1] if ix + 1 < len(seg) else anchor_lex
                if not seglex[ix][1] and not nlex[0] and not is_blank(seg[ix]) and not re.match(r'\s*(///|//!)', nxt) \
                        and not seglex[ix][0]:
                    joined = seg[ix].rstrip() + ' ' + nxt.lstrip()
                    if ix + 1 < len(seg):
                        seg[ix] = joined; seglex[ix] = (seglex[ix][0], nlex[1]); del seg[ix + 1]; del seglex[ix + 1]
                    else:
                        anchor_line = joined; anchor_lex = (seglex[ix][0], anchor_lex[1]); del seg[ix]; del seglex[ix]
                    removed += 1
                ix -= 1
            status = f'-{removed}' if removed == rm else f'FAIL could only remove {removed}/{rm}'
        if status.startswith('FAIL'):
            seg = [lines[ln - 1] for ln in range(prev_c + 1, c)]
            anchor_line = lines[c - 1]
        rows.append((c, t, status, labs))
        out += seg + [anchor_line]
        prev_c, prev_t = c, prev_t + len(seg) + 1
    tail = lines[prev_c:]
    tail, _ = strip_pads(tail, lex[prev_c:])
    out += tail
    return '\n'.join(out), rows


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['sitemap', 'plan', 'apply'])
    ap.add_argument('--src', type=Path, required=True, help='crate dir (Cargo.toml, src/)')
    ap.add_argument('--cand', type=Path, required=True, help='unstripped.so built from --src as it is now')
    ap.add_argument('--pairs', type=Path, help='manual pairs JSON {"pairs":[{"orig","cand","index"}]}')
    ap.add_argument('--patterns', type=Path, default=DEFAULT_PATTERNS)
    ap.add_argument('--classes', default='pin,exact,pattern,pre')
    ap.add_argument('--json', type=Path, help='write the site map / plan JSON here')
    a = ap.parse_args()
    O = load_orig(); C = load_cand(a.cand); M = matches(O, C)
    manual = json.loads(a.pairs.read_text())['pairs'] if a.pairs and a.pairs.exists() else []
    rows = build_sitemap(O, C, M, a.src, manual)
    sha = hashlib.sha256(a.cand.read_bytes()).hexdigest()
    if a.cmd == 'sitemap':
        doc = {'description': 'Original Source sites in programs/pump/src/lib.rs -> our counterpart (coordlib lane)',
               'cand_unstripped_sha256': sha, 'sites': rows}
        if a.json:
            a.json.write_text(json.dumps(doc, indent=1))
        cnt = Counter(r['status'] for r in rows)
        print(f'{len(rows)} sites: {dict(cnt)}')
        for r in rows:
            o = r['ours']
            print(f"  {r['orig_line']:5d} {r['code']} {r['orig_window']:>9} {r['status']:14s} "
                  + (f"{short(o['path'])}:{o['line']}  {o['symbol'][:70]}" if o else '-'))
        return
    src_file = a.src / 'src/lib.rs'
    text = src_file.read_text()
    patterns = json.loads(a.patterns.read_text()) if a.patterns and a.patterns.exists() else []
    classes = set(a.classes.split(','))
    anchors, notes = anchors_from(rows, O, C, M, text, patterns)
    anchors = [x for x in anchors if x[3].split(':')[0] in classes]
    pts, dropped = chain(anchors)
    new, res = solve(text, pts)
    off = [r for r in res if r[0] != r[1]]
    print(f"anchors: {len(pts)} kept ({len(off)} off target), {len(dropped)} dropped; "
          f"site rows: {dict(Counter(r['status'] for r in rows))}")
    for c, t, st, labs in res:
        if c != t or st != 'ok':
            print(f"  {c:5d} -> {t:5d} {st:10s} {', '.join(labs)[:100]}")
    for d in dropped:
        print(f"  dropped {d[0]}->{d[1]} {d[2]} ({d[3]})")
    for n in notes:
        print('  note:', n)
    for r in rows:
        if r['status'].endswith('MOVE'):
            print(f"  MOVE {r['orig_window']} orig lib.rs:{r['orig_line']} <- ours {short(r['ours']['path'])}:{r['ours']['line']}")
        elif r['status'] in ('missing', 'unpaired-site'):
            print(f"  MISSING {r['orig_window']} orig lib.rs:{r['orig_line']} code {r['code']} ({r['status']})")
    if a.json:
        a.json.write_text(json.dumps({'cand_unstripped_sha256': sha, 'anchors': [list(p[:3]) + [p[3]] for p in pts],
                                      'result': [list(r) for r in res], 'dropped': dropped, 'notes': notes}, indent=1))
    if a.cmd == 'apply' and new != text:
        src_file.write_text(new)
        print(f'wrote {src_file} ({len(text.splitlines())} -> {len(new.splitlines())} lines)')


if __name__ == '__main__':
    main()
