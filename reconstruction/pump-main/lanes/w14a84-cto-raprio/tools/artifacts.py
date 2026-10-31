#!/usr/bin/env python3
"""artifacts.py <fn.bin> [--orig orig.bin] [--json]: list register-allocator split artifacts in admin_cto::execute.
 dead   : ldxdw rX,[r10-s] whose rX is overwritten before any read (same straight-line run, no branch in between)
 restore: ldxdw rX,[r10-a] whose only use is stxdw [r10-b],rX before rX is overwritten (spill-slot copy)
 Each site is tagged with its enclosing Rc-increment block (ldxdw rA,[rB+0]; add64 rA,1 within 8 insns before)."""
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bdis import decode


def is_branch(d):
    return d['cls'] == 5 and d['txt'].split()[0] not in ('call',)


def scan(raw):
    ins = decode(raw); res = []
    for k, d in enumerate(ins):
        if not (d['op'] == 0x79 and d['src'] == 10): continue
        r = d['dst']; kind = None; partner = None
        for j in range(k + 1, min(k + 40, len(ins))):
            e = ins[j]
            if r in e['reads']:
                if e['op'] == 0x7b and e['dst'] == 10 and e['src'] == r:
                    # spill copy candidate: check the reg is dead after
                    for q in range(j + 1, min(j + 40, len(ins))):
                        f = ins[q]
                        if r in f['reads']: break
                        if r in f['writes']: kind = 'restore'; partner = e['o']; break
                        if is_branch(f) or f['op'] == 0x95: break
                break
            if r in e['writes']: kind = 'dead'; break
            if is_branch(e) or e['op'] == 0x95: break
        if kind:
            # Rc block: look back for "ldxdw rA,[rB+0]; add64 rA,1"
            rc = None
            for j in range(k - 1, max(-1, k - 12), -1):
                e = ins[j]
                if e['op'] == 0x07 and e['imm'] == 1 and j > 0 and ins[j - 1]['op'] == 0x79 and ins[j - 1]['o'] == 0 \
                        and ins[j - 1]['dst'] == e['dst']:
                    rc = ins[j - 1]['off']; break
            res.append(dict(off=d['off'], kind=kind, reg=r, slot=d['o'], to=partner, rc=rc))
    return res


def group(res):
    out = []; cur = None
    for a in res:
        if cur and a['off'] - cur['end'] <= 8 and a['kind'] == cur['kind'] and a['reg'] == cur['reg']:
            cur['slots'].append(a['slot']); cur['end'] = a['off']
            if a['to'] is not None: cur['to'].append(a['to'])
        else:
            cur = dict(off=a['off'], end=a['off'], kind=a['kind'], reg=a['reg'], slots=[a['slot']],
                       to=[a['to']] if a['to'] is not None else [], rc=a['rc']); out.append(cur)
    return out


if __name__ == '__main__':
    a = sys.argv[1:]; js = '--json' in a; a = [x for x in a if x != '--json']
    for f in a:
        g = group(scan(open(f, 'rb').read()))
        if js: print(json.dumps({'file': f, 'sites': g})); continue
        print('#', f, len(g), 'sites')
        for s in g:
            print('%04x %-7s r%d %s%s%s' % (s['off'], s['kind'], s['reg'], ' '.join('-0x%x' % -x for x in s['slots']),
                                         (' -> ' + ' '.join('-0x%x' % -x for x in s['to'])) if s['to'] else '',
                                         ('  rc@%04x' % s['rc']) if s['rc'] is not None else ''))


def liveness(raw):
    """Function-level register liveness. Returns (ins, live_out list per insn)."""
    ins = decode(raw); idx = {d['off']: k for k, d in enumerate(ins)}; N = len(ins)
    succ = []
    for k, d in enumerate(ins):
        t = d['txt'].split()[0]; s = []
        if d['cls'] == 5 and t not in ('call',):
            if t == 'exit': pass
            else:
                tgt = d['off'] + d['n'] + d['o'] * 8
                if tgt in idx: s.append(idx[tgt])
                if t != 'ja' and k + 1 < N: s.append(k + 1)
        elif d['op'] == 0x85 and k > 0 and ins[k - 1]['cls'] == 5 and ins[k - 1]['o'] == 1 and ins[k - 1]['imm'] == 1 \
                and ins[k - 1]['txt'].startswith('jne'):
            s = []; d['abort'] = True  # Rc-overflow abort (jne rX,1,+1; call abort): noreturn
        else:
            s = [k + 1] if k + 1 < N else []
        succ.append(s)
    global LAST_SUCC
    LAST_SUCC = succ
    for k, d in enumerate(ins):  # calls: r1-r5 read conservatively; r0-r5 written
        if d['op'] == 0x85: d['reads'] = set() if d.get('abort') else {1, 2, 3, 4, 5}; d['writes'] = {0, 1, 2, 3, 4, 5}
    lin = [set() for _ in range(N)]; lout = [set() for _ in range(N)]
    ch = True
    while ch:
        ch = False
        for k in range(N - 1, -1, -1):
            o = set()
            for s in succ[k]: o |= lin[s]
            i = (o - ins[k]['writes']) | ins[k]['reads']
            if o != lout[k] or i != lin[k]: lout[k] = o; lin[k] = i; ch = True
    return ins, lout


def dead_reloads(raw):
    ins, lout = liveness(raw); res = []
    for k, d in enumerate(ins):
        if d['op'] == 0x79 and d['src'] == 10 and d['dst'] not in lout[k]:
            res.append(dict(off=d['off'], kind='dead', reg=d['dst'], slot=d['o'], to=None, rc=None))
        if d['op'] == 0x79 and d['src'] == 10 and k + 1 < len(ins):
            e = ins[k + 1]
            if e['op'] == 0x7b and e['dst'] == 10 and e['src'] == d['dst'] and e['o'] == d['o']:
                res.append(dict(off=d['off'], kind='self', reg=d['dst'], slot=d['o'], to=e['o'], rc=None))
    for a in res:
        k = [i for i, d in enumerate(ins) if d['off'] == a['off']][0]
        for j in range(k - 1, max(-1, k - 14), -1):
            e = ins[j]
            if e['op'] == 0x07 and e['imm'] == 1 and j > 0 and ins[j - 1]['op'] == 0x79 and ins[j - 1]['o'] == 0 \
                    and ins[j - 1]['dst'] == e['dst']:
                a['rc'] = ins[j - 1]['off']; break
    return res


def reaching(ins, succ, k, r, limit=4000):
    """CFG reaching definitions of register r at instruction k (defs strictly before k on every path)."""
    pred = [[] for _ in ins]
    for i, ss in enumerate(succ):
        for j in ss: pred[j].append(i)
    seen = set(); out = set(); st = list(pred[k])
    while st and len(seen) < limit:
        j = st.pop()
        if j in seen: continue
        seen.add(j)
        if r in ins[j]['writes']: out.add(j); continue
        st.extend(pred[j])
    return sorted(out)
