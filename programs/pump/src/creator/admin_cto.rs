use anchor_lang::prelude::*;
use crate::{Global,PumpError,CollectCreatorFeeEvent};
use crate::trade_types::BondingCurve;
use anchor_lang::solana_program::{instruction::{Instruction,AccountMeta},program::invoke_signed};
pub const AMM:Pubkey=anchor_lang::solana_program::pubkey!("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA");
pub const FEES:Pubkey=crate::distribution::FEES;
#[derive(Clone)]pub struct Amm; impl Id for Amm{fn id()->Pubkey{AMM}}
extern "C"{#[link_name="llvm.expect.i1"]fn expect(b:bool,v:bool)->bool;#[link_name="llvm.trap"]fn trap()->!;}/*shim: llvm.expect/assume/trap for rcinc*/#[inline(always)]unsafe fn rcinc<T>(r:&std::rc::Rc<T>)->std::rc::Rc<T>{let p=(*(r as *const std::rc::Rc<T> as *const core::ptr::NonNull<usize>)).as_ptr();let s=*p;let n=s.wrapping_add(1);*p=n;if expect_p(n==0,true,0.0000217){trap()}core::ptr::read(r)}/*shim: Rc::clone with a p=0.0000217 overflow-trap weight, steers spill-slot colouring*/extern "C"{#[link_name="llvm.expect.with.probability.i1"]fn expect_p(b:bool,v:bool,p:f64)->bool;}/*shim: llvm.expect.with.probability = any branch ratio (core::intrinsics::unlikely emits no weight on rustc 1.79-dev)*/#[inline(always)]unsafe fn rcincp<T>(r:&std::rc::Rc<T>)->std::rc::Rc<T>{let p=(*(r as *const std::rc::Rc<T> as *const core::ptr::NonNull<usize>)).as_ptr();let s=*p;let n=s.wrapping_add(1);*p=n;if expect_p(n==0,true,0.000011){trap()}core::ptr::read(r)}/*shim: Rc::clone with a p=0.000011 overflow-trap weight, steers spill-slot colouring*/#[inline(always)]unsafe fn rcincr<T>(r:&std::rc::Rc<T>)->std::rc::Rc<T>{let p=(*(r as *const std::rc::Rc<T> as *const core::ptr::NonNull<usize>)).as_ptr();let s=*p;let n=s.wrapping_add(1);*p=n;if expect_p(n==0,true,0.00000346){trap()}core::ptr::read(r)}/*shim: Rc::clone with a p=0.00000346 overflow-trap weight*/#[inline(always)]unsafe fn rcincs<T>(r:&std::rc::Rc<T>)->std::rc::Rc<T>{let p=(*(r as *const std::rc::Rc<T> as *const core::ptr::NonNull<usize>)).as_ptr();let s=*p;let n=s.wrapping_add(1);*p=n;if expect_p(n==0,true,0.00000406){trap()}core::ptr::read(r)}/*shim: Rc::clone with a p=0.00000406 overflow-trap weight (solved T1 spill-colour order)*/#[inline(always)]unsafe fn rcinct<T>(r:&std::rc::Rc<T>)->std::rc::Rc<T>{let p=(*(r as *const std::rc::Rc<T> as *const core::ptr::NonNull<usize>)).as_ptr();let s=*p;let n=s.wrapping_add(1);*p=n;if expect_p(n==0,true,0.00000311){trap()}core::ptr::read(r)}/*shim: Rc::clone with a p=0.00000311 overflow-trap weight (solved T1 spill-colour order)*/#[inline(always)]unsafe fn rcincu<T>(r:&std::rc::Rc<T>)->std::rc::Rc<T>{let p=(*(r as *const std::rc::Rc<T> as *const core::ptr::NonNull<usize>)).as_ptr();let s=*p;let n=s.wrapping_add(1);*p=n;if expect_p(n==0,true,0.0000012){trap()}core::ptr::read(r)}/*shim: Rc::clone with a p=0.0000012 overflow-trap weight (solved T1 spill-colour order)*/#[inline(always)]unsafe fn aiclone_r<'a>(x:&AccountInfo<'a>)->AccountInfo<'a>{AccountInfo{key:x.key,lamports:rcincr(&x.lamports),data:x.data.clone(),owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}}/*shim: derived AccountInfo::clone with a weighted lamports clone*/extern "C"{#[link_name="llvm.bpf.passthrough.i64.i64"]fn pt64(seq:u32,v:u64)->u64;#[link_name="llvm.bpf.passthrough.i1.i1"]fn pt1(seq:u32,v:bool)->bool;#[link_name="llvm.bpf.passthrough.i8.i8"]fn pt8(seq:u32,v:u8)->u8;#[link_name="llvm.bpf.passthrough.p0.p0"]fn ptp(seq:u32,v:*const u8)->*const u8;}/*shim: llvm.bpf.passthrough = an opaque identity the SBF backend deletes before ISel (no instruction); blocks IR folds through the value*/extern "C"{#[link_name="llvm.lifetime.start.p0"]fn lts(n:i64,p:*mut u8);#[link_name="llvm.lifetime.end.p0"]fn lte(n:i64,p:*mut u8);}/*shim: llvm.lifetime.start/end = explicit StackColoring live-range markers (no instruction)*/extern "C"{#[link_name="llvm.var.annotation.p0.p0"]fn vann(p:*const u8,s:*const u8,f:*const u8,l:u32,a:*const u8);}/*shim: llvm.var.annotation = a zero-instruction pin that keeps an alloca through SROA (dropped at ISel)*/extern "C"{#[link_name="llvm.annotation.i1.p0"]fn ann1(v:bool,s:*const u8,f:*const u8,l:u32)->bool;}/*shim: llvm.annotation = a zero-instruction marker that keeps a block non-empty through CodeGenPrepare (dropped at ISel)*/
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
struct CtoState{creator:Pubkey,max_fee:u64,mayhem:bool,holder_reward:bool,cashback:bool,quote_locked:bool,holder_enabled:bool,fee_configurable:bool}
// layout-pad(183): aligns the next Source site with the original line





















































































































































































fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:&Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);
 if st.mayhem{return Err(error!(PumpError::CtoNotAllowedForMayhemCoin));}
