#!/usr/bin/env python3
"""ext798.py <crate dir>: code from the parallel Round37 frontier (shawkkkkk packets research/pump-round37-*, final tree
W/peer-snap/ext798/tree, 803/133 on our recipe) ported onto the integ composite, for the windows it has and we lacked.
Their blank-line positioning is NOT copied: coordlib's layout + tools/cl/patterns.json place the lib.rs sites, coordfiles'
layout + integ_anchors.json place util/constant_product.rs:13/17/19 and util/transfer_fee.rs:48/56/66 (code compacted to
one statement per line).
  account-name-recovery: util/account_name.rs with_owned_name (0x2bc0), used by set_reserved_fee_recipients
  buyback-values:        set_buyback_fee_recipients compares with require_neq (0x98af0, lib.rs:1895/1905)
  curve-price:           BondingCurve::sell_quote (0xa0538, lib.rs:2454); their buy_quote method is not taken (pump-hi's
                         buy_quote already matches 0xa0070); integ_genuine.py routes the four original sell-quote callers
  marketcap-checked:     buy_fee_market_cap with checked_div, moved into lib.rs (0xa08f8, lib.rs:2481)
  curve-apply:           BondingCurve::apply_buy / apply_sell (0xa0bf0 2496..2511, 0xa13e0 2520..2535) replace the V3
                         handlers' reserve assignments (the earlier checked next_* values stay for the events)
  curve-fee-accrual:     BondingCurve::accrue_fees (0xa1bd8, 2550/2554) replaces the V3 fee-field assignments (first fill
                         and post-complete fill accrued separately, as in theirs)
  transfer-fees:         util/transfer_fee.rs calculate_fee / post_fee_amount / pre_fee_amount (0x950e0 at :56) behind
                         trade_v3 quote_fee_for_amount and the exact-input budget (quote_post_fee_amount)
  constant product:      util/constant_product.rs output / tokens_for_quote (0x880b0, 0xa0838) for the exact-input
                         token-out computations: legacy buy_exact_sol_in (buy.rs, as theirs) and, per the original call
                         graph (0xa0838 callers 0x13f630 / 0x1489f8), the normal-fee paths of buy_exact_quote_in_v2 and
                         buy_exact_quote v3 - each keeps its own Truncation closure (coordfiles' 927 / 911 windows).
  Not taken: exact_input_tokens (0x834c8, trade_v3.rs:591): its original callers 0x83088 / 0x837a8 have no counterpart
  here, and theirs replaces coordfiles' 904/911 closures in buy_exact_quote.
"""
import shutil, sys
from pathlib import Path
C = Path(sys.argv[1]); S = C / 'src'
EXT = Path('/Users/shawwalters/Documents/Codex/2026-10-24/claude-pump-work/peer-snap/ext798/tree/src')
def rd(p): return (S / p).read_text()
def wr(p, t): (S / p).write_text(t)
def rep(t, old, new, n=1, what=''):
    assert t.count(old) == n, (what or old[:80], t.count(old), n)
    return t.replace(old, new)

shutil.copy2(EXT / 'util/account_name.rs', S / 'util/account_name.rs')
# util/constant_product.rs and util/transfer_fee.rs: their code with THEIR blank-line positioning removed (one statement
# per line, so every error site has a unique line pattern); coordfiles' layout.py positions the sites through
# integ_anchors.json (constant_product.rs:13/17/19, transfer_fee.rs:48/56/66).
(S / 'util/constant_product.rs').write_text('''use anchor_lang::prelude::*;
use crate::PumpError;

#[inline(never)]
pub fn output(amount_in:u128,reserve_in:u128,reserve_out:u128)->Result<u128> {
    let numerator=amount_in.checked_mul(reserve_out).ok_or_else(||error!(PumpError::Overflow))?;
    let denominator=reserve_in.checked_add(amount_in).ok_or_else(||error!(PumpError::Overflow))?;
    numerator.checked_div(denominator).ok_or_else(||error!(PumpError::DivisionByZero))
}

#[inline(never)]
pub fn tokens_for_quote(curve:&crate::trade_types::BondingCurve,quote:u64)->Result<u128>{
    let effective=quote.checked_sub(1).ok_or(PumpError::Overflow)?;
    output(effective as u128,curve.virtual_quote_reserves as u128,curve.virtual_token_reserves as u128)
}
''')
(S / 'util/transfer_fee.rs').write_text('''use crate::*;
use crate::trade::native_transfer_fee::Fee;

#[inline(never)]
pub fn calculate_fee(fee:&Option<Fee>,amount:u64)->Result<u64>{
 match *fee {
  None=>Ok(0),
  Some(fee)=>fee.calculate_fee(amount).ok_or_else(||error!(PumpError::Overflow)),
 }
}

#[inline(never)]
pub fn post_fee_amount(fee:&Option<Fee>,amount:u64)->Result<u64>{
 let fee=calculate_fee(fee,amount)?;
 amount.checked_sub(fee).ok_or_else(||error!(PumpError::Overflow))
}

#[inline(never)]
pub fn pre_fee_amount(fee:&Option<Fee>,amount:u64)->Result<u64>{
 match *fee {
  None=>Ok(amount),
  Some(fee)=>fee.calculate_pre_fee_amount(amount).ok_or_else(||error!(PumpError::Overflow)),
 }
}
''')

