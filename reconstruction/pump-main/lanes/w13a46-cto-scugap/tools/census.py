#!/usr/bin/env python3
"""census.py <cand.so> [<ref.so>] : align admin_cto candidate vs original (target_metric token stream),
print opcode summary, pure delete (orig-only) runs, pure insert (cand-only) runs, with disassembly.
With ref.so: also list orig insns matched in ref but not in cand (lost) and vice versa (won)."""
import sys, difflib, re
H='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a46-cto-scugap/reconstruction/harness'
sys.path.insert(0,H)
from win import Cand, insns, demangle, ORIG, ORIG_SECS, objdump_text, resolve_original, BASE
from score import original_windows
W=0x22a10; NB=27400
def orig_tok():
    raw=ORIG[0:0]
    from score import sections
    s=ORIG_SECS
    t=[w for w in original_windows() if w['start']==W][0]
    return insns(t['raw'],W,ORIG_SECS)
def cand_tok(p):
    c=Cand(p)
    for s,n,nm in c.funcs:
        if re.search(r'admin_cto::execute$',demangle(nm)): return insns(c.fn(s,n),s,c.secs),s,n
O=orig_tok()
def dis(path,start,n):
    return objdump_text(path,start,start+n)
def align(ct):
    sm=difflib.SequenceMatcher(None,[x[2] for x in O],[x[2] for x in ct],autojunk=False)
    return sm
if __name__=='__main__':
    p=sys.argv[1]; ct,cs,cn=cand_tok(p)
    sm=align(ct); print('ratio',round(sm.ratio(),5),'orig',len(O),'cand',len(ct))
    ops=sm.get_opcodes()
    from collections import Counter
    c=Counter();
    for t,i1,i2,j1,j2 in ops: c[t+'_o']+=i2-i1; c[t+'_c']+=j2-j1
    print(dict(c))
    od=dis(str(resolve_original(BASE/'original.so')),W,NB); cd=dis(p,cs,cn)
    mode=sys.argv[2] if len(sys.argv)>2 else 'runs'
    if mode=='runs':
      for t,i1,i2,j1,j2 in ops:
        if t=='equal': continue
        print(f'--{t} o[{i1}:{i2}] c[{j1}:{j2}] o@{O[i1][0]-W if i1<len(O) else -1:#x} c@{ct[j1][0]-cs if j1<len(ct) else -1:#x}')
        if t in('delete','replace'):
            for k in range(i1,i2): print('   O',hex(O[k][0]-W),od.get(O[k][0],'?'))
        if t in('insert','replace'):
            for k in range(j1,j2): print('   C',hex(ct[k][0]-cs),cd.get(ct[k][0],'?'))
def side(p, o1, o2):
    """print orig range [o1,o2) byte offsets with aligned candidate lines"""
    ct,cs,cn=cand_tok(p); sm=align(ct)
    od=dis(str(resolve_original(BASE/'original.so')),W,NB); cd=dis(p,cs,cn)
    for t,i1,i2,j1,j2 in sm.get_opcodes():
        oa=[O[k][0]-W for k in range(i1,i2)]
        if not oa:
            pa=O[i1][0]-W if i1<len(O) else NB
            if not(o1<=pa<o2): continue
        elif oa[-1]<o1 or oa[0]>=o2: continue
        n=max(i2-i1,j2-j1)
        for k in range(n):
            ol=f'{O[i1+k][0]-W:#06x} {od.get(O[i1+k][0],"?")}' if i1+k<i2 else ''
            cl=f'{ct[j1+k][0]-cs:#06x} {cd.get(ct[j1+k][0],"?")}' if j1+k<j2 else ''
            print(f'{t[0]} {ol:<52} | {cl}')
