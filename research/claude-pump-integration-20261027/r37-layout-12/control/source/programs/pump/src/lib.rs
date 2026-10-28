#[path="multi_hop_curve_swap.rs"]pub mod multi_hop_curve;
pub use multi_hop_curve::*;
pub mod global_init;
pub use global_init::*;
pub mod incentives;
pub use incentives::*;
pub mod token_incentives;
pub use token_incentives::*;
pub use token_incentives::volume_accumulator::{GlobalVolumeAccumulator, UserVolumeAccumulator};
pub mod mayhem_virtual_params;
pub use mayhem_virtual_params::*;
pub mod buy_v2;
pub use buy_v2::*;
pub mod cashback;
pub use cashback::*;
pub mod migrate_v2;
pub use migrate_v2::*;
#[path="buy.rs"]pub mod legacy_buy;
pub use legacy_buy::*;
use anchor_lang::prelude::*;
#[path="creator/distribute_fee_to_holders.rs"]pub mod holder_distribution;
pub use holder_distribution::*;
pub mod migrate;
pub use migrate::*;
pub mod sell_v2;
pub use sell_v2::*;
#[path="sell.rs"]pub mod legacy_sell;
pub use legacy_sell::*;

pub mod create_v2;
pub use create_v2::*;

pub mod create;
pub use create::*;

#[path="creator/collect_creator_fee.rs"]pub mod collect_v2;
pub use collect_v2::*;
#[path="extend_account.rs"]pub mod extend;
pub use extend::*;
pub mod volume_sync;
pub use volume_sync::*;
#[path="sweep_fees.rs"]pub mod sweep;
pub use sweep::*;
#[path="creator/admin_cto.rs"]pub mod admin_cto;
pub use admin_cto::*;
#[path="creator/migrate_bonding_curve_creator.rs"]pub mod creator_migration;
pub use creator_migration::*;
pub mod set_params;
pub use set_params::*;
pub mod set_creator;
pub use set_creator::*;
#[path="admin_set_idl_authority.rs"]pub mod idl_authority;
pub use idl_authority::*;
pub mod distribution;
pub use distribution::*;
pub mod minimum;
pub use minimum::*;
pub mod trade_types;
#[path = "trade_v3.rs"] pub mod trade;
pub use trade::*;

pub mod quote_control;
pub use quote_control::*;

declare_program!(pump_fees);

declare_id!("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P");

