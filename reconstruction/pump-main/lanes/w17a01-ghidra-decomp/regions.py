#!/usr/bin/env python3
"""Region diff of admin_cto::execute (0x22a10), original vs ours, from the Ghidra exports (lane w17a01-ghidra-decomp).

usage: regions.py <ghidra_out> <lane_dir> [--orig-so deployed.so --ours-so unstripped.so]

Reads <tag>_22a10.{lst,cfg.json,calls.json,addr.c,frame_ghidra.json} written by SbfDecomp.java and writes into
<lane_dir>: decode_check.json, frame_map.json, regions.json, REGIONS.md and regions/<id>.{orig,ours}.c.
No build, no slot: pure text analysis.
"""
import argparse, difflib, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

W = 0x22a10
# Original regions (window offsets). Boundaries come from the original's call list (calls.json) and are snapped
# to block leaders. Names follow the swarm's region vocabulary (regions2.py of the w16 skeleton lens).
REGIONS = [
    ('E1', 0x0000, 'entry: holder PDA + shared test'),
    ('E2', 0x0280, 'entry: quote_locked (default/native/whitelist)'),
    ('E3', 0x0420, 'entry: CtoState + new/key copies, mayhem 284'),
    ('V1', 0x0700, 'validate: holder arm head, 289/298'),
    ('V2', 0x0b00, 'validate: non-holder arm 306/307/312 memcmps + shared split'),
    ('V3', 0x0e60, 'validate: 306/296/326 error blocks + holder exit'),
    ('V4', 0x1258, 'validate: 312/307 error blocks (outlined to_string)'),
    ('V5', 0x1490, 'validate: fee checks 330/334/338'),
    ('J1', 0x1800, 'join: holder/shared arms -> (collect_old, skip, sharing_update, target)'),
    ('J2', 0x1990, 'join: prepare_bonding_curve + 410'),
    ('W1', 0x1c80, 'wallet head: executable / owner checks, shared msg!'),
    ('S1', 0x1d80, 'sweep head + gate: native, creator-vault PDA, ConstraintSeeds, AMM present/frozen, 660'),
    ('T1', 0x26e8, 'TCF CPI: inline AccountInfo literals + transfer_creator_fees_to_pump_v2, Rent::get'),
    ('C1', 0x3c40, 'sharing-config CPI clone run (admin_cto_sharing_config)'),
    ('P1', 0x4a80, 'pool CPI: AMM pool owner test, msg, to_account_info clones, admin_cto_pool'),
    ('EV', 0x4e30, 'event: Clock::get, AdminCtoEvent emit + self-CPI'),
    ('TL', 0x5520, 'tails: error tails 92/88, unwrap_failed, From<AnchorError>'),
    ('S2', 0x5990, 'sweep native arm: Rent min balance, ensure_rent_exempt, transfer_native'),
    ('W2', 0x5bd0, 'wallet body: collect, create_idempotent x2, sweep token arm, CollectCreatorFeeEvent, AMM collect'),
]
END = 27400

ALU = {0x0: 'add', 0x1: 'sub', 0x2: 'mul', 0x3: 'div', 0x4: 'or', 0x5: 'and', 0x6: 'lsh', 0x7: 'rsh', 0x8: 'neg',
       0x9: 'mod', 0xa: 'xor', 0xb: 'mov', 0xc: 'arsh'}


def parse_lst(p):
    out = []
    for l in Path(p).read_text().splitlines()[1:]:
        m = re.match(r'^([0-9a-f]{6}) \+([0-9a-f]{5})  (.*?)\s*(?:;\s*(.*))?$', l)
        if not m:
            continue
        txt = m.group(3).strip(); note = m.group(4) or ''
        mn, _, ops = txt.partition(' ')
        out.append(dict(addr=int(m.group(1), 16), off=int(m.group(2), 16), mn=mn.lower(), ops=ops, note=note, text=txt))
    return out


def nums(s):
    return [int(x, 16) * (-1 if neg else 1) for neg, x in
            ((a == '-', b) for a, b in re.findall(r'(-?)\s*0x([0-9a-f]+)', s.lower()))]


def regs(s):
    return re.findall(r'\br(\d+)\b', s.lower())


