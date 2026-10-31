#!/usr/bin/env python3
"""gen.py: w15a17 spelling generator (experiment only). Writes e/<name>.py exact-edit files for the TCF CPI (line 661)
and the sweep token-arm create_idempotent (line 719)."""
import os
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w15a17-cto-tcfsroa64'
E='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a17-cto-tcfsroa64/e'
s=open(WT+'/programs/pump/src/creator/admin_cto.rs').read()
def split_top(body):
    out=[];d=0;cur=''
    for ch in body:
        if ch in '({[': d+=1
        if ch in ')}]': d-=1
        if ch==',' and d==0: out.append(cur);cur=''
        else: cur+=ch
    if cur: out.append(cur)
    return [(f.split(':',1)[0],f.split(':',1)[1]) for f in out]
V={}
# ---- TCF (line 661)
L=s.split('\n')[660]
fn='crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2('
head=fn+'CpiContext::new('
i=L.index(head)+len(head)
PROG='{let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{owner:x.owner,key:x.key,lamports:x.lamports.clone(),data:x.data.clone(),rent_epoch:x.rent_epoch,executable:x.executable,is_writable:x.is_writable,is_signer:x.is_signer}}'
assert L[i:].startswith(PROG+',')
rest=L[i+len(PROG)+1:]; tail='))?;}'; assert rest.endswith(tail)
ACCTS=rest[:-len(tail)]
OLD=head+PROG+','+ACCTS+'))?;'
assert s.count(OLD)==1
TN='crate::pump_amm::cpi::accounts::TransferCreatorFeesToPumpV2'
assert ACCTS.startswith(TN+'{') and ACCTS.endswith('}')
F=split_top(ACCTS[len(TN)+1:-1])
V['t_ctxsplit']='let cpi=CpiContext::new('+PROG+','+ACCTS+');'+fn+'cpi)?;'
V['t_tuple']='let (program,accounts)=('+PROG+','+ACCTS+');'+fn+'CpiContext::new(program,accounts))?;'
V['t_tuplet']='let t=('+PROG+','+ACCTS+');'+fn+'CpiContext::new(t.0,t.1))?;'
V['t_defer']='let accounts;'+fn+'CpiContext::new('+PROG+',{accounts='+ACCTS+';accounts}))?;'
V['t_defer2']='let accounts;let program='+PROG+';accounts='+ACCTS+';'+fn+'CpiContext::new(program,accounts))?;'
V['t_allbind']='let cpi_program='+PROG+';'+''.join(f'let {k}={v};' for k,v in F)+fn+'CpiContext::new(cpi_program,'+TN+'{'+','.join(k for k,_ in F)+'}))?;'
V['t_subbind']=fn+'CpiContext::new('+PROG+',{'+''.join(f'let {k}={v};' for k,v in F)+TN+'{'+','.join(k for k,_ in F)+'}}))?;'
# sub-literals given their own let inside the block: {let x=..;let ai=AccountInfo{..};ai}
def subloc(v):
    if v.startswith('{let x:&AccountInfo=') and v.endswith('}}'):
        j=v.index(';AccountInfo{'); return v[:j]+';let ai='+v[j+1:-1]+';ai}'
    return v
V['t_subloc']=head+PROG+','+TN+'{'+','.join(f'{k}:{subloc(v)}' for k,v in F)+'}))?;'
PSUB=subloc(PROG)
V['t_progloc']=head+PSUB+','+ACCTS+'))?;'
V['t_allloc']=head+PSUB+','+TN+'{'+','.join(f'{k}:{subloc(v)}' for k,v in F)+'}))?;'
for k in list(V):
    if k.startswith('t_'):
        open(f'{E}/{k}.py','w').write('EDITS='+repr([(OLD,V[k])])+'\n')
# ---- token arm (line 719)
L2=s.split('\n')[718]
KH='anchor_spl::associated_token::create_idempotent(CpiContext::new('
ATP='a.associated_token_program.to_account_info()'
CN='anchor_spl::associated_token::Create'
k0=L2.index(KH); k1=L2.index(').and_then(',k0)
OLD2=L2[k0:k1+1]
assert s.count(OLD2)==1
inner=OLD2[len(KH):-2]  # ATP,Create{..}
assert inner.startswith(ATP+','+CN+'{')
CR=inner[len(ATP)+1:]
CF=split_top(CR[len(CN)+1:-1])
W={}
W['k_createlet']='{let accounts='+CR+';'+KH+ATP+',accounts))}'
W['k_allbind']='{let cpi_program='+ATP+';'+''.join(f'let {k}={v};' for k,v in CF)+KH+'cpi_program,'+CN+'{'+','.join(k for k,_ in CF)+'}))}'
W['k_tuple']='{let (program,accounts)=('+ATP+','+CR+');'+KH+'program,accounts))}'
W['k_ctxsplit']='{let cpi=CpiContext::new('+ATP+','+CR+');anchor_spl::associated_token::create_idempotent(cpi)}'
W['k_subbind']=KH+ATP+',{'+''.join(f'let {k}={v};' for k,v in CF)+CN+'{'+','.join(k for k,_ in CF)+'}}))'
for k,v in W.items():
    open(f'{E}/{k}.py','w').write('EDITS='+repr([(OLD2,v)])+'\n')
