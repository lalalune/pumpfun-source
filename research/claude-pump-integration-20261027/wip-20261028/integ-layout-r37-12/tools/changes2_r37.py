#!/usr/bin/env python3
"""[integ-layout r37 copy of coordlib changes2.py: section B only.
  A (SharingConfig impl at the pump_fees declare_program! line) is obsolete on Round37: distribution.rs already uses the
  generated crate::pump_fees::accounts::SharingConfig.  C/D (boost_enabled via pump_amm GlobalConfig, IDL trim) are in
  the r37g5 base (libnear3-01).]
coordlib round 2, step 2 (after restructure.py, before layout.py): lib.rs-origin sites that need small body changes.

  A. SharingConfig AccountDeserialize impl (distribution.rs) becomes a #[macro_export] macro expanded on the
     `declare_program!(pump_fees)` line of lib.rs (orig 0x115e70 Source lib.rs:84 is the declare_program-generated
     impl; our hand-written impl is byte-identical except Source). SYNTHETIC placement device.
  B. impl Global gains `validate_buyback_fee_recipient` (orig 0x98438, lib.rs:1879 require_keys_neq! 6062 /
     1884 require! 6057, between set_buyback_basis_points and set_buyback_fee_recipients; takes &Global - recipients
     at offset 0 of Global's layout - and the key); the inline duplicates in buy_v2 / sell_v2 / trade_v3 / legacy
     buy / legacy sell call it (orig callers 0x13b9b8, 0x13f630, 0x144508, 0x7e490 x2, 0x6f3e8). Line counts kept.
  C. migrate boost check reads pump_amm's GlobalConfig through the declare_program!(pump_amm) client
     (orig 0x524f0 -> 0x1091b0 = GlobalConfig::try_deserialize, Source lib.rs:83).
Usage: changes2.py <crate dir>
"""
import re, sys
from pathlib import Path

S = Path(sys.argv[1]) / 'src'


def edit(p, old, new, count=1):
    """count=None: replace every occurrence (at least one) - call sites may be duplicated by other lanes' splits."""
    f = S / p
    t = f.read_text()
    n = t.count(old)
    assert (n >= 1) if count is None else (n == count), (p, n, old[:80])
    if count is None:
        print(f'  {p}: {n} call site(s)')
    f.write_text(t.replace(old, new))


# ---------------------------------------------------------------- B. Global::validate_buyback_fee_recipient
L = (S / 'lib.rs').read_text()
anchor = '''  self.buyback_basis_points=value;
  Ok(())
 }
'''
assert L.count(anchor) == 1
method = anchor + ''' #[inline(never)]
 pub fn validate_buyback_fee_recipient(&self,buyback_fee_recipient:Pubkey)->Result<()>{
  require_keys_neq!(buyback_fee_recipient,Pubkey::default(),PumpError::BuybackFeeRecipientMissing);
  require!(self.buyback_fee_recipients.contains(&buyback_fee_recipient),PumpError::BuybackFeeRecipientNotAuthorized);
  Ok(())
 }
'''
(S / 'lib.rs').write_text(L.replace(anchor, method, 1))

edit('buy_v2.rs',
     ' require_keys_neq!(a.buyback_fee_recipient.key(),Pubkey::default(),PumpError::BuybackFeeRecipientMissing);\n'
     ' require!(a.global.buyback_fee_recipients.contains(&a.buyback_fee_recipient.key()),PumpError::BuybackFeeRecipientNotAuthorized);\n',
     ' a.global.validate_buyback_fee_recipient(a.buyback_fee_recipient.key())?;\n\n', count=None)
edit('sell_v2.rs',
     'let bb=&a.buyback_fee_recipient;require_keys_neq!(*bb.key,Pubkey::default(),PumpError::BuybackFeeRecipientMissing);require!(a.global.buyback_fee_recipients.contains(bb.key),PumpError::BuybackFeeRecipientNotAuthorized);',
     'let bb=&a.buyback_fee_recipient;a.global.validate_buyback_fee_recipient(*bb.key)?;', count=None)
edit('trade_v3.rs',
     'if is_sol{require_keys_neq!(a.buyback_fee_recipient.key(),Pubkey::default(),PumpError::BuybackFeeRecipientMissing);require!(a.global.buyback_fee_recipients.contains(&a.buyback_fee_recipient.key()),PumpError::BuybackFeeRecipientNotAuthorized);}',
     'if is_sol{a.global.validate_buyback_fee_recipient(a.buyback_fee_recipient.key())?;}', count=None)
edit('trade_v3.rs',
     'if role==2{require_keys_neq!(token.owner,Pubkey::default(),PumpError::BuybackFeeRecipientMissing);require!(a.global.buyback_fee_recipients.contains(&token.owner),PumpError::BuybackFeeRecipientNotAuthorized)}',
     'if role==2{a.global.validate_buyback_fee_recipient(token.owner)?}', count=None)
edit('buy.rs',
     'require_keys_neq!(*bb.key,Pubkey::default(),PumpError::BuybackFeeRecipientMissing);require!(a.global.buyback_fee_recipients.contains(bb.key),PumpError::BuybackFeeRecipientNotAuthorized);',
     'a.global.validate_buyback_fee_recipient(*bb.key)?;')
edit('sell.rs',
     'require!(a.global.buyback_fee_recipients.contains(bb.key),PumpError::BuybackFeeRecipientNotAuthorized);',
     'a.global.validate_buyback_fee_recipient(*bb.key)?;')

print('changes2 (r37: B only) applied')
