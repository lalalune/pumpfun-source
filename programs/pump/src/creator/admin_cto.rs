use anchor_lang::prelude::*;
use crate::{Global,PumpError,CollectCreatorFeeEvent};
use crate::trade_types::BondingCurve;
use anchor_lang::solana_program::{instruction::{Instruction,AccountMeta},program::invoke_signed};
pub const AMM:Pubkey=anchor_lang::solana_program::pubkey!("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA");
pub const FEES:Pubkey=crate::distribution::FEES;
#[derive(Clone)]pub struct Amm; impl Id for Amm{fn id()->Pubkey{AMM}}
extern "C"{#[link_name="llvm.expect.i1"]fn expect(b:bool,v:bool)->bool;#[link_name="llvm.assume"]fn assume(b:bool);#[link_name="llvm.trap"]fn trap()->!;}/*shim: llvm.expect/assume/trap for rcinc*/#[inline(always)]unsafe fn rcinc<T>(r:&std::rc::Rc<T>)->std::rc::Rc<T>{let p=(*(r as *const std::rc::Rc<T> as *const core::ptr::NonNull<usize>)).as_ptr();let s=*p;assume(s!=0);let n=s.wrapping_add(1);*p=n;if expect(n==0,false){trap()}core::ptr::read(r)}/*shim: Rc::clone with a 1:2000 overflow-trap weight, steers spill-slot colouring*/extern "C"{#[link_name="llvm.expect.with.probability.i1"]fn expect_p(b:bool,v:bool,p:f64)->bool;}/*shim: llvm.expect.with.probability = any branch ratio (core::intrinsics::unlikely emits no weight on rustc 1.79-dev)*/#[inline(always)]unsafe fn rcincp<T>(r:&std::rc::Rc<T>)->std::rc::Rc<T>{let p=(*(r as *const std::rc::Rc<T> as *const core::ptr::NonNull<usize>)).as_ptr();let s=*p;assume(s!=0);let n=s.wrapping_add(1);*p=n;if expect_p(n==0,true,0.00002){trap()}core::ptr::read(r)}/*shim: Rc::clone with a p=0.00002 overflow-trap weight, steers spill-slot colouring*/#[inline(always)]unsafe fn rcincr<T>(r:&std::rc::Rc<T>)->std::rc::Rc<T>{let p=(*(r as *const std::rc::Rc<T> as *const core::ptr::NonNull<usize>)).as_ptr();let s=*p;assume(s!=0);let n=s.wrapping_add(1);*p=n;if expect_p(n==0,true,0.00001){trap()}core::ptr::read(r)}/*shim: Rc::clone with a p=0.00001 overflow-trap weight*/#[inline(always)]unsafe fn aiclone_r<'a>(x:&AccountInfo<'a>)->AccountInfo<'a>{AccountInfo{key:x.key,lamports:rcincr(&x.lamports),data:x.data.clone(),owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}}/*shim: derived AccountInfo::clone with a weighted lamports clone*/extern "C"{#[link_name="llvm.bpf.passthrough.i64.i64"]fn pt64(seq:u32,v:u64)->u64;#[link_name="llvm.bpf.passthrough.i1.i1"]fn pt1(seq:u32,v:bool)->bool;#[link_name="llvm.bpf.passthrough.i8.i8"]fn pt8(seq:u32,v:u8)->u8;#[link_name="llvm.bpf.passthrough.p0.p0"]fn ptp(seq:u32,v:*const u8)->*const u8;}/*shim: llvm.bpf.passthrough = an opaque identity the SBF backend deletes before ISel (no instruction); blocks IR folds through the value*/extern "C"{#[link_name="llvm.lifetime.start.p0"]fn lts(n:i64,p:*mut u8);#[link_name="llvm.lifetime.end.p0"]fn lte(n:i64,p:*mut u8);}/*shim: llvm.lifetime.start/end = explicit StackColoring live-range markers (no instruction)*/extern "C"{#[link_name="llvm.var.annotation.p0.p0"]fn vann(p:*const u8,s:*const u8,f:*const u8,l:u32,a:*const u8);}/*shim: llvm.var.annotation = a zero-instruction pin that keeps an alloca through SROA (dropped at ISel)*/
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
struct CtoState{creator:Pubkey,max_fee:u64,mayhem:bool,holder_reward:bool,holder_enabled:bool,fee_configurable:bool,cashback:bool,quote_locked:bool}
// layout-pad(183): aligns the next Source site with the original line





















































































































































































fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);
 if st.mayhem{return Err(error!(PumpError::CtoNotAllowedForMayhemCoin));}