def objdump_norm(line, addr):
    """win.py objdump text -> (family, regs, numbers) with jumps/calls made absolute."""
    line = re.sub(r'\s*<[^>]*>', '', line)  # objdump labels of the unstripped build (<LBB206_3>, <symbol>)
    m = re.match(r'^\s*(\S+)\s*(.*)$', line)
    mn, ops = m.group(1), m.group(2)
    fam = re.sub(r'64$', '', mn)
    if fam.startswith('j') and fam != 'ja' or fam == 'ja':
        rel = re.search(r'([+-])0x([0-9a-f]+)\s*$', ops)
        n = nums(ops[:rel.start()]) if rel else nums(ops)
        tgt = addr + 8 + (int(rel.group(2), 16) * (1 if rel.group(1) == '+' else -1)) * 8 if rel else None
        return fam, regs(ops), n + ([tgt] if tgt is not None else [])
    if fam == 'call':
        v = nums(ops)[0]
        return fam, [], [addr + 8 + v * 8]
    if fam in ('mov32',):
        fam = 'mov'
    return fam, regs(ops), nums(ops.replace(' - ', ' -').replace('- ', '-'))


def ghidra_norm(ins):
    fam = ins['mn']
    ops = ins['ops']
    n = nums(ops)
    return fam, regs(ops), n


def decode_check(lst, objtxt):
    """Compare Ghidra's decode with win.py's objdump decode instruction by instruction."""
    od = dict(objtxt)  # win.objdump_text: {address: 'mnemonic operands'}
    bad = []
    for ins in lst:
        o = od.get(ins['addr'])
        if o is None:
            bad.append((hex(ins['addr']), ins['text'], 'missing in win.py')); continue
        f1, r1, n1 = objdump_norm(o, ins['addr'])
        f2, r2, n2 = ghidra_norm(ins)
        if f1 == 'call' and f2 == 'call':
            # syscalls (`call -1`) are overridden in Ghidra to named stubs; compare the raw decode only
            if 'syscall' in ins['note']:
                ok = n1[0] == ins['addr']
            else:
                ok = n1 == n2
        else:
            ok = f1 == f2 and r1 == r2 and sorted(n1) == sorted(n2)
        if not ok:
            bad.append((hex(ins['addr']), ins['text'], o))
    extra = sorted(set(od) - {i['addr'] for i in lst})
    return dict(ghidra_insns=len(lst), winpy_insns=len(od), mismatches=len(bad), first_mismatches=bad[:20],
                missing_in_ghidra=[hex(a) for a in extra[:20]])


# ---------------------------------------------------------------- liveness / frame
def du(ins, nargs):
    """(defs, uses) register sets of one instruction (r10 excluded)."""
    mn, ops = ins['mn'], ins['ops']
    rs = [int(r) for r in regs(ops)]
    d, u = set(), set()
    if mn == 'call':
        u = set(range(1, 1 + nargs)); d = {0, 1, 2, 3, 4, 5}
    elif mn == 'exit':
        u = {0}
    elif mn in ('ja',):
        pass
    elif mn.startswith('j'):
        u = set(rs)
    elif mn.startswith('ldx') or mn.startswith('ldsx'):
        d = {rs[0]}; u = set(rs[1:])
    elif mn.startswith('stx'):
        u = set(rs)
    elif mn.startswith('st'):
        u = set(rs)
    elif mn == 'lddw':
        d = {rs[0]}
    elif mn in ('mov', 'mov32', 'movw', 'movsx'):
        d = {rs[0]}; u = set(rs[1:])
    else:  # alu: dst = dst op src
        d = {rs[0]}; u = set(rs)
    return d - {10}, u - {10}


def frame_access(ins):
    """('r'|'w'|'lea', offset, size) for r10-based accesses."""
    mn, ops = ins['mn'], ins['ops']
    m = re.search(r'\[R10 \+ (-?0x[0-9a-f]+)\]', ops)
    if m:
        off = int(m.group(1), 16)
        sz = {'b': 1, 'h': 2, 'w': 4, 'dw': 8}[re.sub(r'^(ldx|stx|st|ldsx)', '', mn)]
        return ('r' if mn.startswith('ld') else 'w', off, sz)
    return None


def analyze(tag, gdir):
    lst = parse_lst(gdir / f'{tag}_22a10.lst')
    cfg = json.loads((gdir / f'{tag}_22a10.cfg.json').read_text())
    calls = json.loads((gdir / f'{tag}_22a10.calls.json').read_text())['calls']
    frame = json.loads((gdir / f'{tag}_22a10.frame_ghidra.json').read_text())['high_symbols']
    addrc = (gdir / f'{tag}_22a10.addr.c').read_text().splitlines()
    return dict(lst=lst, cfg=cfg, calls=calls, frame=frame, addrc=addrc)


