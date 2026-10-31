#!/usr/bin/env python3
"""rastate.py ra.log line [reg...]: replay RAPRIO_LOG up to a line; print vregs holding each reg then (size, weight)."""
import sys,re,collections
log,upto=sys.argv[1],int(sys.argv[2]); regs=sys.argv[3:] or ['R6','R7','R8','R9']
asg={}; info={}
for i,l in enumerate(open(log),1):
    if i>upto: break
    p=l.split()
    if not p: continue
    if p[0]=='Q': info[p[1]]=(p[4],p[5])
    elif p[0]=='R':
        v=p[1]; r=p[3]
        if r!='0': asg[v]=r
        else: asg.pop(v,None)
    elif p[0]=='E': asg.pop(p[1],None)
    elif p[0]=='F' and len(p)>3: pass
by=collections.defaultdict(list)
for v,r in asg.items(): by[r].append(v)
for r in regs:
    print(r, ' '.join(f"{v}({info.get(v,('',''))[0]},{info.get(v,('',''))[1]})" for v in sorted(by[r],key=lambda x:-int(info.get(x,('sz=0',''))[0][3:] or 0))[:14]))
