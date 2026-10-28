use anchor_lang::prelude::*;
#[derive(AnchorSerialize, AnchorDeserialize, Clone)]
pub struct BondingCurve {
    pub virtual_token_reserves: u64,
    pub virtual_quote_reserves: u64,
    pub real_token_reserves: u64,
    pub real_quote_reserves: u64,
    pub token_total_supply: u64,
    pub complete: bool,
    pub creator: Pubkey,
    pub is_mayhem_mode: bool,
    pub is_cashback_coin: bool,
    pub quote_mint: Pubkey,
    pub creator_fee_bps: u64,
    pub can_edit_creator_fee: bool,
    pub is_holder_reward: bool,
    pub creator_fee: u64,
    pub protocol_fees: u64,
    pub depth: u8,
    pub initial_virtual_quote_reserves: u64,
    pub post_complete_base_out: u64,
    pub post_complete_quote_in: u64,
}
impl anchor_lang::Discriminator for BondingCurve {
    const DISCRIMINATOR: &'static [u8] = &[23, 183, 248, 55, 96, 216, 172, 96];
}
impl anchor_lang::Owner for BondingCurve {
    fn owner() -> Pubkey { crate::ID }
}
impl anchor_lang::AccountSerialize for BondingCurve {
    fn try_serialize<W: std::io::Write>(&self, writer: &mut W) -> Result<()> {
        writer.write_all(Self::DISCRIMINATOR)?;
        AnchorSerialize::serialize(self, writer)?;
        Ok(())
    }
}
// Source proposal only: original checked 0x9b148 and unchecked 0x9b430.
// Account owner/lamports/borrow checks and field-name errors belong to Anchor.
impl anchor_lang::AccountDeserialize for BondingCurve {
    #[inline(never)]
    fn try_deserialize(buf: &mut &[u8]) -> Result<Self> {
        if buf.len() < Self::DISCRIMINATOR.len()
            || &buf[..Self::DISCRIMINATOR.len()] != Self::DISCRIMINATOR
        {
            return Err(anchor_lang::solana_program::program_error::ProgramError::InvalidAccountData.into());
        }
        Self::try_deserialize_unchecked(buf)
    }

    fn try_deserialize_unchecked(buf: &mut &[u8]) -> Result<Self> {
        if buf.len() < Self::DISCRIMINATOR.len() {
            return Err(anchor_lang::solana_program::program_error::ProgramError::InvalidAccountData.into());
        }
        *buf = &buf[Self::DISCRIMINATOR.len()..];
        decode_original_curve_payload(buf)
    }
}

// Recovered historical layout dispatch. Each Borsh layout owns one complete
// version; bytes between complete layout boundaries are not decoded.
fn decode_original_curve_payload(buf: &mut &[u8]) -> Result<BondingCurve> {
    let n = buf.len();
    if n < 41 {
        return Err(anchor_lang::solana_program::program_error::ProgramError::InvalidAccountData.into());
    }
    if n < 73 { return historical_curve::decode_v0(buf); }
    if n == 73 { return historical_curve::decode_v1(buf); }
    if n < 75 { return historical_curve::decode_v2(buf); }
    if n < 107 { return historical_curve::decode_v3(buf); }
    if n < 116 { return historical_curve::decode_v4(buf); }
    if n == 116 { return historical_curve::decode_v5(buf); }
    if n < 133 { return historical_curve::decode_v6(buf); }
    if n < 158 { return historical_curve::decode_v7(buf); }
    historical_curve::decode_v8(buf)
}

mod historical_curve {
    use super::*;

