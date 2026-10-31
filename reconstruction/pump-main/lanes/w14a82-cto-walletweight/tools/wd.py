#!/usr/bin/env python3
"""wd.py <cand.dis|m.ll> [lo hi] : align orig wallet [lo,hi) (default 0x5b30..0x6b08) to cand by structure (regs/frame/jumps masked),
then classify aligned pairs: equal / reg-only / frame-only / jump-only / mixed. Prints counts and reg-diff pairs (-v)."""
import sys,re,difflib,subprocess,os
T=os.path.dirname(os.path.abspath(__file__))
def clean(s): return re.sub(r'\s*<[^>]*>','',s).strip()
def struct(s):
    s=clean(s)
    if s.startswith('call'): return 'call'
    s=re.sub(r'\br\d\b','R',s); s=re.sub(r'R - 0x[0-9a-f]+','FP',s)
    s=re.sub(r'^(add64 R), -0x[0-9a-f]+$',r'\1, -FP',s)
    if s.startswith('lddw'): s='lddw R'
    if s.startswith('j'): s=re.sub(r'[+-]0x[0-9a-f]+$','J',s)
    return s
def fm(s):
    s=clean(s)
    if s.startswith('call'): return 'call'
    if s.startswith('lddw'): return re.sub(r'0x[0-9a-f]+','IMM',s)
    s=re.sub(r'r10 - 0x[0-9a-f]+','FP',s); s=re.sub(r'^(add64 r\d+), -0x[0-9a-f]+$',r'\1, -FP',s)
    if s.startswith('j'): s=re.sub(r'[+-]0x[0-9a-f]+$','J',s)
    return s
def rm(s):
    s=clean(s)
    if s.startswith('call'): return 'call'
    if s.startswith('lddw'): return 'lddw '+s.split()[1]
    s=re.sub(r'\br\d\b','R',s)
    if s.startswith('j'): s=re.sub(r'[+-]0x[0-9a-f]+$','J',s)
    return s
def rd(lines):
    r=[]
    for l in lines:
        q=l.split(None,1)
        if len(q)==2: r.append((int(q[0],16),clean(q[1])))
    return r
a=sys.argv[1:]; v='-v' in a; a=[x for x in a if x!='-v']
p=a[0]; lo=int(a[1],16) if len(a)>1 else 0x5b30; hi=int(a[2],16) if len(a)>2 else 0x6b08
O=[x for x in rd(open(T+'/../or.dis')) if lo<=x[0]<hi]
d=subprocess.run(['bash',T+'/dll.sh',p],capture_output=True,text=True).stdout.split('\n') if p.endswith('.ll') else open(p).read().split('\n')
C=rd(d)
sm=difflib.SequenceMatcher(None,[struct(x[1]) for x in O],[struct(x[1]) for x in C],autojunk=False)
st=dict(eq=0,reg=0,frame=0,jump=0,mixed=0,unaligned=len(O)); regp=[]
for i,j,n in sm.get_matching_blocks():
    for k in range(n):
        o=O[i+k][1]; c=C[j+k][1]; st['unaligned']-=1
        if o==c: st['eq']+=1; continue
        f=fm(o)==fm(c); r=rm(o)==rm(c); jj=o.startswith('j') and re.sub(r'[+-]0x[0-9a-f]+$','',o)==re.sub(r'[+-]0x[0-9a-f]+$','',c)
        if jj: st['jump']+=1
        elif f: st['frame']+=1
        elif r: st['reg']+=1; regp.append((O[i+k][0],C[j+k][0],o,c))
        else: st['mixed']+=1; regp.append((O[i+k][0],C[j+k][0],o,c))
print(p,st)
if v:
    for x in regp: print('  %04x %04x  %-36s | %s'%x)
