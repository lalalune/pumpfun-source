# holder-test genes (new main e60774c17)
gene('nop')
HD="->Result<Pubkey>{let holder=hopt==Some(true);\n if st.mayhem{return Err(error!(PumpError::CtoNotAllowedForMayhemCoin));}"
EXPW="/*shim: holder test weight (the and-1 test has no zero heuristic; keeps the original 12:20 block frequencies)*/"
# validate holder and-1 computed after the mayhem test; 289 test with the 12:20 weight
gene('vh',(HD,"->Result<Pubkey>{\n if st.mayhem{return Err(error!(PumpError::CtoNotAllowedForMayhemCoin));}let holder=hopt.unwrap_or(false);"),
 ("if !(hopt==Some(true)){","if !unsafe{expect_p(holder,true,0.625)}"+EXPW+"{"))
# same, no weight on 289
gene('vh0',(HD,"->Result<Pubkey>{\n if st.mayhem{return Err(error!(PumpError::CtoNotAllowedForMayhemCoin));}let holder=hopt.unwrap_or(false);"),
 ("if !(hopt==Some(true)){","if !holder{"))
# execute shared arm test as and-1 with the 12:20 weight
gene('e23',("{if holder{sharing_update=Some(None);(false,false)}","{if unsafe{expect_p(hopt.unwrap_or(false),true,0.625)}"+EXPW+"{sharing_update=Some(None);(false,false)}"))
gene('e230',("{if holder{sharing_update=Some(None);(false,false)}","{if hopt.unwrap_or(false){sharing_update=Some(None);(false,false)}"))
# curve store: keep its own and-1 (no GVN with the validate test)
gene('p755',("curve.is_holder_reward=holder.unwrap_or(false);","curve.is_holder_reward=(unsafe{pt8(9,*(&holder as *const Option<bool> as *const u8))}/*shim: passthrough on the holder byte of the curve store (own and-1, no CSE with the validate test)*/&1)!=0;"))
# 306 tag test as a single-bit test
gene('tag1',("let t=if unsafe{expect_p(new.is_none(),true,0.75)}/*shim: 306 None probability*/{","let t=if unsafe{expect_p((*(&new as *const Option<Pubkey> as *const u8)&1)==0,true,0.75)}/*shim: 306 None probability, single-bit tag test*/{"))
RV="unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;"
gene('pad7',("_=>if unsafe{expect_p(holder,true,0.49)}/*shim: !hr holder test 49:51 (MBP places the 306 test after the !hr holder test)*/{","_=>{"+RV+"if unsafe{expect_p(holder,true,0.49)}/*shim: !hr holder test 49:51 (MBP places the 306 test after the !hr holder test)*/{"),
 ("if !st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}true}else{false}}","if !st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}true}else{false}}}"))
H312="/*shim: 312 holder_key compare unlikely 1:2000 (llc placement)*/{"
for _k in range(1,9):
    gene('f312p%d'%_k,(H312,H312+RV*_k))
gene('pad306',("{return Err(error!(PumpError::CtoNewCreatorRequired));}","{"+RV+"return Err(error!(PumpError::CtoNewCreatorRequired));}"))
# 307 with_pubkeys key: words 1..3 from the t stack slot (not forwarded to new+1), word 0 from new+1 (keeps the new+1 pointer interval)
gene('v4s',("return Err(error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((t,Pubkey::default())));","return Err(error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((unsafe{let mut k=core::mem::MaybeUninit::<Pubkey>::uninit();let kp=k.as_mut_ptr() as *mut u8;core::ptr::copy_nonoverlapping((&t as *const Pubkey as *const u8).add(8),kp.add(8),24);(kp as *mut u64).write_unaligned(((&new as *const Option<Pubkey> as *const u8).add(1) as *const u64).read_unaligned());k.assume_init()}/*shim: 307 key read back from the t stack slot (no memcpy forwarding to new+1), first word from new+1*/,Pubkey::default())));"))
# new is a reference on main a596efe59
gene('v4r',("return Err(error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((t,Pubkey::default())));","return Err(error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((unsafe{let mut k=core::mem::MaybeUninit::<Pubkey>::uninit();let kp=k.as_mut_ptr() as *mut u8;core::ptr::copy_nonoverlapping((&t as *const Pubkey as *const u8).add(8),kp.add(8),24);(kp as *mut u64).write_unaligned(((new as *const Option<Pubkey> as *const u8).add(1) as *const u64).read_unaligned());k.assume_init()}/*shim: 307 key read back from the t stack slot (no memcpy forwarding to new+1), first word from new+1*/,Pubkey::default())));"))
def _d312(s):
    L=s.split('\n'); l=L[311]; R="unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;"
    assert R in l
    L[311]=l.replace(R,'',1); return '\n'.join(L)
