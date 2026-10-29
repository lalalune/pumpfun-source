#!/usr/bin/env python3
"""Coordinate archaeology: per-window source-coordinate line maps (original vs candidate).

Extracts, for an original window and a candidate function:
  * Anchor Source{file,line} stack sites (tools/harness/coords.py::sites), with the nearest
    error-code immediate (stw/mov imm in [100, 10000)) as an alignment key;
  * panic core::panic::Location{file,line,col} references (lddw into .data.rel.ro whose
    24-byte record is a {ptr<<32, len, line, col} pointing at a *.rs path).
Then aligns the two site sequences on (kind, path, code) and reports line deltas.

  linemap.py targets --cand unstripped.so --src programs/pump [--json out.json]
  linemap.py locset  --cand unstripped.so       # global panic-Location multiset diff
  linemap.py scan    --cand unstripped.so [--json out.json]   # all normalized windows
"""
import argparse, difflib, json, re, struct, sys
from collections import Counter
from pathlib import Path

TOOLS = Path('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/restore/reconstruction')
sys.path.insert(0, str(TOOLS / 'harness'))
from score import sections, body, original_windows, candidate_functions, BASE, normalize, score  # noqa
from coords import sites as source_sites  # noqa

TARGETS = {
    0x14f4e0: r'buy_exact_sol_in17h', 0x80df8: r'5trade12v3_buy_costs17h',
    0x6cd78: r'process_cashback_inner17h', 0x83c00: r'5trade14v3_execute_buy17h',
    0x13f630: r'buy_v226buy_exact_quote_in_handler17h', 0x13b9b8: r'buy_v211buy_handler17h',
    0x144508: r'sell_v27execute17h', 0x4c158: r'create_token_account_v217h',
    0x147ba0: r'5trade3buy17h', 0x14a8a8: r'5trade4sell17h', 0x1489f8: r'5trade15buy_exact_quote17h',
    0x72810: r'5sweep7execute17h', 0x1e7c0: r'create_v27execute17h', 0x77940: r'cashback8claim_v217h',
    0x5b3b0: r'swap_hop17h', 0x22a10: r'admin_cto7execute17h',
}


def decode(raw):
    out = []; i = 0
    while i < len(raw):
        op = raw[i]
        if op == 0x18:
            lo = struct.unpack_from('<I', raw, i + 4)[0]; hi = struct.unpack_from('<I', raw, i + 12)[0]
            out.append((i, op, raw[i + 1], 0, lo | hi << 32)); i += 16
        else:
            _, regs, off, imm = struct.unpack_from('<BBhi', raw, i)
            out.append((i, op, regs, off, imm)); i += 8
    return out


class Image:
    def __init__(self, path):
        self.blob = Path(path).read_bytes(); self.secs = sections(self.blob)
        self.locs = self._locations()

    def read(self, va, n):
        for s in self.secs.values():
            if s['addr'] and s['addr'] <= va < s['addr'] + s['size']:
                o = va - s['addr'] + s['offset']; return self.blob[o:o + n]
        return None

    def _locations(self):
        d = self.secs['.data.rel.ro']; out = {}
        for off in range(0, d['size'] - 23, 8):
            p, l, ln, c = struct.unpack_from('<QQII', self.blob, d['offset'] + off)
            if not 0 < l < 200:
                continue
            for pp in (p >> 32, p):
                st = self.read(pp, l)
                if st and st.endswith(b'.rs') and all(32 <= x < 127 for x in st):
                    out[d['addr'] + off] = (st.decode(), ln, c); break
        return out

    def sites(self, start, raw):
        ins = decode(raw); res = []
        for s in source_sites(self.blob, self.secs, start, raw):
            k = next(j for j, x in enumerate(ins) if x[0] == s['len_slot'])
            # AnchorError.error_code_number is stored at Source.filename.len slot + 136 (392/392 original sites)
            code = None; best = 99; X = ins[k][3]
            # scan outward within the straight-line run (stop at call/exit/ja/conditional jumps).
            # NOTE coords.py takes the FIRST stw [r10+X+8] in a +-30 window, which can be a preceding
            # site's line when two sites reuse one stack slot; we take the nearest in the same run.
            line = None; lbest = 99; line_slot = None
            for rng in (range(k, max(-1, k - 40), -1), range(k + 1, min(len(ins), k + 40))):
                for j in rng:
                    p, op, rg, of, im = ins[j]
                    if op in (0x85, 0x95, 0x05) or (op & 0x07) == 0x05:
                        break
                    if op == 0x62 and (rg & 0xf) == 10 and of == X + 136 and abs(j - k) < best:
                        code, best = im, abs(j - k)
                    if op == 0x62 and (rg & 0xf) == 10 and of == X + 8 and abs(j - k) < lbest:
                        line, lbest, line_slot = im, abs(j - k), p
            if line is not None and line != s['line']:
                s = dict(s, line=line, line_slot=line_slot, coords_py_line=s['line'])
            res.append({'slot': s['len_slot'], 'kind': 'source', 'path': s['path'], 'line': s['line'], 'col': None, 'code': code,
                        'line_slot': s['line_slot'], 'coords_py_line': s.get('coords_py_line')})
        for (p, op, rg, of, im) in ins:
            if op == 0x18 and im in self.locs:
                f, ln, c = self.locs[im]
                res.append({'slot': p, 'kind': 'panic', 'path': f, 'line': ln, 'col': c, 'code': None, 'loc_addr': hex(im)})
        res.sort(key=lambda r: r['slot'])
        return res


