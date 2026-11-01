use anchor_lang::prelude::*;
use crate::anchor_framework::{DaasEventDiscriminator};

/// External attribution is bound by the existing source commitment, never a synthetic Pubkey.
#[event]
pub struct BridgeDonationAdmittedV1Event {pub daas_event_discriminator:DaasEventDiscriminator,pub source_id:[u8;32],pub source_commitment:[u8;32],pub payment_id:[u8;32],pub config_id:[u8;32],pub mint:Pubkey,pub epoch:u128,pub gross_amount:u64,pub tip:u64}
