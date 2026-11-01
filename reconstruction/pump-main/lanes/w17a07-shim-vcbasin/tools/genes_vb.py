# w17a07 vcbasin genes: w16a14 genes_vc (VC, VCsh, t1n, ...) + marked shim genes for the VC basins
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import genes_vc as _S
G=_S.G
def apply(s,names): return _S.apply(s,names)
_CBO='let cashback=!holder&&st.cashback;'
# cbn with the tag read through a raw u8 pointer: no !range on the tag, so the sharing tag phi is not folded to constants
G['cbr']=[(_CBO,'let cashback=unsafe{*(&new as *const Option<Pubkey> as *const u8)}!=0&&st.cashback;/*shim: tag byte without range metadata keeps the sharing tag phi unfolded*/')]
G['cbrv']=[(_CBO,'let cashback=unsafe{core::ptr::read_volatile(&new as *const Option<Pubkey> as *const u8)}!=0&&st.cashback;/*shim: volatile tag byte for the outer cashback*/')]
G['cbr2']=[(_CBO,'let cashback=st.cashback&&unsafe{*(&new as *const Option<Pubkey> as *const u8)}!=0;/*shim: tag byte without range metadata keeps the sharing tag phi unfolded*/')]
# the 312 expect_p shim of main (tuned for main's colouring) reverted / retuned under VC
_P312='if unsafe{expect_p(t==*sharing,true,0.625)}/*shim: 312 t==sharing memcmp equal-likely 20:12 (llc spill colour; was the libcall 12:20)*/||t==*holder_key{'
G['n312']=[(_P312,'if t==*sharing||t==*holder_key{')]
for _p in ('0.5','0.375','0.75','0.25'):
    G['p312_'+_p.replace('0.','')]=[(_P312,_P312.replace('0.625',_p))]
# per-arm cashback flag carried through the CtoState local (orig [r10-0x958]: 0 in the holder arm, st.cashback otherwise):
# the closure's holder arm clears st.cashback through a raw pointer; the outer block reads st.cashback after the closure,
# so the head no longer reloads hopt for `!holder&&st.cashback` (the extra `and 253` of basin A)
_H298='let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{let new=new;'
_W='unsafe{(core::ptr::addr_of!(st.cashback) as *mut bool).write(false)}/*shim: per-arm cashback flag in st (orig [r10-0x958])*/;'
G['stcb']=[(_CBO,''),(_H298,_H298.replace('*holder_key}else',_W+'*holder_key}else')),
           ('Ok(target)})()?;let mut sharing_update','Ok(target)})()?;let cashback=st.cashback;/*shim: per-arm cashback read back*/let mut sharing_update')]
G['stcb2']=G['stcb']+[(' let cashback=if holder{false}else{st.cashback};',' let cashback=st.cashback;')]
# same, but the flag write happens at the closure's holder test head (before the 298 new check)
G['stcb3']=[(_CBO,''),(_H298,_H298.replace('let target=if holder{if new','let target=if holder{'+_W+'if new')),
           ('Ok(target)})()?;let mut sharing_update','Ok(target)})()?;let cashback=st.cashback;/*shim: per-arm cashback read back*/let mut sharing_update')]