#[program]
pub mod pump_recovered {
    use super::*;
    pub fn initialize(ctx:Context<Initialize>)->Result<()>{global_init::execute(ctx)}
    pub fn update_global_authority(ctx:Context<UpdateGlobalAuthority>)->Result<()>{update_global_authority_handler(ctx)}
    pub fn toggle_create_v2(ctx: Context<AdminGlobal>, enabled: bool) -> Result<()> {
        require_neq!(ctx.accounts.global.create_v2_enabled, enabled, PumpError::NotAuthorized);
        ctx.accounts.global.create_v2_enabled = enabled;
        Ok(())
    }
    pub fn toggle_cashback_enabled(ctx: Context<AdminGlobal>, enabled: bool) -> Result<()> {
        require_neq!(ctx.accounts.global.is_cashback_enabled, enabled, PumpError::NotAuthorized);
        ctx.accounts.global.is_cashback_enabled = enabled;
        Ok(())
    }
    pub fn update_holder_reward_config(ctx:Context<AdminGlobal>,is_holder_reward_enabled:bool,holder_reward_claim_authority:Pubkey)->Result<()>{ctx.accounts.global.is_holder_reward_enabled=is_holder_reward_enabled;ctx.accounts.global.holder_reward_claim_authority=holder_reward_claim_authority;Ok(())}
    pub fn set_max_curve_depth(ctx: Context<AdminGlobal>, max_curve_depth: u8) -> Result<()> {
        ctx.accounts.global.max_curve_depth = max_curve_depth;
        Ok(())
    }
    pub fn toggle_mayhem_mode(ctx: Context<AdminGlobal>, enabled: bool) -> Result<()> {
        require_neq!(ctx.accounts.global.mayhem_mode_enabled, enabled, PumpError::NotAuthorized);
        ctx.accounts.global.mayhem_mode_enabled = enabled;
        Ok(())
    }
    pub fn update_creator_fee_config(ctx:Context<AdminGlobal>,creator_fee_configurable:bool,max_configurable_creator_fee_bps:u64)->Result<()>{
      ctx.accounts.global.creator_fee_configurable=creator_fee_configurable;ctx.accounts.global.max_configurable_creator_fee_bps=max_configurable_creator_fee_bps;
      let event=UpdateCreatorFeeConfigEvent{timestamp:Clock::get()?.unix_timestamp,authority:ctx.accounts.authority.key(),creator_fee_configurable,max_configurable_creator_fee_bps};emit!(event);emit_cpi!(event);Ok(())
    }
    pub fn add_quote_mint(ctx:Context<AdminGlobal>,quote_mint:Pubkey)->Result<()>{ctx.accounts.global.add_quote_mint(quote_mint)}
    pub fn remove_quote_mint(ctx:Context<AdminGlobal>,quote_mint:Pubkey)->Result<()>{ctx.accounts.global.remove_quote_mint(quote_mint)}
    pub fn set_virtual_quote_reserves(ctx:Context<AdminGlobal>,initial_virtual_quote_reserves:u64)->Result<()>{ctx.accounts.global.initial_virtual_quote_reserves=initial_virtual_quote_reserves;Ok(())}
    pub fn set_params(ctx:Context<SetParams>,initial_virtual_token_reserves:u64,initial_virtual_sol_reserves:u64,initial_real_token_reserves:u64,token_total_supply:u64,fee_basis_points:u64,withdraw_authority:Pubkey,enable_migrate:bool,pool_migration_fee:u64,creator_fee_basis_points:u64,set_creator_authority:Pubkey,admin_set_creator_authority:Pubkey)->Result<()>{set_params::execute(ctx,initial_virtual_token_reserves,initial_virtual_sol_reserves,initial_real_token_reserves,token_total_supply,fee_basis_points,withdraw_authority,enable_migrate,pool_migration_fee,creator_fee_basis_points,set_creator_authority,admin_set_creator_authority)}
    pub fn set_mayhem_virtual_params(ctx: Context<SetMayhemVirtualParams>) -> Result<()> { mayhem_virtual_params::execute(ctx) }
    pub fn set_reserved_fee_recipients(ctx:Context<AdminReadonly>,whitelist_pda:Pubkey)->Result<()>{
     require_gte!(ctx.remaining_accounts.len(),8,PumpError::NotEnoughRemainingAccounts);
     for (index,account) in ctx.remaining_accounts.iter().take(8).enumerate(){require_keys_neq!(account.key(),Pubkey::default(),PumpError::AllFeeRecipientsShouldBeNonZero);if account.executable{return Err(error!(anchor_lang::error::ErrorCode::ConstraintExecutable).with_account_name(format!("reserved_fee_recipients[{}]",index)));}if !Rent::get()?.is_exempt(account.lamports(),account.data_len()){return Err(error!(anchor_lang::error::ErrorCode::ConstraintRentExempt).with_account_name(format!("reserved_fee_recipients[{}]",index)));}}
     let first=ctx.remaining_accounts[0].key();let rest=core::array::from_fn(|i|ctx.remaining_accounts[i+1].key());
     ctx.accounts.global.whitelist_pda=whitelist_pda;ctx.accounts.global.reserved_fee_recipient=first;ctx.accounts.global.reserved_fee_recipients=rest;
     let event=ReservedFeeRecipientsEvent{timestamp:Clock::get()?.unix_timestamp,reserved_fee_recipient:first,reserved_fee_recipients:rest};emit!(event.clone());emit_cpi!(event);Ok(())
    }
    pub fn create(ctx:Context<Create>,name:String,symbol:String,uri:String,creator:Pubkey)->Result<()>{create::execute(ctx,name,symbol,uri,creator)}
    pub fn create_v2<'info>(ctx:Context<'_,'_,'_,'info,CreateV2<'info>>,name:String,symbol:String,uri:String,creator:Pubkey,is_mayhem_mode:bool,is_cashback_enabled:OptionBool,creator_fee_bps:CreationOptionU64,is_holder_reward:OptionBool)->Result<()>{create_v2::execute(ctx,name,symbol,uri,creator,is_mayhem_mode,is_cashback_enabled,creator_fee_bps,is_holder_reward)}
    pub fn buy_v2<'info>(ctx:Context<'_,'_,'_,'info,BuyV2<'info>>,amount:u64,max_sol_cost:u64,partial_fill:OptionBool)->Result<()>{buy_v2::execute(ctx,amount,max_sol_cost,partial_fill.0,false)}
    pub fn buy_exact_quote_in_v2<'info>(ctx:Context<'_,'_,'_,'info,BuyV2<'info>>,spendable_quote_in:u64,min_tokens_out:u64,partial_fill:OptionBool)->Result<()>{buy_v2::execute(ctx,spendable_quote_in,min_tokens_out,partial_fill.0,true)}
    pub fn sell_v2(ctx:Context<SellV2>,amount:u64,min_sol_output:u64)->Result<()>{sell_v2::execute(ctx,amount,min_sol_output)}
    pub fn buy_v3(ctx: Context<SellV3>, amount:u64,max_sol_cost:u64,partial_fill:OptionBool)->Result<()>{trade::buy(ctx,amount,max_sol_cost,partial_fill.0)}
    pub fn buy_exact_quote_in_v3(ctx:Context<SellV3>,spendable_quote_in:u64,min_tokens_out:u64,partial_fill:OptionBool)->Result<()>{trade::buy_exact_quote(ctx,spendable_quote_in,min_tokens_out,partial_fill.0)}
    pub fn sell_v3(ctx: Context<SellV3>, amount: u64, min_sol_output: u64) -> Result<()> { trade::sell(ctx, amount, min_sol_output) }
    pub fn multi_hop_curve_swap<'info>(ctx:Context<'_,'_,'info,'info,MultiHopCurve<'info>>,amount_in:u64,hop_fees:Vec<u8>)->Result<CurveRunResult>{multi_hop_curve::execute(ctx,amount_in,hop_fees)}
    pub fn sweep_protocol_fee(ctx:Context<SweepFees>)->Result<()>{sweep::execute(ctx,false)}
    pub fn sweep_creator_fee(ctx:Context<SweepFees>)->Result<()>{sweep::execute(ctx,true)}
    pub fn buy<'info>(ctx:Context<'_,'_,'_,'info,LegacyBuy<'info>>,amount:u64,max_sol_cost:u64,track_volume:OptionBool,partial_fill:OptionBool)->Result<()>{legacy_buy::execute(ctx,amount,max_sol_cost,track_volume.0,partial_fill.0,false)}
    pub fn buy_exact_sol_in<'info>(ctx:Context<'_,'_,'_,'info,LegacyBuy<'info>>,spendable_sol_in:u64,min_tokens_out:u64,track_volume:OptionBool,partial_fill:OptionBool)->Result<()>{legacy_buy::execute(ctx,spendable_sol_in,min_tokens_out,track_volume.0,partial_fill.0,true)}
    pub fn sell(ctx:Context<LegacySell>,amount:u64,min_sol_output:u64)->Result<()>{legacy_sell::execute(ctx,amount,min_sol_output)}
    pub fn migrate<'info>(ctx:Context<'_,'_,'_,'info,Migrate<'info>>)->Result<()>{migrate::execute(ctx)}
    pub fn migrate_v2<'info>(ctx:Context<'_, '_, '_, 'info,MigrateV2<'info>>)->Result<()>{migrate_v2::execute(ctx)}
    pub fn extend_account(ctx:Context<ExtendAccount>)->Result<()>{extend::execute(ctx)}
    pub fn collect_creator_fee(ctx:Context<CollectCreatorFee>)->Result<()>{
      require!(*ctx.accounts.creator.owner!=crate::distribution::FEES,PumpError::UnableToDistributeCreatorVaultMigratedToSharingConfig);
      if ctx.accounts.creator.executable{msg!("Creator account is executable, so it cannot receive lamports");return Ok(());}
      let rent=Rent::get()?;
      let amount=ctx.accounts.creator_vault.lamports().saturating_sub(rent.minimum_balance(0));
      if amount==0{msg!("No creator fee to collect");return Ok(());}
      if ctx.accounts.creator.lamports().saturating_add(amount)<rent.minimum_balance(ctx.accounts.creator.data_len()){msg!("Creator account does not have enough rent-exemption lamports");return Ok(());}
      let creator=ctx.accounts.creator.key();let bump=[ctx.bumps.creator_vault];let seeds:&[&[u8]]=&[b"creator-vault",creator.as_ref(),&bump];
      anchor_lang::system_program::transfer(CpiContext::new_with_signer(ctx.accounts.system_program.to_account_info(),anchor_lang::system_program::Transfer{from:ctx.accounts.creator_vault.to_account_info(),to:ctx.accounts.creator.to_account_info()},&[seeds]),amount)?;
      let event=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,creator,creator_fee:amount,quote_mint:Pubkey::default()};emit!(event.clone());emit_cpi!(event);Ok(())
    }
    pub fn collect_creator_fee_v2(ctx:Context<CollectCreatorFeeV2>)->Result<()>{collect_v2::execute(ctx)}
    pub fn distribute_fee_to_holders<'info>(ctx:Context<'_, '_, '_, 'info,DistributeFeeToHolders<'info>>,amounts:Vec<u64>)->Result<()>{holder_distribution::execute(ctx,amounts)}
    pub fn set_metaplex_creator(ctx:Context<SetMetaplexCreator>)->Result<()>{set_creator::sync(ctx)}
    pub fn set_creator(ctx:Context<SetCreator>,creator:Pubkey)->Result<()>{set_creator::set(ctx,creator)}
    pub fn admin_cto(ctx:Context<AdminCto>,is_holder_reward:Option<bool>,creator_fee_bps:Option<u64>,new_creator:Option<Pubkey>)->Result<()>{admin_cto::execute(ctx,is_holder_reward,creator_fee_bps,new_creator)}
    pub fn admin_update_token_incentives(ctx: Context<AdminUpdateTokenIncentives>, start_time: i64, end_time: i64, seconds_in_a_day: i64, day_number: u64, pump_token_supply_per_day: u64) -> Result<()> { incentives::execute(ctx, start_time, end_time, seconds_in_a_day, day_number, pump_token_supply_per_day) }
    pub fn claim_token_incentives(ctx: Context<ClaimTokenIncentives>) -> Result<()> { token_incentives::claim(ctx) }
    pub fn claim_cashback(ctx:Context<ClaimCashback>)->Result<()>{cashback::claim(ctx)}
    pub fn claim_cashback_v2(ctx:Context<ClaimCashbackV2>)->Result<()>{cashback::claim_v2(ctx)}
    pub fn init_user_volume_accumulator(ctx:Context<InitUserVolume>)->Result<()>{
      let event=InitUserVolumeAccumulatorEvent{payer:ctx.accounts.payer.key(),user:ctx.accounts.user.key(),timestamp:Clock::get()?.unix_timestamp};ctx.accounts.user_volume_accumulator.user=ctx.accounts.user.key();emit!(event.clone());emit_cpi!(event);Ok(())
    }
    pub fn close_user_volume_accumulator(ctx:Context<CloseUserVolume>)->Result<()>{
      let a=&ctx.accounts.user_volume_accumulator;let event=CloseUserVolumeAccumulatorEvent{total_unclaimed_tokens:a.total_unclaimed_tokens,total_claimed_tokens:a.total_claimed_tokens,current_sol_volume:a.current_sol_volume,last_update_timestamp:a.last_update_timestamp,user:ctx.accounts.user.key(),timestamp:Clock::get()?.unix_timestamp};emit!(event.clone());emit_cpi!(event);Ok(())
    }
    pub fn sync_user_volume_accumulator(ctx:Context<SyncUserVolumeAccumulator>)->Result<()>{volume_sync::execute(ctx)}
    pub fn admin_set_idl_authority(ctx:Context<AdminSetIdlAuthority>,idl_authority:Pubkey)->Result<()>{idl_authority::execute(ctx,idl_authority)}
    pub fn migrate_bonding_curve_creator(ctx:Context<MigrateBondingCurveCreator>)->Result<()>{creator_migration::execute(ctx)}
    pub fn get_minimum_distributable_fee<'info>(ctx:Context<'_,'_,'_,'info,GetMinimumDistributableFee<'info>>)->Result<MinimumDistributableFeeEvent>{minimum::execute(ctx)}
    pub fn distribute_creator_fees<'info>(ctx:Context<'_,'_,'_,'info,DistributeCreatorFees<'info>>)->Result<DistributeCreatorFeesEvent>{distribution::execute(ctx)}
    pub fn distribute_creator_fees_v2<'info>(ctx:Context<'_,'_,'_,'info,DistributeCreatorFeesV2<'info>>,initialize_ata:bool)->Result<DistributeCreatorFeesEvent>{distribution::execute_v2(ctx,initialize_ata)}
    pub fn update_buyback_config(ctx:Context<AdminGlobal>,buyback_basis_points:Option<u64>)->Result<()>{
     let global=&mut ctx.accounts.global;
     if let Some(value)=buyback_basis_points{global.set_buyback_basis_points(value)?;}
     if ctx.remaining_accounts.is_empty(){return Ok(());}
     require!(ctx.remaining_accounts.len()==8,PumpError::WrongBuybackFeeRecipientsCount);
     let recipients=core::array::from_fn(|index|ctx.remaining_accounts[index].key());
     global.set_buyback_fee_recipients(recipients)
    }
    pub fn initialize_quote_control(ctx: Context<InitializeQuoteControl>) -> Result<()> { quote_control::initialize_quote_control(ctx) }
    pub fn set_quote_control_admin(ctx: Context<SetQuoteControlAdmin>, new_admin: Pubkey) -> Result<()> { quote_control::set_quote_control_admin(ctx, new_admin) }
    pub fn add_quote_control_mint(ctx: Context<UpdateQuoteControlMints>, quote_mint: Pubkey, initial_virtual_quote_reserves: u64) -> Result<()> { quote_control::add_quote_control_mint(ctx, quote_mint, initial_virtual_quote_reserves) }
    pub fn remove_quote_control_mint(ctx: Context<UpdateQuoteControlMints>, quote_mint: Pubkey) -> Result<()> { quote_control::remove_quote_control_mint(ctx, quote_mint) }
    pub fn set_quote_control_reserves_admin(ctx: Context<SetQuoteControlReservesAdmin>, new_reserves_admin: Pubkey) -> Result<()> { quote_control::set_quote_control_reserves_admin(ctx, new_reserves_admin) }
    pub fn set_quote_control_mint_reserves(ctx: Context<SetQuoteControlMintReserves>, quote_mint: Pubkey, initial_virtual_quote_reserves: u64) -> Result<()> { quote_control::set_quote_control_mint_reserves(ctx, quote_mint, initial_virtual_quote_reserves) }
}

