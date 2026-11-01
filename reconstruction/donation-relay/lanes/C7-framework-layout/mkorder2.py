#!/usr/bin/env python3
"""mkorder2.py <unstripped.so> <link.map> [--check] > ordered.ld

mkorder.py with one blocker fixed. relay.compare pairs functions by normalized body, and bodies are not unique: the (u64, u64) and (usize, usize)
with_values instances, the Signer::try_accounts instances, the classic and interface Account::reload instances and others are identical. A wrong pair
scores the same but lays the instance out at the other's address, so every call to it differs in the final ELF.

Each ambiguous group is resolved from evidence the ordered link has to reproduce anyway:
  callers  the k-th call of a paired caller on both sides must reach the paired instance
  callees  an instance is excluded when a paired callee differs
  data     relocated lddw and .data.rel.ro words must agree on content; a .data.rel.ro word that points into .text pairs the two functions
Selectors keep this build's symbol hashes, so regenerate after any source change, from a link.map of the same host.

--check prints the pairing report to stderr and writes no script."""
import collections, os, re, struct, sys
sys.path.insert(0, os.path.expanduser('~/.cache/pumpfun-reconstruction/relay/tools'))
import relay
from relaylib import demangle


def refine(t, c, sy, tf, tn, cn, log=None):
    """Return {target addr: candidate addr}, resolved beyond normalized-body equality, plus the groups left ambiguous."""
    rt, rc = relay.Ro(t), relay.Ro(c)
    tsize = dict(tf)
    groups_t, groups_c = collections.defaultdict(list), collections.defaultdict(list)
    for a, s in tf:
        groups_t[(s, tn[a][0])].append(a)
    for b, (s, _) in sy.items():
        groups_c[(s, cn[b][0])].append(b)
    P = {}; used = set(); amb = {}
    for k, ta in groups_t.items():
        tc = groups_c.get(k, [])
        if len(ta) == 1 and len(tc) == 1:
            P[ta[0]] = tc[0]; used.add(tc[0])
        elif tc:
            amb[k] = (set(ta), set(tc))
    # .data.rel.ro: the same section layout pairs functions reached through pointers (vtables, function tables)
    dt, dc = t.sec.get('.data.rel.ro'), c.sec.get('.data.rel.ro')
    votes = collections.Counter()
    if dt and dc and dt['size'] == dc['size']:
        for off in range(0, dt['size'], 8):
            at, ac = dt['addr'] + off, dc['addr'] + off
            if at in t.rel and ac in c.rel:
                vt, vc = t.ptr(at), c.ptr(ac)
                if t.ta <= vt < t.ta + t.tn and c.ta <= vc < c.ta + c.tn:
                    votes[(vt, vc)] += 1

    def possible(a, b):
        """False when known evidence excludes the pair a->b."""
        for x, y in zip(tn[a][1], cn[b][1]):
            if x in P and P[x] != y:
                return False
        for x, y in zip(tn[a][3], cn[b][3]):
            if not relay.content_equal(rt, x, rc, y):
                return False
        return True

    for _round in range(40):
        changed = 0
        for (vt, vc), n in votes.items():
            if vt not in P and vc not in used:
                for k, (ta, tc) in amb.items():
                    if vt in ta and vc in tc:
                        P[vt] = vc; used.add(vc); ta.discard(vt); tc.discard(vc); changed += 1
                        break
        # caller evidence: paired callers vote for their k-th callee
        cv = collections.Counter()
        for a, _s in tf:
            b = P.get(a)
            if b is None:
                continue
            for x, y in zip(tn[a][1], cn[b][1]):
                if x not in P and y not in used:
                    cv[(x, y)] += 1
        for k, (ta, tc) in amb.items():
            for a in sorted(ta):
                cand = [b for b in tc if possible(a, b)]
                if len(cand) > 1:
                    best = [b for b in cand if cv[(a, b)] > 0]
                    if best:
                        cand = best
                if len(cand) == 1:
                    P[a] = cand[0]; used.add(cand[0]); ta.discard(a); tc.discard(cand[0]); changed += 1
            # the last one left in a group
            if len(ta) == 1 and len(tc) == 1:
                a, b = next(iter(ta)), next(iter(tc))
                if possible(a, b):
                    P[a] = b; used.add(b); ta.clear(); tc.clear(); changed += 1
        if not changed:
            break
    # what is left is automorphic as far as this evidence goes: pair in address order and report it
    left = []
    for k, (ta, tc) in amb.items():
        if ta and tc:
            left.append((sorted(ta), sorted(tc)))
            for a, b in zip(sorted(ta), sorted(tc)):
                P[a] = b; used.add(b)
    return P, left