    // Preserve the observed decoder boundary and per-field Anchor error conversion.
    #[inline(never)]
    pub(super) fn decode_v0(buf: &mut &[u8]) -> Result<BondingCurve> {
        Ok(BondingCurve {
            virtual_token_reserves: u64::deserialize(buf).map_err(anchor_lang::error::Error::from)?,
            virtual_quote_reserves: u64::deserialize(buf).map_err(anchor_lang::error::Error::from)?,
            real_token_reserves: u64::deserialize(buf).map_err(anchor_lang::error::Error::from)?,
            real_quote_reserves: u64::deserialize(buf).map_err(anchor_lang::error::Error::from)?,
            token_total_supply: u64::deserialize(buf).map_err(anchor_lang::error::Error::from)?,
            complete: bool::deserialize(buf).map_err(anchor_lang::error::Error::from)?,
            creator: Pubkey::default(),
            is_mayhem_mode: false,
            is_cashback_coin: false,
            quote_mint: Pubkey::default(),
            creator_fee_bps: 0,
            can_edit_creator_fee: false,
            is_holder_reward: false,
            creator_fee: 0,
            protocol_fees: 0,
            depth: 0,
            initial_virtual_quote_reserves: 0,
            post_complete_base_out: 0,
            post_complete_quote_in: 0,
        })
    }

    // Preserve the observed decoder boundary and per-field Anchor error conversion.
    #[inline(never)]
    pub(super) fn decode_v1(buf: &mut &[u8]) -> Result<BondingCurve> {
        Ok(BondingCurve {
            virtual_token_reserves: u64::deserialize(buf)?,
            virtual_quote_reserves: u64::deserialize(buf)?,
            real_token_reserves: u64::deserialize(buf)?,
            real_quote_reserves: u64::deserialize(buf)?,
            token_total_supply: u64::deserialize(buf)?,
            complete: bool::deserialize(buf)?,
            creator: Pubkey::deserialize(buf)?,
            is_mayhem_mode: false,
            is_cashback_coin: false,
            quote_mint: Pubkey::default(),
            creator_fee_bps: 0,
            can_edit_creator_fee: false,
            is_holder_reward: false,
            creator_fee: 0,
            protocol_fees: 0,
            depth: 0,
            initial_virtual_quote_reserves: 0,
            post_complete_base_out: 0,
            post_complete_quote_in: 0,
        })
    }

    // Preserve the observed decoder boundary and per-field Anchor error conversion.
    #[inline(never)]
    pub(super) fn decode_v2(buf: &mut &[u8]) -> Result<BondingCurve> {
        Ok(BondingCurve {
            virtual_token_reserves: u64::deserialize(buf)?,
            virtual_quote_reserves: u64::deserialize(buf)?,
            real_token_reserves: u64::deserialize(buf)?,
            real_quote_reserves: u64::deserialize(buf)?,
            token_total_supply: u64::deserialize(buf)?,
            complete: bool::deserialize(buf)?,
            creator: Pubkey::deserialize(buf)?,
            is_mayhem_mode: bool::deserialize(buf)?,
            is_cashback_coin: false,
            quote_mint: Pubkey::default(),
            creator_fee_bps: 0,
            can_edit_creator_fee: false,
            is_holder_reward: false,
            creator_fee: 0,
            protocol_fees: 0,
            depth: 0,
            initial_virtual_quote_reserves: 0,
            post_complete_base_out: 0,
            post_complete_quote_in: 0,
        })
    }

    // Preserve the observed decoder boundary and per-field Anchor error conversion.
    #[inline(never)]
    pub(super) fn decode_v3(buf: &mut &[u8]) -> Result<BondingCurve> {
        Ok(BondingCurve {
            virtual_token_reserves: u64::deserialize(buf)?,
            virtual_quote_reserves: u64::deserialize(buf)?,
            real_token_reserves: u64::deserialize(buf)?,
            real_quote_reserves: u64::deserialize(buf)?,
            token_total_supply: u64::deserialize(buf)?,
            complete: bool::deserialize(buf)?,
            creator: Pubkey::deserialize(buf)?,
            is_mayhem_mode: bool::deserialize(buf)?,
            is_cashback_coin: bool::deserialize(buf)?,
            quote_mint: Pubkey::default(),
            creator_fee_bps: 0,
            can_edit_creator_fee: false,
            is_holder_reward: false,
            creator_fee: 0,
            protocol_fees: 0,
            depth: 0,
            initial_virtual_quote_reserves: 0,
            post_complete_base_out: 0,
            post_complete_quote_in: 0,
        })
    }

