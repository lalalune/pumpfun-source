#![feature(link_llvm_intrinsics,custom_mir,core_intrinsics)]
#![recursion_limit="512"]
extern crate anchor_lang;
extern crate pump_recovered;
use anchor_lang::prelude::*;
use pump_recovered::{PumpError,trade_types::BondingCurve};
use core::mem::{size_of,align_of};
extern "C" {
#[link_name="llvm.expect.i1"]fn expect(b:bool,v:bool)->bool;
#[link_name="llvm.expect.with.probability.i1"]fn expect_p(b:bool,v:bool,p:f64)->bool;
#[link_name="llvm.trap"]fn trapu();
#[link_name="llvm.bpf.passthrough.i8.i8"]fn pt8(n:u32,v:u8)->u8;
#[link_name="llvm.lifetime.start.p0"]fn lts(n:i64,p:*mut u8);
#[link_name="llvm.lifetime.end.p0"]fn lte(n:i64,p:*mut u8);
#[link_name="llvm.var.annotation.p0.p0"]fn vann(p:*const u8,s:*const u8,f:*const u8,l:u32,a:*const u8);
}
struct CtoState{creator:Pubkey,max_fee:u64,mayhem:bool,holder_reward:bool,cashback:bool,quote_locked:bool,holder_enabled:bool,fee_configurable:bool}
#[no_mangle]pub fn main34_validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);
 if st.mayhem{return Err(error!(PumpError::CtoNotAllowedForMayhemCoin));}
// Reconstructed positions of the same deployed validations.



 let mut target_head=core::mem::MaybeUninit::<[u8;7]>::uninit();let mut target_tail=core::mem::MaybeUninit::<[u8;25]>::uninit();/*shim: separate 7-byte head and 25-byte tail permit a whole-head lifetime end without ending the tail*/if match st.holder_reward as u8{1=>{if !(hopt==Some(true)){return Err({let e=error!(PumpError::HolderRewardCreatorImmutable);unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;e});}true}_=>if unsafe{expect_p(holder,true,0.49)}/*shim: !hr holder test 49:51 (MBP places the 306 test after the !hr holder test)*/{






  if !st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}true}else{false}}

 {if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}{let b=holder_key.to_bytes();let p=b.as_ptr();unsafe{core::ptr::copy_nonoverlapping(p,target_head.as_mut_ptr().cast::<u8>(),7);core::ptr::copy_nonoverlapping(p.add(7),target_tail.as_mut_ptr().cast::<u8>(),25);}}}else{unsafe{lte(7,target_head.as_mut_ptr().cast::<u8>())}/*shim: only the seven-byte head is dead through the non-holder checks; the tail keeps its existing lifetime*/;







  let t=if unsafe{expect_p(new.is_none(),true,0.75)}/*shim: 306 None probability*/{return Err(error!(PumpError::CtoNewCreatorRequired));}else{unsafe{core::ptr::read_unaligned((&new as *const Option<Pubkey> as *const u8).add(1) as *const Pubkey)}/*shim: 306 payload read, no tag re-test*/};
  if t==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((t,Pubkey::default())));}




  if unsafe{expect_p((pt8(4,(t==*sharing) as u8)&1)!=0,true,0.625)}/*shim: 312 t==sharing memcmp equal-likely 20:12 (llc spill colour; was the libcall 12:20); passthrough on the compare byte*/||unsafe{expect(t==*holder_key,false)}/*shim: 312 holder_key compare unlikely 1:2000 (llc placement)*/{unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;return Err(error!(PumpError::InvalidCreator));}unsafe{lts(7,target_head.as_mut_ptr().cast::<u8>());lts(25,target_tail.as_mut_ptr().cast::<u8>())}/*shim: start the parts before storing the checked key; copy head before materializing the tail source to preserve SROA order*/;{unsafe{core::ptr::copy_nonoverlapping(&t as *const Pubkey as *const u8,target_head.as_mut_ptr().cast::<u8>(),7);}let b=t.to_bytes();unsafe{core::ptr::copy_nonoverlapping(b.as_ptr().add(7),target_tail.as_mut_ptr().cast::<u8>(),25);}}}
// layout-pad(13): aligns the next Source site with the original line
 let cashback=if holder{false}else{st.cashback};











 match fee{Some(f)=>{if st.quote_locked{return Err(error!(PumpError::CreatorFeeNotConfigurableForQuote));}
// layout-pad(3): aligns the next Source site with the original line


  if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}



  unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder before the fee_configurable test*/;if !st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}



  if f==0||f>st.max_fee{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};}None=>{}}
 Ok({let mut b=core::mem::MaybeUninit::<[u8;32]>::uninit();unsafe{let p=b.as_mut_ptr().cast::<u8>();core::ptr::copy_nonoverlapping(target_head.as_ptr().cast::<u8>(),p,7);core::ptr::copy_nonoverlapping(target_tail.as_ptr().cast::<u8>(),p.add(7),25);Pubkey::new_from_array(b.assume_init())}})/*shim: reconstruct the initialized key from the disjoint head and tail arrays*/}
