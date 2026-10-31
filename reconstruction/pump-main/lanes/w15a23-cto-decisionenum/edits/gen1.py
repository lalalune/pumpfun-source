import runpy,os
g=runpy.run_path('common.py'); globals().update({k:v for k,v in g.items() if k.isupper()})
V={}
E3="#[derive(Clone,Copy)]enum Next{Holder,Shared(Option<Pubkey>),Wallet{collect:bool}}"
def t_exec(nextexpr):
    return T0.replace("let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),true)};(holder,cashback,target,sharing_update,collect_old,skip)};let (target,sharing_update,cashback)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback))?;",
      "let next="+nextexpr+";(holder,cashback,target,next)};let (target,next,cashback)=Ok::<_,anchor_lang::error::Error>((target,next,cashback))?;").replace("let (_holder,cashback,target,sharing_update,collect_old,skip)=","let (_holder,cashback,target,next)=")
N3="if shared{if holder{Next::Holder}else{target=a.bonding_curve.creator;Next::Shared(args.0)}}else{Next::Wallet{collect:!st.holder_reward&&st.creator!=Pubkey::default()}}"
COMMON3=[(STRUCT,STRUCT+E3),(COLL," if let Next::Wallet{collect:true}=next{wallet(&ctx)?;}"),
 (SW," swept=matches!(next,Next::Holder).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);"),
 (RST,"sharing_config_reset:!matches!(next,Next::Wallet{..}),")]
# sharing forms
SHa=[(SH0," match next{Next::Holder|Next::Shared(_)=>{let val=if let Next::Shared(v)=next{v}else{None};\n"),(SH1," }Next::Wallet{..}=>{}}\n")]
SHb=[(SH0," match match next{Next::Holder=>Some(None),Next::Shared(v)=>Some(v),Next::Wallet{..}=>None}{Some(val)=>{\n")]
SHc=[(SH0," match next{Next::Wallet{..}=>{}n=>{let val=if let Next::Shared(v)=n{v}else{None};\n"),(SH1," }}\n")]
SHd=[(SH0," if let Some(val)=match next{Next::Holder=>Some(None),Next::Shared(v)=>Some(v),Next::Wallet{..}=>None}{\n"),(SH1," }\n")]
V['d1a']=[(T0,t_exec(N3))]+COMMON3+SHa
V['d1b']=[(T0,t_exec(N3))]+COMMON3+SHb
V['d1c']=[(T0,t_exec(N3))]+COMMON3+SHc
V['d1d']=[(T0,t_exec(N3))]+COMMON3+SHd
# event reset from match
V['d1b_rm']=[(T0,t_exec(N3))]+[c if c[0]!=RST else (RST,"sharing_config_reset:match next{Next::Wallet{..}=>false,_=>true},") for c in COMMON3]+SHb
# collect via matches!
V['d1b_cm']=[(T0,t_exec(N3))]+[c if c[0]!=COLL else (COLL," if matches!(next,Next::Wallet{collect:true}){wallet(&ctx)?;}") for c in COMMON3]+SHb
# sweep via if-let expression
V['d1b_sif']=[(T0,t_exec(N3))]+[c if c[0]!=SW else (SW," swept=if let Next::Holder=next{sweep(&ctx,&holder_key)?}else{0};") for c in COMMON3]+SHb
# 4-variant enum carrying holder
E4="#[derive(Clone,Copy)]enum Next{SharedHolder,SharedNew(Option<Pubkey>),Holder{collect:bool},New{collect:bool}}"
N4="{let collect=!st.holder_reward&&st.creator!=Pubkey::default();if shared{if holder{Next::SharedHolder}else{target=a.bonding_curve.creator;Next::SharedNew(args.0)}}else if holder{Next::Holder{collect}}else{Next::New{collect}}}"
C4=[(STRUCT,STRUCT+E4),(COLL," if let Next::Holder{collect:true}|Next::New{collect:true}=next{wallet(&ctx)?;}"),
 (SW," swept=matches!(next,Next::SharedHolder).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);"),
 (RST,"sharing_config_reset:matches!(next,Next::SharedHolder|Next::SharedNew(_)),"),
 (SH0," match match next{Next::SharedHolder=>Some(None),Next::SharedNew(v)=>Some(v),_=>None}{Some(val)=>{\n")]
V['d4']=[(T0,t_exec(N4))]+C4
V['d4_hr']=[(T0,t_exec(N4))]+C4+[(HR,"  curve.is_holder_reward=matches!(next,Next::SharedHolder|Next::Holder{..});")]
for k,v in V.items():
    open(k+'.py','w').write('EDITS='+repr(v)+'\n')
print(list(V))
