#![feature(core_intrinsics, try_blocks)] use anchor_lang::prelude::*;
pub use pump_fees_math::{FeeTier, Fees};
mod contexts;
mod donation;
pub mod social;
mod withdrawal;
mod buyback;
mod sharing;
pub mod sharing_update; mod common;
mod sharing_admin;
use sharing_update::*;
use sharing_admin::*;
use buyback::*;
use sharing::*;
use withdrawal::*;
use social::*;
use donation::*;
mod pump_global;
mod types;
pub mod instructions;
mod state;
use contexts::*;
use types::*;

declare_id!("pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ");

declare_program!(pump);
declare_program!(pump_amm);
pub mod relay_cpi;







crate::define_fee_errors!();
#[program]
pub mod pump_fees_candidate {
    use super::*;
    #[allow(unused_variables)]
    pub fn initialize_fee_config(ctx: Context<InitializeFeeConfig>) -> Result<()> {
        let bump = ctx.bumps.fee_config;
        core::sync::atomic::compiler_fence(core::sync::atomic::Ordering::SeqCst);
        ctx.accounts.fee_config.bump = bump;
        ctx.accounts.fee_config.admin = ctx.accounts.admin.key();
        let event = InitializeFeeConfigEvent {
            timestamp: Clock::get()?.unix_timestamp,
            admin: ctx.accounts.admin.key(),
            fee_config: ctx.accounts.fee_config.key(),
        };
        emit!(event);
        emit_cpi!(event);
        Ok(())
    }
    #[allow(unused_variables)]
    pub fn initialize_fee_program_global(ctx: Context<InitializeFeeProgramGlobal>, social_claim_authority: Pubkey, disable_flags: u8, claim_rate_limit: u64) -> Result<()> {
        let state = &mut ctx.accounts.fee_program_global;
        state.bump = ctx.bumps.fee_program_global;
        state.authority = ctx.accounts.authority.key();
        state.social_claim_authority = social_claim_authority;
        state.disable_flags = disable_flags;
        state.claim_rate_limit = claim_rate_limit;
        let event = InitializeFeeProgramGlobalEvent {
            timestamp: Clock::get()?.unix_timestamp, authority: ctx.accounts.authority.key(),
            social_claim_authority, disable_flags, claim_rate_limit,
        };
        emit!(event);
        emit_cpi!(event);
        Ok(())
    }
    #[allow(unused_variables)]
    pub fn set_social_claim_authority(ctx: Context<SetSocialClaimAuthority>, social_claim_authority: Pubkey) -> Result<()> {
        ctx.accounts.fee_program_global.social_claim_authority = social_claim_authority;
        let event = SetSocialClaimAuthorityEvent { timestamp: Clock::get()?.unix_timestamp, social_claim_authority };
        emit!(event);
        emit_cpi!(event);
        Ok(())
    }
    #[allow(unused_variables)]
    pub fn set_disable_flags(ctx: Context<SetDisableFlags>, disable_flags: u8) -> Result<()> {
        ctx.accounts.fee_program_global.disable_flags = disable_flags;
        let event = SetDisableFlagsEvent { timestamp: Clock::get()?.unix_timestamp, disable_flags };
        emit!(event);
        emit_cpi!(event);
        Ok(())
    }
    #[allow(unused_variables)]
    pub fn set_claim_rate_limit(ctx: Context<SetClaimRateLimit>, claim_rate_limit: u64) -> Result<()> {
        ctx.accounts.fee_program_global.claim_rate_limit = claim_rate_limit;
        let event = SetClaimRateLimitEvent { timestamp: Clock::get()?.unix_timestamp, claim_rate_limit };
        emit!(event);
        emit_cpi!(event);
        Ok(())
    }
    #[allow(unused_variables)]
    pub fn set_authority(ctx: Context<SetAuthority>, new_authority: Pubkey) -> Result<()> { include!("instructions/admin/update_fee_program_global.rs") 







    }
    #[allow(unused_variables)]
    pub fn update_fee_config(ctx: Context<UpdateFeeConfig>, fee_tiers: Vec<FeeTier>, flat_fees: Fees) -> Result<()> { ctx.accounts.fee_config.set_flat_fees(flat_fees)?; state::replace_normal_tiers(&mut ctx.accounts.fee_config.fee_tiers, &fee_tiers, 0, false)?; let event = UpdateFeeConfigEvent { timestamp: Clock::get()?.unix_timestamp, admin: ctx.accounts.fee_config.admin, fee_config: ctx.accounts.fee_config.key(), fee_tiers, flat_fees }; emit!(event); emit_cpi!(event); Ok(()) }
    #[allow(unused_variables)]
    pub fn upsert_fee_tiers(ctx: Context<UpsertFeeTiers>, fee_tiers: Vec<FeeTier>, offset: u8) -> Result<()> { state::replace_normal_tiers(&mut ctx.accounts.fee_config.fee_tiers, &fee_tiers, offset as usize, true)?; let event = UpsertFeeTiersEvent { timestamp: Clock::get()?.unix_timestamp, admin: ctx.accounts.fee_config.admin, fee_config: ctx.accounts.fee_config.key(), fee_tiers, offset }; emit!(event); emit_cpi!(event); Ok(()) }
    #[allow(unused_variables)]
    pub fn update_stable_fee_config(ctx: Context<UpdateStableFeeConfig>, fee_tiers: Vec<FeeTier>) -> Result<()> {
        state::replace_stable_tiers(&mut ctx.accounts.fee_config, &fee_tiers, 0, false)?;

        let event = UpdateStableFeeConfigEvent { timestamp: Clock::get()?.unix_timestamp,
            admin: ctx.accounts.fee_config.admin, fee_config: ctx.accounts.fee_config.key(),
            stable_fee_tiers: fee_tiers, flat_fees: ctx.accounts.fee_config.flat_fees.clone() };
        emit!(event); emit_cpi!(event); Ok(())
    }
    #[allow(unused_variables)]
    pub fn upsert_stable_fee_tiers(ctx: Context<UpsertStableFeeTiers>, fee_tiers: Vec<FeeTier>, offset: u8) -> Result<()> { state::replace_stable_tiers(&mut ctx.accounts.fee_config, &fee_tiers, offset as usize, true)?; let event = UpsertStableFeeTiersEvent { timestamp: Clock::get()?.unix_timestamp, admin: ctx.accounts.fee_config.admin, fee_config: ctx.accounts.fee_config.key(), stable_fee_tiers: fee_tiers, offset }; emit!(event); emit_cpi!(event); Ok(())
    }
    #[allow(unused_variables)]
    pub fn extend_fee_config(ctx: Context<ExtendFeeConfig>) -> Result<()> { instructions::admin::extend_fee_config::execute(ctx) }






