const PSOME:&Option<bool>=&Some(true);const E_CreatorFeeBpsOutOfRange:PumpError=PumpError::CreatorFeeBpsOutOfRange;const E_CreatorFeeNotAllowedForCashbackCoin:PumpError=PumpError::CreatorFeeNotAllowedForCashbackCoin;const E_CreatorFeeNotConfigurable:PumpError=PumpError::CreatorFeeNotConfigurable;const E_CreatorFeeNotConfigurableForQuote:PumpError=PumpError::CreatorFeeNotConfigurableForQuote;const E_CreatorShouldNotBeZero:PumpError=PumpError::CreatorShouldNotBeZero;const E_CtoNewCreatorNotAllowed:PumpError=PumpError::CtoNewCreatorNotAllowed;const E_CtoNewCreatorRequired:PumpError=PumpError::CtoNewCreatorRequired;const E_CtoNotAllowedForMayhemCoin:PumpError=PumpError::CtoNotAllowedForMayhemCoin;const E_HolderRewardCreatorImmutable:PumpError=PumpError::HolderRewardCreatorImmutable;const E_HolderRewardDisabled:PumpError=PumpError::HolderRewardDisabled;const E_InvalidCreator:PumpError=PumpError::InvalidCreator;const R_CreatorFeeBpsOutOfRange:&PumpError=&PumpError::CreatorFeeBpsOutOfRange;const R_CreatorFeeNotAllowedForCashbackCoin:&PumpError=&PumpError::CreatorFeeNotAllowedForCashbackCoin;const R_CreatorFeeNotConfigurable:&PumpError=&PumpError::CreatorFeeNotConfigurable;const R_CreatorFeeNotConfigurableForQuote:&PumpError=&PumpError::CreatorFeeNotConfigurableForQuote;const R_CreatorShouldNotBeZero:&PumpError=&PumpError::CreatorShouldNotBeZero;const R_CtoNewCreatorNotAllowed:&PumpError=&PumpError::CtoNewCreatorNotAllowed;const R_CtoNewCreatorRequired:&PumpError=&PumpError::CtoNewCreatorRequired;const R_CtoNotAllowedForMayhemCoin:&PumpError=&PumpError::CtoNotAllowedForMayhemCoin;const R_HolderRewardCreatorImmutable:&PumpError=&PumpError::HolderRewardCreatorImmutable;const R_HolderRewardDisabled:&PumpError=&PumpError::HolderRewardDisabled;const R_InvalidCreator:&PumpError=&PumpError::InvalidCreator;#[no_mangle]#[custom_mir(dialect="runtime",phase="optimized")]/*shim: custom MIR body (exact CFG and locals): 306 and holder tests 50:50; a never-true volatile compare with a 50:50 llvm.trap edge heads the t path (its head keeps the frequency block placement needs, the rest runs at the frequency the RA saw before); holder-first 312 compares; the 312 head ends the MBP chain with a never-true volatile compare and llvm.trap, so the 312 rest is placed after 326; a volatile byte load in front of each trap keeps it from merging with the Rc overflow trap*/pub fn custom_mir_validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{use core::intrinsics::mir::*;mir!{let _7: bool;let _8: &std::option::Option<bool>;let _9: bool;let _10: anchor_lang::error::Error;let _11: anchor_lang::error::AnchorError;let _12: std::string::String;let _13: u32;let _14: std::string::String;let _15: std::option::Option<anchor_lang::error::ErrorOrigin>;let _16: anchor_lang::error::ErrorOrigin;let _17: anchor_lang::error::Source;let _18: std::option::Option<anchor_lang::error::ComparedValues>;let _19: std::mem::MaybeUninit<Pubkey>;let _20: u8;let _21: bool;let _22: bool;let _23: &std::option::Option<bool>;let _24: anchor_lang::error::Error;let _25: anchor_lang::error::AnchorError;let _26: std::string::String;let _27: u32;let _28: std::string::String;let _29: std::option::Option<anchor_lang::error::ErrorOrigin>;let _30: anchor_lang::error::ErrorOrigin;let _31: anchor_lang::error::Source;let _32: std::option::Option<anchor_lang::error::ComparedValues>;let _33: u8;let _34: *const u8;let _35: *const Pubkey;let _36: bool;let _37: bool;let _38: anchor_lang::error::Error;let _39: anchor_lang::error::AnchorError;let _40: std::string::String;let _41: u32;let _42: std::string::String;let _43: std::option::Option<anchor_lang::error::ErrorOrigin>;let _44: anchor_lang::error::ErrorOrigin;let _45: anchor_lang::error::Source;let _46: std::option::Option<anchor_lang::error::ComparedValues>;let _47: anchor_lang::error::Error;let _48: anchor_lang::error::AnchorError;let _49: std::string::String;let _50: u32;let _51: std::string::String;let _52: std::option::Option<anchor_lang::error::ErrorOrigin>;let _53: anchor_lang::error::ErrorOrigin;let _54: anchor_lang::error::Source;let _55: std::option::Option<anchor_lang::error::ComparedValues>;let _56: Pubkey;let _57: ();let _58: *mut u8;let _59: Pubkey;let _60: bool;let _61: bool;let _62: anchor_lang::error::Error;let _63: anchor_lang::error::AnchorError;let _64: std::string::String;let _65: u32;let _66: std::string::String;let _67: std::option::Option<anchor_lang::error::ErrorOrigin>;let _68: anchor_lang::error::ErrorOrigin;let _69: anchor_lang::error::Source;let _70: std::option::Option<anchor_lang::error::ComparedValues>;let _71: *const Pubkey;let _72: *const u8;let _73: *const u8;let _74: *const std::option::Option<Pubkey>;let _75: bool;let _76: Pubkey;let _77: anchor_lang::error::Error;let _78: anchor_lang::error::Error;let _79: anchor_lang::error::AnchorError;let _80: std::string::String;let _81: u32;let _82: std::string::String;let _83: std::option::Option<anchor_lang::error::ErrorOrigin>;let _84: anchor_lang::error::ErrorOrigin;let _85: anchor_lang::error::Source;let _86: std::option::Option<anchor_lang::error::ComparedValues>;let _87: (Pubkey, Pubkey);let _88: Pubkey;let _89: Pubkey;let _90: bool;let _91: bool;let _92: u8;let _93: u8;let _94: u8;let _95: bool;let _96: bool;let _97: bool;let _98: u8;let _99: *const u8;let _100: *const Pubkey;let _101: u8;let _102: *const u8;let _103: *const Pubkey;let _104: u8;let _105: *const u8;let _106: *const Pubkey;let _107: u8;let _108: *const u8;let _109: *const Pubkey;let _110: u8;let _111: *const u8;let _112: *const Pubkey;let _113: u8;let _114: *const u8;let _115: *const Pubkey;let _116: u8;let _117: *const u8;let _118: *const Pubkey;let _119: u8;let _120: *const u8;let _121: *const Pubkey;let _122: anchor_lang::error::Error;let _123: anchor_lang::error::AnchorError;let _124: std::string::String;let _125: u32;let _126: std::string::String;let _127: std::option::Option<anchor_lang::error::ErrorOrigin>;let _128: anchor_lang::error::ErrorOrigin;let _129: anchor_lang::error::Source;let _130: std::option::Option<anchor_lang::error::ComparedValues>;let _131: ();let _132: *mut u8;let _133: Pubkey;let _134: bool;let _135: isize;let _136: u64;let _137: bool;let _138: anchor_lang::error::Error;let _139: anchor_lang::error::AnchorError;let _140: std::string::String;let _141: u32;let _142: std::string::String;let _143: std::option::Option<anchor_lang::error::ErrorOrigin>;let _144: anchor_lang::error::ErrorOrigin;let _145: anchor_lang::error::Source;let _146: std::option::Option<anchor_lang::error::ComparedValues>;let _147: bool;let _148: anchor_lang::error::Error;let _149: anchor_lang::error::AnchorError;let _150: std::string::String;let _151: u32;let _152: std::string::String;let _153: std::option::Option<anchor_lang::error::ErrorOrigin>;let _154: anchor_lang::error::ErrorOrigin;let _155: anchor_lang::error::Source;let _156: std::option::Option<anchor_lang::error::ComparedValues>;let _157: u8;let _158: *const u8;let _159: *const Pubkey;let _160: bool;let _161: anchor_lang::error::Error;let _162: anchor_lang::error::AnchorError;let _163: std::string::String;let _164: u32;let _165: std::string::String;let _166: std::option::Option<anchor_lang::error::ErrorOrigin>;let _167: anchor_lang::error::ErrorOrigin;let _168: anchor_lang::error::Source;let _169: std::option::Option<anchor_lang::error::ComparedValues>;let _170: bool;let _171: u64;let _172: anchor_lang::error::Error;let _173: anchor_lang::error::AnchorError;let _174: std::string::String;let _175: u32;let _176: std::string::String;let _177: std::option::Option<anchor_lang::error::ErrorOrigin>;let _178: anchor_lang::error::ErrorOrigin;let _179: anchor_lang::error::Source;let _180: std::option::Option<anchor_lang::error::ComparedValues>;let _181: u8;let _182: *const u8;let _183: *const Pubkey;let _184: std::mem::MaybeUninit<Pubkey>;let _185: isize;let _186: std::mem::MaybeUninit<Pubkey>;let _187: std::mem::ManuallyDrop<Pubkey>;let _188: *mut std::mem::MaybeUninit<Pubkey>;let _189: bool;let _190: isize;let _191: [u8; 32];let _192: &[u8; 32];let _193: &[u8; 32];let _194: [u8; 32];let _195: &[u8; 32];let _196: &[u8; 32];let _197: &[u8; 32];let _198: &[u8; 32];let _199: *mut std::mem::MaybeUninit<Pubkey>;let _200: std::mem::MaybeUninit<Pubkey>;let _201: std::mem::ManuallyDrop<Pubkey>;let _202: Pubkey;let _810: u8;let _811: u8;let _812: bool;let _813: ();let _814: *const u8;let _815: *const Pubkey;let _832: u8;let _860: *const Pubkey;let _861: *const u8;let _862: u8;let _863: u8;let _864: bool;let _865: bool;let _866: ();let _870: u8;let _871: *const u8;let _872: *const Pubkey;let x_195: &Pubkey;let x_196: &Pubkey;let x_197: &Pubkey;let x_198: &Pubkey;let x_192: &Pubkey;let x_193: &Pubkey;{StorageLive(_8);_8 = &hopt;Call(_7 = <Option<bool> as PartialEq>::eq(Move(_8),PSOME),ReturnTo(bb1),UnwindUnreachable())}bb1={StorageDead(_8);StorageLive(_9);_9 = ((*st)).mayhem;match Move(_9) {false => bb6,_ => bb2}}bb2={StorageLive(_10);StorageLive(_11);StorageLive(_12);Call(_12 = PumpError::name(R_CtoNotAllowedForMayhemCoin),ReturnTo(bb3),UnwindUnreachable())}bb3={StorageLive(_13);Call(_13 = <u32 as From<PumpError>>::from(E_CtoNotAllowedForMayhemCoin),ReturnTo(bb85),UnwindUnreachable())}bb4={StorageLive(_15);StorageLive(_16);StorageLive(_17);_17 = anchor_lang::error::Source{filename:"programs/pump/src/creator/admin_cto.rs",line:284_u32};_16 = anchor_lang::error::ErrorOrigin::Source(Move(_17));StorageDead(_17);_15 = Some(Move(_16));StorageDead(_16);StorageLive(_18);_18 = None;_11 = anchor_lang::error::AnchorError{error_name:Move(_12),error_code_number:Move(_13),error_msg:Move(_14),error_origin:Move(_15),compared_values:Move(_18)};StorageDead(_18);StorageDead(_15);StorageDead(_14);StorageDead(_13);StorageDead(_12);Call(_10 = <anchor_lang::error::Error as From<anchor_lang::error::AnchorError>>::from(Move(_11)),ReturnTo(bb5),UnwindUnreachable())}bb5={StorageDead(_11);RET = Err(Move(_10));StorageDead(_10);StorageDead(_9);Goto(bb84)}bb6={StorageDead(_9);StorageLive(_19);StorageLive(_20);StorageLive(_21);_21 = ((*st)).holder_reward;_20 = Move(_21) as u8;StorageDead(_21);match _20 {1 => bb8,_ => bb7}}bb7={StorageLive(_36);Call(_36 = expect_p(_7,true,0.5f64),ReturnTo(bb15),UnwindUnreachable())}bb8={StorageLive(_22);StorageLive(_23);_23 = &hopt;Call(_22 = <Option<bool> as PartialEq>::eq(Move(_23),PSOME),ReturnTo(bb9),UnwindUnreachable())}bb9={match Move(_22) {false => bb11,_ => bb10}}bb10={StorageDead(_23);StorageDead(_22);Goto(bb23)}bb11={StorageDead(_23);StorageLive(_25);StorageLive(_26);Call(_26 = PumpError::name(R_HolderRewardCreatorImmutable),ReturnTo(bb12),UnwindUnreachable())}bb12={StorageLive(_27);Call(_27 = <u32 as From<PumpError>>::from(E_HolderRewardCreatorImmutable),ReturnTo(bb86),UnwindUnreachable())}bb13={StorageLive(_29);StorageLive(_30);StorageLive(_31);_31 = anchor_lang::error::Source{filename:"programs/pump/src/creator/admin_cto.rs",line:289_u32};_30 = anchor_lang::error::ErrorOrigin::Source(Move(_31));StorageDead(_31);_29 = Some(Move(_30));StorageDead(_30);StorageLive(_32);_32 = None;_25 = anchor_lang::error::AnchorError{error_name:Move(_26),error_code_number:Move(_27),error_msg:Move(_28),error_origin:Move(_29),compared_values:Move(_32)};StorageDead(_32);StorageDead(_29);StorageDead(_28);StorageDead(_27);StorageDead(_26);Call(_24 = <anchor_lang::error::Error as From<anchor_lang::error::AnchorError>>::from(Move(_25)),ReturnTo(bb14),UnwindUnreachable())}bb14={StorageDead(_25);StorageLive(_33);StorageLive(_34);_35 = core::ptr::addr_of!((*holder_key));_34 = _35 as *const u8;Call(_33 = core::intrinsics::volatile_load::<u8>(Move(_34)),ReturnTo(bb87),UnwindUnreachable())}bb15={match Move(_36) {false => bb22,_ => bb16}}bb16={StorageLive(_37);_37 = ((*st)).holder_enabled;match Move(_37) {false => bb17,_ => bb21}}bb17={StorageLive(_38);StorageLive(_39);StorageLive(_40);Call(_40 = PumpError::name(R_HolderRewardDisabled),ReturnTo(bb18),UnwindUnreachable())}bb18={StorageLive(_41);Call(_41 = <u32 as From<PumpError>>::from(E_HolderRewardDisabled),ReturnTo(bb88),UnwindUnreachable())}bb19={StorageLive(_43);StorageLive(_44);StorageLive(_45);_45 = anchor_lang::error::Source{filename:"programs/pump/src/creator/admin_cto.rs",line:296_u32};_44 = anchor_lang::error::ErrorOrigin::Source(Move(_45));StorageDead(_45);_43 = Some(Move(_44));StorageDead(_44);StorageLive(_46);_46 = None;_39 = anchor_lang::error::AnchorError{error_name:Move(_40),error_code_number:Move(_41),error_msg:Move(_42),error_origin:Move(_43),compared_values:Move(_46)};StorageDead(_46);StorageDead(_43);StorageDead(_42);StorageDead(_41);StorageDead(_40);Call(_38 = <anchor_lang::error::Error as From<anchor_lang::error::AnchorError>>::from(Move(_39)),ReturnTo(bb20),UnwindUnreachable())}bb20={StorageDead(_39);RET = Err(Move(_38));StorageDead(_38);StorageDead(_37);StorageDead(_36);Goto(bb81)}bb21={StorageDead(_37);StorageDead(_36);Goto(bb23)}bb22={StorageDead(_36);StorageDead(_20);StorageLive(_58);_188 = core::ptr::addr_of_mut!(_19);_58 = _188 as *mut u8;Call(_57 = lte(32_i64,Move(_58)),ReturnTo(bb27),UnwindUnreachable())}bb23={StorageDead(_20);StorageLive(_185);_185 = Discriminant(new);match Move(_185) {1 => bb90,0 => bb89,_ => bb54}}bb24={StorageLive(_50);Call(_50 = <u32 as From<PumpError>>::from(E_CtoNewCreatorNotAllowed),ReturnTo(bb91),UnwindUnreachable())}bb25={StorageLive(_52);StorageLive(_53);StorageLive(_54);_54 = anchor_lang::error::Source{filename:"programs/pump/src/creator/admin_cto.rs",line:298_u32};_53 = anchor_lang::error::ErrorOrigin::Source(Move(_54));StorageDead(_54);_52 = Some(Move(_53));StorageDead(_53);StorageLive(_55);_55 = None;_48 = anchor_lang::error::AnchorError{error_name:Move(_49),error_code_number:Move(_50),error_msg:Move(_51),error_origin:Move(_52),compared_values:Move(_55)};StorageDead(_55);StorageDead(_52);StorageDead(_51);StorageDead(_50);StorageDead(_49);Call(_47 = <anchor_lang::error::Error as From<anchor_lang::error::AnchorError>>::from(Move(_48)),ReturnTo(bb26),UnwindUnreachable())}bb26={StorageDead(_48);RET = Err(Move(_47));StorageDead(_47);Goto(bb82)}bb27={StorageDead(_58);StorageLive(_59);StorageLive(_60);StorageLive(_61);StorageLive(_189);StorageLive(_190);_190 = Discriminant(new);match Move(_190) {1 => bb94,0 => bb93,_ => bb54}}bb28={StorageDead(_61);match Move(_60) {false => bb860,_ => bb29}}bb29={StorageLive(_62);StorageLive(_63);StorageLive(_64);Call(_64 = PumpError::name(R_CtoNewCreatorRequired),ReturnTo(bb30),UnwindUnreachable())}bb30={StorageLive(_65);Call(_65 = <u32 as From<PumpError>>::from(E_CtoNewCreatorRequired),ReturnTo(bb95),UnwindUnreachable())}bb31={StorageLive(_67);StorageLive(_68);StorageLive(_69);_69 = anchor_lang::error::Source{filename:"programs/pump/src/creator/admin_cto.rs",line:306_u32};_68 = anchor_lang::error::ErrorOrigin::Source(Move(_69));StorageDead(_69);_67 = Some(Move(_68));StorageDead(_68);StorageLive(_70);_70 = None;_63 = anchor_lang::error::AnchorError{error_name:Move(_64),error_code_number:Move(_65),error_msg:Move(_66),error_origin:Move(_67),compared_values:Move(_70)};StorageDead(_70);StorageDead(_67);StorageDead(_66);StorageDead(_65);StorageDead(_64);Call(_62 = <anchor_lang::error::Error as From<anchor_lang::error::AnchorError>>::from(Move(_63)),ReturnTo(bb32),UnwindUnreachable())}bb32={StorageDead(_63);RET = Err(Move(_62));StorageDead(_62);StorageDead(_60);Goto(bb80)}bb33={StorageLive(_71);StorageLive(_72);StorageLive(_73);StorageLive(_74);_74 = core::ptr::addr_of!(new);_73 = Move(_74) as *const u8;StorageDead(_74);_72 = Offset(_73,1_usize);StorageDead(_73);_71 = Move(_72) as *const Pubkey;StorageDead(_72);Call(_59 = core::ptr::read_unaligned::<anchor_lang::prelude::Pubkey>(Move(_71)),ReturnTo(bb34),UnwindUnreachable())}bb34={StorageDead(_71);StorageDead(_60);StorageLive(_75);StorageLive(_76);StorageLive(_191);Call(_191 = <[u8; 32] as Default>::default(),ReturnTo(bb96),UnwindUnreachable())}bb35={StorageDead(_76);StorageLive(_77);StorageLive(_78);StorageLive(_79);StorageLive(_80);Call(_80 = PumpError::name(R_CreatorShouldNotBeZero),ReturnTo(bb36),UnwindUnreachable())}bb36={StorageLive(_81);Call(_81 = <u32 as From<PumpError>>::from(E_CreatorShouldNotBeZero),ReturnTo(bb98),UnwindUnreachable())}bb37={StorageLive(_83);StorageLive(_84);StorageLive(_85);_85 = anchor_lang::error::Source{filename:"programs/pump/src/creator/admin_cto.rs",line:307_u32};_84 = anchor_lang::error::ErrorOrigin::Source(Move(_85));StorageDead(_85);_83 = Some(Move(_84));StorageDead(_84);StorageLive(_86);_86 = None;_79 = anchor_lang::error::AnchorError{error_name:Move(_80),error_code_number:Move(_81),error_msg:Move(_82),error_origin:Move(_83),compared_values:Move(_86)};StorageDead(_86);StorageDead(_83);StorageDead(_82);StorageDead(_81);StorageDead(_80);Call(_78 = <anchor_lang::error::Error as From<anchor_lang::error::AnchorError>>::from(Move(_79)),ReturnTo(bb38),UnwindUnreachable())}bb38={StorageDead(_79);StorageLive(_87);StorageLive(_88);_88 = _59;StorageLive(_89);StorageLive(_194);Call(_194 = <[u8; 32] as Default>::default(),ReturnTo(bb99),UnwindUnreachable())}bb39={StorageDead(_87);StorageDead(_78);RET = Err(Move(_77));StorageDead(_77);StorageDead(_75);Goto(bb80)}bb40={StorageDead(_76);StorageDead(_75);StorageLive(_90);StorageLive(_91);StorageLive(_92);StorageLive(_93);StorageLive(_94);StorageLive(_95);StorageLive(_196);StorageLive(_195);x_195 = &_59;_195 = CastTransmute(Move(x_195));x_196 = &(*holder_key);_196 = CastTransmute(Move(x_196));Call(_95 = core::intrinsics::raw_eq::<[u8; 32]>(Move(_195),Move(_196)),ReturnTo(bb100),UnwindUnreachable())}bb41={StorageDead(_94);_92 = Move(_93) & 1_u8;StorageDead(_93);_91 = Move(_92) != 0_u8;StorageDead(_92);Call(_90 = expect_p(Move(_91),true,0.625f64),ReturnTo(bb42),UnwindUnreachable())}bb42={StorageDead(_91);match Move(_90) {false => bb43,_ => bb800}}bb43={StorageLive(_96);StorageLive(_97);StorageLive(_198);StorageLive(_197);x_197 = &_59;_197 = CastTransmute(Move(x_197));x_198 = &(*sharing);_198 = CastTransmute(Move(x_198));Call(_97 = core::intrinsics::raw_eq::<[u8; 32]>(Move(_197),Move(_198)),ReturnTo(bb101),UnwindUnreachable())}bb44={StorageDead(_97);match Move(_96) {false => bb49,_ => bb800}}bb45={StorageLive(_98);StorageLive(_99);_100 = core::ptr::addr_of!((*holder_key));_99 = _100 as *const u8;Call(_98 = core::intrinsics::volatile_load::<u8>(Move(_99)),ReturnTo(bb102),UnwindUnreachable())}bb46={StorageLive(_125);Call(_125 = <u32 as From<PumpError>>::from(E_InvalidCreator),ReturnTo(bb110),UnwindUnreachable())}bb47={StorageLive(_127);StorageLive(_128);StorageLive(_129);_129 = anchor_lang::error::Source{filename:"programs/pump/src/creator/admin_cto.rs",line:312_u32};_128 = anchor_lang::error::ErrorOrigin::Source(Move(_129));StorageDead(_129);_127 = Some(Move(_128));StorageDead(_128);StorageLive(_130);_130 = None;_123 = anchor_lang::error::AnchorError{error_name:Move(_124),error_code_number:Move(_125),error_msg:Move(_126),error_origin:Move(_127),compared_values:Move(_130)};StorageDead(_130);StorageDead(_127);StorageDead(_126);StorageDead(_125);StorageDead(_124);Call(_122 = <anchor_lang::error::Error as From<anchor_lang::error::AnchorError>>::from(Move(_123)),ReturnTo(bb48),UnwindUnreachable())}bb48={StorageDead(_123);RET = Err(Move(_122));StorageDead(_122);StorageDead(_96);StorageDead(_90);Goto(bb80)}bb49={StorageDead(_96);StorageDead(_90);StorageLive(_132);_199 = core::ptr::addr_of_mut!(_19);_132 = _199 as *mut u8;Call(_131 = lts(32_i64,Move(_132)),ReturnTo(bb50),UnwindUnreachable())}bb50={StorageDead(_132);StorageLive(_133);_133 = _59;StorageLive(_200);StorageLive(_201);_201 = CastTransmute(_133);_200 = CastTransmute(Move(_201));StorageDead(_201);_19 = Move(_200);StorageDead(_200);StorageDead(_133);StorageDead(_59);Goto(bb51)}bb51={StorageLive(_134);match _7 {false => bb53,_ => bb52}}bb52={_134 = false;_135 = Discriminant(fee);match Move(_135) {0 => bb78,1 => bb117,_ => bb54}}bb53={_134 = ((*st)).cashback;_135 = Discriminant(fee);match Move(_135) {0 => bb78,1 => bb55,_ => bb54}}bb54={Unreachable()}bb55={_136 = Field::<u64>(Variant(fee,1),0);StorageLive(_137);_137 = ((*st)).quote_locked;match Move(_137) {false => bb60,_ => bb56}}bb56={StorageLive(_138);StorageLive(_139);StorageLive(_140);Call(_140 = PumpError::name(R_CreatorFeeNotConfigurableForQuote),ReturnTo(bb57),UnwindUnreachable())}bb57={StorageLive(_141);Call(_141 = <u32 as From<PumpError>>::from(E_CreatorFeeNotConfigurableForQuote),ReturnTo(bb111),UnwindUnreachable())}bb58={StorageLive(_143);StorageLive(_144);StorageLive(_145);_145 = anchor_lang::error::Source{filename:"programs/pump/src/creator/admin_cto.rs",line:326_u32};_144 = anchor_lang::error::ErrorOrigin::Source(Move(_145));StorageDead(_145);_143 = Some(Move(_144));StorageDead(_144);StorageLive(_146);_146 = None;_139 = anchor_lang::error::AnchorError{error_name:Move(_140),error_code_number:Move(_141),error_msg:Move(_142),error_origin:Move(_143),compared_values:Move(_146)};StorageDead(_146);StorageDead(_143);StorageDead(_142);StorageDead(_141);StorageDead(_140);Call(_138 = <anchor_lang::error::Error as From<anchor_lang::error::AnchorError>>::from(Move(_139)),ReturnTo(bb59),UnwindUnreachable())}bb59={StorageDead(_139);RET = Err(Move(_138));StorageDead(_138);StorageDead(_137);Goto(bb79)}bb60={StorageDead(_137);StorageLive(_147);_147 = _134;match Move(_147) {false => bb62,_ => bb61}}bb61={StorageLive(_148);StorageLive(_149);StorageLive(_150);Call(_150 = PumpError::name(R_CreatorFeeNotAllowedForCashbackCoin),ReturnTo(bb63),UnwindUnreachable())}bb62={StorageDead(_147);StorageLive(_157);StorageLive(_158);_159 = core::ptr::addr_of!((*holder_key));_158 = _159 as *const u8;Goto(bb112)}bb63={StorageLive(_151);Call(_151 = <u32 as From<PumpError>>::from(E_CreatorFeeNotAllowedForCashbackCoin),ReturnTo(bb113),UnwindUnreachable())}bb64={StorageLive(_153);StorageLive(_154);StorageLive(_155);_155 = anchor_lang::error::Source{filename:"programs/pump/src/creator/admin_cto.rs",line:330_u32};_154 = anchor_lang::error::ErrorOrigin::Source(Move(_155));StorageDead(_155);_153 = Some(Move(_154));StorageDead(_154);StorageLive(_156);_156 = None;_149 = anchor_lang::error::AnchorError{error_name:Move(_150),error_code_number:Move(_151),error_msg:Move(_152),error_origin:Move(_153),compared_values:Move(_156)};StorageDead(_156);StorageDead(_153);StorageDead(_152);StorageDead(_151);StorageDead(_150);Call(_148 = <anchor_lang::error::Error as From<anchor_lang::error::AnchorError>>::from(Move(_149)),ReturnTo(bb65),UnwindUnreachable())}bb65={StorageDead(_149);RET = Err(Move(_148));StorageDead(_148);StorageDead(_147);Goto(bb79)}bb66={StorageLive(_161);StorageLive(_162);StorageLive(_163);Call(_163 = PumpError::name(R_CreatorFeeNotConfigurable),ReturnTo(bb67),UnwindUnreachable())}bb67={StorageLive(_164);Call(_164 = <u32 as From<PumpError>>::from(E_CreatorFeeNotConfigurable),ReturnTo(bb114),UnwindUnreachable())}bb68={StorageLive(_166);StorageLive(_167);StorageLive(_168);_168 = anchor_lang::error::Source{filename:"programs/pump/src/creator/admin_cto.rs",line:334_u32};_167 = anchor_lang::error::ErrorOrigin::Source(Move(_168));StorageDead(_168);_166 = Some(Move(_167));StorageDead(_167);StorageLive(_169);_169 = None;_162 = anchor_lang::error::AnchorError{error_name:Move(_163),error_code_number:Move(_164),error_msg:Move(_165),error_origin:Move(_166),compared_values:Move(_169)};StorageDead(_169);StorageDead(_166);StorageDead(_165);StorageDead(_164);StorageDead(_163);Call(_161 = <anchor_lang::error::Error as From<anchor_lang::error::AnchorError>>::from(Move(_162)),ReturnTo(bb69),UnwindUnreachable())}bb69={StorageDead(_162);RET = Err(Move(_161));StorageDead(_161);StorageDead(_160);Goto(bb79)}bb70={StorageDead(_160);match Move(_136) {0 => bb74,_ => bb71}}bb71={StorageLive(_170);StorageLive(_171);_171 = ((*st)).max_fee;_170 = _136 > Move(_171);match Move(_170) {false => bb73,_ => bb72}}bb72={StorageDead(_171);Goto(bb74)}bb73={StorageDead(_171);StorageDead(_170);StorageLive(_181);StorageLive(_182);_183 = core::ptr::addr_of!((*holder_key));_182 = _183 as *const u8;Call(_181 = core::intrinsics::volatile_load::<u8>(Move(_182)),ReturnTo(bb115),UnwindUnreachable())}bb74={StorageLive(_172);StorageLive(_173);StorageLive(_174);Call(_174 = PumpError::name(R_CreatorFeeBpsOutOfRange),ReturnTo(bb75),UnwindUnreachable())}bb75={StorageLive(_175);Call(_175 = <u32 as From<PumpError>>::from(E_CreatorFeeBpsOutOfRange),ReturnTo(bb116),UnwindUnreachable())}bb76={StorageLive(_177);StorageLive(_178);StorageLive(_179);_179 = anchor_lang::error::Source{filename:"programs/pump/src/creator/admin_cto.rs",line:338_u32};_178 = anchor_lang::error::ErrorOrigin::Source(Move(_179));StorageDead(_179);_177 = Some(Move(_178));StorageDead(_178);StorageLive(_180);_180 = None;_173 = anchor_lang::error::AnchorError{error_name:Move(_174),error_code_number:Move(_175),error_msg:Move(_176),error_origin:Move(_177),compared_values:Move(_180)};StorageDead(_180);StorageDead(_177);StorageDead(_176);StorageDead(_175);StorageDead(_174);Call(_172 = <anchor_lang::error::Error as From<anchor_lang::error::AnchorError>>::from(Move(_173)),ReturnTo(bb77),UnwindUnreachable())}bb77={StorageDead(_173);RET = Err(Move(_172));StorageDead(_172);StorageDead(_170);Goto(bb79)}bb78={StorageLive(_184);_184 = _19;_202 = CastTransmute(Move(_184));StorageDead(_184);RET = Ok(_202);StorageDead(_134);StorageDead(_19);Goto(bb84)}bb79={StorageDead(_134);Goto(bb83)}bb80={StorageDead(_59);Goto(bb82)}bb81={StorageDead(_20);Goto(bb82)}bb82={Goto(bb83)}bb83={StorageDead(_19);Goto(bb84)}bb84={Return()}bb85={StorageLive(_14);Call(_14 = <PumpError as ToString>::to_string(R_CtoNotAllowedForMayhemCoin),ReturnTo(bb4),UnwindUnreachable())}bb86={StorageLive(_28);Call(_28 = <PumpError as ToString>::to_string(R_HolderRewardCreatorImmutable),ReturnTo(bb13),UnwindUnreachable())}bb87={StorageDead(_34);StorageDead(_33);RET = Err(_24);StorageDead(_22);Goto(bb81)}bb88={StorageLive(_42);Call(_42 = <PumpError as ToString>::to_string(R_HolderRewardDisabled),ReturnTo(bb19),UnwindUnreachable())}bb89={StorageDead(_185);StorageLive(_56);_56 = (*holder_key);StorageLive(_186);StorageLive(_187);_187 = CastTransmute(_56);_186 = CastTransmute(Move(_187));StorageDead(_187);_19 = Move(_186);StorageDead(_186);StorageDead(_56);Goto(bb51)}bb90={StorageDead(_185);StorageLive(_47);StorageLive(_48);StorageLive(_49);Call(_49 = PumpError::name(R_CtoNewCreatorNotAllowed),ReturnTo(bb24),UnwindUnreachable())}bb91={StorageLive(_51);Call(_51 = <PumpError as ToString>::to_string(R_CtoNewCreatorNotAllowed),ReturnTo(bb25),UnwindUnreachable())}bb92={StorageDead(_190);_61 = !Move(_189);StorageDead(_189);Call(_60 = expect_p(Move(_61),true,0.5f64),ReturnTo(bb28),UnwindUnreachable())}bb93={_189 = false;Goto(bb92)}bb94={_189 = true;Goto(bb92)}bb95={StorageLive(_66);Call(_66 = <PumpError as ToString>::to_string(R_CtoNewCreatorRequired),ReturnTo(bb31),UnwindUnreachable())}bb96={_76 = CastTransmute(Move(_191));StorageDead(_191);StorageLive(_193);StorageLive(_192);x_192 = &_59;_192 = CastTransmute(Move(x_192));x_193 = &_76;_193 = CastTransmute(Move(x_193));Call(_75 = core::intrinsics::raw_eq::<[u8; 32]>(Move(_192),Move(_193)),ReturnTo(bb97),UnwindUnreachable())}bb97={StorageDead(_192);StorageDead(_193);match Move(_75) {false => bb40,_ => bb35}}bb98={StorageLive(_82);Call(_82 = <PumpError as ToString>::to_string(R_CreatorShouldNotBeZero),ReturnTo(bb37),UnwindUnreachable())}bb99={_89 = CastTransmute(Move(_194));StorageDead(_194);_87 = (Move(_88),Move(_89));StorageDead(_89);StorageDead(_88);Call(_77 = anchor_lang::error::Error::with_pubkeys(Move(_78),Move(_87)),ReturnTo(bb39),UnwindUnreachable())}bb100={StorageDead(_195);StorageDead(_196);_94 = Move(_95) as u8;StorageDead(_95);Call(_93 = pt8(4_u32,Move(_94)),ReturnTo(bb41),UnwindUnreachable())}bb101={StorageDead(_197);StorageDead(_198);Call(_96 = expect(Move(_97),false),ReturnTo(bb44),UnwindUnreachable())}bb102={StorageDead(_99);StorageDead(_98);StorageLive(_101);StorageLive(_102);_103 = core::ptr::addr_of!((*holder_key));_102 = _103 as *const u8;Call(_101 = core::intrinsics::volatile_load::<u8>(Move(_102)),ReturnTo(bb103),UnwindUnreachable())}bb103={StorageDead(_102);StorageDead(_101);StorageLive(_104);StorageLive(_105);_106 = core::ptr::addr_of!((*holder_key));_105 = _106 as *const u8;Call(_104 = core::intrinsics::volatile_load::<u8>(Move(_105)),ReturnTo(bb104),UnwindUnreachable())}bb104={StorageDead(_105);StorageDead(_104);StorageLive(_107);StorageLive(_108);_109 = core::ptr::addr_of!((*holder_key));_108 = _109 as *const u8;Call(_107 = core::intrinsics::volatile_load::<u8>(Move(_108)),ReturnTo(bb105),UnwindUnreachable())}bb105={StorageDead(_108);StorageDead(_107);StorageLive(_110);StorageLive(_111);_112 = core::ptr::addr_of!((*holder_key));_111 = _112 as *const u8;Call(_110 = core::intrinsics::volatile_load::<u8>(Move(_111)),ReturnTo(bb106),UnwindUnreachable())}bb106={StorageDead(_111);StorageDead(_110);StorageLive(_113);StorageLive(_114);_115 = core::ptr::addr_of!((*holder_key));_114 = _115 as *const u8;Call(_113 = core::intrinsics::volatile_load::<u8>(Move(_114)),ReturnTo(bb107),UnwindUnreachable())}bb107={StorageDead(_114);StorageDead(_113);StorageLive(_116);StorageLive(_117);_118 = core::ptr::addr_of!((*holder_key));_117 = _118 as *const u8;Call(_116 = core::intrinsics::volatile_load::<u8>(Move(_117)),ReturnTo(bb108),UnwindUnreachable())}bb108={StorageDead(_117);StorageDead(_116);StorageLive(_119);StorageLive(_120);_121 = core::ptr::addr_of!((*holder_key));_120 = _121 as *const u8;Call(_119 = core::intrinsics::volatile_load::<u8>(Move(_120)),ReturnTo(bb109),UnwindUnreachable())}bb109={StorageDead(_120);StorageDead(_119);StorageLive(_122);StorageLive(_123);StorageLive(_124);Call(_124 = PumpError::name(R_InvalidCreator),ReturnTo(bb46),UnwindUnreachable())}bb110={StorageLive(_126);Call(_126 = <PumpError as ToString>::to_string(R_InvalidCreator),ReturnTo(bb47),UnwindUnreachable())}bb111={StorageLive(_142);Call(_142 = <PumpError as ToString>::to_string(R_CreatorFeeNotConfigurableForQuote),ReturnTo(bb58),UnwindUnreachable())}bb112={StorageDead(_158);StorageDead(_157);StorageLive(_160);_160 = ((*st)).fee_configurable;match Move(_160) {false => bb66,_ => bb70}}bb113={StorageLive(_152);Call(_152 = <PumpError as ToString>::to_string(R_CreatorFeeNotAllowedForCashbackCoin),ReturnTo(bb64),UnwindUnreachable())}bb114={StorageLive(_165);Call(_165 = <PumpError as ToString>::to_string(R_CreatorFeeNotConfigurable),ReturnTo(bb68),UnwindUnreachable())}bb115={StorageDead(_182);StorageDead(_181);Goto(bb78)}bb116={StorageLive(_176);Call(_176 = <PumpError as ToString>::to_string(R_CreatorFeeBpsOutOfRange),ReturnTo(bb76),UnwindUnreachable())}bb117={_136 = Field::<u64>(Variant(fee,1),0);StorageLive(_137);_137 = ((*st)).quote_locked;match Move(_137) {false => bb118,_ => bb56}}bb118={StorageDead(_137);StorageLive(_147);Goto(bb62)}bb860={_860 = core::ptr::addr_of!((*holder_key));_861 = _860 as *const u8;Call(_862 = core::intrinsics::volatile_load::<u8>(_861),ReturnTo(bb861),UnwindUnreachable())}bb861={Call(_863 = core::intrinsics::volatile_load::<u8>(_861),ReturnTo(bb862),UnwindUnreachable())}bb862={_864 = _862 != _863;Call(_865 = expect_p(_864,true,0.5f64),ReturnTo(bb863),UnwindUnreachable())}bb863={match Move(_865) {false => bb33,_ => bb864}}bb864={_872 = core::ptr::addr_of!((*holder_key));_871 = _872 as *const u8;Call(_870 = core::intrinsics::volatile_load::<u8>(_871),ReturnTo(bb964),UnwindUnreachable())}bb800={_815 = core::ptr::addr_of!((*holder_key));_814 = _815 as *const u8;Call(_810 = core::intrinsics::volatile_load::<u8>(_814),ReturnTo(bb801),UnwindUnreachable())}bb801={Call(_811 = core::intrinsics::volatile_load::<u8>(_814),ReturnTo(bb802),UnwindUnreachable())}bb802={_812 = _810 != _811;match Move(_812) {true => bb820,_ => bb109}}bb820={_872 = core::ptr::addr_of!((*holder_key));_871 = _872 as *const u8;Call(_870 = core::intrinsics::volatile_load::<u8>(_871),ReturnTo(bb920),UnwindUnreachable())}bb964={Call(_866 = trapu(),ReturnTo(bb54),UnwindUnreachable())}bb920={Call(_813 = trapu(),ReturnTo(bb54),UnwindUnreachable())}}}
























































