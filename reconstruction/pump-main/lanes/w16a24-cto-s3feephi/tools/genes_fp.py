# w16a24 s3feephi genes: fee-tag phi as a fresh out-param `fo` (starts None, set only by the validated arm), on main and S3n.
# Each gene is a list of exact single-occurrence (old,new) replacements or callables s->s; newline count must hold.
import os,sys,runpy
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import genes_af as _A
G=_A.G
_RV='unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};'
_R338='if f==0||f>st.max_fee{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}'
# S3n (w16a08 basinbound e/S3n.py): per-arm holder flag out-param hf
_S3N=[tuple(x) for x in runpy.run_path('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a08-cto-basinbound/e/S3n.py')['EDITS']] if os.path.exists('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a08-cto-basinbound/e/S3n.py') else None
def _rep(s,a,b,tag):
    c=s.count(a); assert c==1,(tag,c,a[:100]); return s.replace(a,b)
def _s3n(s):
    for a,b in _S3N: s=_rep(s,a,b,'S3n')
    return s
G['S3n']=[_s3n]
# fo: fresh `let mut fo:Option<u64>=None;` declared in the validate block (where ftc put `let mut fee=fee;`); validate takes
#     `fo:&mut Option<u64>` as its LAST parameter; the fee arm writes `*fo=Some(f)` after the range check (after the 338
#     placeholder, as ftc); the block returns fo; line 757 and pargs.2 read fo. The fee argument dies in validate.
def _fo(s):
    s=_rep(s,'sharing:&Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);','sharing:&Pubkey,fo:&mut Option<u64>)->Result<Pubkey>{let holder=hopt==Some(true);','fo1') if 'hf:&mut bool)->Result' not in s else \
      _rep(s,'hf:&mut bool)->Result<Pubkey>{let holder=hopt==Some(true);','hf:&mut bool,fo:&mut Option<u64>)->Result<Pubkey>{let holder=hopt==Some(true);','fo1')
    s=_rep(s,_R338+_RV+'}None=>{}}',_R338+_RV+'*fo=Some(f);}None=>{}}','fo2')
    s=_rep(s,'let hopt=holder;','let hopt=holder;let mut fo:Option<u64>=None;','fo3')
    if '&sk,&mut hf)?;' in s: s=_rep(s,'&sk,&mut hf)?;','&sk,&mut hf,&mut fo)?;','fo4')
    else: s=_rep(s,'validate(&st,hopt,fee,new,&holder_key,&sk)?;','validate(&st,hopt,fee,new,&holder_key,&sk,&mut fo)?;','fo4')
    s=_rep(s,'cashback,target,sharing_update,collect_old,skip)};','cashback,target,sharing_update,collect_old,skip,fo)};','fo5')
    s=_rep(s,'let (_holder,cashback,target,sharing_update,collect_old,skip)={','let (_holder,cashback,target,sharing_update,collect_old,skip,fo)={','fo6')
    s=_rep(s,'if let Some(f)=fee{curve.creator_fee_bps=f;}','if let Some(f)=fo{curve.creator_fee_bps=f;}','fo7')
    s=_rep(s,'let pargs=(target,a.bonding_curve.is_holder_reward,fee);','let pargs=(target,a.bonding_curve.is_holder_reward,fo);','fo8')
    return s
G['fo']=[_fo]
# fob: fo with `*fo=Some(f)` BEFORE the 338 placeholder (right after the range check)
def _fob(s):
    s=_fo(s); return _rep(s,_R338+_RV+'*fo=Some(f);}None=>{}}',_R338+'*fo=Some(f);'+_RV+'}None=>{}}','fob')
G['fob']=[_fob]
# d338 / d334: drop the read_volatile placeholders (line count kept)
def _d338(s):
    i=s.index(_R338); j=s.index(_RV,i); assert j==i+len(_R338) or s[i+len(_R338):j] in ('*fo=Some(f);',),(s[i:j+80]); return s[:j]+s[j+len(_RV):]
def _d334(s):
    a=_RV+'if !st.fee_configurable{'; return _rep(s,a,'if !st.fee_configurable{','d334')
G['d338']=[_d338]; G['d334']=[_d334]
def apply(s,names): return _A.apply(s,names)
