# w14a138 devolpair genes: w14a119 library (genes_x) + pair genes on the devol338st base
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import genes_x as _X
G=_X.G
def apply(s,names): return _X.apply(s,names)
# ---- validate-local ordinary spellings (devolpair batch 1) ----
_F338='if f==0||f>st.max_fee{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}'
G['q_maxlt']=[(_F338,'if f==0||st.max_fee<f{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}')]
G['q_range']=[(_F338,'if !(f>0&&f<=st.max_fee){return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}')]
G['q_rangec']=[(_F338,'if !(1..=st.max_fee).contains(&f){return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}')]
G['q_lt1']=[(_F338,'if f<1||f>st.max_fee{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}')]
G['q_swap']=[(_F338,'if f>st.max_fee||f==0{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}')]
G['q_cbeq']=[('  if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}','  if cashback==true{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}')]
G['q_qleq']=[('Some(f)=>{if st.quote_locked{return','Some(f)=>{if st.quote_locked==true{return')]
G['q_iflet']=[(' match fee{Some(f)=>{if st.quote_locked{',' if let Some(f)=fee{if st.quote_locked{'),('st.fee_configurable=false;}None=>{}}','st.fee_configurable=false;}')]
G['q_cbexpr']=[(' let cashback=if holder{false}else{st.cashback};',' let cashback=!holder&&st.cashback;')]
G['q_cbst']=[(' let cashback=if holder{false}else{st.cashback};',' let cashback=st.cashback&&!holder;')]
G['q_mayeq']=[(' if st.mayhem{return',' if st.mayhem==true{return')]
G['q_fcneg']=[('if !st.fee_configurable{return','if st.fee_configurable!=true{return')]
G['q_fcmatch']=[('if !st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}','if let false=st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}')]
G['q_fsome']=[(' match fee{Some(f)=>{if st.quote_locked{',' match fee{Some(f) if true=>{if st.quote_locked{')]
G['q_fnone1']=[(' match fee{Some(f)=>{if st.quote_locked{',' match fee{None=>{},Some(f)=>{if st.quote_locked{'),('st.fee_configurable=false;}None=>{}}','st.fee_configurable=false;}}')]
