import os,sys
d=sys.argv[1]
exec(open(os.path.join(os.path.dirname(__file__),'genarm.py')).read().split("V={")[0].replace("d=sys.argv[1]",""))
B9='if frozen{'+R+'}else if amount>0{'+C0+'?;'+TV+'?;return Ok(amount);}\n   Ok(amount)}'
NE='crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)?;'
TN='crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&vsigner)'
NAT='if amount>0{'+NE+TN+'.map(|()|amount)}else{Ok(amount)}}else{'
V={
'c1_natq':[(CUR,B9),(NAT,'if amount>0{'+NE+TN+'?;Ok(amount)}else{Ok(amount)}}else{')],
'c2_natret':[(CUR,B9),(NAT,'if amount>0{'+NE+TN+'?;return Ok(amount);}else{Ok(amount)}}else{')],
'c4_frret':[(CUR,'if frozen{'+R+'return Ok(amount);}else if amount>0{'+C0+'?;'+TV+'?;return Ok(amount);}\n   Ok(amount)}')],
'c5_pol':[(CUR,'if !frozen{if amount>0{'+C0+'?;'+TV+'?;return Ok(amount);}}else{'+R+'}\n   Ok(amount)}')],
'c6_zero':[(CUR,'if frozen{'+R+'}else if amount==0{return Ok(0);}else{'+C0+'?;'+TV+'?;return Ok(amount);}\n   Ok(amount)}')],
'c7_cret':[(CUR,'if frozen{'+R+'}else if amount>0{'+C0+'?;'+TV+'?;return Ok(amount);}\n   return Ok(amount);}')],
'c8_retall':[(CUR,'if frozen{'+R+'return Ok(amount);}else if amount>0{'+C0+'?;'+TV+'?;return Ok(amount);}else{return Ok(amount);}\n   }')],
'c9_okval':[(CUR,'if frozen{'+R+'}else if amount>0{'+C0+'?;'+TV+'?;return Ok(amount);}\n   Ok(0)}')],
'c10_frz0':[(CUR,'if frozen{'+R+'return Ok(0);}else if amount>0{'+C0+'?;'+TV+'?;return Ok(amount);}\n   Ok(amount)}')],
}
for n,v in V.items():
    open(f'{d}/{n}.py','w').write('EDITS=%r\n'%(v,))
print(' '.join(V))
