use anchor_lang::prelude::*; use anchor_spl::{associated_token::AssociatedToken,token_interface::{Mint,TokenAccount,TokenInterface}}; use crate::anchor_framework::*;
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
#[event_cpi]
#[derive(Accounts)]
#[instruction(amount: u64, config_id: Pubkey, tip_bps: u16, message: String, credited_to: Pubkey)]
pub struct DonatePubkeyConfigIdWithPayerV1<'info> {
    #[account(seeds = [b"epoch_tracker_v1", config_id.as_ref(), mint.key().as_ref()], bump, init_if_needed, payer = payer, space = 90)]
    pub epoch_tracker: Account<'info,EpochTrackerV1>,
    #[account(seeds = [b"debouncer_v1", config_id.as_ref(), mint.key().as_ref()], bump, init_if_needed, payer = payer, space = 82)]
    pub debouncer: Account<'info,DebouncerV1>,
    #[account(init_if_needed, payer = payer, associated_token::mint = mint, associated_token::authority = debouncer, associated_token::token_program = token_program)]
    pub debouncer_token_account: InterfaceAccount<'info,TokenAccount>,
    #[account(mut, mint::token_program = token_program)]
    pub mint: Box<InterfaceAccount<'info,Mint>>,
    #[account(mut, associated_token::mint = mint, associated_token::authority = from, associated_token::token_program = token_program)]
    pub from_token_account: InterfaceAccount<'info,TokenAccount>,
    #[account(mut)]
    pub from: Signer<'info>,
    #[account(mut)]
    pub payer: Signer<'info>,
    #[account(seeds = [b"mint_whitelist_v1"], bump = mint_whitelist.bump)]
    pub mint_whitelist: Account<'info,MintWhitelistV1>,
    pub associated_token_program: Program<'info,AssociatedToken>,
    pub token_program: Interface<'info,TokenInterface>,
    pub system_program: Program<'info,System>,
}

// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
// Historical source text before this handler is unknown.
impl<'info> DonatePubkeyConfigIdWithPayerV1<'info> {
    pub fn donate_pubkey_config_id_with_payer_v1_handler(
        accounts: &mut Self,
        args: crate::codec::wire::DonatePubkeyConfigIdWithPayerV1,
        epoch_tracker_bump: u8,
        debouncer_bump: u8,
    ) -> Result<DonationMadeV1Event> {
        let crate::codec::wire::DonatePubkeyConfigIdWithPayerV1 {
            amount,
            config_id,
            tip_bps,
            message,
            credited_to,
        } = args;

        let result = crate::shared_donation::donate_shared(
            crate::shared_donation::DonationContext {
                epoch_tracker: &mut accounts.epoch_tracker,
                debouncer: &mut accounts.debouncer,
                debouncer_token_account: accounts.debouncer_token_account.to_account_info(),
                mint: accounts.mint.to_account_info(),
                from_token_account: accounts.from_token_account.to_account_info(),
                from: &accounts.from,
                token_program: accounts.token_program.to_account_info(),
                mint_whitelist: &accounts.mint_whitelist,
            },
            crate::shared_donation::DonationArgs {
                config_id: config_id.to_bytes(),
                amount,
                tip_bps,
                message: message.clone(),
                epoch_tracker_bump,
                debouncer_bump,
            },
        )?;

        Ok(DonationMadeV1Event {
            daas_event_discriminator: DaasEventDiscriminator::DonationV1,
            config_id: config_id.to_bytes(),
            mint: accounts.mint.key(),
            epoch: result.epoch,
            gross_amount: result.gross_amount,
            tip: result.tip,
            message,
            credited_to,
        })
    }
}
