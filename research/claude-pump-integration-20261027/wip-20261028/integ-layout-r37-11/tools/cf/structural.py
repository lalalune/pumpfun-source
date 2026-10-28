#!/usr/bin/env python3
"""structural.py - genuine structure recovery for non-lib.rs Source sites (coordfiles lane, round 2).

    structural.py <crate dir>        # applies in place; asserts the expected base text (i1)

Each step moves whole items (no logic change) into the file / order that the original binary's
Source {filename, line} records imply:
  S1 buy_v2.rs: admit_associated_token_account before the BuyV2 accounts struct
       (orig 0x14910 sites buy_v2.rs:55/60/81/88 precede BuyV2 try_accounts at buy_v2.rs:129)
  S2 util/fee.rs: checked_ceil_div before fee (orig 0x88908 :15/:17/:19 precede 0x88f90 :34)
  S3 trade_v3.rs: add() after validate_trade() (orig 0x7e0b0 :149 precedes 0x81848 add :390)
  S4 InitUserVolume accounts struct lib.rs -> token_incentives/init_user_volume_accumulator.rs
       (orig 0xfdf20 try_accounts site token_incentives/init_user_volume_accumulator.rs:8)
  S5 nested_create.rs inlined as `mod nested_create {..}` at the end of create_v2.rs
       (orig 0x19cc0 walk closure site create_v2.rs:412; ancestor/walk sites create_v2.rs:345..473)
"""
import re, sys
from pathlib import Path

S = Path(sys.argv[1]) / 'src'
done = []


def rd(p):
    return (S / p).read_text()


def wr(p, t):
    (S / p).write_text(t)


def step(name):
    def deco(f):
        f(); done.append(name)
        return f
    return deco


@step('S1 buy_v2 admit before BuyV2')
def s1():
    t = rd('buy_v2.rs')
    start = '// Shared main-program admission for an ATA, including the optional idempotent creation.\n#[inline(never)]\npub fn admit_associated_token_account'
    i = t.index(start)
    j = t.index('\n}\n', i) + 3
    blk = t[i:j]
    t = t[:i] + t[j:]
    t = t.rstrip('\n') + '\n'
    k = t.index('#[derive(Accounts)]\npub struct BuyV2')
    t = t[:k] + blk + t[k:]
    wr('buy_v2.rs', t)


@step('S2 fee.rs checked_ceil_div before fee')
def s2():
    t = rd('util/fee.rs')
    fee_fn = ('pub fn fee(quote_amount: u64, basis_points: u64) -> Result<u64> {\n'
              '    let value = checked_ceil_div(u128::from(quote_amount) * u128::from(basis_points), 10000)?;\n'
              '    u64::try_from(value).map_err(|_| error!(crate::PumpError::Truncation))\n}\n')
    assert t.count(fee_fn) == 1
    t = t.replace(fee_fn + '\n', '', 1)
    t = t.rstrip('\n') + '\n\n' + fee_fn
    wr('util/fee.rs', t)


@step('S3 trade_v3 add after validate_trade')
def s3():
    t = rd('trade_v3.rs')
    add_line = 'fn add(a:u64,b:u64)->Result<u64>{a.checked_add(b).ok_or_else(||error!(PumpError::Overflow))}\n'
    assert t.count(add_line) == 1
    t = t.replace(add_line, '', 1)
    vt_end = ('        require!(cashback==0,PumpError::CashbackCoinNotSupported);\n'
              '    }\n    Ok(())\n}\n')
    assert t.count(vt_end) == 1
    t = t.replace(vt_end, vt_end + add_line, 1)
    wr('trade_v3.rs', t)


@step('S4 InitUserVolume -> token_incentives/init_user_volume_accumulator.rs')
def s4():
    L = rd('lib.rs')
    m = re.search(r"#\[event_cpi\]\n#\[derive\(Accounts\)\]\npub struct InitUserVolume<'info>\{\n.*?\n\}\n", L, re.S)
    assert m
    blk = m.group(0)
    L = L[:m.start()] + L[m.end():]
    wr('lib.rs', L)
    body = ('use anchor_lang::prelude::*;\n\n'
            'use super::volume_accumulator::UserVolumeAccumulator;\n\n'
            + blk)
    wr('token_incentives/init_user_volume_accumulator.rs', body)
    mod = rd('token_incentives/mod.rs')
    assert 'pub mod volume_accumulator;\n' in mod
    mod = mod.replace('pub mod volume_accumulator;\n', 'pub mod volume_accumulator;\npub mod init_user_volume_accumulator;\n', 1)
    mod = mod.rstrip('\n') + '\npub use init_user_volume_accumulator::*;\n'
    wr('token_incentives/mod.rs', mod)


