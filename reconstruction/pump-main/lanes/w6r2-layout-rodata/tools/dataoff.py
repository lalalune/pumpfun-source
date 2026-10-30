# dataoff.py cand.so : per normalized window, does SOME matching candidate symbol have every .rodata/.data.rel.ro lddw at the original in-section offset?
import sys,struct,hashlib
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w6r2-layout-rodata/reconstruction/harness')
from score import candidate_functions, body, original_windows, normalize, sections
orig=open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w6r2-layout-rodata/reconstruction/base/original.so','rb').read()
os_=sections(orig); cand=open(sys.argv[1],'rb').read(); cs=sections(cand)
def refs(raw,S):
    out=[];i=0
    while i<len(raw):
        if raw[i]==0x18:
            v=struct.unpack_from('<I',raw,i+4)[0]|struct.unpack_from('<I',raw,i+12)[0]<<32
            for n in ('.rodata','.data.rel.ro'):
                if S[n]['addr']<=v<S[n]['addr']+S[n]['size']: out.append((i,n,v-S[n]['addr']))
            i+=16
        else: i+=8
    return out
by={}
for st,l,n in candidate_functions(sys.argv[1]):
    raw=body(cand,cs,st,l); by.setdefault((l,hashlib.sha256(normalize(raw,st,cs)).digest()),[]).append((st,n,raw))
tot=0;ok=0;bad=[];withdata=0
for w in original_windows():
    ms=by.get((w['bytes'],hashlib.sha256(w['norm']).digest()),[])
    if not ms: continue
    tot+=1; r0=refs(w['raw'],os_)
    if r0: withdata+=1
    if any(refs(m[2],cs)==r0 for m in ms): ok+=1
    else: bad.append(hex(w['start']))
print('normalized',tot,'with data refs',withdata,'data-offset-equal',ok,'bad',bad)