#[no_mangle]pub fn actual_curve_size()->usize{size_of::<BondingCurve>()}
#[no_mangle]pub fn actual_account_size()->usize{size_of::<Account<BondingCurve>>()}
#[no_mangle]pub fn actual_box_size()->usize{size_of::<Box<Account<BondingCurve>>>()}
#[no_mangle]pub fn actual_curve_holder_offset(x:&BondingCurve)->usize{&x.is_holder_reward as *const bool as usize - x as *const BondingCurve as usize}
#[no_mangle]pub fn actual_account_holder_offset(x:&Account<BondingCurve>)->usize{&x.is_holder_reward as *const bool as usize - x as *const Account<BondingCurve> as usize}
#[no_mangle]pub fn actual_account_raw_hold(x:&Box<Account<BondingCurve>>)->u8{let cvk=unsafe{core::ptr::read_volatile(x as *const Box<Account<BondingCurve>> as *const *const u8)};unsafe{core::ptr::read_volatile(cvk.add(165))}}
#[no_mangle]pub fn actual_account_holder(x:&Box<Account<BondingCurve>>)->bool{x.is_holder_reward}
#[inline(always)]unsafe fn aipin<'a,T>(x:&AccountInfo<'a>)->AccountInfo<'a>{let r=x.clone();vann(&r as *const AccountInfo as *const u8,b"\0".as_ptr(),b"\0".as_ptr(),0,core::ptr::null());r}
#[no_mangle]pub fn actual_clone<'a>(x:&AccountInfo<'a>)->AccountInfo<'a>{unsafe{aipin::<()>(x)}}

