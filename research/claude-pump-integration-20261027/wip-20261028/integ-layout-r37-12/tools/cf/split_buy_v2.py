#!/usr/bin/env python3
"""split_buy_v2.py <crate dir>: replace buy_v2's generic execute_inner<EXACT> by the two handlers the original
has (buy 0x13b9b8 at buy_v2.rs:345..500, buy_exact_quote_in 0x13f630 at buy_v2.rs:767..995), specialising
`exact` mechanically (no logic change), and write the arithmetic whose Overflow/Truncation errors the
original raises from separate closures as inline `ok_or_else`/`map_err` closures:
  buy:   465 Truncation (curve quote u128->u64), 469 Overflow (transfer fee = gross - quote),
         498/500 Overflow (gross + protocol fee + creator fee inside the TooMuchSolRequired check at 494)
  exact: 927 Truncation (tokens out for the fee-adjusted quote), 959 Truncation (quote for the capped amount)
"""
import re, sys
from pathlib import Path
f = Path(sys.argv[1]) / 'src' / 'buy_v2.rs'
t = f.read_text()
lines = t.split('\n')

def find(pred, start=0):
    for i in range(start, len(lines)):
        if pred(lines[i]):
            return i
    raise KeyError

i_exec = find(lambda l: l.startswith("pub fn execute<'info>(ctx:Context<'_,'_,'_,'info,BuyV2<'info>>,input:u64,limit:u64,partial:bool,exact:bool)"))
i_inner = find(lambda l: l.startswith("fn execute_inner<'info,const EXACT:bool>"))
assert lines[i_inner - 1] == '#[inline(never)]'
i_end = find(lambda l: l == '}', i_inner)
body = lines[i_inner + 1:i_end]
# shared head: from validate_fee_recipient through the line before `let c=&a.bonding_curve`
h0 = next(k for k, l in enumerate(body) if l.startswith(' crate::legacy_sell::fee_recipient::validate_fee_recipient('))
c0 = next(k for k, l in enumerate(body) if l.startswith(' let c=&a.bonding_curve;let native='))
head = body[h0:c0]
# shared tail: from `let vb=sub(` to the end
v0 = next(k for k, l in enumerate(body) if l.startswith(' let vb=sub(c.virtual_token_reserves,amount)?;'))
tail = body[v0:]
assert sum('if exact{"buy_exact_quote_in".into()}else{"buy".into()}' in l for l in tail) == 1
def tail_for(name):
    return [l.replace('if exact{"buy_exact_quote_in".into()}else{"buy".into()}', f'"{name}".into()') for l in tail]
# sanity: the specialised parts we rewrite must still read exactly like this
expect = [
 ' let c=&a.bonding_curve;let native=c.quote_mint==Pubkey::default();',
 ' let available=if exact && !native{sub(input,crate::trade::quote_transfer_fee(&a.quote_mint.to_account_info(),input,false)?)?}else{input};',
 ' if exact{require_gt!(available,0,PumpError::BuyNotEnoughSolToCoverFees);}',
 ' let quoted_amount=if exact{0}else{input.min(c.real_token_reserves)};',
 ' let pre_quote=if exact{0}else{add(narrow(quoted_amount as u128*c.virtual_quote_reserves as u128/(c.virtual_token_reserves as u128-quoted_amount as u128))?,1)?};',
 ' let pre_quote_transfer_fee=if !exact && !native{crate::trade::quote_transfer_fee(&a.quote_mint.to_account_info(),pre_quote,true)?}else{0};',
 ' let (initial_protocol_fee,initial_creator_fee,protocol_fee_bps,creator_fee_bps)=if a.user.key()==a.global.whitelist_pda{(0,0,0,0)}else{crate::legacy_sell::fee_cpi::trade_fees(',
 '  &a.global,&a.bonding_curve,&a.base_mint,&a.fee_config,&a.fee_program,a.program.as_ref(),if exact{available}else{pre_quote}',
 ' )?};',
 ' let cb=if c.creator==Pubkey::default(){0}else{creator_fee_bps};',
 ' let raw_quote=if exact{let total_bps=protocol_fee_bps.checked_add(cb).ok_or(PumpError::Overflow)?;let denominator=10000u128+total_bps as u128;narrow(available as u128*10000/denominator)?}else{0};',
 ' let adjusted=if exact && add(add(raw_quote,ceil_fee(raw_quote,protocol_fee_bps)?)?,ceil_fee(raw_quote,cb)?)?>available{sub(raw_quote,1)?}else{raw_quote};',
 ' let computed=if exact{require_gt!(raw_quote,0,PumpError::BuyNotEnoughSolToCoverFees);require_gt!(adjusted,0,PumpError::BuySlippageBelowMinTokensOut);let e=adjusted.saturating_sub(1);narrow(c.virtual_token_reserves as u128*e as u128/(c.virtual_quote_reserves as u128+e as u128))?}else{input};',
 ' if !partial{require_gte!(c.real_token_reserves,computed,PumpError::NotEnoughTokensToBuy);}let amount=computed.min(c.real_token_reserves);',
 ' let quote=if !exact{pre_quote}else if computed<=c.real_token_reserves{adjusted}else{add(narrow(amount as u128*c.virtual_quote_reserves as u128/(c.virtual_token_reserves as u128-amount as u128))?,1)?};',
 ' let fq=if exact && computed<=c.real_token_reserves{raw_quote}else{quote};let pf=if exact{ceil_fee(fq,protocol_fee_bps)?}else{initial_protocol_fee};let cf=if exact{ceil_fee(fq,cb)?}else{initial_creator_fee};',
 ' let quote_transfer_fee=if !exact{pre_quote_transfer_fee}else if native{0}else{crate::trade::quote_transfer_fee(&a.quote_mint.to_account_info(),quote,true)?};',
 ' let gross_quote=add(quote,quote_transfer_fee)?;',
 ' if exact{if !(partial && computed>c.real_token_reserves){require_gte!(amount,limit,PumpError::BuySlippageBelowMinTokensOut);}}else{require_gte!(limit,add(add(gross_quote,pf)?,cf)?,PumpError::TooMuchSolRequired);}',
]
mid = [l for l in body[c0:v0] if l.strip()]
assert mid == expect, '\n'.join(x for x in mid if x not in expect)
pre = [l for l in body[:h0] if l.strip()]
assert pre == [
 ' let exact=EXACT;',
 ' let a=&mut *ctx.accounts;',
 ' require!(!a.bonding_curve.complete,PumpError::BondingCurveComplete);',
 ' if exact{require_gt!(limit,0,PumpError::BuyZeroAmount);require_gt!(input,0,PumpError::BuyNotEnoughSolToCoverFees);}else{',
 '  if partial{input=input.min(a.bonding_curve.real_token_reserves);}',
 '  require_gt!(input,0,PumpError::BuyZeroAmount);',
 '  require_gte!(a.bonding_curve.real_token_reserves,input,PumpError::NotEnoughTokensToBuy);',
 ' }'], pre
