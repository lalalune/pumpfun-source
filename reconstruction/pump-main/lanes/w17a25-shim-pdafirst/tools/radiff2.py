#!/usr/bin/env python3
"""radiff2.py <a> <b> [lim] [skip] [shiftB]: greedy trace compare keyed by live-range start slot; B slots >= skip are
shifted by -shiftB (to undo an instruction-count change in E1). Prints first divergences with context."""
import sys,re,os
OUT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def trace(n,shift=0,skip=2000):
    ev=[];cur=None
    def f(s):
        s=int(s); return str(s-shift) if s>=skip else str(s)
    for l in open(f'{OUT}/ra/{n}.ra.txt'):
        m=re.match(r'selectOrSplit GPR:(%\d+) \[(\d+)[rBed]',l)
        if m: cur=f(m.group(2)); ev.append(('sel',cur)); continue
        m=re.match(r'assigning (%\d+) to \$(r\d+)',l)
        if m: ev.append(('asg',cur,m.group(2))); continue
        m=re.match(r'evicting \$(r\d+) interference',l)
        if m: ev.append(('evict',cur,m.group(1))); continue
        if l.startswith('Inline spilling') or l.startswith('spillAll') : ev.append(('spill',cur)); continue
        m=re.match(r'(splitAroundRegion|tryLocalSplit|trySplit|Split around|Split for)',l)
        if m: ev.append(('split',cur,m.group(1)))
    return ev
a1=sys.argv[1]; b1=sys.argv[2]
lim=int(sys.argv[3]) if len(sys.argv)>3 else 15
skip=int(sys.argv[4]) if len(sys.argv)>4 else 2000
sh=int(sys.argv[5]) if len(sys.argv)>5 else 0
a=trace(a1); b=trace(b1,sh,skip)
print(len(a),len(b))
i=j=0;n=0
while i<len(a) and j<len(b) and n<lim:
    x=a[i];y=b[j]
    if x==y: i+=1;j+=1;continue
    if len(x)>1 and x[1] and int(x[1])<skip: i+=1;continue
    if len(y)>1 and y[1] and int(y[1])<skip: j+=1;continue
    print(i,j,'A',a[i:i+5]); print(i,j,'B',b[j:j+5]); n+=1; i+=1; j+=1