#[event_cpi]
#[derive(Accounts)]
pub struct AdminGlobal<'info> {
    #[account(mut, seeds = [b"global"], bump, has_one = authority @ PumpError::NotAuthorized)]
    pub global: Account<'info, Global>,
    #[account(mut)]
    pub authority: Signer<'info>,
}

#[account]
pub struct Global {
    pub initialized: bool,
    pub authority: Pubkey,
    pub fee_recipient: Pubkey,
    pub initial_virtual_token_reserves: u64,
    pub initial_virtual_sol_reserves: u64,
    pub initial_real_token_reserves: u64,
    pub token_total_supply: u64,
    pub fee_basis_points: u64,
    pub withdraw_authority: Pubkey,
    pub enable_migrate: bool,
    pub pool_migration_fee: u64,
    pub creator_fee_basis_points: u64,
    pub fee_recipients: [Pubkey; 7],
    pub set_creator_authority: Pubkey,
    pub admin_set_creator_authority: Pubkey,
    pub create_v2_enabled: bool,
    pub whitelist_pda: Pubkey,
    pub reserved_fee_recipient: Pubkey,
    pub mayhem_mode_enabled: bool,
    pub reserved_fee_recipients: [Pubkey; 7],
    pub is_cashback_enabled: bool,
    pub buyback_fee_recipients: [Pubkey; 8],
    pub buyback_basis_points: u64,
    pub initial_virtual_quote_reserves: u64,
    pub whitelisted_quote_mints: [Pubkey; 1],
    pub creator_fee_configurable: bool,
    pub max_configurable_creator_fee_bps: u64,
    pub holder_reward_claim_authority: Pubkey,
    pub is_holder_reward_enabled: bool,
    pub max_curve_depth: u8,
}

