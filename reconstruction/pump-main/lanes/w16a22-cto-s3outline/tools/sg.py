# w16a13 sutag306 genes: exact single-occurrence (old,new) replacements in admin_cto.rs (line count kept).
# Carriers for the original's 306 test as a bit test on the sharing_update tag (Option<Option<Pubkey>>).
G={}
SIG="fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{"
L306="  let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};"
EX=("let args=&(new,);let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;"
    "let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}"
    "else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),true)};")
STH2="{ let st=CtoState{fee_configurable:a.global.creator_fee_configurable,creator:a.bonding_curve.creator,"
E306="return Err(error!(PumpError::CtoNewCreatorRequired))"
CO="(!st.holder_reward&&st.creator!=Pubkey::default(),true)"

def su_exec(call, nonholder="target=a.bonding_curve.creator;", init="Some(args.0)", pre=""):
    # su-first: sharing_update built from new before validate; arms overwrite Some(None)/None
    return (EX, pre+"let args=&(new,);let sk=a.sharing_config.key();let mut sharing_update:Option<Option<Pubkey>>="+init+";"
            "let mut target="+call+"?;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}"
            "else{"+nonholder+"(false,true)}}else{sharing_update=None;"+CO+"};")

SIG_R=SIG.replace("new:Option<Pubkey>,","new:Option<Pubkey>,su:&Option<Option<Pubkey>>,")
SIG_V=SIG.replace("new:Option<Pubkey>,","new:Option<Pubkey>,su:Option<Option<Pubkey>>,")
CALL_R="validate(&st,hopt,fee,new,&sharing_update,&holder_key,&sk)"
CALL_V="validate(&st,hopt,fee,new,sharing_update,&holder_key,&sk)"

T306={
 # '_' arm (None and Some(None) share the error block)
 'w':"  let t=match *su{Some(Some(t))=>t,_=>"+E306+"};",
 # let-else / if-let
 'le':"  let Some(Some(t))=*su else{"+E306+";};",
 'il':"  let t=if let Some(Some(t))=*su{t}else{"+E306+";};",
 # 3-arm: None / Some(None) / Some(Some) distinct blocks
 'm3':"  let t=match *su{None=>"+E306+",Some(None)=>"+E306+",Some(Some(t))=>t};",
 'm3s':"  let t=match *su{Some(Some(t))=>t,Some(None)=>"+E306+",None=>"+E306+"};",
 # nested match (outer None arm distinct from inner None arm)
 'ne':"  let t=match *su{Some(n)=>match n{Some(t)=>t,None=>"+E306+"},None=>"+E306+"};",
 'ne2':"  let t=match *su{None=>"+E306+",Some(n)=>match n{None=>"+E306+",Some(t)=>t}};",
 # or-pattern
 'op':"  let t=match *su{None|Some(None)=>"+E306+",Some(Some(t))=>t};",
 # flatten
 'fl':"  let t=match su.flatten(){Some(t)=>t,None=>"+E306+"};",
}
for k,v in T306.items():
    G['r'+k]=[(SIG,SIG_R),(L306,v),su_exec(CALL_R)]
    vv=v.replace('*su','su')
    G['v'+k]=[(SIG,SIG_V),(L306,vv),su_exec(CALL_V)]
    # tf_g3 creator binding variants (w15a21): early creator binding + non-holder arm target=creator
    G['tr'+k]=[(STH2,"{ let creator=a.bonding_curve.creator;"+STH2[2:]),(SIG,SIG_R),(L306,v),su_exec(CALL_R,"target=creator;")]
    G['tv'+k]=[(STH2,"{ let creator=a.bonding_curve.creator;"+STH2[2:]),(SIG,SIG_V),(L306,vv),su_exec(CALL_V,"target=creator;")]
G['nop']=[]

# ---- (A) a separate Option<Option<Pubkey>> temporary read only by validate (sharing_update stays main's) ----
VCALL="validate(&st,hopt,fee,new,&holder_key,&sk)?"
def _tmp(call, sig, l306, tf=False):
    eds=[(SIG,sig),(L306,l306),(VCALL,call+"?")]
    if tf: eds=[(STH2,"{ let creator=a.bonding_curve.creator;"+STH2[2:]),
               ("else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}","else{target=creator;sharing_update=Some(args.0);(false,true)}}")]+eds
    return eds
