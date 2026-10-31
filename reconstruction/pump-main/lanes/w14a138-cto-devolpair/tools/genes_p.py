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
# ---- state-field local bindings in validate (devolpair batch 3) ----
_HR=' let hr=st.holder_reward;if hr&&'
_FC='if !st.fee_configurable{return'
_MX='if f==0||f>st.max_fee{return'
G['h_fc0']=[(_HR,' let hr=st.holder_reward;let fc=st.fee_configurable;if hr&&'),(_FC,'if !fc{return')]
G['h_mx0']=[(_HR,' let hr=st.holder_reward;let mx=st.max_fee;if hr&&'),(_MX,'if f==0||f>mx{return')]
G['h_fcmx0']=G['h_fc0']+[(_MX,'if f==0||f>mx{return')]
G['h_fcmx0']=[(_HR,' let hr=st.holder_reward;let fc=st.fee_configurable;let mx=st.max_fee;if hr&&'),(_FC,'if !fc{return'),(_MX,'if f==0||f>mx{return')]
G['h_mxa']=[(' match fee{Some(f)=>{if st.quote_locked{',' match fee{Some(f)=>{let mx=st.max_fee;if st.quote_locked{'),(_MX,'if f==0||f>mx{return')]
G['h_fca']=[(' match fee{Some(f)=>{if st.quote_locked{',' match fee{Some(f)=>{let fc=st.fee_configurable;if st.quote_locked{'),(_FC,'if !fc{return')]
G['h_mx334']=[(_FC,'let mx=st.max_fee;if !st.fee_configurable{return'),(_MX,'if f==0||f>mx{return')]
G['h_ql0']=[(_HR,' let hr=st.holder_reward;let ql=st.quote_locked;if hr&&'),('Some(f)=>{if st.quote_locked{','Some(f)=>{if ql{')]
G['h_cb0']=[(_HR,' let hr=st.holder_reward;let cb=st.cashback;if hr&&'),(' let cashback=if holder{false}else{st.cashback};',' let cashback=if holder{false}else{cb};')]
G['h_may0']=[(' if st.mayhem{return',' let may=st.mayhem;if may{return')]
G['h_he0']=[(_HR,' let hr=st.holder_reward;let he=st.holder_enabled;if hr&&'),('if holder&&!hr&&!st.holder_enabled{','if holder&&!hr&&!he{')]
_I0='let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r'
G['I6n']=[(_I0,'target=a.bonding_curve.creator;(false,Some(new),true)')]
G['I6nb']=[(_I0,'let r=(false,Some(new),true);target=a.bonding_curve.creator;r')]
G['I6a']=[(_I0,'target=a.bonding_curve.creator;(false,Some(*&args.0),true)')]
G['I6t']=[(_I0,'target=a.bonding_curve.creator;let s=Some(args.0);(false,s,true)')]
G['I6st']=[(_I0,'let s=Some(args.0);target=a.bonding_curve.creator;(false,s,true)')]
# ---- main 90300f9 (#3621 vinarm: per-arm sharing_update local) analogues of I6 / I6s ----
_N0='sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)'
G['N6']=[(_N0,'target=a.bonding_curve.creator;sharing_update=Some(args.0);(false,true)')]
G['N6s']=[(_N0,'target=st.creator;sharing_update=Some(args.0);(false,true)')]
G['N0s']=[(_N0,'sharing_update=Some(args.0);target=st.creator;(false,true)')]
G['N6h']=[('if holder{sharing_update=Some(None);(false,false)}','if holder{sharing_update=Some(None);(false,false)}')]
_V334='unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};if !st.fee_configurable{'
G['st334m']=[(_V334,'st.mayhem=false;if !st.fee_configurable{')]
G['st334f']=[(_V334,'st.max_fee=1;if !st.fee_configurable{')]
