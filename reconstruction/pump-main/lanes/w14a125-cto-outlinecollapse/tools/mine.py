G={}
_H="->Result<Pubkey>{let holder=hopt==Some(true);"
G['v_uo']=[(_H,"->Result<Pubkey>{let holder=hopt.unwrap_or(false);")]
G['v_mt']=[(_H,"->Result<Pubkey>{let holder=matches!(hopt,Some(true));")]
G['v_ud']=[(_H,"->Result<Pubkey>{let holder=hopt.unwrap_or_default();")]
G['v_isa']=[(_H,"->Result<Pubkey>{let holder=hopt.is_some_and(|h|h);")]
G['nop']=[]
_S="fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);"
_E="let hopt=holder;let holder=hopt==Some(true);"
_C="validate(&st,hopt,fee,new,&holder_key,&sk)"
_289="if st.holder_reward&&!(hopt==Some(true)){"
_284=" if st.mayhem{return Err(error!(PumpError::CtoNotAllowedForMayhemCoin));}"
# validate takes the bool
G['c_vb']=[(_S,"fn validate(st:&CtoState,holder:bool,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{"),(_289,"if st.holder_reward&&!holder{"),(_C,"validate(&st,holder,fee,new,&holder_key,&sk)")]
G['c_vbu']=G['c_vb']+[(_E,"let hopt=holder;let holder=hopt.unwrap_or(false);")]
# holder after the mayhem test
G['c_mh']=[(_S,_S.replace("let holder=hopt==Some(true);","")),(_284,_284+"let holder=hopt.unwrap_or(false);")]
G['c_mh289']=G['c_mh']+[(_289,"if st.holder_reward&&!holder{")]
G['c_uo289']=G['v_uo']+[(_289,"if st.holder_reward&&!holder{")]
G['c_uoe']=G['v_uo']+[(_E,"let hopt=holder;let holder=hopt.unwrap_or(false);")]
G['c_tup']=[(_S,_S.replace("let holder=hopt==Some(true);","let (holder,)=(hopt.unwrap_or(false),);"))]
G['c_ifl']=[(_S,_S.replace("let holder=hopt==Some(true);","let holder=if let Some(h)=hopt{h}else{false};"))]
G['c_m3']=[(_S,_S.replace("let holder=hopt==Some(true);","let holder=match hopt{Some(h)=>h,None=>false};"))]
G['c_m3n']=[(_S,_S.replace("let holder=hopt==Some(true);","let holder=match hopt{None=>false,Some(h)=>h};"))]
_SD="holder_reward:bool,cashback:bool,quote_locked:bool,holder_enabled:bool,fee_configurable:bool}"
G['c_fo']=G['v_uo']+[(_SD,"holder_enabled:bool,holder_reward:bool,cashback:bool,quote_locked:bool,fee_configurable:bool}")]
G['c_ro']=G['v_uo']+[("if holder&&!st.holder_reward&&!st.holder_enabled{","if holder&&!st.holder_enabled&&!st.holder_reward{")]
