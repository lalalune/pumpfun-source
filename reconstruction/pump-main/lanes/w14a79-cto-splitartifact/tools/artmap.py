#!/usr/bin/env python3
"""artmap.py <rxdir> [--orig orig.txt] [--lo 0x2800 --hi 0x4000]: split-artifact map for admin_cto::execute (experiment only).
For every dead stack reload / same-slot reload+re-spill (artifacts.dead_reloads) in ours (rxdir/fn.bin) and in the original,
name the spilled LLVM value: ours directly (unshared-frame twin, lr.py), orig via the L2-aligned orig->ours slot votes and the
nearest aligned access of that orig slot. Prints per Rc block {block: live-through spilled values} for both sides and the diff."""
import sys, os, re, subprocess, difflib, collections, json
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
src = open(D + '/lr.py').read(); g = {'__name__': 'lr', '__file__': D + '/lr.py'}; exec(src[:src.index('def main')], g)
from artifacts import dead_reloads, group
a = sys.argv[1:]; rx = a.pop(0); op = None; lo, hi = 0, 1 << 20
while a:
    x = a.pop(0)
    if x == '--orig': op = a.pop(0)
    elif x == '--lo': lo = int(a.pop(0), 0)
    elif x == '--hi': hi = int(a.pop(0), 0)
op = op or os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a79-cto-splitartifact/orig.txt')
m = os.path.join(rx, 'm.ll'); o = os.path.join(rx, 'dbg.o')
FL = ['-debug-only=regalloc,prologepilog,stack-slot-coloring']
if not os.path.exists(o + '.ns.log'):
    subprocess.run([g['DBG'], *g['LLC'], m, '-filetype=obj', '-o', o], capture_output=True, text=True)
    r2 = subprocess.run([g['DBG'], *g['LLC'], m, '-filetype=obj', '-o', o + '.ns', '-no-stack-slot-sharing', *FL], capture_output=True, text=True)
    open(o + '.ns.log', 'w').write(r2.stderr)
defs, slot, ss = g['parse_log'](open(o + '.ns.log').read())
C = g['dis_obj'](o); NS = g['dis_obj'](o + '.ns'); assert len(C) == len(NS)
O = [(ad - 0x22a10, s) for ad, s in g['read_dis'](op)]
SP, RL, n2, desc = g['SP'], g['RL'], g['n2'], g['desc']
def acc(s):
    mm = SP.match(s) or RL.match(s)
    return int(mm.group(1) if s.startswith('st') else mm.group(2), 16) if mm else None
ival = {}
for (a1, s1), (a2, s2) in zip(C, NS):
    x = acc(s2)
    if x is not None and x in slot: ival[a1] = slot[x]
# fn.bin must equal dbg.o text
sm = difflib.SequenceMatcher(None, [n2(s) for _, s in O], [n2(s) for _, s in C], autojunk=False)
vote = collections.defaultdict(collections.Counter); near = collections.defaultdict(list); o2c_at = {}
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag != 'equal': continue
    for k in range(i2 - i1):
        xo = acc(O[i1 + k][1]); xc = acc(C[j1 + k][1]); o2c_at[O[i1 + k][0]] = C[j1 + k][0]
        if xo is not None and xc is not None:
            vote[xo][xc] += 1
            if C[j1 + k][0] in ival: near[xo].append((O[i1 + k][0], ival[C[j1 + k][0]]))
def short(v):
    d = desc(defs, v); d = re.sub(r' :: \(.*?\)', '', d); return d[:110]
def ours_vals(addr): return sorted(ival.get(addr, set()), key=lambda q: int(q[1:]))
def orig_vals(addr, x):
    nn = near.get(-x if x < 0 else x, [])
    if not nn: return []
    return sorted(min(nn, key=lambda t: abs(t[0] - addr))[1], key=lambda q: int(q[1:]))
ob = open(os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a79-cto-splitartifact/orig.bin'), 'rb').read()
cb = open(os.path.join(rx, 'fn.bin'), 'rb').read()
out = {'orig': [], 'ours': []}
for side, raw in (('orig', ob), ('ours', cb)):
    for s in dead_reloads(raw):
        if not (lo <= s['off'] < hi): continue
        x = -s['slot']
        vs = orig_vals(s['off'], x) if side == 'orig' else ours_vals(s['off'])
        out[side].append(dict(off=s['off'], kind=s['kind'], reg=s['reg'], slot=x, rc=s['rc'], vals=vs,
                              cslot=(vote[x].most_common(1)[0][0] if side == 'orig' and vote[x] else None)))
for side in ('orig', 'ours'):
    print('==', side)
    for r in out[side]:
        print('%04x %-4s r%d -0x%x%s rc@%s  %s' % (r['off'], r['kind'], r['reg'], r['slot'],
              (' (~ours -0x%x)' % r['cslot']) if r['cslot'] else '', ('%04x' % r['rc']) if r['rc'] is not None else '-',
              ' | '.join(short(v) for v in r['vals'][:2]) or '?'))
vo = collections.Counter(v for r in out['orig'] for v in r['vals'][:1]); vc = collections.Counter(v for r in out['ours'] for v in r['vals'][:1])
print('\n== values named by artifacts: orig-only / ours-only / both')
for v in sorted(set(vo) | set(vc), key=lambda q: int(q[1:])):
    print('%-5s orig %d ours %d  %s' % ('both' if v in vo and v in vc else ('orig' if v in vo else 'ours'), vo[v], vc[v], short(v)))
json.dump(out, open(os.path.join(rx, 'artmap.json'), 'w'), indent=1)
