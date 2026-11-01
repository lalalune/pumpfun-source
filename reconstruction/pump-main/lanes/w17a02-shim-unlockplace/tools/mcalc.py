#!/usr/bin/env python3
# mcalc.py <unstripped.so>...: admin_cto M (difflib matched tokens), token counts, ratio, lddw count, error-site offsets
import sys,re,difflib,struct
H='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a02-shim-unlockplace/reconstruction/harness'
sys.path.insert(0,H)
from score import original_windows
from win import Cand, insns, demangle, ORIG_SECS
W=[w for w in original_windows() if w['start']==0x22a10][0] if callable(original_windows) else None
otok=[x[2] for x in insns(W['raw'],W['start'],ORIG_SECS)]
def errs(raw):
    out=[]
    for i in range(0,len(raw)-8,8):
        if raw[i]==0x62:  # stw [dst+off], imm
            dst=raw[i+1]&15; off=struct.unpack_from('<h',raw,i+2)[0]; imm=struct.unpack_from('<i',raw,i+4)[0]
            if dst==10 and 280<=imm<=780: out.append((imm,i))
    return out
for p in sys.argv[1:]:
    c=Cand(p); pat=re.compile(r'admin_cto::execute$')
    s,n,nm=[(s,n,nm) for s,n,nm in c.funcs if pat.search(demangle(nm))][0]
    raw=c.fn(s,n); ctok=[x[2] for x in insns(raw,s,c.secs)]
    sm=difflib.SequenceMatcher(None,otok,ctok,autojunk=False); M=sum(b.size for b in sm.get_matching_blocks())
    nl=sum(1 for i in range(0,n,8) if raw[i]==0x18)//1
    print(p.split('/')[-2], 'bytes',n,'M',M,'ntok',len(ctok),'ratio',round(2*M/(len(otok)+len(ctok)),5),'lddw',sum(1 for t in ctok if str(t).startswith('lddw')))
