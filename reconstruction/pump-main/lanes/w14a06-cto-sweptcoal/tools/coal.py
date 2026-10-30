#!/usr/bin/env python3
"""coal.py <m.ll|dir-with-m.ll> [...]: swept/Err-payload coalescing and clone-run RA diagnosis for admin_cto::execute
(experiment only). Runs the debug llc (-debug-only=regalloc; output equals the SDK llc) and reports:
  pay      : the Err-payload vreg class (most `LDD_V1 %stack.N, 8` result loads) and its size
  swept_in : whether the AdminCtoEvent swept_to_holder_vault store (offset 184 of the event, last one) uses that class
  pay_reg  : physreg given to the payload class
  split    : the accounts pointer (%0) region-split candidate ('Split for $rX in N bundles')
  cf       : clonefeat spill/reg on the resulting object.
Mechanism (w13a40): RegisterCoalescer visits blocks by (pred+succ) count; when the post-sweep CPI Err join (3 preds)
is visited before the sweep Err copy block (2 preds), the post-sweep payload copies join the payload class first
and `swept` interferes (it is live in the CPI call blocks), so swept stays a separate, spilled vreg."""
import sys,os,re,subprocess,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import ctoracle as co, clonefeat
DBG=os.path.expanduser('~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/llc')
def one(p):
    if os.path.isdir(p): p=os.path.join(p,'m.ll')
    d=os.path.dirname(p)
    r=subprocess.run([DBG,'-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',p,'-filetype=obj','-o',d+'/dbg.o','-debug-only=regalloc'],capture_output=True,text=True)
    log=r.stderr; g=log[log.index('GREEDY REGISTER ALLOCATION'):]
    mi=g[g.index('MACHINEINSTRS'):g.index('REWRITE VIRTUAL REGISTERS') if 'REWRITE VIRTUAL REGISTERS' in g else None]
    c=collections.Counter(re.findall(r'(%\d+):gpr = LDD_V1 %stack\.\d+, 8 ::',mi))
    pay,n=c.most_common(1)[0]
    st=re.findall(r'^\d+B\t  STD_V1 (%\d+):gpr, %stack\.\d+\._54\.i\d*, 184 ',mi,re.M)
    swept_in=bool(st) and st[-1]==pay
    regs=re.findall(r'^assigning '+re.escape(pay)+r' to \$(r\d+)',g,re.M)
    sp=None; L=g.split('\n')
    for k,l in enumerate(L):
        if l.startswith('selectOrSplit GPR:%0 '):
            for m in L[k+1:k+40]:
                if m.startswith('Split for '): sp=m[10:].split(',')[0]; break
                if m.startswith('selectOrSplit'): break
    ct,raw,_=co.obj_tokens(d+'/dbg.o'); s,rg=clonefeat.feats(ct)
    print(f'{p}: pay={pay} n={n} swept_in={swept_in} swept_vreg={st[-1] if st else None} pay_reg={regs[-1] if regs else None} split={sp} cf={s}/{rg} bytes={len(raw)}')
for p in sys.argv[1:]: one(p)