    #[allow(unused_variables)]
    pub fn set_exotic_flat_fees(ctx: Context<SetExoticFlatFees>, exotic_flat_fees: Fees) -> Result<()> {

        resize_fee_config_for_exotic(ctx.accounts.fee_config.as_ref(), ctx.accounts.system_program.as_ref(), ctx.accounts.admin.as_ref())?;











        ctx.accounts.fee_config.set_exotic_flat_fees(exotic_flat_fees)?;
        let event = SetExoticFlatFeesEvent { timestamp: Clock::get()?.unix_timestamp,
            admin: ctx.accounts.admin.key(), fee_config: ctx.accounts.fee_config.key(), exotic_flat_fees };
        emit!(event); emit_cpi!(event); Ok(())
    }
    #[allow(unused_variables)]
    pub fn update_admin(ctx: Context<UpdateAdmin>) -> Result<()> {
        let old_admin = ctx.accounts.fee_config.admin;
        ctx.accounts.fee_config.admin = ctx.accounts.new_admin.key();
        let event = UpdateAdminEvent { timestamp: Clock::get()?.unix_timestamp, old_admin, new_admin: ctx.accounts.fee_config.admin };
        emit!(event); emit_cpi!(event); Ok(())
    }
    #[allow(unused_variables)]
    pub fn get_fees(ctx: Context<GetFees>, is_pump_pool: bool, market_cap_lamports: u128, trade_size_lamports: u64, is_new_quote_mint: OptionBool) -> Result<Fees> { let config = &ctx.accounts.fee_config; let fees = if !is_pump_pool { config.flat_fees.clone() } else if is_new_quote_mint.0 { select_fee_tier(&config.stable_fee_tiers, market_cap_lamports) } else { select_fee_tier(&config.fee_tiers, market_cap_lamports) }; Ok(fees) }
    #[allow(unused_variables)]
    pub fn get_fees_with_quote_mint(ctx: Context<GetFeesWithQuoteMint>, is_pump_pool: bool, market_cap_lamports: u128, quote_mint: Pubkey) -> Result<Fees> { Ok(select_quote_fees(&ctx.accounts.fee_config, is_pump_pool, market_cap_lamports, quote_mint)) }
    #[allow(unused_variables)]
    pub fn create_fee_sharing_config(ctx: Context<CreateFeeSharingConfig>) -> Result<()> {
        instructions::fee_sharing::create_fee_sharing_config::create_sharing(ctx)
    }
    #[allow(unused_variables)]
    pub fn revoke_fee_sharing_authority(_ctx: Context<RevokeFeeSharingAuthority>) -> Result<()> {
        Err(error!(FeeError::DeprecatedInstruction))
    }

