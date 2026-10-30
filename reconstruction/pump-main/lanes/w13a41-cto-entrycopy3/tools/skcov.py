#!/usr/bin/env python3
"""skcov.py a.dis b.dis [regs=1]: per orig 0x200 bucket skeleton (frame+regs masked) matched counts a->b vs orig.dis"""
import sys,re,difflib
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a41-cto-entrycopy3'
R=len(sys.argv)<4 or sys.argv[3]=='1'
def norm(f):
    out=[]
    for l in open(f):
        p=l.split(None,1)
        if len(p)<2 or not re.match(r'^(0x)?[0-9a-f]+$',p[0]): continue
        s=re.sub(r'<[^>]*>','',p[1]).strip()
        if s.startswith('call'): s='call'
        s=re.sub(r'^lddw (r\d+), .*',r'lddw \1',s)
        s=re.sub(r'r10 - 0x[0-9a-f]+','r10-X',s)
        s=re.sub(r'(add64 r\d+), -0x[0-9a-f]+$',r'\1, -F',s)
        if R: s=re.sub(r'\br\d\b','R',s)
        s=re.sub(r'(j\w+ .*?)[+-]0x[0-9a-f]+$',r'\1J',s); s=re.sub(r'^ja [+-]0x[0-9a-f]+','ja J',s)
        out.append(s)
    return out
o=norm(O+'/orig.dis')
def cov(f):
    c=norm(f); sm=difflib.SequenceMatcher(None,o,c,autojunk=False); h={}
    for a,b,n in sm.get_matching_blocks():
        for k in range(a,a+n): h[k*8//0x200]=h.get(k*8//0x200,0)+1
    return h,sm.ratio()
ha,ra=cov(sys.argv[1]); hb,rb=cov(sys.argv[2]); print('ratio %.4f -> %.4f'%(ra,rb))
for k in sorted(set(ha)|set(hb)):
    d=hb.get(k,0)-ha.get(k,0)
    if abs(d)>=4: print('  orig 0x%05x: %d -> %d (%+d)'%(0x22a10+k*0x200,ha.get(k,0),hb.get(k,0),d))
