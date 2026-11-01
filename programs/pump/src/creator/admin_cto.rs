use anchor_lang::prelude::*;
use crate::{Global,PumpError,CollectCreatorFeeEvent};
use crate::trade_types::BondingCurve;
use anchor_lang::solana_program::{instruction::{Instruction,AccountMeta},program::invoke_signed};
pub const AMM:Pubkey=anchor_lang::solana_program::pubkey!("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA");
pub const FEES:Pubkey=crate::distribution::FEES;
#[derive(Clone)]pub struct Amm; impl Id for Amm{fn id()->Pubkey{AMM}}
#[inline(always)]fn aic<'a>(x:&AccountInfo<'a>)->AccountInfo<'a>{AccountInfo{key:x.key,lamports:x.lamports.clone(),data:x.data.clone(),owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}}extern "C"{#[link_name="llvm.bpf.passthrough.p0.p0"]fn ptp(seq:u32,v:*const u8)->*const u8;}/*shim: llvm.bpf.passthrough on a pointer: opaque identity the SBF backend deletes before ISel (no instruction)*/extern "C"{#[link_name="llvm.trap"]fn trap()->!;#[link_name="llvm.assume"]fn assume(b:bool);#[link_name="llvm.expect.with.probability.i1"]fn expect_p(b:bool,v:bool,p:f64)->bool;}/*shim: llvm.expect.with.probability, assume and trap for rcw*/struct Wt<const D:u32>;impl<const D:u32> Wt<D>{const P:f64=1.0/(D as f64+1.0);}#[inline(always)]unsafe fn rcw<const D:u32,T>(r:&std::rc::Rc<T>)->std::rc::Rc<T>{let p=(*(r as *const std::rc::Rc<T> as *const core::ptr::NonNull<usize>)).as_ptr();let s=*p;assume(s!=0);let n=s.wrapping_add(1);*p=n;if expect_p(n==0,true,Wt::<D>::P){trap()}core::ptr::read(r)}/*shim: Rc::clone with an explicit 1:D overflow-trap weight*/#[inline(always)]fn aicd<'a,const D:u32>(x:&AccountInfo<'a>)->AccountInfo<'a>{AccountInfo{key:x.key,lamports:x.lamports.clone(),data:unsafe{rcw::<D,_>(&x.data)},owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}}/*shim: AccountInfo clone, weighted data*/#[inline(always)]fn aicl<'a,const D:u32>(x:&AccountInfo<'a>)->AccountInfo<'a>{AccountInfo{key:x.key,lamports:unsafe{rcw::<D,_>(&x.lamports)},data:x.data.clone(),owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}}/*shim: AccountInfo clone, weighted lamports*/#[inline(always)]fn aicb<'a,const P:u32,const D:u32>(x:&AccountInfo<'a>)->AccountInfo<'a>{AccountInfo{key:x.key,lamports:unsafe{rcw::<P,_>(&x.lamports)},data:unsafe{rcw::<D,_>(&x.data)},owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}}/*shim: AccountInfo clone, both Rc weighted*/
#[derive(Accounts)]
pub struct AdminCto<'info>{
#[account(mut)]
/// CHECK: constrained address or handler validation.
pub admin_set_creator_authority:Signer<'info>,
#[account(has_one=admin_set_creator_authority @ PumpError::NotAuthorized,seeds=[&[103,108,111,98,97,108]],bump)]
/// CHECK: constrained address or handler validation.
pub global:Box<Account<'info,Global>>,
/// CHECK: constrained address or handler validation.
pub mint:UncheckedAccount<'info>,
/// CHECK: constrained address or handler validation.
#[account(mint::token_program=quote_token_program,constraint=quote_mint.key()==bonding_curve.quote_mint||(bonding_curve.quote_mint==Pubkey::default()&&quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID) @ PumpError::MintDoesNotMatchBondingCurve)]
pub quote_mint:Box<InterfaceAccount<'info,anchor_spl::token_interface::Mint>>,
/// CHECK: constrained address or handler validation.
pub quote_token_program:Interface<'info,anchor_spl::token_interface::TokenInterface>,
/// CHECK: constrained address or handler validation.
pub associated_token_program:Program<'info,anchor_spl::associated_token::AssociatedToken>,
/// CHECK: constrained address or handler validation.
pub system_program:Program<'info,System>,
#[account(mut,seeds=[&[98,111,110,100,105,110,103,45,99,117,114,118,101],mint.key().as_ref()],bump)]
/// CHECK: constrained address or handler validation.
pub bonding_curve:Box<Account<'info,BondingCurve>>,
#[account(address=bonding_curve.creator @ PumpError::InvalidCreator)]
/// CHECK: constrained address or handler validation.
pub current_creator:AccountInfo<'info>,
#[account(mut,seeds=[current_creator.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]
/// CHECK: constrained address or handler validation.
pub current_creator_quote_token_account:UncheckedAccount<'info>,
#[account(mut,seeds=[&[99,114,101,97,116,111,114,45,118,97,117,108,116],current_creator.key().as_ref()],bump)]
/// CHECK: constrained address or handler validation.
pub creator_vault:AccountInfo<'info>,
#[account(mut,seeds=[creator_vault.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]
/// CHECK: constrained address or handler validation.
pub creator_vault_quote_token_account:UncheckedAccount<'info>,
#[account(mut)]
/// CHECK: constrained address or handler validation.
pub holder_creator_vault:AccountInfo<'info>,
#[account(mut,seeds=[holder_creator_vault.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]
/// CHECK: constrained address or handler validation.
pub holder_creator_vault_quote_token_account:UncheckedAccount<'info>,
/// CHECK: constrained address or handler validation.
pub pump_amm:Program<'info,crate::pump_amm::program::PumpAmm>,
#[account(seeds=[&[103,108,111,98,97,108,95,99,111,110,102,105,103]],bump,seeds::program=pump_amm.key())]
/// CHECK: constrained address or handler validation.
pub amm_global_config:UncheckedAccount<'info>,
#[account(seeds=[&[112,111,111,108,45,97,117,116,104,111,114,105,116,121],mint.key().as_ref()],bump)]
/// CHECK: constrained address or handler validation.
pub pool_authority:UncheckedAccount<'info>,
#[account(mut,seeds=[&[112,111,111,108],&0u16.to_le_bytes(),pool_authority.key().as_ref(),mint.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=pump_amm.key())]
/// CHECK: constrained address or handler validation.
pub pool:UncheckedAccount<'info>,
#[account(seeds=[&[95,95,101,118,101,110,116,95,97,117,116,104,111,114,105,116,121]],bump,seeds::program=pump_amm.key())]
/// CHECK: constrained address or handler validation.
pub pump_amm_event_authority:UncheckedAccount<'info>,
#[account(mut,seeds=[&[99,114,101,97,116,111,114,95,118,97,117,108,116],current_creator.key().as_ref()],bump,seeds::program=pump_amm.key())]
/// CHECK: constrained address or handler validation.
pub coin_creator_vault_authority:UncheckedAccount<'info>,
#[account(mut,seeds=[coin_creator_vault_authority.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]
/// CHECK: constrained address or handler validation.
pub coin_creator_vault_ata:UncheckedAccount<'info>,
#[account(mut,seeds=[&[115,104,97,114,105,110,103,45,99,111,110,102,105,103],mint.key().as_ref()],bump,seeds::program=pump_fees.key())]
/// CHECK: constrained address or handler validation.
pub sharing_config:UncheckedAccount<'info>,
/// CHECK: constrained address or handler validation.
pub pump_fees:Program<'info,crate::legacy_sell::LegacyFeesProgram>,
#[account(seeds=[&[95,95,101,118,101,110,116,95,97,117,116,104,111,114,105,116,121]],bump,seeds::program=pump_fees.key())]
/// CHECK: constrained address or handler validation.
pub pump_fees_event_authority:UncheckedAccount<'info>,
#[account(seeds=[&[95,95,101,118,101,110,116,95,97,117,116,104,111,114,105,116,121]],bump)]
/// CHECK: constrained address or handler validation.
pub event_authority:AccountInfo<'info>,
/// CHECK: constrained address or handler validation.
pub program:AccountInfo<'info>,
}
#[event]
#[derive(Clone)]
pub struct AdminCtoEvent{
pub timestamp:i64,
pub authority:Pubkey,
pub mint:Pubkey,
pub bonding_curve:Pubkey,
pub old_creator:Pubkey,
pub new_creator:Pubkey,
pub is_holder_reward:bool,
pub is_cashback_coin:bool,
pub old_creator_fee_bps:u64,
pub new_creator_fee_bps:u64,
pub sharing_config_reset:bool,
pub swept_to_holder_vault:u64,
pub pool_updated:bool,
}
struct CtoState{creator:Pubkey,max_fee:u64,mayhem:bool,holder_reward:bool,cashback:bool,quote_locked:bool,holder_enabled:bool,fee_configurable:bool}struct Plan{fee:Option<u64>,target:Pubkey,sharing_update:Option<Option<Pubkey>>,is_holder:bool,cashback:bool,collect_old:bool,skip:bool}
// layout-pad(183): aligns the next Source site with the original line





















































































































































































