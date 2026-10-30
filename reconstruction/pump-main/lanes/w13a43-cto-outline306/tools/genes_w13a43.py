# w13a43 genes; append to w13a17's tools/genes.py (E dict)
E={}
# ---- w13a43-cto-outline306 genes
E['T289']=[("if st.holder_reward&&!(hopt==Some(true)){","if st.holder_reward&&!holder{")]
E['T289N']=[("if st.holder_reward&&!(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}","if st.holder_reward{if !holder{return Err(error!(PumpError::HolderRewardCreatorImmutable));}}")]
E['T296']=[("if holder&&!st.holder_reward&&!st.holder_enabled{","if holder&&!(st.holder_reward||st.holder_enabled){")]
_L289="if st.holder_reward&&!(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}"
E['T289D']=[(_L289,"if st.holder_reward{if holder{}else{return Err(error!(PumpError::HolderRewardCreatorImmutable));}}")]
E['T289M']=[(_L289,"match (st.holder_reward,holder){(true,false)=>return Err(error!(PumpError::HolderRewardCreatorImmutable)),_=>{}}")]
E['T289G']=[(_L289,"if st.holder_reward{if !(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}}")]
E['ANEW']=[("(Some(args.0),false,true)","(Some(new),false,true)"),("let args=&(new,);","")]
E['ANEWK']=[("(Some(args.0),false,true)","(Some(new),false,true)")]
E['ARGL']=[("let args=&(new,);",""),("let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;","let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;let args=&(new,);")]
E['HB3']=[("fn validate(st:&CtoState,hopt:Option<bool>,","fn validate(st:&CtoState,hb:&bool,hopt:Option<bool>,"),("Result<Pubkey>{let holder=hopt==Some(true);","Result<Pubkey>{let holder=*hb;"),("validate(&st,hopt,fee,new,&holder_key,&sk)","validate(&st,&holder,hopt,fee,new,&holder_key,&sk)")]
E['SU1']=[("let args=&(new,);","let su=Some(new);"),("(Some(args.0),false,true)","(su,false,true)")]
E['SU2']=[("let args=&(new,);","let su=&Some(new);"),("(Some(args.0),false,true)","(*su,false,true)")]
