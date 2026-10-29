#[path = "fee_recipient.rs"]
pub(crate) mod fee_recipient;
use anchor_lang::prelude::*;
use anchor_spl::token_interface::{self,Mint,TokenAccount,TokenInterface,TransferChecked};
use crate::{Global,PumpError};
use crate::trade_types::{BondingCurve,TradeEvent};

#[derive(Clone)]pub struct LegacyCurve(pub BondingCurve,pub usize);
impl std::ops::Deref for LegacyCurve{type Target=BondingCurve;fn deref(&self)->&BondingCurve{&self.0}}
impl std::ops::DerefMut for LegacyCurve{fn deref_mut(&mut self)->&mut BondingCurve{&mut self.0}}
impl Owner for LegacyCurve{fn owner()->Pubkey{crate::ID}}
impl AccountDeserialize for LegacyCurve{fn try_deserialize(buf:&mut &[u8])->Result<Self>{let len=buf.len();Ok(Self(BondingCurve::try_deserialize(buf)?,len))}fn try_deserialize_unchecked(buf:&mut &[u8])->Result<Self>{Self::try_deserialize(buf)}}
impl AccountSerialize for LegacyCurve{fn try_serialize<W:std::io::Write>(&self,w:&mut W)->Result<()>{let mut b=Vec::new();self.0.try_serialize(&mut b)?;w.write_all(&b[..self.1.min(b.len())])?;Ok(())}}
pub use crate::pump_fees::{
    accounts::FeeConfig as LegacyFeeConfig,
    program::PumpFees as LegacyFeesProgram,
};

