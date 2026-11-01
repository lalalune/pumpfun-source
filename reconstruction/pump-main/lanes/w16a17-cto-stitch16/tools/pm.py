#!/usr/bin/env python3
"""pm.py: size-complementary pairs (+X B capture, -X B capture) of the translated library on the newest main, priced with
ratio + positional slots; reports pairs at 27,400 B with ratio >= main and fewer slots, or higher ratio. Experiment only."""
import sys,os,json,collections
sys.path.insert(0,'tools'); import splice, oracle
OLD=open('rx/main/fn.bin','rb').read(); NEW=oracle.elf_fn(os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so'),oracle.KEEP)
orig=oracle.orig_window(); r0,s0=oracle.metric(NEW,orig); M0=splice.M(NEW)
OB=splice.parse(OLD); OBT=splice.targets(OB); NV=splice.Var(OB,NEW)
T=json.load(open('w17/tnew2_34899af.json'))
by=collections.defaultdict(list)
for x in T:
    d=x['bytes']-27400
    if d!=0 and abs(d)<=48 and x['M']>=M0-10: by[d].append(x)
raw={}
def R(x):
    if x['tpath'] not in raw: raw[x['tpath']]=splice.Var(OB,open(x['tpath'],'rb').read())
    return raw[x['tpath']]
out=[]; n=0
for d in sorted(k for k in by if k>0):
    for a in by[d]:
        for b in by.get(-d,[]):
            s=splice.splice(OLD,[NV,R(a),R(b)],OB,OBT); n+=1
            if s is None or len(s)!=27400: continue
            rr,sd=oracle.metric(s,orig); m=splice.M(s)
            out.append((m,-sd,a['name'],b['name'],d,rr,sd))
out.sort(reverse=True)
print('main',M0,r0,s0,'pairs tried',n,'priced',len(out))
for o in out[:15]: print(o)
good=[o for o in out if (o[0]>M0) or (o[0]==M0 and o[6]<s0)]
print('better than main:',len(good)); [print(g) for g in good[:20]]
json.dump(out,open('w17/pm_34899af.json','w'))