fn validate(st:&CtoState,shared:bool,holder:bool,fee:Option<u64>,new:Option<Pubkey>,sharing:Pubkey,holder_key:Pubkey,hkr:&Pubkey)->Result<Plan>{
 let mut sharing_update:Option<Option<Pubkey>>=None;if st.mayhem{return Err(error!(PumpError::CtoNotAllowedForMayhemCoin));}
// Reconstructed positions of the same deployed validations.



 unsafe{core::ptr::read_volatile(hkr as *const Pubkey as *const u8)}/*shim: holder_key byte read before the holder_reward test, repays the pin*/;if st.holder_reward{if !holder{return Err(error!(PumpError::HolderRewardCreatorImmutable));}}else if holder{






  if !st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}}

 let cashback=!holder&&st.cashback;let (target,is_holder)=if holder{if !(new==None){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}(holder_key,true)}else{







  let (tg,ih)={let t=new.ok_or_else(||error!(PumpError::CtoNewCreatorRequired))?;
  if t==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((t,Pubkey::default())));}




  require!(t!=holder_key&&t!=sharing,PumpError::InvalidCreator);if shared{(st.creator,false)}else{(t,false)}};(tg,ih)};
// layout-pad(13): aligns the next Source site with the original line












 let fee_bps=match fee{Some(f)=>{if st.quote_locked{return Err(error!(PumpError::CreatorFeeNotConfigurableForQuote));}
// layout-pad(3): aligns the next Source site with the original line


  if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}



  if !st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}



  if f==0||f>st.max_fee{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}Some(f)}None=>None};
 let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);let n7=core::mem::MaybeUninit::<[u8;7]>::uninit();let n9=core::mem::MaybeUninit::<[u8;9]>::uninit();/*shim: the None temp of the original Some(None) (7 B and 9 B pieces, orig -0x450 and -0x2d0)*/unsafe{let p=&mut sharing_update as *mut Option<Option<Pubkey>> as *mut u8;core::ptr::copy_nonoverlapping(ptp(40,n7.as_ptr() as *const u8),p.add(1),7);core::ptr::copy_nonoverlapping(ptp(41,n9.as_ptr() as *const u8),p.add(24),9);}/*shim: original instructions 0x1140-0x1178, the uninit payload copy of Some(None); passthrough keeps MemCpyOpt from dropping the copy*/(false,false)}else{sharing_update=Some(new);(false,true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),true)};Ok(Plan{fee:fee_bps,target,sharing_update,is_holder,cashback,collect_old,skip})}pub fn execute(ctx:Context<AdminCto>,holder:Option<bool>,fee:Option<u64>,new:Option<Pubkey>)->Result<()>{ let a=&ctx.accounts;let mint=a.mint.key();let holder_key=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID).0;let sc:&AccountInfo=a.sharing_config.as_ref();let shared=a.bonding_curve.creator==sc.key()&&sc.owner==&FEES&&!sc.data_is_empty();let plan={let global:&Global=&a.global;let curve:&BondingCurve=&a.bonding_curve;let my0=curve.is_mayhem_mode;let hr0=curve.is_holder_reward;let cb0=curve.is_cashback_coin;let quote_locked={let q=curve.quote_mint;q==Pubkey::default()||q==anchor_spl::token::spl_token::native_mint::ID||global.whitelisted_quote_mints.contains(&q)};let st=CtoState{fee_configurable:global.creator_fee_configurable,creator:curve.creator,max_fee:global.max_configurable_creator_fee_bps,mayhem:my0,holder_reward:hr0,cashback:cb0,quote_locked,holder_enabled:global.is_holder_reward_enabled};let hb=holder.unwrap_or(false);let args=&(new,);validate(&st,shared,hb,fee,args.0,a.sharing_config.key(),holder_key,&holder_key)?};let target=plan.target;let sharing_update=plan.sharing_update;let collect_old=plan.collect_old;let skip=plan.skip;let cashback=plan.cashback; crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.admin_set_creator_authority)?;






































































 require!(a.bonding_curve.creator_fee==0,PumpError::CreatorFeesNotSwept);




