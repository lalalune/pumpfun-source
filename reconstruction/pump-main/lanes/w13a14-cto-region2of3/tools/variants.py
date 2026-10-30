# Region-2 (orig rel 0x23b0..0x4760: sweep head, transfer CPI, seeds, sharing CPI start) source variants on main 8f050a236.
V = {}
DEST = '  let dest=Pubkey::find_program_address(&[b"creator-vault",holder_key.as_ref()],&crate::ID).0;'
CHK = 'if a.holder_creator_vault.key()!=dest{return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((a.holder_creator_vault.key(),dest)));}'
AMMF = '  let amm_frozen=!a.coin_creator_vault_ata.data_is_empty()&&token_frozen(a.coin_creator_vault_ata.as_ref())?;'
L660 = 'if amm_frozen{require!(token_raw_amount(a.coin_creator_vault_ata.as_ref())?==0,PumpError::CtoSharedVaultFrozen);}'
SEEDS = 'let bump=[ctx.bumps.creator_vault];let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&bump];let vsigner:&[&[&[u8]];1]=&[vaultseeds];'
V['dest_tuple'] = [(DEST, '  let (dest,_)=Pubkey::find_program_address(&[b"creator-vault",holder_key.as_ref()],&crate::ID);')]
V['chk_rev'] = [(CHK, 'if dest!=a.holder_creator_vault.key(){return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((a.holder_creator_vault.key(),dest)));}')]
V['chk_rkeq'] = [(CHK, 'require_keys_eq!(a.holder_creator_vault.key(),dest,anchor_lang::error::ErrorCode::ConstraintSeeds);')]
V['chk_hk_local'] = [(CHK, 'let hv=a.holder_creator_vault.key();if hv!=dest{return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((hv,dest)));}')]
V['ammf_if'] = [(AMMF, '  let amm_frozen=if a.coin_creator_vault_ata.data_is_empty(){false}else{token_frozen(a.coin_creator_vault_ata.as_ref())?};')]
V['l660_ne'] = [(L660, 'if amm_frozen{if token_raw_amount(a.coin_creator_vault_ata.as_ref())?!=0{return err!(PumpError::CtoSharedVaultFrozen);}}')]
V['l660_let'] = [(L660, 'if amm_frozen{let amt=token_raw_amount(a.coin_creator_vault_ata.as_ref())?;require!(amt==0,PumpError::CtoSharedVaultFrozen);}')]
V['seeds_old_first'] = [(SEEDS, 'let old=a.current_creator.key();let bump=[ctx.bumps.creator_vault];let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&bump];let vsigner:&[&[&[u8]];1]=&[vaultseeds];')]
V['seeds_slice'] = [(SEEDS, 'let bump=[ctx.bumps.creator_vault];let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&bump];let vsigner:&[&[&[u8]]]=&[vaultseeds];')]
V['seeds_bump_ref'] = [(SEEDS, 'let bump=ctx.bumps.creator_vault;let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&[bump]];let vsigner:&[&[&[u8]];1]=&[vaultseeds];')]
V['seeds_old_ref'] = [(SEEDS, 'let bump=[ctx.bumps.creator_vault];let old=a.current_creator.key;let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&bump];let vsigner:&[&[&[u8]];1]=&[vaultseeds];')]
V['tcpi_ctx_accounts'] = [('crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2(CpiContext::new(a.pump_amm.to_account_info(),', 'crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2(CpiContext::new(ctx.accounts.pump_amm.to_account_info(),')]
R745 = ' let reset=sharing_update.is_some();let signer_seeds'
B752 = ' let (old_creator,old_fee)={\n  let curve=&mut ctx.accounts.bonding_curve;let old_creator=curve.creator;'
F755 = 'curve.is_cashback_coin=cashback;let old_fee=curve.creator_fee_bps;'
E759 = ' (old_creator,old_fee)};'
V['oc_decl'] = [(R745, ' let old_creator;let old_fee;let reset=sharing_update.is_some();let signer_seeds'),
                (B752, ' {\n  let curve=&mut ctx.accounts.bonding_curve;old_creator=curve.creator;'),
                (F755, 'curve.is_cashback_coin=cashback;old_fee=curve.creator_fee_bps;'), (E759, ' };')]
