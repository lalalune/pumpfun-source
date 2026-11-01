#!/usr/bin/env python3
"""mk.py <trial> <edit1> [edit2 ...]: copy worktree programs/pump to src/<trial>, apply x1 patch? no: edits are named functions in EDITS."""
import sys, os, shutil, subprocess
WT='./worktrees/w10r1-swaphop-stitch'
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w10r1-swaphop-stitch')
F='src/multi_hop_curve_swap.rs'
def R(old,new,count=1):
    def f(t):
        assert t.count(old)>=1, ('missing',old[:80])
        return t.replace(old,new,count)
    return f
X1_PATCH=None  # x1 diff: git diff 43daa2043 6936bc3f8 -- programs/pump/src/multi_hop_curve_swap.rs
EDITS={
 'le': [R("let (base_amount,quote_amount,fees,post_fill) = if base > reserves {","let (base_amount,quote_amount,fees,post_fill) = if base <= reserves {(base,q,nf,None)} else {"),
        R("            }else{(base,q,nf,None)};","            };")],
 'adbind': [R("        amount.checked_sub(trade_amount).ok_or_else(|| error!(PumpError::Overflow))?;","        let adapter_difference = amount.checked_sub(trade_amount).ok_or_else(|| error!(PumpError::Overflow))?;"),
            R("(fees,base_amount,quote_amount,raw_output,amount - trade_amount,post_fill)","(fees,base_amount,quote_amount,raw_output,adapter_difference,post_fill)")],
 'cfmatch': [R("""                if let Some((f, quote, post)) = complete_fill(&a.global,&a.fee_config,fee_config_len,cap,c,
                    &h.associated_base_bonding_curve,flag,p_rate,c_rate,trade_amount)? {""","""                match complete_fill(&a.global,&a.fee_config,fee_config_len,cap,c,
                    &h.associated_base_bonding_curve,flag,p_rate,c_rate,trade_amount)? { Some((f, quote, post)) => {"""),
             R("                }else{(reserves,q,nf,None)}","                }, None => (reserves,q,nf,None) }")],
 'capq': [R("let cap = match crate::buy_fee_market_cap(c,&h.base_mint) { Ok(v) => v, Err(e) => return Err(e) };","let cap = crate::buy_fee_market_cap(c,&h.base_mint)?;")],
 'cfnone': [R("""                if let Some((f, quote, post)) = complete_fill(&a.global,&a.fee_config,fee_config_len,cap,c,
                    &h.associated_base_bonding_curve,flag,p_rate,c_rate,trade_amount)? {

                    (reserves,quote,f,Some(post))
                }else{(reserves,q,nf,None)}""","""                let fill = complete_fill(&a.global,&a.fee_config,fee_config_len,cap,c,
                    &h.associated_base_bonding_curve,flag,p_rate,c_rate,trade_amount)?; match fill {
                    None => (reserves,q,nf,None),
                    Some((f, quote, post)) => (reserves,quote,f,Some(post)),
                }""")],
 'fi': [R("        let fee_config_len = a.fee_config.to_account_info().data_len(); let cap = match crate::buy_fee_market_cap(c,&h.base_mint) { Ok(v) => v, Err(e) => return Err(e) };",
          "        let (fee_config_len, cap) = match fee_inputs(c,&a.fee_config,&h.base_mint) { Ok(v) => v, Err(e) => return Err(e) }; #[inline(always)] fn fee_inputs(curve:&BondingCurve,fee_config:&Account<crate::pump_fees::accounts::FeeConfig>,mint:&Mint)->Result<(usize,u128)>{ let len = fee_config.to_account_info().data_len(); let cap = crate::buy_fee_market_cap(curve,mint)?; Ok((len,cap)) }")],
 'fi8': [R("        let fee_config_len = a.fee_config.to_account_info().data_len(); let cap = match crate::buy_fee_market_cap(c,&h.base_mint) { Ok(v) => v, Err(e) => return Err(e) };",
          "        let (fee_config_len, cap) = fee_inputs(c,&a.fee_config,&h.base_mint); let cap = match cap { Ok(v) => v, Err(e) => return Err(e) }; #[inline(always)] fn fee_inputs(curve:&BondingCurve,fee_config:&Account<crate::pump_fees::accounts::FeeConfig>,mint:&Mint)->(usize,Result<u128>){ let len = fee_config.to_account_info().data_len(); (len,crate::buy_fee_market_cap(curve,mint)) }")],
 'wsub': [R("(fees,base_amount,quote_amount,raw_output,amount - trade_amount,post_fill)","(fees,base_amount,quote_amount,raw_output,amount.wrapping_sub(trade_amount),post_fill)")],
 'adbind1': [R("        amount.checked_sub(trade_amount).ok_or_else(|| error!(PumpError::Overflow))?;","        let adapter_difference = amount.checked_sub(trade_amount).ok_or_else(|| error!(PumpError::Overflow))?;"),
            R("(fees,base_amount,quote_amount,raw_output,amount - trade_amount,post_fill)","(fees,base_amount,quote_amount,raw_output,adapter_difference,post_fill)")],
 'gfirst': [R("let allowed = { let user = a.user.key(); !c.is_mayhem_mode && user!=a.global.whitelist_pda };","let allowed = { let global = &*a.global; let user = a.user.key(); !c.is_mayhem_mode && user!=global.whitelist_pda };")],
 'pfglobal': [R("        let post_buyback_raw = if let Some(post)=post_fill.as_ref() {\n","        let post_buyback_raw = if let Some(post)=post_fill.as_ref() { let global: &Global = &a.global;\n"),
               R("            h.bonding_curve.accrue_fees(&a.global,post.fees.protocol_fee,post.fees.creator_fee)?","            h.bonding_curve.accrue_fees(global,post.fees.protocol_fee,post.fees.creator_fee)?")],
 'pfm': [R('            crate::transfer_fee_recovered::post_fee_amount(&quote_fee,amount)?\n',"            match crate::transfer_fee_recovered::post_fee_amount(&quote_fee,amount) { Ok(v) => v, Err(e) => return Err(e) }\n")],
 'pfme': [R('            crate::transfer_fee_recovered::post_fee_amount(&quote_fee,amount)?\n',"            match crate::transfer_fee_recovered::post_fee_amount(&quote_fee,amount) { Err(e) => return Err(e), Ok(v) => v }\n")],
 'gfm': [R('            let selected = crate::legacy_sell::fee_math::get_fees(&a.global,c,&a.fee_config,fee_config_len,cap,trade_amount)?;',"            let selected = match crate::legacy_sell::fee_math::get_fees(&a.global,c,&a.fee_config,fee_config_len,cap,trade_amount) { Ok(v) => v, Err(e) => return Err(e) };")],
 'gfme': [R('            let selected = crate::legacy_sell::fee_math::get_fees(&a.global,c,&a.fee_config,fee_config_len,cap,trade_amount)?;',"            let selected = match crate::legacy_sell::fee_math::get_fees(&a.global,c,&a.fee_config,fee_config_len,cap,trade_amount) { Err(e) => return Err(e), Ok(v) => v };")],
}
def main():
    trial, names = sys.argv[1], sys.argv[2:]
    dst=f'{OUT}/src/{trial}'
    shutil.rmtree(dst, ignore_errors=True); os.makedirs(f'{OUT}/src',exist_ok=True)
    subprocess.check_call(['cp','-cR',f'{WT}/programs/pump',dst])
    base = names[0] if names and names[0].startswith('@') else None
    if base:  # @x1 => apply x1 patch
        names=names[1:]
    p=f'{dst}/{F}'
    if base in ('@main','@x1'):
        open(p,'w').write(open(f'{OUT}/tools/main.rs').read())
        if base=='@x1': subprocess.check_call(['patch','-p3','-s','-i',X1_PATCH],cwd=dst)
    elif base:
        open(p,'w').write(open(f'{OUT}/src/{base[1:]}/{F}').read())
    t=open(p).read(); o=t
    for n in names:
        for f in EDITS[n]: t=f(t)
    open(p,'w').write(t)
    print(trial, 'changed' if t!=o else 'UNCHANGED')
main()
