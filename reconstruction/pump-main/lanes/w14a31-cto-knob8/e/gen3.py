import json,os
OUT=os.path.dirname(os.path.abspath(__file__))
E="crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)"
T="crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&vsigner)"
OLD="   if amount>0{"+E+"?;"+T+".map(|()|amount)}else{Ok(amount)}}else{"
def v(new): return [(OLD,new)]
V={
'n_flip':v("   if amount==0{Ok(amount)}else{"+E+"?;"+T+".map(|()|amount)}}else{"),
'n_andthen':v("   if amount>0{"+E+".and_then(|()|"+T+").map(|()|amount)}else{Ok(amount)}}else{"),
'n_ensmatch':v("   if amount>0{match "+E+"{Ok(())=>"+T+".map(|()|amount),Err(e)=>Err(e)}}else{Ok(amount)}}else{"),
'n_ensiflet':v("   if amount>0{if let Err(e)="+E+"{return Err(e);}"+T+".map(|()|amount)}else{Ok(amount)}}else{"),
'n_qq':v("   if amount>0{"+E+"?;"+T+"?;Ok(amount)}else{Ok(amount)}}else{"),
'n_okq':v("   if amount>0{"+E+"?;Ok("+T+".map(|()|amount)?)}else{Ok(amount)}}else{"),
'n_tmatch':v("   if amount>0{"+E+"?;match "+T+"{Ok(())=>Ok(amount),Err(e)=>Err(e)}}else{Ok(amount)}}else{"),
'n_tmatch_errfirst':v("   if amount>0{"+E+"?;match "+T+"{Err(e)=>Err(e),Ok(())=>Ok(amount)}}else{Ok(amount)}}else{"),
'n_ens_mapamt':v("   if amount>0{"+E+".map(|()|amount)?;"+T+".map(|()|amount)}else{Ok(amount)}}else{"),
'n_both_and':v("   if amount>0{"+E+".and("+T+").map(|()|amount)}else{Ok(amount)}}else{"),
'n_gt_flip':v("   if 0<amount{"+E+"?;"+T+".map(|()|amount)}else{Ok(amount)}}else{"),
'n_ok0':v("   if amount>0{"+E+"?;"+T+".map(|()|amount)}else{Ok(0)}}else{"),
}
# k3 revalidated on current main
for n,e in V.items(): open(f'{OUT}/{n}.py','w').write('EDITS='+json.dumps(e)+'\n')
print(' '.join(V))
