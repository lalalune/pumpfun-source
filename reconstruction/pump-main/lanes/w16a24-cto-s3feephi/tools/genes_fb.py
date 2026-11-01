# w16a24 s3feephi wave-17 genes (SHIM TRACK): fee-tag phi as ONE validated-fee flag.
# The original keeps a single tag phi (r7 = 1 in the range-check OK block, 0 on the None paths, spilled to [r10-0x8e8])
# that feeds both the line-757 test and the admin_cto_pool tag; the fee value stays in its entry slot [r10-0x930].
# fo (Option<u64> out-param) splits that tag into two phis after InstCombine (an i1 phi for the 757 branch, an i64 phi
# for the pool tag); the IR oracle that merges them back is +34 M on main+fo and +94 M on S3n+fo.
# fb: `let mut fb=false;` out-param set only by the validated arm; 757 tests fb and pargs.2 is rebuilt from fb; the value
#     comes from the fee argument through a marked unwrap_unchecked shim (no second tag test). The fee tag dies in validate.
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import genes_fp as _P
G=_P.G
_rep=_P._rep; _RV=_P._RV; _R338=_P._R338
_SH='/*shim: fee value under the validated-fee flag, no second fee-tag test*/'
def _fb(s,ty='bool',init='false',setv='true',test='fb',mk=None):
    if 'hf:&mut bool)->Result' in s:
        s=_rep(s,'hf:&mut bool)->Result<Pubkey>{let holder=hopt==Some(true);',f'hf:&mut bool,fb:&mut {ty})->Result<Pubkey>{{let holder=hopt==Some(true);','fb1')
    else:
        s=_rep(s,'sharing:&Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);',f'sharing:&Pubkey,fb:&mut {ty})->Result<Pubkey>{{let holder=hopt==Some(true);','fb1')
    s=_rep(s,_R338+_RV+'}None=>{}}',_R338+_RV+f'*fb={setv};}}None=>{{}}}}','fb2')
    s=_rep(s,'let hopt=holder;',f'let hopt=holder;let mut fb:{ty}={init};','fb3')
    if '&sk,&mut hf)?;' in s: s=_rep(s,'&sk,&mut hf)?;','&sk,&mut hf,&mut fb)?;','fb4')
    else: s=_rep(s,'validate(&st,hopt,fee,new,&holder_key,&sk)?;','validate(&st,hopt,fee,new,&holder_key,&sk,&mut fb)?;','fb4')
    s=_rep(s,'cashback,target,sharing_update,collect_old,skip)};','cashback,target,sharing_update,collect_old,skip,fb)};','fb5')
    s=_rep(s,'let (_holder,cashback,target,sharing_update,collect_old,skip)={','let (_holder,cashback,target,sharing_update,collect_old,skip,fb)={','fb6')
    s=_rep(s,'if let Some(f)=fee{curve.creator_fee_bps=f;}','if '+test+'{curve.creator_fee_bps=unsafe{fee.unwrap_unchecked()}'+_SH+';}','fb7')
    pa=mk or ('if '+test+'{Some(unsafe{fee.unwrap_unchecked()}'+_SH+')}else{None}')
    s=_rep(s,'let pargs=(target,a.bonding_curve.is_holder_reward,fee);','let pargs=(target,a.bonding_curve.is_holder_reward,'+pa+');','fb8')
    return s
G['fb']=[_fb]
# fu: the flag as u64 0/1 (the original's tag is a 64-bit value), tested !=0
G['fu']=[lambda s:_fb(s,ty='u64',init='0',setv='1',test='fb!=0')]
# fbm: pargs.2 as fb.then(..) (bool::then) instead of if/else
G['fbm']=[lambda s:_fb(s,mk='fb.then(||unsafe{fee.unwrap_unchecked()}'+_SH+')')]
def apply(s,names): return _P.apply(s,names)
# fbx: pargs.2 built without a branch: Option<u64> transmuted from [flag as u64, fee payload]; the payload is read by
#      transmuting fee (no unwrap_unchecked outside the flag, so no unreachable for LLVM to exploit)
_SHX='/*shim: Option<u64> = [fee-flag phi as tag, fee payload], no branch*/'
_FX='unsafe{core::mem::transmute::<[u64;2],Option<u64>>([fb as u64,core::mem::transmute::<Option<u64>,[u64;2]>(fee)[1]])}'+_SHX
G['fbx']=[lambda s:_fb(s,mk=_FX)]
# fbo: one Option<u64> fo rebuilt from the flag (transmute) on line 752, read by 757 (if let) and pargs.2
def _fbo(s):
    s=_fb(s,mk='fo')
    s=_rep(s,'if fb{curve.creator_fee_bps=unsafe{fee.unwrap_unchecked()}'+_SH+';}','if let Some(f)=fo{curve.creator_fee_bps=f;}','fbo1')
    s=_rep(s,' let (old_creator,old_fee)={\n',' let fo='+_FX+';let (old_creator,old_fee)={\n','fbo2')
    return s
G['fbo']=[_fbo]
# fe: fo as in genes_fp, but the validated arm copies the whole argument (`*fo=fee;`, which is Some(f) there): the tag phi's
#     OK-path incoming value is the entry tag, not a constant, so InstCombine has no constant phi to split.
def _fe(s):
    s=_P._fo(s); return _rep(s,_R338+_RV+'*fo=Some(f);}None=>{}}',_R338+_RV+'*fo=fee;}None=>{}}','fe')
G['fe']=[_fe]
