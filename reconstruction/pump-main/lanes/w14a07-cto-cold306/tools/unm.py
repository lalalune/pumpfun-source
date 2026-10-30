import sys,re,difflib
# unm.py orig cand lo hi : orig instructions in [lo,hi] not matched by cand (normalized tokens)
def rd(f):
    A=[];T=[]
    for l in open(f):
        p=l.split(None,1)
        if len(p)<2: continue
        s=p[1].strip(); A.append((int(p[0],16),s))
        s=re.sub(r'^call .*','call',s); s=re.sub(r'lddw (r\d+), .*',r'lddw \1',s); s=re.sub(r'r10 - 0x[0-9a-f]+','r10-X',s); s=re.sub(r'r\d','r',s); T.append(s)
    return A,T
oa,ot=rd(sys.argv[1]); ca,ct=rd(sys.argv[2]); lo,hi=int(sys.argv[3],16),int(sys.argv[4],16)
for t,i1,i2,j1,j2 in difflib.SequenceMatcher(None,ot,ct,autojunk=False).get_opcodes():
    if t=='equal': continue
    seg=[oa[i] for i in range(i1,i2) if lo<=oa[i][0]<=hi]
    if seg: print(f'--{t} orig {i2-i1} vs cand {j2-j1} (cand @{ca[j1][0]:#x})' if j1<len(ca) else t); [print(f'  {a:#06x} {s}') for a,s in seg[:14]]