// Reconstructed positions of the same deployed validations.



 let mut target=core::mem::MaybeUninit::<Pubkey>::uninit();/*shim: validate target held in a MaybeUninit so lts/lte can bracket its non-holder arm*/if match st.holder_reward as u8{1=>{if !(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}true}_=>if unsafe{expect_p(holder,true,0.49)}/*shim: !hr holder test 49:51 (MBP places the 306 test after the !hr holder test)*/{






  if !st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}true}else{false}}

 {if unsafe{pt1(3,new.is_some())}/*shim: passthrough on the holder-arm new.is_some() test (no fold of the tag test)*/{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}target.write(*holder_key);}else{unsafe{lte(32,target.as_mut_ptr() as *mut u8)}/*shim: lifetime end of validate target at the non-holder arm head (its pieces stay free through the 306/307/312 checks)*/;







  let t=if unsafe{expect_p(new.is_none(),true,0.75)}/*shim: 306 None probability*/{return Err(error!(PumpError::CtoNewCreatorRequired));}else{unsafe{core::ptr::read_unaligned((&new as *const Option<Pubkey> as *const u8).add(1) as *const Pubkey)}/*shim: 306 payload read, no tag re-test*/};
  if t==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((t,Pubkey::default())));}




  if unsafe{expect_p((pt8(4,(t==*sharing) as u8)&1)!=0,true,0.625)}/*shim: 312 t==sharing memcmp equal-likely 20:12 (llc spill colour; was the libcall 12:20); passthrough on the compare byte*/||unsafe{expect(t==*holder_key,false)}/*shim: 312 holder_key compare unlikely 1:2000 (llc placement)*/{return Err(error!(PumpError::InvalidCreator));}unsafe{lts(32,target.as_mut_ptr() as *mut u8)}/*shim: lifetime start of validate target right before the checked t is stored*/;target.write(t);}
// layout-pad(13): aligns the next Source site with the original line
 let cashback=if holder{false}else{st.cashback};











 match fee{Some(f)=>{if st.quote_locked{return Err(error!(PumpError::CreatorFeeNotConfigurableForQuote));}
// layout-pad(3): aligns the next Source site with the original line


  if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}



  unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder before the fee_configurable test*/;if !st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}



  if f==0||f>st.max_fee{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};}None=>{}}
 Ok(unsafe{target.assume_init()})/*shim: validate target held in a MaybeUninit for the lifetime markers*/}pub fn execute(ctx:Context<AdminCto>,holder:Option<bool>,fee:Option<u64>,new:Option<Pubkey>)->Result<()>{ let a=&ctx.accounts;let mint=a.mint.key();let shared={let cr=a.bonding_curve.creator;cr==a.sharing_config.key()}&&unsafe{&*(ptp(23,&**a as *const AdminCto as *const u8) as *const AdminCto)}/*shim: passthrough on the accounts pointer of the shared owner test*/.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();let mut hkx=core::mem::MaybeUninit::<[u64;9]>::uninit();/*shim: holder_key in a 72 B slot whose 40 B tail keeps hk's frame region (orig -0x680..-0x658 target/new pieces)*/let holder_key:&Pubkey=unsafe{hkx.as_mut_ptr().cast::<Pubkey>().write(Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID).0);&*hkx.as_ptr().cast::<Pubkey>()}/*shim: PDA result is a temp (orig -0x2d0 out-param)*/;let quote_locked={let q=a.bonding_curve.quote_mint;q==Pubkey::default()||q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(&q)};let (_holder,cashback,target,sharing_update,collect_old,skip)={ let mut skm=core::mem::MaybeUninit::<Pubkey>::uninit();let mut hk2=core::mem::MaybeUninit::<[u64;4]>::uninit();/*shim: frame stand-in for the original hk2 copy (32 B slot live across validate: FI47 -0x518)*/let creator=a.bonding_curve.creator;let st=CtoState{fee_configurable:a.global.creator_fee_configurable,creator:{unsafe{lts(32,skm.as_mut_ptr() as *mut u8)}/*shim: lifetime start of the sk slot between the fee_configurable load and the creator copy (creator stores ascending)*/;a.bonding_curve.creator},max_fee:unsafe{&*(ptp(24,&**a as *const AdminCto as *const u8) as *const AdminCto)}/*shim: passthrough on the accounts pointer of max_fee*/.global.max_configurable_creator_fee_bps,mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin,quote_locked,holder_enabled:a.global.is_holder_reward_enabled};let hopt=holder;let holder=hopt==Some(true);let cashback=!holder&&st.cashback;let args=&(new,);let sk:&Pubkey=unsafe{skm.as_mut_ptr().write(core::ptr::read_volatile(&a.sharing_config)/*shim: volatile reload of the sharing_config account ref for the sk copy*/.key());&*skm.as_ptr()};let mut target=validate(&st,hopt,fee,new,holder_key,sk)?;let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if unsafe{expect_p(shared,true,0.625)}/*shim: shared split weight (llc block placement)*/{if holder{sharing_update=Some(None);(false,false)}else{target=creator;sharing_update=Some(args.0);(false,true)}}else{(!st.holder_reward&&{let mut c=false;unsafe{core::ptr::write_volatile(&mut c,st.creator==Pubkey::default())};/*shim: creator==default compare kept in memory*/!c},true)};unsafe{vann(hk2.as_mut_ptr() as *const u8,b"\0".as_ptr(),b"\0".as_ptr(),0,core::ptr::null())}/*shim: var.annotation keeps the hk2 stand-in through SROA (no instruction)*/;(holder,cashback,target,sharing_update,collect_old,skip)};let (target,sharing_update,cashback)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback))?;let mut target=target; crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.admin_set_creator_authority)?;






































































 require!(a.bonding_curve.creator_fee==0,PumpError::CreatorFeesNotSwept);




