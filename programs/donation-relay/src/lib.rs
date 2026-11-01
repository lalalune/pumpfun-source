//! Reconstructed Relay Rust; whole captured-byte identity remains unproven.
pub mod codec;
pub mod mint_policy; pub mod cpi { pub mod jupiter; }


#[cfg(not(target_os = "solana"))]
compile_error!("Relay proposal requires a real SBF loader/syscall target; host success stubs are disabled");


pub type Key=[u8;32];






pub mod business_error_codes; pub mod events { pub mod v1 { pub mod donation_epoch_closed; pub mod donation_epoch_just_swapped; pub mod donation_epoch_processed; pub mod donation_made; pub mod bridge_donation_admitted; pub mod bridge_payment_recovered; pub mod donation_epoch_processed_exact; } } pub mod shared_donation; pub mod settlement_handlers; pub mod shared_distribution { pub use crate::tools::distribution::shared::*; pub use crate::tools::fair_distribution::*; } pub mod instructions { pub mod v1 { pub mod public_api { pub mod donate { pub mod donate; pub mod donate_native; pub mod donate_native_pubkey_config_id; pub mod donate_pubkey_config_id; pub mod donate_pubkey_config_id_with_payer; } } pub mod relayer_only { pub mod close_donation_epoch; pub mod distribute { pub mod distribute_after_just_swapping; pub mod distribute_non_swap_output_mint; pub mod just_swap; pub mod swap_then_distribute; } pub mod upsert_mint_whitelist; pub mod admit_bridge_payment; } pub mod recover_bridge_payment; } } pub mod state { pub mod v1 { pub mod bridge_membership; pub mod debouncer; pub mod distribution; pub mod epoch_tracker; pub mod mint_whitelist; pub mod swap_receipt; } } pub mod tools { pub mod checks; pub mod distribution { pub mod shared; } pub mod donate { pub mod shared; } pub mod fair_distribution; }
mod embedded_security;
anchor_lang::declare_id!("RLAYHr9TRFcKB2ubYQhspcnXiaGpaVzNQvHytt47RZu");
pub mod anchor_framework {
    use anchor_lang::prelude::*;
    use crate::ID;
    /*
     * The captured generated IDL error records lib.rs line 36.
     * Its filename is programs/contracts/src/lib.rs (29 bytes).
     * Anchor expands the program macro into those source values.
     * Preserve the observed macro coordinate in this reconstruction.
     * The historical source text preceding it remains unknown.
     * These comments document the coordinate, not historical text.
     * Build this root crate with the documented source-path remap.
     * Dependency source paths retain their own SDK remapping.
     * No captured machine instructions enter the Rust build.
     * Runtime account decorators replace this source origin later.
     * The initial constructor still has to match before replacement.
     */
#[program]
    pub mod relay_anchor_idl_reconstruction_probe {
        use super::*;
        pub fn donate_v1(ctx: Context<DonateV1>, amount:u64, config_id:[u8;32], tip_bps:u16, message:String, credited_to:Pubkey) -> Result<DonationMadeV1Event> {
            let epoch_tracker_bump=ctx.bumps.epoch_tracker;
            let debouncer_bump=ctx.bumps.debouncer;
            let event=DonateV1::donate_v1_handler(ctx.accounts,crate::codec::wire::DonateV1 {amount,config_id,tip_bps,message,credited_to},epoch_tracker_bump,debouncer_bump)?;
            emit!(event);emit_cpi!(event);Ok(event)
        }
        pub fn donate_pubkey_config_id_v1(ctx: Context<DonatePubkeyConfigIdV1>, amount:u64, config_id:Pubkey, tip_bps:u16, message:String, credited_to:Pubkey) -> Result<DonationMadeV1Event> {
            let epoch_tracker_bump=ctx.bumps.epoch_tracker;
            let debouncer_bump=ctx.bumps.debouncer;
            let event=DonatePubkeyConfigIdV1::donate_pubkey_config_id_v1_handler(ctx.accounts,crate::codec::wire::DonatePubkeyConfigIdV1 {amount,config_id,tip_bps,message,credited_to},epoch_tracker_bump,debouncer_bump)?;
            emit!(event);emit_cpi!(event);Ok(event)
        }
        pub fn donate_native_v1(ctx: Context<DonateNativeV1>, amount:u64, config_id:[u8;32], tip_bps:u16, message:String, credited_to:Pubkey) -> Result<DonationMadeV1Event> {
            let epoch_tracker_bump=ctx.bumps.epoch_tracker;
            let debouncer_bump=ctx.bumps.debouncer;
            let event=DonateNativeV1::donate_native_v1_handler(ctx.accounts,crate::codec::wire::DonateNativeV1 {amount,config_id,tip_bps,message,credited_to},epoch_tracker_bump,debouncer_bump)?;
            emit!(event);emit_cpi!(event);Ok(event)
        }
        pub fn donate_native_pubkey_config_id_v1(ctx: Context<DonateNativePubkeyConfigIdV1>, amount:u64, config_id:Pubkey, tip_bps:u16, message:String, credited_to:Pubkey) -> Result<DonationMadeV1Event> {
            let epoch_tracker_bump=ctx.bumps.epoch_tracker;
            let debouncer_bump=ctx.bumps.debouncer;
            let event=DonateNativePubkeyConfigIdV1::donate_native_pubkey_config_id_v1_handler(ctx.accounts,crate::codec::wire::DonateNativePubkeyConfigIdV1 {amount,config_id,tip_bps,message,credited_to},epoch_tracker_bump,debouncer_bump)?;
            emit!(event);emit_cpi!(event);Ok(event)
        }
        pub fn donate_pubkey_config_id_with_payer_v1(ctx: Context<DonatePubkeyConfigIdWithPayerV1>, amount:u64, config_id:Pubkey, tip_bps:u16, message:String, credited_to:Pubkey) -> Result<DonationMadeV1Event> {
            let epoch_tracker_bump=ctx.bumps.epoch_tracker;
            let debouncer_bump=ctx.bumps.debouncer;
            let event=DonatePubkeyConfigIdWithPayerV1::donate_pubkey_config_id_with_payer_v1_handler(ctx.accounts,crate::codec::wire::DonatePubkeyConfigIdWithPayerV1 {amount,config_id,tip_bps,message,credited_to},epoch_tracker_bump,debouncer_bump)?;
            emit!(event);emit_cpi!(event);Ok(event)
        }
        pub fn admit_bridge_payment_v1(ctx:Context<AdmitBridgePaymentV1>,source_id:[u8;32],source_commitment:[u8;32],payment_id:[u8;32],config_id:[u8;32],amount:u64,minimum_amount:u64,tip_bps:u16)->Result<BridgeDonationAdmittedV1Event> {
            check_relayer(&ctx.accounts.signer)?;
            let event=crate::instructions::v1::relayer_only::admit_bridge_payment::admit_bridge_payment(ctx.accounts,source_id,source_commitment,payment_id,config_id,amount,minimum_amount,tip_bps,ctx.bumps.receiver,ctx.bumps.epoch_tracker,ctx.bumps.debouncer)?;
            emit!(event);emit_cpi!(event);Ok(event)
        }
        pub fn recover_bridge_payment_v1(ctx:Context<RecoverBridgePaymentV1>,source_id:[u8;32],source_commitment:[u8;32],payment_id:[u8;32],amount:u64)->Result<BridgePaymentRecoveredV1Event> {
            let event=crate::instructions::v1::recover_bridge_payment::recover_bridge_payment(ctx.accounts,source_id,source_commitment,payment_id,amount,ctx.bumps.receiver)?;
            emit!(event);emit_cpi!(event);Ok(event)
        }
        pub fn close_donation_epoch_v1(ctx:Context<CloseDonationEpochV1>,config_id:[u8;32],epoch:u128)->Result<DonationEpochClosedV1Event> {
            check_relayer(&ctx.accounts.signer)?;
            let distribution_bump=ctx.bumps.distribution;
            let event=crate::settlement_handlers::close_epoch(ctx.accounts,crate::codec::wire::CloseDonationEpochV1 {config_id,epoch},distribution_bump)?;
            emit!(event);emit_cpi!(event);Ok(event)
        }
        pub fn swap_then_distribute_v1<'info>(ctx:Context<'_, '_, 'info, 'info,SwapThenDistributeV1<'info>>,jupiter_swap_ix_data:Vec<u8>,shares:Vec<Share>)->Result<DonationEpochProcessedV1Event> {
            check_relayer(&ctx.accounts.signer)?;
            let remaining=ctx.remaining_accounts;
            let event=crate::settlement_handlers::swap_then_distribute(ctx.accounts,crate::codec::wire::SwapThenDistributeV1 {jupiter_swap_ix_data,shares},remaining)?;
            emit!(event);emit_cpi!(event);Ok(event)
        }
        pub fn just_swap_v1<'info>(ctx:Context<'_, '_, '_, 'info,JustSwapV1<'info>>,swap_data:Vec<u8>)->Result<DonationEpochJustSwappedV1Event> {
            check_relayer(&ctx.accounts.signer)?;
            let event=crate::settlement_handlers::just_swap(ctx.accounts,crate::codec::wire::JustSwapV1 {jupiter_swap_ix_data:swap_data},ctx.remaining_accounts,ctx.bumps.swap_receipt)?;
            emit!(event);emit_cpi!(event);Ok(event)
        }
        pub fn distribute_after_just_swapping_v1<'info>(ctx:Context<'_, '_, 'info, 'info,DistributeAfterJustSwappingV1<'info>>,shares:Vec<Share>)->Result<DonationEpochProcessedV1Event> {
            check_relayer(&ctx.accounts.signer)?;
            let event=crate::settlement_handlers::distribute_after(ctx.accounts,crate::codec::wire::DistributeAfterJustSwappingV1 {shares},ctx.remaining_accounts)?;
            emit!(event);emit_cpi!(event);Ok(event)
        }
        pub fn distribute_non_swap_output_mint_v1<'info>(ctx:Context<'_, '_, 'info, 'info,DistributeNonSwapOutputMintV1<'info>>,shares:Vec<Share>)->Result<DonationEpochProcessedV1Event> {
            check_relayer(&ctx.accounts.signer)?;
            let event=crate::settlement_handlers::distribute_non_swap(ctx.accounts,crate::codec::wire::DistributeNonSwapOutputMintV1 {shares},ctx.remaining_accounts)?;
            emit!(event);emit_cpi!(event);Ok(event)
        }
        pub fn distribute_exact_non_swap_output_mint_v1<'info>(ctx:Context<'_, '_, 'info, 'info,DistributeNonSwapOutputMintV1<'info>>,transfers:Vec<ExactTransfer>)->Result<DonationEpochProcessedExactV1Event> {
            check_relayer(&ctx.accounts.signer)?;
            let event=crate::settlement_handlers::distribute_exact_non_swap(ctx.accounts,transfers,ctx.remaining_accounts)?;
            emit!(event);emit_cpi!(event);Ok(event)
        }
        pub fn distribute_exact_after_just_swapping_v1<'info>(ctx:Context<'_, '_, 'info, 'info,DistributeAfterJustSwappingV1<'info>>,transfers:Vec<ExactTransfer>)->Result<DonationEpochProcessedExactV1Event> {
            check_relayer(&ctx.accounts.signer)?;
            let event=crate::settlement_handlers::distribute_exact_after(ctx.accounts,transfers,ctx.remaining_accounts)?;
            emit!(event);emit_cpi!(event);Ok(event)
        }
        pub fn upsert_mint_whitelist_v1(ctx: Context<UpsertMintWhitelistV1>, mints: Vec<Pubkey>) -> Result<()> {
            check_relayer(&ctx.accounts.signer)?;
            upsert_whitelist(&mut ctx.accounts.mint_whitelist, mints, ctx.bumps.mint_whitelist)
        }
    }
    include!("anchor_donate.rs");
    pub use crate::state::v1::mint_whitelist::*;
    pub use crate::instructions::v1::relayer_only::upsert_mint_whitelist::*; pub(crate) use crate::instructions::v1::relayer_only::upsert_mint_whitelist::__client_accounts_upsert_mint_whitelist_v1;
}
pub(crate) use anchor_framework::{__client_accounts_upsert_mint_whitelist_v1,__client_accounts_admit_bridge_payment_v1,__client_accounts_recover_bridge_payment_v1,__client_accounts_donate_v1,__client_accounts_donate_pubkey_config_id_v1,__client_accounts_donate_pubkey_config_id_with_payer_v1,__client_accounts_donate_native_v1,__client_accounts_donate_native_pubkey_config_id_v1,__client_accounts_close_donation_epoch_v1,__client_accounts_just_swap_v1,__client_accounts_distribute_after_just_swapping_v1,__client_accounts_distribute_non_swap_output_mint_v1,__client_accounts_swap_then_distribute_v1};
anchor_lang::solana_program::entrypoint!(process_instruction);
fn process_instruction<'info>(program_id: &anchor_lang::solana_program::pubkey::Pubkey, accounts: &'info [anchor_lang::solana_program::account_info::AccountInfo<'info>], data: &[u8]) -> anchor_lang::solana_program::entrypoint::ProgramResult {
    anchor_framework::entry(program_id, accounts, data)
}


