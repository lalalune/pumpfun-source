#!/usr/bin/env python3
"""closures6.py <crate dir> (after closures5.py): multi-hop sell quote closure in source order.
  673 T  sell hop quote u64::try_from(lib.rs:2454-style quote)   (orig 0x5b3b0 +0x1970, after W0xa0538)
The original evaluates the sell quote inside the sell branch, after the whole buy branch (589..624) and before
SellZeroAmount (686); ours computed it before both branches.  Fee selection is moved into each branch with the
same per-path evaluation order (cap -> [sell quote] -> select_fees -> rates), so values and errors are unchanged.
"""
import sys
from pathlib import Path
S = Path(sys.argv[1]) / 'src'
f = S / 'multi_hop_curve_swap.rs'; t = f.read_text()
def rep(old, new):
    global t
    assert t.count(old) == 1, (old[:90], t.count(old))
    t = t.replace(old, new)
rep('''        let gross_sell = if buy { 0 } else {
            n(div(amount as u128 * c.virtual_quote_reserves as u128,
                c.virtual_token_reserves as u128 + amount as u128)?)?
        };
        let selected = select_fees(a,c,cap,if buy { trade_amount } else { gross_sell })?;
        let p_rate = if flag & 1 != 0 { selected.rates.protocol_fee_bps } else { 0 };
        let c_rate = if flag & 2 != 0 { selected.rates.creator_fee_bps } else { 0 };
        let mut post_fill = None;
        let (base_amount,quote_amount,pf,cf,raw_output) = if buy {
''', '''        let mut post_fill = None;
        let (p_rate,c_rate,base_amount,quote_amount,pf,cf,raw_output) = if buy {
            let selected = select_fees(a,c,cap,trade_amount)?;
            let p_rate = if flag & 1 != 0 { selected.rates.protocol_fee_bps } else { 0 };
            let c_rate = if flag & 2 != 0 { selected.rates.creator_fee_bps } else { 0 };
''')
rep('(capped,first_quote,first_protocol,first_creator,capped.checked_add(post_base)',
    '(p_rate,c_rate,capped,first_quote,first_protocol,first_creator,capped.checked_add(post_base)')
rep('}else{(capped,q,pf,cf,capped)}', '}else{(p_rate,c_rate,capped,q,pf,cf,capped)}')
rep('}else{(base,q,pf,cf,base)}', '}else{(p_rate,c_rate,base,q,pf,cf,base)}')
rep('''        } else {
            let pf = if flag & 1 != 0 { selected.protocol } else { 0 };
            let cf = if flag & 2 != 0 { selected.creator } else { 0 };
            let net = sub(sub(gross_sell,pf)?,cf)?;
            require_gt!(net,0,PumpError::SellZeroAmount);
            (amount,gross_sell,pf,cf,net)
        };
''', '''        } else {
            let gross_sell = u64::try_from(div(amount as u128 * c.virtual_quote_reserves as u128, c.virtual_token_reserves as u128 + amount as u128)?).map_err(|_| error!(PumpError::Truncation))?;
            let selected = select_fees(a,c,cap,gross_sell)?;
            let p_rate = if flag & 1 != 0 { selected.rates.protocol_fee_bps } else { 0 };
            let c_rate = if flag & 2 != 0 { selected.rates.creator_fee_bps } else { 0 };
            let pf = if flag & 1 != 0 { selected.protocol } else { 0 };
            let cf = if flag & 2 != 0 { selected.creator } else { 0 };
            let net = sub(sub(gross_sell,pf)?,cf)?;
            require_gt!(net,0,PumpError::SellZeroAmount);
            (p_rate,c_rate,amount,gross_sell,pf,cf,net)
        };
''')
f.write_text(t)
print('closures6 applied')
