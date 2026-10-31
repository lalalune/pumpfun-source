import json,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a33-cto-nativejoin/e/')
SRC=open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a33-cto-nativejoin/programs/pump/src/creator/admin_cto.rs').read()
ENS="crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)"
TN="crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&vsigner)"
CUR=f"   (if amount>0{{{ENS}?;{TN}}}else{{Ok(())}}).map(|()|amount)}}else{{"
R0="if native{let min={let rent=Rent::get()?;rent.minimum_balance(0)};let amount=a.creator_vault.lamports().saturating_sub(min);"
assert SRC.count(CUR)==1 and SRC.count(R0)==1
N={
'v_old':f"   if amount>0{{{ENS}?;{TN}.map(|()|amount)}}else{{Ok(amount)}}}}else{{",
'v_j3':f"   let r=if amount>0{{{ENS}?;{TN}}}else{{Ok(())}};r.map(|()|amount)}}else{{",
'v_j6':f"   let r:Result<()>=(||{{if amount>0{{{ENS}?;{TN}?;}}Ok(())}})();r.map(|()|amount)}}else{{",
'v_j10':f"   (if amount>0{{{ENS}.and_then(|()|{TN})}}else{{Ok(())}}).map(|()|amount)}}else{{",
'v_ok0':f"   if amount>0{{{ENS}?;{TN}.map(|()|amount)}}else{{Ok(0)}}}}else{{",
'v_mret':f"   return (if amount>0{{{ENS}?;{TN}}}else{{Ok(())}}).map(|()|amount);}}else{{",
'v_and':f"   (if amount>0{{{ENS}?;{TN}}}else{{Ok(())}}).and(Ok(amount))}}else{{",
'v_match':f"   match if amount>0{{{ENS}?;{TN}}}else{{Ok(())}}{{Ok(())=>Ok(amount),Err(e)=>Err(e)}}}}else{{",
}
R={
'v_r2':"if native{let min=Rent::get()?.minimum_balance(0);let amount=a.creator_vault.lamports().saturating_sub(min);",
'v_r4':"if native{let amount={let rent=Rent::get()?;let min=rent.minimum_balance(0);a.creator_vault.lamports().saturating_sub(min)};",
'v_r7':"if native{let min={let rent:Rent=Rent::get()?;rent.minimum_balance(0)};let amount=a.creator_vault.lamports().saturating_sub(min);",
'v_r8':"if native{let min=Rent::get().map(|r|r.minimum_balance(0))?;let amount=a.creator_vault.lamports().saturating_sub(min);",
'v_r9':"if native{let amount={let min=Rent::get()?.minimum_balance(0);a.creator_vault.lamports().saturating_sub(min)};",
}
for k,v in N.items(): open(O+k+'.py','w').write('EDITS='+json.dumps([[CUR,v]])+'\n')
for k,v in R.items(): open(O+k+'.py','w').write('EDITS='+json.dumps([[R0,v]])+'\n')
print(' '.join(list(N)+list(R)))
