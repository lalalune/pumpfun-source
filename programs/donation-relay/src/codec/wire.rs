//! Wire structs reconstructed from the captured Relay IDL.
use anchor_lang::prelude::*;
#[derive(AnchorDeserialize,AnchorSerialize,Clone,Copy)]
pub enum ShareType {Beneficiary, Fee, Tip}
#[derive(AnchorDeserialize,AnchorSerialize,Clone)]
pub struct Share {pub share_type:ShareType,pub address:Pubkey,pub bps:u16}
#[derive(AnchorDeserialize)]
pub struct CloseDonationEpochV1 { pub config_id:[u8;32],pub epoch:u128 }
#[derive(AnchorDeserialize)]
pub struct DistributeAfterJustSwappingV1 { pub shares:Vec<Share> }
#[derive(AnchorDeserialize)]
pub struct DistributeNonSwapOutputMintV1 { pub shares:Vec<Share> }
#[derive(AnchorDeserialize)]
pub struct DonateNativePubkeyConfigIdV1 { pub amount:u64,pub config_id:Pubkey,pub tip_bps:u16,pub message:String,pub credited_to:Pubkey }
#[derive(AnchorDeserialize)]
pub struct DonateNativeV1 { pub amount:u64,pub config_id:[u8;32],pub tip_bps:u16,pub message:String,pub credited_to:Pubkey }
#[derive(AnchorDeserialize)]
pub struct DonatePubkeyConfigIdV1 { pub amount:u64,pub config_id:Pubkey,pub tip_bps:u16,pub message:String,pub credited_to:Pubkey }
#[derive(AnchorDeserialize)]
pub struct DonatePubkeyConfigIdWithPayerV1 { pub amount:u64,pub config_id:Pubkey,pub tip_bps:u16,pub message:String,pub credited_to:Pubkey }
#[derive(AnchorDeserialize)]
pub struct DonateV1 { pub amount:u64,pub config_id:[u8;32],pub tip_bps:u16,pub message:String,pub credited_to:Pubkey }
#[derive(AnchorDeserialize)]
pub struct JustSwapV1 { pub jupiter_swap_ix_data:Vec<u8> }
#[derive(AnchorDeserialize)]
pub struct SwapThenDistributeV1 { pub jupiter_swap_ix_data:Vec<u8>,pub shares:Vec<Share> }
#[derive(AnchorDeserialize)]
pub struct UpsertMintWhitelistV1 { pub mints:Vec<Pubkey> }
