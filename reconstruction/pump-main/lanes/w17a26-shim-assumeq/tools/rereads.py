#!/usr/bin/env python3
"""rereads.py <o3.ll> [fnpat]: list same-address same-type load groups in the post-opt function (symbolic address
expressions: gep-const chains over params / load results / allocas)."""
import sys,re,collections
src=sys.argv[1]; pat=sys.argv[2] if len(sys.argv)>2 else r'admin_cto7execute17h'
L=open(src).read().split('\n')
s=None
for i,l in enumerate(L):
    if l.startswith('define') and re.search(pat,l.split('(')[0]): s=i; break
e=s
while L[e]!='}': e+=1
VAL=r'(%[\w.$-]+|%"[^"]+")'
defs={}
blk=None; blkof={}
for i in range(s+1,e):
    l=L[i]
    m=re.match(r'^("?[\w.$-]+"?):',l)
    if m: blk=m.group(1); continue
    m=re.match(r'^\s+'+VAL+r' = (.*)$',l)
    if m: defs[m.group(1)]=(i,m.group(2)); blkof[m.group(1)]=blk
memo={}
def addr(v,depth=0):
    if v in memo: return memo[v]
    if depth>12: return v
    if v not in defs: r=v
    else:
        i,rhs=defs[v]
        m=re.match(r'getelementptr inbounds i8, ptr '+VAL+r', i64 (-?\d+)$',rhs)
        if m:
            b=addr(m.group(1),depth+1); r=f'{b}+{m.group(2)}'
        else:
            m=re.match(r'load (ptr|i\d+), ptr '+VAL+r'(,.*)?$',rhs)
            if m: r='*('+addr(m.group(2),depth+1)+')'
            elif rhs.startswith('alloca'): r=v
            else: r=v
    memo[v]=r; return r
G=collections.defaultdict(list)
for v,(i,rhs) in defs.items():
    m=re.match(r'load (volatile )?(ptr|i\d+), ptr '+VAL+r'(,.*)?$',rhs)
    if not m: continue
    a=addr(m.group(3))
    if re.match(r'^%[\w.$-]*$',a) and defs.get(a,(0,''))[1].startswith('alloca'): continue
    G[(m.group(2),a)].append((i,v,blkof[v],bool(m.group(1))))
n=0
for (t,a),xs in sorted(G.items(),key=lambda kv:kv[1][0][0]):
    if len(xs)<2: continue
    n+=1
    print(f'{t:4s} {a[:90]:90s} n={len(xs)} ' + ' '.join(f'{i}:{v}{"(vol)" if vo else ""}' for i,v,b,vo in xs))
print('groups',n,file=sys.stderr)