V['oc_decl_only'] = [(R745, ' let old_creator;let reset=sharing_update.is_some();let signer_seeds'),
                (B752, ' let old_fee={\n  let curve=&mut ctx.accounts.bonding_curve;old_creator=curve.creator;'),
                (E759, ' old_fee};')]
V['oc_noinner'] = [(B752, ' let (old_creator,old_fee)={\n  let curve=&mut ctx.accounts.bonding_curve;let oc=curve.creator;'), (E759, ' (oc,old_fee)};')]
V['oc_decl_top'] = [(' let swept;', ' let swept;let old_creator;let old_fee;'),
                (B752, ' {\n  let curve=&mut ctx.accounts.bonding_curve;old_creator=curve.creator;'),
                (F755, 'curve.is_cashback_coin=cashback;old_fee=curve.creator_fee_bps;'), (E759, ' };')]
V['val_ifreset'] = [(' match sharing_update{Some(val)=>{', ' if let Some(val)=sharing_update{'), (' }None=>{}}', ' }')]
V['val_clone'] = [('signer_seeds),val)?;', 'signer_seeds),val.clone())?;')]
SWH = 'fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{let a=&ctx.accounts;'
V['sw_accts'] = [('(!skip).then(||sweep(&ctx,&holder_key))', '(!skip).then(||sweep(&ctx.accounts,ctx.bumps.creator_vault,&holder_key))'),
                 (SWH, 'fn sweep(a:&AdminCto,cv_bump:u8,holder_key:&Pubkey)->Result<u64>{'),
                 ('let bump=[ctx.bumps.creator_vault];', 'let bump=[cv_bump];')]
V['sw_hkval'] = [('(!skip).then(||sweep(&ctx,&holder_key))', '(!skip).then(||sweep(&ctx,holder_key))'),
                 (SWH, 'fn sweep(ctx:&Context<AdminCto>,holder_key:Pubkey)->Result<u64>{let a=&ctx.accounts;')]
V['sw_bumps'] = [('(!skip).then(||sweep(&ctx,&holder_key))', '(!skip).then(||sweep(&ctx.accounts,&ctx.bumps,&holder_key))'),
                 (SWH, 'fn sweep(a:&AdminCto,bumps:&AdminCtoBumps,holder_key:&Pubkey)->Result<u64>{'),
                 ('let bump=[ctx.bumps.creator_vault];', 'let bump=[bumps.creator_vault];')]
V['sw_dest_arg'] = [('(!skip).then(||sweep(&ctx,&holder_key))', '(!skip).then(||sweep(&ctx,&Pubkey::find_program_address(&[b"creator-vault",holder_key.as_ref()],&crate::ID).0))'),
                 (SWH, 'fn sweep(ctx:&Context<AdminCto>,dest:&Pubkey)->Result<u64>{let a=&ctx.accounts;let dest=*dest;'),
                 ('  let dest=Pubkey::find_program_address(&[b"creator-vault",holder_key.as_ref()],&crate::ID).0;', '  ')]
S662 = '  let bump=[ctx.bumps.creator_vault];let old=a.current_creator.key();'
SH647 = 'fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{let a=&ctx.accounts;let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;'
V['sv_tailfn'] = [(S662, '  sweep_tail(ctx,native)}fn sweep_tail(ctx:&Context<AdminCto>,native:bool)->Result<u64>{let a=&ctx.accounts;let bump=[ctx.bumps.creator_vault];let old=a.current_creator.key();')]
V['sv_headfn'] = [(SH647, 'fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{let a=&ctx.accounts;let native=sweep_head(ctx,holder_key)?;fn sweep_head(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<bool>{let a=&ctx.accounts;let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;'),
                  (S662, '  Ok(native)}let bump=[ctx.bumps.creator_vault];let old=a.current_creator.key();')]
V['sv_tailclosure'] = [(S662, '  (||->Result<u64>{let bump=[ctx.bumps.creator_vault];let old=a.current_creator.key();'),
                       ('   Ok(amount)}\n', '   Ok(amount)}})()\n')]
