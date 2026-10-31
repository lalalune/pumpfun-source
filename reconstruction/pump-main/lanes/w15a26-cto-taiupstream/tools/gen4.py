#!/usr/bin/env python3
"""gen4.py: tai base (and main) x accounts-as-noalias-param forms of the sweep / TCF helper. Writes e/{u,m}_<name>.py
(exact per-line edits for capvar.sh). Experiment only."""
import runpy
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a26-cto-taiupstream'
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w15a26-cto-taiupstream'
s=open(WT+'/programs/pump/src/creator/admin_cto.rs').read()
T=runpy.run_path(O+'/e/p_tai.py')['EDITS']
HEAD='sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{let a=&ctx.accounts;'
U={'sweepa':[(HEAD,'sweep(&ctx.accounts,ctx.bumps.creator_vault,&holder_key)).transpose()?.unwrap_or(0);fn sweep(a:&AdminCto,bump:u8,holder_key:&Pubkey)->Result<u64>{'),
             ('let vsigner:[&[&[u8]];1];let bump=ctx.bumps.creator_vault;','let vsigner:[&[&[u8]];1];')],
   'sweepab':[(HEAD,'sweep(&ctx.accounts,&ctx.bumps,&holder_key)).transpose()?.unwrap_or(0);fn sweep(a:&AdminCto,bumps:&AdminCtoBumps,holder_key:&Pubkey)->Result<u64>{'),
              ('let vsigner:[&[&[u8]];1];let bump=ctx.bumps.creator_vault;','let vsigner:[&[&[u8]];1];let bump=bumps.creator_vault;')]}
G='else if !a.coin_creator_vault_ata.data_is_empty(){'
def tcf(t):  # the TCF CPI moved into a nested fn tcf(a:&AdminCto) on the same line
    i=t.index(G+'crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2('); j=t.index('))?;}',i)+len('))?;}')
    call=t[i+len(G):j-len('?;}')]
    return t[:i]+G+'fn tcf(a:&AdminCto)->Result<()>{'+call+'}tcf(a)?;}'+t[j:]
def w(name,ed,fns=()):
    t=s
    for a,b in ed:
        assert t.count(a)==1,(a[:90],t.count(a)); t=t.replace(a,b)
    for f in fns: t=f(t)
    assert t.count('\n')==s.count('\n')
    E=[(a,b) for a,b in zip(s.split('\n'),t.split('\n')) if a!=b]
    open(f'{O}/e/{name}.py','w').write('EDITS='+repr(E)+'\n'); print(name,len(E))
w('u_sweepa',T+U['sweepa']); w('u_sweepab',T+U['sweepab']); w('u_tcfa',T,[tcf]); w('u_sweepa_tcfa',T+U['sweepa'],[tcf])
w('m_sweepa',U['sweepa']); w('m_sweepab',U['sweepab']); w('m_tcfa',[],[tcf])
