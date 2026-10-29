use crate::*;
use anchor_spl::{associated_token::AssociatedToken, token_interface::TokenInterface};
#[derive(Accounts)]
pub struct LegacySell<'info> {
    #[account(mut,has_one=base_mint @ PumpAmmError::InvalidBaseMint,has_one=quote_mint @ PumpAmmError::InvalidQuoteMint,has_one=pool_base_token_account @ PumpAmmError::InvalidPoolBaseTokenAccount,has_one=pool_quote_token_account @ PumpAmmError::InvalidPoolQuoteTokenAccount)]
    pub pool: Box<Account<'info, Pool>>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub global_config: Box<Account<'info, GlobalConfig>>,
    pub base_mint: Box<InterfaceAccount<'info, Mint>>,
    pub quote_mint: Box<InterfaceAccount<'info, Mint>>,
    #[account(mut)]
    pub user_base_token_account: Box<InterfaceAccount<'info, TokenAccount>>,
    #[account(mut)]
    pub user_quote_token_account: Box<InterfaceAccount<'info, TokenAccount>>,
    #[account(mut)]
    pub pool_base_token_account: Box<InterfaceAccount<'info, TokenAccount>>,
    #[account(mut)]
    pub pool_quote_token_account: Box<InterfaceAccount<'info, TokenAccount>>,
    /// CHECK: Authorization checked in handler.
    pub protocol_fee_recipient: AccountInfo<'info>,
    #[account(init_if_needed,payer=user,associated_token::mint=quote_mint,associated_token::authority=protocol_fee_recipient,associated_token::token_program=quote_token_program)]
    pub protocol_fee_recipient_token_account: Box<InterfaceAccount<'info, TokenAccount>>,
    pub base_token_program: Interface<'info, TokenInterface>,
    pub quote_token_program: Interface<'info, TokenInterface>,
    pub system_program: Program<'info, System>,
    pub associated_token_program: Program<'info, AssociatedToken>,
    /// CHECK: Self event signer.
    #[account(seeds=[b"__event_authority"],bump)]
    pub event_authority: AccountInfo<'info>,
    pub program: Program<'info, trade::PumpAmmProgram>,
    #[account(init_if_needed,payer=user,associated_token::mint=quote_mint,associated_token::authority=coin_creator_vault_authority,associated_token::token_program=quote_token_program)]
    pub coin_creator_vault_ata: Box<InterfaceAccount<'info, TokenAccount>>,
    /// CHECK: Original PDA constraint.
    #[account(seeds=[b"creator_vault",pool.coin_creator.as_ref()],bump)]
    pub coin_creator_vault_authority: AccountInfo<'info>,
    #[account(seeds=[b"fee_config",crate::ID.as_ref()],bump,seeds::program=fee_program.key())]
    pub fee_config: Account<'info, trade::TradeFeeConfig>,
    pub fee_program: Program<'info, FeesProgram>,
}
/// Fee program (`pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ`): the
/// `declare_program!(pump_fees)` program type, so `Program<FeesProgram>`
/// checks the account key against the declared program id
/// (same address as `trade::FEE_OWNER`).
/// Reused by the legacy buy accounts.
pub use crate::pump_fees::program::PumpFees as FeesProgram;
pub fn execute<'info>(
    ctx: Context<'_, '_, 'info, 'info, LegacySell<'info>>,
    base_amount_in: u64,
    min_quote_amount_out: u64,
) -> Result<()> {

















































    require!(ctx.accounts.global_config.disable_flags & 16 == 0, PumpAmmError::DisabledSell);
    super::prepare_pool(&ctx.accounts.pool, &ctx.accounts.system_program, &ctx.accounts.user)?;
    super::validate_protocol_fee_recipient(
        &ctx.accounts.global_config,
        &ctx.accounts.protocol_fee_recipient,
        ctx.accounts.pool.is_mayhem_mode as u8,
    )?;


    require_gt!(base_amount_in, 0, PumpAmmError::ZeroBaseAmount);
    let user_base_token_reserves = ctx.accounts.user_base_token_account.amount;
    let user_quote_token_reserves = ctx.accounts.user_quote_token_account.amount;
    let pool_base_token_reserves = ctx.accounts.pool_base_token_account.amount;
    let pool_quote_token_reserves = ctx.accounts.pool_quote_token_account.amount;
    let quote_reserves = ctx
        .accounts
        .pool
        .effective_quote_reserves(pool_quote_token_reserves)?;
    let quote_amount_out = crate::curve::constant_product::quote_for_sell(
        base_amount_in,
        pool_base_token_reserves,
        quote_reserves,
    )?;
    let fees = crate::curve::fees::select_and_apply(
        &ctx.accounts.pool,
        &ctx.accounts.global_config,
        &ctx.accounts.fee_config,
        &ctx.accounts.fee_program,
        &ctx.accounts.program,
        &ctx.accounts.base_mint,
        pool_base_token_reserves,
        quote_reserves,
        quote_amount_out,
    )?;
    let fees = if ctx.accounts.global_config.whitelist_pda == ctx.accounts.user.key() {
        crate::curve::fees::AppliedFees::default()
    } else {
        fees
    };

























    let quote_amount_out_without_lp_fee = quote_amount_out
        .checked_sub(fees.lp_fee)
        .ok_or_else(|| error!(PumpAmmError::Overflow))?;



    require_gte!(
        ctx.accounts.pool.available_quote_reserves(pool_quote_token_reserves)?,
        quote_amount_out_without_lp_fee,
        PumpAmmError::InsufficientRealQuoteReserves
    );

    let quote_amount_out_without_creator_fee = quote_amount_out_without_lp_fee
        .checked_sub(fees.creator_fee)
        .ok_or_else(|| error!(PumpAmmError::Overflow))?;

    let user_quote_amount_out = quote_amount_out_without_creator_fee
        .checked_sub(fees.protocol_fee)
        .ok_or_else(|| error!(PumpAmmError::Overflow))?;
    let quote_fee =
        crate::utils::transfer_fee::from_mint(&ctx.accounts.quote_mint.to_account_info())?;
    let user_quote_amount_out_after_fee =
        crate::utils::transfer_fee::amount_after_fee(&quote_fee, user_quote_amount_out)?;

    require_gte!(
        user_quote_amount_out_after_fee,
        min_quote_amount_out,
        PumpAmmError::ExceededSlippage
    );
    let quote_transfer_fee = user_quote_amount_out
        .checked_sub(user_quote_amount_out_after_fee)
        .ok_or_else(|| error!(PumpAmmError::Overflow))?;
    crate::utils::token::transfer_checked(
        &ctx.accounts.base_token_program,
        &ctx.accounts.base_mint,
        &ctx.accounts.user_base_token_account,
        &ctx.accounts.pool_base_token_account,
        &ctx.accounts.user,
        base_amount_in,
        &[],
    )?;
    crate::utils::token::transfer_from_pool(
        &ctx.accounts.quote_token_program,
        &ctx.accounts.quote_mint,
        &ctx.accounts.pool_quote_token_account,
        &ctx.accounts.user_quote_token_account,
        user_quote_amount_out,
        &ctx.accounts.pool,
    )?;
    let (buyback_fee, protocol_fee) = ctx
        .accounts
        .global_config
        .split_buyback(fees.protocol_fee, ctx.accounts.pool.is_mayhem_mode);
    crate::utils::token::transfer_from_pool(
        &ctx.accounts.quote_token_program,
        &ctx.accounts.quote_mint,
        &ctx.accounts.pool_quote_token_account,
        &ctx.accounts.protocol_fee_recipient_token_account,
        protocol_fee,
        &ctx.accounts.pool,
    )?;
    let is_cashback = fees.creator_fee > 0 && ctx.accounts.pool.is_cashback_coin;
    let mut buyback_index = 0;
    match fees.creator_fee {
        1.. => {
            if is_cashback {
                cashback(
                    ctx.remaining_accounts,
                    &ctx.accounts.user,
                    &ctx.accounts.pool_quote_token_account,
                    &ctx.accounts.quote_mint,
                    &ctx.accounts.quote_token_program,
                    &ctx.accounts.system_program,
                    &ctx.accounts.associated_token_program,
                    fees.creator_fee,
                    &ctx.accounts.pool,
                    &ctx.accounts.base_mint.key(),
                )?;
                buyback_index = 3;
            } else {
                validate_pool_v2(ctx.remaining_accounts, &ctx.accounts.base_mint.key(), 0)?;
                crate::utils::token::transfer_from_pool(
                    &ctx.accounts.quote_token_program,
                    &ctx.accounts.quote_mint,
                    &ctx.accounts.pool_quote_token_account,
                    &ctx.accounts.coin_creator_vault_ata,
                    fees.creator_fee,
                    &ctx.accounts.pool,
                )?;
                buyback_index = 1;
            }
        }
        0 => {}
    }
    let (buyback_authority, buyback_token_account) =
        crate::instructions::swap::buy::get_buyback_accounts(
            ctx.remaining_accounts,
            &ctx.accounts.global_config,
            buyback_index,
            &ctx.accounts.quote_mint.key(),
            &ctx.accounts.quote_token_program.key(),
        )?;
    if buyback_fee > 0 {
        crate::utils::token::create_ata_if_empty(
            &ctx.accounts.quote_token_program,
            &ctx.accounts.quote_mint,
            buyback_authority,
            buyback_token_account,
            &ctx.accounts.user,
            &ctx.accounts.system_program,
            &ctx.accounts.associated_token_program,
        )?;
        crate::utils::token::transfer_from_pool_to_raw(
            &ctx.accounts.quote_token_program,
            &ctx.accounts.quote_mint,
            &ctx.accounts.pool_quote_token_account,
            &ctx.accounts.pool,
            buyback_token_account,
            buyback_fee,
        )?;
    }
    let event = trade::SellEvent {
        timestamp: Clock::get()?.unix_timestamp,
        base_amount_in,
        min_quote_amount_out,
        user_base_token_reserves,
        user_quote_token_reserves,
        pool_base_token_reserves,
        pool_quote_token_reserves,
        quote_amount_out,
        lp_fee_basis_points: fees.lp_fee_bps,
        lp_fee: fees.lp_fee,
        protocol_fee_basis_points: fees.protocol_fee_bps,
        protocol_fee: fees.protocol_fee,
        quote_amount_out_without_lp_fee,
        user_quote_amount_out,
        pool: ctx.accounts.pool.key(),
        user: ctx.accounts.user.key(),
        user_base_token_account: ctx.accounts.user_base_token_account.key(),
        user_quote_token_account: ctx.accounts.user_quote_token_account.key(),
        protocol_fee_recipient: ctx.accounts.protocol_fee_recipient.key(),
        protocol_fee_recipient_token_account: ctx
            .accounts
            .protocol_fee_recipient_token_account
            .key(),
        coin_creator: ctx.accounts.pool.coin_creator,
        coin_creator_fee_basis_points: if is_cashback { 0 } else { fees.creator_fee_bps },
        coin_creator_fee: if is_cashback { 0 } else { fees.creator_fee },
        cashback_fee_basis_points: if is_cashback { fees.creator_fee_bps } else { 0 },
        cashback: if is_cashback { fees.creator_fee } else { 0 },
        holder_rewards_bps: if ctx.accounts.pool.is_holder_reward {
            fees.creator_fee_bps
        } else {
            0
        },
        holder_rewards: if ctx.accounts.pool.is_holder_reward {
            fees.creator_fee
        } else {
            0
        },
        buyback_fee_basis_points: if ctx.accounts.pool.is_mayhem_mode {
            0
        } else {
            ctx.accounts.global_config.buyback_basis_points
        },
        buyback_fee: crate::utils::transfer_fee::amount_after_fee(&quote_fee, buyback_fee)?,
        virtual_quote_reserves: ctx.accounts.pool.virtual_quote_reserves,
        can_boost: ctx.accounts.pool.can_boost(),
        base_supply: if ctx.accounts.pool.is_mayhem_mode {
            1_000_000_000_000_000
        } else {
            ctx.accounts.base_mint.supply
        },
        creator_fee_unclaimed: ctx.accounts.pool.creator_fees,
        quote_transfer_fee,
    };
    emit!(event);
    emit_cpi!(event);
    Ok(())
}


















