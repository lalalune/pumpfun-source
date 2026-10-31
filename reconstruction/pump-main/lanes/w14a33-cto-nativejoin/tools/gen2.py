import json,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a33-cto-nativejoin/e/')
ENS="crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)"
TN="crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&vsigner)"
OLD=f"   if amount>0{{{ENS}?;{TN}.map(|()|amount)}}else{{Ok(amount)}}}}else{{"
J1=f"   (if amount>0{{{ENS}?;{TN}}}else{{Ok(())}}).map(|()|amount)}}else{{"
R0="if native{let rent=Rent::get()?;let min=rent.minimum_balance(0);let amount=a.creator_vault.lamports().saturating_sub(min);"
R={
'r1':"if native{let min={let rent=Rent::get()?;rent.minimum_balance(0)};let amount=a.creator_vault.lamports().saturating_sub(min);",
'r2':"if native{let min=Rent::get()?.minimum_balance(0);let amount=a.creator_vault.lamports().saturating_sub(min);",
'r4':"if native{let amount={let rent=Rent::get()?;let min=rent.minimum_balance(0);a.creator_vault.lamports().saturating_sub(min)};",
'r5':"if native{let rent:Rent=Rent::get()?;let amount=a.creator_vault.lamports().saturating_sub(rent.minimum_balance(0));",
'r6':"if native{let amount=a.creator_vault.lamports().saturating_sub(Rent::get()?.minimum_balance(0));",
}
names=[]
for k,v in R.items():
    open(O+k+'.py','w').write('EDITS='+json.dumps([[R0,v]])+'\n'); names.append(k)
    open(O+k+'j1.py','w').write('EDITS='+json.dumps([[R0,v],[OLD,J1]])+'\n'); names.append(k+'j1')
print(' '.join(names))
