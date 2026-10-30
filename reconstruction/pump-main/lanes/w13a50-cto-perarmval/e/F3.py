import sys; sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a50-cto-perarmval/e')
from common import *
# F1 + holder out-param phi (h2 form)
EDITS=[SIG,(L298,L298.replace(ERR298+'*holder_key',ERR298+'fee_ok(st,fee,false)?;*ho=true;*holder_key')),(L312,L312.replace('}t};','}fee_ok(st,fee,st.cashback)?;t};')),(L314,FEEFN),END,EXH2,STORES,POOL2]
