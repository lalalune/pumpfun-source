# w16a05 skelsplice genes: w15a16 genes_mp library + splice-pair donors
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import genes_mp as _S
G=_S.G
def apply(s,names): return _S.apply(s,names)
_VC='let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;'
G['g1']=[(_VC,'let creator=st.creator;'+_VC),('target=a.bonding_curve.creator;','target=creator;')]
# curve-store spellings of is_holder_reward (break or keep GVN reuse of the validate closure's `and i8 %holder,1`)
_CS='curve.is_holder_reward=holder.unwrap_or(false);'
G['c0s']=[(_CS,'curve.is_holder_reward=holder==Some(true);')]
G['c0m']=[(_CS,'curve.is_holder_reward=matches!(holder,Some(true));')]
G['c0il']=[(_CS,'curve.is_holder_reward=if let Some(h)=holder{h}else{false};')]
G['c0ud']=[(_CS,'curve.is_holder_reward=holder.unwrap_or_default();')]
G['c0ne']=[(_CS,'curve.is_holder_reward=holder!=None&&holder!=Some(false);')]
# shared-arm holder test spellings (RA basin probe on the VC family)
_HN="if shared{if holder{sharing_update=Some(None);(false,false)}else{"
G['t1h']=[(_HN,"if shared{if hopt==Some(true){sharing_update=Some(None);(false,false)}else{")]
G['t1u']=[(_HN,"if shared{if hopt.unwrap_or(false){sharing_update=Some(None);(false,false)}else{")]
G['t1s']=[("if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}","if shared{if new.is_some(){sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}else{sharing_update=Some(None);(false,false)}}")]