#[error_code]
pub enum PumpError {
    #[msg("The given account is not authorized to execute this instruction.")]
    NotAuthorized,
    #[msg("The program is already initialized.")]
    AlreadyInitialized,
    #[msg("slippage: Too much SOL required to buy the given amount of tokens.")]
    TooMuchSolRequired,
    #[msg("slippage: Too little SOL received to sell the given amount of tokens.")]
    TooLittleSolReceived,
    #[msg("The mint does not match the bonding curve.")]
    MintDoesNotMatchBondingCurve,
    #[msg("The bonding curve has completed and liquidity migrated to raydium.")]
    BondingCurveComplete,
    #[msg("The bonding curve has not completed.")]
    BondingCurveNotComplete,
    #[msg("The program is not initialized.")]
    NotInitialized,
    #[msg("Withdraw too frequent")]
    WithdrawTooFrequent,
    #[msg("new_size should be > current_size")]
    NewSizeShouldBeGreaterThanCurrentSize,
    #[msg("Account type not supported")]
    AccountTypeNotSupported,
    #[msg("initial_real_token_reserves should be less than token_total_supply")]
    InitialRealTokenReservesShouldBeLessThanTokenTotalSupply,
    #[msg("initial_virtual_token_reserves should be greater than initial_real_token_reserves")]
    InitialVirtualTokenReservesShouldBeGreaterThanInitialRealTokenReserves,
    #[msg("fee_basis_points greater than maximum")]
    FeeBasisPointsGreaterThanMaximum,
    #[msg("Withdraw authority cannot be set to System Program ID")]
    AllZerosWithdrawAuthority,
    #[msg("pool_migration_fee should be less than final_real_sol_reserves")]
    PoolMigrationFeeShouldBeLessThanFinalRealSolReserves,
    #[msg("pool_migration_fee should be greater than creator_fee + MAX_MIGRATE_FEES")]
    PoolMigrationFeeShouldBeGreaterThanCreatorFeePlusMaxMigrateFees,
    #[msg("Migrate instruction is disabled")]
    DisabledWithdraw,
    #[msg("Migrate instruction is disabled")]
    DisabledMigrate,
    #[msg("Invalid creator pubkey")]
    InvalidCreator,
    #[msg("Buy zero amount")]
    BuyZeroAmount,
    #[msg("Not enough tokens to buy")]
    NotEnoughTokensToBuy,
    #[msg("Sell zero amount")]
    SellZeroAmount,
    #[msg("Not enough tokens to sell")]
    NotEnoughTokensToSell,
    #[msg("Overflow")]
    Overflow,
    #[msg("Truncation")]
    Truncation,
    #[msg("Division by zero")]
    DivisionByZero,
    #[msg("Not enough remaining accounts")]
    NotEnoughRemainingAccounts,
    #[msg("All fee recipients should be non-zero")]
    AllFeeRecipientsShouldBeNonZero,
    #[msg("Unsorted or not unique fee recipients")]
    UnsortedNotUniqueFeeRecipients,
    #[msg("Creator should not be zero")]
    CreatorShouldNotBeZero,
    StartTimeInThePast,
    EndTimeInThePast,
    EndTimeBeforeStartTime,
    TimeRangeTooLarge,
    EndTimeBeforeCurrentDay,
    SupplyUpdateForFinishedRange,
    DayIndexAfterEndIndex,
    DayInActiveRange,
    InvalidIncentiveMint,
    #[msg("Buy: Not enough SOL to cover for rent exemption.")]
    BuyNotEnoughSolToCoverRent,
    #[msg("Buy: Not enough SOL to cover for fees.")]
    BuyNotEnoughSolToCoverFees,
    #[msg("Slippage: Would buy less tokens than expected min_tokens_out")]
    BuySlippageBelowMinTokensOut,
    NameTooLong,
    SymbolTooLong,
    UriTooLong,
    CreateV2Disabled,
    CpitializeMayhemFailed,
    MayhemModeDisabled,
    #[msg("creator has been migrated to sharing config")]
    CreatorMigratedToSharingConfig,
    #[msg("creator_vault has been migrated to sharing config, use pump:distribute_creator_fees instead")]
    UnableToDistributeCreatorVaultMigratedToSharingConfig,
    #[msg("Sharing config is not active")]
    SharingConfigNotActive,
    #[msg("The recipient account is executable, so it cannot receive lamports, remove it from the team first")]
    UnableToDistributeCreatorFeesToExecutableRecipient,
    #[msg("Bonding curve creator does not match sharing config")]
    BondingCurveAndSharingConfigCreatorMismatch,
    #[msg("Remaining accounts do not match shareholders, make sure to pass exactly the same pubkeys in the same order")]
    ShareholdersAndRemainingAccountsMismatch,
    #[msg("Share bps must be greater than 0")]
    InvalidShareBps,
    #[msg("Cashback is not enabled")]
    CashbackNotEnabled,
    #[msg("Buyback fee recipient not authorized")]
    BuybackFeeRecipientNotAuthorized,
    AllBuybackFeeRecipientsShouldBeNonZero,
    NotUniqueBuybackFeeRecipients,
    #[msg("buyback_basis_points must be <= 10_000")]
    BuybackBasisPointsOutOfRange,
    #[msg("buyback fee recipients require exactly 8 remaining accounts (or none)")]
    WrongBuybackFeeRecipientsCount,
    BuybackFeeRecipientMissing,
    #[msg("Unsupported quote mint")]
    UnsupportedQuoteMint,
    #[msg("Create v2: quote token program must be SPL Token or Token-2022")]
    InvalidQuoteTokenProgram,
    #[msg("Create v2: associated quote bonding curve address does not match derivation")]
    InvalidAssociatedQuoteBondingCurve,
    #[msg("Quote mint whitelist is full")]
    QuoteMintWhitelistFull,
    #[msg("Quote mint is already whitelisted")]
    QuoteMintAlreadyWhitelisted,
    #[msg("Quote mint is not in the whitelist")]
    QuoteMintNotWhitelisted,
    #[msg("Quote mint cannot be added or removed via whitelist (default or native SOL mint)")]
    QuoteMintNotEligibleForWhitelist,
    #[msg("Unable to distribute creator fees to uninitialized account")]
    UnableToDistributeCreatorFeesToUninitializedAccount,
    #[msg("Mayhem mode quote mint not allowed")]
    MayhemModeQuoteMintNotAllowed,
    #[msg("Cashback trade is missing the required remaining accounts")]
    MissingCashbackAccounts,
    #[msg("Cashback user_volume_accumulator account is invalid")]
    InvalidCashbackAccumulator,
    #[msg("bonding_curve_v2 remaining account is missing or invalid")]
    InvalidBondingCurveV2,
    #[msg("quote_control remaining account does not match derivation or is uninitialized")]
    InvalidQuoteControl,
    #[msg("Cashback recipient token account is not owned by user")]
    InvalidCashbackRecipient,
    #[msg("Configurable creator fees are disabled")]
    CreatorFeeNotConfigurable,
    #[msg("Creator fee basis points must be between 1 and the configured maximum")]
    CreatorFeeBpsOutOfRange,
    #[msg("Creator fee is not editable for this bonding curve")]
    CreatorFeeNotEditable,
    #[msg("Creator fee cannot be configured for a cashback coin")]
    CreatorFeeNotAllowedForCashbackCoin,
    #[msg("Bonding curve has already migrated")]
    BondingCurveAlreadyMigrated,
    #[msg("Cashback coins can no longer be created")]
    CashbackDeprecated,
    #[msg("The creator of a holder-reward coin cannot be changed")]
    HolderRewardCreatorImmutable,
    #[msg("Holder-reward coins are disabled")]
    HolderRewardDisabled,
    #[msg("Holder-reward amounts and recipient accounts do not match")]
    HolderRewardRecipientsMismatch,
    #[msg("The holder-rewards PDA cannot be left below its rent-exempt minimum")]
    HolderRewardsRentFloor,
    #[msg("A holder-rewards token account is required on a token quote")]
    HolderRewardTokenAccountMissing,
    #[msg("CTO is not allowed on a mayhem-mode coin")]
    CtoNotAllowedForMayhemCoin,
    #[msg("new_creator is required unless converting to holder rewards")]
    CtoNewCreatorRequired,
    #[msg("new_creator must be omitted when converting to holder rewards")]
    CtoNewCreatorNotAllowed,
    #[msg("Creator fee is not configurable on a SOL or whitelisted quote; the fee schedule applies")]
    CreatorFeeNotConfigurableForQuote,
    #[msg("current_creator must be passed writable so the outgoing creator can be paid")]
    CtoCreatorAccountNotWritable,
    #[msg("A frozen sharing-config vault account holds a balance; thaw it before the holder conversion")]
    CtoSharedVaultFrozen,
    #[msg("v3 trades do not support cashback coins; use the v2 instructions")]
    CashbackCoinNotSupported,
    #[msg("creator_fee must be swept before the creator changes or the vault is distributed")]
    CreatorFeesNotSwept,
    #[msg("The fee config tier table is empty")]
    FeeTiersEmpty,
    #[msg("The fee config account is shorter than its initialize size")]
    FeeConfigTooShort,
    #[msg("multi-hop: a hop's input mint is neither side of its bonding curve")]
    MultiHopDiscontinuousPath,
    #[msg("Quote bonding curve remaining account does not match derivation or is uninitialized")]
    InvalidQuoteBondingCurve,
    #[msg("Quote bonding curve is not eligible as a quote: mayhem mode, or the chain's depth-0 root is quoted in a mint no list admits")]
    QuoteBondingCurveNotEligible,
    #[msg("A quote-chain bonding curve has migrated: its pool and vault remaining accounts are required")]
    QuotePoolAccountsRequired,
    #[msg("Quote pool remaining account is not an initialized pump-amm pool")]
    QuotePoolNotFound,
    #[msg("Quote pool or vault remaining accounts do not match derivation or are invalid")]
    InvalidQuotePool,
    #[msg("Derived quote reserves are zero")]
    QuoteReservesOutOfRange,
    #[msg("The new curve's depth (quote coin depth plus one) exceeds Global.max_curve_depth or the program's cap of 5")]
    CurveDepthExceeded,
    #[msg("multi-hop: hop_fees must carry one flag byte per curve hop using only the protocol and creator bits")]
    MultiHopHopFeesMismatch,
    #[msg("A quote-chain coin's curve is complete but not yet migrated; retry once migrate_v2 creates its pool")]
    QuoteCurveAwaitingMigration,
    #[msg("multi-hop: mayhem-mode curves are not routable; use the v2 instructions")]
    MultiHopMayhemCurveNotSupported,
    #[msg("The quote coin is nested: a bonding curve remaining account is required for every coin on its quote chain down to the depth-0 root")]
    QuoteChainAccountsRequired,
    // Binary evidence extends the captured official IDL, which stops at 6109.
    #[msg("quote_mint must be writable for a quote with a Token-2022 transfer fee: its withheld fees are harvested to the mint")]
    QuoteMintNotWritable = 110,
}