extern "C" {#[link_name="llvm.annotation.i1.p0"]fn ann1(v:bool,s:*const u8,f:*const u8,l:u32)->bool;#[link_name="llvm.bpf.passthrough.i64.i64"]fn pt64(n:u32,v:u64)->u64;}
const _: [();33]=[();size_of::<Option<Option<Pubkey>>>()];
const _: [();1]=[();align_of::<Option<Option<Pubkey>>>()];
#[no_mangle]pub fn nested_outer_none()->u8{let x:Option<Option<Pubkey>>=None;unsafe{*(&x as *const Option<Option<Pubkey>> as *const u8)}}
#[no_mangle]pub fn nested_inner_none()->u8{let x:Option<Option<Pubkey>>=Some(None);unsafe{*(&x as *const Option<Option<Pubkey>> as *const u8)}}
#[no_mangle]pub fn nested_some(v:Pubkey)->u8{let x=Some(Some(v));unsafe{*(&x as *const Option<Option<Pubkey>> as *const u8)}}
#[no_mangle]pub fn nested_raw(x:&Option<Pubkey>)->Option<Option<Pubkey>>{let (ntag,np)=unsafe{let p=x as *const Option<Pubkey> as *const u8;(*p,p.add(1))};let mut out=None;unsafe{let sp=&mut out as *mut Option<Option<Pubkey>> as *mut u8;*sp=ntag;core::ptr::copy_nonoverlapping(np,sp.add(1),32);}out}
#[no_mangle]pub fn nested_control(x:&Option<Pubkey>)->Option<Option<Pubkey>>{Some(*x)}
#[no_mangle]pub fn annotation_bool(v:bool)->bool{unsafe{ann1(v,b"\0".as_ptr(),b"\0".as_ptr(),0)}}
#[no_mangle]pub fn annotation_control(v:bool)->bool{v}

#[no_mangle]pub fn ordinary4158_validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:&Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);
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
 Ok({let mut b=core::mem::MaybeUninit::<[u8;32]>::uninit();unsafe{let p=b.as_mut_ptr().cast::<u8>();core::ptr::copy_nonoverlapping(target_head.as_ptr().cast::<u8>(),p,7);core::ptr::copy_nonoverlapping(target_tail.as_ptr().cast::<u8>(),p.add(7),25);Pubkey::new_from_array(b.assume_init())}})/*shim: reconstruct the initialized key from the disjoint head and tail arrays*/}

