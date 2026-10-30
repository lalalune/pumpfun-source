import json,os
OUT=os.path.dirname(os.path.abspath(__file__))
E="crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)"
T="crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&vsigner)"
OLD="   if amount>0{"+E+"?;"+T+".map(|()|amount)}else{Ok(amount)}}else{"
def v(new): return [(OLD,new)]
V={
'h_clos':v("   if amount>0{(||->Result<()>{"+E+"?;"+T+"})().map(|()|amount)}else{Ok(amount)}}else{"),
'h_clos2':v("   if amount>0{(||->Result<u64>{"+E+"?;"+T+"?;Ok(amount)})()}else{Ok(amount)}}else{"),
'h_fn':v("   if amount>0{fn pay(a:&AdminCto,amount:u64,vsigner:&[&[&[u8]]])->Result<()>{"+E+"?;"+T.replace('&vsigner','vsigner')+"}pay(a,amount,&vsigner).map(|()|amount)}else{Ok(amount)}}else{"),
'h_fn2':v("   if amount>0{fn pay(a:&AdminCto,amount:u64,vsigner:&[&[&[u8]]])->Result<u64>{"+E+"?;"+T.replace('&vsigner','vsigner')+".map(|()|amount)}pay(a,amount,&vsigner)}else{Ok(amount)}}else{"),
'h_ensfn':v("   if amount>0{fn ens(a:&AdminCto)->Result<()>{"+E+"}ens(a)?;"+T+".map(|()|amount)}else{Ok(amount)}}else{"),
'h_ensclos':v("   if amount>0{(||"+E+")()?;"+T+".map(|()|amount)}else{Ok(amount)}}else{"),
'h_tclos':v("   if amount>0{"+E+"?;(||"+T+")().map(|()|amount)}else{Ok(amount)}}else{"),
'h_blk':v("   if amount>0{let r:Result<()>={"+E+"?;"+T+"};r.map(|()|amount)}else{Ok(amount)}}else{"),
}
for n,e in V.items(): open(f'{OUT}/{n}.py','w').write('EDITS='+json.dumps(e)+'\n')
print(' '.join(V))