#[derive(AnchorSerialize,Clone)]
pub struct OptionBool(pub bool);
impl AnchorDeserialize for OptionBool {
 fn deserialize_reader<R:std::io::Read>(reader:&mut R)->std::io::Result<Self>{
  let mut b=[0u8];match reader.read_exact(&mut b){Err(e) if e.kind()==std::io::ErrorKind::UnexpectedEof=>Ok(Self(false)),Err(e)=>Err(e),Ok(())=>match b[0]{0=>Ok(Self(false)),1=>Ok(Self(true)),value=>Err(std::io::Error::new(std::io::ErrorKind::InvalidData,format!("Invalid bool representation: {}",value)))}}
 }
}

#[event]
#[derive(Clone)]
pub struct UpdateCreatorFeeConfigEvent {pub timestamp:i64,pub authority:Pubkey,pub creator_fee_configurable:bool,pub max_configurable_creator_fee_bps:u64}

#[event_cpi]
#[derive(Accounts)]
pub struct AdminReadonly<'info>{
 #[account(mut,seeds=[b"global"],bump,has_one=authority @ PumpError::NotAuthorized)]
 pub global:Account<'info,Global>,
 pub authority:Signer<'info>,
}
#[event_cpi]
#[derive(Accounts)]
pub struct UpdateGlobalAuthority<'info>{
 #[account(mut,seeds=[b"global"],bump,has_one=authority @ PumpError::NotAuthorized)]
 pub global:Account<'info,Global>,
 pub authority:Signer<'info>,
 /// CHECK: new authority is assigned by the current signer; zero/self are accepted by the original.
 pub new_authority:AccountInfo<'info>,
}
#[event]
#[derive(Clone)]
pub struct UpdateGlobalAuthorityEvent{pub global:Pubkey,pub authority:Pubkey,pub new_authority:Pubkey,pub timestamp:i64}
#[event]
#[derive(Clone)]
pub struct ReservedFeeRecipientsEvent{pub timestamp:i64,pub reserved_fee_recipient:Pubkey,pub reserved_fee_recipients:[Pubkey;7]}