// layout-pad(141): aligns the next Source site with the original line












































































































































 if collect_old{wallet(&ctx)?;}fn wallet(ctx:&Context<AdminCto>)->Result<()>{let a=&ctx.accounts;if a.current_creator.executable{msg!("Creator is a program; fees left in the vaults");}else if {let mut c=false;unsafe{core::ptr::write_volatile(&mut c,a.current_creator.owner==&anchor_lang::system_program::ID)};/*shim: current_creator owner compare kept in memory*/!c}{msg!("Creator is not a system-owned wallet; fees left in the vaults");}else{if !a.current_creator.is_writable{return Err(error!(PumpError::CtoCreatorAccountNotWritable));}if token_frozen(a.current_creator_quote_token_account.as_ref())?{msg!("Creator quote token account is frozen; fees left in the vaults");}else{
  let collection_native={let mut c=false;unsafe{core::ptr::write_volatile(&mut c,a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID)};/*shim: wallet quote==native compare kept in memory*/c};
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
  if coin_present&unsafe{pt1(27,(pt8(6,*(&do_coin as *const bool as *const u8))&1)!=0)}/*shim: passthrough on the do_coin byte and on its test at the AMM collect test*/{
  crate::pump_amm::cpi::collect_coin_creator_fee(CpiContext::new(a.pump_amm.to_account_info(),crate::pump_amm::cpi::accounts::CollectCoinCreatorFee{quote_mint:a.quote_mint.to_account_info(),quote_token_program:a.quote_token_program.to_account_info(),coin_creator:a.current_creator.to_account_info(),coin_creator_vault_authority:a.coin_creator_vault_authority.to_account_info(),coin_creator_vault_ata:a.coin_creator_vault_ata.to_account_info(),coin_creator_token_account:a.current_creator_quote_token_account.to_account_info(),event_authority:a.pump_amm_event_authority.to_account_info(),program:a.pump_amm.to_account_info()}))?;}
 }}Ok(())}
 let swept;
