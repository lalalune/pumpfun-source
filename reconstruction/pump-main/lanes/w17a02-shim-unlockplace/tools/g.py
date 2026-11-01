# w17a02 shim genes: (file, old, new) exact single-occurrence replacements; line counts must not change.
G={}
L1='#[path="admin_set_idl_authority.rs"]pub mod idl_authority;'
FG=[('lib',L1,'#![feature(link_llvm_intrinsics)]'+L1)]
EXD=[('cto','\n\n#[derive(Accounts)]','\nextern "C"{#[link_name="llvm.expect.i1"]fn expect(b:bool,v:bool)->bool;}/*shim: llvm.expect = likely/unlikely branch weights (core::intrinsics::unlikely emits none on rustc 1.79-dev)*/\n#[derive(Accounts)]')]
LP='// layout-pad(183): aligns the next Source site with the original line\n\n'
CLD=[('cto',LP,LP[:-1]+'#[cold] fn cold(){}/*shim: cold-call BPI marker, inlined away*/\n')]
L306='  let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};'
L307='  if t==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((t,Pubkey::default())));}'
L312='  if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};'
SW='  swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);'
G['fg']=FG
G['fgx']=FG+EXD
G['fgc']=CLD
# cold() inside 307/312 error branches
G['c307']=CLD+[('cto',L307,L307.replace('{return Err(error!(PumpError::CreatorShouldNotBeZero)','{cold();/*shim: cold 307*/return Err(error!(PumpError::CreatorShouldNotBeZero)'))]
G['c312']=CLD+[('cto',L312,L312.replace('{return Err(error!(PumpError::InvalidCreator));}','{cold();/*shim: cold 312*/return Err(error!(PumpError::InvalidCreator));}'))]
G['c3']=G['c307']+[G['c312'][1]]
# cold() at head of 306 Some arm (None-hot at V)
G['c306']=CLD+[('cto',L306,'  let t=if let Some(t)=new{cold();/*shim: 306 Some arm cold at V*/t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};')]
# expect on guards
G['x307']=FG+EXD+[('cto',L307,L307.replace('if t==Pubkey::default(){','if unsafe{expect(t==Pubkey::default(),false)}/*shim: 307 unlikely*/{'))]
G['x312']=FG+EXD+[('cto',L312,L312.replace('if t==*sharing||t==*holder_key{','if unsafe{expect(t==*sharing,false)}||unsafe{expect(t==*holder_key,false)}/*shim: 312 unlikely*/{'))]
G['x3']=G['x307']+[G['x312'][-1]]
G['x312b']=FG+EXD+[('cto',L312,L312.replace('if t==*sharing||t==*holder_key{','if unsafe{expect(t==*sharing||t==*holder_key,false)}/*shim: 312 unlikely*/{'))]
# 306 None-hot via expect
G['x306n']=FG+EXD+[('cto',L306,'  let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};'.replace('let t=if let Some(t)=new{t}else{','let t=if unsafe{expect(new.is_some(),false)}/*shim: 306 None-hot*/{new.unwrap_or_default()}else{'))]
# tf_g3 (w15a21 creator binding)
STH2="{ let st=CtoState{fee_configurable:a.global.creator_fee_configurable,creator:a.bonding_curve.creator,"
G['tf']=[('cto',STH2,"{ let creator=a.bonding_curve.creator;"+STH2[2:]),
         ('cto',"else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}","else{target=creator;sharing_update=Some(args.0);(false,true)}}")]
# ---- llc-persistent single-weight sweep (expect on one branch) ----
def EX(cond):
    return 'unsafe{expect('+cond+',%s)}'