@step('S5 inline nested_create into create_v2.rs')
def s5():
    cv = rd('create_v2.rs')
    decl = '#[path = "nested_create.rs"]\nmod nested_create;\n'
    assert cv.count(decl) == 1
    cv = cv.replace(decl, '', 1)
    nc = rd('nested_create.rs')
    cv = cv.rstrip('\n') + '\n\nmod nested_create {\n' + nc.rstrip('\n') + '\n}\n'
    wr('create_v2.rs', cv)
    (S / 'nested_create.rs').unlink()


@step('S6 trade_v3 sell after buy_exact_quote')
def s6():
    # original order: buy_v3 handler 0x147ba0 (trade_v3.rs:801..842) < buy_exact_quote_in_v3 0x1489f8
    # (:881..1001) < sell_v3 0x14a8a8 (:1126..1155); ours had sell first.
    t = rd('trade_v3.rs')
    i = t.index('pub fn sell(ctx:Context<SellV3>,amount:u64,min_sol_output:u64)->Result<()> {\n')
    j = t.index('\n}\n', i) + 3
    blk = t[i:j]
    t = t[:i] + t[j:].lstrip('\n')
    k = t.index('pub fn buy_exact_quote(ctx:Context<SellV3>,')
    e = t.index('\n}\n', k) + 3
    t = t[:e] + '\n' + blk + t[e:]
    wr('trade_v3.rs', t)


@step('S7 distribution.rs handlers -> creator/distribute_creator_fees.rs + creator/distribute_creator_fee_v2.rs')
def s7():
    # orig: creator/distribute_creator_fees.rs  0x311f8 (:103..158 amounts helper), 0x32840 (:241 SharingConfigNotActive,
    #       :249 CreatorFeesNotSwept = handler); creator/distribute_creator_fee_v2.rs 0x2bf18 (:101..168 token amounts
    #       helper), 0x2d920 (:205/:213 handler v2).  Shared account types stay in distribution.rs (SharingConfig is a
    #       lib.rs item in the original, lib.rs:84 - coordlib lane).
    t = rd('distribution.rs')
    def cut(start, end_pat='\n}\n'):
        nonlocal t
        i = t.index(start); j = t.index(end_pat, i) + len(end_pat)
        blk = t[i:j]; t = t[:i] + t[j:]
        return blk
    s1 = cut('#[derive(Accounts)]\npub struct DistributeCreatorFees<\'info>{')
    e1 = cut("pub fn execute<'info>(ctx:Context<'_, '_, '_, 'info,DistributeCreatorFees<'info>>)")
    s2 = cut('#[derive(Accounts)]\npub struct DistributeCreatorFeesV2<\'info>{')
    e2 = cut("pub fn execute_v2<'info>(ctx:Context<'_, '_, '_, 'info,DistributeCreatorFeesV2<'info>>")
    h1 = cut("pub(crate) fn get_distribution_amounts<'info>(")
    h2 = cut("#[inline(never)]\npub fn get_token_distribution_amounts(")
    while '\n\n\n' in t:
        t = t.replace('\n\n\n', '\n\n')
    t = t.rstrip('\n') + ('\n\n#[path="creator/distribute_creator_fees.rs"]\npub mod distribute_creator_fees;\npub use distribute_creator_fees::*;\n'
                         '#[path="creator/distribute_creator_fee_v2.rs"]\npub mod distribute_creator_fee_v2;\npub use distribute_creator_fee_v2::*;\n')
    wr('distribution.rs', t)
    head = ('use anchor_lang::prelude::*;\n'
            'use crate::{PumpError,trade_types::{Shareholder,BondingCurve}};\n'
            'use crate::distribution::{FEES,ConfigStatus,SharingConfig,DistributeCreatorFeesEvent};\n')
    wr('creator/distribute_creator_fees.rs', head + '\n' + s1 + '\n' + h1 + '\n' + e1)
    wr('creator/distribute_creator_fee_v2.rs', head + 'use crate::distribution::get_distribution_amounts;\n\n' + s2 + '\n' + h2 + '\n' + e2)


@step('S8 cashback claims -> token_incentives/claim_token_incentives.rs (nested mod cashback)')
def s8():
    # orig: claim_cashback 0x76a28 (Overflow x2 at token_incentives/claim_token_incentives.rs:252) and
    # claim_cashback_v2 0x77940 (:305 6064, :310 6010, :333 6010, :342 6076 = ours 6010/6010/6076) live in
    # claim_token_incentives.rs after the token-incentive claim.  Nested module keeps the item names
    # (`claim` already exists there); cashback.rs re-exports it so lib.rs paths are unchanged.
    c = rd('cashback.rs')
    t = rd('token_incentives/claim_token_incentives.rs')
    body = '\n'.join((' ' + l) if l else l for l in c.rstrip('\n').split('\n'))
    t = t.rstrip('\n') + '\n\npub mod cashback {\n' + body + '\n}\n'
    wr('token_incentives/claim_token_incentives.rs', t)
    wr('cashback.rs', 'pub use crate::token_incentives::claim_token_incentives::cashback::*;\n')


print('applied:', *done, sep='\n  ')
