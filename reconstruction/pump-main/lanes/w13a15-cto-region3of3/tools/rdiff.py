#!/usr/bin/env python3
"""rdiff.py orig.rel cand.rel olo ohi [clo chi] [--frame] [--regs] [-q]: masked diff of a range (relative hex offsets).
(after w13a13-cto-region1of3's rdiff.py; .rel files come from annot.py)"""
import sys,re,difflib
args=[a for a in sys.argv[1:] if not a.startswith('-')]
fr='--frame' in sys.argv; rg='--regs' in sys.argv
def load(p):
    out=[]
    for l in open(p):
        a,rest=l.rstrip('\n').split(None,1); out.append((int(a,16),rest))
    return out
def ab(s):
    lab=s.split(';')[1].strip()[:40] if ';' in s else ''
    s=re.sub(r'\s*<[^>]*>$','',s.split(';')[0].strip())
    if s.startswith('call'): s='call '+lab
    s=re.sub(r'lddw (r\d+), 0x[0-9a-f]+',r'lddw \1, X',s)
    s=re.sub(r'^(j\w+ .*)[+-]0x[0-9a-f]+$',r'\1J',s)
    if fr: s=re.sub(r'r10 - 0x[0-9a-f]+','FP',s); s=re.sub(r'^add64 (r\d+), -0x[0-9a-f]+$',r'add64 \1, -A',s)
    if rg: s=re.sub(r'\br[0-9]\b','R',s)
    return s
O=load(args[0]); C=load(args[1])
olo,ohi=int(args[2],16),int(args[3],16)
clo,chi=(int(args[4],16),int(args[5],16)) if len(args)>5 else (olo,ohi)
o=[x for x in O if olo<=x[0]<ohi]; c=[x for x in C if clo<=x[0]<chi]
sm=difflib.SequenceMatcher(None,[ab(x[1]) for x in o],[ab(x[1]) for x in c],autojunk=False)
print('ratio',round(sm.ratio(),4),len(o),len(c))
if '-q' in sys.argv: sys.exit()
for t,i1,i2,j1,j2 in sm.get_opcodes():
    if t=='equal':
        print(f'  = {i2-i1} same ({o[i1][0]:05x}..{o[i2-1][0]:05x} / {c[j1][0]:05x}..)'); continue
    for x in o[i1:i2]: print(f'- {x[0]:05x} {x[1]}')
    for x in c[j1:j2]: print(f'+ {x[0]:05x} {x[1]}')
