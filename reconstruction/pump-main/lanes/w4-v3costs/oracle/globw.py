#!/usr/bin/env python3
"""Diagnostic: add 1:N weights to every branch that targets a block calling unwrap_failed with the Display-error message (to_string expect)."""
import re,sys
src,dst=sys.argv[1],sys.argv[2]; N=int(sys.argv[3]) if len(sys.argv)>3 else 2000
MSG=sys.argv[4] if len(sys.argv)>4 else 'alloc_cc656815297f75969399c3f4b1ad3de4, i64 noundef 55'
t=open(src).read()
out=[];pos=0;cnt=0;miss=0
for m in re.finditer(r'^define[^\n]*\{\n.*?^\}\n',t,re.M|re.S):
    f=m.group(0)
    blocks=re.split(r'\n(?=[^\s;][^\n]*:(?:\s|$))',f)
    tgt=set()
    for b in blocks:
        lab=b.split(':')[0].strip()
        if MSG in b and 'unwrap_failed' in b and b.rstrip().endswith('unreachable'):
            tgt.add(lab)
    if tgt:
        def rep(mm):
            global cnt
            c,a,bb=mm.group(1),mm.group(2),mm.group(3)
            if mm.group(4): return mm.group(0)
            la=a[1:] if a.startswith('%') else a; lb=bb[1:]
            if la in tgt: cnt+=1; return mm.group(0)+', !prof !990001'
            if lb in tgt: cnt+=1; return mm.group(0)+', !prof !990002'
            return mm.group(0)
        f=re.sub(r'  br i1 (\S+), label (%"[^"]+"|%\S+), label (%"[^"]+"|%[^\s,]+)(, !prof)?',lambda mm:rep(mm) if not mm.group(4) else mm.group(0),f)
        f=f.replace('label %"','label %"')
    out.append(t[pos:m.start()]); out.append(f); pos=m.end()
out.append(t[pos:])
r=''.join(out)+'\n!990001 = !{!"branch_weights", i32 1, i32 %d}\n!990002 = !{!"branch_weights", i32 %d, i32 1}\n'%(N,N)
open(dst,'w').write(r); print('weighted',cnt)
