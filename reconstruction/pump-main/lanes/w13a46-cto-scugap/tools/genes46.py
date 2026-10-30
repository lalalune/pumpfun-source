import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import genes30, knobs34
G=dict(genes30.G)
for k,v in knobs34.K.items(): G['k_'+k]=v
def apply(names,src):
    genes30.G.update(G); return genes30.apply(names,src)
# keyed on main 6ff770f7a: inner tuple now (collect_old,sharing_update,skip)
_TQ2 = "let (collect_old,sharing_update,skip)=if shared{if holder{(false,Some(None),false)}else{target=st.creator;(false,Some(args.0),true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)};"
for _o in ('cus','csu','scu','suc','usc','ucs'):
    G['T_'+_o]=[(_TQ2, genes30._tq(_o))]
_A0="let cashback=st.cashback&&!holder;let args=&(new,);let sk=a.sharing_config.key();"
G['A_after_sk']=[(_A0,"let cashback=st.cashback&&!holder;let sk=a.sharing_config.key();let args=&(new,);")]
G['A_after_hopt']=[(_A0,"let cashback=st.cashback&&!holder;let sk=a.sharing_config.key();"),("let hopt=holder;let holder=hopt==Some(true);","let hopt=holder;let args=&(new,);let holder=hopt==Some(true);")]
G['A_after_holder']=[(_A0,"let cashback=st.cashback&&!holder;let sk=a.sharing_config.key();"),("let hopt=holder;let holder=hopt==Some(true);","let hopt=holder;let holder=hopt==Some(true);let args=&(new,);")]
G['A_before_st']=[(_A0,"let cashback=st.cashback&&!holder;let sk=a.sharing_config.key();"),("let st=CtoState{","let args=&(new,);let st=CtoState{")]
G['A_after_val']=[(_A0,"let cashback=st.cashback&&!holder;let sk=a.sharing_config.key();"),("let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;","let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;let args=&(new,);")]
# keyed on main 53abf28b1 (stitch9 pargs)
_PA="let pargs=(target,a.bonding_curve.is_holder_reward,fee);"
G['P_hr']=[(_PA,"let pargs=(target,holder,fee);")]
G['P_hr_call']=[("signer_seeds),pargs.0,pargs.1,pargs.2)?;","signer_seeds),pargs.0,holder,pargs.2)?;")]
G['P_cr']=[(_PA,"let pargs=(a.bonding_curve.creator,a.bonding_curve.is_holder_reward,fee);")]
_A1=(_A0,"let cashback=st.cashback&&!holder;let sk=a.sharing_config.key();")
G['A_top']=[_A1,("->Result<()>{ let a=&ctx.accounts;let mint=a.mint.key();","->Result<()>{ let a=&ctx.accounts;let args=&(new,);let mint=a.mint.key();")]
G['A_before_ql']=[_A1,("let quote_locked=crate::pump_quote","let args=&(new,);let quote_locked=crate::pump_quote")]
G['A_before_hk']=[_A1,("let holder_key;let hk=","let args=&(new,);let holder_key;let hk=")]
G['A_after_ql']=[_A1,("let (holder,cashback,target,sharing_update,collect_old,skip)={","let args=&(new,);let (holder,cashback,target,sharing_update,collect_old,skip)={")]
G['A_after_cb']=[_A1,("let cashback=st.cashback&&!holder;let sk=a.sharing_config.key();let mut target=validate","let cashback=st.cashback&&!holder;let sk=a.sharing_config.key();let args=&(new,);let mut target=validate")]
_QL="let quote_locked=crate::pump_quote::global_quote("
_STB="mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin,"
G['B_cbhrmy']=[(_QL,"let cb0=a.bonding_curve.is_cashback_coin;let hr0=a.bonding_curve.is_holder_reward;let my0=a.bonding_curve.is_mayhem_mode;"+_QL),(_STB,"mayhem:my0,holder_reward:hr0,cashback:cb0,")]
G['B_myhrcb']=[(_QL,"let my0=a.bonding_curve.is_mayhem_mode;let hr0=a.bonding_curve.is_holder_reward;let cb0=a.bonding_curve.is_cashback_coin;"+_QL),(_STB,"mayhem:my0,holder_reward:hr0,cashback:cb0,")]
G['B_tup']=[(_QL,"let (my0,hr0,cb0)=(a.bonding_curve.is_mayhem_mode,a.bonding_curve.is_holder_reward,a.bonding_curve.is_cashback_coin);"+_QL),(_STB,"mayhem:my0,holder_reward:hr0,cashback:cb0,")]
# keyed on main 308b545f1
_A40="let cashback=!holder&&st.cashback;let args=&(new,);let sk=a.sharing_config.key();"
G['A4_bs']=[(_A40,"let cashback=!holder&&st.cashback;let sk=a.sharing_config.key();"),("let st=CtoState{","let args=&(new,);let st=CtoState{")]
G['A4_sk']=[(_A40,"let cashback=!holder&&st.cashback;let sk=a.sharing_config.key();let args=&(new,);")]
_PU4="let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;"
G['U4_keyfn']=[(_PU4,"let pool_updated=!a.pool.data_is_empty() && *a.pool.owner==a.pump_amm.key();")]
G['U4_key']=[(_PU4,"let pool_updated=!a.pool.data_is_empty() && a.pool.owner==a.pump_amm.key;")]
G['U4_ownerfirst']=[(_PU4,"let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();")]
G['U4_keyfn_of']=[(_PU4,"let pool_updated=*a.pool.owner==a.pump_amm.key() && !a.pool.data_is_empty();")]
G['N4_cb']=[("let cashback=!holder&&st.cashback;","let cashback=st.cashback&&!holder;")]
G['E4_nf_back']=[("new_creator_fee_bps:nf,","new_creator_fee_bps:a.bonding_curve.creator_fee_bps,"),(" let nf=a.bonding_curve.creator_fee_bps;let pool_updated"," let pool_updated")]
_TQ4=_TQ2
G['D_scu']=[(_TQ4,"let (skip,collect_old,sharing_update);if shared{if holder{skip=false;collect_old=false;sharing_update=Some(None);}else{target=st.creator;skip=true;collect_old=false;sharing_update=Some(args.0);}}else{skip=true;collect_old=!st.holder_reward&&st.creator!=Pubkey::default();sharing_update=None;}")]
G['D_cus']=[(_TQ4,"let (collect_old,sharing_update,skip);if shared{if holder{collect_old=false;sharing_update=Some(None);skip=false;}else{target=st.creator;collect_old=false;sharing_update=Some(args.0);skip=true;}}else{collect_old=!st.holder_reward&&st.creator!=Pubkey::default();sharing_update=None;skip=true;}")]
G['D_scu_ord']=[(_TQ4,"let (collect_old,sharing_update,skip);if shared{if holder{skip=false;collect_old=false;sharing_update=Some(None);}else{target=st.creator;skip=true;collect_old=false;sharing_update=Some(args.0);}}else{skip=true;collect_old=!st.holder_reward&&st.creator!=Pubkey::default();sharing_update=None;}")]
G['D_skipexpr']=[(_TQ4,"let skip=!(shared&&holder);let (collect_old,sharing_update)=if shared{if holder{(false,Some(None))}else{target=st.creator;(false,Some(args.0))}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),None)};")]
G['D_skipnest']=[(_TQ4,"let (skip,(collect_old,sharing_update))=if shared{if holder{(false,(false,Some(None)))}else{target=st.creator;(true,(false,Some(args.0)))}}else{(true,(!st.holder_reward&&st.creator!=Pubkey::default(),None))};")]
G['D_cusnest']=[(_TQ4,"let ((collect_old,sharing_update),skip)=if shared{if holder{((false,Some(None)),false)}else{target=st.creator;((false,Some(args.0)),true)}}else{((!st.holder_reward&&st.creator!=Pubkey::default(),None),true)};")]
import itertools as _it
def _dg(let_order, asg_order):
    vals={'s':('skip',['false','true','true']),'c':('collect_old',['false','false','!st.holder_reward&&st.creator!=Pubkey::default()']),'u':('sharing_update',['Some(None)','Some(args.0)','None'])}
    def arm(i): return ''.join(f"{vals[x][0]}={vals[x][1][i]};" for x in asg_order)
    lp='('+','.join(vals[x][0] for x in let_order)+')'
    return [(_TQ4,f"let {lp};if shared{{if holder{{{arm(0)}}}else{{target=st.creator;{arm(1)}}}}}else{{{arm(2)}}}")]
for _l in ('scu','csu','cus','usc','suc','ucs'):
    for _a in ('scu','csu','cus','usc','suc','ucs'):
        G[f'DD_{_l}_{_a}']=_dg(_l,_a)