print([k for k in V],[k for k in W])
# ---- FRU grid on the TCF sub-literals (x {main program, fru1 program})
TAILD=',rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}'
P_FRU1='{let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{owner:x.owner,key:x.key,lamports:x.lamports.clone(),data:x.data.clone(),..*x}}'
import itertools
FD=dict(F); SUBS=['coin_creator_vault_ata','pump_creator_vault_ata','program']
for k in SUBS: assert FD[k].count(TAILD)==1,k
for pf in (0,1):
    for bits in itertools.product((0,1),repeat=3):
        if not pf and not any(bits): continue
        nm='g'+('f' if pf else 'm')+''.join(map(str,bits))
        F2=[(k,(v.replace(TAILD,',..*x}') if k in SUBS and bits[SUBS.index(k)] else v)) for k,v in F]
        new=head+(P_FRU1 if pf else PROG)+','+TN+'{'+','.join(f'{k}:{v}' for k,v in F2)+'}))?;'
        open(f'{E}/{nm}.py','w').write('EDITS='+repr([(OLD,new)])+'\n')
# ---- CpiContext struct literals, program first
V2={}
V2['lit2']=fn+'CpiContext{program:'+PROG+',accounts:'+ACCTS+',remaining_accounts:Vec::new(),signer_seeds:&[]})?;'
V2['lit3']=fn+'CpiContext{program:'+PROG+',accounts:'+ACCTS+',signer_seeds:&[],remaining_accounts:Vec::new()})?;'
V2['lit4']=fn+'CpiContext{program:'+PROG+',remaining_accounts:Vec::new(),accounts:'+ACCTS+',signer_seeds:&[]})?;'
for k,v in V2.items(): open(f'{E}/{k}.py','w').write('EDITS='+repr([(OLD,v)])+'\n')
open(f'{E}/k_lit2.py','w').write('EDITS='+repr([(OLD2,'anchor_spl::associated_token::create_idempotent(CpiContext{program:'+ATP+',accounts:'+CR+',remaining_accounts:Vec::new(),signer_seeds:&[]})')])+'\n')
# ---- program literal orders (pre-sink IR order reasoning: orig asm E W S R O after the payer inc)
X='{let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{'
FL={'K':'key:x.key','L':'lamports:x.lamports.clone()','D':'data:x.data.clone()','O':'owner:x.owner','R':'rent_epoch:x.rent_epoch','S':'is_signer:x.is_signer','W':'is_writable:x.is_writable','E':'executable:x.executable'}
for o in ['KLDORSWE','KLDOREWS','KLDREWSO','KLDRSWEO','KLDOEWSR']:
    p=X+','.join(FL[c] for c in o)+'}}'
    open(f'{E}/p_{o}.py','w').write('EDITS='+repr([(OLD,head+p+','+ACCTS+'))?;')])+'\n')
open(f'{E}/p_tai.py','w').write('EDITS='+repr([(OLD,head+'a.pump_amm.to_account_info(),'+ACCTS+'))?;')])+'\n')
open(f'{E}/p_clone.py','w').write('EDITS='+repr([(OLD,head+'AccountInfo::clone(a.pump_amm.as_ref()),'+ACCTS+'))?;')])+'\n')
# ---- sub-literals replaced by to_account_info (do the padding allocas discriminate?)
SRC={'coin_creator_vault_ata':'a.coin_creator_vault_ata','pump_creator_vault_ata':'a.creator_vault_quote_token_account','program':'a.pump_amm'}
for i,k in enumerate(SUBS):
    F2=[(kk,(SRC[k]+'.to_account_info()' if kk==k else v)) for kk,v in F]
    new=head+PROG+','+TN+'{'+','.join(f'{kk}:{v}' for kk,v in F2)+'}))?;'
    open(f'{E}/s_tai{i}.py','w').write('EDITS='+repr([(OLD,new)])+'\n')
F2=[(kk,(SRC[kk]+'.to_account_info()' if kk in SUBS else v)) for kk,v in F]
open(f'{E}/s_taiall.py','w').write('EDITS='+repr([(OLD,head+'a.pump_amm.to_account_info(),'+TN+'{'+','.join(f'{kk}:{v}' for kk,v in F2)+'}))?;')])+'\n')
# ---- joint grid: CPI program {lit,tai} x each sub-literal {lit,tai}
for pf in (0,1):
    for bits in itertools.product((0,1),repeat=3):
        nm='j'+('t' if pf else 'l')+''.join(map(str,bits))
        F2=[(kk,(SRC[kk]+'.to_account_info()' if kk in SUBS and bits[SUBS.index(kk)] else v)) for kk,v in F]
        new=head+('a.pump_amm.to_account_info()' if pf else PROG)+','+TN+'{'+','.join(f'{kk}:{v}' for kk,v in F2)+'}))?;'
        open(f'{E}/{nm}.py','w').write('EDITS='+repr([(OLD,new)])+'\n')
for o in ['KOLDREWS','KLODREWS','KLODRSWE']:
    p=X+','.join(FL[c] for c in o)+'}}'
    open(f'{E}/p_{o}.py','w').write('EDITS='+repr([(OLD,head+p+','+ACCTS+'))?;')])+'\n')
