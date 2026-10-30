"""cpis.py: parse the six CPI calls of admin_cto.rs (tf transfer_creator_fees_to_pump_v2, sh admin_cto_sharing_config,
po admin_cto_pool, cc collect_coin_creator_fee, ci/ch create_idempotent in wallet/sweep) into
{full, fn, ctor, prog, accts, seeds, rest} and rebuild them, for generating CPI-spelling variants.
Set CTO_SRC to the admin_cto.rs to parse (default: this worktree's)."""
import os
from pathlib import Path
F=os.environ.get('CTO_SRC',str(Path(__file__).resolve().parents[5]/'programs/pump/src/creator/admin_cto.rs'))
SRC=open(F).read()
def find_cpi(anchor):
    """returns (full_text, fn_path, ctor, prog, accts, extra_after_ctx_args(with signer), tail_args) for the CPI call starting at anchor"""
    i=SRC.index(anchor)
    # call: anchor(CpiContext::ctor(prog,accts[,seeds])[,args])?;
    j=SRC.index('(',i)
    depth=0;k=j
    while True:
        c=SRC[k]
        if c in '([{': depth+=1
        elif c in ')]}':
            depth-=1
            if depth==0: break
        k+=1
    full=SRC[i:k+1]
    return full
def split_top(s):
    out=[];depth=0;cur=''
    for c in s:
        if c in '([{': depth+=1
        if c in ')]}': depth-=1
        if c==',' and depth==0: out.append(cur);cur=''
        else: cur+=c
    out.append(cur); return out
def parse(anchor):
    full=find_cpi(anchor)
    fn=full[:full.index('(')]
    inner=full[len(fn)+1:-1]
    args=split_top(inner)
    ctxe=args[0]; rest=args[1:]
    ctor=ctxe[:ctxe.index('(')]
    cargs=split_top(ctxe[len(ctor)+1:-1])
    return dict(full=full,fn=fn,ctor=ctor,prog=cargs[0],accts=cargs[1],seeds=cargs[2:],rest=rest)
ANCH={'tf':'crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2(','sh':'crate::pump_fees::cpi::admin_cto_sharing_config(','po':'crate::pump_amm::cpi::admin_cto_pool(','cc':'crate::pump_amm::cpi::collect_coin_creator_fee(','ci':'anchor_spl::associated_token::create_idempotent(CpiContext::new(a.associated_token_program.to_account_info(),anchor_spl::associated_token::Create{payer:a.admin_set_creator_authority.to_account_info(),associated_token:a.current_creator_quote_token_account','ch':'anchor_spl::associated_token::create_idempotent(CpiContext::new(a.associated_token_program.to_account_info(),anchor_spl::associated_token::Create{payer:a.admin_set_creator_authority.to_account_info(),associated_token:a.holder_creator_vault_quote_token_account'}
def rebuild(p,prog=None,accts=None,pre=''):
    prog=prog or p['prog']; accts=accts or p['accts']
    c=p['ctor']+'('+','.join([prog,accts]+p['seeds'])+')'
    return pre+p['fn']+'('+','.join([c]+p['rest'])+')'
