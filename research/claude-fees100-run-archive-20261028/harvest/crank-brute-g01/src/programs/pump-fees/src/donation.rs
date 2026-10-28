//! Partial donation behavior integrated from the independently validated local draft.
//! Captured relay code executes only as an external dependency in local tests.
use anchor_lang::prelude::*;
use anchor_lang::solana_program::instruction::AccountMeta;
use anchor_spl::token_interface::Mint;
use crate::{FeeError, ID};
use crate::types::FeeProgramGlobal;
pub const RELAY: Pubkey = anchor_lang::solana_program::pubkey!("RLAYHr9TRFcKB2ubYQhspcnXiaGpaVzNQvHytt47RZu");
pub const PUMP: Pubkey = crate::pump_global::PUMP_ID;
pub const AMM: Pubkey = anchor_lang::solana_program::pubkey!("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA");

pub(crate) fn sync_native_excess<'info>(donation: &AccountInfo<'info>, ata: &mut Account<'info, anchor_spl::token::TokenAccount>, rent: &UncheckedAccount<'info>) -> Result<Option<u64>> {
    let rent_sysvar = Rent::get()?;
    let minimum = rent_sysvar.minimum_balance(218);
    let excess = donation.lamports().saturating_sub(minimum);
    if excess > 0 {
        let ata_info = ata.to_account_info();
        donation.sub_lamports(excess)?;
        ata_info.add_lamports(excess)?;
        anchor_lang::solana_program::program::invoke(&anchor_lang::solana_program::instruction::Instruction {
            program_id: anchor_spl::token::ID,
            accounts: vec![AccountMeta::new(ata.key(), false), AccountMeta::new_readonly(rent.key(), false), AccountMeta::new(donation.key(), false)],
            data: anchor_spl::token::spl_token::instruction::TokenInstruction::SyncNative.pack(),
        }, &[ata.to_account_info(), rent.to_account_info(), donation.clone()])?;
        ata.reload()?;
    }
    let amount = ata.amount;
    if amount == 0 {
        msg!("Nothing to donate");
        return Ok(None);
    }
    Ok(Some(amount))
}


















pub fn create(ctx: Context<CreateDonationFeePda>) -> Result<()> {
        if ctx.accounts.fee_program_global.disable_flags & 4 != 0 {
            msg!("CreateDonationFeePda is currently disabled");
            return Err(FeeError::FeatureDeactivated.into());
        }
        if ctx.accounts.donation_fee_pda.version != 0 {
            msg!("donation_fee_pda already exists");
            return Ok(());
        }
        let curve = &ctx.accounts.bonding_curve;
        let (creator, quote_mint) = if curve.real_sol_reserves != 0
            || curve.virtual_sol_reserves != 0
            || curve.real_token_reserves != 0
            || curve.virtual_token_reserves != 0
        {
            let quote = donation_raw_curve_quote(curve.to_account_info());
            let quote = if quote == Pubkey::default() {
                anchor_spl::token::spl_token::native_mint::ID
            } else {
                quote
            };
            (curve.creator, quote)
        } else {
            let info = &ctx.accounts.pool;
            require_keys_eq!(*info.owner, AMM, FeeError::InvalidPool);
            let data=info.try_borrow_data()?;
            let pool=Pool::try_deserialize(&mut &data[..])?;
            require_keys_eq!(pool.base_mint, ctx.accounts.base_mint.key(), FeeError::InvalidPool);
            let authority=Pubkey::find_program_address(&[b"pool-authority",ctx.accounts.base_mint.key().as_ref()],&crate::pump::ID).0;
            require_keys_eq!(pool.creator,authority,FeeError::InvalidPool);
            let expected=Pubkey::create_program_address(&[b"pool",&pool.index.to_le_bytes(),pool.creator.as_ref(),pool.base_mint.as_ref(),pool.quote_mint.as_ref(),&[pool.pool_bump]],&crate::pump_amm::ID).map_err(|_| FeeError::InvalidPool)?;
            require_keys_eq!(info.key(),expected,FeeError::InvalidPool);
            (pool.coin_creator, pool.quote_mint)
        };
        let creator = if creator == ctx.accounts.sharing_config.key() {
            let sharing = &ctx.accounts.sharing_config;
            require_keys_eq!(*sharing.owner,ID,FeeError::InvalidSharingConfig);
            require!(!sharing.data_is_empty(),FeeError::InvalidSharingConfig);
            let bytes=sharing.try_borrow_data()?;
            let config=SharingConfig::try_deserialize(&mut &bytes[..])?;
            require_keys_eq!(config.mint,ctx.accounts.base_mint.key(),FeeError::InvalidSharingConfig);
            require!(config.admin == ctx.accounts.payer.key(), FeeError::NotAuthorized);
            if config.admin_revoked {
                return Err(FeeError::SharingConfigAdminRevoked.into());
            }
            require!(config.status==ConfigStatus::Active,FeeError::SharingConfigNotActive);
            config.admin
        } else {
            require_keys_eq!(ctx.accounts.payer.key(),creator,FeeError::NotAuthorized);
            creator
        };
        let pda=&mut ctx.accounts.donation_fee_pda;
        pda.bump=ctx.bumps.donation_fee_pda;
        pda.version=1;
        pda.config_id=ctx.accounts.config_id.key();
        pda.base_mint=ctx.accounts.base_mint.key();
        pda.quote_mint=quote_mint;
        pda.creator=creator;
        pda.total_donated=0;pda.last_crank_ts=0;pda.reserved=[0;64];
        let event=DonationFeePdaCreated { timestamp:Clock::get()?.unix_timestamp, created_by:ctx.accounts.payer.key(),donation_fee_pda:pda.key(),config_id:pda.config_id,base_mint:pda.base_mint,quote_mint:pda.quote_mint,creator:pda.creator };
        emit!(event);emit_cpi!(event);Ok(())
    }