// layout-pad(141): aligns the next Source site with the original line












































































































































 if collect_old{wallet(&ctx)?;}fn wallet(ctx:&Context<AdminCto>)->Result<()>{let a=&ctx.accounts;if a.current_creator.executable{msg!("Creator is a program; fees left in the vaults");}else if a.current_creator.owner!=&anchor_lang::system_program::ID{msg!("Creator is not a system-owned wallet; fees left in the vaults");}else{if !a.current_creator.is_writable{return Err(error!(PumpError::CtoCreatorAccountNotWritable));}if token_frozen(a.current_creator_quote_token_account.as_ref())?{msg!("Creator quote token account is frozen; fees left in the vaults");}else{
  let collection_native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;
  let coin_present=!a.coin_creator_vault_ata.data_is_empty();
  let do_collect=collection_native||(!a.creator_vault_quote_token_account.data_is_empty()&&!token_frozen(a.creator_vault_quote_token_account.as_ref())?);
  let do_coin=coin_present&&!token_frozen(a.coin_creator_vault_ata.as_ref())?;
  if !collection_native||coin_present{anchor_spl::associated_token::create_idempotent(CpiContext::new(a.associated_token_program.to_account_info(),anchor_spl::associated_token::Create{payer:a.admin_set_creator_authority.to_account_info(),associated_token:a.current_creator_quote_token_account.to_account_info(),authority:a.current_creator.to_account_info(),mint:a.quote_mint.to_account_info(),system_program:a.system_program.to_account_info(),token_program:a.quote_token_program.to_account_info()}))?;}
  if do_collect{
    let event_signers:[&[&[u8]];1];if let Some((collected,quote_mint))=crate::collect_v2::collect(&a.current_creator,a.current_creator_quote_token_account.as_ref(),&a.creator_vault,ctx.bumps.creator_vault,a.creator_vault_quote_token_account.as_ref(),a.quote_mint.decimals,a.quote_mint.as_ref().as_ref(),&a.quote_token_program,a.system_program.as_ref())?{
     let e=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,creator:a.current_creator.key(),creator_fee:collected,quote_mint};emit!(e);
     {
         let authority_info=ctx.accounts.event_authority.to_account_info();
         let authority_bump=ctx.bumps.event_authority;
         let disc=anchor_lang::event::EVENT_IX_TAG_LE;
         let inner_data=anchor_lang::Event::data(&e);
         let ix_data:Vec<u8>=disc.into_iter().map(|b|*b).chain(inner_data.into_iter()).collect();
         let ix=anchor_lang::solana_program::instruction::Instruction::new_with_bytes(crate::ID,&ix_data,vec![anchor_lang::solana_program::instruction::AccountMeta::new_readonly(*authority_info.key,true)]);
         let event_infos=[authority_info];({let event_inner:&[&[u8]]=&[b"__event_authority",&[authority_bump]];
         event_signers=[event_inner];
         anchor_lang::solana_program::program::invoke_signed(&ix,&event_infos,&event_signers)}).map_err(anchor_lang::error::Error::from)?;
     }
    }
  }
  if do_coin{
  crate::pump_amm::cpi::collect_coin_creator_fee(CpiContext::new(a.pump_amm.to_account_info(),crate::pump_amm::cpi::accounts::CollectCoinCreatorFee{quote_mint:a.quote_mint.to_account_info(),quote_token_program:a.quote_token_program.to_account_info(),coin_creator:a.current_creator.to_account_info(),coin_creator_vault_authority:a.coin_creator_vault_authority.to_account_info(),coin_creator_vault_ata:a.coin_creator_vault_ata.to_account_info(),coin_creator_token_account:a.current_creator_quote_token_account.to_account_info(),event_authority:a.pump_amm_event_authority.to_account_info(),program:a.pump_amm.to_account_info()}))?;}
 }}Ok(())}
 let swept;
