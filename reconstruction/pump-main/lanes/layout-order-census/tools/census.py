#!/usr/bin/env python3
"""layout-order-census: pair original windows to candidate functions, then census order and operands.

census.py <unstripped.so> <out.json>
"""
import sys, json, hashlib, struct, re, bisect
from pathlib import Path
from collections import defaultdict, Counter
TOOLS = Path('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/restore/reconstruction')
sys.path.insert(0, str(TOOLS / 'harness'))
from score import sections, normalize, body, candidate_functions, original_windows, BASE  # noqa

UNMATCHED_NAMES = {
    0x14f4e0: r'14pump_recovered16buy_exact_sol_in', 0x80df8: r'v3_buy_costs', 0x6cd78: r'process_cashback_inner',
    0x83c00: r'v3_execute_buy', 0x13f630: r'(buy_exact_quote_in_handler17h|14pump_recovered21buy_exact_quote_in_v217h)', 0x13b9b8: r'(6buy_v211buy_handler17h|14pump_recovered6buy_v217h)',
    0x144508: r'(7sell_v27execute17h|14pump_recovered7sell_v217h)', 0x4c158: r'create_token_account_v2', 0x147ba0: r'5trade3buy17',
    0x14a8a8: r'5trade4sell17', 0x1489f8: r'5trade15buy_exact_quote17', 0x72810: r'5sweep7execute',
    0x1e7c0: r'9create_v27execute', 0x77940: r'8cashback8claim_v2', 0x5b3b0: r'swap_hop',
    0x22a10: r'9admin_cto7execute',
}


def insn_iter(raw):
    i = 0
    while i < len(raw):
        n = 16 if raw[i] == 0x18 else 8
        yield i, raw[i:i + n]
        i += n


def operands(raw, addr, secs):
    """list of (offset, kind, value) for masked operands."""
    out = []
    for i, ins in insn_iter(raw):
        op = ins[0]
        if op == 0x18:
            v = struct.unpack_from('<I', ins, 4)[0] | struct.unpack_from('<I', ins, 12)[0] << 32
            sec = next((n for n, s in secs.items() if s['addr'] > 0 and s['addr'] <= v < s['addr'] + s['size']), None)
            if sec:
                out.append((i, 'lddw', v, sec))
        elif op == 0x85 and ins[1] >> 4 == 1:
            imm = struct.unpack_from('<i', ins, 4)[0]
            if imm != -1:
                tgt = addr + i + 8 + imm * 8
                out.append((i, 'call', tgt, imm))
    return out