    #[allow(unused_variables)]
    pub fn transfer_fee_sharing_authority(_ctx: Context<TransferFeeSharingAuthority>) -> Result<()> {
        Err(error!(FeeError::DeprecatedInstruction))
    }

    #[allow(unused_variables)]
    pub fn update_fee_shares<'info>(ctx: Context<'_, '_, '_, 'info, UpdateFeeShares<'info>>, shareholders: Vec<Shareholder>) -> Result<()> {
        sharing_update::update_fee_shares(ctx, shareholders)
    }

    #[allow(unused_variables)]
    pub fn update_fee_shares_v2<'info>(ctx: Context<'_, '_, '_, 'info, UpdateFeeSharesV2<'info>>, shareholders: Vec<Shareholder>) -> Result<()> {
        sharing_update::update_fee_shares_v2(ctx, shareholders)
    }

    #[allow(unused_variables)]
    pub fn admin_cto_sharing_config(ctx: Context<AdminCtoSharingConfig>, new_admin: Option<Pubkey>) -> Result<()> {
        include!("instructions/fee_sharing/admin_cto_sharing_config.rs")
    }

    #[allow(unused_variables)]
    pub fn create_social_fee_pda(ctx: Context<CreateSocialFeePda>, user_id: String, platform: u8) -> Result<()> {
        social::create_social(ctx, user_id, platform)
    }

    #[allow(unused_variables)]
    pub fn claim_social_fee_pda(ctx: Context<ClaimSocialFeePda>, user_id: String, platform: u8) -> Result<Option<SocialFeePdaClaimed>> {
        social::claim(ctx, user_id, platform)
    }

    #[allow(unused_variables)]
    pub fn claim_social_fee_pda_v2(ctx: Context<ClaimSocialFeePdaV2>, user_id: String, platform: u8) -> Result<Option<SocialFeePdaClaimed>> {
        social::claim_v2(ctx, user_id, platform)
    }

    #[allow(unused_variables)]
    pub fn initialize_buyback(ctx: Context<InitializeBuyback>, index: u8) -> Result<()> {
        buyback::initialize_buyback(ctx,index)
    }

    #[allow(unused_variables)]
    pub fn sweep_buyback(ctx: Context<SweepBuyback>, index: u8) -> Result<()> {
        buyback::sweep_buyback(ctx,index)
    }

    #[allow(unused_variables)]
    pub fn update_buyback_authority(ctx: Context<UpdateBuyback>, index: u8, new_authority: Pubkey) -> Result<()> {
        buyback::update_buyback_authority(ctx,index,new_authority)
    }

    #[allow(unused_variables)]
    pub fn update_buyback_claim_rate_limit(ctx: Context<UpdateBuyback>, index: u8, claim_rate_limit: i64) -> Result<()> {
        buyback::update_buyback_claim_rate_limit(ctx,index,claim_rate_limit)
    }

    #[allow(unused_variables)]
    pub fn create_donation_fee_pda(ctx: Context<CreateDonationFeePda>) -> Result<()> {
        instructions::fee_sharing::create_donation_fee_pda::create(ctx)
    }

    #[allow(unused_variables)]
    pub fn crank_donation_fee_pda(ctx: Context<CrankDonationFeePda>) -> Result<()> {
        if ctx.accounts.fee_program_global.disable_flags & 8 != 0 {msg!("CrankDonationFeePda is currently disabled");return Err(FeeError::FeatureDeactivated.into());} let config=ctx.accounts.donation_fee_pda.config_id; let base=ctx.accounts.donation_fee_pda.base_mint; let creator=ctx.accounts.donation_fee_pda.creator; let amount=if ctx.accounts.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID { let donation=ctx.accounts.donation_fee_pda.to_account_info(); match crate::donation::sync_native_excess(&donation,&mut ctx.accounts.donation_fee_pda_ata,&ctx.accounts.rent)? { Some(amount)=>amount, None=>return Ok(()) } } else { let amount=ctx.accounts.donation_fee_pda_ata.amount; if amount==0{msg!("Nothing to donate");return Ok(());} amount }; let relay_args=crate::relay_cpi::DonatePubkeyConfigIdWithPayerV1Args {amount,config_id:config,tip_bps:0,message:format!("{},{}",base,creator),credited_to:ID}; let seeds:&[&[u8]]=&[b"donation-fee-pda",base.as_ref(),config.as_ref(),&[ctx.accounts.donation_fee_pda.bump]]; (crate::relay_cpi::DonatePubkeyConfigIdWithPayerV1 { program:ctx.accounts.donation_relay_program.to_account_info(),epoch_tracker:ctx.accounts.epoch_tracker.to_account_info(),debouncer:ctx.accounts.debouncer.to_account_info(),debouncer_token_account:ctx.accounts.debouncer_ata.to_account_info(),mint:ctx.accounts.quote_mint.to_account_info(),from_token_account:ctx.accounts.donation_fee_pda_ata.to_account_info(),from:ctx.accounts.donation_fee_pda.to_account_info(),payer:ctx.accounts.payer.to_account_info(),mint_whitelist:ctx.accounts.mint_whitelist.to_account_info(),associated_token_program:ctx.accounts.associated_token_program.to_account_info(),token_program:ctx.accounts.token_program.to_account_info(),system_program:ctx.accounts.system_program.to_account_info(),event_authority:ctx.accounts.donation_relay_event_authority.to_account_info() }).invoke_signed(relay_args,seeds)?; let state=&mut ctx.accounts.donation_fee_pda; state.total_donated=state.total_donated.checked_add(amount).ok_or(FeeError::ShareCalculationOverflow)?; state.last_crank_ts=Clock::get()?.unix_timestamp; let event=DonationFeePdaCranked {timestamp:state.last_crank_ts,signer:ctx.accounts.payer.key(),donation_fee_pda:state.key(),config_id:config,base_mint:base,quote_mint:ctx.accounts.quote_mint.key(),creator,amount}; emit!(event);emit_cpi!(event);Ok(())
    }

    #[allow(unused_variables)]
    pub fn withdraw(ctx: Context<Withdraw>) -> Result<()> {
        instructions::withdraw::execute(ctx)
    }

}

