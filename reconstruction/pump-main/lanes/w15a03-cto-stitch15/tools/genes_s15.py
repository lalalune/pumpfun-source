# stitch15 genes: stitch14 library + w14a42 le_vy1 closure family (ny/le/cf_*, on top of v7c)
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import genes_s14 as _S
G=_S.G
import genes as _G0
def apply(s,names): return _G0.apply(s,names)
_lv={'G':{}}
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'levy_genes.py')).read(),_lv)
for _n,_e in _lv['G'].items():
    G['lv_'+_n]=_e
# ---- stitch15 new spellings on 90300f9 ----
_EH='is_holder_reward:a.bonding_curve.is_holder_reward,is_cashback'
G['e0u']=[(_EH,'is_holder_reward:holder.unwrap_or(false),is_cashback')]
G['e0h']=[(_EH,'is_holder_reward:_holder,is_cashback')]
G['e0s']=[(_EH,'is_holder_reward:holder==Some(true),is_cashback')]
_PH='let pargs=(target,a.bonding_curve.is_holder_reward,fee);'
G['p0u']=[(_PH,'let pargs=(target,holder.unwrap_or(false),fee);')]
G['p0h']=[(_PH,'let pargs=(target,_holder,fee);')]
G['c0h']=[('curve.is_holder_reward=holder.unwrap_or(false);','curve.is_holder_reward=_holder;')]
# holder_key deferred init moved next to validate (original copies hk.0 into the validate arg slot after the sharing key copy)
_HKI='let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;'
_VC='let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;'
G['hkl1']=[(_HKI,'let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);'),(_VC,'holder_key=hk.0;'+_VC)]
G['hkl2']=[(_HKI,'let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);'),(_VC,'let sk=a.sharing_config.key();holder_key=hk.0;let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;')]
G['hkl3']=[(_HKI,'let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);'),('let st=CtoState{','holder_key=hk.0;let st=CtoState{')]
G['hkl4']=[(_HKI,'let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);'),('let quote_locked=','holder_key=hk.0;let quote_locked=')]
G['hkl5']=[(_HKI,'let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);'),(_VC,'let sk=a.sharing_config.key();let holder_key=hk.0;let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;')]
# new copied to a local at the block head (original loads new's pieces before the mayhem test)
G['nwl1']=[('let hopt=holder;let holder=hopt==Some(true);','let hopt=holder;let new=new;let holder=hopt==Some(true);')]
G['nwl2']=[('let args=&(new,);','let args=&(new,);let new=args.0;')]
G['nwl3']=[('let args=&(new,);','let args=(new,);let args=&args;')]
# ---- sweep-head +8 B spellings (to pair with sh_iflet's -8 B: insmap shows +1 for one slot in sweep head 0x2130-0x2508) ----
_AP='let amm_present=!a.coin_creator_vault_ata.data_is_empty();let amm_frozen=amm_present&&token_frozen(a.coin_creator_vault_ata.as_ref())?;'
G['sw_apif']=[(_AP,'let amm_present=!a.coin_creator_vault_ata.data_is_empty();let amm_frozen=if amm_present{token_frozen(a.coin_creator_vault_ata.as_ref())?}else{false};')]
G['sw_apdl']=[(_AP,'let amm_present=a.coin_creator_vault_ata.data_len()!=0;let amm_frozen=amm_present&&token_frozen(a.coin_creator_vault_ata.as_ref())?;')]
G['sw_apeq']=[(_AP,'let amm_present=a.coin_creator_vault_ata.data_is_empty()==false;let amm_frozen=amm_present&&token_frozen(a.coin_creator_vault_ata.as_ref())?;')]
_AF='if amm_frozen{require!(token_raw_amount(a.coin_creator_vault_ata.as_ref())?==0,PumpError::CtoSharedVaultFrozen);}'
G['sw_afne']=[(_AF,'if amm_frozen{if token_raw_amount(a.coin_creator_vault_ata.as_ref())?!=0{return Err(error!(PumpError::CtoSharedVaultFrozen));}}')]
G['sw_afgt']=[(_AF,'if amm_frozen{require!(token_raw_amount(a.coin_creator_vault_ata.as_ref())?<=0,PumpError::CtoSharedVaultFrozen);}')]
G['sw_aflet']=[(_AF,'if amm_frozen{let amt=token_raw_amount(a.coin_creator_vault_ata.as_ref())?;require!(amt==0,PumpError::CtoSharedVaultFrozen);}')]
_FZ='if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);}else if amount>0{'
G['sw_fzne']=[(_FZ,'if frozen{if amount!=0{return Err(error!(PumpError::CtoSharedVaultFrozen));}}else if amount>0{')]
G['sw_fzle']=[(_FZ,'if frozen{require!(amount<=0,PumpError::CtoSharedVaultFrozen);}else if amount>0{')]
G['sw_fzam']=[(_FZ,'if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);}else if amount!=0{')]
_DS='if a.holder_creator_vault.key()!=dest{return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((a.holder_creator_vault.key(),dest)));}'
G['sw_dsrk']=[(_DS,'require_keys_eq!(a.holder_creator_vault.key(),dest,anchor_lang::error::ErrorCode::ConstraintSeeds);')]
G['sw_dshv']=[(_DS,'let hv=a.holder_creator_vault.key();if hv!=dest{return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((hv,dest)));}')]
G['sw_dsnp']=[(_DS,'if a.holder_creator_vault.key()!=dest{return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((*a.holder_creator_vault.key,dest)));}')]
_NT='let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;'
G['sw_nteq']=[(_NT,'let native=a.quote_mint.key().eq(&anchor_spl::token::spl_token::native_mint::ID);')]
G['sw_ntrv']=[(_NT,'let native=anchor_spl::token::spl_token::native_mint::ID==a.quote_mint.key();')]
