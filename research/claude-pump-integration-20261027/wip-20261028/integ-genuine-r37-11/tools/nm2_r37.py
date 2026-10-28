#!/usr/bin/env python3
"""nm2_r37.py <crate dir> - nearmiss2-03..07 genuine (non-layout) changes, re-applied on the Round37-based composite
(after the coordfiles and coordlib steps).  Not re-applied because the r37g5 base already has them:
  - pump_amm GlobalConfig IDL trim + boost_enabled via the generated client (libnear3-01 in r37g5),
  - LegacyFeeConfig = pump_fees::accounts::FeeConfig (Round37 sell.rs imports `accounts::FeeConfig as LegacyFeeConfig`),
  - transfer_native_signed for creator-vault payouts (Round37: collect_v2::transfer_native with a plain AccountInfo source),
  - add/remove_quote_mint loop forms (coordlib changes3.py covers the same windows).
Re-applied:
  1. (nearmiss2-02/03) trade_v3.rs validate_trade(complete:u8, cashback:u64, allow_cashback:u64) with the allow-first
     require!; callers pass `is_cashback_coin as u64` and 0 / `(flag & 2 == 0) as u64`.  Kept in place (coordfiles'
     layout anchors `require!(complete==0,..)` at trade_v3.rs:149; the CashbackCoinNotSupported require! is :150).
  2. (nearmiss2-04) add3/sub3 three-operand helpers (#[inline(never)], and_then form) after validate_trade, used by buy's
     first_cost and sell's user_output (orig 0x801f8 :285 / 0x80488 :294; integ_anchors.json positions them).
  3. (nearmiss2-05) generic move_native<T: AsRef<AccountInfo>> (no zero-amount check) in curve_quote_payments.rs, used by
     the legacy sell creator-vault payout (&AccountInfo) and buyback payout (&&AccountInfo) (orig 0x96280 / 0x95f38).
     The legacy sell body lives in the lib.rs `sell` handler after coordlib's changes4.py, so the edit is made there.
  4. (nearmiss2-07) transfer_to_user/owned/recipient build the bonding-curve signer seeds inline (orig 0x96d48 /
     0x970f8 / 0x97580).
"""
import sys
from pathlib import Path
S = Path(sys.argv[1]) / 'src'


def edit(p, old, new, count=1):
    f = S / p; t = f.read_text(); n = t.count(old)
    assert n == count, (p, n, old[:90])
    f.write_text(t.replace(old, new))


def edit_any(files, old, new, count=1):
    hits = [(p, (S / p).read_text().count(old)) for p in files if (S / p).exists()]
    tot = sum(n for _, n in hits)
    assert tot == count, (hits, old[:90])
    for p, n in hits:
        if n:
            edit(p, old, new, n)


# 1. validate_trade
edit('trade_v3.rs',
     'pub fn validate_trade(complete:u8,cashback:u8,allow_cashback:bool)->Result<()> {\n'
     '    require!(complete==0,PumpError::BondingCurveComplete);\n'
     '    if !allow_cashback {\n'
     '        require!(cashback==0,PumpError::CashbackCoinNotSupported);\n'
     '    }\n'
     '    Ok(())\n}\n',
     'pub fn validate_trade(complete:u8,cashback:u64,allow_cashback:u64)->Result<()> {\n'
     '    require!(complete==0,PumpError::BondingCurveComplete);\n'
     '    require!(allow_cashback!=0 || cashback as u8==0,PumpError::CashbackCoinNotSupported);\n'
     '    Ok(())\n}\n')
edit('trade_v3.rs',
     'validate_trade(a.bonding_curve.complete as u8,a.bonding_curve.is_cashback_coin as u8,false)?;',
     'validate_trade(a.bonding_curve.complete as u8,a.bonding_curve.is_cashback_coin as u64,0)?;', count=3)
edit('multi_hop_curve_swap.rs',
     'crate::trade::validate_trade(h.bonding_curve.complete as u8,h.bonding_curve.is_cashback_coin as u8,flag & 2 == 0)?;',
     'crate::trade::validate_trade(h.bonding_curve.complete as u8,h.bonding_curve.is_cashback_coin as u64,(flag & 2 == 0) as u64)?;')

# 2. add3 / sub3
t = (S / 'trade_v3.rs').read_text()
vt = ('pub fn validate_trade(complete:u8,cashback:u64,allow_cashback:u64)->Result<()> {\n'
      '    require!(complete==0,PumpError::BondingCurveComplete);\n'
      '    require!(allow_cashback!=0 || cashback as u8==0,PumpError::CashbackCoinNotSupported);\n'
      '    Ok(())\n}\n')
