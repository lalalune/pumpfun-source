#!/usr/bin/env python3
"""gx.py <in admin_cto.rs> <out> <genes...>: w17a30 stand-in genes (exact single-occurrence edits, line count kept)."""
import sys
DECL_OLD='fn lte(n:i64,p:*mut u8);}/*shim: llvm.lifetime.start/end = explicit StackColoring live-range markers (no instruction)*/'
DECL_NEW=DECL_OLD+'extern "C"{#[link_name="llvm.var.annotation.p0.p0"]fn vann(p:*const u8,s:*const u8,f:*const u8,l:u32,a:*const u8);}/*shim: llvm.var.annotation = a zero-instruction pin that keeps an alloca through SROA (dropped at ISel)*/'
SKM='let mut skm=core::mem::MaybeUninit::<Pubkey>::uninit();'
def X(ty='[u64;4]',pos='after_skm'):
    s='let mut hk2=core::mem::MaybeUninit::<%s>::uninit();unsafe{vann(hk2.as_mut_ptr() as *const u8,core::ptr::null(),core::ptr::null(),0,core::ptr::null())}/*shim: frame stand-in for the original hk2 copy (FI47 live across validate)*/;'%ty
    return [(SKM,SKM+s)]
G={'X':[(DECL_OLD,DECL_NEW)]+X(),'X24':[(DECL_OLD,DECL_NEW)]+X('[u64;3]'),'X40':[(DECL_OLD,DECL_NEW)]+X('[u64;5]'),'X48':[(DECL_OLD,DECL_NEW)]+X('[u64;6]'),
   'decl':[(DECL_OLD,DECL_NEW)],
   'p8':[(DECL_OLD+'@',None)]}
P8DECL='#[repr(C,align(8))]struct P8(Pubkey);/*shim: 8-aligned validate return value (target pieces on 8-byte boundaries, no offset-1 SROA pieces)*/'
G['p8']=[('/*shim: llvm.lifetime.start/end = explicit StackColoring live-range markers (no instruction)*/','/*shim: llvm.lifetime.start/end = explicit StackColoring live-range markers (no instruction)*/'+P8DECL),
  ('->Result<Pubkey>{let holder=hopt==Some(true);','->Result<P8>{let holder=hopt==Some(true);'),
  ('Ok(target)}pub fn execute','Ok(P8(target))}pub fn execute'),
  ('let mut target=validate(&st,hopt,fee,new,holder_key,sk)?;','let mut target=validate(&st,hopt,fee,new,holder_key,sk)?.0;')]
G['vt']=[(' let target=if ',' let mut target=core::mem::MaybeUninit::<Pubkey>::uninit();if '),
  ('{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{','{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}target.write(*holder_key);}else{unsafe{lte(32,target.as_mut_ptr() as *mut u8)}/*shim: lifetime end of validate target at the non-holder arm head (its pieces stay free through the 306/307/312 checks)*/;'),
  ('return Err(error!(PumpError::InvalidCreator));}t};','return Err(error!(PumpError::InvalidCreator));}unsafe{lts(32,target.as_mut_ptr() as *mut u8)}/*shim: lifetime start of validate target right before the checked t is stored*/;target.write(t);}'),
  (' Ok(target)}pub fn execute',' Ok(unsafe{target.assume_init()})/*shim: validate target held in a MaybeUninit for the lifetime markers*/}pub fn execute')]
TAIL='(holder,cashback,target,sharing_update,collect_old,skip)};'
G['Xt']=[(DECL_OLD,DECL_NEW),(SKM,SKM+'let mut hk2=core::mem::MaybeUninit::<[u64;4]>::uninit();/*shim: frame stand-in for the original hk2 copy (32 B slot live across validate: FI47 -0x518)*/'),
  (TAIL,'unsafe{vann(hk2.as_mut_ptr() as *const u8,core::ptr::null(),core::ptr::null(),0,core::ptr::null())}/*shim: var.annotation keeps the hk2 stand-in through SROA (no instruction)*/;'+TAIL)]
HEAD='let (_holder,cashback,target,sharing_update,collect_old,skip)={ '
def XH(ty,sz):
    return [(DECL_OLD,DECL_NEW),(HEAD,HEAD+'let mut hk2=core::mem::MaybeUninit::<%s>::uninit();/*shim: frame stand-in for the original hk2 copy (%d B slot live across validate: FI47 -0x518)*/'%(ty,sz)),
      (TAIL,'unsafe{vann(hk2.as_mut_ptr() as *const u8,core::ptr::null(),core::ptr::null(),0,core::ptr::null())}/*shim: var.annotation keeps the hk2 stand-in through SROA (no instruction)*/;'+TAIL)]
G['Xh40']=XH('[u64;5]',40); G['Xh48']=XH('[u64;6]',48); G['Xh32']=XH('[u64;4]',32)
CR='let creator=a.bonding_curve.creator;'
G['crmv']=[(HEAD+CR+SKM,HEAD+SKM+'@@HK2@@'),('@@HK2@@','@@HK2@@')]
def apply(s,genes):
    n0=s.count('\n')
    for g in genes:
        if g=='Xc':   # hk2 after skm, then the tf_g3 creator binding after hk2 (WXvp base)
            a=HEAD+CR+SKM; assert s.count(a)==1,('Xc',s.count(a))
            s=s.replace(a,HEAD+SKM+'let mut hk2=core::mem::MaybeUninit::<[u64;4]>::uninit();/*shim: frame stand-in for the original hk2 copy (32 B slot live across validate: FI47 -0x518)*/'+CR)
            for a,b in [(DECL_OLD,DECL_NEW),(TAIL,'unsafe{vann(hk2.as_mut_ptr() as *const u8,core::ptr::null(),core::ptr::null(),0,core::ptr::null())}/*shim: var.annotation keeps the hk2 stand-in through SROA (no instruction)*/;'+TAIL)]:
                assert s.count(a)==1,(g,a[:80]); s=s.replace(a,b)
            continue
        for a,b in G[g]:
            assert s.count(a)==1,(g,a[:80],s.count(a)); s=s.replace(a,b)
    assert s.count('\n')==n0
    return s
if __name__=='__main__':
    s=open(sys.argv[1]).read(); n0=s.count('\n')
    for g in sys.argv[3:]:
        for a,b in G[g]:
            assert s.count(a)==1,(g,a[:80],s.count(a)); s=s.replace(a,b)
    assert s.count('\n')==n0
    open(sys.argv[2],'w').write(s)
