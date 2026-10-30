#!/usr/bin/env python3
# offd.py <A_fn> <B_fn>: align frame-masked tokens; histogram of (A offset -> B offset) for r10 slots
import sys,re,difflib,collections
def rd(f):
    A=[];T=[]
    for l in open(f):
        p=l.split(None,1)
        if len(p)<2: continue
        s=p[1].strip(); A.append(s); s=re.sub(r'^call .*','call',s); s=re.sub(r'lddw (r\d+), .*',r'lddw \1',s); s=re.sub(r'r10 - 0x[0-9a-f]+','r10-X',s); s=re.sub(r'add64 (r\d), -0x[0-9a-f]+',r'add64 \1, -X',s); T.append(s)
    return A,T
a,ta=rd(sys.argv[1]); b,tb=rd(sys.argv[2]); H=collections.Counter(); D=collections.Counter()
for t,i1,i2,j1,j2 in difflib.SequenceMatcher(None,ta,tb,autojunk=False).get_opcodes():
    if t!='equal': continue
    for k in range(i2-i1):
        x=re.search(r'r10 - (0x[0-9a-f]+)',a[i1+k]); y=re.search(r'r10 - (0x[0-9a-f]+)',b[j1+k])
        if x and y: H[(int(x.group(1),16),int(y.group(1),16))]+=1; D[int(y.group(1),16)-int(x.group(1),16)]+=1
print('delta histogram',sorted(D.items(),key=lambda z:-z[1])[:12])
moved=[(k,v) for k,v in H.items() if k[0]!=k[1]]
for (x,y),n in sorted(moved): print(f'{x:#x} -> {y:#x} ({y-x:+d}) x{n}')