def nargs_table(*sides):
    t = defaultdict(int)
    for s in sides:
        for c in s['calls']:
            m = re.search(r'\((.*)\)\s*;?\s*$', c['c'])
            n = 0 if not m or not m.group(1).strip() else m.group(1).count(',') + 1
            t[c['callee']] = max(t[c['callee']], min(n, 5))
    return t


def liveness(side, nargs):
    lst = side['lst']; byoff = {i['off']: i for i in lst}
    blocks = side['cfg']['blocks']
    binfo = {}
    for b in blocks:
        ins = [i for i in lst if b['off'] <= i['off'] < b['end']]
        use, dfn = set(), set()
        for i in ins:
            callee = i['note'].split('-> ')[-1].split('  ;')[0].strip() if i['mn'] == 'call' else ''
            d, u = du(i, nargs.get(callee, 5))
            use |= (u - dfn); dfn |= d
        binfo[b['off']] = dict(use=use, dfn=dfn, succ=[s['to'] for s in b['succ']])
    live_in = {k: set() for k in binfo}
    changed = True
    while changed:
        changed = False
        for k in sorted(binfo, reverse=True):
            bi = binfo[k]
            out = set()
            for s in bi['succ']:
                out |= live_in.get(s, set())
            new = bi['use'] | (out - bi['dfn'])
            if new != live_in[k]:
                live_in[k] = new; changed = True
    preds = Counter(s for bi in binfo.values() for s in bi['succ'])
    return live_in, preds


def snap(cfg, off):
    leaders = sorted(b['off'] for b in cfg['blocks'])
    for l in leaders:
        if l >= off:
            return l
    return END


def short(n):
    n = re.sub(r'pump_recovered::', '', n)
    n = re.sub(r'<(?:\w+::)*', '<', n)
    n = n.replace('_as_core::', ' as ').replace('_as_anchor_lang::', ' as ')
    return n[-60:]


def align(o, u):
    """Instruction alignment orig->ours on register/frame/jump-masked tokens (difflib, no autojunk)."""
    def tok(i):
        t = i['mn'] + ' ' + re.sub(r'R\d+', 'R', i['ops'])
        t = re.sub(r'\[R \+ -0x[0-9a-f]+\]', '[R+fr]', t) if 'R10' in i['ops'] else t
        if i['mn'].startswith('j'):
            t = re.sub(r'0x[0-9a-f]{8}', 'L', t)
        if i['mn'] == 'call':
            t = 'call ' + i['note'].split('-> ')[-1][:60]
        if i['mn'] == 'add' and 'R,-0x' in t:
            t = 'add R,fr'
        return t
    a = [tok(i) for i in o]; b = [tok(i) for i in u]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    m = {}
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            m[o[blk.a + k]['off']] = u[blk.b + k]['off']
    return m, sm.ratio()


def btoks(side, b):
    out = []
    for i in side['lst']:
        if b['off'] <= i['off'] < b['end']:
            t = i['mn'] + ' ' + re.sub(r'R\d+', 'R', i['ops'])
            if 'R10' in i['ops']:
                t = re.sub(r'-0x[0-9a-f]+', 'fr', t)
            if i['mn'].startswith('j'):
                t = re.sub(r'0x[0-9a-f]{8}', 'L', t)
            if i['mn'] == 'call':
                t = 'call ' + i['note'].split('-> ')[-1][:70]
            if i['mn'] == 'lddw':
                t = 'lddw ' + i['note'][:40]
            if i['mn'] == 'add' and re.match(r'R,-0x', re.sub(r'R\d+', 'R', i['ops'])):
                t = 'add R,fr'
            out.append(t)
    return out


