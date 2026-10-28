#!/usr/bin/env python3
"""coordlib round 2, step 4 (after changes3.py, before layout.py): legacy `buy` / `sell` handler bodies in lib.rs.

Evidence (original binary): `__global::buy` calls 0x14c038 and `__global::sell` calls 0x152888, both with Source
lib.rs (608..747 / 968..1037); `buy_exact_sol_in` alone lives in buy.rs (0x14f4e0, buy.rs:53..232). Each checked
operation in those handlers is its own `|| error!(..)` closure function:
  buy : 629 Truncation (u64::try_from of the curve quote), 664/666 Overflow (quote + protocol fee + creator fee, the
        operand of require_gte!(max_sol_cost, .., TooMuchSolRequired) at 654), 674/679/684/689 Overflow
        (virtual_token -= amount, real_token -= amount, virtual_sol += quote, real_sol += quote)
  sell: 981 Truncation (quote), 1007/1009 Overflow (quote - protocol fee - creator fee), 1012 require_gte! output,
        1022/1027/1032/1037 Overflow (virtual_token += amount, real_token += amount, virtual_sol -= quote,
        real_sol -= quote)
Ours had one generic `legacy_buy::execute::<EXACT>` (buy.rs) and `legacy_sell::execute` (sell.rs) using shared
`add`/`sub`/`narrow` helpers. This moves the non-exact buy path and the sell body into the #[program] handlers,
with the checked operations written inline (each with its own closure, in the original's order). Values, checks and
their order are unchanged (the four reserve updates are independent; only their evaluation order follows the
original: token reserves first). `fee_cpi::buy_quote` returns the unnarrowed u128 (narrowed in the handler, 629).
buy.rs keeps `execute::<true>` for buy_exact_sol_in.
Usage: changes4.py <crate dir>
"""
import sys
from pathlib import Path

S = Path(sys.argv[1]) / 'src'


def rd(p):
    return (S / p).read_text()


def wr(p, t):
    (S / p).write_text(t)


def sub1(t, old, new, n=1):
    assert t.count(old) == n, (t.count(old), old[:90])
    return t.replace(old, new)


# ------------------------------------------------------------------ fee_cpi::buy_quote -> u128
f = rd('fee_cpi.rs')
f = sub1(f, 'pub fn buy_quote(curve: &BondingCurve, amount: u64) -> Result<u64> {', 'pub fn buy_quote(curve: &BondingCurve, amount: u64) -> Result<u128> {')
f = sub1(f, '''    let quote = u128::from(amount) * u128::from(curve.virtual_quote_reserves)
        / u128::from(denominator) + 1;
    u64::try_from(quote).map_err(|_| error!(crate::PumpError::Truncation))
}''', '''    Ok(u128::from(amount) * u128::from(curve.virtual_quote_reserves)
        / u128::from(denominator) + 1)
}''')
wr('fee_cpi.rs', f)

# ------------------------------------------------------------------ sell: body out of sell.rs
s = rd('sell.rs')
lines = s.split('\n')
i = next(k for k, l in enumerate(lines) if l.startswith('pub fn execute(ctx:Context<LegacySell>,amount:u64,minimum:u64)->Result<()>{'))
j = next(k for k in range(i, len(lines)) if lines[k] == '}')
sell_body = '\n'.join(lines[i + 1:j])
del lines[i:j + 1]
s = '\n'.join(lines)
for h in ('add', 'sub', 'narrow'):
    s = sub1(s, f'\nfn {h}(', f'\npub(crate) fn {h}(')
wr('sell.rs', s)

sb = sell_body
sb = sub1(sb, 'require!(!c.complete,PumpError::BondingCurveComplete);require_gt!(amount,0,PumpError::SellZeroAmount);require_gte!(a.associated_user.amount,amount,PumpError::NotEnoughTokensToSell);',
          'require!(!c.complete,PumpError::BondingCurveComplete);\n require_gt!(amount,0,PumpError::SellZeroAmount);\n require_gte!(a.associated_user.amount,amount,PumpError::NotEnoughTokensToSell);')
