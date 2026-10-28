#!/usr/bin/env python3
"""coordlib round 2, step 2 (after restructure.py, before layout.py): lib.rs-origin sites that need small body changes.

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


# ---------------------------------------------------------------- A. SharingConfig impl -> macro expanded at lib.rs:84
d = (S / 'distribution.rs').read_text()
old_impl = d[d.index('impl AccountDeserialize for SharingConfig {'):]
old_impl = old_impl[:old_impl.index('\n}\n') + 3]
new_impl = '''// Expanded on the `declare_program!(pump_fees)` line of lib.rs, where the original's generated SharingConfig
// account impl lives (orig Source lib.rs:84).
#[macro_export]
macro_rules! sharing_config_account_deserialize {
    () => {
impl anchor_lang::AccountDeserialize for $crate::distribution::SharingConfig {
    fn try_deserialize(buf: &mut &[u8]) -> anchor_lang::Result<Self> {
        if buf.len() < <Self as anchor_lang::Discriminator>::DISCRIMINATOR.len() {
            return Err(anchor_lang::error::ErrorCode::AccountDiscriminatorNotFound.into());
        }
        let given_disc = &buf[..<Self as anchor_lang::Discriminator>::DISCRIMINATOR.len()];
        if <Self as anchor_lang::Discriminator>::DISCRIMINATOR != given_disc {
            return Err(anchor_lang::error!(anchor_lang::error::ErrorCode::AccountDiscriminatorMismatch).with_account_name("SharingConfig"));
        }
        Self::try_deserialize_unchecked(buf)
    }
    fn try_deserialize_unchecked(buf: &mut &[u8]) -> anchor_lang::Result<Self> {
        let mut data: &[u8] = &buf[<Self as anchor_lang::Discriminator>::DISCRIMINATOR.len()..];
        anchor_lang::AnchorDeserialize::deserialize(&mut data)
            .map_err(|_| anchor_lang::error::ErrorCode::AccountDidNotDeserialize.into())
    }
}
    };
}
'''
assert 'Self::DISCRIMINATOR' in old_impl and 'with_account_name("SharingConfig")' in old_impl
d = d.replace(old_impl, new_impl, 1)
(S / 'distribution.rs').write_text(d)
edit('lib.rs', 'declare_program!(pump_fees);\n', 'declare_program!(pump_fees); crate::sharing_config_account_deserialize!();\n')

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

# ---------------------------------------------------------------- C. boost check through pump_amm::accounts::GlobalConfig
m = (S / 'migration_native_payments.rs').read_text()
i = m.index('#[derive(AnchorDeserialize)]\nstruct AmmConfigBase {')
m = m[:i] + '''pub(crate) fn boost_enabled(config: &AccountInfo) -> bool {
    let Ok(data) = config.try_borrow_data() else { return false };
    let global_config = crate::pump_amm::accounts::GlobalConfig::try_deserialize(&mut &data[..]);
    global_config.map(|c| c.boost_enabled).unwrap_or(false)
}
'''
(S / 'migration_native_payments.rs').write_text(m)
print('changes2 applied')

# ---------------------------------------------------------------- D. pump_amm GlobalConfig as the original's IDL had it
# orig 0x1091b0 (GlobalConfig::try_deserialize) writes the Result::Err niche at struct offset 0x3a3 = boost_enabled,
# i.e. the original's pump_amm IDL GlobalConfig ended at boost_enabled (no creator_fee_configurable /
# max_configurable_creator_fee_bps, 9 bytes); orig 0x524f0 reads boost_enabled from that same niche byte.
I = Path(sys.argv[1]) / 'idls/pump_amm.json'
t = I.read_text()
old = ('''            "name": "boost_enabled",
            "type": "bool"
          },
          {
            "name": "creator_fee_configurable",
            "type": "bool"
          },
          {
            "name": "max_configurable_creator_fee_bps",
            "type": "u64"
          }
        ]''')
new = ('''            "name": "boost_enabled",
            "type": "bool"
          }
        ]''')
assert t.count(old) == 1, t.count(old)
I.write_text(t.replace(old, new, 1))
print('changes2 D applied (pump_amm GlobalConfig without creator fee fields)')
