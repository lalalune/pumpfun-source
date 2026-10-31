#!/usr/bin/env python3
"""sscsim.py <dir> [--drop f,f,..] [--late f,f,..]: emulate LLVM StackSlotColoring (stable sort by weight desc over FI order,
first-fit over used colours ascending, else next unused spill FI). Checks reproduction of ssc.log; with --late, those
intervals are coloured LAST (after all others), i.e. as if they did not press on the colouring; writes the colour map
as a mirperm-style rewrite and scores it (experiment only)."""
import sys,re,os,subprocess,json
D=sys.argv[1]; args=sys.argv[2:]
late=set(); 
if '--late' in args: late=set(int(x) for x in args[args.index('--late')+1].split(','))
log=open(D+'/ssc.log').read()
SUBK={'B':0,'e':1,'r':2,'d':3}
def iv(s): return [(int(a)*4+SUBK[b],int(c)*4+SUBK[d]) for a,b,c,d in re.findall(r'\[(\d+)([Berd]),(\d+)([Berd]):\d+\)',s)]
IV={int(m.group(1)):iv(m.group(2)) for m in re.finditer(r'^SS#(\d+) (.*)$',log,re.M)}
W={int(m.group(1)):float(m.group(2)) for m in re.finditer(r'^SS#(\d+) .*weight:(\S+)',log,re.M)}
COL={int(a):int(b) for a,b in re.findall(r'Assigning fi#(\d+) to fi#(\d+)',log)}
for f in IV: COL.setdefault(f,f)
def ov(a,b):
    i=j=0
    while i<len(a) and j<len(b):
        if a[i][0]<b[j][1] and b[j][0]<a[i][1]: return True
        if a[i][1]<=b[j][1]: i+=1
        else: j+=1
    return False
def colour(order):
    allc=sorted(IV); used=[]; asg={}; occ={}; nxt=0
    for f in order:
        c=None
        for u in used:
            if not any(ov(IV[f],IV[g]) for g in occ[u]): c=u; break
        if c is None:
            c=allc[nxt]; nxt+=1; used.append(c); used.sort(); occ[c]=[]
        occ[c].append(f); asg[f]=c
    return asg
base=[int(a) for a,b in re.findall(r'Assigning fi#(\d+) to fi#(\d+)',log)]
sim=colour(base)
bad=[f for f in IV if sim[f]!=COL[f]]
print('reproduce:',len(IV)-len(bad),'/',len(IV),'mismatch',bad[:10],file=sys.stderr)
if late:
    order=[f for f in base if f not in late]+[f for f in base if f in late]
    new=colour(order)
    json.dump({str(k):v for k,v in new.items()},open(D+'/sim_late.json','w'))
    ch=sum(1 for f in IV if new[f]!=COL[f]); print('late',sorted(late),'changed',ch,'maxcol',max(new.values()),'late colours',{f:new[f] for f in late},file=sys.stderr)