def main():
    cpath = Path(sys.argv[1]); outp = Path(sys.argv[2])
    orig = (BASE / 'original.so').read_bytes(); osec = sections(orig)
    cand = cpath.read_bytes(); csec = sections(cand)
    wins = original_windows()
    funcs = candidate_functions(cpath)
    byaddr = {}
    for a, s, n in funcs:
        byaddr.setdefault(a, (a, s, []))[2].append(n)
    cf = sorted(byaddr.values())
    cls = defaultdict(list)
    for a, s, names in cf:
        raw = body(cand, csec, a, s)
        cls[(s, hashlib.sha256(normalize(raw, a, csec)).digest())].append((a, raw, names))
    ocls = defaultdict(list)
    for w in wins:
        ocls[(w['bytes'], hashlib.sha256(w['norm']).digest())].append(w)
    pair = {}  # orig start -> cand addr
    amb = 0
    for k, ws in ocls.items():
        cs = cls.get(k, [])
        if not cs:
            continue
        ws = sorted(ws, key=lambda w: w['start'])
        if len(ws) > 1 or len(cs) > 1:
            amb += 1
        # prefer raw-equal pairing, then rank order
        used = set()
        for w in ws:
            for c in cs:
                if c[0] not in used and c[1] == w['raw']:
                    pair[w['start']] = c[0]; used.add(c[0]); break
        rest = [c for c in cs if c[0] not in used]
        for w in ws:
            if w['start'] not in pair and rest:
                pair[w['start']] = rest.pop(0)[0]
    # unmatched by name
    for s, rx in UNMATCHED_NAMES.items():
        hits = [a for a, sz, names in cf if any(re.search(rx, n) for n in names)]
        if s not in pair and hits:
            pair[s] = hits[0]
    cinfo = {a: (s, names) for a, s, names in cf}
    winfo = {w['start']: w for w in wins}
    ostarts = sorted(winfo)
    # orig text coverage
    t = osec['.text']
    covered = sum(w['bytes'] for w in wins)
    # order analysis: sequence of cand addrs in original order
    seq = [(s, pair[s]) for s in ostarts if s in pair]
    # LIS
    import itertools
    vals = [c for _, c in seq]
    tails, tidx, prev = [], [], [-1] * len(vals)
    for i, v in enumerate(vals):
        j = bisect.bisect_left(tails, v)
        if j == len(tails):
            tails.append(v); tidx.append(i)
        else:
            tails[j] = v; tidx[j] = i
        prev[i] = tidx[j - 1] if j > 0 else -1
    lis = set(); k = tidx[-1] if tidx else -1
    while k >= 0:
        lis.add(k); k = prev[k]
    out_of_order = [seq[i] for i in range(len(seq)) if i not in lis]
    # delta profile
    deltas = [(s, c - s) for s, c in seq]
    # per normalized window operand census
    res = []
    o2c = pair
    # map original address -> window start (for call targets)
    def owin(addr):
        i = bisect.bisect_right(ostarts, addr) - 1
        return ostarts[i] if i >= 0 and addr < ostarts[i] + winfo[ostarts[i]]['bytes'] else None
    cstarts = sorted(cinfo)
    def cfn(addr):
        i = bisect.bisect_right(cstarts, addr) - 1
        return cstarts[i] if i >= 0 else None
    for s in ostarts:
        w = winfo[s]
        if s not in pair:
            res.append({'start': hex(s), 'status': 'unpaired'}); continue
        c = pair[s]; csz, names = cinfo[c]
        craw = body(cand, csec, c, csz)
        norm_eq = csz == w['bytes'] and normalize(craw, c, csec) == w['norm']
        raw_eq = norm_eq and craw == w['raw']
        r = {'start': hex(s), 'cand': hex(c), 'bytes': w['bytes'], 'cand_bytes': csz, 'name': names[0],
             'normalized': norm_eq, 'raw': raw_eq, 'delta': c - s}
        if norm_eq and not raw_eq:
            oo = operands(w['raw'], s, osec); co = operands(craw, c, csec)
            calls = Counter(); lddw = Counter(); bad = []
            for a, b in zip(oo, co):
                if a[1] == 'call':
                    if a[2] == b[2] - (c - s) and False:
                        pass
                    if struct.unpack_from('<i', w['raw'], a[0] + 4) == struct.unpack_from('<i', craw, b[0] + 4):
                        calls['same_imm'] += 1; continue
                    ot = owin(a[2]); ct = cfn(b[2])
                    if ot is None:
                        calls['orig_target_not_window'] += 1
                    elif o2c.get(ot) == ct:
                        calls['same_callee_shifted'] += 1
                    else:
                        calls['different_callee'] += 1; bad.append((hex(a[0]), hex(a[2]), hex(b[2])))
                else:
                    if a[2] == b[2]:
                        lddw['same_value'] += 1; continue
                    osn, csn = a[3], b[3]
                    if osn == '.text':
                        ot = owin(a[2]); ct = cfn(b[2])
                        lddw['text_same_fn' if ot is not None and o2c.get(ot) == ct else 'text_other'] += 1
                    else:
                        oo_ = a[2] - osec[osn]['addr']; co_ = b[2] - csec[csn]['addr']
                        lddw[f'{osn}:{"same_off" if osn==csn and oo_==co_ else "diff_off"}'] += 1
            r['calls'] = dict(calls); r['lddw'] = dict(lddw); r['bad_calls'] = bad[:5]
        res.append(r)
    summ = {
        'orig_text_size': t['size'], 'cand_text_size': csec['.text']['size'],
        'orig_windows': len(wins), 'covered_bytes': covered, 'paired': len(pair), 'ambiguous_classes': amb,
        'lis_len': len(lis), 'out_of_order': len(out_of_order),
        'out_of_order_list': [(hex(a), hex(b), cinfo[b][1][0]) for a, b in out_of_order],
    }
    json.dump({'summary': summ, 'windows': res, 'deltas': [(hex(a), d) for a, d in deltas]}, outp.open('w'), indent=1)
    print(json.dumps(summ, indent=1)[:4000])


if __name__ == '__main__':
    main()
