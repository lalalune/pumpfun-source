import json,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a33-cto-nativejoin/e/')
SRC=open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a33-cto-nativejoin/programs/pump/src/creator/admin_cto.rs').read()
F0="   if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);}else if amount>0{"
E0="amount,&vsigner)?;return Ok(amount);}\n   Ok(amount)}"
assert SRC.count(F0)==1 and SRC.count(E0)==1
S={
't_ok0':[[E0,"amount,&vsigner)?;return Ok(amount);}\n   Ok(0)}"]],
't_frz_ret':[[F0,"   if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);return Ok(amount);}else if amount>0{"]],
't_frz_ret0':[[F0,"   if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);return Ok(0);}else if amount>0{"]],
't_frz_ret_ok0':[[F0,"   if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);return Ok(amount);}else if amount>0{"],[E0,"amount,&vsigner)?;return Ok(amount);}\n   Ok(0)}"]],
't_ret_else':[[E0,"amount,&vsigner)?;return Ok(amount);}else{return Ok(amount);}\n   }"]],
't_ok_amt_tail':[[E0,"amount,&vsigner)?;Ok(amount)}else{Ok(amount)}\n   }"]],
't_frz_else':[[F0,"   if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);Ok(amount)}else if amount>0{"],[E0,"amount,&vsigner)?;Ok(amount)}else{Ok(amount)}\n   }"]],
't_ok0_ret0':[[E0,"amount,&vsigner)?;return Ok(amount);}\n   Ok(0u64)}"]],
}
for k,v in S.items(): open(O+k+'.py','w').write('EDITS='+json.dumps(v)+'\n')
print(' '.join(S))
