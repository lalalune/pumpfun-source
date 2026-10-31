# w16a02 faithknobs gene library. Each gene: list of (old,new) exact replacements; each old must occur exactly once
# (or (old,new,count) to require count occurrences, all replaced). Line count must be kept by the caller's check.
G={}
def apply(s,names):
    for n in names:
        for e in G[n]:
            if callable(e): s=e(s); continue
            if len(e)==3: a,b,k=e
            else: (a,b),k=e,1
            c=s.count(a)
            if c!=k: raise Exception(f'gene {n}: {c} occurrences (want {k}) of {a[:120]!r}')
            s=s.replace(a,b)
    return s
# sh_iflet (w15a03 #3732) == mil (w15a23): if-let on the sharing update -> post-CPI `jne r7,2,err` as orig 0x4aa0 (-8 B)
G['sh_iflet']=[(" match sharing_update{Some(val)=>{\n"," if let Some(val)=sharing_update{{\n"),("signer_seeds),val)?;\n\n }None=>{}}\n","signer_seeds),val)?;\n\n }}\n")]
# ---------------- sweep-head spellings (lines 647-664, 719): candidates for one surviving +8 B instruction ----------------
_NT='let a=&ctx.accounts;let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;'
G['h_ader']=[(_NT,'let a=&*ctx.accounts;let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;')]
G['h_ntid']=[(_NT,'let a=&ctx.accounts;let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::id();')]
G['h_ntck']=[(_NT,'let a=&ctx.accounts;let native=anchor_spl::token::spl_token::native_mint::check_id(&a.quote_mint.key());')]
G['h_ntref']=[(_NT,'let a=&ctx.accounts;let native=&a.quote_mint.key()==&anchor_spl::token::spl_token::native_mint::ID;')]
_DS='let dest=Pubkey::find_program_address(&[b"creator-vault",holder_key.as_ref()],&crate::ID).0;if a.holder_creator_vault.key()!=dest{return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((a.holder_creator_vault.key(),dest)));}'
G['d_tup']=[(_DS,'let (dest,_)=Pubkey::find_program_address(&[b"creator-vault",holder_key.as_ref()],&crate::ID);if a.holder_creator_vault.key()!=dest{return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((a.holder_creator_vault.key(),dest)));}')]
G['d_full']=[(_DS,'let dest=Pubkey::find_program_address(&[b"creator-vault",holder_key.as_ref()],&crate::ID);if a.holder_creator_vault.key()!=dest.0{return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((a.holder_creator_vault.key(),dest.0)));}')]
G['d_rev']=[(_DS,'let dest=Pubkey::find_program_address(&[b"creator-vault",holder_key.as_ref()],&crate::ID).0;if dest!=a.holder_creator_vault.key(){return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((a.holder_creator_vault.key(),dest)));}')]
G['d_not']=[(_DS,'let dest=Pubkey::find_program_address(&[b"creator-vault",holder_key.as_ref()],&crate::ID).0;if !(a.holder_creator_vault.key()==dest){return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((a.holder_creator_vault.key(),dest)));}')]
G['d_refcmp']=[(_DS,'let dest=Pubkey::find_program_address(&[b"creator-vault",holder_key.as_ref()],&crate::ID).0;if a.holder_creator_vault.key!=&dest{return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((a.holder_creator_vault.key(),dest)));}')]
G['d_seedas']=[(_DS,'let dest=Pubkey::find_program_address(&[b"creator-vault".as_ref(),holder_key.as_ref()],&crate::ID).0;if a.holder_creator_vault.key()!=dest{return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((a.holder_creator_vault.key(),dest)));}')]
G['d_progid']=[(_DS,'let dest=Pubkey::find_program_address(&[b"creator-vault",holder_key.as_ref()],&crate::id()).0;if a.holder_creator_vault.key()!=dest{return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((a.holder_creator_vault.key(),dest)));}')]
G['d_ctxpid']=[(_DS,'let dest=Pubkey::find_program_address(&[b"creator-vault",holder_key.as_ref()],ctx.program_id).0;if a.holder_creator_vault.key()!=dest{return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((a.holder_creator_vault.key(),dest)));}')]
G['d_ctxkey']=[(_DS,'let dest=Pubkey::find_program_address(&[b"creator-vault",holder_key.as_ref()],&crate::ID).0;if a.holder_creator_vault.key()!=dest{return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((ctx.accounts.holder_creator_vault.key(),dest)));}')]
G['d_errinto']=[(_DS,'let dest=Pubkey::find_program_address(&[b"creator-vault",holder_key.as_ref()],&crate::ID).0;if a.holder_creator_vault.key()!=dest{return Err(anchor_lang::error::Error::from(error!(anchor_lang::error::ErrorCode::ConstraintSeeds)).with_pubkeys((a.holder_creator_vault.key(),dest)));}')]
G['d_infokey']=[(_DS,'let dest=Pubkey::find_program_address(&[b"creator-vault",holder_key.as_ref()],&crate::ID).0;if a.holder_creator_vault.key()!=dest{return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((*a.holder_creator_vault.as_ref().key,dest)));}')]
_AP='let amm_present=!a.coin_creator_vault_ata.data_is_empty();let amm_frozen=amm_present&&token_frozen(a.coin_creator_vault_ata.as_ref())?;'
G['ap_reuse']=[('else if !a.coin_creator_vault_ata.data_is_empty(){crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2(','else if amm_present{crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2(')]
G['ap_info']=[(_AP,'let amm_present=!a.coin_creator_vault_ata.data_is_empty();let amm_frozen=amm_present&&token_frozen(&a.coin_creator_vault_ata)?;')]
_VS='let vsigner:[&[&[u8]];1];let bump=ctx.bumps.creator_vault;let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&[bump]];vsigner=[vaultseeds];'
G['v_bumplate']=[(_VS,'let vsigner:[&[&[u8]];1];let old=a.current_creator.key();let bump=ctx.bumps.creator_vault;let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&[bump]];vsigner=[vaultseeds];')]
G['v_bumpinl']=[(_VS,'let vsigner:[&[&[u8]];1];let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&[ctx.bumps.creator_vault]];vsigner=[vaultseeds];')]
G['v_bumparr']=[(_VS,'let vsigner:[&[&[u8]];1];let bump=[ctx.bumps.creator_vault];let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&bump];vsigner=[vaultseeds];')]
G['v_direct']=[(_VS,'let bump=ctx.bumps.creator_vault;let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&[bump]];let vsigner:[&[&[u8]];1]=[vaultseeds];')]
_FA='let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;'
G['a1']=[(_FA,'let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;')]
# ---------------- sibling-idiom size-knob catalog (k_*): ordinary forms from byte-matched siblings ----------------
# entry (create_v2 `.0` projection, admin_cto_pool `let (x,_)=`, crate::id())
_HK='let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;'
G['k_hkproj']=[(_HK,'let holder_key=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID).0;')]
G['k_hktup']=[(_HK,'let (holder_key,_)=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);')]
G['k_hkpid']=[(_HK,'let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::id());holder_key=hk.0;')]
G['k_dpid']=G['d_progid']
# validate (create_v2 / admin_cto_pool require! forms and `if flag{require!(..)}` nesting)
G['k_req284']=[('if st.mayhem{return Err(error!(PumpError::CtoNotAllowedForMayhemCoin));}','require!(!st.mayhem,PumpError::CtoNotAllowedForMayhemCoin);')]
G['k_req289']=[('if st.holder_reward&&!(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}','if st.holder_reward{require!(hopt==Some(true),PumpError::HolderRewardCreatorImmutable);}')]
G['k_req296']=[('if holder&&!st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}','if holder&&!st.holder_reward{require!(st.holder_enabled,PumpError::HolderRewardDisabled);}')]
G['k_req298']=[('if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}','require!(new.is_none(),PumpError::CtoNewCreatorNotAllowed);')]
G['k_rkn307']=[('if t==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((t,Pubkey::default())));}','require_keys_neq!(t,Pubkey::default(),PumpError::CreatorShouldNotBeZero);')]
G['k_req312']=[('if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}','require!(t!=*sharing&&t!=*holder_key,PumpError::InvalidCreator);')]
G['k_req326']=[('if st.quote_locked{return Err(error!(PumpError::CreatorFeeNotConfigurableForQuote));}','require!(!st.quote_locked,PumpError::CreatorFeeNotConfigurableForQuote);')]
G['k_req330']=[('if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}','require!(!cashback,PumpError::CreatorFeeNotAllowedForCashbackCoin);')]
G['k_req334']=[('if !st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}','require!(st.fee_configurable,PumpError::CreatorFeeNotConfigurable);')]
G['k_req338']=[('if f==0||f>st.max_fee{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}','require!(f>0&&f<=st.max_fee,PumpError::CreatorFeeBpsOutOfRange);')]
G['k_iflet326']=[('match fee{Some(f)=>{if st.quote_locked{','if let Some(f)=fee{{if st.quote_locked{'),('unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};}None=>{}}','unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};}}')]
G['k_okor306']=[('let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};','let t=new.ok_or_else(||error!(PumpError::CtoNewCreatorRequired))?;')]
# tree (admin_cto_pool is_cashback_coin form)
G['k_cbif']=[('let cashback=!holder&&st.cashback;','let cashback=if holder{false}else{st.cashback};')]
# sweep (sweep_fees: Rent direct)
G['k_rentdirect']=[('let min={let rent=Rent::get()?;rent.minimum_balance(0)};','let min=Rent::get()?.minimum_balance(0);')]
# curve block (admin_cto_pool: old fee read after the creator/holder/cashback stores; sweep_fees `&mut *ctx.accounts`)
G['k_oldfee_after']=[('let curve=&mut ctx.accounts.bonding_curve;let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;','let curve=&mut ctx.accounts.bonding_curve;let old_creator=curve.creator;'),('curve.is_cashback_coin=cashback;','curve.is_cashback_coin=cashback;let old_fee=curve.creator_fee_bps;')]
G['k_amutstar']=[('let curve=&mut ctx.accounts.bonding_curve;let old_creator=','let a=&mut *ctx.accounts;let curve=&mut a.bonding_curve;let old_creator=')]
# wallet (collect_creator_fee early-return msg! forms)
G['k_wl_early']=[('if a.current_creator.executable{msg!("Creator is a program; fees left in the vaults");}else if a.current_creator.owner!=&anchor_lang::system_program::ID{msg!("Creator is not a system-owned wallet; fees left in the vaults");}else{','if a.current_creator.executable{msg!("Creator is a program; fees left in the vaults");return Ok(());}if a.current_creator.owner!=&anchor_lang::system_program::ID{msg!("Creator is not a system-owned wallet; fees left in the vaults");return Ok(());}{')]
G['k_wl_early2']=[('if token_frozen(a.current_creator_quote_token_account.as_ref())?{msg!("Creator quote token account is frozen; fees left in the vaults");}else{','if token_frozen(a.current_creator_quote_token_account.as_ref())?{msg!("Creator quote token account is frozen; fees left in the vaults");return Ok(());}{')]
# helper boundaries (collect_creator_fee #[inline] fn wrappers): MIR-inlines the helper before codegen
G['k_inl_wallet']=[('fn wallet(ctx:&Context<AdminCto>)->Result<()>{','#[inline]fn wallet(ctx:&Context<AdminCto>)->Result<()>{')]
G['k_inl_sweep']=[('fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{','#[inline]fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{')]
G['k_inl_validate']=[('fn validate(st:&CtoState,','#[inline]fn validate(st:&CtoState,')]
# ---------------- bounded leads (for pairing) ----------------
_HN="if shared{if holder{sharing_update=Some(None);(false,false)}else{"
G['t1n']=[(_HN,"if shared{if new.is_none(){sharing_update=Some(None);(false,false)}else{")]           # w14a76/w15a03: -24 B, M-1
G['g11']=[('let sk=a.sharing_config.key();let mut target=validate(','let sk=a.sharing_config.key();let creator=&st.creator;let mut target=validate('),('sharing_update=Some(args.0);target=a.bonding_curve.creator;','sharing_update=Some(args.0);target=*creator;')]  # w15a13: -8 B, -3 M
G['g13']=[('if shared{if holder{','if shared{let creator=st.creator;if holder{'),('sharing_update=Some(args.0);target=a.bonding_curve.creator;','sharing_update=Some(args.0);target=creator;')]  # w15a13: -8 B, -3 M
_SHN='let shared={let sk=a.sharing_config.key();a.bonding_curve.creator==sk}&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();'
G['crl3']=[(_SHN,'let shared={let cr=a.bonding_curve.creator;cr==a.sharing_config.key()}&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();')]  # w15a03: +72 B, +1
# t1 (w14a70 #3402): a1 + separate `?` on create_idempotent and transfer_vault_tokens (the original's create/transfer Err tests)
G['tsplit']=[(')).and_then(|()|crate::collect_v2::transfer_vault_tokens(','))?;crate::collect_v2::transfer_vault_tokens('),('amount,&vsigner))?;return Ok(amount);}','amount,&vsigner)?;return Ok(amount);}')]