def key(s):
    return (s['kind'], s['path'], s['code'] if s['kind'] == 'source' else s['col'])


def src_line(srcroot, path, line):
    if not srcroot or line is None:
        return None
    p = Path(srcroot).parent.parent / path  # programs/pump/src/x.rs relative to repo root
    if not p.exists():
        return None
    L = p.read_text().splitlines()
    return L[line - 1].strip()[:160] if 0 < line <= len(L) else None


KIND = [(r'require_keys_neq!', 'require_keys_neq!'), (r'require_keys_eq!', 'require_keys_eq!'), (r'require_gte!', 'require_gte!'),
        (r'require_gt!', 'require_gt!'), (r'require_neq!', 'require_neq!'), (r'require_eq!', 'require_eq!'), (r'require!', 'require!'),
        (r'err!', 'err!'), (r'error!', 'error!'), (r'panic!|unwrap\(|expect\(|\[|unreachable!|assert', 'panic-site'), (r'\?', '?')]


def classify(text, kind):
    if text is None:
        return None
    for rx, nm in KIND:
        if re.search(rx, text):
            return nm
    return 'other'


def align(osites, csites, srcroot):
    sm = difflib.SequenceMatcher(None, [key(s) for s in osites], [key(s) for s in csites], autojunk=False)
    rows = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            pairs = [(osites[i1 + t], csites[j1 + t]) for t in range(i2 - i1)]
        else:
            n = max(i2 - i1, j2 - j1)
            # pair positionally only when path+kind agree (code differs => statement differs)
            pairs = []
            for t in range(n):
                o = osites[i1 + t] if i1 + t < i2 else None
                c = csites[j1 + t] if j1 + t < j2 else None
                if o and c and (o['kind'], o['path']) != (c['kind'], c['path']):
                    pairs += [(o, None), (None, c)]
                else:
                    pairs.append((o, c))
        for o, c in pairs:
            r = {'align': tag if (o and c) else ('orig-only' if o else 'cand-only')}
            if o:
                r['orig'] = {k: o[k] for k in ('slot', 'kind', 'path', 'line', 'col', 'code')}
            if c:
                r['cand'] = {k: c[k] for k in ('slot', 'kind', 'path', 'line', 'col', 'code')}
                txt = src_line(srcroot, c['path'], c['line'])
                r['cand']['text'] = txt
                r['statement'] = classify(txt, c['kind'])
            if o and c:
                r['line_delta'] = (o['line'] - c['line']) if (o['line'] is not None and c['line'] is not None) else None
                r['same_path'] = o['path'] == c['path']
                r['code_equal'] = o['code'] == c['code']
                r['status'] = 'match' if (o['path'], o['line'], o['col'], o['code']) == (c['path'], c['line'], c['col'], c['code']) else 'mismatch'
            else:
                r['status'] = 'unpaired'
            rows.append(r)
    return rows


def find_fn(cand_path, rx):
    fs = [(s, n, nm) for s, n, nm in candidate_functions(cand_path) if re.search(rx, nm)]
    fs.sort(key=lambda f: -f[1])
    return fs[0] if fs else None


