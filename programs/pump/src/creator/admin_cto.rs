use anchor_lang::prelude::*;
use crate::{Global,PumpError,CollectCreatorFeeEvent};
use crate::trade_types::BondingCurve;
use anchor_lang::solana_program::{instruction::{Instruction,AccountMeta},program::invoke_signed};
pub const AMM:Pubkey=anchor_lang::solana_program::pubkey!("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA");
pub const FEES:Pubkey=crate::distribution::FEES;
#[derive(Clone)]pub struct Amm; impl Id for Amm{fn id()->Pubkey{AMM}}
extern "C"{#[link_name="llvm.expect.i1"]fn expect(b:bool,v:bool)->bool;#[link_name="llvm.trap"]fn trap()->!;#[link_name="llvm.trap"]fn trapu();}/*shim: llvm.expect/assume/trap for rcinc; trapu is llvm.trap with a unit return so a mir! Call can name it*/#[inline(always)]unsafe fn rcinc<T>(r:&std::rc::Rc<T>)->std::rc::Rc<T>{let p=(*(r as *const std::rc::Rc<T> as *const core::ptr::NonNull<usize>)).as_ptr();let s=*p;let n=s.wrapping_add(1);*p=n;if expect_p(n==0,true,0.0000217){trap()}core::ptr::read(r)}/*shim: Rc::clone with a p=0.0000217 overflow-trap weight, steers spill-slot colouring*/extern "C"{#[link_name="llvm.expect.with.probability.i1"]fn expect_p(b:bool,v:bool,p:f64)->bool;}/*shim: llvm.expect.with.probability = any branch ratio (core::intrinsics::unlikely emits no weight on rustc 1.79-dev)*/#[inline(always)]unsafe fn rcincp<T>(r:&std::rc::Rc<T>)->std::rc::Rc<T>{let p=(*(r as *const std::rc::Rc<T> as *const core::ptr::NonNull<usize>)).as_ptr();let s=*p;let n=s.wrapping_add(1);*p=n;if expect_p(n==0,true,0.000011){trap()}core::ptr::read(r)}/*shim: Rc::clone with a p=0.000011 overflow-trap weight, steers spill-slot colouring*/#[inline(always)]unsafe fn rcincr<T>(r:&std::rc::Rc<T>)->std::rc::Rc<T>{let p=(*(r as *const std::rc::Rc<T> as *const core::ptr::NonNull<usize>)).as_ptr();let s=*p;let n=s.wrapping_add(1);*p=n;if expect_p(n==0,true,0.00000346){trap()}core::ptr::read(r)}/*shim: Rc::clone with a p=0.00000346 overflow-trap weight*/#[inline(always)]unsafe fn rcincs<T>(r:&std::rc::Rc<T>)->std::rc::Rc<T>{let p=(*(r as *const std::rc::Rc<T> as *const core::ptr::NonNull<usize>)).as_ptr();let s=*p;let n=s.wrapping_add(1);*p=n;if expect_p(n==0,true,0.00000406){trap()}core::ptr::read(r)}/*shim: Rc::clone with a p=0.00000406 overflow-trap weight (solved T1 spill-colour order)*/#[inline(always)]unsafe fn rcinct<T>(r:&std::rc::Rc<T>)->std::rc::Rc<T>{let p=(*(r as *const std::rc::Rc<T> as *const core::ptr::NonNull<usize>)).as_ptr();let s=*p;let n=s.wrapping_add(1);*p=n;if expect_p(n==0,true,0.00000311){trap()}core::ptr::read(r)}/*shim: Rc::clone with a p=0.00000311 overflow-trap weight (solved T1 spill-colour order)*/#[inline(always)]unsafe fn rcincu<T>(r:&std::rc::Rc<T>)->std::rc::Rc<T>{let p=(*(r as *const std::rc::Rc<T> as *const core::ptr::NonNull<usize>)).as_ptr();let s=*p;let n=s.wrapping_add(1);*p=n;if expect_p(n==0,true,0.0000012){trap()}core::ptr::read(r)}/*shim: Rc::clone with a p=0.0000012 overflow-trap weight (solved T1 spill-colour order)*/#[inline(always)]unsafe fn aiclone_r<'a>(x:&AccountInfo<'a>)->AccountInfo<'a>{AccountInfo{key:x.key,lamports:rcincr(&x.lamports),data:x.data.clone(),owner:x.owner,rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}}/*shim: derived AccountInfo::clone with a weighted lamports clone*/extern "C"{#[link_name="llvm.bpf.passthrough.i64.i64"]fn pt64(seq:u32,v:u64)->u64;#[link_name="llvm.bpf.passthrough.i1.i1"]fn pt1(seq:u32,v:bool)->bool;#[link_name="llvm.bpf.passthrough.i8.i8"]fn pt8(seq:u32,v:u8)->u8;#[link_name="llvm.bpf.passthrough.p0.p0"]fn ptp(seq:u32,v:*const u8)->*const u8;}/*shim: llvm.bpf.passthrough = an opaque identity the SBF backend deletes before ISel (no instruction); blocks IR folds through the value*/extern "C"{#[link_name="llvm.lifetime.start.p0"]fn lts(n:i64,p:*mut u8);#[link_name="llvm.lifetime.end.p0"]fn lte(n:i64,p:*mut u8);}/*shim: llvm.lifetime.start/end = explicit StackColoring live-range markers (no instruction)*/extern "C"{#[link_name="llvm.var.annotation.p0.p0"]fn vann(p:*const u8,s:*const u8,f:*const u8,l:u32,a:*const u8);}/*shim: llvm.var.annotation = a zero-instruction pin that keeps an alloca through SROA (dropped at ISel)*/extern "C"{#[link_name="llvm.assume"]fn assume(b:bool);}/*shim: llvm.assume for rcw*/struct Wt<const D:u32>;impl<const D:u32> Wt<D>{const P:f64=1.0/(D as f64+1.0);}#[inline(always)]unsafe fn rcw<const D:u32,T>(r:&std::rc::Rc<T>)->std::rc::Rc<T>{let p=(*(r as *const std::rc::Rc<T> as *const core::ptr::NonNull<usize>)).as_ptr();let s=*p;assume(s!=0);let n=s.wrapping_add(1);*p=n;if expect_p(n==0,true,Wt::<D>::P){trap()}core::ptr::read(r)}/*shim: Rc::clone with an explicit 1:D overflow-trap weight (clone-run block frequencies)*/macro_rules! aiw{($i:ident,$x:expr,$l:expr,$d:expr)=>{{let $i:&AccountInfo=$x;AccountInfo{key:$i.key,lamports:$l,data:$d,owner:$i.owner,rent_epoch:$i.rent_epoch,is_signer:$i.is_signer,is_writable:$i.is_writable,executable:$i.executable}}}}/*shim: derived AccountInfo::clone with explicit Rc clones*/macro_rules! aiv{($i:ident,$x:expr,$l:expr,$d:expr,$n:ident,$s:ident)=>{{let $i:&AccountInfo=$x;let k=$i.key;let l=$l;let d=$d;$n=unsafe{&*core::ptr::read_volatile($s)};AccountInfo{key:k,lamports:l,data:d,owner:$i.owner,rent_epoch:$i.rent_epoch,is_signer:$i.is_signer,is_writable:$i.is_writable,executable:$i.executable}}}}/*shim: AccountInfo clone that reads the next clone's accounts pointer from its stack slot before this clone's field loads*/
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





















































































































































































const E_CreatorFeeBpsOutOfRange:PumpError=PumpError::CreatorFeeBpsOutOfRange;const E_CreatorFeeNotAllowedForCashbackCoin:PumpError=PumpError::CreatorFeeNotAllowedForCashbackCoin;const E_CreatorFeeNotConfigurable:PumpError=PumpError::CreatorFeeNotConfigurable;const E_CreatorFeeNotConfigurableForQuote:PumpError=PumpError::CreatorFeeNotConfigurableForQuote;const E_CreatorShouldNotBeZero:PumpError=PumpError::CreatorShouldNotBeZero;const E_CtoNewCreatorNotAllowed:PumpError=PumpError::CtoNewCreatorNotAllowed;const E_CtoNewCreatorRequired:PumpError=PumpError::CtoNewCreatorRequired;const E_CtoNotAllowedForMayhemCoin:PumpError=PumpError::CtoNotAllowedForMayhemCoin;const E_HolderRewardCreatorImmutable:PumpError=PumpError::HolderRewardCreatorImmutable;const E_HolderRewardDisabled:PumpError=PumpError::HolderRewardDisabled;const E_InvalidCreator:PumpError=PumpError::InvalidCreator;const R_CreatorFeeBpsOutOfRange:&PumpError=&PumpError::CreatorFeeBpsOutOfRange;const R_CreatorFeeNotAllowedForCashbackCoin:&PumpError=&PumpError::CreatorFeeNotAllowedForCashbackCoin;const R_CreatorFeeNotConfigurable:&PumpError=&PumpError::CreatorFeeNotConfigurable;const R_CreatorFeeNotConfigurableForQuote:&PumpError=&PumpError::CreatorFeeNotConfigurableForQuote;const R_CreatorShouldNotBeZero:&PumpError=&PumpError::CreatorShouldNotBeZero;const R_CtoNewCreatorNotAllowed:&PumpError=&PumpError::CtoNewCreatorNotAllowed;const R_CtoNewCreatorRequired:&PumpError=&PumpError::CtoNewCreatorRequired;const R_CtoNotAllowedForMayhemCoin:&PumpError=&PumpError::CtoNotAllowedForMayhemCoin;const R_HolderRewardCreatorImmutable:&PumpError=&PumpError::HolderRewardCreatorImmutable;const R_HolderRewardDisabled:&PumpError=&PumpError::HolderRewardDisabled;const R_InvalidCreator:&PumpError=&PumpError::InvalidCreator;#[custom_mir(dialect="runtime",phase="optimized")]/*shim: custom MIR body (exact CFG and locals): 306 and holder tests 50:50; a never-true volatile compare with a 50:50 llvm.trap edge heads the t path (its head keeps the frequency block placement needs, the rest runs at the frequency the RA saw before); holder-first 312 compares; the 312 head ends the MBP chain with a never-true volatile compare and llvm.trap, so the 312 rest is placed after 326; a volatile byte load in front of each trap keeps it from merging with the Rc overflow trap*/fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{use core::intrinsics::mir::*;mir!{let _7: bool;let _8: anchor_lang::error::Error;let _9: anchor_lang::error::AnchorError;let _10: std::string::String;let _11: u32;let _12: std::string::String;let _13: std::option::Option<anchor_lang::error::ErrorOrigin>;let _14: anchor_lang::error::ErrorOrigin;let _15: anchor_lang::error::Source;let _16: std::option::Option<anchor_lang::error::ComparedValues>;let _17: bool;let _18: std::mem::MaybeUninit<[u8; 7]>;let _19: std::mem::MaybeUninit<[u8; 25]>;let _20: u8;let _21: bool;let _22: bool;let _23: bool;let _24: anchor_lang::error::Error;let _25: anchor_lang::error::AnchorError;let _26: std::string::String;let _27: u32;let _28: std::string::String;let _29: std::option::Option<anchor_lang::error::ErrorOrigin>;let _30: anchor_lang::error::ErrorOrigin;let _31: anchor_lang::error::Source;let _32: std::option::Option<anchor_lang::error::ComparedValues>;let _33: u8;let _34: *const u8;let _35: *const Pubkey;let _36: bool;let _37: bool;let _38: bool;let _39: anchor_lang::error::Error;let _40: anchor_lang::error::AnchorError;let _41: std::string::String;let _42: u32;let _43: std::string::String;let _44: std::option::Option<anchor_lang::error::ErrorOrigin>;let _45: anchor_lang::error::ErrorOrigin;let _46: anchor_lang::error::Source;let _47: std::option::Option<anchor_lang::error::ComparedValues>;let _48: anchor_lang::error::Error;let _49: anchor_lang::error::AnchorError;let _50: std::string::String;let _51: u32;let _52: std::string::String;let _53: std::option::Option<anchor_lang::error::ErrorOrigin>;let _54: anchor_lang::error::ErrorOrigin;let _55: anchor_lang::error::Source;let _56: std::option::Option<anchor_lang::error::ComparedValues>;let _57: [u8; 32];let _58: *const u8;let _59: &[u8];let _60: &[u8; 32];let _61: *mut u8;let _62: *const u8;let _63: *mut u8;let _64: ();let _65: *mut u8;let _66: Pubkey;let _67: bool;let _68: bool;let _69: u8;let _70: u8;let _71: *const u8;let _72: *const std::option::Option<Pubkey>;let _73: u8;let _74: *const u8;let _75: *const Pubkey;let _76: anchor_lang::error::Error;let _77: anchor_lang::error::AnchorError;let _78: std::string::String;let _79: u32;let _80: std::string::String;let _81: std::option::Option<anchor_lang::error::ErrorOrigin>;let _82: anchor_lang::error::ErrorOrigin;let _83: anchor_lang::error::Source;let _84: std::option::Option<anchor_lang::error::ComparedValues>;let _85: *const Pubkey;let _86: *const u8;let _87: *const u8;let _88: *const std::option::Option<Pubkey>;let _89: bool;let _90: Pubkey;let _91: anchor_lang::error::Error;let _92: anchor_lang::error::Error;let _93: anchor_lang::error::AnchorError;let _94: std::string::String;let _95: u32;let _96: std::string::String;let _97: std::option::Option<anchor_lang::error::ErrorOrigin>;let _98: anchor_lang::error::ErrorOrigin;let _99: anchor_lang::error::Source;let _100: std::option::Option<anchor_lang::error::ComparedValues>;let _101: (Pubkey, Pubkey);let _102: std::mem::MaybeUninit<Pubkey>;let _103: *mut u8;let _104: *const u8;let _105: *const u8;let _106: *const Pubkey;let _107: *mut u8;let _108: u64;let _109: *const u64;let _110: *const u8;let _111: *const u8;let _112: *const std::option::Option<Pubkey>;let _113: std::mem::MaybeUninit<Pubkey>;let _114: Pubkey;let _115: bool;let _116: bool;let _117: u8;let _118: u8;let _119: u8;let _120: bool;let _121: bool;let _122: bool;let _123: u8;let _124: *const u8;let _125: *const Pubkey;let _126: u8;let _127: *const u8;let _128: *const Pubkey;let _129: u8;let _130: *const u8;let _131: *const Pubkey;let _132: u8;let _133: *const u8;let _134: *const Pubkey;let _135: u8;let _136: *const u8;let _137: *const Pubkey;let _138: u8;let _139: *const u8;let _140: *const Pubkey;let _141: u8;let _142: *const u8;let _143: *const Pubkey;let _144: u8;let _145: *const u8;let _146: *const Pubkey;let _147: u8;let _148: *const u8;let _149: *const Pubkey;let _150: anchor_lang::error::Error;let _151: anchor_lang::error::AnchorError;let _152: std::string::String;let _153: u32;let _154: std::string::String;let _155: std::option::Option<anchor_lang::error::ErrorOrigin>;let _156: anchor_lang::error::ErrorOrigin;let _157: anchor_lang::error::Source;let _158: std::option::Option<anchor_lang::error::ComparedValues>;let _159: ();let _160: ();let _161: *mut u8;let _162: *mut u8;let _163: *const u8;let _164: *const Pubkey;let _165: *mut u8;let _166: [u8; 32];let _167: *const u8;let _168: *const u8;let _169: &[u8];let _170: &[u8; 32];let _171: *mut u8;let _172: bool;let _173: bool;let _174: isize;let _175: u64;let _176: bool;let _177: anchor_lang::error::Error;let _178: anchor_lang::error::AnchorError;let _179: std::string::String;let _180: u32;let _181: std::string::String;let _182: std::option::Option<anchor_lang::error::ErrorOrigin>;let _183: anchor_lang::error::ErrorOrigin;let _184: anchor_lang::error::Source;let _185: std::option::Option<anchor_lang::error::ComparedValues>;let _186: bool;let _187: anchor_lang::error::Error;let _188: anchor_lang::error::AnchorError;let _189: std::string::String;let _190: u32;let _191: std::string::String;let _192: std::option::Option<anchor_lang::error::ErrorOrigin>;let _193: anchor_lang::error::ErrorOrigin;let _194: anchor_lang::error::Source;let _195: std::option::Option<anchor_lang::error::ComparedValues>;let _196: u8;let _197: *const u8;let _198: *const Pubkey;let _199: bool;let _200: anchor_lang::error::Error;let _201: anchor_lang::error::AnchorError;let _202: std::string::String;let _203: u32;let _204: std::string::String;let _205: std::option::Option<anchor_lang::error::ErrorOrigin>;let _206: anchor_lang::error::ErrorOrigin;let _207: anchor_lang::error::Source;let _208: std::option::Option<anchor_lang::error::ComparedValues>;let _209: bool;let _210: u64;let _211: anchor_lang::error::Error;let _212: anchor_lang::error::AnchorError;let _213: std::string::String;let _214: u32;let _215: std::string::String;let _216: std::option::Option<anchor_lang::error::ErrorOrigin>;let _217: anchor_lang::error::ErrorOrigin;let _218: anchor_lang::error::Source;let _219: std::option::Option<anchor_lang::error::ComparedValues>;let _220: u8;let _221: *const u8;let _222: *const Pubkey;let _223: Pubkey;let _224: std::mem::MaybeUninit<[u8; 32]>;let _225: *mut u8;let _226: *const u8;let _227: *const u8;let _228: *mut u8;let _229: std::mem::MaybeUninit<[u8; 32]>;let _230: isize;let _231: bool;let _232: isize;let _233: *const [u8];let _234: *mut std::mem::MaybeUninit<[u8; 7]>;let _235: *mut std::mem::MaybeUninit<[u8; 25]>;let _236: *mut std::mem::MaybeUninit<[u8; 7]>;let _237: [u8; 32];let _238: &[u8; 32];let _239: &[u8; 32];let _240: *mut std::mem::MaybeUninit<Pubkey>;let _241: u64;let _242: *const u8;let _243: *const u64;let _244: [u8; 32];let _245: &[u8; 32];let _246: &[u8; 32];let _247: &[u8; 32];let _248: &[u8; 32];let _249: *mut std::mem::MaybeUninit<[u8; 7]>;let _250: *mut std::mem::MaybeUninit<[u8; 25]>;let _251: *mut std::mem::MaybeUninit<[u8; 7]>;let _252: *const [u8];let _253: *mut std::mem::MaybeUninit<[u8; 25]>;let _254: *mut std::mem::MaybeUninit<[u8; 32]>;let _255: *const std::mem::MaybeUninit<[u8; 7]>;let _256: *const std::mem::MaybeUninit<[u8; 25]>;let _257: [u8; 32];let _258: [u8; 32];let _259: Pubkey;let _260: [u8; 32];let _810: u8;let _811: u8;let _812: bool;let _813: ();let _814: *const u8;let _815: *const Pubkey;let _832: u8;let _860: *const Pubkey;let _861: *const u8;let _862: u8;let _863: u8;let _864: bool;let _865: bool;let _866: ();let _870: u8;let _871: *const u8;let _872: *const Pubkey;let xd1: *mut [u8;24];let xs1: *const [u8;24];let x_245: &Pubkey;let x_246: &Pubkey;let x_247: &Pubkey;let x_248: &Pubkey;let xd2: *mut [u8;7];let xs2: *const [u8;7];let xu3: (&[u8;32],usize);let xd4: *mut [u8;25];let xs4: *const [u8;25];let xd5: *mut [u8;7];let xs5: *const [u8;7];let xd6: *mut [u8;25];let xs6: *const [u8;25];let xu7: (&[u8;32],usize);let xd8: *mut [u8;7];let xs8: *const [u8;7];let xd9: *mut [u8;25];let xs9: *const [u8;25];let x_238: &Pubkey;let x_239: &Pubkey;let xd10: *mut [u8;8];let xs10: *const [u8;8];{StorageLive(_7);_7 = ((*st)).mayhem;match Move(_7) {false => bb5,_ => bb1}}bb1={StorageLive(_8);StorageLive(_9);StorageLive(_10);Call(_10 = PumpError::name(R_CtoNotAllowedForMayhemCoin),ReturnTo(bb2),UnwindUnreachable())}bb2={StorageLive(_11);Call(_11 = <u32 as From<PumpError>>::from(E_CtoNotAllowedForMayhemCoin),ReturnTo(bb85),UnwindUnreachable())}bb3={StorageLive(_13);StorageLive(_14);StorageLive(_15);_15 = anchor_lang::error::Source{filename:"programs/pump/src/creator/admin_cto.rs",line:284_u32};_14 = anchor_lang::error::ErrorOrigin::Source(Move(_15));StorageDead(_15);_13 = Some(Move(_14));StorageDead(_14);StorageLive(_16);_16 = None;_9 = anchor_lang::error::AnchorError{error_name:Move(_10),error_code_number:Move(_11),error_msg:Move(_12),error_origin:Move(_13),compared_values:Move(_16)};StorageDead(_16);StorageDead(_13);StorageDead(_12);StorageDead(_11);StorageDead(_10);Call(_8 = <anchor_lang::error::Error as From<anchor_lang::error::AnchorError>>::from(Move(_9)),ReturnTo(bb4),UnwindUnreachable())}bb4={StorageDead(_9);RET = Err(Move(_8));StorageDead(_8);StorageDead(_7);Goto(bb84)}bb5={StorageDead(_7);StorageLive(_17);StorageLive(_230);_230 = Discriminant(hopt);match Move(_230) {0 => bb87,1 => bb88,_ => bb54}}bb6={StorageLive(_36);StorageLive(_37);_37 = _17;Call(_36 = expect_p(Move(_37),true,0.5f64),ReturnTo(bb14),UnwindUnreachable())}bb7={StorageLive(_22);StorageLive(_23);_23 = _17;Call(_22 = expect_p(Move(_23),true,0.625f64),ReturnTo(bb8),UnwindUnreachable())}bb8={StorageDead(_23);match Move(_22) {false => bb9,_ => bb13}}bb9={StorageLive(_25);StorageLive(_26);Call(_26 = PumpError::name(R_HolderRewardCreatorImmutable),ReturnTo(bb10),UnwindUnreachable())}bb10={StorageLive(_27);Call(_27 = <u32 as From<PumpError>>::from(E_HolderRewardCreatorImmutable),ReturnTo(bb89),UnwindUnreachable())}bb11={StorageLive(_29);StorageLive(_30);StorageLive(_31);_31 = anchor_lang::error::Source{filename:"programs/pump/src/creator/admin_cto.rs",line:289_u32};_30 = anchor_lang::error::ErrorOrigin::Source(Move(_31));StorageDead(_31);_29 = Some(Move(_30));StorageDead(_30);StorageLive(_32);_32 = None;_25 = anchor_lang::error::AnchorError{error_name:Move(_26),error_code_number:Move(_27),error_msg:Move(_28),error_origin:Move(_29),compared_values:Move(_32)};StorageDead(_32);StorageDead(_29);StorageDead(_28);StorageDead(_27);StorageDead(_26);Call(_24 = <anchor_lang::error::Error as From<anchor_lang::error::AnchorError>>::from(Move(_25)),ReturnTo(bb12),UnwindUnreachable())}bb12={StorageDead(_25);StorageLive(_33);StorageLive(_34);_35 = core::ptr::addr_of!((*holder_key));_34 = _35 as *const u8;Call(_33 = core::intrinsics::volatile_load::<u8>(Move(_34)),ReturnTo(bb90),UnwindUnreachable())}bb13={StorageDead(_22);Goto(bb22)}bb14={StorageDead(_37);match Move(_36) {false => bb21,_ => bb15}}bb15={StorageLive(_38);_38 = ((*st)).holder_enabled;match Move(_38) {false => bb16,_ => bb20}}bb16={StorageLive(_39);StorageLive(_40);StorageLive(_41);Call(_41 = PumpError::name(R_HolderRewardDisabled),ReturnTo(bb17),UnwindUnreachable())}bb17={StorageLive(_42);Call(_42 = <u32 as From<PumpError>>::from(E_HolderRewardDisabled),ReturnTo(bb91),UnwindUnreachable())}bb18={StorageLive(_44);StorageLive(_45);StorageLive(_46);_46 = anchor_lang::error::Source{filename:"programs/pump/src/creator/admin_cto.rs",line:296_u32};_45 = anchor_lang::error::ErrorOrigin::Source(Move(_46));StorageDead(_46);_44 = Some(Move(_45));StorageDead(_45);StorageLive(_47);_47 = None;_40 = anchor_lang::error::AnchorError{error_name:Move(_41),error_code_number:Move(_42),error_msg:Move(_43),error_origin:Move(_44),compared_values:Move(_47)};StorageDead(_47);StorageDead(_44);StorageDead(_43);StorageDead(_42);StorageDead(_41);Call(_39 = <anchor_lang::error::Error as From<anchor_lang::error::AnchorError>>::from(Move(_40)),ReturnTo(bb19),UnwindUnreachable())}bb19={StorageDead(_40);RET = Err(Move(_39));StorageDead(_39);StorageDead(_38);StorageDead(_36);Goto(bb81)}bb20={StorageDead(_38);StorageDead(_36);Goto(bb22)}bb21={StorageDead(_36);StorageDead(_20);StorageLive(_65);_236 = core::ptr::addr_of_mut!(_18);_65 = _236 as *mut u8;Call(_64 = lte(7_i64,Move(_65)),ReturnTo(bb26),UnwindUnreachable())}bb22={StorageDead(_20);StorageLive(_232);_232 = Discriminant(new);match Move(_232) {1 => bb93,0 => bb92,_ => bb54}}bb23={StorageLive(_51);Call(_51 = <u32 as From<PumpError>>::from(E_CtoNewCreatorNotAllowed),ReturnTo(bb94),UnwindUnreachable())}bb24={StorageLive(_53);StorageLive(_54);StorageLive(_55);_55 = anchor_lang::error::Source{filename:"programs/pump/src/creator/admin_cto.rs",line:298_u32};_54 = anchor_lang::error::ErrorOrigin::Source(Move(_55));StorageDead(_55);_53 = Some(Move(_54));StorageDead(_54);StorageLive(_56);_56 = None;_49 = anchor_lang::error::AnchorError{error_name:Move(_50),error_code_number:Move(_51),error_msg:Move(_52),error_origin:Move(_53),compared_values:Move(_56)};StorageDead(_56);StorageDead(_53);StorageDead(_52);StorageDead(_51);StorageDead(_50);Call(_48 = <anchor_lang::error::Error as From<anchor_lang::error::AnchorError>>::from(Move(_49)),ReturnTo(bb25),UnwindUnreachable())}bb25={StorageDead(_49);RET = Err(Move(_48));StorageDead(_48);Goto(bb82)}bb26={StorageDead(_65);StorageLive(_66);StorageLive(_67);StorageLive(_68);StorageLive(_69);StorageLive(_70);StorageLive(_71);StorageLive(_72);_72 = core::ptr::addr_of!(new);_71 = Move(_72) as *const u8;StorageDead(_72);_70 = (*_71);_69 = Move(_70) & 1_u8;StorageDead(_70);_68 = Move(_69) == 0_u8;StorageDead(_69);Call(_67 = expect_p(Move(_68),true,0.5f64),ReturnTo(bb27),UnwindUnreachable())}bb27={StorageDead(_68);match Move(_67) {false => bb860,_ => bb28}}bb28={StorageDead(_71);StorageLive(_73);StorageLive(_74);_75 = core::ptr::addr_of!((*holder_key));_74 = _75 as *const u8;Call(_73 = core::intrinsics::volatile_load::<u8>(Move(_74)),ReturnTo(bb95),UnwindUnreachable())}bb29={StorageLive(_79);Call(_79 = <u32 as From<PumpError>>::from(E_CtoNewCreatorRequired),ReturnTo(bb96),UnwindUnreachable())}bb30={StorageLive(_81);StorageLive(_82);StorageLive(_83);_83 = anchor_lang::error::Source{filename:"programs/pump/src/creator/admin_cto.rs",line:306_u32};_82 = anchor_lang::error::ErrorOrigin::Source(Move(_83));StorageDead(_83);_81 = Some(Move(_82));StorageDead(_82);StorageLive(_84);_84 = None;_77 = anchor_lang::error::AnchorError{error_name:Move(_78),error_code_number:Move(_79),error_msg:Move(_80),error_origin:Move(_81),compared_values:Move(_84)};StorageDead(_84);StorageDead(_81);StorageDead(_80);StorageDead(_79);StorageDead(_78);Call(_76 = <anchor_lang::error::Error as From<anchor_lang::error::AnchorError>>::from(Move(_77)),ReturnTo(bb31),UnwindUnreachable())}bb31={StorageDead(_77);RET = Err(Move(_76));StorageDead(_76);StorageDead(_67);Goto(bb80)}bb32={StorageDead(_71);StorageLive(_85);StorageLive(_86);StorageLive(_87);StorageLive(_88);_88 = core::ptr::addr_of!(new);_87 = Move(_88) as *const u8;StorageDead(_88);_86 = Offset(_87,1_usize);StorageDead(_87);_85 = Move(_86) as *const Pubkey;StorageDead(_86);Call(_66 = core::ptr::read_unaligned::<anchor_lang::prelude::Pubkey>(Move(_85)),ReturnTo(bb33),UnwindUnreachable())}bb33={StorageDead(_85);StorageDead(_67);StorageLive(_89);StorageLive(_90);StorageLive(_237);Call(_237 = <[u8; 32] as Default>::default(),ReturnTo(bb97),UnwindUnreachable())}bb34={StorageDead(_90);StorageLive(_91);StorageLive(_92);StorageLive(_93);StorageLive(_94);Call(_94 = PumpError::name(R_CreatorShouldNotBeZero),ReturnTo(bb35),UnwindUnreachable())}bb35={StorageLive(_95);Call(_95 = <u32 as From<PumpError>>::from(E_CreatorShouldNotBeZero),ReturnTo(bb99),UnwindUnreachable())}bb36={StorageLive(_97);StorageLive(_98);StorageLive(_99);_99 = anchor_lang::error::Source{filename:"programs/pump/src/creator/admin_cto.rs",line:307_u32};_98 = anchor_lang::error::ErrorOrigin::Source(Move(_99));StorageDead(_99);_97 = Some(Move(_98));StorageDead(_98);StorageLive(_100);_100 = None;_93 = anchor_lang::error::AnchorError{error_name:Move(_94),error_code_number:Move(_95),error_msg:Move(_96),error_origin:Move(_97),compared_values:Move(_100)};StorageDead(_100);StorageDead(_97);StorageDead(_96);StorageDead(_95);StorageDead(_94);Call(_92 = <anchor_lang::error::Error as From<anchor_lang::error::AnchorError>>::from(Move(_93)),ReturnTo(bb37),UnwindUnreachable())}bb37={StorageDead(_93);StorageLive(_101);StorageLive(_102);_240 = core::ptr::addr_of_mut!(_102);_103 = _240 as *mut u8;StorageLive(_104);StorageLive(_105);StorageLive(_106);_106 = core::ptr::addr_of!(_66);_105 = Move(_106) as *const u8;StorageDead(_106);_104 = Offset(_105,8_usize);StorageDead(_105);StorageLive(_107);_107 = Offset(_103,8_usize);xd1 = _107 as *mut [u8;24];xs1 = _104 as *const [u8;24];(*xd1) = (*xs1);StorageDead(_107);StorageDead(_104);StorageLive(_108);StorageLive(_109);StorageLive(_110);StorageLive(_111);StorageLive(_112);_112 = core::ptr::addr_of!(new);_111 = Move(_112) as *const u8;StorageDead(_112);_110 = Offset(_111,1_usize);StorageDead(_111);_109 = Move(_110) as *const u64;StorageDead(_110);Call(_108 = core::ptr::read_unaligned::<u64>(Move(_109)),ReturnTo(bb100),UnwindUnreachable())}bb38={StorageDead(_101);StorageDead(_92);RET = Err(Move(_91));StorageDead(_91);StorageDead(_89);Goto(bb80)}bb39={StorageDead(_90);StorageDead(_89);StorageLive(_115);StorageLive(_116);StorageLive(_117);StorageLive(_118);StorageLive(_119);StorageLive(_120);StorageLive(_246);StorageLive(_245);x_245 = &_66;_245 = CastTransmute(Move(x_245));x_246 = &(*holder_key);_246 = CastTransmute(Move(x_246));Call(_120 = core::intrinsics::raw_eq::<[u8; 32]>(Move(_245),Move(_246)),ReturnTo(bb102),UnwindUnreachable())}bb40={StorageDead(_119);_117 = Move(_118) & 1_u8;StorageDead(_118);_116 = Move(_117) != 0_u8;StorageDead(_117);Call(_115 = expect_p(Move(_116),true,0.625f64),ReturnTo(bb41),UnwindUnreachable())}bb41={StorageDead(_116);match Move(_115) {false => bb42,_ => bb800}}bb42={StorageLive(_121);StorageLive(_122);StorageLive(_248);StorageLive(_247);x_247 = &_66;_247 = CastTransmute(Move(x_247));x_248 = &(*sharing);_248 = CastTransmute(Move(x_248));Call(_122 = core::intrinsics::raw_eq::<[u8; 32]>(Move(_247),Move(_248)),ReturnTo(bb103),UnwindUnreachable())}bb43={StorageDead(_122);match Move(_121) {false => bb48,_ => bb800}}bb44={StorageLive(_123);StorageLive(_124);_125 = core::ptr::addr_of!((*holder_key));_124 = _125 as *const u8;Call(_123 = core::intrinsics::volatile_load::<u8>(Move(_124)),ReturnTo(bb104),UnwindUnreachable())}bb45={StorageLive(_153);Call(_153 = <u32 as From<PumpError>>::from(E_InvalidCreator),ReturnTo(bb113),UnwindUnreachable())}bb46={StorageLive(_155);StorageLive(_156);StorageLive(_157);_157 = anchor_lang::error::Source{filename:"programs/pump/src/creator/admin_cto.rs",line:312_u32};_156 = anchor_lang::error::ErrorOrigin::Source(Move(_157));StorageDead(_157);_155 = Some(Move(_156));StorageDead(_156);StorageLive(_158);_158 = None;_151 = anchor_lang::error::AnchorError{error_name:Move(_152),error_code_number:Move(_153),error_msg:Move(_154),error_origin:Move(_155),compared_values:Move(_158)};StorageDead(_158);StorageDead(_155);StorageDead(_154);StorageDead(_153);StorageDead(_152);Call(_150 = <anchor_lang::error::Error as From<anchor_lang::error::AnchorError>>::from(Move(_151)),ReturnTo(bb47),UnwindUnreachable())}bb47={StorageDead(_151);RET = Err(Move(_150));StorageDead(_150);StorageDead(_121);StorageDead(_115);Goto(bb80)}bb48={StorageDead(_121);StorageDead(_115);StorageLive(_161);_249 = core::ptr::addr_of_mut!(_18);_161 = _249 as *mut u8;Call(_160 = lts(7_i64,Move(_161)),ReturnTo(bb49),UnwindUnreachable())}bb49={StorageDead(_161);StorageLive(_162);_250 = core::ptr::addr_of_mut!(_19);_162 = _250 as *mut u8;Call(_159 = lts(25_i64,Move(_162)),ReturnTo(bb50),UnwindUnreachable())}bb50={StorageDead(_162);StorageLive(_163);_164 = core::ptr::addr_of!(_66);_163 = _164 as *const u8;StorageLive(_165);_251 = core::ptr::addr_of_mut!(_18);_165 = _251 as *mut u8;xd2 = _165 as *mut [u8;7];xs2 = _163 as *const [u8;7];(*xd2) = (*xs2);StorageDead(_165);StorageDead(_163);StorageLive(_166);_258 = CastTransmute(_66);_166 = _258;StorageLive(_167);StorageLive(_168);StorageLive(_169);StorageLive(_170);_170 = &_166;xu3 = (Move(_170),32_usize);_169 = CastTransmute(Move(xu3));StorageDead(_170);StorageLive(_252);_252 = core::ptr::addr_of!((*_169));_168 = Move(_252) as *const u8;StorageDead(_252);StorageDead(_169);_167 = Offset(_168,7_usize);StorageDead(_168);StorageLive(_171);_253 = core::ptr::addr_of_mut!(_19);_171 = _253 as *mut u8;xd4 = _171 as *mut [u8;25];xs4 = _167 as *const [u8;25];(*xd4) = (*xs4);StorageDead(_171);StorageDead(_167);StorageDead(_166);StorageDead(_66);Goto(bb51)}bb51={StorageLive(_172);StorageLive(_173);_173 = _17;match Move(_173) {false => bb53,_ => bb52}}bb52={_172 = false;StorageDead(_173);_174 = Discriminant(fee);match Move(_174) {0 => bb78,1 => bb120,_ => bb54}}bb53={_172 = ((*st)).cashback;StorageDead(_173);_174 = Discriminant(fee);match Move(_174) {0 => bb78,1 => bb55,_ => bb54}}bb54={Unreachable()}bb55={_175 = Field::<u64>(Variant(fee,1),0);StorageLive(_176);_176 = ((*st)).quote_locked;match Move(_176) {false => bb60,_ => bb56}}bb56={StorageLive(_177);StorageLive(_178);StorageLive(_179);Call(_179 = PumpError::name(R_CreatorFeeNotConfigurableForQuote),ReturnTo(bb57),UnwindUnreachable())}bb57={StorageLive(_180);Call(_180 = <u32 as From<PumpError>>::from(E_CreatorFeeNotConfigurableForQuote),ReturnTo(bb114),UnwindUnreachable())}bb58={StorageLive(_182);StorageLive(_183);StorageLive(_184);_184 = anchor_lang::error::Source{filename:"programs/pump/src/creator/admin_cto.rs",line:326_u32};_183 = anchor_lang::error::ErrorOrigin::Source(Move(_184));StorageDead(_184);_182 = Some(Move(_183));StorageDead(_183);StorageLive(_185);_185 = None;_178 = anchor_lang::error::AnchorError{error_name:Move(_179),error_code_number:Move(_180),error_msg:Move(_181),error_origin:Move(_182),compared_values:Move(_185)};StorageDead(_185);StorageDead(_182);StorageDead(_181);StorageDead(_180);StorageDead(_179);Call(_177 = <anchor_lang::error::Error as From<anchor_lang::error::AnchorError>>::from(Move(_178)),ReturnTo(bb59),UnwindUnreachable())}bb59={StorageDead(_178);RET = Err(Move(_177));StorageDead(_177);StorageDead(_176);Goto(bb79)}bb60={StorageDead(_176);StorageLive(_186);_186 = _172;match Move(_186) {false => bb62,_ => bb61}}bb61={StorageLive(_187);StorageLive(_188);StorageLive(_189);Call(_189 = PumpError::name(R_CreatorFeeNotAllowedForCashbackCoin),ReturnTo(bb63),UnwindUnreachable())}bb62={StorageDead(_186);StorageLive(_196);StorageLive(_197);_198 = core::ptr::addr_of!((*holder_key));_197 = _198 as *const u8;Goto(bb115)}bb63={StorageLive(_190);Call(_190 = <u32 as From<PumpError>>::from(E_CreatorFeeNotAllowedForCashbackCoin),ReturnTo(bb116),UnwindUnreachable())}bb64={StorageLive(_192);StorageLive(_193);StorageLive(_194);_194 = anchor_lang::error::Source{filename:"programs/pump/src/creator/admin_cto.rs",line:330_u32};_193 = anchor_lang::error::ErrorOrigin::Source(Move(_194));StorageDead(_194);_192 = Some(Move(_193));StorageDead(_193);StorageLive(_195);_195 = None;_188 = anchor_lang::error::AnchorError{error_name:Move(_189),error_code_number:Move(_190),error_msg:Move(_191),error_origin:Move(_192),compared_values:Move(_195)};StorageDead(_195);StorageDead(_192);StorageDead(_191);StorageDead(_190);StorageDead(_189);Call(_187 = <anchor_lang::error::Error as From<anchor_lang::error::AnchorError>>::from(Move(_188)),ReturnTo(bb65),UnwindUnreachable())}bb65={StorageDead(_188);RET = Err(Move(_187));StorageDead(_187);StorageDead(_186);Goto(bb79)}bb66={StorageLive(_200);StorageLive(_201);StorageLive(_202);Call(_202 = PumpError::name(R_CreatorFeeNotConfigurable),ReturnTo(bb67),UnwindUnreachable())}bb67={StorageLive(_203);Call(_203 = <u32 as From<PumpError>>::from(E_CreatorFeeNotConfigurable),ReturnTo(bb117),UnwindUnreachable())}bb68={StorageLive(_205);StorageLive(_206);StorageLive(_207);_207 = anchor_lang::error::Source{filename:"programs/pump/src/creator/admin_cto.rs",line:334_u32};_206 = anchor_lang::error::ErrorOrigin::Source(Move(_207));StorageDead(_207);_205 = Some(Move(_206));StorageDead(_206);StorageLive(_208);_208 = None;_201 = anchor_lang::error::AnchorError{error_name:Move(_202),error_code_number:Move(_203),error_msg:Move(_204),error_origin:Move(_205),compared_values:Move(_208)};StorageDead(_208);StorageDead(_205);StorageDead(_204);StorageDead(_203);StorageDead(_202);Call(_200 = <anchor_lang::error::Error as From<anchor_lang::error::AnchorError>>::from(Move(_201)),ReturnTo(bb69),UnwindUnreachable())}bb69={StorageDead(_201);RET = Err(Move(_200));StorageDead(_200);StorageDead(_199);Goto(bb79)}bb70={StorageDead(_199);match Move(_175) {0 => bb74,_ => bb71}}bb71={StorageLive(_209);StorageLive(_210);_210 = ((*st)).max_fee;_209 = _175 > Move(_210);match Move(_209) {false => bb73,_ => bb72}}bb72={StorageDead(_210);Goto(bb74)}bb73={StorageDead(_210);StorageDead(_209);StorageLive(_220);StorageLive(_221);_222 = core::ptr::addr_of!((*holder_key));_221 = _222 as *const u8;Call(_220 = core::intrinsics::volatile_load::<u8>(Move(_221)),ReturnTo(bb118),UnwindUnreachable())}bb74={StorageLive(_211);StorageLive(_212);StorageLive(_213);Call(_213 = PumpError::name(R_CreatorFeeBpsOutOfRange),ReturnTo(bb75),UnwindUnreachable())}bb75={StorageLive(_214);Call(_214 = <u32 as From<PumpError>>::from(E_CreatorFeeBpsOutOfRange),ReturnTo(bb119),UnwindUnreachable())}bb76={StorageLive(_216);StorageLive(_217);StorageLive(_218);_218 = anchor_lang::error::Source{filename:"programs/pump/src/creator/admin_cto.rs",line:338_u32};_217 = anchor_lang::error::ErrorOrigin::Source(Move(_218));StorageDead(_218);_216 = Some(Move(_217));StorageDead(_217);StorageLive(_219);_219 = None;_212 = anchor_lang::error::AnchorError{error_name:Move(_213),error_code_number:Move(_214),error_msg:Move(_215),error_origin:Move(_216),compared_values:Move(_219)};StorageDead(_219);StorageDead(_216);StorageDead(_215);StorageDead(_214);StorageDead(_213);Call(_211 = <anchor_lang::error::Error as From<anchor_lang::error::AnchorError>>::from(Move(_212)),ReturnTo(bb77),UnwindUnreachable())}bb77={StorageDead(_212);RET = Err(Move(_211));StorageDead(_211);StorageDead(_209);Goto(bb79)}bb78={StorageLive(_223);StorageLive(_224);_254 = core::ptr::addr_of_mut!(_224);_225 = _254 as *mut u8;StorageLive(_226);_255 = core::ptr::addr_of!(_18);_226 = _255 as *const u8;xd5 = _225 as *mut [u8;7];xs5 = _226 as *const [u8;7];(*xd5) = (*xs5);StorageDead(_226);StorageLive(_227);_256 = core::ptr::addr_of!(_19);_227 = _256 as *const u8;StorageLive(_228);_228 = Offset(_225,7_usize);xd6 = _228 as *mut [u8;25];xs6 = _227 as *const [u8;25];(*xd6) = (*xs6);StorageDead(_228);StorageDead(_227);StorageLive(_229);_229 = _224;_260 = CastTransmute(Move(_229));StorageDead(_229);_223 = CastTransmute(_260);StorageDead(_224);RET = Ok(Move(_223));StorageDead(_223);StorageDead(_172);StorageDead(_19);StorageDead(_18);StorageDead(_17);Goto(bb84)}bb79={StorageDead(_172);Goto(bb83)}bb80={StorageDead(_66);Goto(bb82)}bb81={StorageDead(_20);Goto(bb82)}bb82={Goto(bb83)}bb83={StorageDead(_19);StorageDead(_18);StorageDead(_17);Goto(bb84)}bb84={Return()}bb85={StorageLive(_12);Call(_12 = <PumpError as ToString>::to_string(R_CtoNotAllowedForMayhemCoin),ReturnTo(bb3),UnwindUnreachable())}bb86={StorageDead(_230);StorageLive(_18);StorageLive(_19);StorageLive(_20);StorageLive(_21);_21 = ((*st)).holder_reward;_20 = Move(_21) as u8;StorageDead(_21);match _20 {1 => bb7,_ => bb6}}bb87={_17 = false;Goto(bb86)}bb88={StorageLive(_231);_231 = Field::<bool>(Variant(hopt,1),0);_17 = Move(_231);StorageDead(_231);Goto(bb86)}bb89={StorageLive(_28);Call(_28 = <PumpError as ToString>::to_string(R_HolderRewardCreatorImmutable),ReturnTo(bb11),UnwindUnreachable())}bb90={StorageDead(_34);StorageDead(_33);RET = Err(_24);StorageDead(_22);Goto(bb81)}bb91={StorageLive(_43);Call(_43 = <PumpError as ToString>::to_string(R_HolderRewardDisabled),ReturnTo(bb18),UnwindUnreachable())}bb92={StorageDead(_232);StorageLive(_57);_257 = CastTransmute((*holder_key));_57 = _257;StorageLive(_59);StorageLive(_60);_60 = &_57;xu7 = (Move(_60),32_usize);_59 = CastTransmute(Move(xu7));StorageDead(_60);_233 = core::ptr::addr_of!((*_59));_58 = _233 as *const u8;StorageDead(_59);StorageLive(_61);_234 = core::ptr::addr_of_mut!(_18);_61 = _234 as *mut u8;xd8 = _61 as *mut [u8;7];xs8 = _58 as *const [u8;7];(*xd8) = (*xs8);StorageDead(_61);StorageLive(_62);_62 = Offset(_58,7_usize);StorageLive(_63);_235 = core::ptr::addr_of_mut!(_19);_63 = _235 as *mut u8;xd9 = _63 as *mut [u8;25];xs9 = _62 as *const [u8;25];(*xd9) = (*xs9);StorageDead(_63);StorageDead(_62);StorageDead(_57);Goto(bb51)}bb93={StorageDead(_232);StorageLive(_48);StorageLive(_49);StorageLive(_50);Call(_50 = PumpError::name(R_CtoNewCreatorNotAllowed),ReturnTo(bb23),UnwindUnreachable())}bb94={StorageLive(_52);Call(_52 = <PumpError as ToString>::to_string(R_CtoNewCreatorNotAllowed),ReturnTo(bb24),UnwindUnreachable())}bb95={StorageDead(_74);StorageDead(_73);StorageLive(_76);StorageLive(_77);StorageLive(_78);Call(_78 = PumpError::name(R_CtoNewCreatorRequired),ReturnTo(bb29),UnwindUnreachable())}bb96={StorageLive(_80);Call(_80 = <PumpError as ToString>::to_string(R_CtoNewCreatorRequired),ReturnTo(bb30),UnwindUnreachable())}bb97={_90 = CastTransmute(Move(_237));StorageDead(_237);StorageLive(_239);StorageLive(_238);x_238 = &_66;_238 = CastTransmute(Move(x_238));x_239 = &_90;_239 = CastTransmute(Move(x_239));Call(_89 = core::intrinsics::raw_eq::<[u8; 32]>(Move(_238),Move(_239)),ReturnTo(bb98),UnwindUnreachable())}bb98={StorageDead(_238);StorageDead(_239);match Move(_89) {false => bb39,_ => bb34}}bb99={StorageLive(_96);Call(_96 = <PumpError as ToString>::to_string(R_CreatorShouldNotBeZero),ReturnTo(bb36),UnwindUnreachable())}bb100={StorageDead(_109);StorageLive(_241);_241 = Move(_108);StorageLive(_243);StorageLive(_242);_243 = core::ptr::addr_of!(_241);_242 = _243 as *const u8;xd10 = _103 as *mut [u8;8];xs10 = _242 as *const [u8;8];(*xd10) = (*xs10);StorageDead(_242);StorageDead(_243);StorageDead(_241);StorageDead(_108);StorageLive(_113);_113 = _102;_259 = CastTransmute(Move(_113));StorageDead(_113);StorageDead(_102);StorageLive(_114);StorageLive(_244);Call(_244 = <[u8; 32] as Default>::default(),ReturnTo(bb101),UnwindUnreachable())}bb101={_114 = CastTransmute(Move(_244));StorageDead(_244);_101 = (_259,Move(_114));StorageDead(_114);Call(_91 = anchor_lang::error::Error::with_pubkeys(Move(_92),Move(_101)),ReturnTo(bb38),UnwindUnreachable())}bb102={StorageDead(_245);StorageDead(_246);_119 = Move(_120) as u8;StorageDead(_120);Call(_118 = pt8(4_u32,Move(_119)),ReturnTo(bb40),UnwindUnreachable())}bb103={StorageDead(_247);StorageDead(_248);Call(_121 = expect(Move(_122),false),ReturnTo(bb43),UnwindUnreachable())}bb104={StorageDead(_124);StorageDead(_123);StorageLive(_126);StorageLive(_127);_128 = core::ptr::addr_of!((*holder_key));_127 = _128 as *const u8;Call(_126 = core::intrinsics::volatile_load::<u8>(Move(_127)),ReturnTo(bb105),UnwindUnreachable())}bb105={StorageDead(_127);StorageDead(_126);StorageLive(_129);StorageLive(_130);_131 = core::ptr::addr_of!((*holder_key));_130 = _131 as *const u8;Call(_129 = core::intrinsics::volatile_load::<u8>(Move(_130)),ReturnTo(bb106),UnwindUnreachable())}bb106={StorageDead(_130);StorageDead(_129);StorageLive(_132);StorageLive(_133);_134 = core::ptr::addr_of!((*holder_key));_133 = _134 as *const u8;Call(_132 = core::intrinsics::volatile_load::<u8>(Move(_133)),ReturnTo(bb107),UnwindUnreachable())}bb107={StorageDead(_133);StorageDead(_132);StorageLive(_135);StorageLive(_136);_137 = core::ptr::addr_of!((*holder_key));_136 = _137 as *const u8;Call(_135 = core::intrinsics::volatile_load::<u8>(Move(_136)),ReturnTo(bb108),UnwindUnreachable())}bb108={StorageDead(_136);StorageDead(_135);StorageLive(_138);StorageLive(_139);_140 = core::ptr::addr_of!((*holder_key));_139 = _140 as *const u8;Call(_138 = core::intrinsics::volatile_load::<u8>(Move(_139)),ReturnTo(bb109),UnwindUnreachable())}bb109={StorageDead(_139);StorageDead(_138);StorageLive(_141);StorageLive(_142);_143 = core::ptr::addr_of!((*holder_key));_142 = _143 as *const u8;Call(_141 = core::intrinsics::volatile_load::<u8>(Move(_142)),ReturnTo(bb110),UnwindUnreachable())}bb110={StorageDead(_142);StorageDead(_141);StorageLive(_144);StorageLive(_145);_146 = core::ptr::addr_of!((*holder_key));_145 = _146 as *const u8;Call(_144 = core::intrinsics::volatile_load::<u8>(Move(_145)),ReturnTo(bb111),UnwindUnreachable())}bb111={StorageDead(_145);StorageDead(_144);StorageLive(_147);StorageLive(_148);_149 = core::ptr::addr_of!((*holder_key));_148 = _149 as *const u8;Call(_147 = core::intrinsics::volatile_load::<u8>(Move(_148)),ReturnTo(bb112),UnwindUnreachable())}bb112={StorageDead(_148);StorageDead(_147);StorageLive(_150);StorageLive(_151);StorageLive(_152);Call(_152 = PumpError::name(R_InvalidCreator),ReturnTo(bb45),UnwindUnreachable())}bb113={StorageLive(_154);Call(_154 = <PumpError as ToString>::to_string(R_InvalidCreator),ReturnTo(bb46),UnwindUnreachable())}bb114={StorageLive(_181);Call(_181 = <PumpError as ToString>::to_string(R_CreatorFeeNotConfigurableForQuote),ReturnTo(bb58),UnwindUnreachable())}bb115={StorageDead(_197);StorageDead(_196);StorageLive(_199);_199 = ((*st)).fee_configurable;match Move(_199) {false => bb66,_ => bb70}}bb116={StorageLive(_191);Call(_191 = <PumpError as ToString>::to_string(R_CreatorFeeNotAllowedForCashbackCoin),ReturnTo(bb64),UnwindUnreachable())}bb117={StorageLive(_204);Call(_204 = <PumpError as ToString>::to_string(R_CreatorFeeNotConfigurable),ReturnTo(bb68),UnwindUnreachable())}bb118={StorageDead(_221);StorageDead(_220);Goto(bb78)}bb119={StorageLive(_215);Call(_215 = <PumpError as ToString>::to_string(R_CreatorFeeBpsOutOfRange),ReturnTo(bb76),UnwindUnreachable())}bb120={_175 = Field::<u64>(Variant(fee,1),0);StorageLive(_176);_176 = ((*st)).quote_locked;match Move(_176) {false => bb121,_ => bb56}}bb121={StorageDead(_176);StorageLive(_186);Goto(bb62)}bb860={_860 = core::ptr::addr_of!((*holder_key));_861 = _860 as *const u8;Call(_862 = core::intrinsics::volatile_load::<u8>(_861),ReturnTo(bb861),UnwindUnreachable())}bb861={Call(_863 = core::intrinsics::volatile_load::<u8>(_861),ReturnTo(bb862),UnwindUnreachable())}bb862={_864 = _862 != _863;Call(_865 = expect_p(_864,true,0.5f64),ReturnTo(bb863),UnwindUnreachable())}bb863={match Move(_865) {false => bb32,_ => bb864}}bb864={_872 = core::ptr::addr_of!((*holder_key));_871 = _872 as *const u8;Call(_870 = core::intrinsics::volatile_load::<u8>(_871),ReturnTo(bb964),UnwindUnreachable())}bb800={_815 = core::ptr::addr_of!((*holder_key));_814 = _815 as *const u8;Call(_810 = core::intrinsics::volatile_load::<u8>(_814),ReturnTo(bb801),UnwindUnreachable())}bb801={Call(_811 = core::intrinsics::volatile_load::<u8>(_814),ReturnTo(bb802),UnwindUnreachable())}bb802={_812 = _810 != _811;match Move(_812) {true => bb820,_ => bb111}}bb820={_872 = core::ptr::addr_of!((*holder_key));_871 = _872 as *const u8;Call(_870 = core::intrinsics::volatile_load::<u8>(_871),ReturnTo(bb920),UnwindUnreachable())}bb964={Call(_866 = trapu(),ReturnTo(bb54),UnwindUnreachable())}bb920={Call(_813 = trapu(),ReturnTo(bb54),UnwindUnreachable())}}}























































pub fn execute(ctx:Context<AdminCto>,holder:Option<bool>,fee:Option<u64>,new:Option<Pubkey>)->Result<()>{ let a=&ctx.accounts;let mint=a.mint.key();let shared={let cr=a.bonding_curve.creator;cr==a.sharing_config.key()}&&unsafe{&*(ptp(23,&**a as *const AdminCto as *const u8) as *const AdminCto)}/*shim: passthrough on the accounts pointer of the shared owner test*/.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();let mut hkx=core::mem::MaybeUninit::<[u64;9]>::uninit();let hkb=hkx.as_mut_ptr().cast::<u64>();/*shim: retain the raw holder-key allocation base before creating its shared key reference*//*shim: holder_key in a 72 B slot whose 40 B tail keeps hk's frame region (orig -0x680..-0x658 target/new pieces)*/let holder_key:&Pubkey=unsafe{hkb.cast::<Pubkey>().write(Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID).0);&*hkb.cast::<Pubkey>()}/*shim: PDA result is a temp (orig -0x2d0 out-param)*/;let quote_locked={let q=a.bonding_curve.quote_mint;q==Pubkey::default()||q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(&q)};let (_holder,cashback,target,sharing_update,collect_old,skip)={ let mut skm=core::mem::MaybeUninit::<Pubkey>::uninit();let mut hk2=core::mem::MaybeUninit::<[u64;4]>::uninit();/*shim: frame stand-in for the original hk2 copy (32 B slot live across validate: FI47 -0x518)*/let creator=a.bonding_curve.creator;let mut st=CtoState{fee_configurable:a.global.creator_fee_configurable,creator:{unsafe{lts(32,skm.as_mut_ptr() as *mut u8)}/*shim: lifetime start of the sk slot between the fee_configurable load and the creator copy (creator stores ascending)*/;a.bonding_curve.creator},max_fee:a.global.max_configurable_creator_fee_bps,mayhem:false,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin,quote_locked,holder_enabled:a.global.is_holder_reward_enabled};let hopt=holder;let holder=hopt==Some(true);let cashback=!holder&&st.cashback;let args=&(new,);let sk:&Pubkey=unsafe{skm.as_mut_ptr().write((&*(ptp(25,&**a as *const AdminCto as *const u8) as *const AdminCto))/*shim: passthrough reload of the sharing_config account ref for the sk copy*/.sharing_config.key());&*skm.as_ptr()};st.mayhem=unsafe{&*(ptp(24,&**a as *const AdminCto as *const u8) as *const AdminCto)}/*shim: passthrough on the accounts pointer of the mayhem read (curve reloaded after the sk copy, original 0x598 window)*/.bonding_curve.is_mayhem_mode;let mut target=validate(&st,hopt,fee,new,holder_key,sk)?;let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if unsafe{expect_p(shared,true,0.625)}/*shim: shared split weight (llc block placement)*/{if unsafe{expect_p(hopt.unwrap_or(false),true,0.625)}/*shim: holder test weight (the and-1 test has no zero heuristic; keeps the original 12:20 block frequencies)*/{sharing_update=Some(None);(false,false)}else{target=creator;sharing_update=Some(args.0);(false,true)}}else{(!st.holder_reward&&{let mut c=false;unsafe{core::ptr::write_volatile(&mut c,st.creator==Pubkey::default())};/*shim: creator==default compare kept in memory*/!c},true)};unsafe{vann(hk2.as_mut_ptr() as *const u8,b"\0".as_ptr(),b"\0".as_ptr(),0,core::ptr::null())}/*shim: var.annotation keeps the hk2 stand-in through SROA (no instruction)*/;(holder,cashback,target,sharing_update,collect_old,skip)};let (target,sharing_update,cashback)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback))?;let mut target=target; crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.admin_set_creator_authority)?;






































































 require!(a.bonding_curve.creator_fee==0,PumpError::CreatorFeesNotSwept);




