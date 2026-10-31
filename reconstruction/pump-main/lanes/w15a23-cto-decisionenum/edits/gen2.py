import runpy
g=runpy.run_path('common.py'); globals().update({k:v for k,v in g.items() if k.isupper()})
G1=runpy.run_path('gen1.py') if False else None
V={}
def t_exec(nextexpr,keep_su=False):
    old="let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),true)};(holder,cashback,target,sharing_update,collect_old,skip)};let (target,sharing_update,cashback)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback))?;"
    if keep_su:
        new="let mut sharing_update:Option<Option<Pubkey>>=None;let next="+nextexpr+";(holder,cashback,target,sharing_update,next)};let (target,sharing_update,cashback)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback))?;"
        return T0.replace(old,new).replace("let (_holder,cashback,target,sharing_update,collect_old,skip)=","let (_holder,cashback,target,sharing_update,next)=")
    new="let next="+nextexpr+";(holder,cashback,target,next)};let (target,next,cashback)=Ok::<_,anchor_lang::error::Error>((target,next,cashback))?;"
    return T0.replace(old,new).replace("let (_holder,cashback,target,sharing_update,collect_old,skip)=","let (_holder,cashback,target,next)=")
# d5: payload-less tail gate enum; sharing_update kept
E5="#[derive(Clone,Copy,PartialEq)]enum Tail{Sweep,Neither,Collect}"
N5="if shared{if holder{sharing_update=Some(None);Tail::Sweep}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;Tail::Neither}}else if !st.holder_reward&&st.creator!=Pubkey::default(){Tail::Collect}else{Tail::Neither}"
C5=[(STRUCT,STRUCT+E5),(COLL," if next==Tail::Collect{wallet(&ctx)?;}"),(SW," swept=(next==Tail::Sweep).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);")]
V['d5']=[(T0,t_exec(N5,True))]+C5
C5m=[(STRUCT,STRUCT+E5),(COLL," if let Tail::Collect=next{wallet(&ctx)?;}"),(SW," swept=matches!(next,Tail::Sweep).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);")]
V['d5m']=[(T0,t_exec(N5,True))]+C5m
# d6: payload-less 3-variant decision; payload from new arg
E6="#[derive(Clone,Copy)]enum Next{Holder,Shared,Wallet{collect:bool}}"
N6="if shared{if holder{Next::Holder}else{target=a.bonding_curve.creator;Next::Shared}}else{Next::Wallet{collect:!st.holder_reward&&st.creator!=Pubkey::default()}}"
C6=[(STRUCT,STRUCT+E6),(COLL," if let Next::Wallet{collect:true}=next{wallet(&ctx)?;}"),
 (SW," swept=matches!(next,Next::Holder).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);"),
 (RST,"sharing_config_reset:!matches!(next,Next::Wallet{..}),")]
V['d6b']=[(T0,t_exec(N6))]+C6+[(SH0," match match next{Next::Holder=>Some(None),Next::Shared=>Some(new),Next::Wallet{..}=>None}{Some(val)=>{\n")]
V['d6a']=[(T0,t_exec(N6))]+C6+[(SH0," match next{Next::Holder|Next::Shared=>{let val=if let Next::Shared=next{new}else{None};\n"),(SH1," }Next::Wallet{..}=>{}}\n")]
# d6 with reset from shared (known knob ev_reset_shared idea) 
V['d6b_rs']=[(T0,t_exec(N6))]+[c if c[0]!=RST else (RST,"sharing_config_reset:shared,") for c in C6]+[(SH0," match match next{Next::Holder=>Some(None),Next::Shared=>Some(new),Next::Wallet{..}=>None}{Some(val)=>{\n")]
for k,v in V.items():
    open(k+'.py','w').write('EDITS='+repr(v)+'\n')
print(list(V))
