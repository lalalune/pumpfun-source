# compare .data.rel.ro slot by slot: decode relocated pointers (u32 target in upper half per sBPF) to (section, offset)
import sys,struct
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/restore/reconstruction/harness')
from score import sections
def load(p):
    b=open(p,'rb').read(); S=sections(b); return b,S
def sec_of(S,v):
    for n,s in S.items():
        if s['addr'] and s['addr']<=v<s['addr']+s['size']: return n,v-s['addr']
    return None
def slots(b,S):
    d=S['.data.rel.ro']; raw=b[d['offset']:d['offset']+d['size']]; out=[]
    for i in range(0,len(raw),8):
        lo,hi=struct.unpack_from('<II',raw,i)
        t=sec_of(S,hi) if lo==0 and hi else None
        out.append(('P',)+t if t else ('V',raw[i:i+8]))
    return out
ob,OS=load('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/restore/reconstruction/base/original.so')
cb,CS=load(sys.argv[1])
o=slots(ob,OS); c=slots(cb,CS)
diff=[i for i,(x,y) in enumerate(zip(o,c)) if x!=y]
txt=[i for i in diff if o[i][0]=='P' and c[i][0]=='P' and o[i][1]=='.text' and c[i][1]=='.text']
print('slots',len(o),len(c),'differ',len(diff),'of which text-pointer only',len(txt),'other',len(diff)-len(txt))
for i in [i for i in diff if i not in txt][:12]: print(hex(i*8),o[i],c[i])
