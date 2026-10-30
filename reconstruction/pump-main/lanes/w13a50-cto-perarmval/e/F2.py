import sys; sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a50-cto-perarmval/e')
from common import *
# F1 with fee helper taking &CtoState fields by value (quote_locked,fee_configurable,max_fee) not st
FEEFN2=' fn fee_ok(fee:Option<u64>,ql:bool,cashback:bool,fc:bool,mx:u64)->Result<()>{'
EDITS=[(L298,L298.replace(ERR298+'*holder_key',ERR298+'fee_ok(fee,st.quote_locked,false,st.fee_configurable,st.max_fee)?;*holder_key')),(L312,L312.replace('}t};','}fee_ok(fee,st.quote_locked,st.cashback,st.fee_configurable,st.max_fee)?;t};')),(L314,FEEFN2),END,
 ('if st.quote_locked{return Err(error!(PumpError::CreatorFeeNotConfigurableForQuote));}','if ql{return Err(error!(PumpError::CreatorFeeNotConfigurableForQuote));}'),
 ('if !st.fee_configurable{','if !fc{'),('if f==0||f>st.max_fee{','if f==0||f>mx{')]