def conflicts(t, c, tf, tn, cn, P):
    """Pairs whose callees disagree under the final pairing, i.e. calls that will differ in the ordered ELF."""
    bad = []
    for a, _s in tf:
        b = P.get(a)
        if b is None:
            continue
        for x, y in zip(tn[a][1], cn[b][1]):
            if x in P and P[x] != y:
                bad.append((a, b, x, y)); break
    return bad


def main():
    args = [x for x in sys.argv[1:] if not x.startswith('--')]
    check = '--check' in sys.argv
    cand, lm = args[:2]
    t, c, sy, tf, tn, cn, pair0, idx = relay.compare(cand)
    P, left = refine(t, c, sy, tf, tn, cn)
    moved = sum(1 for a in P if pair0.get(a) != P[a])
    bad = conflicts(t, c, tf, tn, cn, P)
    print(f'{len(P)} paired of {len(tf)}, {moved} differ from relay.compare, {len(left)} groups left ambiguous, {len(bad)} functions with conflicting callees', file=sys.stderr)
    for ta, tc in left:
        print('  ambiguous', [hex(x) for x in ta], [hex(x) for x in tc], demangle(sy[tc[0]][1])[:90], file=sys.stderr)
    for a, b, x, y in bad[:40]:
        print(f'  conflict {a:#x}->{b:#x} {demangle(sy[b][1])[:70]}: callee {x:#x} paired {P[x]:#x}, candidate calls {y:#x}', file=sys.stderr)
    un = [a for a, _ in tf if a not in P]
    if un:
        print('  unpaired', [hex(a) for a in un], file=sys.stderr)
    if check:
        return
    sec = {}
    pat = re.compile(r'^\s*([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+(\d+)\s+(\S.*):\((\.text[^)]*)\)\s*$')
    for line in open(lm, errors='replace'):
        m = pat.match(line)
        if m:
            sec[int(m.group(1), 16)] = (m.group(5).strip(), m.group(6))
    out = ['PHDRS', '{', '  text PT_LOAD ;', '  rodata PT_LOAD ;', '  data PT_LOAD ;', '  dynamic PT_DYNAMIC ;', '}', '', 'SECTIONS', '{', '  . = SIZEOF_HEADERS;', '  .text : {']
    miss = 0
    for a, _ in tf:
        b = P.get(a)
        if b is None:
            continue
        s = sec.get(b)
        if s is None:
            miss += 1
            print(f'  no map section for {b:#x} {demangle(sy[b][1])[:80]}', file=sys.stderr)
            continue
        obj, name = s
        obj = obj.split('/')[-1]
        m = re.match(r'(.*\.rlib)\((.*)\)$', obj)
        if m:
            obj = m.group(1) + ':' + m.group(2)
        out.append(f'    *{obj}("{name}")')
    out += ['    *(.text*)', '  } :text', '  .rodata : { *(.rodata*) } :rodata', '  .data.rel.ro : { *(.data.rel.ro*) } :rodata', '  .dynamic : { *(.dynamic) } :dynamic', '  .dynsym : { *(.dynsym) } :data',
            '  .dynstr : { *(.dynstr) } :data', '  .rel.dyn : { *(.rel.dyn) } :data', '  /DISCARD/ : {', '      *(.eh_frame*)', '      *(.gnu.hash*)', '      *(.hash*)', '    }', '}']
    print('\n'.join(out))
    print(f'{miss} without a map section', file=sys.stderr)


if __name__ == '__main__':
    main()
