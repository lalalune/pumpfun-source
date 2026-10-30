#!/usr/bin/env python3
"""lr.py <rxdir> [--orig orig.txt] [--json out.json]: live-range / spill census for admin_cto::execute (experiment only).

Runs the debug llc (-debug-only=regalloc,prologepilog,stack-slot-coloring) on <rxdir>/m.ll and builds
  spill-slot r10 offset -> SS# -> LLVM original vreg -> defining MIR (block, instr, %ir name).
Then aligns ours vs the original with difflib on n2 tokens (registers, r10 offsets, jump offsets, call/lddw imms masked)
and lists every spill (stxdw [r10-X] at a spill slot) and reload (ldxdw [r10-X]) that is present on only one side,
annotated with the ours value (directly for ours-only, via the aligned orig->ours slot map for orig-only)."""
import sys, os, re, subprocess, difflib, collections, json
D = os.path.dirname(os.path.abspath(__file__))
DBG = os.path.expanduser('~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/llc')
SDK = os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
LLC = ['-O3', '-relocation-model=pic', '-mattr=+store-imm,+jmp-ext', '-function-sections']


def dis_obj(o):
    h = subprocess.run([SDK + '/llvm-objdump', '-h', o], capture_output=True, text=True).stdout
    sec = re.search(r'\.text\.\S*admin_cto7execute\S*', h).group(0)
    d = subprocess.run([SDK + '/llvm-objdump', '-d', '--no-show-raw-insn', o, '--section=' + sec], capture_output=True, text=True).stdout
    res = []
    for l in d.split('\n'):
        m = re.match(r'\s*(\d+):\s+(.*)', l)
        if m: res.append((int(m.group(1)) * 8, m.group(2).strip()))
    return res


def read_dis(p):
    return [(int(l.split()[0], 16), l.split(None, 1)[1].strip()) for l in open(p) if l.strip()]


def n2(s):
    s = re.sub(r'\s+<[^>]*>', '', s)
    if s.startswith('call'): return 'call'
    s = re.sub(r'^lddw (r\d+), .*', r'lddw \1', s)
    s = re.sub(r'r10 - 0x[0-9a-f]+', 'FP', s)
    if s.startswith('j'): s = re.sub(r'([+-]0x[0-9a-f]+|[+-]\d+)$', 'J', s)
    s = re.sub(r'\br[0-9]\b', 'R', s)
    return s


SP = re.compile(r'^stxdw \[r10 - (0x[0-9a-f]+)\], (r\d)$')
RL = re.compile(r'^ldxdw (r\d), \[r10 - (0x[0-9a-f]+)\]$')


def parse_log(log):
    g = log[log.index('GREEDY REGISTER ALLOCATION'):]
    mi = g[g.index('MACHINEINSTRS'):]
    mi = mi[:mi.index('\n\n# End machine code') if '\n\n# End machine code' in mi else len(mi)]
    # vreg defs in the greedy-start MIR
    defs = collections.defaultdict(list); bb = None
    for l in mi.split('\n'):
        m = re.match(r'^\d+B\t(bb\.\d+[.\w]*)', l)
        if m: bb = m.group(1); continue
        m = re.match(r'^(\d+)B\t\s+(%\d+)(?::gpr)? = (.*)', l)
        if m: defs[m.group(2)].append((bb, m.group(1), m.group(3)[:110]))
    # SS -> originals
    ss = collections.defaultdict(set); cur = None; orig = None
    for l in g.split('\n'):
        m = re.match(r'^Inline spilling GPR:(%\d+)', l)
        if m: cur = m.group(1); orig = cur; continue
        m = re.match(r'^From original (%\d+)', l)
        if m: orig = m.group(1); continue
        m = re.match(r'^Merged spilled regs: SS#(\d+)', l)
        if m and orig: ss[int(m.group(1))].add(orig)
    col = {}
    for a, b in re.findall(r'^Assigning fi#(\d+) to fi#(\d+)', log, re.M): col[int(a)] = int(b)
    off = {int(a): -int(b) for a, b in re.findall(r'^alloc FI\((\d+)\) at SP\[(-?\d+)\]', log, re.M)}
    slot = collections.defaultdict(set)  # r10 offset -> originals
    for s, vs in ss.items():
        f = col.get(s, s)
        if f in off: slot[off[f]] |= vs
    return defs, dict(slot), ss


def desc(defs, v):
    d = defs.get(v, [])
    if not d: return v + ' ?'
    bb, i, t = d[0]
    return '%s=%s @%s %s%s' % (v, t, i, bb, (' (+%d defs)' % (len(d) - 1)) if len(d) > 1 else '')


