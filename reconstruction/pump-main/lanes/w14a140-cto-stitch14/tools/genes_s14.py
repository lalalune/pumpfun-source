# stitch14 genes: stitch13 library + w14a119 (I6 family, mine108 as m_*) + w14a123 origfill (o_*)
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import genes_s13 as _S
G=_S.G
import genes as _G0
def apply(s,names): return _G0.apply(s,names)
_R='let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r'
G['I6']=[(_R,'target=a.bonding_curve.creator;(false,Some(args.0),true)')]
G['I6s']=[(_R,'target=st.creator;(false,Some(args.0),true)')]
G['I6b']=[(_R,'target=a.bonding_curve.creator;let r=(false,Some(args.0),true);r')]
G['I6sb']=[(_R,'target=st.creator;let r=(false,Some(args.0),true);r')]
import mine108 as _M
for _n,_e in _M.G.items(): G.setdefault('m_'+_n,_e)
import og as _O
for _n,_e in _O.G.items(): G['o_'+_n]=_e
# w14a70 t1 shape: separate `?` on create_idempotent and transfer_vault_tokens (original Err tests)
G['ct']=[("})).and_then(|()|crate::collect_v2::transfer_vault_tokens(","}))?;crate::collect_v2::transfer_vault_tokens("),("amount,&vsigner))?;return Ok(amount);}","amount,&vsigner)?;return Ok(amount);}")]
# w14a118 rw7: wallet coin CPI gate as `if do_coin`
G['rw7']=[("if coin_present&do_coin{","if do_coin{")]
G['rw7b']=[("let do_coin=coin_present&&!token_frozen(a.coin_creator_vault_ata.as_ref())?;","let do_coin=if coin_present{!token_frozen(a.coin_creator_vault_ata.as_ref())?}else{false};"),("if coin_present&do_coin{","if do_coin{")]
# ---- main e88f9d5 (#3621 per-arm sharing_update local) spellings of the shared-tree genes ----
_HN="if shared{if holder{sharing_update=Some(None);(false,false)}else{"
_SN="sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)"
G['t1n']=[(_HN,"if shared{if new.is_none(){sharing_update=Some(None);(false,false)}else{")]
G['t3n']=[(_HN,"if shared{if let None=new{sharing_update=Some(None);(false,false)}else{")]
G['han']=[("if holder{sharing_update=Some(None);(false,false)}","if holder{sharing_update=Some(args.0);(false,false)}")]
G['I6n']=[(_SN,"target=a.bonding_curve.creator;sharing_update=Some(args.0);(false,true)")]
G['I6sn']=[(_SN,"sharing_update=Some(args.0);target=st.creator;(false,true)")]
G['I6ssn']=[(_SN,"target=st.creator;sharing_update=Some(args.0);(false,true)")]
G['sunew']=[(_SN,"sharing_update=Some(new);target=a.bonding_curve.creator;(false,true)")]
