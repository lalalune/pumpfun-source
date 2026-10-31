#!/usr/bin/env python3
"""gen.py: write e/<name>.py EDITS for the curve-tail screen (w14a34)."""
import itertools,os,json
D=os.path.dirname(os.path.abspath(__file__))+'/e'
BLK=("  let curve=&mut ctx.accounts.bonding_curve;let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;\n"
"  curve.creator=target;\n"
"  curve.is_cashback_coin=cashback;\n"
"  curve.is_holder_reward=holder;\n"
"  if let Some(f)=fee{curve.creator_fee_bps=f;}\n"
"  curve.can_edit_creator_fee=false;\n")
def lay(stmts,n=6):
    # place statements one per line, extra joined on last line, pad with blank lines
    if len(stmts)>n: stmts=stmts[:n-1]+[''.join(stmts[n-1:])]
    L=['  '+s for s in stmts]+['']*(n-len(stmts))
    return '\n'.join(L)+'\n'
S=dict(
 cur='let curve=&mut ctx.accounts.bonding_curve;',
 oc='let old_creator=curve.creator;', of='let old_fee=curve.creator_fee_bps;',
 T='curve.creator=target;', C='curve.is_cashback_coin=cashback;', H='curve.is_holder_reward=holder;',
 F='if let Some(f)=fee{curve.creator_fee_bps=f;}', E='curve.can_edit_creator_fee=false;')
V={}
def blk(order,cur=None,oc=None,of=None,sub={}):
    s=dict(S); s.update(sub)
    if cur: s['cur']=cur
    if oc is not None: s['oc']=oc
    if of is not None: s['of']=of
    first=s['cur']+s['oc']+s['of']
    rest=[s[k] for k in order]
    return lay([first]+rest)
def blk2(stmts): return lay(stmts)
# P: permutations of C,H,F,E after T
for p in itertools.permutations('CHFE'):
    o='T'+''.join(p)
    if o=='TCHFE': continue
    V['p_'+o]=blk(o)
# creator later
for o in ['CTHFE','HTCFE','CHTFE','HCTFE','CHFTE','CHFET','ETCHF','FTCHE']:
    V['p_'+o]=blk(o)
# R: read positions
V['r_of_afterT']=blk2([S['cur']+S['oc'],S['T']+S['of'],S['C'],S['H'],S['F'],S['E']])
V['r_of_beforeF']=blk2([S['cur']+S['oc'],S['T'],S['C'],S['H'],S['of']+S['F'],S['E']])
V['r_of_first']=blk2([S['cur']+S['of']+S['oc'],S['T'],S['C'],S['H'],S['F'],S['E']])
V['r_oc_replace']=blk2([S['cur']+'let old_fee=curve.creator_fee_bps;',"let old_creator=core::mem::replace(&mut curve.creator,target);",S['C'],S['H'],S['F'],S['E']])
V['r_oc_replace_first']=blk2([S['cur']+"let old_creator=core::mem::replace(&mut curve.creator,target);",S['of'],S['C'],S['H'],S['F'],S['E']])
V['r_of_matchrep']=blk2([S['cur']+S['oc'],S['T'],S['C'],S['H'],"let old_fee=match fee{Some(f)=>core::mem::replace(&mut curve.creator_fee_bps,f),None=>curve.creator_fee_bps};",S['E']])
V['r_both_replace']=blk2([S['cur'],"let old_creator=core::mem::replace(&mut curve.creator,target);",S['C'],S['H'],"let old_fee=match fee{Some(f)=>core::mem::replace(&mut curve.creator_fee_bps,f),None=>curve.creator_fee_bps};",S['E']])
# D: derivation of the curve reference
for nm,c in [('d_derefbox','let curve=&mut *ctx.accounts.bonding_curve;'),('d_derefacct','let curve=&mut **ctx.accounts.bonding_curve;'),
             ('d_typed','let curve:&mut BondingCurve=&mut ctx.accounts.bonding_curve;'),('d_accmut','let curve=&mut ctx.accounts.bonding_curve.as_mut();'),
             ('d_acclet','let accs=&mut ctx.accounts;let curve=&mut accs.bonding_curve;')]:
    V[nm]=blk('TCHFE',cur=c)
# repeated paths, no let
rp=lambda x:x.replace('curve.','ctx.accounts.bonding_curve.')
V['d_paths']=blk2(['let old_creator=ctx.accounts.bonding_curve.creator;let old_fee=ctx.accounts.bonding_curve.creator_fee_bps;']+[rp(S[k]) for k in 'TCHFE'])
# F: fee spellings
for nm,f in [('f_match','match fee{Some(f)=>curve.creator_fee_bps=f,None=>{}}'),('f_issome','if fee.is_some(){curve.creator_fee_bps=fee.unwrap();}'),
             ('f_unwrapor_old','curve.creator_fee_bps=fee.unwrap_or(old_fee);'),('f_unwrapor_cur','curve.creator_fee_bps=fee.unwrap_or(curve.creator_fee_bps);'),
             ('f_map','fee.map(|f|curve.creator_fee_bps=f);'),('f_asref','if let Some(&f)=fee.as_ref(){curve.creator_fee_bps=f;}'),
             ('f_ifletmut','if let Some(f)=fee{let p=&mut curve.creator_fee_bps;*p=f;}')]:
    V[nm]=blk('TCHFE',sub={'F':f})
# H/C: flag spellings
V['h_branch']=blk2([S['cur']+S['oc']+S['of'],S['T'],'if holder{curve.is_holder_reward=true;curve.is_cashback_coin=false;}else{curve.is_holder_reward=false;curve.is_cashback_coin=cashback;}','',S['F'],S['E']])
V['h_branch2']=blk2([S['cur']+S['oc']+S['of'],S['T'],'if holder{curve.is_cashback_coin=false;curve.is_holder_reward=true;}else{curve.is_cashback_coin=cashback;curve.is_holder_reward=false;}','',S['F'],S['E']])
V['h_ifset']=blk2([S['cur']+S['oc']+S['of'],S['T'],S['C'],'curve.is_holder_reward=if holder{true}else{false};',S['F'],S['E']])
V['h_tuple']=blk2([S['cur']+S['oc']+S['of'],S['T'],'(curve.is_cashback_coin,curve.is_holder_reward)=(cashback,holder);','',S['F'],S['E']])
V['h_tuple_hc']=blk2([S['cur']+S['oc']+S['of'],S['T'],'(curve.is_holder_reward,curve.is_cashback_coin)=(holder,cashback);','',S['F'],S['E']])
V['h_all_tuple']=blk2([S['cur']+S['oc']+S['of'],'(curve.creator,curve.is_cashback_coin,curve.is_holder_reward)=(target,cashback,holder);','','',S['F'],S['E']])
for nm,ed in V.items():
    assert ed.count('\n')==BLK.count('\n'),nm
    open(f'{D}/{nm}.py','w').write('EDITS='+repr([(BLK,ed)])+'\n')
print(len(V)); print(' '.join(V))