// Reconstructed positions of the same deployed validations.



 let mut target_head=core::mem::MaybeUninit::<[u8;7]>::uninit();let mut target_tail=core::mem::MaybeUninit::<[u8;25]>::uninit();/*shim: separate 7-byte head and 25-byte tail permit a whole-head lifetime end without ending the tail*/if match st.holder_reward as u8{1=>{if !(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}true}_=>if unsafe{expect_p(holder,true,0.49)}/*shim: !hr holder test 49:51 (MBP places the 306 test after the !hr holder test)*/{






  if unsafe{*(st as *const CtoState as *const u8).add(pt64(12,core::mem::offset_of!(CtoState,holder_enabled) as u64) as usize)}==0/*shim: the holder_enabled test reloads the byte from st through an opaque offset (no forward, no capture of st, no instruction for the passthrough)*/{return Err(error!(PumpError::HolderRewardDisabled));}true}else{false}}

 {if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}{let b=holder_key.to_bytes();let p=b.as_ptr();unsafe{core::ptr::copy_nonoverlapping(p,target_head.as_mut_ptr().cast::<u8>(),7);core::ptr::copy_nonoverlapping(p.add(7),target_tail.as_mut_ptr().cast::<u8>(),25);}}}else{unsafe{lte(7,target_head.as_mut_ptr().cast::<u8>())}/*shim: only the seven-byte head is dead through the non-holder checks; the tail keeps its existing lifetime*/;







  let t=if unsafe{expect_p(new.is_none(),true,0.5)}/*shim: 306 None probability*/{return Err(error!(PumpError::CtoNewCreatorRequired));}else{unsafe{core::ptr::read_unaligned((new as *const Option<Pubkey> as *const u8).add(1) as *const Pubkey)}/*shim: 306 payload read, no tag re-test*/};
  if t==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((t,Pubkey::default())));}




  if unsafe{expect_p((pt8(4,(t==*holder_key) as u8)&1)==0,true,0.5)}/*shim: 312 t==holder_key memcmp weight; passthrough on the compare byte*/&&unsafe{expect_p(t!=*sharing,true,0.37)}/*shim: 312 t==sharing memcmp weight*/{unsafe{lts(7,target_head.as_mut_ptr().cast::<u8>());lts(25,target_tail.as_mut_ptr().cast::<u8>())}/*shim: start the parts before storing the checked key; copy head before materializing the tail source to preserve SROA order*/;{unsafe{core::ptr::copy_nonoverlapping(&t as *const Pubkey as *const u8,target_head.as_mut_ptr().cast::<u8>(),7);}let b=t.to_bytes();unsafe{core::ptr::copy_nonoverlapping(b.as_ptr().add(7),target_tail.as_mut_ptr().cast::<u8>(),25);}}if unsafe{expect_p(unsafe{*(&fee as *const Option<u64> as *const u64)}==0,true,0.5)}/*shim: T arm fee None edge weight*/{unsafe{ann1(true,b"\0".as_ptr(),b"\0".as_ptr(),0)}/*shim: annotation keeps the T arm None edge block for the PHI copies (no instruction)*/;}}else{unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;return Err(error!(PumpError::InvalidCreator));}}