#[error_code]
pub enum CandidateError {
    #[msg("Research candidate handler not reconstructed")]
    Unsupported,
}

use fee_math::select_fee_tier;






pub const WRAPPED_SOL: [u8; 32] = [6,155,136,87,254,171,129,132,251,104,127,99,70,24,192,53,218,196,57,220,26,235,59,85,152,160,240,0,0,0,0,1];
pub const OTHER_NORMAL_QUOTE: [u8; 32] = [131,13,252,159,222,95,230,184,170,124,4,164,118,233,30,138,198,187,38,74,173,144,250,25,201,223,73,216,92,62,91,94];
pub const USDC: [u8; 32] = [198,250,122,243,190,219,173,58,61,101,243,106,171,201,116,49,177,187,228,194,210,246,224,228,124,166,2,3,69,47,93,97];

#[macro_export] macro_rules! define_fee_errors { () => { #[error_code]
pub enum FeeError {
    #[msg("Only Pump and PumpSwap programs can call this instruction")]
    UnauthorizedProgram = 0,
    #[msg("Invalid admin")]
    InvalidAdmin = 1,
    #[msg("No fee tiers provided")]
    NoFeeTiers = 2,
    #[msg("format")]
    TooManyFeeTiers = 3,
    #[msg("The offset should be <= fee_config.fee_tiers.len()")]
    OffsetNotContinuous = 4,
    #[msg("Fee tiers must be sorted by market cap threshold (ascending)")]
    FeeTiersNotSorted = 5,
    #[msg("Fee total must not exceed 10_000bps")]
    InvalidFeeTotal = 6,
    #[msg("Invalid Sharing Config")]
    InvalidSharingConfig = 7,
    #[msg("Invalid Pool")]
    InvalidPool = 8,
    #[msg("Sharing config authority has been revoked - sharing config can only be updated once")]
    SharingConfigAdminRevoked = 9,
    #[msg("No shareholders provided")]
    NoShareholders = 10,
    #[msg("format")]
    TooManyShareholders = 11,
    #[msg("Duplicate shareholder address")]
    DuplicateShareholder = 12,
    #[msg("Not enough remaining accounts")]
    NotEnoughRemainingAccounts = 13,
    #[msg("Invalid share total - must equal 10_000 basis points")]
    InvalidShareTotal = 14,
    #[msg("Share calculation overflow")]
    ShareCalculationOverflow = 15,
    #[msg("The given account is not authorized to execute this instruction.")]
    NotAuthorized = 16,
    #[msg("Shareholder cannot have zero share")]
    ZeroShareNotAllowed = 17,
    #[msg("Fee sharing config is not active")]
    SharingConfigNotActive = 18,
    #[msg("AMM accounts are required for graduated coins")]
    AmmAccountsRequiredForGraduatedCoin = 19,
    #[msg("Remaining account key doesn't match shareholder address")]
    ShareholderAccountMismatch = 20,
    #[msg("Feature is currently deactivated")]
    FeatureDeactivated = 21,
    #[msg("User ID exceeds maximum length")]
    UserIdTooLong = 22,
    #[msg("Instruction is deprecated")]
    DeprecatedInstruction = 23,
    #[msg("Reward split can only be updated once")]
    FeeSharesAlreadyUpdated = 24,
    #[msg("Math overflow")]
    MathOverflow = 25,
    #[msg("Invalid buybackindex")]
    InvalidBuybackIndex = 26,
    #[msg("Claim rate limit exceeded")]
    ClaimRateLimitExceeded = 27,
    #[msg("Account is not a valid FeeConfig for this instruction")]
    InvalidFeeConfigAccount = 28,
    #[msg("Account type not supported")]
    AccountTypeNotSupported = 29,
    #[msg("Mint does not match quote mint")]
    InvalidMint = 30,
    #[msg("Unsupported quote mint")]
    UnsupportedQuoteMint = 31,
    #[msg("Invalid remaining accounts")]
    InvalidRemainingAccounts = 32,
    #[msg("Pool creator_fees must be swept before the shares change")]
    PoolCreatorFeesNotSwept = 33,
    #[msg("quote_mint is not the bonding curve's quote mint")]
    InvalidQuoteMint = 34,
    #[msg("Token withdrawals need quote_mint, vault_ata, user_ata and token_program")]
    IncompleteTokenAccounts = 35,
    #[msg("Nothing to withdraw")]
    NothingToWithdraw = 36,
} }; }