# ---- lib.rs
t = rd('lib.rs')
t = rep(t, "pub mod quote_control;\n", "pub mod quote_control;\n"
        '#[path="util/transfer_fee.rs"] pub mod transfer_fee_recovered;\n'
        '#[path="util/constant_product.rs"] pub mod constant_product;\n'
        '#[path="util/account_name.rs"] pub mod account_name;\n', what='module decls')
t = rep(t, 'if account.executable{return Err(error!(anchor_lang::error::ErrorCode::ConstraintExecutable).with_account_name(format!("reserved_fee_recipients[{}]",index)));}',
        'if account.executable{return Err(crate::account_name::with_owned_name(error!(anchor_lang::error::ErrorCode::ConstraintExecutable), &format!("reserved_fee_recipients[{}]",index)));}',
        what='reserved fee recipient executable error')
t = rep(t, 'require_keys_neq!(recipients[left],recipients[right],PumpError::NotUniqueBuybackFeeRecipients)',
        'require_neq!(recipients[left],recipients[right],PumpError::NotUniqueBuybackFeeRecipients)', what='buyback require_neq')
curve = '''
impl trade_types::BondingCurve {
 #[inline(never)]
 pub fn sell_quote(&self,amount:u64)->Result<u128>{
  let numerator=self.virtual_quote_reserves as u128*amount as u128;
  numerator.checked_div(self.virtual_token_reserves as u128+amount as u128).ok_or_else(||error!(PumpError::DivisionByZero))
 }
}

#[inline(never)]
pub(crate) fn buy_fee_market_cap(curve:&trade_types::BondingCurve,mint:&anchor_spl::token_interface::Mint)->Result<u128>{
 let supply=if curve.is_mayhem_mode {curve.token_total_supply}else{mint.supply};
 (u128::from(supply)*u128::from(curve.virtual_quote_reserves)).checked_div(u128::from(curve.virtual_token_reserves)).ok_or_else(||error!(PumpError::DivisionByZero))
}

impl trade_types::BondingCurve {
 #[inline(never)]
 pub fn apply_buy(&mut self,amount:u64,quote:u64)->Result<()>{
  self.virtual_token_reserves=self.virtual_token_reserves.checked_sub(amount).ok_or_else(||error!(PumpError::Overflow))?;
  self.real_token_reserves=self.real_token_reserves.checked_sub(amount).ok_or_else(||error!(PumpError::Overflow))?;
  self.virtual_quote_reserves=self.virtual_quote_reserves.checked_add(quote).ok_or_else(||error!(PumpError::Overflow))?;
  self.real_quote_reserves=self.real_quote_reserves.checked_add(quote).ok_or_else(||error!(PumpError::Overflow))?;
  Ok(())
 }
 #[inline(never)]
 pub fn apply_sell(&mut self,amount:u64,quote:u64)->Result<()>{
  self.virtual_token_reserves=self.virtual_token_reserves.checked_add(amount).ok_or_else(||error!(PumpError::Overflow))?;
  self.real_token_reserves=self.real_token_reserves.checked_add(amount).ok_or_else(||error!(PumpError::Overflow))?;
  self.virtual_quote_reserves=self.virtual_quote_reserves.checked_sub(quote).ok_or_else(||error!(PumpError::Overflow))?;
  self.real_quote_reserves=self.real_quote_reserves.checked_sub(quote).ok_or_else(||error!(PumpError::Overflow))?;
  Ok(())
 }
}

impl trade_types::BondingCurve {
 #[inline(never)]
 pub fn accrue_fees(&mut self,global:&Global,protocol_fee:u64,creator_fee:u64)->Result<u64>{
  let (buyback_fee,retained)=if self.is_mayhem_mode {(0,protocol_fee)}else{
   let buyback_fee=u64::try_from(global.buyback_basis_points as u128*protocol_fee as u128/10000).expect("buyback fee is at most protocol_fee");
   let retained=protocol_fee.checked_sub(buyback_fee).expect("buyback_fee never exceeds protocol_fee");
   (buyback_fee,retained)};
  self.protocol_fees=self.protocol_fees.checked_add(retained).ok_or_else(||error!(PumpError::Overflow))?;
  self.creator_fee=self.creator_fee.checked_add(creator_fee).ok_or_else(||error!(PumpError::Overflow))?;
  Ok(buyback_fee)
 }
}
'''
anchor = "    Ok(numerator / denominator + 1)\n}\n"   # end of pump-hi's buy_quote (lib.rs:2428/2430)
t = rep(t, anchor, anchor + curve, what='curve region')
wr('lib.rs', t)

