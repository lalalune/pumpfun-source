#!/usr/bin/env python3
"""mut.py IN.ll OUTDIR [--kinds icmp,br,add,hoist,sink] : generate single IR mutations of swap_hop as edit files list (json)."""
import sys, re, os, json
sys.path.insert(0, os.path.dirname(__file__)); import blk
SW = {'eq':'eq','ne':'ne','ugt':'ult','ult':'ugt','uge':'ule','ule':'uge','sgt':'slt','slt':'sgt','sge':'sle','sle':'sge'}
INV = {'eq':'ne','ne':'eq','ugt':'ule','ule':'ugt','ult':'uge','uge':'ult','sgt':'sle','sle':'sgt','slt':'sge','sge':'slt'}
DEF = re.compile(r'^\s+(%[\w.\-]+) = ')
USE = re.compile(r'%[\w.\-]+')
def muts(t, kinds):
    pre, hdr, blocks, post = blk.split(t)
    out = []
    # use counts
    uses = {}
    for b in blocks:
        for l in b[1]:
            d = DEF.match(l); rhs = l[d.end():] if d else l
            for u in USE.findall(rhs): uses[u] = uses.get(u, 0) + 1
    for bi, b in enumerate(blocks):
        L = b[1]
        for li, l in enumerate(L):
            m = re.match(r'^(\s+%[\w.\-]+ = icmp )(\w+) (i\d+|ptr) (%[\w.\-]+), (%[\w.\-]+)(.*)$', l)
            if m and 'icmp' in kinds and m.group(2) in SW:
                nl = f'{m.group(1)}{SW[m.group(2)]} {m.group(3)} {m.group(5)}, {m.group(4)}{m.group(6)}'
                out.append((f'icmp:{b[0]}:{li}', bi, li, [nl]))
            m = re.match(r'^(\s+%[\w.\-]+ = (?:add|mul|and|or|xor)(?: nuw| nsw)* )(i\d+) (%[\w.\-]+), (%[\w.\-]+)(.*)$', l)
            if m and 'add' in kinds:
                out.append((f'add:{b[0]}:{li}', bi, li, [f'{m.group(1)}{m.group(2)} {m.group(4)}, {m.group(3)}{m.group(5)}']))
            m = re.match(r'^(\s+br i1 )(%[\w.\-]+), label (%[\w.\-]+), label (%[\w.\-]+)(.*)$', l)
            if m and 'br' in kinds:
                c = m.group(2)
                # find def of c in same block
                for lj in range(li - 1, 0, -1):
                    mm = re.match(r'^(\s+' + re.escape(c) + r' = icmp )(\w+)( .*)$', L[lj])
                    if mm and uses.get(c, 0) == 1 and mm.group(2) in INV:
                        out.append((f'br:{b[0]}:{li}', bi, (lj, li), [f'{mm.group(1)}{INV[mm.group(2)]}{mm.group(3)}', f'{m.group(1)}{c}, label {m.group(4)}, label {m.group(3)}{m.group(5)}']))
                        break
            d = DEF.match(l)
            if d and ('hoist' in kinds or 'sink' in kinds) and not re.search(r' = (phi|alloca|landingpad)', l) and not l.lstrip().startswith(';'):
                name = d.group(1); ops = set(USE.findall(l[d.end():]))
                if re.search(r'= (call|tail call|load)', l) and 'call' in l and not re.search(r'@llvm\.', l): continue
                # hoist: earliest position after last def of ops / after phis; can't pass calls/stores if load
                isload = ' load ' in l
                k = li
                while k - 1 >= 1:
                    p = L[k - 1]; pd = DEF.match(p)
                    if pd and pd.group(1) in ops: break
                    if re.search(r' = phi ', p) or p.strip().startswith(';') and k - 2 >= 1 and False: break
                    if isload and (re.search(r'\b(call|store)\b', p)): break
                    if re.search(r'\bcall\b.*@llvm\.lifetime', p) and name in p: break
                    k -= 1
                while k < li and (L[k].strip() == '' or L[k].lstrip().startswith(';')): k += 1
                if k < li and 'hoist' in kinds:
                    out.append((f'hoist:{b[0]}:{li}->{k}', bi, ('mv', li, k), None))
                # sink: just before first user in block (or before terminator)
                k = li
                while k + 1 < len(L):
                    nx = L[k + 1]
                    if name in USE.findall(nx[DEF.match(nx).end():] if DEF.match(nx) else nx): break
                    if re.match(r'^\s+(br|ret|switch|unreachable|resume)\b', nx): break
                    if isload and re.search(r'\b(call|store)\b', nx): break
                    k += 1
                if k > li and 'sink' in kinds:
                    out.append((f'sink:{b[0]}:{li}->{k}', bi, ('mv', li, k), None))
    return pre, hdr, blocks, post, out
def apply(pre, hdr, blocks, post, m):
    name, bi, where, new = m
    B = [[b[0], list(b[1])] for b in blocks]; L = B[bi][1]
    if isinstance(where, tuple) and where[0] == 'mv':
        _, s, d = where; x = L.pop(s)
        # also carry a preceding comment line? skip
        L.insert(d if d < s else d, x)
    elif isinstance(where, tuple):
        for idx, nl in zip(where, new): L[idx] = nl
    else: L[where] = new[0]
    return blk.join(pre, hdr, B, post)
