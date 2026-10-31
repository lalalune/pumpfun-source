#!/usr/bin/env python3
"""gen2.py: pool gate / pargs / nf combos with curve-store orders (w14a34)."""
import os,runpy,itertools
D=os.path.dirname(os.path.abspath(__file__))
G=runpy.run_path(D+'/gen.py.lib') if False else None
BLK=("  let curve=&mut ctx.accounts.bonding_curve;let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;\n"
"  curve.creator=target;\n"
"  curve.is_cashback_coin=cashback;\n"
"  curve.is_holder_reward=holder;\n"
"  if let Some(f)=fee{curve.creator_fee_bps=f;}\n"
"  curve.can_edit_creator_fee=false;\n")
HF=BLK.replace("  curve.is_cashback_coin=cashback;\n  curve.is_holder_reward=holder;\n","  curve.is_holder_reward=holder;\n  curve.is_cashback_coin=cashback;\n")
PU="let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;"
PA="let pargs=(target,a.bonding_curve.is_holder_reward,fee);"
NF="let nf=a.bonding_curve.creator_fee_bps;"
EV="new_creator_fee_bps:nf,"
K=dict(
 own=[(PU,"let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();")],
 ph=[(PA,"let pargs=(target,holder,fee);")],
 hf=[(BLK,HF)],
 e1=[(NF,""),(EV,"new_creator_fee_bps:a.bonding_curve.creator_fee_bps,")],
 nfafter=[(NF+PU,PU+NF)],
 pa_first=[(NF+PU+PA,PA+NF+PU)],
 nf_blk=[("  curve.can_edit_creator_fee=false;\n (old_creator,old_fee)};","  curve.can_edit_creator_fee=false;let nf=curve.creator_fee_bps;\n (old_creator,old_fee,nf)};"),
         (" let (old_creator,old_fee)={"," let (old_creator,old_fee,nf)={"),(NF,"")],
)
combos=[('own',),('ph',),('own','ph'),('own','hf'),('own','ph','hf'),('ph','hf'),('e1',),('own','e1'),('own','ph','e1'),('nfafter',),('own','nfafter'),('pa_first',),('own','pa_first'),('nf_blk',),('own','nf_blk'),('e1','ph'),('e1','hf')]
names=[]
for c in combos:
    n='g_'+'_'.join(c); E=[]
    for k in c: E+=K[k]
    # nfafter after e1 impossible; fine
    open(f'{D}/e/{n}.py','w').write('EDITS='+repr(E)+'\n'); names.append(n)
print(' '.join(names))
