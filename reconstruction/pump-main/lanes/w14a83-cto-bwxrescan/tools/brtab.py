#!/usr/bin/env python3
"""brtab.py m.ll bpi.txt -> json lines: block, cond, cond-def text, succs, prob, heuristic guess"""
import sys,re,json
sys.path.insert(0,__import__('os').path.dirname(__file__)); import bwx
mod=open(sys.argv[1]).read(); _,fn,_=bwx.split(mod); _,bl,_=bwx.blocks(fn)
defs={}
for lab,ls in bl:
    for l in ls:
        m=re.match(r'\s*(%[-\w.$"]+) = (.*)',l)
        if m: defs[m.group(1)]=(lab,m.group(2)[:160])
prob={}
for l in open(sys.argv[2]):
    m=re.match(r'\s*edge (%\S+) -> (%\S+) probability is 0x([0-9a-f]+) / 0x80000000 = ([\d.]+)%',l)
    if m: prob.setdefault(m.group(1).lstrip('%').strip('"'),[]).append((m.group(2).lstrip('%').strip('"'),int(m.group(3),16)))
blk={lab:ls for lab,ls in bl}
def succ_kind(s):
    ls=blk.get(s,[]); t=' '.join(ls)
    k=[]
    if 'unreachable' in t: k.append('unr')
    if re.search(r'call .*@(_ZN[^ ]*panic|_ZN[^ ]*unwrap_failed|_ZN[^ ]*handle_error|_ZN[^ ]*handle_alloc)',t): k.append('panic')
    if re.search(r'\bret\b',t): k.append('ret')
    return '+'.join(k)
for lab,c,a,b,hasprof in bwx.brs(mod):
    a=a.lstrip('%').strip('"'); b=b.lstrip('%').strip('"')
    p=dict(prob.get(lab,[]))
    pa=p.get(a); 
    d=defs.get(c,('',''))[1]
    if pa is None: h='?'
    elif pa in (0x30000000,0x50000000):
        if re.search(r'icmp \w+ ptr',d): h='ptr'
        elif 'call' in d or 'memcmp' in d: h='libcall'
        else: h='zero'
    elif pa==0x40000000: h='none'
    elif pa<0x1000000 or pa>0x7f000000: h='cold/unr'
    else: h='other'
    print(json.dumps({'blk':lab,'c':c,'def':d,'T':a,'F':b,'pT':round((pa or 0)/0x80000000,4),'h':h,'prof':hasprof,'kT':succ_kind(a),'kF':succ_kind(b)}))