    // Preserve the observed decoder boundary and per-field Anchor error conversion.
    #[inline(never)]
    pub(super) fn decode_v4(buf: &mut &[u8]) -> Result<BondingCurve> {
        Ok(BondingCurve {
            virtual_token_reserves: u64::deserialize(buf)?,
            virtual_quote_reserves: u64::deserialize(buf)?,
            real_token_reserves: u64::deserialize(buf)?,
            real_quote_reserves: u64::deserialize(buf)?,
            token_total_supply: u64::deserialize(buf)?,
            complete: bool::deserialize(buf)?,
            creator: Pubkey::deserialize(buf)?,
            is_mayhem_mode: bool::deserialize(buf)?,
            is_cashback_coin: bool::deserialize(buf)?,
            quote_mint: Pubkey::deserialize(buf)?,
            creator_fee_bps: 0,
            can_edit_creator_fee: false,
            is_holder_reward: false,
            creator_fee: 0,
            protocol_fees: 0,
            depth: 0,
            initial_virtual_quote_reserves: 0,
            post_complete_base_out: 0,
            post_complete_quote_in: 0,
        })
    }

    // Preserve the observed decoder boundary and per-field Anchor error conversion.
    #[inline(never)]
    pub(super) fn decode_v5(buf: &mut &[u8]) -> Result<BondingCurve> {
        Ok(BondingCurve {
            virtual_token_reserves: u64::deserialize(buf)?,
            virtual_quote_reserves: u64::deserialize(buf)?,
            real_token_reserves: u64::deserialize(buf)?,
            real_quote_reserves: u64::deserialize(buf)?,
            token_total_supply: u64::deserialize(buf)?,
            complete: bool::deserialize(buf)?,
            creator: Pubkey::deserialize(buf)?,
            is_mayhem_mode: bool::deserialize(buf)?,
            is_cashback_coin: bool::deserialize(buf)?,
            quote_mint: Pubkey::deserialize(buf)?,
            creator_fee_bps: u64::deserialize(buf)?,
            can_edit_creator_fee: bool::deserialize(buf)?,
            is_holder_reward: false,
            creator_fee: 0,
            protocol_fees: 0,
            depth: 0,
            initial_virtual_quote_reserves: 0,
            post_complete_base_out: 0,
            post_complete_quote_in: 0,
        })
    }

    // Preserve the observed decoder boundary and per-field Anchor error conversion.
    #[inline(never)]
    pub(super) fn decode_v6(buf: &mut &[u8]) -> Result<BondingCurve> {
        Ok(BondingCurve {
            virtual_token_reserves: u64::deserialize(buf)?,
            virtual_quote_reserves: u64::deserialize(buf)?,
            real_token_reserves: u64::deserialize(buf)?,
            real_quote_reserves: u64::deserialize(buf)?,
            token_total_supply: u64::deserialize(buf)?,
            complete: bool::deserialize(buf)?,
            creator: Pubkey::deserialize(buf)?,
            is_mayhem_mode: bool::deserialize(buf)?,
            is_cashback_coin: bool::deserialize(buf)?,
            quote_mint: Pubkey::deserialize(buf)?,
            creator_fee_bps: u64::deserialize(buf)?,
            can_edit_creator_fee: bool::deserialize(buf)?,
            is_holder_reward: bool::deserialize(buf)?,
            creator_fee: 0,
            protocol_fees: 0,
            depth: 0,
            initial_virtual_quote_reserves: 0,
            post_complete_base_out: 0,
            post_complete_quote_in: 0,
        })
    }

    // Preserve the observed decoder boundary and per-field Anchor error conversion.
    #[inline(never)]
    pub(super) fn decode_v7(buf: &mut &[u8]) -> Result<BondingCurve> {
        Ok(BondingCurve {
            virtual_token_reserves: u64::deserialize(buf)?,
            virtual_quote_reserves: u64::deserialize(buf)?,
            real_token_reserves: u64::deserialize(buf)?,
            real_quote_reserves: u64::deserialize(buf)?,
            token_total_supply: u64::deserialize(buf)?,
            complete: bool::deserialize(buf)?,
            creator: Pubkey::deserialize(buf)?,
            is_mayhem_mode: bool::deserialize(buf)?,
            is_cashback_coin: bool::deserialize(buf)?,
            quote_mint: Pubkey::deserialize(buf)?,
            creator_fee_bps: u64::deserialize(buf)?,
            can_edit_creator_fee: bool::deserialize(buf)?,
            is_holder_reward: bool::deserialize(buf)?,
            creator_fee: u64::deserialize(buf)?,
            protocol_fees: u64::deserialize(buf)?,
            depth: 0,
            initial_virtual_quote_reserves: 0,
            post_complete_base_out: 0,
            post_complete_quote_in: 0,
        })
    }

