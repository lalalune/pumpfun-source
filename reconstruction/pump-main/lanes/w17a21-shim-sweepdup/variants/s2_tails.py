N0='   (if amount>0{crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)?;crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&vsigner)}else{Ok(())}).map(|()|amount)}else{'
N1='   if amount>0{crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)?;crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&vsigner)?;}Ok(amount)}else{'
N2='   if amount>0{crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)?;crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&vsigner).map(|()|amount)}else{Ok(0)}}else{'
T0=',amount,&vsigner))?;return Ok(amount);}'
T1=',amount,&vsigner))?;}'
V={
 's_nat1':[(N0,N1)],
 's_nat0':[(N0,N2)],
 's_tok1':[(T0,T1)],
 's_nt11':[(N0,N1),(T0,T1)],
}
