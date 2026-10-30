# raw count if candidate data sections were rebased to the original's addresses (i.e. .text total size equal)
import sys, struct, json
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w6r2-layout-rodata/reconstruction/harness')
from score import candidate_functions, body, original_windows, normalize, sections
from original_input import resolve_original
from pathlib import Path
import hashlib
orig=resolve_original(Path('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w6r2-layout-rodata/reconstruction/base/original.so')).read_bytes()
os_=sections(orig)
cand=open(sys.argv[1],'rb').read(); cs=sections(cand)
def rebase(raw):
    m=bytearray(raw); i=0
    while i<len(raw):
        op=raw[i]
        if op==0x18:
            v=struct.unpack_from('<I',raw,i+4)[0]|struct.unpack_from('<I',raw,i+12)[0]<<32
            for n,s in cs.items():
                if n and s['addr']>0 and s['addr']<=v<s['addr']+s['size'] and n in os_:
                    nv=v-s['addr']+os_[n]['addr']; struct.pack_into('<I',m,i+4,nv&0xffffffff); struct.pack_into('<I',m,i+12,nv>>32); break
            i+=16
        else: i+=8
    return bytes(m)
by={}
for st,l,n in candidate_functions(sys.argv[1]):
    raw=body(cand,cs,st,l); by.setdefault((l,hashlib.sha256(normalize(raw,st,cs)).digest()),[]).append((st,n,raw))
nr=0;r=0;rr=0;fails=[]
for w in original_windows():
    ms=by.get((w['bytes'],hashlib.sha256(w['norm']).digest()),[])
    if not ms: continue
    nr+=1
    if any(m[2]==w['raw'] for m in ms): r+=1
    if any(rebase(m[2])==w['raw'] for m in ms): rr+=1
    else: fails.append(w['start'])
print(json.dumps({'normalized':nr,'raw':r,'raw_if_data_rebased':rr}))
if len(sys.argv)>2: json.dump(fails,open(sys.argv[2],'w'))