# ---- trade_v3.rs
t = rd('trade_v3.rs')
i = t.index('fn buy_fee_market_cap(curve: &BondingCurve, mint: &Mint) -> Result<u128> {')
j = t.index('\n}\n', i) + 3
t = t[:i] + 'use crate::buy_fee_market_cap;\n' + t[j:]
ASSIGN = ("    curve.virtual_token_reserves=next_base;curve.virtual_quote_reserves=next_quote;\n"
          "    curve.real_token_reserves=next_real_base;curve.real_quote_reserves=next_real_quote;\n"
          "    curve.creator_fee=next_creator;curve.protocol_fees=next_protocol;\n")
assert t.count(ASSIGN) == 3
BUY = ("    curve.apply_buy(amount,quote)?;\n"
       "    let _=curve.accrue_fees(&a.global,protocol_fee,creator_fee)?;let _=curve.accrue_fees(&a.global,post_protocol,post_creator)?;\n")
SELL = ("    curve.apply_sell(amount,quote)?;\n"
        "    let _=curve.accrue_fees(&a.global,protocol_fee,creator_fee)?;\n")
parts = t.split(ASSIGN)
assert parts[1].startswith('    if crossing{') and parts[2].startswith('    if post_active{') and parts[3].startswith('    let event='), [p[:30] for p in parts[1:]]
t = parts[0] + BUY + parts[1] + BUY + parts[2] + SELL + parts[3]
i = t.index('fn quote_fee_for_amount(snapshot:&Option<(u64,u64,u64)>,amount:u64,inverse:bool)->Result<u64>{')
j = t.index('\n}\n', i) + 3
t = t[:i] + ('fn quote_fee_for_amount(snapshot:&Option<(u64,u64,u64)>,amount:u64,inverse:bool)->Result<u64>{\n'
             ' let fee=snapshot.map(|(epoch,maximum_fee,basis_points)|native_transfer_fee::Fee{epoch,maximum_fee,basis_points:basis_points as u16});\n'
             ' if inverse{let gross=crate::transfer_fee_recovered::pre_fee_amount(&fee,amount)?;crate::transfer_fee_recovered::calculate_fee(&fee,gross)}else{crate::transfer_fee_recovered::calculate_fee(&fee,amount)}\n'
             '}\n'
             '#[inline(always)] fn quote_post_fee_amount(snapshot:&Option<(u64,u64,u64)>,amount:u64)->Result<u64>{let fee=snapshot.map(|(epoch,maximum_fee,basis_points)|native_transfer_fee::Fee{epoch,maximum_fee,basis_points:basis_points as u16});crate::transfer_fee_recovered::post_fee_amount(&fee,amount)}\n') + t[j:]
t = rep(t, 'let available=if is_sol{spendable_quote_in}else{sub(spendable_quote_in,quote_fee_for_amount(&quote_fee,spendable_quote_in,false)?)?};',
        'let available=if is_sol{spendable_quote_in}else{quote_post_fee_amount(&quote_fee,spendable_quote_in)?};', what='exact budget')
t = rep(t, '        else{u64::try_from(curve.virtual_token_reserves as u128*effective as u128/(curve.virtual_quote_reserves as u128+effective as u128)).map_err(|_|error!(PumpError::Truncation))?};',
        '        else{u64::try_from(crate::constant_product::tokens_for_quote(curve,quote_budget)?).map_err(|_|error!(PumpError::Truncation))?};', what='v3 exact tokens')
wr('trade_v3.rs', t)

# ---- buy.rs (legacy buy_exact_sol_in) and buy_v2.rs (buy_exact_quote_in_v2 normal path)
t = rd('buy.rs')
t = rep(t, 'let e=adjusted.saturating_sub(1);narrow(c.virtual_token_reserves as u128*e as u128/(c.virtual_quote_reserves as u128+e as u128))?',
        'narrow(crate::constant_product::tokens_for_quote(c,adjusted)?)?', what='legacy exact tokens')
wr('buy.rs', t)
t = rd('buy_v2.rs')
t = rep(t, '  else{u64::try_from(c.virtual_token_reserves as u128*e as u128/(c.virtual_quote_reserves as u128+e as u128)).map_err(|_|error!(PumpError::Truncation))?}};',
        '  else{u64::try_from(crate::constant_product::tokens_for_quote(c,adjusted)?).map_err(|_|error!(PumpError::Truncation))?}};', what='v2 exact tokens')
wr('buy_v2.rs', t)
print('ext798 port applied')