SIG = "<'info>(ctx:Context<'_,'_,'_,'info,BuyV2<'info>>,{m}input:u64,limit:u64,partial:bool)->Result<()>{{"
buy = ['#[inline(never)]', 'fn buy_handler' + SIG.format(m='mut '),
 ' let a=&mut *ctx.accounts;',
 ' require!(!a.bonding_curve.complete,PumpError::BondingCurveComplete);',
 ' if partial{input=input.min(a.bonding_curve.real_token_reserves);}',
 ' require_gt!(input,0,PumpError::BuyZeroAmount);',
 ' require_gte!(a.bonding_curve.real_token_reserves,input,PumpError::NotEnoughTokensToBuy);',
 *head,
 ' let c=&a.bonding_curve;let native=c.quote_mint==Pubkey::default();',
 ' let quoted_amount=input.min(c.real_token_reserves);',
 ' let pre_quote=add(u64::try_from(quoted_amount as u128*c.virtual_quote_reserves as u128/(c.virtual_token_reserves as u128-quoted_amount as u128)).map_err(|_|error!(PumpError::Truncation))?,1)?;',
 ' let pre_quote_transfer_fee=if !native{crate::trade::quote_transfer_fee(&a.quote_mint.to_account_info(),pre_quote,true)?}else{0};',
 ' let gross_quote=add(pre_quote,pre_quote_transfer_fee)?;',
 ' let quote_transfer_fee=gross_quote.checked_sub(pre_quote).ok_or_else(||error!(PumpError::Overflow))?;',
 ' let (initial_protocol_fee,initial_creator_fee,protocol_fee_bps,creator_fee_bps)=if a.user.key()==a.global.whitelist_pda{(0,0,0,0)}else{crate::legacy_sell::fee_cpi::trade_fees(',
 '  &a.global,&a.bonding_curve,&a.base_mint,&a.fee_config,&a.fee_program,a.program.as_ref(),pre_quote',
 ' )?};',
 ' let cb=if c.creator==Pubkey::default(){0}else{creator_fee_bps};',
 ' let computed=input;',
 ' if !partial{require_gte!(c.real_token_reserves,computed,PumpError::NotEnoughTokensToBuy);}let amount=computed.min(c.real_token_reserves);',
 ' let quote=pre_quote;',
 ' let pf=initial_protocol_fee;let cf=initial_creator_fee;',
 ' require_gte!(limit,gross_quote.checked_add(pf)',
 '  .ok_or_else(||error!(PumpError::Overflow))?',
 '  .checked_add(cf)',
 '  .ok_or_else(||error!(PumpError::Overflow))?,PumpError::TooMuchSolRequired);',
 *tail_for('buy'), '}']