#[allow(clippy::too_many_arguments)]
fn cashback<'info>(
    remaining_accounts: &'info [AccountInfo<'info>],
    user: &Signer<'info>,
    pool_quote_token_account: &InterfaceAccount<'info, TokenAccount>,
    quote_mint: &InterfaceAccount<'info, Mint>,
    quote_token_program: &Interface<'info, TokenInterface>,
    system_program: &Program<'info, System>,
    associated_token_program: &Program<'info, AssociatedToken>,
    amount: u64,
    pool: &Account<'info, Pool>,
    base_mint: &Pubkey,
) -> Result<()> {
    let ata = remaining_accounts
        .get(0)
        .ok_or_else(|| error!(PumpAmmError::MissingCashbackAccounts))?;


    let user_volume_accumulator = remaining_accounts
        .get(1)
        .ok_or_else(|| error!(PumpAmmError::MissingCashbackAccounts))?;


    let user_key = user.key();
    let (expected_accumulator, bump) = Pubkey::find_program_address(
        &[b"user_volume_accumulator", user_key.as_ref()],
        &crate::ID,
    );
    if user_volume_accumulator.key() != expected_accumulator {
        return err!(PumpAmmError::InvalidCashbackAccumulator);
    }

    require!(user_volume_accumulator.is_writable, PumpAmmError::InvalidCashbackAccumulator);
    if user_volume_accumulator.data_is_empty() {
        let rent = Rent::get()?;
        let rent = rent.minimum_balance(137);
        let bump = [bump];
        let seeds: &[&[u8]] = &[b"user_volume_accumulator", user_key.as_ref(), &bump];
        let signer_seeds = &[seeds];
        let lamports = user_volume_accumulator.lamports();
        if rent > lamports {
            anchor_lang::system_program::transfer(
                CpiContext::new(
                    system_program.to_account_info(),
                    anchor_lang::system_program::Transfer {
                        from: user.to_account_info(),
                        to: user_volume_accumulator.clone(),
                    },
                ),
                rent.saturating_sub(lamports),
            )?;
        }
        anchor_lang::solana_program::program::invoke_signed(
            &anchor_lang::solana_program::system_instruction::allocate(user_volume_accumulator.key, 137),
            &[user_volume_accumulator.clone()],
            signer_seeds,
        )?;
        anchor_lang::solana_program::program::invoke_signed(
            &anchor_lang::solana_program::system_instruction::assign(user_volume_accumulator.key, &crate::ID),
            &[user_volume_accumulator.clone()],
            signer_seeds,
        )?;
        let mut data = user_volume_accumulator.try_borrow_mut_data()?;













        data[..8].copy_from_slice(UserVolumeAccumulator::DISCRIMINATOR);
        data[8..40].copy_from_slice(user_key.as_ref());


    } else {
        require!(*user_volume_accumulator.owner == crate::ID, PumpAmmError::InvalidCashbackAccumulator);
        let data = user_volume_accumulator.try_borrow_data()?;

        if data.len() < 8 || data[..8] != *UserVolumeAccumulator::DISCRIMINATOR {
            return err!(PumpAmmError::InvalidCashbackAccumulator);
        }
    }
    let mut accumulator = Account::<UserVolumeAccumulator>::try_from(user_volume_accumulator)?;
    let expected_ata = anchor_spl::associated_token::get_associated_token_address_with_program_id(
        &accumulator.key(),
        &quote_mint.key(),
        &quote_token_program.key(),
    );







    require!(ata.key() == expected_ata, PumpAmmError::InvalidCashbackAccumulatorAta);


    require!(ata.is_writable, PumpAmmError::InvalidCashbackAccumulatorAta);
    if ata.data_is_empty() {
        anchor_spl::associated_token::create(CpiContext::new(
            associated_token_program.to_account_info(),
            anchor_spl::associated_token::Create {
                payer: user.to_account_info(),
                associated_token: ata.clone(),
                authority: accumulator.to_account_info(),
                mint: quote_mint.to_account_info(),
                system_program: system_program.to_account_info(),
                token_program: quote_token_program.to_account_info(),
            },
        ))
    } else { Ok(()) }?;
    let ata = InterfaceAccount::<TokenAccount>::try_from_unchecked(ata)?;
    crate::utils::token::transfer_from_pool(
        quote_token_program,
        quote_mint,
        pool_quote_token_account,
        &ata,
        amount,
        pool,
    )?;








    accumulator.user = user.key();
    accumulator.cashback_earned = accumulator
        .cashback_earned
        .checked_add(amount)
        .ok_or(error!(PumpAmmError::Overflow))?;
    accumulator.exit(&crate::ID)?;
    validate_pool_v2(remaining_accounts, &base_mint.key(), 2)?;
    Ok(())
}








