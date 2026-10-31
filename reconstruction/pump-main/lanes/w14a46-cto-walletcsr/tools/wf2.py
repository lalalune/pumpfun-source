#!/usr/bin/env python3
"""wf.py <m.ll>...: frame-masked (r10 offsets, jump offsets, call/lddw imms masked; registers KEPT) difflib match vs orig.
Prints whole-function F ratio, matched tokens, and matched tokens whose orig offset is in the wallet [0x5c40,0x6b08) (Fw)."""
import sys,re,difflib,subprocess,os
T=os.path.dirname(os.path.abspath(__file__))
def norm(s):
    s=re.sub(r'\s*<[^>]*>','',s).strip()
    if s.startswith('call'): return 'call'
    if s.startswith('lddw'): return re.sub(r'0x[0-9a-f]+','IMM',s)
    s=re.sub(r'r10 - 0x[0-9a-f]+','FP',s); s=re.sub(r'^(add64 r\d+), -0x[0-9a-f]+$',r'\1, -FP',s)
    if s.startswith('j'): s=re.sub(r'[+-]0x[0-9a-f]+$','J',s)
    return s
def rd(lines):
    r=[]
    for l in lines:
        q=l.split(None,1)
        if len(q)==2: r.append((int(q[0],16),norm(q[1])))
    return r
O=rd(open(T+'/../or.dis'))
for p in sys.argv[1:]:
    d=subprocess.run(['bash',T+'/dll.sh',p],capture_output=True,text=True).stdout.split('\n') if p.endswith('.ll') else open(p).read().split('\n')
    C=rd(d)
    sm=difflib.SequenceMatcher(None,[x[1] for x in O],[x[1] for x in C],autojunk=False)
    M=0;Fw=0
    for a,b,n in sm.get_matching_blocks():
        M+=n; Fw+=sum(1 for i in range(a,a+n) if 0x5c40<=O[i][0]<0x6b08)
    print(p, 'F=%.5f'%sm.ratio(),'M=%d'%M,'Fw=%d'%Fw, 'wallet_orig=%d'%sum(1 for x in O if 0x5c40<=x[0]<0x6b08))