SITES={
 'v284':('if st.mayhem{','if '+EX('st.mayhem')+'/*shim: 284 weight*/{'),
 'v289':('if st.holder_reward&&!(hopt==Some(true)){','if '+EX('st.holder_reward&&!(hopt==Some(true))')+'/*shim: 289 weight*/{'),
 'v296':('if holder&&!st.holder_reward&&!st.holder_enabled{','if '+EX('holder&&!st.holder_reward&&!st.holder_enabled')+'/*shim: 296 weight*/{'),
 'v298':('if new.is_some(){','if '+EX('new.is_some()')+'/*shim: 298 weight*/{'),
 'v307':('if t==Pubkey::default(){','if '+EX('t==Pubkey::default()')+'/*shim: 307 weight*/{'),
 'v326':('if st.quote_locked{','if '+EX('st.quote_locked')+'/*shim: 326 weight*/{'),
 'v330':('if cashback{return','if '+EX('cashback')+'/*shim: 330 weight*/{return'),
 'v334':('if !st.fee_configurable{','if '+EX('!st.fee_configurable')+'/*shim: 334 weight*/{'),
 'v338':('if f==0||f>st.max_fee{','if '+EX('f==0||f>st.max_fee')+'/*shim: 338 weight*/{'),
 'e410':('require!(a.bonding_curve.creator_fee==0,PumpError::CreatorFeesNotSwept);','if '+EX('a.bonding_curve.creator_fee!=0')+'/*shim: 410 weight*/{return Err(error!(PumpError::CreatorFeesNotSwept));}'),
 'e556':('if collect_old{','if '+EX('collect_old')+'/*shim: wallet gate weight*/{'),
 'wex':('if a.current_creator.executable{','if '+EX('a.current_creator.executable')+'/*shim: wallet executable weight*/{'),
 'wown':('else if a.current_creator.owner!=&anchor_lang::system_program::ID{','else if '+EX('a.current_creator.owner!=&anchor_lang::system_program::ID')+'/*shim: wallet owner weight*/{'),
 'wwr':('if !a.current_creator.is_writable{','if '+EX('!a.current_creator.is_writable')+'/*shim: wallet writable weight*/{'),
 'wcol':('if !collection_native||coin_present{','if '+EX('!collection_native||coin_present')+'/*shim: wallet ata weight*/{'),
 'wdc':('if do_collect{','if '+EX('do_collect')+'/*shim: wallet collect weight*/{'),
 'wcp':('if coin_present&do_coin{','if '+EX('coin_present&do_coin')+'/*shim: wallet coin weight*/{'),
 's648':('if a.holder_creator_vault.key()!=dest{','if '+EX('a.holder_creator_vault.key()!=dest')+'/*shim: 648 weight*/{'),
 'snat':('if native{','if '+EX('native')+'/*shim: sweep native weight*/{'),
 'sna0':('(if amount>0{','(if '+EX('amount>0')+'/*shim: sweep native amount weight*/{'),
 'sfz':('if frozen{','if '+EX('frozen')+'/*shim: sweep frozen weight*/{'),
 'stk0':('else if amount>0{','else if '+EX('amount>0')+'/*shim: sweep token amount weight*/{'),
 'gate':('swept=(!skip).then(','swept='+EX('!skip')+'/*shim: sweep gate weight*/.then('),
 'pool':('if pool_updated{','if '+EX('pool_updated')+'/*shim: pool weight*/{'),
 'shr':('if shared{','if '+EX('shared')+'/*shim: shared weight*/{'),
 'shh':('if holder{sharing_update','if '+EX('holder')+'/*shim: shared holder weight*/{sharing_update'),
}
for k,(a,b) in SITES.items():
    for d,v in (('f','false'),('t','true')):
        G[k+d]=FG+EXD+[('cto',a,b%v)]
# ---- 306 weight with the payload read through a raw pointer (no MIR re-test of the tag) ----
L306R='  let t=if unsafe{expect(new.is_none(),%s)}/*shim: 306 weight*/{return Err(error!(PumpError::CtoNewCreatorRequired));}else{unsafe{core::ptr::read_unaligned((&new as *const Option<Pubkey> as *const u8).add(1) as *const Pubkey)}/*shim: 306 payload read, no tag re-test*/};'
G['r306n']=FG+EXD+[('cto',L306,L306R%'true')]
G['r306s']=FG+EXD+[('cto',L306,L306R%'false')]
# ---- arbitrary probabilities: llvm.expect.with.probability.i1 (LowerExpect turns p into branch_weights) ----
EXP=[('cto','\n\n#[derive(Accounts)]','\nextern "C"{#[link_name="llvm.expect.with.probability.i1"]fn expect_p(b:bool,v:bool,p:f64)->bool;#[link_name="llvm.expect.i1"]fn expect(b:bool,v:bool)->bool;}/*shim: llvm.expect(.with.probability) branch weights (core::intrinsics::unlikely emits none on rustc 1.79-dev)*/\n#[derive(Accounts)]')]
L306P='  let t=if unsafe{expect_p(new.is_none(),true,%s)}/*shim: 306 None probability*/{return Err(error!(PumpError::CtoNewCreatorRequired));}else{unsafe{core::ptr::read_unaligned((&new as *const Option<Pubkey> as *const u8).add(1) as *const Pubkey)}/*shim: 306 payload read, no tag re-test*/};'
for nm,p in (('50','0.5'),('60','0.625'),('67','0.6667'),('75','0.75'),('80','0.8'),('90','0.9'),('97','0.97'),('99','0.995'),('33','0.3333'),('20','0.2'),('10','0.1'),('03','0.03'),('01','0.005')):
    G['p306_'+nm]=FG+EXP+[('cto',L306,L306P%p)]
def EXPP(cond,p):
    return 'unsafe{expect_p('+cond+',true,'+p+')}'
for k,(a,b) in SITES.items():
    for nm,p in (('h','0.625'),('l','0.375')):
        bb=b.replace('unsafe{expect(','unsafe{expect_p(').replace(',%s)}',',true,'+p+')}')
        G[k+nm]=FG+EXP+[('cto',a,bb)]
# 312 compares with mild probabilities (equal-likely 20:12 etc.), each compare separately
for nm,p in (('h','0.625'),('l','0.375')):
    G['x312a'+nm]=FG+EXP+[('cto',L312,L312.replace('if t==*sharing||t==*holder_key{','if unsafe{expect_p(t==*sharing,true,'+p+')}/*shim: 312a weight*/||t==*holder_key{'))]
    G['x312b'+nm]=FG+EXP+[('cto',L312,L312.replace('if t==*sharing||t==*holder_key{','if t==*sharing||unsafe{expect_p(t==*holder_key,true,'+p+')}/*shim: 312b weight*/{'))]
