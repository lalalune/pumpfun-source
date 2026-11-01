#!/usr/bin/env python3
"""cdiff.py <a fn.bin> <b fn.bin> [ctx]: difflib opcodes between two candidate blobs (unmasked disassembly), plus per-side M vs orig."""
import sys,os,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import oracle,sbpfdis
a=open(sys.argv[1],'rb').read(); b=open(sys.argv[2],'rb').read(); cx=int(sys.argv[3]) if len(sys.argv)>3 else 2
da=sbpfdis.d(a); db=sbpfdis.d(b)
import re
norm=lambda s: re.sub(r'(j\w+ .*?)[0-9a-f]+$',r'\1J',s) if s.startswith('j') else s
A=[norm(s) for _,s in da]; B=[norm(s) for _,s in db]
sm=difflib.SequenceMatcher(None,A,B,autojunk=False)
n=0
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': continue
    n+=1
    if n>40: print('...'); break
    print(f'== {tag} a[{i1}:{i2}] @{da[i1][0] if i1<len(da) else -1:#x} b[{j1}:{j2}] @{db[j1][0] if j1<len(db) else -1:#x}')
    for k in range(max(0,i1-cx),i1): print('    ',f'{da[k][0]:#7x}',A[k])
    for k in range(i1,min(i2,i1+15)): print('   -',f'{da[k][0]:#7x}',A[k])
    for k in range(j1,min(j2,j1+15)): print('   +',f'{db[k][0]:#7x}',B[k])
