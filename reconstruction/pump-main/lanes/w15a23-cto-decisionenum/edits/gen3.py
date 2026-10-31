import runpy
g=runpy.run_path('common.py'); globals().update({k:v for k,v in g.items() if k.isupper()})
V={}
E6="#[derive(Clone,Copy)]enum Next{Holder,Shared,Wallet{collect:bool}}"
OLD="let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),true)};(holder,cashback,target,sharing_update,collect_old,skip)};let (target,sharing_update,cashback)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback))?;"
NEW="let (target,next)=validate(&st,hopt,fee,new,&holder_key,&sk,shared)?;(holder,cashback,target,next)};let (target,next,cashback)=Ok::<_,anchor_lang::error::Error>((target,next,cashback))?;"
def T(new=NEW): return T0.replace(OLD,new).replace("let (_holder,cashback,target,sharing_update,collect_old,skip)=","let (_holder,cashback,target,next)=")
VS=VSIG.replace("sharing:&Pubkey)->Result<Pubkey>{","sharing:&Pubkey,shared:bool)->Result<(Pubkey,Next)>{")
C6=[(STRUCT,STRUCT+E6),(COLL," if let Next::Wallet{collect:true}=next{wallet(&ctx)?;}"),
 (SW," swept=matches!(next,Next::Holder).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);"),
 (RST,"sharing_config_reset:!matches!(next,Next::Wallet{..}),"),
 (SH0," match match next{Next::Holder=>Some(None),Next::Shared=>Some(new),Next::Wallet{..}=>None}{Some(val)=>{\n")]
R1=" Ok(if shared{if holder{(target,Next::Holder)}else{(st.creator,Next::Shared)}}else{(target,Next::Wallet{collect:!st.holder_reward&&st.creator!=Pubkey::default()})})}pub fn execute"
V['v1']=[(VSIG,VS),(VRET,R1),(T0,T())]+C6
R2=" let next=if shared{if holder{Next::Holder}else{target=st.creator;Next::Shared}}else{Next::Wallet{collect:!st.holder_reward&&st.creator!=Pubkey::default()}};Ok((target,next))}pub fn execute"
V['v2']=[(VSIG,VS),(VRET,R2),(" let target=if holder{if new.is_some()"," let mut target=if holder{if new.is_some()"),(T0,T())]+C6
for k,v in V.items():
    open(k+'.py','w').write('EDITS='+repr(v)+'\n')
print(list(V))
