#!/usr/bin/env python3
"""mksitemap.py - derive the coordfiles site map (original Source site -> our file:line) from a build.

    mksitemap.py --src <crate dir> --cand <unstripped.so built from it> [--pairs pairs.json]
                 [--out sitemap.json] [--scope nonlib|all]

Pairing of original windows with candidate functions (strongest first):
  pin     window already normalized-matched: its candidate sites keep their current lines
  manual  explicit pair from --pairs (orig window -> candidate symbol [+ index]); sites aligned in
          order ("shape") or by error-code sequence ("bycode", pre-positioning of body-different windows)
  gain    unique same-length same-shape pair (identical up to Source slots)
  file    same-shape group where exactly one candidate lives in the original's file
Every paired site whose candidate file equals the original file becomes a layout anchor with a
text locator (line regex + context + occurrence) so layout.py can re-apply it without a build.
Sites whose counterpart lives in another file are listed under "moves"; original sites with no
counterpart are listed under "unmapped" with the reason.
"""
import argparse, difflib, json, re, sys
from collections import defaultdict, Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'tools'))
from cf import load_orig, load_cand, matched_map, callers, PREFIX  # noqa

WEIGHT = {'pin': 1000, 'manual': 200, 'gain': 100, 'file': 90, 'call': 80, 'pre': 2}


def align_by_code(osites, csites):
    oi = sorted(range(len(osites)), key=lambda i: osites[i]['line'] or 0)
    ci = sorted(range(len(csites)), key=lambda i: csites[i]['line'] or 0)
    sm = difflib.SequenceMatcher(None, [osites[i]['code'] for i in oi], [csites[i]['code'] for i in ci], autojunk=False)
    res = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            for d in range(i2 - i1):
                res.append((osites[oi[i1 + d]], csites[ci[j1 + d]]))
    return res


def pair(O, C, manual):
    M = matched_map(O, C)
    out = []          # (class, orig, cand, [(osite, csite)])
    used_c = set(); done_o = set()
    for st, ms in M.items():
        done_o.add(st)
        if O[st]['sites']:
            for a in ms:
                out.append(('pin', st, a, list(zip(O[st]['sites'], C[a]['sites']))))
                used_c.add(a)
    byname = defaultdict(list)
    for a, f in C.items():
        byname[f['name']].append(a)
    notes = []
    for m in manual:
        st = int(m['orig'], 0)
        if st in done_o and st in M:
            notes.append(f"manual {m['orig']}: already matched"); continue
        w = O[st]
        rx = re.compile(m['cand'])
        cands = [a for nm, lst in byname.items() if rx.fullmatch(nm) for a in lst]
        mode = m.get('mode', 'shape')
        if mode == 'shape':
            cands = [a for a in cands if C[a]['shape'] == w['shape'] and C[a]['bytes'] == w['bytes']]
        if m.get('file'):
            cands = [a for a in cands if any(s['short'] == m['file'] for s in C[a]['sites'])]
        if m.get('line') is not None:
            cands = [a for a in cands if any(s['line'] == m['line'] for s in C[a]['sites'])]
        cands.sort(key=lambda a: [(s['short'], s['line'] or 0) for s in C[a]['sites']])
        idx = m.get('index', 0)
        if idx >= len(cands):
            notes.append(f"manual {m['orig']}: no candidate #{idx} for {m['cand']!r} ({mode}); {len(cands)} found"); continue
        a = cands[idx]
        sp = list(zip(w['sites'], C[a]['sites'])) if mode == 'shape' else align_by_code(w['sites'], C[a]['sites'])
        out.append(('manual' if mode == 'shape' else 'pre', st, a, sp))
        done_o.add(st)
        if mode == 'shape':
            used_c.add(a)
    groups = defaultdict(lambda: ([], []))
    for st, w in O.items():
        if st not in done_o and w['sites']:
            groups[(w['bytes'], w['shape'])][0].append(st)
    for a, f in C.items():
        if a not in used_c and f['sites'] and (f['bytes'], f['shape']) in groups:
            groups[(f['bytes'], f['shape'])][1].append(a)
    for k, (os_, cs_) in groups.items():
        if len(os_) == 1 and len(cs_) == 1:
            st, a = os_[0], cs_[0]
            out.append(('gain', st, a, list(zip(O[st]['sites'], C[a]['sites']))))
            used_c.add(a); done_o.add(st)
        elif os_ and cs_:
            # file rule: an original window whose sites are all in one file pairs with the unique
            # same-shape candidate in that file
            for st in os_:
                fo = {s['short'] for s in O[st]['sites']}
                if len(fo) != 1:
                    continue
                same = [a for a in cs_ if a not in used_c and {s['short'] for s in C[a]['sites']} == fo]
                osame = [x for x in os_ if {s['short'] for s in O[x]['sites']} == fo]
                if len(same) == 1 and len(osame) == 1:
                    a = same[0]
                    out.append(('file', st, a, list(zip(O[st]['sites'], C[a]['sites']))))
                    used_c.add(a); done_o.add(st)
    return out, notes, M