exact = ['#[inline(never)]', 'fn buy_exact_quote_in_handler' + SIG.format(m=''),
 ' let a=&mut *ctx.accounts;',
 ' require!(!a.bonding_curve.complete,PumpError::BondingCurveComplete);',
 ' require_gt!(limit,0,PumpError::BuyZeroAmount);',
 ' require_gt!(input,0,PumpError::BuyNotEnoughSolToCoverFees);',
 *head,
 ' let c=&a.bonding_curve;let native=c.quote_mint==Pubkey::default();',
 ' let available=if !native{sub(input,crate::trade::quote_transfer_fee(&a.quote_mint.to_account_info(),input,false)?)?}else{input};',
 ' require_gt!(available,0,PumpError::BuyNotEnoughSolToCoverFees);',
 ' let (_initial_protocol_fee,_initial_creator_fee,protocol_fee_bps,creator_fee_bps)=if a.user.key()==a.global.whitelist_pda{(0,0,0,0)}else{crate::legacy_sell::fee_cpi::trade_fees(',
 '  &a.global,&a.bonding_curve,&a.base_mint,&a.fee_config,&a.fee_program,a.program.as_ref(),available',
 ' )?};',
 ' let cb=if c.creator==Pubkey::default(){0}else{creator_fee_bps};',
 ' let raw_quote={let total_bps=protocol_fee_bps.checked_add(cb).ok_or(PumpError::Overflow)?;let denominator=10000u128+total_bps as u128;narrow(available as u128*10000/denominator)?};',
 ' let adjusted=if add(add(raw_quote,ceil_fee(raw_quote,protocol_fee_bps)?)?,ceil_fee(raw_quote,cb)?)?>available{sub(raw_quote,1)?}else{raw_quote};',
 ' let computed={require_gt!(raw_quote,0,PumpError::BuyNotEnoughSolToCoverFees);require_gt!(adjusted,0,PumpError::BuySlippageBelowMinTokensOut);let e=adjusted.saturating_sub(1);',
 '  u64::try_from(c.virtual_token_reserves as u128*e as u128/(c.virtual_quote_reserves as u128+e as u128)).map_err(|_|error!(PumpError::Truncation))?};',
 ' if !partial{require_gte!(c.real_token_reserves,computed,PumpError::NotEnoughTokensToBuy);}let amount=computed.min(c.real_token_reserves);',
 ' let quote=if computed<=c.real_token_reserves{adjusted}else{add(',
 '  u64::try_from(amount as u128*c.virtual_quote_reserves as u128/(c.virtual_token_reserves as u128-amount as u128)).map_err(|_|error!(PumpError::Truncation))?,1)?};',
 ' let fq=if computed<=c.real_token_reserves{raw_quote}else{quote};let pf=ceil_fee(fq,protocol_fee_bps)?;let cf=ceil_fee(fq,cb)?;',
 ' let quote_transfer_fee=if native{0}else{crate::trade::quote_transfer_fee(&a.quote_mint.to_account_info(),quote,true)?};',
 ' let gross_quote=add(quote,quote_transfer_fee)?;',
 ' if !(partial && computed>c.real_token_reserves){require_gte!(amount,limit,PumpError::BuySlippageBelowMinTokensOut);}',
 *tail_for('buy_exact_quote_in'), '}']
new_exec = [lines[i_exec], ' if exact{buy_exact_quote_in_handler(ctx,input,limit,partial)}else{buy_handler(ctx,input,limit,partial)}', '}']
assert lines[i_exec + 1] == ' if exact{execute_inner::<true>(ctx,input,limit,partial)}else{execute_inner::<false>(ctx,input,limit,partial)}'
assert lines[i_exec + 2] == '}' and i_exec + 3 == i_inner - 1
out = lines[:i_exec] + new_exec + buy + exact + lines[i_end + 1:]
f.write_text('\n'.join(out))
print('split ok:', len(buy), len(exact))

# Keep the shared v2 helpers externally visible: the generic execute_inner<EXACT> made them reachable
# (hidden external linkage), which is what keeps ensure_rent_exempt's unused leading `_size` argument and
# transfer_curve_tokens' by-reference arguments as in the original; private non-generic callers would let
# LLVM's DeadArgElim/ArgumentPromotion rewrite them (seen as losses 0x3b598 / 0x8f5c8 in b03).
def rep(p, old, new):
    q = Path(sys.argv[1]) / 'src' / p; s = q.read_text()
    assert s.count(old) == 1, (p, old)
    q.write_text(s.replace(old, new))
rep('buy_v2.rs', '#[path="v2_native_payments.rs"]\npub(crate) mod native_payments;', '#[path="v2_native_payments.rs"]\npub mod native_payments;')
rep('buy_v2.rs', '#[path="v2_token_transfers.rs"]\nmod token_transfers;', '#[path="v2_token_transfers.rs"]\npub mod token_transfers;')
rep('v2_native_payments.rs', 'pub(crate) fn ensure_rent_exempt<', 'pub fn ensure_rent_exempt<')
rep('v2_token_transfers.rs', 'pub(super) fn transfer_curve_tokens<', 'pub fn transfer_curve_tokens<')
print('helper visibility: pub')
