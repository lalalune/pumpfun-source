use anchor_lang::prelude::*;
use crate::anchor_framework::{DaasEventDiscriminator};

/// An exceptional USDC transfer, not a donation or proof of reimbursement to the EVM payer.
#[event]
pub struct BridgePaymentRecoveredV1Event {pub daas_event_discriminator:DaasEventDiscriminator,pub source_id:[u8;32],pub source_commitment:[u8;32],pub payment_id:[u8;32],pub mint:Pubkey,pub receiver_token_account:Pubkey,pub destination_owner:Pubkey,pub destination_token_account:Pubkey,pub amount:u64,pub authority:Pubkey}