// layout-pad(75): aligns the next Source site with the original line
































































 swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{let a=&ctx.accounts;let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;
  let dest=Pubkey::find_program_address(&[b"creator-vault",holder_key.as_ref()],&crate::ID).0;if a.holder_creator_vault.key()!=dest{return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((a.holder_creator_vault.key(),dest)));}
  let amm_present=!a.coin_creator_vault_ata.data_is_empty();let amm_frozen=amm_present&&token_frozen(a.coin_creator_vault_ata.as_ref())?;









  match (amm_present,amm_frozen){(_,false)=>if !a.coin_creator_vault_ata.data_is_empty(){crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2(CpiContext::new(aic(a.pump_amm.as_ref()),crate::pump_amm::cpi::accounts::TransferCreatorFeesToPumpV2{payer:a.admin_set_creator_authority.to_account_info(),quote_mint:a.quote_mint.to_account_info(),token_program:aic(a.quote_token_program.as_ref()),system_program:a.system_program.to_account_info(),associated_token_program:aic(a.associated_token_program.as_ref()),coin_creator:aic(&a.current_creator),coin_creator_vault_authority:a.coin_creator_vault_authority.to_account_info(),coin_creator_vault_ata:aic(a.coin_creator_vault_ata.as_ref()),pump_creator_vault:a.creator_vault.to_account_info(),pump_creator_vault_ata:aic(a.creator_vault_quote_token_account.as_ref()),event_authority:a.pump_amm_event_authority.to_account_info(),program:aic(a.pump_amm.as_ref())}))?;}
  (true,true)=>{require!(token_raw_amount(a.coin_creator_vault_ata.as_ref()).map_err(|e|{let _=unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};/*shim: holder_key byte read placeholder on the error path, repays the pin*/e})?==0,PumpError::CtoSharedVaultFrozen);}(false,true)=>{}}

  let vsigner:[&[&[u8]];1];let bump=ctx.bumps.creator_vault;let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&[bump]];vsigner=[vaultseeds];
  if native{let min={let rent=Rent::get()?;rent.minimum_balance(0)};let amount=a.creator_vault.lamports().saturating_sub(min);
   return if amount>0{crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)?;crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&vsigner).map(|()|amount)}else{Ok(0)};}else{let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;






















































   if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);return Ok(amount);}else if amount>0{anchor_spl::associated_token::create_idempotent(CpiContext::new(a.associated_token_program.to_account_info(),anchor_spl::associated_token::Create{payer:a.admin_set_creator_authority.to_account_info(),associated_token:a.holder_creator_vault_quote_token_account.to_account_info(),authority:a.holder_creator_vault.to_account_info(),mint:a.quote_mint.to_account_info(),system_program:a.system_program.to_account_info(),token_program:a.quote_token_program.to_account_info()}))?;crate::collect_v2::transfer_vault_tokens(&a.quote_token_program,&a.creator_vault_quote_token_account,&a.holder_creator_vault_quote_token_account,&a.creator_vault,a.quote_mint.decimals,a.quote_mint.as_ref().as_ref(),amount,&vsigner)?;}else{return Ok(amount);}
   Ok(amount)}





 }


















 let signer_seeds:&[&[&[u8]]]=&[&[b"pool-authority",mint.as_ref(),&[ctx.bumps.pool_authority]]];
 if let Some(val)=sharing_update{{


  crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer(a.pump_fees.to_account_info(),crate::pump_fees::cpi::accounts::AdminCtoSharingConfig{pool_authority:aicl::<5>(a.pool_authority.as_ref()),authority:aic(a.admin_set_creator_authority.as_ref()),global:aic(a.global.as_ref().as_ref()),mint:aicd::<200>(a.mint.as_ref()),sharing_config:aic(a.sharing_config.as_ref()),event_authority:aic(a.pump_fees_event_authority.as_ref()),program:aic(a.pump_fees.as_ref())},signer_seeds),val)?;

 }}
 let (old_creator,old_fee)={
  let curve=&mut ctx.accounts.bonding_curve;let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;
  curve.creator=target;
  curve.is_holder_reward=plan.is_holder;
  curve.is_cashback_coin=cashback;
  if let Some(f)=plan.fee{curve.creator_fee_bps=f;}
  curve.can_edit_creator_fee=false;
 (old_creator,old_fee)};
 let a=&ctx.accounts;
 let pool_updated=a.pool.owner==&AMM&&!a.pool.data_is_empty();let pargs=(target,plan.is_holder,plan.fee);
 if pool_updated{


  crate::pump_amm::cpi::admin_cto_pool(CpiContext::new_with_signer(a.pump_amm.to_account_info(),crate::pump_amm::cpi::accounts::AdminCtoPool{payer:a.admin_set_creator_authority.to_account_info(),global_config:a.amm_global_config.to_account_info(),pool:a.pool.to_account_info(),pool_authority:a.pool_authority.to_account_info(),system_program:a.system_program.to_account_info(),event_authority:a.pump_amm_event_authority.to_account_info(),program:a.pump_amm.to_account_info()},signer_seeds),pargs.0,pargs.1,pargs.2)?;
 }else{msg!("No canonical pump pool for this mint; curve only");}
 let e=AdminCtoEvent{timestamp:Clock::get()?.unix_timestamp,authority:a.admin_set_creator_authority.key(),mint,bonding_curve:a.bonding_curve.key(),old_creator,new_creator:a.bonding_curve.creator,is_holder_reward:a.bonding_curve.is_holder_reward,is_cashback_coin:a.bonding_curve.is_cashback_coin,old_creator_fee_bps:old_fee,new_creator_fee_bps:a.bonding_curve.creator_fee_bps,sharing_config_reset:sharing_update.is_some(),swept_to_holder_vault:swept,pool_updated};emit!(e);emit_cpi!(e);Ok(())
}

fn token_frozen(a:&AccountInfo)->Result<bool>{if a.data_is_empty(){return Ok(false);}let d=a.try_borrow_data()?;let t=anchor_spl::token_interface::TokenAccount::try_deserialize(&mut &d[..])?;Ok(t.is_frozen())}

fn token_raw_amount(a:&AccountInfo)->Result<u64>{if a.data_is_empty(){return Ok(0);}let d=a.try_borrow_data()?;let t=anchor_spl::token_interface::TokenAccount::try_deserialize(&mut &d[..])?;Ok(t.amount)}
