#!/usr/bin/env python3
"""side.py name lo hi [ref]: align orig vs rx/<name> (sk-normalized) and print orig[lo:hi] (byte offs) beside candidate"""
import sys,os,difflib,subprocess
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import absratio as A
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a21-cto-helperbound')
def dis(n):
    t=subprocess.run(['bash',O+'/tools/dis.sh',f'{O}/rx/{n}/m.o'],capture_output=True,text=True).stdout
    return [(int(l.split()[0],16),l.split(None,1)[1]) for l in t.split('\n') if len(l.split(None,1))>1]
ol=[l for l in open(O+'/orig.rel') if len(l.split(None,1))>1]
orig=[(int(l.split()[0],16) if all(c in '0123456789abcdefx' for c in l.split()[0]) else i*8,l.split(None,1)[1].strip()) for i,l in enumerate(ol)]
n=sys.argv[1]; lo=int(sys.argv[2],16); hi=int(sys.argv[3],16)
C=dis(n)
sm=difflib.SequenceMatcher(None,[A.norm(t,True) for _,t in orig],[A.norm(t,True) for _,t in C],autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if orig[min(i1,len(orig)-1)][0]>hi or (i2<len(orig) and orig[i2-1][0]<lo and i2>i1): continue
    if tag=='equal':
        for k in range(i2-i1):
            a=orig[i1+k]; b=C[j1+k]
            if lo<=a[0]<=hi: print(f'{a[0]:05x} {a[1][:44]:44s} | {b[0]:05x} {b[1][:44]}' + ('' if a[1].split('<')[0].strip()==b[1].split('<')[0].strip() else '  *'))
    else:
        L=max(i2-i1,j2-j1)
        for k in range(L):
            a=orig[i1+k] if i1+k<i2 else None; b=C[j1+k] if j1+k<j2 else None
            anc=a[0] if a else orig[min(i1,len(orig)-1)][0]
            if not lo<=anc<=hi: continue
            print(f'{(a[0] if a else 0):05x} {(a[1][:44] if a else ""):44s} # {(b[0] if b else 0):05x} {(b[1][:44] if b else "")}  {tag}')