def cmd_targets(a):
    orig = Image(BASE / 'original.so'); cand = Image(a.cand)
    wins = {w['start']: w for w in original_windows()}
    out = {}
    for start, rx in TARGETS.items():
        w = wins[start]
        f = find_fn(a.cand, rx)
        osites = orig.sites(start, w['raw'])
        csites = cand.sites(f[0], body(cand.blob, cand.secs, f[0], f[1])) if f else []
        rows = align(osites, csites, a.src)
        groups = {}
        for tag, L in (('orig', osites), ('cand', csites)):
            for x in L:
                g = groups.setdefault('|'.join(map(str, key(x))), {'orig': [], 'cand': []})
                g[tag].append(x['line'])
        multiset = []
        for g, v in sorted(groups.items()):
            o, c = Counter(v['orig']), Counter(v['cand'])
            if o != c:
                multiset.append({'key': g, 'orig_lines': sorted(v['orig']), 'cand_lines': sorted(v['cand']),
                                 'orig_only': sorted((o - c).elements()), 'cand_only': sorted((c - o).elements()),
                                 'cand_text': {str(l): src_line(a.src, g.split('|')[1], l) for l in sorted(set((c - o).elements()))}})
        paths = Counter(s['path'] for s in osites)
        cpaths = Counter(s['path'] for s in csites)
        mm = [r for r in rows if r['status'] != 'match']
        deltas = Counter(r.get('line_delta') for r in rows if r['status'] == 'mismatch' and r.get('line_delta') is not None)
        out[hex(start)] = {
            'window_bytes': w['bytes'], 'candidate': f[2] if f else None, 'cand_addr': hex(f[0]) if f else None, 'cand_bytes': f[1] if f else None,
            'original_source_files': dict(paths), 'candidate_source_files': dict(cpaths),
            'orig_sites': len(osites), 'cand_sites': len(csites),
            'matched_sites': sum(r['status'] == 'match' for r in rows),
            'mismatched_pairs': sum(r['status'] == 'mismatch' for r in rows),
            'orig_only': sum(r['align'] == 'orig-only' for r in rows), 'cand_only': sum(r['align'] == 'cand-only' for r in rows),
            'mismatch_line_delta_histogram': {str(k): v for k, v in sorted(deltas.items())},
            'line_multiset_mismatches': multiset,
            'rows': rows,
        }
        t = out[hex(start)]
        print(f"{hex(start):>9} {w['bytes']:6} files={dict(paths)} orig={len(osites)} cand={len(csites)} match={t['matched_sites']} "
              f"mismatch={t['mismatched_pairs']} o-only={t['orig_only']} c-only={t['cand_only']} deltas={t['mismatch_line_delta_histogram']} multiset_mm={len(multiset)}")
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1))


def cmd_locset(a):
    orig = Image(BASE / 'original.so'); cand = Image(a.cand)
    o = Counter(orig.locs.values()); c = Counter(cand.locs.values())
    print('orig-only:', sorted((o - c).items())); print('cand-only:', sorted((c - o).items()))
    oo = [v for _, v in sorted(orig.locs.items())]; cc = [v for _, v in sorted(cand.locs.items())]
    print('same order:', oo == cc, len(oo), len(cc))


def cmd_scan(a):
    """All windows that are normalized-matched: compare their site sequences with the matched candidate."""
    orig = Image(BASE / 'original.so'); cand = Image(a.cand)
    cur = score(a.cand)
    addr = {nm: (s, n) for s, n, nm in candidate_functions(a.cand)}
    rows = []; stats = Counter()
    for w in original_windows():
        r = cur[w['start']]
        if not r['normalized']:
            continue
        best = None
        for nm in r['symbols']:
            s, n = addr[nm]
            cs = cand.sites(s, body(cand.blob, cand.secs, s, n)); os_ = orig.sites(w['start'], w['raw'])
            sig = lambda L: [(x['kind'], x['path'], x['line'], x['col'], x['code']) for x in L]
            same = sig(cs) == sig(os_)
            raw_c = body(cand.blob, cand.secs, s, n)
            # immediate (non-masked) differences other than lddw/call masks: by definition zero for normalized pairs
            if best is None or same:
                best = (nm, same, os_, cs)
            if same:
                break
        nm, same, os_, cs = best
        stats['windows'] += 1; stats['with_sites'] += bool(os_); stats['same'] += same
        stats['raw'] += r['raw']
        if not same:
            rows.append({'start': hex(w['start']), 'symbol': nm, 'orig': os_, 'cand': cs})
        stats['panic_sites'] += sum(x['kind'] == 'panic' for x in os_); stats['source_sites'] += sum(x['kind'] == 'source' for x in os_)
    print(dict(stats)); print('differing windows:', len(rows))
    for r in rows[:40]:
        print(r['start'], r['symbol'][:70], [(x['kind'], x['path'].split('/')[-1], x['line'], x['col']) for x in r['orig']],
              [(x['kind'], x['path'].split('/')[-1], x['line'], x['col']) for x in r['cand']])
    if a.json:
        Path(a.json).write_text(json.dumps({'stats': dict(stats), 'differing': rows}, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    for nm in ('targets', 'locset', 'scan'):
        p = sub.add_parser(nm); p.add_argument('--cand', required=True); p.add_argument('--json'); p.add_argument('--src')
    a = ap.parse_args()
    {'targets': cmd_targets, 'locset': cmd_locset, 'scan': cmd_scan}[a.cmd](a)


if __name__ == '__main__':
    main()