def main():
    a = sys.argv[1:]; rx = a.pop(0); op = os.path.join(os.path.dirname(D), 'orig.txt'); jo = None
    while a:
        x = a.pop(0)
        if x == '--orig': op = a.pop(0)
        elif x == '--json': jo = a.pop(0)
    m = os.path.join(rx, 'm.ll'); o = os.path.join(rx, 'dbg.o')
    r = subprocess.run([DBG, *LLC, m, '-filetype=obj', '-o', o, '-debug-only=regalloc,prologepilog,stack-slot-coloring'], capture_output=True, text=True)
    log = r.stderr; open(os.path.join(rx, 'ra.log'), 'w').write(log)
    C = dis_obj(o); O = read_dis(op)
    r2 = subprocess.run([DBG, *LLC, m, '-filetype=obj', '-o', o + '.ns', '-no-stack-slot-sharing', '-debug-only=regalloc,prologepilog,stack-slot-coloring'], capture_output=True, text=True)
    defs, slot, ss = parse_log(r2.stderr)
    NS = dis_obj(o + '.ns'); assert len(NS) == len(C), (len(NS), len(C))
    # per-instruction value set from the unshared frame
    ival = {}
    for (a1, s1), (a2, s2) in zip(C, NS):
        mm = SP.match(s2) or RL.match(s2)
        if mm:
            x = int(mm.group(1) if s2.startswith('st') else mm.group(2), 16)
            if x in slot: ival[a1] = slot[x]
    on = [n2(s) for _, s in O]; cn = [n2(s) for _, s in C]
    sm = difflib.SequenceMatcher(None, on, cn, autojunk=False)
    # aligned spill/reload pairs -> orig slot -> ours slot votes
    vote = collections.defaultdict(collections.Counter); near = collections.defaultdict(list)
    only = {'orig_reload': [], 'ours_reload': [], 'orig_spill': [], 'ours_spill': []}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            for k in range(i2 - i1):
                so, sc = O[i1 + k][1], C[j1 + k][1]
                mo = SP.match(so) or RL.match(so); mc = SP.match(sc) or RL.match(sc)
                if mo and mc:
                    xo = int((mo.group(1) if so.startswith('st') else mo.group(2)), 16)
                    xc = int((mc.group(1) if sc.startswith('st') else mc.group(2)), 16)
                    vote[xo][xc] += 1
                    if C[j1 + k][0] in ival: near[xo].append((i1 + k, ival[C[j1 + k][0]]))
        else:
            for k in range(i1, i2):
                s = O[k][1]
                if SP.match(s): only['orig_spill'].append((O[k][0], s, int(SP.match(s).group(1), 16), j1))
                elif RL.match(s): only['orig_reload'].append((O[k][0], s, int(RL.match(s).group(2), 16), j1))
            for k in range(j1, j2):
                s = C[k][1]
                if SP.match(s): only['ours_spill'].append((C[k][0], s, int(SP.match(s).group(1), 16), i1))
                elif RL.match(s): only['ours_reload'].append((C[k][0], s, int(RL.match(s).group(2), 16), i1))
    o2c = {xo: c.most_common(1)[0][0] for xo, c in vote.items()}
    res = {'slots': {}, 'only': {}}
    for x, vs in sorted(slot.items()):
        res['slots'][hex(x)] = [desc(defs, v) for v in sorted(vs, key=lambda q: int(q[1:]))]
    print('spill slots (ours r10 offset -> originals): %d' % len(slot))
    for k in only:
        print('\n== %s (%d)' % (k, len(only[k])))
        res['only'][k] = []
        for addr, s, x, other in only[k]:
            if k.startswith('orig'):
                xc = o2c.get(x); nn = near.get(x, [])
                oi = next(q for q in range(len(O)) if O[q][0] == addr)
                vs = min(nn, key=lambda t: abs(t[0] - oi))[1] if nn else set()
                tag = 'orig@%04x %s | ~ours@%04x slot->%s' % (addr, s, C[other][0] if other < len(C) else -1, hex(xc) if xc else '?')
            else:
                vs = ival.get(addr, set()); tag = 'ours@%04x %s | ~orig@%04x' % (addr, s, O[other][0] if other < len(O) else -1)
            ds = [desc(defs, v) for v in sorted(vs, key=lambda q: int(q[1:]))]
            print(tag); [print('     ', d) for d in ds[:3]]
            res['only'][k].append({'addr': addr, 'insn': s, 'values': ds})
    # per-value traffic: ours from ival, orig via nearest aligned pair of the same orig slot
    tv = collections.defaultdict(lambda: [0, 0, 0, 0])
    for a1, s1 in C:
        if a1 in ival:
            k = '; '.join(desc(defs, v)[:70] for v in sorted(ival[a1], key=lambda q: int(q[1:]))[:2])
            tv[k][0 if s1.startswith('st') else 1] += 1
    for oi, (a0, s0) in enumerate(O):
        mm = SP.match(s0) or RL.match(s0)
        if not mm: continue
        x = int(mm.group(1) if s0.startswith('st') else mm.group(2), 16)
        nn = near.get(x, [])
        if not nn: tv['(orig slot -%#x unpaired)' % x][2 if s0.startswith('st') else 3] += 1; continue
        vs = min(nn, key=lambda t: abs(t[0] - oi))[1]
        k = '; '.join(desc(defs, v)[:70] for v in sorted(vs, key=lambda q: int(q[1:]))[:2])
        tv[k][2 if s0.startswith('st') else 3] += 1
    print('\n== per-value traffic: ours st/ld | orig st/ld (orig via nearest aligned pair)')
    for k, t in sorted(tv.items(), key=lambda kv: -abs((kv[1][2] + kv[1][3]) - (kv[1][0] + kv[1][1]))):
        print('%3d/%3d | %3d/%3d  %+4d  %s' % (t[0], t[1], t[2], t[3], (t[2] + t[3]) - (t[0] + t[1]), k))
    res['pervalue'] = {k: t for k, t in tv.items()}
    print('\nratio(n2)=%.5f' % sm.ratio())
    if jo: json.dump(res, open(jo, 'w'), indent=1)


main()
