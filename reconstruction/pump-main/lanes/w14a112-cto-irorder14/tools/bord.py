#!/usr/bin/env python3
"""bord.py m.ll [n]: execute post-opt block order from the first validate block; error blocks tagged by PumpError alloc (mapped from main)."""
import sys,re,json,os
M=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def blocks(f):
    L=open(f).read().split('\n')
    fs=[i for i,l in enumerate(L) if l.startswith('define') and 'admin_cto7execute' in l][0]
    out=[];cur=None
    for i in range(fs+1,len(L)):
        if L[i]=='}': break
        m=re.match(r'^("[^"]+"|[\w.$-]+):',L[i])
        if m:
            n=m.group(1).strip('"'); n=n.split('E.')[-1] if 'to_string' in n else n
            cur=[n,[]]; out.append(cur)
        elif cur: cur[1].append(L[i])
    return out
def tag(b):
    for l in b[1]:
        m=re.search(r'PumpError4name\w*\(.*?(@alloc_\w+)',l)
        if m: return m.group(1)
    return ''
mp=json.load(open(M+'/io/allocmap.json')) if os.path.exists(M+'/io/allocmap.json') else {}
bl=blocks(sys.argv[1]); n=int(sys.argv[2]) if len(sys.argv)>2 else 40
st=[i for i,b in enumerate(bl) if b[0].endswith('.i')][0]-1
out=[]
for b in bl[st:st+n]:
    t=tag(b); term=[l.strip() for l in b[1] if l.strip().startswith(('br ','switch','ret','unreachable'))]
    out.append(b[0]+('['+mp.get(t,t[-6:])+']' if t else ''))
print(' '.join(out))