fn donation_raw_curve_quote(info: AccountInfo<'_>) -> Pubkey {
    let mut quote_bytes = [0u8; 32];
    if info.data_len() >= 115 {
        let data = info.data.borrow();
        quote_bytes.copy_from_slice(&data[83..115]);
    }
    Pubkey::new_from_array(quote_bytes)
}

pub use crate::instructions::fee_sharing::create_donation_fee_pda::*;

















pub use crate::state::DonationFeePda;
pub use crate::pump::accounts::BondingCurve;
pub use crate::pump_amm::accounts::Pool;
#[event]
pub struct DonationFeePdaCreated {pub timestamp:i64,pub created_by:Pubkey,pub donation_fee_pda:Pubkey,pub config_id:Pubkey,pub base_mint:Pubkey,pub quote_mint:Pubkey,pub creator:Pubkey}

#[derive(AnchorSerialize,AnchorDeserialize,Clone,PartialEq)]
pub enum ConfigStatus {Paused,Active}
pub use crate::instructions::fee_sharing::create_fee_sharing_config::SharingConfig;

#[derive(Accounts)]
pub struct CrankDonationFeePda<'info> {
    /// CHECK: event PDA.
    #[account(seeds=[b"__event_authority"],bump)] pub event_authority:AccountInfo<'info>,
    pub program:Program<'info,crate::program::PumpFeesCandidate>,
    #[account(mut)]pub payer:Signer<'info>,
    pub system_program:Program<'info,System>,
    pub token_program:Program<'info,anchor_spl::token::Token>,
    pub associated_token_program:Program<'info,anchor_spl::associated_token::AssociatedToken>,
    /// CHECK: rent address.
    #[account(address=anchor_lang::solana_program::sysvar::rent::ID)]pub rent:UncheckedAccount<'info>,
    #[account(seeds=[b"fee-program-global"],bump=fee_program_global.bump)]pub fee_program_global:Account<'info,FeeProgramGlobal>,
    #[account(mut,seeds=[b"donation-fee-pda",donation_fee_pda.base_mint.as_ref(),donation_fee_pda.config_id.as_ref()],bump=donation_fee_pda.bump)]pub donation_fee_pda:Account<'info,DonationFeePda>,
    #[account(mut,address=donation_fee_pda.quote_mint @ anchor_lang::error::ErrorCode::ConstraintMintTokenProgram)]pub quote_mint:Box<InterfaceAccount<'info,anchor_spl::token_interface::Mint>>,
    #[account(init_if_needed,payer=payer,associated_token::mint=quote_mint,associated_token::authority=donation_fee_pda)]pub donation_fee_pda_ata:Account<'info,anchor_spl::token::TokenAccount>,
    /// CHECK: fixed executable dependency.
    #[account(executable,address=RELAY @ anchor_lang::error::ErrorCode::AccountOwnedByWrongProgram)]pub donation_relay_program:UncheckedAccount<'info>,
    /// CHECK: dependency enforces its constraints.
    pub donation_relay_event_authority:UncheckedAccount<'info>,
    /// CHECK: dependency enforces its constraints.
    pub mint_whitelist:UncheckedAccount<'info>,
    /// CHECK: dependency enforces its constraints.
    #[account(mut)]pub epoch_tracker:UncheckedAccount<'info>,
    /// CHECK: dependency enforces its constraints.
    #[account(mut)]pub debouncer:UncheckedAccount<'info>,
    /// CHECK: dependency enforces its constraints.
    #[account(mut)]pub debouncer_ata:UncheckedAccount<'info>,
}
#[derive(AnchorSerialize,AnchorDeserialize)]
pub struct DonationFeePdaCranked {pub timestamp:i64,pub signer:Pubkey,pub donation_fee_pda:Pubkey,pub config_id:Pubkey,pub base_mint:Pubkey,pub quote_mint:Pubkey,pub creator:Pubkey,pub amount:u64}

impl anchor_lang::Event for DonationFeePdaCranked {  fn data(&self)->Vec<u8>{let mut data=Vec::with_capacity(256);data.extend_from_slice(Self::DISCRIMINATOR);anchor_lang::AnchorSerialize::serialize(self,&mut data).unwrap();data} }














impl anchor_lang::Discriminator for DonationFeePdaCranked {
    const DISCRIMINATOR: &'static [u8] = &[30, 208, 107, 93, 177, 0, 223, 78];
}


#[inline(always)]
pub(crate) fn donation_clone_account<'a>(info: &AccountInfo<'a>) -> AccountInfo<'a> {
 AccountInfo {
  key: info.key, lamports: info.lamports.clone(), data: info.data.clone(), owner: info.owner,
  rent_epoch: info.rent_epoch, is_signer: info.is_signer, is_writable: info.is_writable,
  executable: info.executable,
 }
}