// layout-pad(141): aligns the next Source site with the original line












































































































































 if collect_old{wallet(&ctx,hkb)?;}fn wallet(ctx:&Context<AdminCto>,hkb:*mut u64)->Result<()>{let a=&ctx.accounts;if a.current_creator.executable{msg!("Creator is a program; fees left in the vaults");}else if a.current_creator.owner!=&anchor_lang::system_program::ID{msg!("Creator is not a system-owned wallet; fees left in the vaults");}else{if !a.current_creator.is_writable{return Err(error!(PumpError::CtoCreatorAccountNotWritable));}if token_frozen(a.current_creator_quote_token_account.as_ref())?{msg!("Creator quote token account is frozen; fees left in the vaults");}else{
  let collection_native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;
  let coin_empty=a.coin_creator_vault_ata.data_is_empty();let coin_present=!coin_empty;unsafe{let p=hkb.add(8) as *mut bool;core::ptr::write_volatile(p,coin_empty);core::ptr::write_volatile(p,coin_empty);core::ptr::write_volatile(p,coin_empty);core::ptr::write_volatile(p,coin_empty);core::ptr::write_volatile(p,coin_empty);core::ptr::write_volatile(p,coin_empty);}/*shim: six volatile coin_empty stores to the unused holder-key slot tail raise its spill weight above the wallet buffer pointer's, so the buffer waits for %0's split and the wallet accounts piece takes r7 as in the original*/
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
































































 unsafe{core::ptr::write_volatile(hkb.add(6).cast::<*const AdminCto>(),&**a as *const AdminCto)};/*shim: accounts pointer kept in a stack slot for the sharing clone run, stored at the sweep gate (the displacement of jumps across it)*/swept=(!skip).then(||sweep(&ctx,holder_key)).transpose()?.unwrap_or(0);fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{let a=&ctx.accounts;let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;
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


















 unsafe{core::ptr::write_volatile(hkb.add(7),cashback as u64)}/*shim: cashback flag parked in a stack slot across the sweep and the sharing clone run*/;let signer_seeds:&[&[&[u8]]]=&[&[b"pool-authority",mint.as_ref(),&[ctx.bumps.pool_authority]]];
 if let Some(val)=sharing_update{{


  let asl:*mut *const AdminCto=unsafe{hkb.add(6)}.cast::<*const AdminCto>();/*shim: accounts pointer kept in a stack slot for the sharing clone run*/let a0:&AdminCto=&**a;let (a1,a2,a3,a4,a5,a6,a7):(&AdminCto,&AdminCto,&AdminCto,&AdminCto,&AdminCto,&AdminCto,&AdminCto);crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer(aiv!(x,a0.pump_fees.as_ref(),x.lamports.clone(),x.data.clone(),a1,asl),crate::pump_fees::cpi::accounts::AdminCtoSharingConfig{pool_authority:aiv!(x,a1.pool_authority.as_ref(),unsafe{rcw::<3,_>(&x.lamports)},x.data.clone(),a2,asl),authority:aiv!(x,a2.admin_set_creator_authority.as_ref(),x.lamports.clone(),unsafe{rcw::<40,_>(&x.data)},a3,asl),global:aiv!(x,a3.global.as_ref().as_ref(),unsafe{rcw::<40,_>(&x.lamports)},x.data.clone(),a4,asl),mint:aiv!(x,a4.mint.as_ref(),unsafe{rcw::<40,_>(&x.lamports)},x.data.clone(),a5,asl),sharing_config:aiv!(x,a5.sharing_config.as_ref(),x.lamports.clone(),x.data.clone(),a6,asl),event_authority:aiv!(x,a6.pump_fees_event_authority.as_ref(),unsafe{rcw::<20,_>(&x.lamports)},x.data.clone(),a7,asl),program:aiw!(x,a7.pump_fees.as_ref(),unsafe{rcw::<14,_>(&x.lamports)},unsafe{rcw::<3,_>(&x.data)})},signer_seeds),val)?;

 }}
 let (old_creator,old_fee)={
  let curve=&mut ctx.accounts.bonding_curve;let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;
  curve.creator=target;
  curve.is_holder_reward=(unsafe{pt8(9,*(&holder as *const Option<bool> as *const u8))}/*shim: passthrough on the holder byte of the curve store (own and-1, no CSE with the validate test)*/&1)!=0;
  unsafe{core::ptr::addr_of_mut!(curve.is_cashback_coin).cast::<u8>().write(core::ptr::read_volatile(hkb.add(7).cast::<u8>()))};/*shim: cashback flag byte stored back unmasked*/
  if unsafe{pt1(30,*(&fee as *const Option<u64> as *const u64)!=0)}/*shim: passthrough on the raw fee tag test (keeps the jne tag,0 form)*/{curve.creator_fee_bps=unsafe{fee.unwrap_unchecked()};}
  curve.can_edit_creator_fee=false;
 (old_creator,old_fee)};
 let a=&ctx.accounts;
 let cvk=unsafe{core::ptr::read_volatile(&a.bonding_curve as *const Box<Account<BondingCurve>> as *const *const u8)}/*shim: curve pointer held in a register from the pool gate to the event (its range steers the tail colours as the original swept range does)*/;let pool_updated=a.pool.owner==&AMM && !unsafe{core::ptr::read_volatile(core::mem::transmute::<&&mut AdminCto,*const &AdminCto>(a))}/*shim: reload the accounts pointer for the pool data_is_empty test*/.pool.data_is_empty();let pargs=(target,a.bonding_curve.is_holder_reward,fee);
 if pool_updated{


  crate::pump_amm::cpi::admin_cto_pool(CpiContext::new_with_signer(a.pump_amm.to_account_info(),crate::pump_amm::cpi::accounts::AdminCtoPool{payer:a.admin_set_creator_authority.to_account_info(),global_config:a.amm_global_config.to_account_info(),pool:a.pool.to_account_info(),pool_authority:a.pool_authority.to_account_info(),system_program:a.system_program.to_account_info(),event_authority:a.pump_amm_event_authority.to_account_info(),program:a.pump_amm.to_account_info()},signer_seeds),pargs.0,pargs.1,pargs.2)?;
 }else{msg!("No canonical pump pool for this mint; curve only");}
 let e=AdminCtoEvent{timestamp:Clock::get().map_err(|e|{unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read in the Clock::get error path (the displacement of jumps across it)*/;e})?.unix_timestamp,authority:{unsafe{core::ptr::read_volatile(cvk.add(165))}/*shim: last use of the held curve pointer*/;a.admin_set_creator_authority.key()},mint,bonding_curve:a.bonding_curve.key(),old_creator,new_creator:a.bonding_curve.creator,is_holder_reward:a.bonding_curve.is_holder_reward,is_cashback_coin:a.bonding_curve.is_cashback_coin,old_creator_fee_bps:old_fee,new_creator_fee_bps:a.bonding_curve.creator_fee_bps,sharing_config_reset:sharing_update.is_some(),swept_to_holder_vault:swept,pool_updated};emit!(e);{let authority_info=ctx.accounts.event_authority.to_account_info();let authority_bump=ctx.bumps.event_authority;let disc=anchor_lang::event::EVENT_IX_TAG_LE;let inner_data=anchor_lang::Event::data(&e);let ix_data:Vec<u8>=disc.into_iter().map(|b|*b).chain(inner_data.into_iter()).collect();let ix=anchor_lang::solana_program::instruction::Instruction::new_with_bytes(crate::ID,&ix_data,vec![anchor_lang::solana_program::instruction::AccountMeta::new_readonly(*authority_info.key,true)]);unsafe{let p=hkb.add(8) as *mut u8;core::ptr::write_volatile(p,authority_bump);core::ptr::write_volatile(p,authority_bump);}/*shim: two volatile authority_bump stores to the unused holder-key slot tail raise the byte's spill weight above the authority_info pointer's, so the byte holds r6 and the pointer spills to -0x8d8 as in the original (emit_cpi! expanded in place)*/anchor_lang::solana_program::program::invoke_signed(&ix,&[authority_info],&[&[b"__event_authority",&[authority_bump]]]).map_err(|e|{unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: move one sweep-gate byte read to the self-CPI error path to restore the original event-tail jump spans*/;anchor_lang::error::Error::from(e)})?;}Ok(())
}

fn token_frozen(a:&AccountInfo)->Result<bool>{if a.data_is_empty(){return Ok(false);}let d=a.try_borrow_data()?;let t=anchor_spl::token_interface::TokenAccount::try_deserialize(&mut &d[..])?;Ok(t.is_frozen())}

fn token_raw_amount(a:&AccountInfo)->Result<u64>{if a.data_is_empty(){return Ok(0);}let d=a.try_borrow_data()?;let t=anchor_spl::token_interface::TokenAccount::try_deserialize(&mut &d[..])?;Ok(t.amount)}
