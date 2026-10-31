import runpy
g=runpy.run_path('common.py'); globals().update({k:v for k,v in g.items() if k.isupper()})
V={}
OLDT="let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),true)};(holder,cashback,target,sharing_update,collect_old,skip)};"
HEAD="let (_holder,cashback,target,sharing_update,collect_old,skip)="
WCALL=" if collect_old{wallet(&ctx)?;}fn wallet"
SWC=" swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);fn sweep"
# d7: payload-less tail enum, single match dispatch at the sweep site
E5="#[derive(Clone,Copy)]enum Tail{Sweep,Neither,Collect}"
N7="let mut sharing_update:Option<Option<Pubkey>>=None;let tail=if shared{if holder{sharing_update=Some(None);Tail::Sweep}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;Tail::Neither}}else if !st.holder_reward&&st.creator!=Pubkey::default(){Tail::Collect}else{Tail::Neither};(holder,cashback,target,sharing_update,tail)};"
B7=[(STRUCT,STRUCT+E5),(T0,T0.replace(OLDT,N7).replace(HEAD,"let (_holder,cashback,target,sharing_update,tail)=")),(WCALL," fn wallet")]
V['d7']=B7+[(SWC," swept=match tail{Tail::Collect=>{wallet(&ctx)?;0}Tail::Sweep=>sweep(&ctx,&holder_key)?,Tail::Neither=>0};fn sweep")]
V['d7b']=B7+[(SWC," swept=match tail{Tail::Sweep=>sweep(&ctx,&holder_key)?,Tail::Collect=>{wallet(&ctx)?;0}Tail::Neither=>0};fn sweep")]
V['d7c']=B7+[(SWC," swept=match tail{Tail::Neither=>0,Tail::Sweep=>sweep(&ctx,&holder_key)?,Tail::Collect=>{wallet(&ctx)?;0}};fn sweep")]
# d9: isomorphic 2-variant sharing enum replacing Option<Option<Pubkey>>
E9="#[derive(Clone,Copy)]enum Sharing{Reset(Option<Pubkey>),Keep}"
V['d9']=[(STRUCT,STRUCT+E9),(T0,T0.replace("let mut sharing_update:Option<Option<Pubkey>>=None;","let mut sharing_update=Sharing::Keep;").replace("sharing_update=Some(None);","sharing_update=Sharing::Reset(None);").replace("sharing_update=Some(args.0);","sharing_update=Sharing::Reset(args.0);")),
 (SH0," match sharing_update{Sharing::Reset(val)=>{\n"),(SH1," }Sharing::Keep=>{}}\n"),(RST,"sharing_config_reset:matches!(sharing_update,Sharing::Reset(_)),")]
# d8: 2-variant decision enum, tag {0,1,2} like orig 0x8f8: Shared(Option<Pubkey>) / Unshared{collect}
E8="#[derive(Clone,Copy)]enum Next{Shared(Option<Pubkey>),Unshared{collect:bool}}"
N8="let next=if shared{if holder{Next::Shared(None)}else{target=a.bonding_curve.creator;Next::Shared(args.0)}}else{Next::Unshared{collect:!st.holder_reward&&st.creator!=Pubkey::default()}};(holder,cashback,target,next)};"
V['d8']=[(STRUCT,STRUCT+E8),(T0,T0.replace(OLDT,N8).replace(HEAD,"let (_holder,cashback,target,next)=").replace("let (target,sharing_update,cashback)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback))?;","let (target,next,cashback)=Ok::<_,anchor_lang::error::Error>((target,next,cashback))?;")),
 (COLL," if let Next::Unshared{collect:true}=next{wallet(&ctx)?;}"),(SW," swept=matches!(next,Next::Shared(None)).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);"),
 (SH0," match next{Next::Shared(val)=>{\n"),(SH1," }Next::Unshared{..}=>{}}\n"),(RST,"sharing_config_reset:matches!(next,Next::Shared(_)),")]
for k,v in V.items():
    open(k+'.py','w').write('EDITS='+repr(v)+'\n')
print(list(V))