#[event_cpi]
#[derive(Accounts)]
pub struct InitUserVolume<'info>{
 #[account(mut)] pub payer:Signer<'info>,
 /// CHECK: any user may be funded by the payer.
 pub user:AccountInfo<'info>,
 #[account(init_if_needed,payer=payer,space=137,seeds=[b"user_volume_accumulator",user.key().as_ref()],bump)]
 pub user_volume_accumulator:Account<'info,UserVolumeAccumulator>,
 pub system_program:Program<'info,System>,
}
#[event_cpi]
#[derive(Accounts)]
pub struct CloseUserVolume<'info>{
 #[account(mut)] pub user:Signer<'info>,
 #[account(mut,close=user,seeds=[b"user_volume_accumulator",user.key().as_ref()],bump)]
 pub user_volume_accumulator:Account<'info,UserVolumeAccumulator>,
}
#[event]
#[derive(Clone)]
pub struct InitUserVolumeAccumulatorEvent{pub payer:Pubkey,pub user:Pubkey,pub timestamp:i64}
#[event]
#[derive(Clone)]
pub struct CloseUserVolumeAccumulatorEvent{pub user:Pubkey,pub timestamp:i64,pub total_unclaimed_tokens:u64,pub total_claimed_tokens:u64,pub current_sol_volume:u64,pub last_update_timestamp:i64}