// layout-pad(75): aligns the next Source site with the original line
































































 swept=(!skip).then(||sweep(&ctx,holder_key)).transpose()?.unwrap_or(0);fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{let a=&ctx.accounts;let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;
  let dest=Pubkey::find_program_address(&[b"creator-vault",holder_key.as_ref()],&crate::ID).0;if {let mut c=false;unsafe{core::ptr::write_volatile(&mut c,a.holder_creator_vault.key()==dest)};/*shim: holder-vault key compare kept in memory*/!c}{return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((a.holder_creator_vault.key(),dest)));}
  let amm_present=!a.coin_creator_vault_ata.data_is_empty();let amm_frozen=amm_present&&token_frozen(a.coin_creator_vault_ata.as_ref())?;









  match (amm_present,amm_frozen){(_,false)=>if !a.coin_creator_vault_ata.data_is_empty(){crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2(CpiContext::new({let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{owner:unsafe{core::ptr::read_volatile(&x.owner)}/*shim: pins the sweep program-clone owner load*/,key:x.key,lamports:x.lamports.clone(),data:x.data.clone(),rent_epoch:x.rent_epoch,executable:unsafe{pt1(7,x.executable)}/*shim: passthrough on the TCF program-clone executable byte*/,is_writable:x.is_writable,is_signer:x.is_signer}},crate::pump_amm::cpi::accounts::TransferCreatorFeesToPumpV2{payer:a.admin_set_creator_authority.to_account_info(),quote_mint:a.quote_mint.to_account_info(),token_program:{let x:&AccountInfo=a.quote_token_program.as_ref();AccountInfo{key:x.key,lamports:unsafe{rcinc(&x.lamports)}/*shim: weighted Rc clone (bu:1964)*/,data:x.data.clone(),owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}},system_program:a.system_program.to_account_info(),associated_token_program:{let x:&AccountInfo=a.associated_token_program.as_ref();AccountInfo{key:x.key,lamports:unsafe{rcincp(&x.lamports)}/*shim: weighted Rc clone (2051)*/,data:x.data.clone(),owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}},coin_creator:unsafe{aiclone_r(&a.current_creator)}/*shim: weighted clone (2194)*/,coin_creator_vault_authority:a.coin_creator_vault_authority.to_account_info(),coin_creator_vault_ata:{let x:&AccountInfo=a.coin_creator_vault_ata.as_ref();AccountInfo{lamports:x.lamports.clone(),key:x.key,data:x.data.clone(),owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}},pump_creator_vault:a.creator_vault.to_account_info(),pump_creator_vault_ata:{let x:&AccountInfo=a.creator_vault_quote_token_account.as_ref();AccountInfo{key:x.key,data:a.creator_vault_quote_token_account.data.clone(),owner:a.creator_vault_quote_token_account.owner,lamports:x.lamports.clone(),rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}},event_authority:a.pump_amm_event_authority.to_account_info(),program:{let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{key:x.key,owner:x.owner,lamports:x.lamports.clone(),data:x.data.clone(),rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}}}))?;}
  (true,true)=>{require!(token_raw_amount(a.coin_creator_vault_ata.as_ref())?==0,PumpError::CtoSharedVaultFrozen);}(false,true)=>{}}

  let vsigner:[&[&[u8]];1];let bump=ctx.bumps.creator_vault;let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&[bump]];vsigner=[vaultseeds];
  if native{let min={let rent=Rent::get()?;rent.minimum_balance(0)};let amount=a.creator_vault.lamports().saturating_sub(min);
   (if amount>0{crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)?;crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&vsigner)}else{Ok(())}).map(|()|amount)}else{let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;






















































   if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);}else if amount>0{anchor_spl::associated_token::create_idempotent(CpiContext::new(a.associated_token_program.to_account_info(),anchor_spl::associated_token::Create{payer:a.admin_set_creator_authority.to_account_info(),associated_token:a.holder_creator_vault_quote_token_account.to_account_info(),authority:a.holder_creator_vault.to_account_info(),mint:a.quote_mint.to_account_info(),system_program:a.system_program.to_account_info(),token_program:a.quote_token_program.to_account_info()})).and_then(|()|crate::collect_v2::transfer_vault_tokens(&a.quote_token_program,&a.creator_vault_quote_token_account,&a.holder_creator_vault_quote_token_account,&a.creator_vault,a.quote_mint.decimals,a.quote_mint.as_ref().as_ref(),amount,&vsigner))?;return Ok(amount);}
   Ok(amount)}





 }


















 let signer_seeds:&[&[&[u8]]]=&[&[b"pool-authority",mint.as_ref(),&[ctx.bumps.pool_authority]]];
 if let Some(val)=sharing_update{{


  let pf:&AccountInfo;let ead;const _: [();core::mem::size_of::<Program<'static,crate::legacy_sell::LegacyFeesProgram>>()]=[();core::mem::size_of::<&'static AccountInfo<'static>>()];const _: [();core::mem::align_of::<Program<'static,crate::legacy_sell::LegacyFeesProgram>>()]=[();core::mem::align_of::<&'static AccountInfo<'static>>()];crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer(a.pump_fees.to_account_info(),crate::pump_fees::cpi::accounts::AdminCtoSharingConfig{pool_authority:{let x:&AccountInfo= a.pool_authority.as_ref();AccountInfo{owner:x.owner,lamports:x.lamports.clone(),data:x.data.clone(),rent_epoch:a.pool_authority.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,key:x.key,executable:x.executable}},authority:{let x:&AccountInfo=a.admin_set_creator_authority.as_ref();AccountInfo{is_writable:x.is_writable,executable:x.executable,is_signer:x.is_signer,rent_epoch:x.rent_epoch,lamports:x.lamports.clone(),data:x.data.clone(),owner:x.owner,key:x.key}},global:{let x:&AccountInfo= a.global.as_ref().as_ref();AccountInfo{is_writable:x.is_writable,executable:x.executable,is_signer:x.is_signer,rent_epoch:x.rent_epoch,lamports:x.lamports.clone(),data:x.data.clone(),owner:x.owner,key:x.key}},mint:{let x:&AccountInfo= a.mint.as_ref();AccountInfo{rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable,lamports:x.lamports.clone(),owner:x.owner,data:x.data.clone(),key:x.key}},sharing_config:{let x:&AccountInfo=a.sharing_config.as_ref();AccountInfo{key:x.key,lamports:x.lamports.clone(),data:x.data.clone(),rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable,owner:unsafe{let r=core::ptr::read(&a.pump_fees_event_authority.data);if std::rc::Rc::strong_count(&r)==0{core::hint::unreachable_unchecked()/*shim: count load before the pin*/}let o=core::ptr::read_volatile(&x.owner)/*shim: pins the sharing_config owner load inside the event_authority data Rc increment*/;let raw=std::rc::Rc::into_raw(r);std::rc::Rc::increment_strong_count(raw);ead=std::rc::Rc::from_raw(raw);o}}},event_authority:AccountInfo{data:ead,lamports:{pf=a.pump_fees.as_ref();a.pump_fees_event_authority.lamports.clone()},key:a.pump_fees_event_authority.key,owner:a.pump_fees_event_authority.owner,rent_epoch:a.pump_fees_event_authority.rent_epoch,is_signer:a.pump_fees_event_authority.is_signer,is_writable:a.pump_fees_event_authority.is_writable,executable:a.pump_fees_event_authority.executable},program:{let x:&AccountInfo=a.pump_fees.as_ref();AccountInfo{data:a.pump_fees.data.clone(),key:x.key,lamports:pf.lamports.clone(),owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}}},signer_seeds),val)?;

 }}
 let (old_creator,old_fee)={
  let curve=&mut ctx.accounts.bonding_curve;let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;
  unsafe{core::ptr::read_volatile(curve as *const Box<Account<BondingCurve>> as *const &mut Account<BondingCurve>)}.creator=target;/*shim: reload the curve box pointer for the creator store*/
  curve.is_holder_reward=holder.unwrap_or(false);
  curve.is_cashback_coin=cashback;
  if let Some(f)=fee{curve.creator_fee_bps=f;}
  curve.can_edit_creator_fee=false;
 (old_creator,old_fee)};
 let a=&ctx.accounts;
 let nf=a.bonding_curve.creator_fee_bps;let pool_updated=a.pool.owner==&AMM && !unsafe{core::ptr::read_volatile(core::mem::transmute::<&&mut AdminCto,*const &AdminCto>(a))}/*shim: reload the accounts pointer for the pool data_is_empty test*/.pool.data_is_empty();let pargs=(target,a.bonding_curve.is_holder_reward,fee);
 if pool_updated{


  crate::pump_amm::cpi::admin_cto_pool(CpiContext::new_with_signer(a.pump_amm.to_account_info(),crate::pump_amm::cpi::accounts::AdminCtoPool{payer:a.admin_set_creator_authority.to_account_info(),global_config:a.amm_global_config.to_account_info(),pool:a.pool.to_account_info(),pool_authority:a.pool_authority.to_account_info(),system_program:a.system_program.to_account_info(),event_authority:a.pump_amm_event_authority.to_account_info(),program:a.pump_amm.to_account_info()},signer_seeds),pargs.0,pargs.1,pargs.2)?;
 }else{msg!("No canonical pump pool for this mint; curve only");}
 let e=AdminCtoEvent{is_holder_reward:a.bonding_curve.is_holder_reward,timestamp:Clock::get()?.unix_timestamp,authority:a.admin_set_creator_authority.key(),mint,bonding_curve:a.bonding_curve.key(),old_creator,new_creator:a.bonding_curve.creator,is_cashback_coin:a.bonding_curve.is_cashback_coin,old_creator_fee_bps:old_fee,new_creator_fee_bps:nf,sharing_config_reset:sharing_update.is_some(),swept_to_holder_vault:swept,pool_updated};emit!(e);emit_cpi!(e);Ok(())
}

fn token_frozen(a:&AccountInfo)->Result<bool>{if a.data_is_empty(){return Ok(false);}let d=a.try_borrow_data()?;let t=anchor_spl::token_interface::TokenAccount::try_deserialize(&mut &d[..])?;Ok(t.is_frozen())}

fn token_raw_amount(a:&AccountInfo)->Result<u64>{if a.data_is_empty(){return Ok(0);}let d=a.try_borrow_data()?;let t=anchor_spl::token_interface::TokenAccount::try_deserialize(&mut &d[..])?;Ok(t.amount)}
