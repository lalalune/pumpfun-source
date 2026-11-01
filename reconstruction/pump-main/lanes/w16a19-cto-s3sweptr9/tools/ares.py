#!/usr/bin/env python3
"""ares.py <in.mir> <out.mir> [--ref r3,r7] [--dry]: automatic join-restore oracle (experiment only).
Generalises w15a20 restore.sh / mired2.py and w14a142 restore.sh: on pre-branch-folder MIR, find the post-sweep Result
join bb56.i (2 successors, one of them bb88/bb78), take its live-ins beyond REF (main's $r3,$r7), and for each extra
register X: delete X's last def (a reload `$X = LDD_V1 $r10, S` or a `$X = COPY ...`) in every block that feeds the join
with X live (direct preds, and pass-through feeders such as bb52.i*), drop X from those blocks' live-ins, and reload X
(`$X = LDD_V1 $r10, S`, S = the most common reload slot) at the head of each join successor that has X live-in.
Prints a JSON line describing what it did."""
import sys, re, json
from collections import Counter
a = sys.argv[1:]; src, dst = a[0], a[1]
REF = {'$' + x for x in (a[a.index('--ref') + 1].split(',') if '--ref' in a else ['r3', 'r7'])}
dry = '--dry' in a
L = open(src).read().split('\n')
# locate function body blocks: lines '  bb.N.name:' or '  bb.N:' (attrs in parens possible)
hdr = re.compile(r'^  bb\.(\d+)(?:\.([^\s:(]*))?(?: \(([^)]*)\))?:\s*$')
blocks = {}; order = []; cur = None
for i, l in enumerate(L):
    m = hdr.match(l)
    if m:
        cur = int(m.group(1)); blocks[cur] = {'name': m.group(2) or '', 'start': i, 'succ': [], 'live': None, 'liveline': None}
        order.append(cur); continue
    if cur is None: continue
    s = l.strip()
    if s.startswith('successors:'):
        blocks[cur]['succ'] = [int(x) for x in re.findall(r'%bb\.(\d+)', s)]
    elif s.startswith('liveins:'):
        blocks[cur]['live'] = set(re.findall(r'\$r\d+', s)); blocks[cur]['liveline'] = i
for k, b in blocks.items():
    nxt = [blocks[o]['start'] for o in order if blocks[o]['start'] > b['start']]
    b['end'] = min(nxt) if nxt else len(L)
def preds(x): return [k for k, b in blocks.items() if x in b['succ']]
J = [k for k, b in blocks.items() if re.fullmatch(r'bb56\.i\d*', b['name']) and len(b['succ']) == 2
     and any(re.fullmatch(r'bb(88|78)', blocks[s]['name']) for s in b['succ'])]
rep = {'joins': [], 'deleted': 0, 'inserted': 0}
dele = set(); ins = {}; live_drop = {}
for j in J:
    lj = blocks[j]['live'] or set(); extra = sorted(lj - REF)
    rec = {'join': j, 'name': blocks[j]['name'], 'liveins': sorted(lj), 'extra': extra, 'npred': len(preds(j))}
    for X in extra:
        # feeders: walk back from j through blocks that have X live-in and do not define X
        feed = []; seen = set(); stack = [j]
        while stack:
            t = stack.pop()
            for p in preds(t):
                if p in seen: continue
                seen.add(p)
                body = L[blocks[p]['start'] + 1:blocks[p]['end']]
                defs = [(blocks[p]['start'] + 1 + q, s.strip()) for q, s in enumerate(body) if re.match(r'\s*(dead )?' + re.escape(X) + r' = ', s)]
                if defs: feed.append((p, defs[-1]))
                elif blocks[p]['live'] and X in blocks[p]['live']:
                    live_drop.setdefault(p, set()).add(X); stack.append(p)
        slots = Counter()
        for p, (li, s) in feed:
            m = re.fullmatch(re.escape(X) + r' = LDD_V1 \$r10, (-?\d+)', s)
            if m: slots[int(m.group(1))] += 1
        kinds = Counter()
        for p, (li, s) in feed:
            if re.fullmatch(re.escape(X) + r' = (LDD_V1 \$r10, -?\d+|COPY( killed)? \$r\d+)', s):
                dele.add(li); kinds['LDD' if 'LDD' in s else 'COPY'] += 1
            else:
                kinds['other:' + s[:40]] += 1
        S = slots.most_common(1)[0][0] if slots else None
        pure = (slots.most_common(1)[0][1] if slots else 0) + kinds.get('COPY', 0)
        if pure * 2 < max(1, len(feed)):
            for p, (li, s_) in feed: dele.discard(li)
            rec.setdefault('kept', []).append({'reg': X, 'feeders': len(feed), 'kinds': dict(kinds)}); continue
        live_drop.setdefault(j, set()).add(X)
        rec.setdefault('fix', []).append({'reg': X, 'slot': S, 'feeders': len(feed), 'kinds': dict(kinds)})
        if S is not None:
            for s in blocks[j]['succ']:
                if blocks[s]['live'] and X in blocks[s]['live']:
                    ins.setdefault(s, []).append(f'{X} = LDD_V1 $r10, {S}')
    rep['joins'].append(rec)
out = []
for i, l in enumerate(L):
    if i in dele: rep['deleted'] += 1; continue
    blk = None
    for k, b in blocks.items():
        if b['liveline'] == i: blk = k
    if blk is not None and blk in live_drop and '--live' in a:
        regs = [r for r in re.findall(r'\$r\d+', l) if r not in live_drop[blk]]
        l = '    liveins: ' + ', '.join(regs) if regs else None
        if l is None: continue
    out.append(l)
    m = hdr.match(L[i]) if i < len(L) else None
# insert reloads at the head of the body (after the header, successors and liveins lines)
res = []; i = 0; cur = None; pend = []
for l in out:
    m = hdr.match(l)
    if m:
        cur = int(m.group(1)); pend = list(ins.get(cur, [])); res.append(l); continue
    s = l.strip()
    if pend and not (s.startswith('successors:') or s.startswith('liveins:') or s == ''):
        for x in pend: res.append('    ' + x); rep['inserted'] += 1
        pend = []
    res.append(l)
if not dry: open(dst, 'w').write('\n'.join(res))
print(json.dumps(rep))
