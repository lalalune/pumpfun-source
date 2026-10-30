#!/usr/bin/env python3
"""blkdiff.py A.ll B.ll: align swap_hop blocks by a name-free signature and print block-level differences."""
import re, sys, difflib
fn='multi_hop_curve8swap_hop17h'
def blocks(p):
    t=open(p).read(); m=re.search(r'^define[^\n]*'+fn+r'[^\n]*$',t,re.M); s=m.end(); e=t.index('\n}\n',s)
    out=[]
    for b in t[s:e].strip('\n{').split('\n\n'):
        lines=[l for l in b.split('\n') if l.strip() and not l.startswith(';')]
        lab=re.match(r'^("?[\w.$-]+"?):',lines[0]); name=lab.group(1) if lab else 'ENTRY'
        body=lines[1:] if lab else lines
        sig=[]
        for l in body:
            l=l.strip()
            l=re.sub(r'%("[^"]+"|[\w.$-]+)','%',l); l=re.sub(r'!\d+','!',l); l=re.sub(r'#\d+','#',l)
            sig.append(l)
        out.append((name,'\n'.join(sig),b))
    return out
A,B=blocks(sys.argv[1]),blocks(sys.argv[2])
sm=difflib.SequenceMatcher(None,[x[1] for x in A],[x[1] for x in B],autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': continue
    print(f'== {tag} A[{i1}:{i2}] B[{j1}:{j2}]')
    for k in range(i1,i2): print('--- A', A[k][0]); print('\n'.join('  - '+l for l in A[k][2].split('\n')[:40]))
    for k in range(j1,j2): print('+++ B', B[k][0]); print('\n'.join('  + '+l for l in B[k][2].split('\n')[:40]))