def block_regions(O, U, oreg):
    """Match ours blocks to original blocks by masked content (calls, lddw constants, opcode shapes)."""
    ob = [(b, btoks(O, b)) for b in O['cfg']['blocks']]
    ub = [(b, btoks(U, b)) for b in U['cfg']['blocks']]
    cand = []
    for j, (bu, tu) in enumerate(ub):
        cu = Counter(tu)
        scored = []
        for k, (bo, to) in enumerate(ob):
            inter = sum((cu & Counter(to)).values())
            q = 2 * inter / max(1, len(tu) + len(to))
            if q > 0.4:
                scored.append((q, k))
        for q, k in sorted(scored, reverse=True)[:8]:
            r = difflib.SequenceMatcher(None, ob[k][1], tu, autojunk=False).ratio()
            # layout prior: most blocks keep their relative position (0x6b08-byte window)
            r -= 1.0 * abs(ob[k][0]['off'] - bu['off']) / END
            # identity bonus: same callee/constant multiset (error sites differ only in their constants)
            sig_o = [t for t in ob[k][1] if t.startswith(('call', 'lddw'))]
            sig_u = [t for t in tu if t.startswith(('call', 'lddw'))]
            bonus = 0.25 if sig_o and sig_o == sig_u else 0.0
            cand.append((r + bonus, j, k))
    cand.sort(reverse=True)
    mu, mo, bmatch = {}, set(), {}
    for sc, j, k in cand:
        if j in mu or k in mo or sc < 0.55:
            continue
        mu[j] = k; mo.add(k); bmatch[ub[j][0]['off']] = (ob[k][0]['off'], round(sc, 3))
    breg = {}
    for j, (bu, _) in enumerate(ub):
        if j in mu:
            breg[bu['off']] = oreg[ob[mu[j]][0]['off']]
    preds = defaultdict(list)
    for bu, _ in ub:
        for s_ in bu['succ']:
            preds[s_['to']].append(bu['off'])
    order = [bu['off'] for bu, _ in ub]
    for _ in range(4):
        for k, off in enumerate(order):
            if off in breg:
                continue
            ps = [breg[p] for p in preds.get(off, []) if p in breg]
            if ps:
                breg[off] = Counter(ps).most_common(1)[0][0]
    for k, off in enumerate(order):
        if off not in breg:
            breg[off] = breg.get(order[k - 1], 'E1') if k else 'E1'
    ureg = {}
    for bu, _ in ub:
        for i in U['lst']:
            if bu['off'] <= i['off'] < bu['end']:
                ureg[i['off']] = breg[bu['off']]
    return ureg, bmatch


def region_of(off, bounds):
    r = bounds[0][0]
    for rid, lo in bounds:
        if off >= lo:
            r = rid
    return r