pub(crate) fn validate_pool_v2(
    remaining_accounts: &[AccountInfo<'_>],
    base_mint: &Pubkey,
    index: usize,
) -> Result<()> {
    require!(index < remaining_accounts.len(), PumpAmmError::InvalidPoolV2);
    let expected = Pubkey::find_program_address(&[b"pool-v2", base_mint.as_ref()], &crate::ID).0;




    require!(remaining_accounts[index].key() == expected, PumpAmmError::InvalidPoolV2);
    Ok(())
}

#[event]
#[derive(Clone)]
pub struct SellEvent {
    pub timestamp: i64,
    pub base_amount_in: u64,
    pub min_quote_amount_out: u64,
    pub user_base_token_reserves: u64,
    pub user_quote_token_reserves: u64,
    pub pool_base_token_reserves: u64,
    pub pool_quote_token_reserves: u64,
    pub quote_amount_out: u64,
    pub lp_fee_basis_points: u64,
    pub lp_fee: u64,
    pub protocol_fee_basis_points: u64,
    pub protocol_fee: u64,
    pub quote_amount_out_without_lp_fee: u64,
    pub user_quote_amount_out: u64,
    pub pool: Pubkey,
    pub user: Pubkey,
    pub user_base_token_account: Pubkey,
    pub user_quote_token_account: Pubkey,
    pub protocol_fee_recipient: Pubkey,
    pub protocol_fee_recipient_token_account: Pubkey,
    pub coin_creator: Pubkey,
    pub coin_creator_fee_basis_points: u64,
    pub coin_creator_fee: u64,
    pub cashback_fee_basis_points: u64,
    pub cashback: u64,
    pub buyback_fee_basis_points: u64,
    pub buyback_fee: u64,
    pub virtual_quote_reserves: i128,
    pub can_boost: bool,
    pub base_supply: u64,
    pub holder_rewards_bps: u64,
    pub holder_rewards: u64,
    pub creator_fee_unclaimed: u64,
    pub quote_transfer_fee: u64,
}
