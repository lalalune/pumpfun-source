#!/usr/bin/env python3
"""mdiff.py A.bin B.bin [--lo hex --hi hex] [-c ctx]: masked listing diff (call imm, lddw imm and jump offsets masked)."""
import sys,os,re,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import bdis
def norm(t):
    t=re.sub(r'call -?0x[0-9a-f]+','call X',t); t=re.sub(r'^(lddw r\d+), .*',r'\1, X',t)
    t=re.sub(r', [+-]0x[0-9a-f]+$',', J',t); t=re.sub(r'^ja .*','ja J',t); return t
a=sys.argv[1:]; lo,hi,ctx=0,1<<30,0
if '--lo' in a: i=a.index('--lo'); lo=int(a[i+1],16); del a[i:i+2]
if '--hi' in a: i=a.index('--hi'); hi=int(a[i+1],16); del a[i:i+2]
if '-c' in a: i=a.index('-c'); ctx=int(a[i+1]); del a[i:i+2]
A=bdis.dis(open(a[0],'rb').read()); B=bdis.dis(open(a[1],'rb').read())
sm=difflib.SequenceMatcher(None,[norm(x[1]) for x in A],[norm(x[1]) for x in B],autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': continue
    pa=A[i1][0] if i1<len(A) else A[-1][0]; pb=B[j1][0] if j1<len(B) else B[-1][0]
    if not (lo<=pb<hi or lo<=pa<hi): continue
    print(f'@@ A {pa:#06x} B {pb:#06x} {tag} {i2-i1}/{j2-j1}')
    for k in range(max(0,i1-ctx),i1): print(f'   {A[k][0]:#06x}  {A[k][1]}')
    for k in range(i1,i2): print(f' - {A[k][0]:#06x}  {A[k][1]}')
    for k in range(j1,j2): print(f' + {B[k][0]:#06x}  {B[k][1]}')