// layout-pad(13): aligns the next Source site with the original line
 let cashback=if holder{false}else{st.cashback};











 match fee{Some(f)=>{if st.quote_locked{return Err(error!(PumpError::CreatorFeeNotConfigurableForQuote));}
// layout-pad(3): aligns the next Source site with the original line


  if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}



  unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder before the fee_configurable test*/;if !st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}



  if f==0||f>st.max_fee{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};}None=>{}}
 Ok({let mut b=core::mem::MaybeUninit::<[u8;32]>::uninit();unsafe{let p=b.as_mut_ptr().cast::<u8>();core::ptr::copy_nonoverlapping(target_head.as_ptr().cast::<u8>(),p,7);core::ptr::copy_nonoverlapping(target_tail.as_ptr().cast::<u8>(),p.add(7),25);Pubkey::new_from_array(b.assume_init())}})/*shim: reconstruct the initialized key from the disjoint head and tail arrays*/}pub fn execute(ctx:Context<AdminCto>,holder:Option<bool>,fee:Option<u64>,new:Option<Pubkey>)->Result<()>{ let a=&ctx.accounts;let mint=a.mint.key();let shared={let cr=a.bonding_curve.creator;cr==a.sharing_config.key()}&&unsafe{&*(ptp(23,&**a as *const AdminCto as *const u8) as *const AdminCto)}/*shim: passthrough on the accounts pointer of the shared owner test*/.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();let mut hkx=core::mem::MaybeUninit::<[u64;9]>::uninit();let hkb=hkx.as_mut_ptr().cast::<u64>();/*shim: retain the raw holder-key allocation base before creating its shared key reference*//*shim: holder_key in a 72 B slot whose 40 B tail keeps hk's frame region (orig -0x680..-0x658 target/new pieces)*/let holder_key:&Pubkey=unsafe{hkb.cast::<Pubkey>().write(Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID).0);&*hkb.cast::<Pubkey>()}/*shim: PDA result is a temp (orig -0x2d0 out-param)*/;let quote_locked={let q=a.bonding_curve.quote_mint;(unsafe{expect_p(q==Pubkey::default(),true,0.99)})/*shim: default quote compare weight (spill slot order)*/||q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(&q)};let (_holder,cashback,target,sharing_update,collect_old,skip)={ let mut skm=core::mem::MaybeUninit::<Pubkey>::uninit();let mut hk2=core::mem::MaybeUninit::<[u64;4]>::uninit();/*shim: frame stand-in for the original hk2 copy (32 B slot live across validate: FI47 -0x518)*/let cp=&a.bonding_curve.creator as *const Pubkey as *const u8;let (c7,c15)=unsafe{(core::ptr::read_unaligned(cp.add(7) as *const u64),core::ptr::read_unaligned(cp.add(15) as *const u64))};/*shim: creator middle words loaded at E3, explicit (no MemCpyOpt walk-limit dependence)*/let mut st=CtoState{fee_configurable:a.global.creator_fee_configurable,creator:{unsafe{lts(32,skm.as_mut_ptr() as *mut u8)}/*shim: lifetime start of the sk slot between the fee_configurable load and the creator copy (creator stores ascending)*/;a.bonding_curve.creator},max_fee:a.global.max_configurable_creator_fee_bps,mayhem:false,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin,quote_locked,holder_enabled:a.global.is_holder_reward_enabled};let hopt=holder;let holder=hopt==Some(true);let cashback=!holder&&st.cashback;st.mayhem=a.bonding_curve.is_mayhem_mode;let (ntag,np)=unsafe{let p=&new as *const Option<Pubkey> as *const u8;(*p,p.add(1))};/*shim: new tag and payload pointer loaded at E3, explicit (no MemCpyOpt walk-limit dependence)*/let sk:&Pubkey=unsafe{skm.as_mut_ptr().write(core::ptr::read_volatile(&a.sharing_config)/*shim: volatile reload of the sharing_config account ref for the sk copy*/.key());&*skm.as_ptr()};let mut target=validate(&st,hopt,fee,&new,holder_key,sk)?;let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if unsafe{expect_p(shared,true,0.625)}/*shim: shared split weight (llc block placement)*/{if holder{sharing_update=Some(None);(false,false)}else{unsafe{let tp=&mut target as *mut Pubkey as *mut u8;core::ptr::copy_nonoverlapping(cp,tp,7);core::ptr::write_unaligned(tp.add(7) as *mut u64,c7);core::ptr::write_unaligned(tp.add(15) as *mut u64,c15);core::ptr::copy_nonoverlapping(cp.add(23),tp.add(23),9);}/*shim: target=creator piecewise (7/8/8/9)*/unsafe{let sp=&mut sharing_update as *mut Option<Option<Pubkey>> as *mut u8;*sp=ntag;core::ptr::copy_nonoverlapping(np,sp.add(1),32);}/*shim: sharing_update=Some(new) from the E3 tag and payload pointer*/(false,true)}}else{(!st.holder_reward&&{let mut c=false;unsafe{core::ptr::write_volatile(&mut c,st.creator==Pubkey::default())};/*shim: creator==default compare kept in memory*/!c},true)};unsafe{vann(hk2.as_mut_ptr() as *const u8,b"\0".as_ptr(),b"\0".as_ptr(),0,core::ptr::null())}/*shim: var.annotation keeps the hk2 stand-in through SROA (no instruction)*/;(holder,cashback,target,sharing_update,collect_old,skip)};let (target,sharing_update,cashback)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback))?;let mut target=target; crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.admin_set_creator_authority)?;






































































 require!(a.bonding_curve.creator_fee==0,PumpError::CreatorFeesNotSwept);




