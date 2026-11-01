# Calibration variants: one construct each, as exact single-occurrence edits (file, old, new); line count kept.
LIBF='#[path="admin_set_idl_authority.rs"]pub mod idl_authority;'
GCI=('lib',LIBF,'#![feature(core_intrinsics)]'+LIBF)
GLL=('lib',LIBF,'#![feature(link_llvm_intrinsics)]'+LIBF)
NF='let nf=a.bonding_curve.creator_fee_bps;'
VAL='let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;'
VHDR='holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);'
SWH='fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{let a=&ctx.accounts;'
WLH='fn wallet(ctx:&Context<AdminCto>)->Result<()>{let a=&ctx.accounts;'
EXT=('cto','impl Id for Amm{fn id()->Pubkey{AMM}}\n\n#[derive(Accounts)]','impl Id for Amm{fn id()->Pubkey{AMM}}\nextern "C"{#[link_name="llvm.expect.i1"]fn expect(b:bool,v:bool)->bool;}/*shim: llvm.expect.i1 decl*/\n#[derive(Accounts)]')
V={
 'g_ci':  [GCI],
 'g_lli': [GLL],
 'g_ext': [GLL,EXT],
 'rv_fld':[('cto',NF,'let nf=unsafe{core::ptr::read_volatile(&a.bonding_curve.creator_fee_bps)}/*shim: volatile field read*/;')],
 'rv_loc':[('cto','if pool_updated{','if unsafe{core::ptr::read_volatile(&pool_updated)}/*shim: volatile local read*/{')],
 'rv_par':[('cto','if t==*sharing||t==*holder_key{','if t==*sharing||t==unsafe{core::ptr::read_volatile(holder_key)}/*shim: volatile 32 B param read*/{')],
 'rv_unu':[('cto',' let swept;',' let swept;unsafe{core::ptr::read_volatile(&holder_key as *const Pubkey as *const u8)};/*shim: unused volatile read*/')],
 'rv_own':[('cto','CpiContext::new({let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{owner:x.owner,key:x.key,','CpiContext::new({let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{owner:unsafe{core::ptr::read_volatile(&x.owner)}/*shim: pins the sweep program-clone owner load*/,key:x.key,')],
 'wv_fld':[('cto','curve.can_edit_creator_fee=false;','unsafe{core::ptr::write_volatile(&mut curve.can_edit_creator_fee,false)};/*shim: volatile field write*/')],
 'bb_val':[('cto',NF,'let nf=core::hint::black_box(a.bonding_curve.creator_fee_bps)/*shim: black_box value*/;')],
 'bb_ref':[('cto',NF,'let nf=*core::hint::black_box(&a.bonding_curve.creator_fee_bps)/*shim: black_box ref*/;')],
 'uu_arm':[('cto','(false,true)=>{}}','(false,true)=>unsafe{core::hint::unreachable_unchecked()}/*shim: impossible arm*/}')],
 'uu_asm':[('cto',VAL,VAL+'if holder&&new.is_some(){unsafe{core::hint::unreachable_unchecked()}}/*shim: assume via unreachable*/')],
 'ci_lik':[GCI,('cto','if pool_updated{','if core::intrinsics::likely(pool_updated)/*shim: likely*/{')],
 'ci_unl':[GCI,('cto','if pool_updated{','if core::intrinsics::unlikely(pool_updated)/*shim: unlikely*/{')],
 'ci_asm':[GCI,('cto',VAL,VAL+'unsafe{core::intrinsics::assume(!(holder&&new.is_some()))}/*shim: assume*/')],
 'lx_exp':[GLL,EXT,('cto','if pool_updated{','if unsafe{expect(pool_updated,true)}/*shim: llvm.expect*/{')],
 'pc_vst':[('cto','fn validate(st:&CtoState,','fn validate(st:*const CtoState,'),('cto',VHDR,VHDR.replace('{let holder=','{let st=unsafe{&*st};/*shim: raw st param*/let holder='))],
 'pc_vhk':[('cto',VHDR,VHDR.replace('holder_key:&Pubkey','holder_key:*const Pubkey').replace('{let holder=','{let holder_key=unsafe{&*holder_key};/*shim: raw holder_key param*/let holder='))],
 'pc_swc':[('cto',SWH,SWH.replace('ctx:&Context','ctx:*const Context').replace('{let a=','{let ctx=unsafe{&*ctx};/*shim: raw ctx param*/let a='))],
 'pc_swh':[('cto',SWH,SWH.replace('holder_key:&Pubkey','holder_key:*const Pubkey').replace('{let a=','{let holder_key=unsafe{&*holder_key};/*shim: raw holder_key param*/let a='))],
 'pc_wlc':[('cto',WLH,WLH.replace('ctx:&Context','ctx:*const Context').replace('{let a=','{let ctx=unsafe{&*ctx};/*shim: raw ctx param*/let a='))],
 'cp_wr': [('cto','curve.creator=target;','unsafe{core::ptr::write(&mut curve.creator,target)};/*shim: ptr::write*/')],
 'cp_rd': [('cto','let old_creator=curve.creator;','let old_creator=unsafe{core::ptr::read(&curve.creator)};/*shim: ptr::read*/')],
 'cp_cnl':[('cto','curve.creator=target;','unsafe{core::ptr::copy_nonoverlapping(&target,&mut curve.creator,1)};/*shim: copy_nonoverlapping*/')],
 'mu_loc':[('cto',' let swept;',' let mut swept=core::mem::MaybeUninit::<u64>::uninit();/*shim: MaybeUninit local*/'),
           ('cto',' swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);',' swept.write((!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0));'),
           ('cto','swept_to_holder_vault:swept','swept_to_holder_vault:unsafe{swept.assume_init()}')],
 'tg_byt':[('cto','if let Some(f)=fee{curve.creator_fee_bps=f;}','if unsafe{*(&fee as *const Option<u64> as *const u8)}&1!=0{curve.creator_fee_bps=unsafe{fee.unwrap_unchecked()};}/*shim: Option tag byte test*/')],
 'tm_ob': [('cto','curve.is_holder_reward=holder.unwrap_or(false);','curve.is_holder_reward=unsafe{core::mem::transmute::<Option<bool>,u8>(holder)}==1;/*shim: transmute Option<bool>*/')],
}
