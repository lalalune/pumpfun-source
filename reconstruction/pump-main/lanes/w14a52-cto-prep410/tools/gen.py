import json,os
E=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a52-cto-prep410/e')
T0="let (collect_old,sharing_update,skip)=if shared{if holder{(false,Some(None),false)}else{target=st.creator;(false,Some(args.0),true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)};(holder,cashback,target,sharing_update,collect_old,skip)};"
OK0="let (target,sharing_update,cashback)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback))?;"
P0=" crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.admin_set_creator_authority)?;"
R0=" require!(a.bonding_curve.creator_fee==0,PumpError::CreatorFeesNotSwept);"
V={}
def t(body): return [(T0,body+"(holder,cashback,target,sharing_update,collect_old,skip)};")]
V['t_sep']=t("let collect_old=!shared&&!st.holder_reward&&st.creator!=Pubkey::default();let skip=!(shared&&holder);let sharing_update=if shared{if holder{Some(None)}else{target=st.creator;Some(args.0)}}else{None};")
V['t_sep2']=t("let sharing_update=if shared{if holder{Some(None)}else{target=st.creator;Some(args.0)}}else{None};let collect_old=!shared&&!st.holder_reward&&st.creator!=Pubkey::default();let skip=!(shared&&holder);")
V['t_ord_suf']=t("let (sharing_update,collect_old,skip)=if shared{if holder{(Some(None),false,false)}else{target=st.creator;(Some(args.0),false,true)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default(),true)};")
V['t_ord_scs']=t("let (skip,collect_old,sharing_update)=if shared{if holder{(false,false,Some(None))}else{target=st.creator;(true,false,Some(args.0))}}else{(true,!st.holder_reward&&st.creator!=Pubkey::default(),None)};")
V['t_ord_ssc']=t("let (sharing_update,skip,collect_old)=if shared{if holder{(Some(None),false,false)}else{target=st.creator;(Some(args.0),true,false)}}else{(None,true,!st.holder_reward&&st.creator!=Pubkey::default())};")
V['t_coif']=t("let (collect_old,sharing_update,skip)=if shared{if holder{(false,Some(None),false)}else{target=st.creator;(false,Some(args.0),true)}}else{(if st.holder_reward{false}else{st.creator!=Pubkey::default()},None,true)};")
V['t_comem']=t("let (collect_old,sharing_update,skip)=if shared{if holder{(false,Some(None),false)}else{target=st.creator;(false,Some(args.0),true)}}else{(st.creator!=Pubkey::default()&&!st.holder_reward,None,true)};")
V['t_coand']=t("let (collect_old,sharing_update,skip)=if shared{if holder{(false,Some(None),false)}else{target=st.creator;(false,Some(args.0),true)}}else{(!st.holder_reward&(st.creator!=Pubkey::default()),None,true)};")
V['t_codefl']=t("let (collect_old,sharing_update,skip)=if shared{if holder{(false,Some(None),false)}else{target=st.creator;(false,Some(args.0),true)}}else{(!st.holder_reward&&Pubkey::default()!=st.creator,None,true)};")
V['t_notsh']=t("let (collect_old,sharing_update,skip)=if !shared{(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)}else if holder{(false,Some(None),false)}else{target=st.creator;(false,Some(args.0),true)};")
V['t_match']=t("let (collect_old,sharing_update,skip)=match (shared,holder){(true,true)=>(false,Some(None),false),(true,false)=>{target=st.creator;(false,Some(args.0),true)}(false,_)=>(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)};")
V['t_hnot']=t("let (collect_old,sharing_update,skip)=if shared{if !holder{target=st.creator;(false,Some(args.0),true)}else{(false,Some(None),false)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)};")
V['t_new']=t("let (collect_old,sharing_update,skip)=if shared{if holder{(false,Some(None),false)}else{target=st.creator;(false,Some(new),true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)};")
V['t_tgtlate']=t("let (collect_old,sharing_update,skip)=if shared{if holder{(false,Some(None),false)}else{(false,Some(args.0),true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)};if shared&&!holder{target=st.creator;}")
V['t_tgtexpr']=[("let mut target=validate(","let target=validate("),(T0,"let (target,collect_old,sharing_update,skip)=if shared{if holder{(target,false,Some(None),false)}else{(st.creator,false,Some(args.0),true)}}else{(target,!st.holder_reward&&st.creator!=Pubkey::default(),None,true)};(holder,cashback,target,sharing_update,collect_old,skip)};")]
V['t_skipexpr']=t("let skip=!shared||!holder;let (collect_old,sharing_update)=if shared{if holder{(false,Some(None))}else{target=st.creator;(false,Some(args.0))}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),None)};")
V['ok_ord_stc']=[(OK0,"let (sharing_update,target,cashback)=Ok::<_,anchor_lang::error::Error>((sharing_update,target,cashback))?;")]
V['ok_ord_tcs']=[(OK0,"let (target,cashback,sharing_update)=Ok::<_,anchor_lang::error::Error>((target,cashback,sharing_update))?;")]
V['ok_ord_cst']=[(OK0,"let (cashback,sharing_update,target)=Ok::<_,anchor_lang::error::Error>((cashback,sharing_update,target))?;")]
V['ok_co']=[(OK0,"let (target,sharing_update,cashback,collect_old)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback,collect_old))?;")]
V['ok_skip']=[(OK0,"let (target,sharing_update,cashback,skip)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback,skip))?;")]
V['ok_tonly']=[(OK0,"let (target,)=Ok::<_,anchor_lang::error::Error>((target,))?;")]
V['p_ctx']=[(P0," crate::trade_types::prepare_bonding_curve(&ctx.accounts.bonding_curve,&ctx.accounts.system_program,&ctx.accounts.admin_set_creator_authority)?;")]
V['p_bind']=[(P0+"\n"," let curve=&a.bonding_curve;crate::trade_types::prepare_bonding_curve(curve,&a.system_program,&a.admin_set_creator_authority)?;\n")]
V['p_beforeok']=[(OK0+"let mut target=target;"+P0,P0[1:]+OK0+"let mut target=target; ")]
V['p_inblk']=[("(holder,cashback,target,sharing_update,collect_old,skip)};","crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.admin_set_creator_authority)?;(holder,cashback,target,sharing_update,collect_old,skip)};"),(P0," ")]
V['r_if']=[(R0," if a.bonding_curve.creator_fee!=0{return Err(error!(PumpError::CreatorFeesNotSwept));}")]
V['r_ifgt']=[(R0," if a.bonding_curve.creator_fee>0{return Err(error!(PumpError::CreatorFeesNotSwept));}")]
V['r_ne']=[(R0," require!(a.bonding_curve.creator_fee<1,PumpError::CreatorFeesNotSwept);")]
V['r_tmp']=[(R0," let cf=a.bonding_curve.creator_fee;require!(cf==0,PumpError::CreatorFeesNotSwept);")]
for k,v in V.items():
    open(f'{E}/{k}.py','w').write('EDITS='+json.dumps(v)+'\n')
print(' '.join(V))