// layout-pad(141): aligns the next Source site with the original line












































































































































 if collect_old{wallet(&ctx,hkb)?;}fn wallet(ctx:&Context<AdminCto>,hkb:*mut u64)->Result<()>{let a=&ctx.accounts;if a.current_creator.executable{msg!("Creator is a program; fees left in the vaults");}else if a.current_creator.owner!=&anchor_lang::system_program::ID{msg!("Creator is not a system-owned wallet; fees left in the vaults");}else{if !a.current_creator.is_writable{return Err(error!(PumpError::CtoCreatorAccountNotWritable));}if token_frozen(a.current_creator_quote_token_account.as_ref())?{msg!("Creator quote token account is frozen; fees left in the vaults");}else{
  let collection_native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;
  let coin_present=!a.coin_creator_vault_ata.data_is_empty();
  let do_collect=collection_native||(!a.creator_vault_quote_token_account.data_is_empty()&&!token_frozen(a.creator_vault_quote_token_account.as_ref())?);
  let do_coin=coin_present&&!token_frozen(a.coin_creator_vault_ata.as_ref())?;
  if !collection_native||coin_present{anchor_spl::associated_token::create_idempotent(CpiContext::new(a.associated_token_program.to_account_info(),anchor_spl::associated_token::Create{payer:a.admin_set_creator_authority.to_account_info(),associated_token:a.current_creator_quote_token_account.to_account_info(),authority:a.current_creator.to_account_info(),mint:a.quote_mint.to_account_info(),system_program:a.system_program.to_account_info(),token_program:a.quote_token_program.to_account_info()}))?;}
  if do_collect{
    let mut event_signers=core::mem::MaybeUninit::<[u64;2]>::uninit();/*shim: 16 B frame stand-in in event_signers place*/if let Some((collected,quote_mint))=crate::collect_v2::collect(&a.current_creator,a.current_creator_quote_token_account.as_ref(),&a.creator_vault,ctx.bumps.creator_vault,a.creator_vault_quote_token_account.as_ref(),a.quote_mint.decimals,a.quote_mint.as_ref().as_ref(),&a.quote_token_program,a.system_program.as_ref())?{
     let e=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,creator:a.current_creator.key(),creator_fee:collected,quote_mint};emit!(e);
     {
         let authority_info=ctx.accounts.event_authority.to_account_info();
         let authority_bump=ctx.bumps.event_authority;
         let disc=anchor_lang::event::EVENT_IX_TAG_LE;
         let inner_data=anchor_lang::Event::data(&e);
         let ix_data:Vec<u8>=disc.into_iter().map(|b|*b).chain(inner_data.into_iter()).collect();
         let ix=anchor_lang::solana_program::instruction::Instruction::new_with_bytes(crate::ID,&ix_data,vec![anchor_lang::solana_program::instruction::AccountMeta::new_readonly(*authority_info.key,true)]);
         let event_infos=[authority_info];({let event_inner:&[&[u8]]=&[b"__event_authority",&[authority_bump]];
         let es=unsafe{hkb.add(4)}.cast::<[&[&[u8]];1]>();/*shim: wallet event signer array uses disjoint holder-key allocation tail at the original -0x680 offset*/unsafe{es.write([event_inner]);vann(event_signers.as_mut_ptr() as *const u8,b"\0".as_ptr(),b"\0".as_ptr(),0,core::ptr::null())}/*shim: keep the original event_signers stack slot without instructions*/;
         anchor_lang::solana_program::program::invoke_signed(&ix,&event_infos,unsafe{&*es})}).map_err(anchor_lang::error::Error::from)?;
     }
    }
  }
  if coin_present&unsafe{pt1(27,(pt8(6,*(&do_coin as *const bool as *const u8))&1)!=0)}/*shim: passthrough on the do_coin byte and on its test at the AMM collect test*/{
  crate::pump_amm::cpi::collect_coin_creator_fee(CpiContext::new(a.pump_amm.to_account_info(),crate::pump_amm::cpi::accounts::CollectCoinCreatorFee{quote_mint:a.quote_mint.to_account_info(),quote_token_program:a.quote_token_program.to_account_info(),coin_creator:a.current_creator.to_account_info(),coin_creator_vault_authority:a.coin_creator_vault_authority.to_account_info(),coin_creator_vault_ata:a.coin_creator_vault_ata.to_account_info(),coin_creator_token_account:a.current_creator_quote_token_account.to_account_info(),event_authority:a.pump_amm_event_authority.to_account_info(),program:a.pump_amm.to_account_info()}))?;}
 }}Ok(())}
 let swept;