G['mA']=_tmp("validate(&st,hopt,fee,new,&Some(new),&holder_key,&sk)",SIG_R,T306['w'])
G['tA']=_tmp("validate(&st,hopt,fee,new,&Some(new),&holder_key,&sk)",SIG_R,T306['w'],True)
G['mAv']=_tmp("validate(&st,hopt,fee,new,Some(new),&holder_key,&sk)",SIG_V,T306['w'].replace('*su','su'))
G['tAv']=_tmp("validate(&st,hopt,fee,new,Some(new),&holder_key,&sk)",SIG_V,T306['w'].replace('*su','su'),True)
G['tAa']=_tmp("validate(&st,hopt,fee,new,&Some(args.0),&holder_key,&sk)",SIG_R,T306['w'],True)

# ---- (An) test on the Option<Option<Pubkey>> temporary, payload t read from new itself (temp payload dead) ----
TN={'n1':"  let t=match *su{Some(Some(_))=>new.unwrap_or_default(),_=>"+E306+"};",
    'n2':"  let t=match (*su,new){(Some(Some(_)),Some(t))=>t,_=>"+E306+"};",
    'n3':"  let t=match (new,*su){(Some(t),Some(Some(_)))=>t,_=>"+E306+"};",
    'n4':"  let t=if let (Some(Some(_)),Some(t))=(*su,new){t}else{"+E306+";};"}
for k,v in TN.items():
    G['tA'+k]=_tmp("validate(&st,hopt,fee,new,&Some(new),&holder_key,&sk)",SIG_R,v,True)
    G['mA'+k]=_tmp("validate(&st,hopt,fee,new,&Some(new),&holder_key,&sk)",SIG_R,v)
    G['tr'+k]=[(STH2,"{ let creator=a.bonding_curve.creator;"+STH2[2:]),(SIG,SIG_R),(L306,v),su_exec(CALL_R,"target=creator;")]
for k,v in TN.items():
    G['rn'+k[1:]]=[(SIG,SIG_R),(L306,v),su_exec(CALL_R)]   # su-first on main's form

# ---- repay pieces (compose after a carrier) ----
import re as _re
def _one(s,a,b):
    c=s.count(a); assert c==1,(c,a[:100]); return s.replace(a,b)
# Fa (w15a10/#3677): validate reads the args copy of new (entry copy 1/7/8/8/8/1)
G['Fa']=[lambda s:_one(s,'validate(&st,hopt,fee,new,','validate(&st,hopt,fee,args.0,')]
G['Fs']=[lambda s:_one(s,'&Some(new),&holder_key','&Some(args.0),&holder_key')]
# b01 (w15a11): validate takes holder_key by value
_RVm='read_volatile(holder_key as *const Pubkey as *const u8)'
def _b01(s):
    s=_one(s,'holder_key:&Pubkey,sharing:&Pubkey)','holder_key:Pubkey,sharing:&Pubkey)')
    s=_one(s,'&holder_key,&sk)','holder_key,&sk)')
    s=_one(s,'*holder_key}else{','holder_key}else{')
    s=_one(s,'t==*holder_key','t==holder_key')
    if _RVm in s: s=s.replace(_RVm,'read_volatile(&holder_key as *const Pubkey as *const u8)')
    return s
G['b01']=[_b01]
def _v01(s):
    if 'if t==*sharing||t==holder_key{' in s: return _one(s,'if t==*sharing||t==holder_key{','if t==holder_key||t==*sharing{')
    return _one(s,'if t==*sharing||t==*holder_key{','if t==*holder_key||t==*sharing{')
G['v01']=[_v01]

