# w16a22 s3outline genes: S3n (w16a08 per-arm holder flag, e/S3n.py) composed with w16a13 sg.py outline carriers.
# Every gene is a list of exact single-occurrence (old,new) edits or callables; line count is kept.
# Apply carrier genes first (they rewrite validate's signature and call), then 'S3' (call edit by regex).
import re as _re, os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import sg as _sg
G = dict(_sg.G)

def _one(s, a, b):
    c = s.count(a); assert c == 1, (c, a[:120]); return s.replace(a, b)

def _call(s, hf_pre='let mut hf=false;'):
    pat = r'let mut target=validate\(([^;]*?),&holder_key,&sk\)\?;'
    n = len(_re.findall(pat, s)); assert n == 1, ('call', n)
    return _re.sub(pat, lambda m: hf_pre + 'let mut target=validate(' + m.group(1) + ',&holder_key,&sk,&mut hf)?;', s)

def _s3(s):
    s = _one(s, 'holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);',
                'holder_key:&Pubkey,sharing:&Pubkey,hf:&mut bool)->Result<Pubkey>{let holder=hopt==Some(true);')
    s = _one(s, ' let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{',
                ' let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*hf=true;*holder_key}else{')
    s = _one(s, 'if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};',
                'if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}*hf=false;t};')
    s = _call(s)
    s = _one(s, '(holder,cashback,target,sharing_update,collect_old,skip)}', '(hf,cashback,target,sharing_update,collect_old,skip)}')
    s = _one(s, 'curve.is_holder_reward=holder.unwrap_or(false);', 'curve.is_holder_reward=_holder;')
    s = _one(s, 'is_holder_reward:a.bonding_curve.is_holder_reward,', 'is_holder_reward:holder.unwrap_or(false),')
    return s
G['S3'] = [_s3]

# h289 (w14a104 #3489): `if st.holder_reward&&!holder` (the original's 289/298 head order)
G['h289'] = [lambda s: _one(s, ' if st.holder_reward&&!(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}',
                               ' if st.holder_reward&&!holder{return Err(error!(PumpError::HolderRewardCreatorImmutable));}')]

# ---- wave-17 shim genes (owner decision 2026-11-01: marked steering constructs allowed in admin_cto.rs) ----
_CDEF = ('Result<Pubkey>{let holder=hopt==Some(true);',
         'Result<Pubkey>{let holder=hopt==Some(true);#[cold]fn cold(){}/*shim: empty #[cold] fn, fully inlined; marks a path cold for the inliner*/')
# C1 (w14a07 c1): cold() at the head of validate's 306 Some arm -> 307/312 to_string call sites cold at V -> outlined
G['C1'] = [_CDEF, ('  let t=if let Some(t)=new{t}else{',
                   '  let t=if let Some(t)=new{cold()/*shim: cold Some arm, 307/312 to_string outline*/;t}else{')]
# C2 (w14a07 c2): cold() inside the 307 and 312 error branches only
G['C2'] = [_CDEF,
  ('if t==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotBeZero)',
   'if t==Pubkey::default(){cold()/*shim: cold 307 error, to_string outline*/;return Err(error!(PumpError::CreatorShouldNotBeZero)'),
  ('if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}',
   'if t==*sharing||t==*holder_key{cold()/*shim: cold 312 error, to_string outline*/;return Err(error!(PumpError::InvalidCreator));}')]
# tf_g3 creator binding alone (w15a21; w17a02 tfc306 = tf + C1: 27,024 B 0.66385 on main 5998913)
G['tf'] = [(_sg.STH2, "{ let creator=a.bonding_curve.creator;" + _sg.STH2[2:]),
           ("else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}",
            "else{target=creator;sharing_update=Some(args.0);(false,true)}}")]