#[no_mangle]pub fn updated4149_validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{
 if st.mayhem{return Err(error!(PumpError::CtoNotAllowedForMayhemCoin));}let holder=hopt.unwrap_or(false);
// Reconstructed positions of the same deployed validations.



 let mut target_head=core::mem::MaybeUninit::<[u8;7]>::uninit();let mut target_tail=core::mem::MaybeUninit::<[u8;25]>::uninit();/*shim: separate 7-byte head and 25-byte tail permit a whole-head lifetime end without ending the tail*/if match st.holder_reward as u8{1=>{if !unsafe{expect_p(holder,true,0.625)}/*shim: holder test weight (the and-1 test has no zero heuristic; keeps the original 12:20 block frequencies)*/{return Err({let e=error!(PumpError::HolderRewardCreatorImmutable);unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;e});}true}_=>if unsafe{expect_p(holder,true,0.49)}/*shim: !hr holder test 49:51 (MBP places the 306 test after the !hr holder test)*/{






  if !st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}true}else{false}}

 {if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}{let b=holder_key.to_bytes();let p=b.as_ptr();unsafe{core::ptr::copy_nonoverlapping(p,target_head.as_mut_ptr().cast::<u8>(),7);core::ptr::copy_nonoverlapping(p.add(7),target_tail.as_mut_ptr().cast::<u8>(),25);}}}else{unsafe{lte(7,target_head.as_mut_ptr().cast::<u8>())}/*shim: only the seven-byte head is dead through the non-holder checks; the tail keeps its existing lifetime*/;







  let t=if unsafe{expect_p((*(&new as *const Option<Pubkey> as *const u8)&1)==0,true,0.75)}/*shim: 306 None probability, single-bit tag test*/{unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;return Err(error!(PumpError::CtoNewCreatorRequired));}else{unsafe{core::ptr::read_unaligned((&new as *const Option<Pubkey> as *const u8).add(1) as *const Pubkey)}/*shim: 306 payload read, no tag re-test*/};
  if t==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((unsafe{let mut k=core::mem::MaybeUninit::<Pubkey>::uninit();let kp=k.as_mut_ptr() as *mut u8;core::ptr::copy_nonoverlapping((&t as *const Pubkey as *const u8).add(8),kp.add(8),24);(kp as *mut u64).write_unaligned(((&new as *const Option<Pubkey> as *const u8).add(1) as *const u64).read_unaligned());k.assume_init()}/*shim: 307 key read back from the t stack slot (no memcpy forwarding to new+1), first word from new+1*/,Pubkey::default())));}




  if unsafe{expect_p((pt8(4,(t==*sharing) as u8)&1)!=0,true,0.625)}/*shim: 312 t==sharing memcmp equal-likely 20:12 (llc spill colour; was the libcall 12:20); passthrough on the compare byte*/||unsafe{expect(t==*holder_key,false)}/*shim: 312 holder_key compare unlikely 1:2000 (llc placement)*/{unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;return Err(error!(PumpError::InvalidCreator));}unsafe{lts(7,target_head.as_mut_ptr().cast::<u8>());lts(25,target_tail.as_mut_ptr().cast::<u8>())}/*shim: start the parts before storing the checked key; copy head before materializing the tail source to preserve SROA order*/;{unsafe{core::ptr::copy_nonoverlapping(&t as *const Pubkey as *const u8,target_head.as_mut_ptr().cast::<u8>(),7);}let b=t.to_bytes();unsafe{core::ptr::copy_nonoverlapping(b.as_ptr().add(7),target_tail.as_mut_ptr().cast::<u8>(),25);}}}
// layout-pad(13): aligns the next Source site with the original line
 let cashback=if holder{false}else{st.cashback};











 match fee{Some(f)=>{if st.quote_locked{return Err(error!(PumpError::CreatorFeeNotConfigurableForQuote));}
// layout-pad(3): aligns the next Source site with the original line


  if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}



  unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder before the fee_configurable test*/;if !st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}



  if f==0||f>st.max_fee{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};}None=>{}}
 Ok({let mut b=core::mem::MaybeUninit::<[u8;32]>::uninit();unsafe{let p=b.as_mut_ptr().cast::<u8>();core::ptr::copy_nonoverlapping(target_head.as_ptr().cast::<u8>(),p,7);core::ptr::copy_nonoverlapping(target_tail.as_ptr().cast::<u8>(),p.add(7),25);Pubkey::new_from_array(b.assume_init())}})/*shim: reconstruct the initialized key from the disjoint head and tail arrays*/}