# ---- (B) the args copy is the sharing payload Some(new): args=&(Some(new),); validate reads &args.0; arm sharing_update=args.0 ----
def _B(l306, tf=True, byval=False):
    sig=SIG_V if byval else SIG_R
    call="validate(&st,hopt,fee,new,"+("args.0" if byval else "&args.0")+",&holder_key,&sk)"
    eds=[(SIG,sig),(L306,l306.replace('*su','su') if byval else l306),(VCALL,call+"?"),("let args=&(new,);","let args=&(Some(new),);")]
    if tf: eds=[(STH2,"{ let creator=a.bonding_curve.creator;"+STH2[2:]),
               ("else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}","else{target=creator;sharing_update=args.0;(false,true)}}")]+eds
    else: eds=[("else{sharing_update=Some(args.0);target=","else{sharing_update=args.0;target=")]+eds
    return eds
G['tB1']=_B(T306['w']); G['tB2']=_B(TN['n2']); G['mB2']=_B(TN['n2'],tf=False); G['mB1']=_B(T306['w'],tf=False)
G['tB2v']=_B(TN['n2'],byval=True)

# ---- (I) the update built inside validate (decide-helper class): su local to validate, V screen ----
G['iw']=[(L306,"  let su:Option<Option<Pubkey>>=Some(new);let t=match su{Some(Some(t))=>t,_=>"+E306+"};")]
G['in2']=[(L306,"  let su:Option<Option<Pubkey>>=Some(new);let t=match (su,new){(Some(Some(_)),Some(t))=>t,_=>"+E306+"};")]
G['tiw']=[(STH2,"{ let creator=a.bonding_curve.creator;"+STH2[2:]),("else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}","else{target=creator;sharing_update=Some(args.0);(false,true)}}"),(L306,"  let su:Option<Option<Pubkey>>=Some(new);let t=match su{Some(Some(t))=>t,_=>"+E306+"};")]

# ---- (T) tail-order probes on the tAn2 family: keep payload from new, make the su tests survive as a [2,0] switch ----
TT={'n5':"  let t=match *su{Some(Some(_))=>match new{Some(t)=>t,None=>"+E306+"},_=>"+E306+"};",
    'n6':"  let t=match new{Some(t)=>match *su{Some(Some(_))=>t,_=>"+E306+"},None=>"+E306+"};",
    'n7':"  let t=match (*su,new){(Some(Some(_)),Some(t))=>t,(Some(_),_)=>"+E306+",(None,_)=>"+E306+"};",
    'n8':"  let t=match (*su,new){(None,_)=>"+E306+",(Some(None),_)=>"+E306+",(Some(Some(_)),t)=>if let Some(t)=t{t}else{"+E306+"}};"}
for k,v in TT.items():
    G['tA'+k]=_tmp("validate(&st,hopt,fee,new,&Some(new),&holder_key,&sk)",SIG_R,v,True)
# ov1a (w15a20, OV duplication: validate takes shared, non-holder arm yields st.creator when shared)
def _ov1a(s):
    s=_one(s,'sharing:&Pubkey)->Result<Pubkey>','sharing:&Pubkey,shared:bool)->Result<Pubkey>')
    s=_one(s,'{return Err(error!(PumpError::InvalidCreator));}t};','{return Err(error!(PumpError::InvalidCreator));}if shared{st.creator}else{t}};')
    n=len(_re.findall(r'validate\(([^;]*?),&sk\)\?',s)); assert n==1
    s=_re.sub(r'validate\(([^;]*?),&sk\)\?',r'validate(\1,&sk,shared)?',s)
    return s
G['ov1a']=[_ov1a]

# ---- RA-basin screen on the faithful tA base (payload from the copy) ----
def _ord(names):
    def f(s):
        m=_re.search(r'let (mut )?st=CtoState\{([^}]*)\}',s); assert m
        fs=m.group(2).split(','); d={x.split(':')[0]:x for x in fs}; assert set(d)==set(names),(sorted(d),names)
        return s[:m.start(2)]+','.join(d[n] for n in names)+s[m.end(2):]
    return [f]
G['G51']=_ord(['fee_configurable','cashback','creator','max_fee','mayhem','holder_reward','quote_locked','holder_enabled'])
G['Gc']=_ord(['creator','fee_configurable','max_fee','mayhem','holder_reward','cashback','quote_locked','holder_enabled'])
# 306 temp built from args.0 instead of new (Fs on tA)
G['tAs']=_tmp("validate(&st,hopt,fee,new,&Some(args.0),&holder_key,&sk)",SIG_R,T306['w'],True)
