#!/usr/bin/env python3
"""postkeys.py <o3.ll> <out.json>: (type, base+off) keys of same-address load groups (>=2 non-volatile loads) in the
post-opt execute (wallet/sweep/validate inlined), in asgen.py's canonical address format."""
import sys,re,json,collections
src,outp=sys.argv[1:3]
L=open(src).read().split('\n')
s=next(i for i,l in enumerate(L) if l.startswith('define') and re.search(r'admin_cto7execute17h',l.split('(')[0]))
e=s
while L[e]!='}': e+=1
VAL=r'(%[\w.$-]+|%"[^"]+")'
defs={}
for i in range(s+1,e):
    m=re.match(r'^\s+'+VAL+r' = (.*)$',L[i])
    if m: defs[m.group(1)]=(i,m.group(2))
memo={}
def addr(v,d=0):
    if v in memo: return memo[v]
    r=(v,0)
    if d<16 and v in defs:
        i,rhs=defs[v]
        m=re.match(r'getelementptr inbounds i8, ptr '+VAL+r', i64 (-?\d+)$',rhs)
        if m:
            bb,o=addr(m.group(1),d+1); r=(bb,o+int(m.group(2)))
        else:
            m=re.match(r'load (?:volatile )?(ptr), ptr '+VAL+r'(,.*)?$',rhs)
            if m:
                bb,o=addr(m.group(2),d+1); r=('*(%s+%d)'%(bb,o),0)
    memo[v]=r; return r
G=collections.Counter(); V=collections.Counter()
for v,(i,rhs) in defs.items():
    m=re.match(r'load (volatile )?(ptr|i\d+), ptr '+VAL+r'(,.*)?$',rhs)
    if not m: continue
    a=addr(m.group(3)); k='%s|%s+%d'%(m.group(2),a[0],a[1])
    if m.group(1): V[k]+=1
    else: G[k]+=1
keys={k:G[k] for k in G if G[k]+V[k]>=2}
json.dump(keys,open(outp,'w'),indent=0)
print(len(keys))