    // Preserve the observed decoder boundary and per-field Anchor error conversion.
    #[inline(never)]
    pub(super) fn decode_v8(buf: &mut &[u8]) -> Result<BondingCurve> {
        Ok(BondingCurve {
            virtual_token_reserves: u64::deserialize(buf)?,
            virtual_quote_reserves: u64::deserialize(buf)?,
            real_token_reserves: u64::deserialize(buf)?,
            real_quote_reserves: u64::deserialize(buf)?,
            token_total_supply: u64::deserialize(buf)?,
            complete: bool::deserialize(buf)?,
            creator: Pubkey::deserialize(buf)?,
            is_mayhem_mode: bool::deserialize(buf)?,
            is_cashback_coin: bool::deserialize(buf)?,
            quote_mint: Pubkey::deserialize(buf)?,
            creator_fee_bps: u64::deserialize(buf)?,
            can_edit_creator_fee: bool::deserialize(buf)?,
            is_holder_reward: bool::deserialize(buf)?,
            creator_fee: u64::deserialize(buf)?,
            protocol_fees: u64::deserialize(buf)?,
            depth: u8::deserialize(buf)?,
            initial_virtual_quote_reserves: u64::deserialize(buf)?,
            post_complete_base_out: u64::deserialize(buf)?,
            post_complete_quote_in: u64::deserialize(buf)?,
        })
    }
}
// Original shared preparation 0x3cd50 and rent funding 0x3d250.
// The Account is already decoded; temporary AccountInfo clones do not keep a
// data borrow alive across the System CPI or realloc. No state reload follows.
#[inline(never)]
pub fn prepare_bonding_curve<'info>(
    curve: &Account<'info, BondingCurve>,
    system_program: &Program<'info, System>,
    payer: &Signer<'info>,
) -> Result<()> {
    let current_size = curve.to_account_info().data_len();
    let funding = fund_bonding_curve_rent(curve, system_program, payer, current_size.max(166));
    if funding.is_ok() && current_size < 166 {
        curve.to_account_info().realloc(166, false)?;
    }
    funding
}

#[inline(never)]
pub fn reserved_bonding_curve_fees(curve: &BondingCurve) -> Result<u64> {
    curve.creator_fee.checked_add(curve.protocol_fees)
        .ok_or_else(|| error!(crate::PumpError::Overflow))
}

#[inline(never)]
pub fn fund_bonding_curve_rent<'info>(
    curve: &Account<'info, BondingCurve>,
    system_program: &Program<'info, System>,
    payer: &Signer<'info>,
    size: usize,
) -> Result<()> {
    let reserved = if curve.quote_mint == Pubkey::default() {
        let fees = reserved_bonding_curve_fees(curve)?;
        curve.real_quote_reserves.checked_add(fees)
            .ok_or_else(|| error!(crate::PumpError::Overflow))?
    } else {
        0
    };
    let minimum = Rent::get()?.minimum_balance(size);
    let available = curve.to_account_info().lamports().saturating_sub(reserved);
    if minimum > available {
        anchor_lang::system_program::transfer(
            CpiContext::new(
                system_program.to_account_info(),
                anchor_lang::system_program::Transfer {
                    from: payer.to_account_info(),
                    to: curve.to_account_info(),
                },
            ),
            minimum.saturating_sub(available),
        )?;
    }
    Ok(())
}

pub use crate::TradeEvent;
pub use crate::pump_fees::{
    accounts::FeeConfig,
    types::{FeeTier, Fees, Shareholder},
};

#[event]
#[derive(Clone)]
pub struct CompleteEvent {pub user:Pubkey,pub mint:Pubkey,pub bonding_curve:Pubkey,pub timestamp:i64,pub quote_mint:Pubkey}