use pump_fees_math as fee_math;


fn validate_fees(fees: &Fees) -> Result<()> {
    require!(fees.is_valid(), FeeError::InvalidFeeTotal);
    Ok(())
}
fn validate_tiers(tiers: &[FeeTier]) -> Result<()> {
    require!(!tiers.is_empty(), FeeError::NoFeeTiers);
    require!(tiers.len() <= 50, FeeError::TooManyFeeTiers);
    for tier in tiers { validate_fees(&tier.fees)?; }
    require!(tiers.windows(2).all(|pair| pair[0].market_cap_lamports_threshold < pair[1].market_cap_lamports_threshold), FeeError::FeeTiersNotSorted);
    Ok(())
}

fn upsert_tiers(current: &mut Vec<FeeTier>, incoming: &[FeeTier], offset: u8) -> Result<()> {
    require!(!incoming.is_empty(), FeeError::NoFeeTiers);
    let offset = offset as usize;
    require!(offset <= current.len(), FeeError::OffsetNotContinuous);
    require!(current.len().max(offset + incoming.len()) <= 50, FeeError::TooManyFeeTiers);
    for (index, tier) in incoming.iter().enumerate() {
        if offset + index < current.len() { current[offset + index] = tier.clone(); }
        else { current.push(tier.clone()); }
    }
    validate_tiers(current)
}

#[inline(never)]
fn select_quote_fees(config: &FeeConfig, is_pump_pool: bool, market_cap_lamports: u128, quote_mint: Pubkey) -> Fees {
    if !is_pump_pool { return config.flat_fees.clone(); }
    if quote_mint == Pubkey::default() || quote_mint == Pubkey::new_from_array(WRAPPED_SOL) || quote_mint == Pubkey::new_from_array(OTHER_NORMAL_QUOTE) {
        select_fee_tier(&config.fee_tiers, market_cap_lamports)
    } else if Pubkey::new_from_array(USDC) == quote_mint {
        select_fee_tier(&config.stable_fee_tiers, market_cap_lamports)
    } else if config.exotic_flat_fees.lp_fee_bps == 0 && config.exotic_flat_fees.protocol_fee_bps == 0 && config.exotic_flat_fees.creator_fee_bps == 0 {
        config.flat_fees.clone()
    } else { config.exotic_flat_fees.clone() }
}


fn resize_fee_config_for_exotic<'info>(info: &AccountInfo<'info>, system_program: &AccountInfo<'info>, admin: &AccountInfo<'info>) -> Result<()> {
        let info = info.clone();
        if info.data_len() < 4097 {
            let rent = Rent::get()?.minimum_balance(4097);
            let extra = rent.saturating_sub(info.lamports());
            if extra > 0 {
                anchor_lang::system_program::transfer(CpiContext::new(
                    system_program.to_account_info(), anchor_lang::system_program::Transfer {
                        from: admin.to_account_info(), to: info.clone(),
                    }), extra)?;
            }
            info.realloc(4097, false)?;
        }
        Ok(())
}
