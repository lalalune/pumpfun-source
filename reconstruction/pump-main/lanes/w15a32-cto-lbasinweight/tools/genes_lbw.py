# w15a32 lbasinweight genes: w15a16 genes_mp library + entry-argument use spellings on the L basin
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import genes_mp as _S
G=_S.G
def apply(s,names): return _S.apply(s,names)
_XH='let hopt=holder;let holder=hopt==Some(true);let cashback=!holder&&st.cashback;'
G['xcb_if']=[(_XH,'let hopt=holder;let holder=hopt==Some(true);let cashback=if holder{false}else{st.cashback};')]
G['xcb_and']=[(_XH,'let hopt=holder;let holder=hopt==Some(true);let cashback=st.cashback&&!holder;')]
G['xh_uo']=[(_XH,'let hopt=holder;let holder=hopt.unwrap_or(false);let cashback=!holder&&st.cashback;')]
G['xh_mt']=[(_XH,'let hopt=holder;let holder=matches!(hopt,Some(true));let cashback=!holder&&st.cashback;')]
G['xh_ud']=[(_XH,'let hopt=holder;let holder=hopt.unwrap_or_default();let cashback=!holder&&st.cashback;')]
G['xh_cbfirst']=[(_XH,'let hopt=holder;let cashback=!(hopt==Some(true))&&st.cashback;let holder=hopt==Some(true);')]
_XV='let cashback=!holder&&st.cashback;let args=&(new,);let sk=a.sharing_config.key();let mut target=validate(&mut st,hopt,fee,new,&holder_key,&sk)?;'
G['xcb_late']=[(_XV,'let args=&(new,);let sk=a.sharing_config.key();let mut target=validate(&mut st,hopt,fee,new,&holder_key,&sk)?;let cashback=!holder&&st.cashback;')]
G['xcb_late2']=[(_XV,'let args=&(new,);let sk=a.sharing_config.key();let mut target=validate(&mut st,hopt,fee,new,&holder_key,&sk)?;let cashback=if holder{false}else{st.cashback};')]
_VF='match fee{Some(f)=>{if st.quote_locked{'
G['vf_iflet']=[(_VF,'if let Some(f)=fee{if st.quote_locked{'),('st.fee_configurable=false;}None=>{}}','st.fee_configurable=false;}')]
G['vf_range']=[('if f==0||f>st.max_fee{','if !(1..=st.max_fee).contains(&f){')]
G['vf_gt0']=[('if f==0||f>st.max_fee{','if f<1||f>st.max_fee{')]
G['vf_swap']=[('if f==0||f>st.max_fee{','if f>st.max_fee||f==0{')]
G['c0eq']=[('curve.is_holder_reward=holder.unwrap_or(false);','curve.is_holder_reward=holder==Some(true);')]
G['vcb_and']=[('let cashback=if holder{false}else{st.cashback};','let cashback=!holder&&st.cashback;')]