def write_md(lane, rows):
    T = ['| id | region (orig window offsets) | orig range | insns o/u | blocks o/u | calls o/u | frame ld o/u | frame st o/u '
         '| joins o/u | regs live at joins o/u | ours spans | tokens: orig / exact LCS / fully-masked LCS |',
         '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        o, u, t = r['orig'], r['ours'], r.get('tokens', {})
        T.append(f"| {r['id']} | {r['name']} | 0x{r['range'][0]:x}-0x{r['range'][1]:x} | {o['insns']}/{u['insns']} | "
                 f"{o['blocks']}/{u['blocks']} | {len(o['calls'])}/{len(u['calls'])}{'' if r['call_order_same'] else ' (order differs)'} | "
                 f"{o['frame_r']}/{u['frame_r']} | {o['frame_w']}/{u['frame_w']} | {o['joins']}/{u['joins']} | "
                 f"{o['live_across_joins']}/{u['live_across_joins']} | {u['nspans']} | "
                 f"{t.get('ntok', '')} / {t.get('exact', '')} / {t.get('mask_frame_reg_jmp', '')} |")
    out = ['<!-- generated by regions.py; the hand-written analysis is in REGIONS.md -->', '# Region table (generated)', '',
           'o = original, u = ours (main 599891304). Ours regions are assigned by block matching (calls, lddw constants, '
           'masked opcode shapes, layout prior), so a region can be several spans in ours. Token columns attribute the '
           'w16 ceilings `decomp.py --lcs` per-0x400-chunk counts to regions by byte overlap.', ''] + T + ['']
    for r in rows:
        out += [f"## {r['id']}: {r['name']} (orig 0x{r['range'][0]:x}-0x{r['range'][1]:x})", '']
        if not r['call_order_same']:
            out += ['Call order differs:', '', '- orig: ' + ', '.join(r['orig']['calls']), '- ours: ' + ', '.join(r['ours']['calls']), '']
        for tag in ('orig', 'ours'):
            out += [f"{tag} salient lines (full excerpt: `regions/{r['id']}.{tag}.c`):", '', '```c'] + \
                   [l[:170] for l in r[tag]['salient']] + ['```', '']
    (lane / 'REGIONS_TABLE.md').write_text('\n'.join(out) + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('gdir'); ap.add_argument('lane')
    ap.add_argument('--orig-so'); ap.add_argument('--ours-so')
    ap.add_argument('--chunks', help='w16 ceilings decomp.py --lcs output (per-0x400 orig chunk matched tokens)')
    a = ap.parse_args()
    gdir, lane = Path(a.gdir), Path(a.lane)
    (lane / 'regions').mkdir(parents=True, exist_ok=True)
    O, U = analyze('orig', gdir), analyze('ours', gdir)
    # 1. decode check against win.py's objdump decode
    if a.orig_so and a.ours_so:
        sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'reconstruction' / 'harness'))
        from win import objdump_text  # noqa
        res = {}
        for tag, so, side in (('orig', a.orig_so, O), ('ours', a.ours_so, U)):
            txt = objdump_text(so, W, W + END)
            res[tag] = decode_check(side['lst'], txt)
        (lane / 'decode_check.json').write_text(json.dumps(res, indent=1) + '\n')
        print('decode check:', {k: (v['ghidra_insns'], v['winpy_insns'], v['mismatches']) for k, v in res.items()})
    # 2. boundaries
    bounds_o = [(rid, snap(O['cfg'], lo)) for rid, lo, _ in REGIONS]
    amap, aratio = align(O['lst'], U['lst'])
    oreg = {i['off']: region_of(i['off'], bounds_o) for i in O['lst']}
    # ours region: block matching (layout-independent), then CFG-predecessor / layout inheritance for leftovers
    ureg, bmatch = block_regions(O, U, oreg)
    # 3. per-region facts
    nargs = nargs_table(O, U)
    live = {}
    for tag, side, rmap in (('orig', O, oreg), ('ours', U, ureg)):
        li, preds = liveness(side, nargs)
        joins = defaultdict(list)
        for b in side['cfg']['blocks']:
            if preds.get(b['off'], 0) >= 2:
                joins[rmap.get(b['off'], '?')].append((b['off'], sorted(li[b['off']])))
        live[tag] = joins
    chunks = {}
    if a.chunks and Path(a.chunks).exists():
        for l in Path(a.chunks).read_text().splitlines():
            m = re.match(r'^0x([0-9a-f]{5})\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)', l)
            if m:
                chunks[int(m.group(1), 16)] = [int(x) for x in m.groups()[1:]]
    rows = []
    fmap = {}
    for tag, side, rmap in (('orig', O, oreg), ('ours', U, ureg)):
        names = {s['r10_off']: s['name'] for s in side['frame'] if 'r10_off' in s}
        acc = defaultdict(lambda: dict(r=0, w=0, lea=0, sizes=set(), regions=set(), first=None, last=None))
        lst = side['lst']
        for k, i in enumerate(lst):
            fa = frame_access(i)
            if fa:
                kind, off, sz = fa
            elif i['mn'] == 'add' and k and lst[k - 1]['mn'] == 'mov' and lst[k - 1]['ops'].endswith(',R10') \
                    and re.match(r'R\d+,-0x', i['ops']):
                kind, off, sz = 'lea', -int(i['ops'].split(',-')[1], 16), 0
            else:
                continue
            e = acc[off]; e[kind] += 1; e['sizes'].add(sz); e['regions'].add(rmap[i['off']])
            e['first'] = i['off'] if e['first'] is None else e['first']; e['last'] = i['off']
        fmap[tag] = [dict(r10_off=off, ghidra=names.get(off, ''), reads=e['r'], writes=e['w'], lea=e['lea'],
                          sizes=sorted(e['sizes']), regions=sorted(e['regions']), first=e['first'], last=e['last'])
                     for off, e in sorted(acc.items())]
    (lane / 'frame_map.json').write_text(json.dumps(fmap, indent=0) + '\n')
    for rid, lo, name in REGIONS:
        lo_s = dict(bounds_o)[rid]
        nxt = [b for r, b in bounds_o if b > lo_s]
        hi_s = min(nxt) if nxt else END
        r = dict(id=rid, name=name, range=[lo_s, hi_s])
        for tag, side, rmap in (('orig', O, oreg), ('ours', U, ureg)):
            ins = [i for i in side['lst'] if rmap[i['off']] == rid]
            offs = [i['off'] for i in ins]
            blks = [b for b in side['cfg']['blocks'] if rmap.get(b['off']) == rid]
            cl = [c for c in side['calls'] if rmap.get(c['off']) == rid]
            fr = [frame_access(i) for i in ins]
            spans = []
            for o in offs:
                if spans and o == spans[-1][1]:
                    spans[-1][1] = o + (16 if side['lst'][0] and False else 0)
                spans.append([o, o + 8]) if not spans or o > spans[-1][1] else None
                spans[-1][1] = max(spans[-1][1], o + 8)
            r[tag] = dict(insns=len(ins), blocks=len(blks), spans=[[s, e] for s, e in spans][:12], nspans=len(spans),
                          calls=[short(c['callee']) for c in cl],
                          frame_r=sum(1 for f in fr if f and f[0] == 'r'), frame_w=sum(1 for f in fr if f and f[0] == 'w'),
                          frame_slots=len({f[1] for f in fr if f}),
                          lddw=sum(1 for i in ins if i['mn'] == 'lddw'),
                          branches=sum(1 for i in ins if i['mn'].startswith('j') and i['mn'] != 'ja'),
                          ja=sum(1 for i in ins if i['mn'] == 'ja'),
                          joins=len(live[tag].get(rid, [])),
                          live_across_joins=sum(len(x[1]) for x in live[tag].get(rid, [])),
                          max_live=max([len(x[1]) for x in live[tag].get(rid, [])] or [0]))
            # C excerpt: lines whose address range starts in this region's instructions
            sel = set(offs)
            lines = []
            for l in side['addrc']:
                m = re.match(r'^/\*\s*([0-9a-f]+)-\s*([0-9a-f]+)\*/(.*)$', l)
                if m and int(m.group(1), 16) in sel:
                    lines.append(f'/*{int(m.group(1), 16):5x}*/' + m.group(3))
            (lane / 'regions' / f'{rid}.{tag}.c').write_text('\n'.join(lines) + '\n')
            r[tag]['c_lines'] = len(lines)
            sal = [l for l in lines if re.search(r'\w+::\w+.*\(|memcmp\(|memcpy\(|sol_log|\bif \(|goto |return|abort\(', l)]
            r[tag]['salient'] = sal[:16]
        if chunks:
            # w16 ceilings decomp.py --lcs counts per 0x400 orig chunk, attributed by byte overlap
            acc_t = [0.0, 0.0, 0.0]
            for k, v in chunks.items():
                ov = max(0, min(hi_s, k + 0x400) - max(lo_s, k)) / 0x400
                acc_t[0] += v[0] * ov; acc_t[1] += v[1] * ov; acc_t[2] += v[5] * ov
            r['tokens'] = dict(ntok=round(acc_t[0]), exact=round(acc_t[1]), mask_frame_reg_jmp=round(acc_t[2]),
                               gap_exact=round(acc_t[0] - acc_t[1]), gap_masked=round(acc_t[0] - acc_t[2]))
        oc, uc = Counter(r['orig']['calls']), Counter(r['ours']['calls'])
        r['calls_only_orig'] = sorted((oc - uc).elements())
        r['calls_only_ours'] = sorted((uc - oc).elements())
        r['call_order_same'] = r['orig']['calls'] == r['ours']['calls']
        rows.append(r)
    (lane / 'regions.json').write_text(json.dumps(dict(align_ratio=aratio, aligned=len(amap), matched_blocks=len(bmatch),
                                                   block_match={hex(k): [hex(v[0]), v[1]] for k, v in sorted(bmatch.items())},
                                                   regions=rows), indent=1) + '\n')
    print('aligned', len(amap), 'ratio', round(aratio, 4))
    write_md(lane, rows)
    for r in rows:
        o, u = r['orig'], r['ours']
        print(f"{r['id']} {r['range'][0]:5x}-{r['range'][1]:5x} ins {o['insns']:4d}/{u['insns']:4d} blk {o['blocks']:3d}/{u['blocks']:3d} "
              f"calls {len(o['calls']):3d}/{len(u['calls']):3d} fr r{o['frame_r']}/{u['frame_r']} w{o['frame_w']}/{u['frame_w']} "
              f"joins {o['joins']}/{u['joins']} live {o['live_across_joins']}/{u['live_across_joins']} spans {u['nspans']} "
              f"{'' if r['call_order_same'] else 'CALL-ORDER'} {r.get('tokens', '')}")


if __name__ == '__main__':
    main()
