#!/usr/bin/env python3
"""gen.py <name> <src admin_cto.rs> <out edits.py>: poollit variants (AccountInfo spellings at pool CPI / collect event CPI)"""
import sys,re
name,src,out=sys.argv[1:4]; s=open(src).read()
L=[l for l in s.split('\n') if 'crate::pump_amm::cpi::admin_cto_pool(' in l]; assert len(L)==1; P=L[0]
F=['payer:a.admin_set_creator_authority','global_config:a.amm_global_config','pool:a.pool','pool_authority:a.pool_authority','system_program:a.system_program','event_authority:a.pump_amm_event_authority','program:a.pump_amm']
PROG='CpiContext::new_with_signer(a.pump_amm.to_account_info(),'
def lit(x,order='key,lamports,data,owner,rent_epoch,is_signer,is_writable,executable'):
    m={'key':'key:x.key','lamports':'lamports:x.lamports.clone()','data':'data:x.data.clone()','owner':'owner:x.owner','rent_epoch':'rent_epoch:x.rent_epoch','is_signer':'is_signer:x.is_signer','is_writable':'is_writable:x.is_writable','executable':'executable:x.executable'}
    return '{let x:&AccountInfo='+x+'.as_ref();AccountInfo{'+','.join(m[k] for k in order.split(','))+'}}'
def pool_sub(fn):
    q=P
    for f in F:
        k,v=f.split(':')
        q=q.replace(f+'.to_account_info()',k+':'+fn(v,k))
    return q
E=[]
ev_old='let authority_info=ctx.accounts.event_authority.to_account_info();'
def poolrep(q): E.append((P,q))
parts=name.split('+')
for n in parts:
    if n=='m': pass
    elif n=='pas': poolrep(pool_sub(lambda v,k: v+'.as_ref().clone()'))
    elif n=='pdc': poolrep(pool_sub(lambda v,k: '(*'+v+').clone()'))
    elif n=='pufcs': poolrep(pool_sub(lambda v,k: 'AccountInfo::clone('+v+'.as_ref())'))
    elif n=='ptai': poolrep(pool_sub(lambda v,k: 'ToAccountInfo::to_account_info(&'+v+')'))
    elif n=='pctxp': poolrep(P.replace(PROG,'CpiContext::new_with_signer(ctx.accounts.pump_amm.to_account_info(),'))
    elif n.startswith('plit_'):  # plit_<field>  literal at one field (prog = CpiContext program)
        f=n[5:]
        if f=='prog': poolrep(P.replace(PROG,'CpiContext::new_with_signer('+lit('a.pump_amm')+','))
        else:
            g=[x for x in F if x.split(':')[0]==f][0]; k,v=g.split(':')
            poolrep(P.replace(g+'.to_account_info()',k+':'+lit(v)))
    elif n=='porder_gp':
        q=P.replace('payer:a.admin_set_creator_authority.to_account_info(),global_config:a.amm_global_config.to_account_info(),','global_config:a.amm_global_config.to_account_info(),payer:a.admin_set_creator_authority.to_account_info(),'); assert q!=P; poolrep(q)
    elif n=='ecl': E.append((ev_old,'let authority_info=ctx.accounts.event_authority.clone();'))
    elif n=='eufcs': E.append((ev_old,'let authority_info=AccountInfo::clone(&ctx.accounts.event_authority);'))
    elif n=='ea': E.append((ev_old,'let authority_info=a.event_authority.to_account_info();'))
    elif n=='elit': E.append((ev_old,'let authority_info={let x=&ctx.accounts.event_authority;AccountInfo{key:x.key,lamports:x.lamports.clone(),data:x.data.clone(),owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}};'))
    elif n.startswith('w'):
        ES='let event_signers:[&[&[u8]];1];'
        D1='    '+ES+'if let Some((collected,quote_mint))='
        D0='    if let Some((collected,quote_mint))='
        AI='         let authority_info=ctx.accounts.event_authority.to_account_info();'
        AB='         let authority_bump=ctx.bumps.event_authority;'
        EI='         let event_infos=[authority_info];({let event_inner:&[&[u8]]=&[b"__event_authority",&[authority_bump]];'
        if n=='w_es_before_if': E.append(('  if do_collect{\n'+D1,'  '+ES+'if do_collect{\n'+D0))
        elif n=='w_es_blk': E.append((D1,D0)); E.append((AI,'         '+ES+AI.strip()))
        elif n=='w_es_after_infos': E.append((D1,D0)); E.append((EI,EI.replace('let event_infos=[authority_info];','let event_infos=[authority_info];'+ES)))
        elif n=='w_es_in_inner': E.append((D1,D0)); E.append((EI,EI.replace('({let event_inner','({'+ES+'let event_inner')))
        elif n=='w_bump_arr': E.append((EI,EI.replace('let event_infos=[authority_info];','let bump_arr=[authority_bump];let event_infos=[authority_info];').replace('&[authority_bump]]','&bump_arr]')))
        elif n=='w_bump_arr_ab': E.append((AB,AB+'let bump_arr=[authority_bump];')); E.append((EI,EI.replace('&[authority_bump]]','&bump_arr]')))
        elif n=='w_inner_out': E.append((EI,EI.replace('let event_infos=[authority_info];({let event_inner:&[&[u8]]=&[b"__event_authority",&[authority_bump]];','let event_inner:&[&[u8]]=&[b"__event_authority",&[authority_bump]];let event_infos=[authority_info];({')))
        elif n=='w_ab_first': E.append((AI+'\n'+AB,'         '+AB.strip()+AI.strip()+'\n'))
        else: raise SystemExit('unknown gene '+n)
    else: raise SystemExit('unknown gene '+n)
# compose pool edits: if several pool edits, chain them
out_e=[]; cur=P; pe=[e for e in E if e[0]==P]
for a,b in E:
    if a==P: continue
    out_e.append((a,b))
if pe:
    q=P
    for _,b in pe:
        # apply diff of b vs P onto q (only single-gene composition supported unless disjoint)
        q=b if q==P else q
    out_e.append((P,q))
open(out,'w').write('EDITS='+repr(out_e)+'\n')
