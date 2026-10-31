import os
D=os.path.dirname(os.path.abspath(__file__))+'/e'
PU="let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;"
EV="new_creator_fee_bps:a.bonding_curve.creator_fee_bps,"
BEND="  curve.can_edit_creator_fee=false;\n (old_creator,old_fee)};"
X={
 'k_nfold':[(PU,"let nf=a.bonding_curve.creator_fee_bps;"+PU),(EV,"new_creator_fee_bps:nf,")],
 'k_nfafter':[(PU,PU+"let nf=a.bonding_curve.creator_fee_bps;"),(EV,"new_creator_fee_bps:nf,")],
 'k_nfblk':[(BEND,"  curve.can_edit_creator_fee=false;let nf=curve.creator_fee_bps;\n (old_creator,old_fee,nf)};"),(" let (old_creator,old_fee)={"," let (old_creator,old_fee,nf)={"),(EV,"new_creator_fee_bps:nf,")],
 'k_nfev_local':[(EV,"new_creator_fee_bps:{let nf=a.bonding_curve.creator_fee_bps;nf},")],
 'k_evnf_unwrap':[(EV,"new_creator_fee_bps:fee.unwrap_or(old_fee),")],
 'k_own':[(PU,"let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();")],
}
for k,v in X.items(): open(f'{D}/{k}.py','w').write('EDITS='+repr(v)+'\n')
print(' '.join(X))