def locator(lines, ln):
    """text locator for 1-based line ln."""
    text = lines[ln - 1].strip()
    pat = '^' + re.escape(text) + '$'
    same = [i + 1 for i, l in enumerate(lines) if l.strip() == text]
    loc = {'pattern': pat}
    if len(same) > 1 or text.startswith('#['):
        # context: the nearest following non-blank, non-attribute line that is unique-ish
        ctx = None
        for j in range(ln, min(len(lines), ln + 400)):
            t = lines[j].strip()
            if t and not t.startswith('#[') and not t.startswith('// layout-pad('):
                ctx = '^' + re.escape(t) + '$'; break
        if ctx:
            loc['context'] = ctx
            rx = re.compile(ctx)
            same = [i for i in same if any(rx.search(lines[j].strip()) for j in range(max(0, i - 4), min(len(lines), i + 3)))]
        loc['nth'] = same.index(ln) if ln in same else 0
    return loc


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--src', type=Path, required=True)
    ap.add_argument('--cand', type=Path, required=True)
    ap.add_argument('--pairs', type=Path, default=HERE / 'pairs.json')
    ap.add_argument('--out', type=Path, default=HERE / 'sitemap.json')
    ap.add_argument('--scope', default='nonlib', choices=['nonlib', 'all'])
    ap.add_argument('--classes', default='pin,manual,gain,file,pre')
    ap.add_argument('--extra', type=Path, default=HERE / 'extra_anchors.json', help='hand-written anchors for moved items')
    a = ap.parse_args()
    classes = set(a.classes.split(','))
    manual = json.loads(a.pairs.read_text())['pairs'] if a.pairs.exists() else []
    O = load_orig(); C = load_cand(a.cand)
    pairs, notes, M = pair(O, C, manual)
    in_scope = (lambda p: p != 'lib.rs') if a.scope == 'nonlib' else (lambda p: True)
    srcdir = a.src / 'src'
    cache = {}

    from layout import PAD_RE

    def lines_of(rel):
        """pad-stripped lines + map from the built (padded) 1-based line to the stripped 1-based line."""
        if rel not in cache:
            f = srcdir / rel
            if not f.exists():
                cache[rel] = (None, None)
            else:
                raw = f.read_text().split('\n'); out = []; m = {}; k = 0
                while k < len(raw):
                    mm = PAD_RE.match(raw[k])
                    if mm:
                        n = int(mm.group(1)); k += 1; j = 1
                        while j < n and k < len(raw) and raw[k].strip() == '':
                            k += 1; j += 1
                        continue
                    out.append(raw[k]); m[k + 1] = len(out); k += 1
                cache[rel] = (out, m)
        return cache[rel]

    anchors, moves, mapped = [], [], {}
    for cls, st, ca, sp in pairs:
        for o, c in sp:
            key = (st, o['len_slot'])
            mapped[key] = {'class': cls, 'cand_fn': hex(ca), 'cand_name': C[ca]['name'],
                           'cand_file': c['short'], 'cand_line': c['line'], 'cand_code': c['code']}
            if cls not in classes or o['line'] is None or c['line'] is None:
                continue
            if not in_scope(o['short']) and not (cls == 'pin' and in_scope(c['short'])):
                continue
            if o['short'] != c['short']:
                if cls != 'pin':
                    moves.append({'class': cls, 'orig': hex(st), 'cand': hex(ca), 'cand_name': C[ca]['name'],
                                  'from': f"{c['short']}:{c['line']}", 'to': f"{o['short']}:{o['line']}"})
                continue
            ls, lmap = lines_of(c['short'])
            if ls is None or c['line'] not in lmap:
                notes.append(f"no source line for {c['short']}:{c['line']}"); continue
            anc = {'file': c['short'], **locator(ls, lmap[c['line']]), 'target': o['line'], 'weight': WEIGHT[cls],
                   'label': f"{cls}:{hex(st)}", 'cur': c['line'], 'code': o['code']}
            anchors.append(anc)
    if a.extra and a.extra.exists():
        for x in json.loads(a.extra.read_text())['anchors']:
            anchors.append(x)
            for o in O[int(x['orig'], 0)]['sites']:
                if o['line'] == x['target']:
                    mapped[(int(x['orig'], 0), o['len_slot'])] = {'class': x['label'].split(':')[0], 'cand_fn': None,
                        'cand_name': x.get('item'), 'cand_file': x['file'], 'cand_line': None, 'cand_code': x.get('code')}
    sites = []
    for st in sorted(O):
        for o in O[st]['sites']:
            if not in_scope(o['short']):
                continue
            m = mapped.get((st, o['len_slot']))
            sites.append({'orig_window': hex(st), 'orig_file': o['short'], 'orig_line': o['line'], 'code': o['code'],
                          'window_matched': st in M, **(m or {'class': None})})
    sm = {'comment': 'coordfiles site map: original Source sites (non-lib.rs) -> our counterparts; anchors feed layout.py',
          'cand': str(a.cand), 'anchors': anchors, 'moves': moves, 'notes': notes, 'sites': sites}
    a.out.write_text(json.dumps(sm, indent=1))
    cnt = Counter(p[0] for p in pairs)
    print(f"pairs {dict(cnt)}; anchors {len(anchors)} ({sum(1 for x in anchors if x.get('cur') != x['target'])} off-target); "
          f"moves {len(moves)}; sites {len(sites)} mapped {sum(1 for s in sites if s['class'])}")
    for m in moves:
        print('  MOVE', m['class'], m['orig'], m['from'], '->', m['to'], m['cand_name'][:70])
    for n in notes:
        print('  note:', n)


if __name__ == '__main__':
    main()