assert t.count(vt) == 1
helpers = ('#[inline(never)]\n'
           'fn add3(a:u64,b:u64,c:u64)->Result<u64>{a.checked_add(b).and_then(|x|x.checked_add(c)).ok_or_else(||error!(PumpError::Overflow))}\n'
           '#[inline(never)]\n'
           'fn sub3(a:u64,b:u64,c:u64)->Result<u64>{a.checked_sub(b).and_then(|x|x.checked_sub(c)).ok_or_else(||error!(PumpError::Overflow))}\n')
t = t.replace(vt, vt + helpers, 1)
bi = t.index('pub fn buy(ctx:Context<SellV3>,amount:u64,max_sol_cost:u64,partial_fill:bool)->Result<()> {')
be = t.index('\n}\n', bi)
fc_old = '    let first_cost=add(add(quote,protocol_fee)?,creator_fee)?;\n'
seg = t[bi:be]
assert seg.count(fc_old) == 1
t = t[:bi] + seg.replace(fc_old, '    let first_cost=add3(quote,protocol_fee,creator_fee)?;\n') + t[be:]
uo_old = '    let user_output=sub(sub(quote,protocol_fee)?,creator_fee)?;\n'
assert t.count(uo_old) == 1
t = t.replace(uo_old, '    let user_output=sub3(quote,protocol_fee,creator_fee)?;\n')
(S / 'trade_v3.rs').write_text(t)

# 3. move_native
edit('curve_quote_payments.rs', "#[inline(never)]\npub fn transfer_to_user<'info>(",
     "/// Lamport move without the zero-amount early return (callers check the amount).\n"
     "#[inline(never)]\n"
     "pub fn move_native<'a,'info,T:AsRef<AccountInfo<'info>>>(\n"
     "    source:&Account<'a,BondingCurve>,destination:T,amount:u64,\n"
     ")->Result<()>{\n"
     "    source.sub_lamports(amount)?;\n"
     "    destination.add_lamports(amount)?;\n"
     "    Ok(())\n"
     "}\n\n"
     "#[inline(never)]\npub fn transfer_to_user<'info>(")
# the creator payout line: in sell.rs (`add(n,cf)`) or, after coordlib's changes4, in lib.rs (`crate::legacy_sell::add`)
HEAD = "if cf!=0 {a.bonding_curve.sub_lamports(cf)?;if cashback_coin{rem[0].add_lamports(cf)?;"
TAIL = "}else{a.creator_vault.add_lamports(cf)?;}}"
n = 0
for f in ['lib.rs', 'sell.rs']:
    lines = (S / f).read_text().split('\n')
    for i, l in enumerate(lines):
        if HEAD in l and l.rstrip().endswith(TAIL):
            l = l.replace(HEAD, "if cf!=0 {if cashback_coin{a.bonding_curve.sub_lamports(cf)?;rem[0].add_lamports(cf)?;", 1)
            l = l[:l.rindex(TAIL)] + "}else{crate::trade::quote_payments::move_native(&a.bonding_curve,&a.creator_vault,cf)?;}}" + l[l.rindex(TAIL) + len(TAIL):]
            lines[i] = l; n += 1
    (S / f).write_text('\n'.join(lines))
assert n == 1, n
edit_any(['lib.rs', 'sell.rs'],
     "if bf!=0 {a.bonding_curve.sub_lamports(bf)?;bb.add_lamports(bf)?;}",
     "if bf!=0 {crate::trade::quote_payments::move_native(&a.bonding_curve,&bb,bf)?;}")

# 4. inline signer seeds
edit('curve_quote_payments.rs',
     '    let authority=curve.to_account_info();\n'
     '    let mint_key=*base_mint.key;\n'
     '    let bump=[bump];\n'
     '    let seeds:&[&[u8]]=&[b"bonding-curve",mint_key.as_ref(),&bump];\n'
     '    crate::sell_v2::quote_token_transfers::transfer_quote_tokens(\n'
     '        token_program,from,to,authority,quote_decimals,quote_mint,amount,&[seeds],\n'
     '    )\n',
     '    crate::sell_v2::quote_token_transfers::transfer_quote_tokens(\n'
     '        token_program,from,to,curve.to_account_info(),quote_decimals,quote_mint,amount,\n'
     '        &[&[b"bonding-curve",base_mint.key().as_ref(),&[bump]]],\n'
     '    )\n', count=3)
print('nm2_r37 applied')
