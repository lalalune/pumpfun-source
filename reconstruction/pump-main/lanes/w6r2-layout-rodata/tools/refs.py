# refs.py cand.so OFFLO OFFHI [section]  -> who references section offsets in [lo,hi) in orig and cand
import sys,struct
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w6r2-layout-rodata/reconstruction/harness')
from score import candidate_functions, sections, original_windows
from original_input import resolve_original
from pathlib import Path
orig=resolve_original(Path('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w6r2-layout-rodata/reconstruction/base/original.so')).read_bytes()
cand=open(sys.argv[1],'rb').read(); lo=int(sys.argv[2],16); hi=int(sys.argv[3],16); sec=sys.argv[4] if len(sys.argv)>4 else '.rodata'
def scan(img, fns):
    S=sections(img); t=S['.text']; base=S[sec]['addr']; out=[]
    for st,l,n in fns:
        o=st-t['addr']+t['offset']; i=0
        while i<l:
            if img[o+i]==0x18:
                v=struct.unpack_from('<I',img,o+i+4)[0]|struct.unpack_from('<I',img,o+i+12)[0]<<32
                if base+lo<=v-0<base+hi: out.append((hex(v-base),hex(st),hex(i),n[:80]))
                i+=16
            else: i+=8
    return out
ow=[(w['start'],w['bytes'],'win') for w in original_windows()]
print('ORIG'); [print(' ',x) for x in sorted(scan(orig,ow))]
cf=candidate_functions(sys.argv[1]); seen=set(); cf2=[]
for f in cf:
    if f[0] in seen: continue
    seen.add(f[0]); cf2.append(f)
print('CAND'); [print(' ',x) for x in sorted(scan(cand,cf2))]