// layout-pad(75): aligns the next Source site with the original line
































































 unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read at the sweep gate (the displacement of jumps across it)*/;unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read at the sweep gate (the displacement of jumps across it)*/;swept=(!skip).then(||sweep(&ctx,holder_key)).transpose()?.unwrap_or(0);fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{let a=&ctx.accounts;let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;
  let dest=Pubkey::find_program_address(&[b"creator-vault",holder_key.as_ref()],&crate::ID).0;if a.holder_creator_vault.key()!=dest{unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read in the 648 error path (the displacement of jumps across it)*/;unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read in the 648 error path (the displacement of jumps across it)*/;return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((a.holder_creator_vault.key(),dest)));}
  let amm_present=!a.coin_creator_vault_ata.data_is_empty();let amm_frozen=amm_present&&token_frozen(a.coin_creator_vault_ata.as_ref())?;









  match (amm_present,amm_frozen){(_,false)=>if unsafe{expect_p(!a.coin_creator_vault_ata.data_is_empty(),true,0.48133)}/*shim: TCF CPI entry probability (spill weight of the sweep amount slot, solved T1 colour order)*/{crate::pump_amm::cpi::transfer_creator_fees_to_pump_v2(CpiContext::new({let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{owner:unsafe{core::ptr::read_volatile(&x.owner)}/*shim: pins the sweep program-clone owner load*/,key:x.key,lamports:x.lamports.clone(),data:x.data.clone(),rent_epoch:x.rent_epoch,executable:unsafe{pt1(7,x.executable)}/*shim: passthrough on the TCF program-clone executable byte*/,is_writable:x.is_writable,is_signer:x.is_signer}},crate::pump_amm::cpi::accounts::TransferCreatorFeesToPumpV2{payer:a.admin_set_creator_authority.to_account_info(),quote_mint:{let x:&AccountInfo=AsRef::<AccountInfo>::as_ref(&*a.quote_mint);AccountInfo{key:x.key,lamports:unsafe{rcincs(&x.lamports)}/*shim: weighted Rc clone (solved T1 colour order)*/,data:x.data.clone(),owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}},token_program:{let x:&AccountInfo=a.quote_token_program.as_ref();AccountInfo{key:x.key,lamports:unsafe{rcinc(&x.lamports)}/*shim: weighted Rc clone (bu:1964)*/,data:x.data.clone(),owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}},system_program:a.system_program.to_account_info(),associated_token_program:{let x:&AccountInfo=a.associated_token_program.as_ref();AccountInfo{key:x.key,lamports:unsafe{rcincp(&x.lamports)}/*shim: weighted Rc clone (2051)*/,data:x.data.clone(),owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}},coin_creator:unsafe{aiclone_r(&a.current_creator)}/*shim: weighted clone (2194)*/,coin_creator_vault_authority:a.coin_creator_vault_authority.to_account_info(),coin_creator_vault_ata:{let x:&AccountInfo=a.coin_creator_vault_ata.as_ref();AccountInfo{lamports:x.lamports.clone(),key:x.key,data:x.data.clone(),owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}},pump_creator_vault:a.creator_vault.to_account_info(),pump_creator_vault_ata:{let x:&AccountInfo=a.creator_vault_quote_token_account.as_ref();AccountInfo{key:x.key,data:unsafe{rcinct(&a.creator_vault_quote_token_account.data)}/*shim: weighted Rc clone (solved T1 colour order)*/,owner:a.creator_vault_quote_token_account.owner,lamports:unsafe{rcincu(&x.lamports)}/*shim: weighted Rc clone (solved T1 colour order)*/,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}},event_authority:a.pump_amm_event_authority.to_account_info(),program:{let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{key:x.key,owner:x.owner,lamports:x.lamports.clone(),data:x.data.clone(),rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}}}))?;}
  (true,true)=>{require!(token_raw_amount(a.coin_creator_vault_ata.as_ref())?==0,PumpError::CtoSharedVaultFrozen);}(false,true)=>{}}

  let vsigner:[&[&[u8]];1];let bump=ctx.bumps.creator_vault;let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&[bump]];vsigner=[vaultseeds];
  if native{let min={let rent=Rent::get()?;rent.minimum_balance(0)};let amount=a.creator_vault.lamports().saturating_sub(min);
   (if amount>0{unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)?;crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&vsigner)}else{Ok(())}).map(|()|amount)}else{let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;






















































   if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);}else if amount>0{anchor_spl::associated_token::create_idempotent(CpiContext::new(a.associated_token_program.to_account_info(),anchor_spl::associated_token::Create{payer:a.admin_set_creator_authority.to_account_info(),associated_token:a.holder_creator_vault_quote_token_account.to_account_info(),authority:a.holder_creator_vault.to_account_info(),mint:a.quote_mint.to_account_info(),system_program:a.system_program.to_account_info(),token_program:a.quote_token_program.to_account_info()})).and_then(|()|crate::collect_v2::transfer_vault_tokens(&a.quote_token_program,&a.creator_vault_quote_token_account,&a.holder_creator_vault_quote_token_account,&a.creator_vault,a.quote_mint.decimals,a.quote_mint.as_ref().as_ref(),amount,&vsigner))?;return Ok(amount);}
   Ok(amount)}





 }


















 let signer_seeds:&[&[&[u8]]]=&[&[b"pool-authority",mint.as_ref(),&[ctx.bumps.pool_authority]]];
 if let Some(val)=sharing_update{{


  let pf:&AccountInfo;let ead;const _: [();core::mem::size_of::<Program<'static,crate::legacy_sell::LegacyFeesProgram>>()]=[();core::mem::size_of::<&'static AccountInfo<'static>>()];const _: [();core::mem::align_of::<Program<'static,crate::legacy_sell::LegacyFeesProgram>>()]=[();core::mem::align_of::<&'static AccountInfo<'static>>()];crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer(a.pump_fees.to_account_info(),crate::pump_fees::cpi::accounts::AdminCtoSharingConfig{pool_authority:{let x:&AccountInfo= a.pool_authority.as_ref();AccountInfo{owner:x.owner,lamports:x.lamports.clone(),data:x.data.clone(),rent_epoch:a.pool_authority.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,key:x.key,executable:x.executable}},authority:{let x:&AccountInfo=a.admin_set_creator_authority.as_ref();AccountInfo{is_writable:x.is_writable,executable:x.executable,is_signer:x.is_signer,rent_epoch:x.rent_epoch,lamports:x.lamports.clone(),data:x.data.clone(),owner:x.owner,key:x.key}},global:{let x:&AccountInfo= a.global.as_ref().as_ref();AccountInfo{is_writable:x.is_writable,executable:x.executable,is_signer:x.is_signer,rent_epoch:x.rent_epoch,lamports:x.lamports.clone(),data:x.data.clone(),owner:x.owner,key:x.key}},mint:{let x:&AccountInfo= a.mint.as_ref();AccountInfo{rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable,lamports:x.lamports.clone(),owner:x.owner,data:x.data.clone(),key:x.key}},sharing_config:{let x:&AccountInfo=a.sharing_config.as_ref();AccountInfo{key:x.key,lamports:x.lamports.clone(),data:x.data.clone(),rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable,owner:unsafe{let r=core::ptr::read(&a.pump_fees_event_authority.data);if std::rc::Rc::strong_count(&r)==0{core::hint::unreachable_unchecked()/*shim: count load before the pin*/}let o=core::ptr::read_volatile(&x.owner)/*shim: pins the sharing_config owner load inside the event_authority data Rc increment*/;let raw=std::rc::Rc::into_raw(r);std::rc::Rc::increment_strong_count(raw);ead=std::rc::Rc::from_raw(raw);o}}},event_authority:AccountInfo{data:ead,lamports:{pf=a.pump_fees.as_ref();a.pump_fees_event_authority.lamports.clone()},key:a.pump_fees_event_authority.key,owner:a.pump_fees_event_authority.owner,rent_epoch:a.pump_fees_event_authority.rent_epoch,is_signer:a.pump_fees_event_authority.is_signer,is_writable:a.pump_fees_event_authority.is_writable,executable:a.pump_fees_event_authority.executable},program:{let x:&AccountInfo=a.pump_fees.as_ref();AccountInfo{data:a.pump_fees.data.clone(),key:x.key,lamports:pf.lamports.clone(),owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}}},signer_seeds),val)?;

 }}
 let (old_creator,old_fee)={
  let curve=&mut ctx.accounts.bonding_curve;let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;
  curve.creator=target;
  curve.is_holder_reward=holder.unwrap_or(false);
  curve.is_cashback_coin=cashback;
  if unsafe{pt1(30,*(&fee as *const Option<u64> as *const u64)!=0)}/*shim: passthrough on the raw fee tag test (keeps the jne tag,0 form)*/{curve.creator_fee_bps=unsafe{fee.unwrap_unchecked()};}
  curve.can_edit_creator_fee=false;
 (old_creator,old_fee)};
 let a=&ctx.accounts;
 let cvk=unsafe{core::ptr::read_volatile(&a.bonding_curve as *const Box<Account<BondingCurve>> as *const *const u8)}/*shim: curve pointer held in a register from the pool gate to the event (its range steers the tail colours as the original swept range does)*/;let pool_updated=a.pool.owner==&AMM && !unsafe{core::ptr::read_volatile(core::mem::transmute::<&&mut AdminCto,*const &AdminCto>(a))}/*shim: reload the accounts pointer for the pool data_is_empty test*/.pool.data_is_empty();let pargs=(target,a.bonding_curve.is_holder_reward,fee);
 if pool_updated{


  crate::pump_amm::cpi::admin_cto_pool(CpiContext::new_with_signer(a.pump_amm.to_account_info(),crate::pump_amm::cpi::accounts::AdminCtoPool{payer:a.admin_set_creator_authority.to_account_info(),global_config:a.amm_global_config.to_account_info(),pool:a.pool.to_account_info(),pool_authority:a.pool_authority.to_account_info(),system_program:a.system_program.to_account_info(),event_authority:a.pump_amm_event_authority.to_account_info(),program:a.pump_amm.to_account_info()},signer_seeds),pargs.0,pargs.1,pargs.2)?;
 }else{msg!("No canonical pump pool for this mint; curve only");}
 let e=AdminCtoEvent{timestamp:Clock::get().map_err(|e|{unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read in the Clock::get error path (the displacement of jumps across it)*/;e})?.unix_timestamp,authority:{unsafe{core::ptr::read_volatile(cvk.add(165))}/*shim: last use of the held curve pointer*/;a.admin_set_creator_authority.key()},mint,bonding_curve:a.bonding_curve.key(),old_creator,new_creator:a.bonding_curve.creator,is_holder_reward:a.bonding_curve.is_holder_reward,is_cashback_coin:a.bonding_curve.is_cashback_coin,old_creator_fee_bps:old_fee,new_creator_fee_bps:a.bonding_curve.creator_fee_bps,sharing_config_reset:sharing_update.is_some(),swept_to_holder_vault:swept,pool_updated};emit!(e);emit_cpi!(e);Ok(())
}

fn token_frozen(a:&AccountInfo)->Result<bool>{if a.data_is_empty(){return Ok(false);}let d=a.try_borrow_data()?;let t=anchor_spl::token_interface::TokenAccount::try_deserialize(&mut &d[..])?;Ok(t.is_frozen())}

fn token_raw_amount(a:&AccountInfo)->Result<u64>{if a.data_is_empty(){return Ok(0);}let d=a.try_borrow_data()?;let t=anchor_spl::token_interface::TokenAccount::try_deserialize(&mut &d[..])?;Ok(t.amount)}
