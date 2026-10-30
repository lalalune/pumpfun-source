import json,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a33-cto-nativejoin/e/')
ENS="crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)"
TN="crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&vsigner)"
OLD=f"   if amount>0{{{ENS}?;{TN}.map(|()|amount)}}else{{Ok(amount)}}}}else{{"
F={
'j1':f"   (if amount>0{{{ENS}?;{TN}}}else{{Ok(())}}).map(|()|amount)}}else{{",
'j2':f"   let r=if amount>0{{{ENS}?;{TN}}}else{{Ok(())}};r?;Ok(amount)}}else{{",
'j3':f"   let r=if amount>0{{{ENS}?;{TN}}}else{{Ok(())}};r.map(|()|amount)}}else{{",
'j4':f"   if amount==0{{return Ok(0);}}{ENS}?;{TN}.map(|()|amount)}}else{{",
'j5':f"   if amount==0{{return Ok(amount);}}{ENS}?;{TN}?;Ok(amount)}}else{{",
'j6':f"   let r:Result<()>=(||{{if amount>0{{{ENS}?;{TN}?;}}Ok(())}})();r.map(|()|amount)}}else{{",
'j7':f"   (if amount>0{{{ENS}?;{TN}}}else{{Ok(())}})?;Ok(amount)}}else{{",
'j10':f"   (if amount>0{{{ENS}.and_then(|()|{TN})}}else{{Ok(())}}).map(|()|amount)}}else{{",
'j12':f"   if amount>0{{{ENS}?;return {TN}.map(|()|amount);}}Ok(amount)}}else{{",
'j14':f"   if amount>0{{{ENS}?;if let Err(e)={TN}{{return Err(e);}}}}Ok(amount)}}else{{",
'j15':f"   if amount>0{{{ENS}?;{TN}.map(|_|amount)}}else{{Ok(amount)}}}}else{{",
'j21':f"   let r=if amount>0{{{ENS}?;{TN}}}else{{Ok(())}};match r{{Ok(())=>Ok(amount),Err(e)=>Err(e)}}}}else{{",
'j22':f"   let r=if amount>0{{{ENS}.and_then(|()|{TN})}}else{{Ok(())}};r.map(|()|amount)}}else{{",
'j23':f"   if amount>0{{let r={ENS};r?;{TN}.map(|()|amount)}}else{{Ok(amount)}}}}else{{",
}
for k,v in F.items():
    open(O+k+'.py','w').write('EDITS='+json.dumps([[OLD,v]])+'\n')
# j16: amount join for whole sweep
E16=[["  if native{let rent=Rent::get()?;","  Ok(if native{let rent=Rent::get()?;"],[OLD,f"   if amount>0{{{ENS}?;{TN}?;}}amount}}else{{"],["\n   Ok(amount)}\n","\n   amount})\n"]]
open(O+'j16.py','w').write('EDITS='+json.dumps(E16)+'\n')
# j17: Result<()> join for whole sweep: let (r,amount)=...; r?; Ok(amount)
E17=[["  if native{let rent=Rent::get()?;","  let (r,amount)=if native{let rent=Rent::get()?;"],[OLD,f"   (if amount>0{{{ENS}?;{TN}}}else{{Ok(())}},amount)}}else{{"],["\n   Ok(amount)}\n","\n   (Ok(()),amount)};r.map(|()|amount)\n"]]
open(O+'j17.py','w').write('EDITS='+json.dumps(E17)+'\n')
print(' '.join(list(F)+['j16','j17']))