#[event_cpi]
#[derive(Accounts)]
pub struct CollectCreatorFee<'info>{
 /// CHECK: payout destination is bound to the vault PDA.
 #[account(mut)]pub creator:AccountInfo<'info>,
 /// CHECK: original defers owner/data restrictions to System transfer.
 #[account(mut,seeds=[b"creator-vault",creator.key().as_ref()],bump)]pub creator_vault:AccountInfo<'info>,
 pub system_program:Program<'info,System>,
}
#[event]
#[derive(Clone)]
pub struct CollectCreatorFeeEvent{pub timestamp:i64,pub creator:Pubkey,pub creator_fee:u64,pub quote_mint:Pubkey}

impl Global {
 #[inline(never)]
 pub fn set_buyback_basis_points(&mut self,value:u64)->Result<()>{
  require!(value<=10000,PumpError::BuybackBasisPointsOutOfRange);
  self.buyback_basis_points=value;
  Ok(())
 }
 #[inline(never)]
 pub fn set_buyback_fee_recipients(&mut self,recipients:[Pubkey;8])->Result<()>{
  require!(recipients.iter().all(|key|*key!=Pubkey::default()),PumpError::AllBuybackFeeRecipientsShouldBeNonZero);
  for left in 0..8 {for right in left+1..8 {require_keys_neq!(recipients[left],recipients[right],PumpError::NotUniqueBuybackFeeRecipients);}}
  self.buyback_fee_recipients=recipients;
  Ok(())
 }
}

impl Global {
    pub fn add_quote_mint(&mut self,quote_mint:Pubkey)->Result<()>{
     require_keys_neq!(quote_mint,Pubkey::default(),PumpError::QuoteMintNotEligibleForWhitelist);
     require_keys_neq!(quote_mint,anchor_spl::token::spl_token::native_mint::ID,PumpError::QuoteMintNotEligibleForWhitelist);
     require_eq!(self.whitelisted_quote_mints.contains(&quote_mint),false,PumpError::QuoteMintAlreadyWhitelisted);
     let slot=self.whitelisted_quote_mints.iter_mut().find(|key|**key==Pubkey::default()).ok_or_else(||error!(PumpError::QuoteMintWhitelistFull))?;*slot=quote_mint;Ok(())
        }
    pub fn remove_quote_mint(&mut self,quote_mint:Pubkey)->Result<()>{
     require_keys_neq!(quote_mint,Pubkey::default(),PumpError::QuoteMintNotEligibleForWhitelist);
     let slot=self.whitelisted_quote_mints.iter_mut().find(|key|**key==quote_mint).ok_or_else(||error!(PumpError::QuoteMintNotWhitelisted))?;*slot=Pubkey::default();Ok(())
        }
}
/// Split protocol fees after the curve payment, preserving the buyback invariants.
#[inline(never)]
pub(crate) fn split_protocol_fee(
    global: &crate::Global,
    protocol_fee: u64,
    is_mayhem_mode: bool,
) -> (u64, u64) {
    if is_mayhem_mode {
        return (0, protocol_fee);
    }
    let buyback_fee = u64::try_from(global.buyback_basis_points as u128 * protocol_fee as u128 / 10000)
        .expect("buyback fee is at most protocol_fee");
    let remaining = protocol_fee.checked_sub(buyback_fee)
        .expect("buyback_fee never exceeds protocol_fee");
    (buyback_fee, remaining)
}

fn update_global_authority_handler(ctx:Context<UpdateGlobalAuthority>)->Result<()>{
    ctx.accounts.global.authority=ctx.accounts.new_authority.key();
    let event=UpdateGlobalAuthorityEvent{global:ctx.accounts.global.key(),authority:ctx.accounts.authority.key(),new_authority:ctx.accounts.new_authority.key(),timestamp:Clock::get()?.unix_timestamp};
    emit!(event.clone());emit_cpi!(event);Ok(())
}

// Shared user-signed quote payment helpers.
pub mod user_quote_payments {
    use anchor_lang::prelude::*;
    use anchor_spl::token_interface::TokenInterface;
    use crate::trade_types::BondingCurve;