sb = sub1(sb, 'let quote=narrow(amount as u128*c.virtual_quote_reserves as u128/(c.virtual_token_reserves as u128+amount as u128))?;',
          'let quote=u64::try_from(amount as u128*c.virtual_quote_reserves as u128/(c.virtual_token_reserves as u128+amount as u128)).map_err(|_|error!(PumpError::Truncation))?;')
sb = sub1(sb, 'let output=sub(sub(quote,pf)?,cf)?;require_gte!(output,minimum,PumpError::TooLittleSolReceived);',
          'let output=quote.checked_sub(pf).ok_or_else(||error!(PumpError::Overflow))?\n  .checked_sub(cf).ok_or_else(||error!(PumpError::Overflow))?;\n require_gte!(output,minimum,PumpError::TooLittleSolReceived);')
sb = sub1(sb, ' let vb=add(c.virtual_token_reserves,amount)?;let vq=sub(c.virtual_quote_reserves,quote)?;let rb=add(c.real_token_reserves,amount)?;let rq=sub(c.real_quote_reserves,quote)?;',
          ' let vb=c.virtual_token_reserves.checked_add(amount).ok_or_else(||error!(PumpError::Overflow))?;\n'
          ' let rb=c.real_token_reserves.checked_add(amount).ok_or_else(||error!(PumpError::Overflow))?;\n'
          ' let vq=c.virtual_quote_reserves.checked_sub(quote).ok_or_else(||error!(PumpError::Overflow))?;\n'
          ' let rq=c.real_quote_reserves.checked_sub(quote).ok_or_else(||error!(PumpError::Overflow))?;')
sb = sub1(sb, 'token_interface::transfer_checked(CpiContext::new(a.token_program.to_account_info(),TransferChecked{',
          'anchor_spl::token_interface::transfer_checked(CpiContext::new(a.token_program.to_account_info(),anchor_spl::token_interface::TransferChecked{')
sb = sub1(sb, 'copy_from_slice(&add(n,cf)?.to_le_bytes())', 'copy_from_slice(&crate::legacy_sell::add(n,cf)?.to_le_bytes())')
sb = sub1(sb, 'let ev=TradeEvent{', 'let ev=crate::trade_types::TradeEvent{')
assert 'narrow(' not in sb and ' sub(' not in sb and '(add(' not in sb, sb
sell_handler = ('    pub fn sell(ctx:Context<LegacySell>,amount:u64,min_sol_output:u64)->Result<()>{let minimum=min_sol_output;\n'
                + '\n'.join('    ' + l for l in sb.split('\n')) + '\n    }')

# ------------------------------------------------------------------ buy: non-exact path out of the generic
b = rd('buy.rs')
for h in ('add', 'sub', 'narrow'):
    b = sub1(b, f'\nfn {h}(', f'\npub(crate) fn {h}(')
b = sub1(b, 'let pre_quote=if exact{0}else{crate::legacy_sell::fee_cpi::buy_quote(c,input.min(c.real_token_reserves))?};',
         'let pre_quote=if exact{0}else{narrow(crate::legacy_sell::fee_cpi::buy_quote(c,input.min(c.real_token_reserves))?)?};')