fn process_cashback_inner<'info>(
    remaining_accounts: &'info [AccountInfo<'info>], user: &AccountInfo<'info>, system_program: &AccountInfo<'info>,
    bonding_curve: &Account<'info, BondingCurve>, amount: u64, mint: &Pubkey,
) -> Result<()> {
    let user_volume_accumulator = remaining_accounts.first().ok_or_else(|| error!(PumpError::MissingCashbackAccounts))?;
    let user_key = user.key();
    let (expected, bump) = Pubkey::find_program_address(&[b"user_volume_accumulator", user_key.as_ref()], &crate::ID);
// layout-pad(7): aligns the next Source site with the original line






    require!(user_volume_accumulator.key() == expected, PumpError::InvalidCashbackAccumulator);
    if user_volume_accumulator.data_is_empty() {
        let rent = Rent::get()?;
        let space = 137;
        let lamports = rent.minimum_balance(space);
        let seeds = &[b"user_volume_accumulator".as_ref(), user_key.as_ref(), &[bump]]; let signer_seeds = &[&seeds[..]];
        let required_lamports = lamports.saturating_sub(user_volume_accumulator.lamports());
        if required_lamports > 0 {
            anchor_lang::system_program::transfer(
                CpiContext::new(
                    system_program.clone(),
                    anchor_lang::system_program::Transfer { from: user.clone(), to: user_volume_accumulator.clone() },
                ),
                required_lamports,
            )?;
        }
        anchor_lang::solana_program::program::invoke_signed(
            &anchor_lang::solana_program::system_instruction::allocate(user_volume_accumulator.key, space as u64),
            &[user_volume_accumulator.clone()],
            signer_seeds,
        )?;
        anchor_lang::solana_program::program::invoke_signed(
            &anchor_lang::solana_program::system_instruction::assign(user_volume_accumulator.key, &crate::ID),
            &[user_volume_accumulator.clone()],
            signer_seeds,
        )?;
        let mut data = user_volume_accumulator.try_borrow_mut_data()?;
// layout-pad(16): aligns the next panic Location with the original line















        data[..8].copy_from_slice(crate::UserVolumeAccumulator::DISCRIMINATOR);
        data[8..40].copy_from_slice(user_key.as_ref());

    } else { check_existing(user_volume_accumulator)?; }
    fn check_existing(user_volume_accumulator: &AccountInfo) -> Result<()> {
        require!(user_volume_accumulator.owner == &crate::ID, PumpError::InvalidCashbackAccumulator);
        let data = user_volume_accumulator.try_borrow_data()?;
// layout-pad(2): aligns the next Source site with the original line

        require!(data.len() >= 8 && &data[..8] == crate::UserVolumeAccumulator::DISCRIMINATOR, PumpError::InvalidCashbackAccumulator);
        Ok(()) }
    crate::trade::quote_payments::transfer_native(bonding_curve, user_volume_accumulator, amount)?;
    let mut user_volume_accumulator = Account::<crate::UserVolumeAccumulator>::try_from(user_volume_accumulator)?;
    if user_volume_accumulator.user == Pubkey::default() {
        user_volume_accumulator.user = user_key;
    }
// layout-pad(10): aligns the next Source site with the original line









    user_volume_accumulator.cashback_earned = user_volume_accumulator.cashback_earned.checked_add(amount).ok_or(error!(PumpError::Overflow))?;
    user_volume_accumulator.exit(&crate::ID)?;
// layout-pad(3): aligns the next Source site with the original line


    require!(remaining_accounts.len() > 1, PumpError::InvalidBondingCurveV2);
    let bonding_curve_v2 = &remaining_accounts[1];
    let (expected, _) = Pubkey::find_program_address(&[b"bonding-curve-v2", mint.as_ref()], &crate::ID);
// layout-pad(4): aligns the next Source site with the original line



    require!(bonding_curve_v2.key() == expected, PumpError::InvalidBondingCurveV2);
    Ok(())
}
#[derive(Accounts)]
pub struct LegacySell<'info>{
 #[account(seeds=[b"global"],bump)]pub global:Box<Account<'info,Global>>,#[doc="CHECK: handler validates recipient."]#[account(mut)]pub fee_recipient:UncheckedAccount<'info>,pub mint:InterfaceAccount<'info,Mint>,#[account(mut,seeds=[b"bonding-curve",mint.key().as_ref()],bump,constraint=bonding_curve.quote_mint==Pubkey::default() @ PumpError::UnsupportedQuoteMint)]pub bonding_curve:Account<'info,BondingCurve>,
 #[account(mut,associated_token::mint=mint,associated_token::authority=bonding_curve,associated_token::token_program=token_program)]pub associated_bonding_curve:InterfaceAccount<'info,TokenAccount>,#[account(mut,token::mint=mint)]pub associated_user:InterfaceAccount<'info,TokenAccount>,#[account(mut)]pub user:Signer<'info>,pub system_program:Program<'info,System>,#[doc="CHECK: PDA checked."]#[account(mut,seeds=[b"creator-vault",bonding_curve.creator.as_ref()],bump)]pub creator_vault:AccountInfo<'info>,pub token_program:Interface<'info,TokenInterface>,
 #[doc="CHECK: event authority."]#[account(seeds=[b"__event_authority"],bump)]pub event_authority:AccountInfo<'info>,#[doc="CHECK: self CPI."]pub program:Program<'info,crate::program::PumpRecovered>,#[doc="CHECK: fee program validates config."]#[account(seeds=[b"fee_config",crate::ID.as_ref()],bump,seeds::program=fee_program.key())]pub fee_config:Account<'info,LegacyFeeConfig>,#[doc="CHECK: canonical dependency."]pub fee_program:Program<'info,LegacyFeesProgram>,
}
pub(crate) fn add(a:u64,b:u64)->Result<u64>{a.checked_add(b).ok_or_else(||error!(PumpError::Overflow))}pub(crate) fn sub(a:u64,b:u64)->Result<u64>{a.checked_sub(b).ok_or_else(||error!(PumpError::Overflow))}pub(crate) fn narrow(a:u128)->Result<u64>{u64::try_from(a).map_err(|_|error!(PumpError::Truncation))}
#[path="fee_cpi.rs"] pub(crate) mod fee_cpi; #[path="util/fee.rs"] pub mod fee_math;
pub fn check_bonding_curve_v2<'info>(remaining_accounts:&[AccountInfo<'info>],mint:&Pubkey)->Result<()>{
    require!(!remaining_accounts.is_empty(),PumpError::InvalidBondingCurveV2);let bonding_curve_v2=&remaining_accounts[0];
    let (expected,_)=Pubkey::find_program_address(&[b"bonding-curve-v2",mint.as_ref()],&crate::ID);
// layout-pad(5): aligns the next Source site with the original line




    require!(bonding_curve_v2.key()==expected,PumpError::InvalidBondingCurveV2);
    Ok(())
}
// layout-pad(8): aligns the next Source site with the original line







pub fn buyback_fee_recipient<'a,'info>(remaining_accounts:&'a [AccountInfo<'info>],global:&Global,index:usize)->Result<&'a AccountInfo<'info>>{
    require!(index<remaining_accounts.len(),PumpError::BuybackFeeRecipientMissing);let account=&remaining_accounts[index];
    let result=global.validate_buyback_fee_recipient(&account.key());result.map(|_|account)

}

// Evaluate the borrowed mint key before coercing the user and system accounts.
#[inline(always)]
pub fn process_cashback<'info>(
    remaining_accounts: &'info [AccountInfo<'info>],
    mint: &Pubkey,
    user: &AccountInfo<'info>,
    system_program: &AccountInfo<'info>,
    bonding_curve: &Account<'info, BondingCurve>,
    amount: u64,
) -> Result<()> {
    process_cashback_inner(remaining_accounts, user, system_program, bonding_curve, amount, mint)
}