    #[inline(never)]
    pub fn transfer_native<'info>(
        system_program: &AccountInfo<'info>,
        payer: &Signer<'info>,
        destination: &Account<'info, BondingCurve>,
        amount: u64,
    ) -> Result<()> {
        if amount == 0 { return Ok(()); }
        anchor_lang::system_program::transfer(
            CpiContext::new(system_program.clone(), anchor_lang::system_program::Transfer {
                from: payer.to_account_info(),
                to: destination.to_account_info(),
            }), amount,
        )
    }

    #[inline(never)]
    pub fn transfer_from_user<'info>(
        native: bool,
        system_program: &AccountInfo<'info>,
        payer: &Signer<'info>,
        destination: &Account<'info, BondingCurve>,
        amount: u64,
        token_program: &Interface<'info, TokenInterface>,
        quote_decimals: u8,
        quote_mint: &AccountInfo<'info>,
        quote_source: Option<&AccountInfo<'info>>,
        quote_destination: Option<&AccountInfo<'info>>,
    ) -> Result<()> {
        if native { return transfer_native(system_program, payer, destination, amount); }
        let from = quote_source.unwrap();
        let to = quote_destination.unwrap();
        let authority = payer.to_account_info();
        crate::sell_v2::quote_token_transfers::transfer_quote_tokens(
            token_program, from, to, authority, quote_decimals, quote_mint, amount, &[],
        )
    }
    #[inline(never)]
    pub fn transfer_native_owned<'info>(
        system_program: &AccountInfo<'info>,
        payer: &Signer<'info>,
        destination: AccountInfo<'info>,
        amount: u64,
    ) -> Result<()> {
        anchor_lang::system_program::transfer(
            CpiContext::new(system_program.clone(), anchor_lang::system_program::Transfer {
                from: payer.to_account_info(),
                to: destination.clone(),
            }), amount,
        )
    }

    #[inline(never)]
    pub fn transfer_from_user_owned<'info>(
        native: bool,
        system_program: &AccountInfo<'info>,
        payer: &Signer<'info>,
        destination: AccountInfo<'info>,
        amount: u64,
        token_program: &Interface<'info, TokenInterface>,
        quote_decimals: u8,
        quote_mint: &AccountInfo<'info>,
        quote_source: Option<&AccountInfo<'info>>,
        quote_destination: Option<&AccountInfo<'info>>,
    ) -> Result<()> {
        if native { return transfer_native_owned(system_program, payer, destination, amount); }
        let from = quote_source.unwrap();
        let to = quote_destination.unwrap();
        let authority = payer.to_account_info();
        crate::sell_v2::quote_token_transfers::transfer_quote_tokens(
            token_program, from, to, authority, quote_decimals, quote_mint, amount, &[],
        )
    }

    #[inline(never)]
    pub fn transfer_native_recipient<'info>(
        system_program: &AccountInfo<'info>,
        payer: &Signer<'info>,
        destination: &&UncheckedAccount<'info>,
        amount: u64,
    ) -> Result<()> {
        if amount == 0 { return Ok(()); }
        anchor_lang::system_program::transfer(
            CpiContext::new(system_program.clone(), anchor_lang::system_program::Transfer {
                from: payer.to_account_info(),
                to: destination.to_account_info(),
            }), amount,
        )
    }

    #[inline(never)]
    pub fn transfer_from_user_recipient<'info>(
        native: bool,
        system_program: &AccountInfo<'info>,
        payer: &Signer<'info>,
        destination: &&UncheckedAccount<'info>,
        amount: u64,
        token_program: &Interface<'info, TokenInterface>,
        quote_decimals: u8,
        quote_mint: &AccountInfo<'info>,
        quote_source: Option<&AccountInfo<'info>>,
        quote_destination: Option<&AccountInfo<'info>>,
    ) -> Result<()> {
        if native { return transfer_native_recipient(system_program, payer, destination, amount); }
        let from = quote_source.unwrap();
        let to = quote_destination.unwrap();
        let authority = payer.to_account_info();
        crate::sell_v2::quote_token_transfers::transfer_quote_tokens(
            token_program, from, to, authority, quote_decimals, quote_mint, amount, &[],
        )
    }

}

use crate::trade_types::Shareholder;

#[event]
#[derive(Clone)]
pub struct CreateEvent {pub name:String,pub symbol:String,pub uri:String,pub mint:Pubkey,pub bonding_curve:Pubkey,pub user:Pubkey,pub creator:Pubkey,pub timestamp:i64,pub virtual_token_reserves:u64,pub virtual_sol_reserves:u64,pub real_token_reserves:u64,pub token_total_supply:u64,pub token_program:Pubkey,pub is_mayhem_mode:bool,pub is_cashback_enabled:bool,pub quote_mint:Pubkey,pub virtual_quote_reserves:u64,pub creator_fee_bps:u64,pub is_holder_reward:bool,pub depth:u8}

#[event]
#[derive(Clone)]
pub struct TradeEvent {
    pub mint: Pubkey,
    pub sol_amount: u64,
    pub token_amount: u64,
    pub is_buy: bool,
    pub user: Pubkey,
    pub timestamp: i64,
    pub virtual_sol_reserves: u64,
    pub virtual_token_reserves: u64,
    pub real_sol_reserves: u64,
    pub real_token_reserves: u64,
    pub fee_recipient: Pubkey,
    pub fee_basis_points: u64,
    pub fee: u64,
    pub creator: Pubkey,
    pub creator_fee_basis_points: u64,
    pub creator_fee: u64,
    pub track_volume: bool,
    pub total_unclaimed_tokens: u64,
    pub total_claimed_tokens: u64,
    pub current_sol_volume: u64,
    pub last_update_timestamp: i64,
    pub ix_name: String,
    pub mayhem_mode: bool,
    pub cashback_fee_basis_points: u64,
    pub cashback: u64,
    pub buyback_fee_basis_points: u64,
    pub buyback_fee: u64,
    pub shareholders: Vec<Shareholder>,
    pub quote_mint: Pubkey,
    pub quote_amount: u64,
    pub virtual_quote_reserves: u64,
    pub real_quote_reserves: u64,
    pub holder_rewards_bps: u64,
    pub holder_rewards: u64,
    pub creator_fee_unclaimed: u64,
    pub unparsed_trailing_field: u64,
}