wr('buy.rs', b)
buy_body = ''' let (input,limit,track,partial)=(amount,max_sol_cost,track_volume.0,partial_fill.0);
 let a=&mut *ctx.accounts;
 crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.user)?;
 let c=&a.bonding_curve;
 crate::legacy_sell::fee_recipient::validate_fee_recipient(&a.fee_recipient,&a.global,&a.bonding_curve)?;
 let rem=ctx.remaining_accounts;
 let bb=rem.get(1).ok_or_else(||error!(PumpError::BuybackFeeRecipientMissing))?;a.global.validate_buyback_fee_recipient(*bb.key)?;
 require!(!c.complete,PumpError::BondingCurveComplete);
 require_gt!(input,0,PumpError::BuyZeroAmount);
 if !partial{require_gte!(c.real_token_reserves,input,PumpError::NotEnoughTokensToBuy);}
 if partial{let amount=input.min(c.real_token_reserves);require_gt!(amount,0,PumpError::BuyZeroAmount);}
 let pre_quote=u64::try_from(crate::legacy_sell::fee_cpi::buy_quote(c,input.min(c.real_token_reserves))?).map_err(|_|error!(PumpError::Truncation))?;
 let (initial_protocol_fee,initial_creator_fee,protocol_fee_bps,creator_fee_bps)={let values=crate::legacy_sell::fee_cpi::trade_fees(
  &a.global,&a.bonding_curve,&a.mint,&a.fee_config,&a.fee_program,a.program.as_ref(),pre_quote
 )?;if a.user.key()==a.global.whitelist_pda{(0,0,0,0)}else{values}};
 let cb=if c.creator==Pubkey::default(){0}else{creator_fee_bps};
 let computed=input;
 if !partial{require_gte!(c.real_token_reserves,computed,PumpError::NotEnoughTokensToBuy);}let amount=computed.min(c.real_token_reserves);
 let quote=pre_quote;
 let pf=initial_protocol_fee;let cf=initial_creator_fee;
 require_gte!(limit,
  quote.checked_add(pf).ok_or_else(||error!(PumpError::Overflow))?
  .checked_add(cf).ok_or_else(||error!(PumpError::Overflow))?,
  PumpError::TooMuchSolRequired);
 let vb=c.virtual_token_reserves.checked_sub(amount).ok_or_else(||error!(PumpError::Overflow))?;
 let rb=c.real_token_reserves.checked_sub(amount).ok_or_else(||error!(PumpError::Overflow))?;
 let vq=c.virtual_quote_reserves.checked_add(quote).ok_or_else(||error!(PumpError::Overflow))?;
 let rq=c.real_quote_reserves.checked_add(quote).ok_or_else(||error!(PumpError::Overflow))?;
'''
# the remainder of the generic body (from the seeds line on), specialized for exact=false
gb = b[b.index(' let mint=a.mint.key();let bump=[ctx.bumps.bonding_curve];'):]
gb = gb[:gb.index('\n}\n')]
gb = sub1(gb, 'token_interface::transfer_checked(CpiContext::new_with_signer(a.token_program.to_account_info(),TransferChecked{',
          'anchor_spl::token_interface::transfer_checked(CpiContext::new_with_signer(a.token_program.to_account_info(),anchor_spl::token_interface::TransferChecked{')
gb = sub1(gb, 'a.user_volume_accumulator.cashback_earned=add(a.user_volume_accumulator.cashback_earned,cf)?;',
          'a.user_volume_accumulator.cashback_earned=crate::legacy_buy::add(a.user_volume_accumulator.cashback_earned,cf)?;')
gb = sub1(gb, 'let ev=TradeEvent{', 'let ev=crate::trade_types::TradeEvent{')
gb = sub1(gb, 'ix_name:if exact{"buy_exact_sol_in".into()}else{"buy".into()}', 'ix_name:"buy".into()')
assert 'exact' not in gb, gb
buy_handler = ('    pub fn buy<\'info>(ctx:Context<\'_,\'_,\'_,\'info,LegacyBuy<\'info>>,amount:u64,max_sol_cost:u64,track_volume:OptionBool,partial_fill:OptionBool)->Result<()>{\n'
               + '\n'.join('    ' + l for l in (buy_body.rstrip('\n') + '\n' + gb).split('\n')) + '\n    }')

L = rd('lib.rs')
L = sub1(L, "    pub fn buy<'info>(ctx:Context<'_,'_,'_,'info,LegacyBuy<'info>>,amount:u64,max_sol_cost:u64,track_volume:OptionBool,partial_fill:OptionBool)->Result<()>{legacy_buy::execute::<false>(ctx,amount,max_sol_cost,track_volume.0,partial_fill.0)}",
         buy_handler)
L = sub1(L, "    pub fn sell(ctx:Context<LegacySell>,amount:u64,min_sol_output:u64)->Result<()>{legacy_sell::execute(ctx,amount,min_sol_output)}",
         sell_handler)
wr('lib.rs', L)
print('changes4 applied')
