//! Wire structs reconstructed from the captured Relay IDL.
use borsh::BorshDeserialize;
use anchor_lang::solana_program::pubkey::Pubkey;
#[derive(BorshDeserialize,borsh::BorshSerialize,Clone,Copy)]
pub enum ShareType {Beneficiary, Fee, Tip}
#[derive(BorshDeserialize,borsh::BorshSerialize,Clone)]
pub struct Share {pub share_type:ShareType,pub address:Pubkey,pub bps:u16}
#[derive(BorshDeserialize)]
pub struct CloseDonationEpochV1 { pub config_id:[u8;32],pub epoch:u128 }
#[derive(BorshDeserialize)]
pub struct DistributeAfterJustSwappingV1 { pub shares:Vec<Share> }
#[derive(BorshDeserialize)]
pub struct DistributeNonSwapOutputMintV1 { pub shares:Vec<Share> }
#[derive(BorshDeserialize)]
pub struct DonateNativePubkeyConfigIdV1 { pub amount:u64,pub config_id:Pubkey,pub tip_bps:u16,pub message:String,pub credited_to:Pubkey }
#[derive(BorshDeserialize)]
pub struct DonateNativeV1 { pub amount:u64,pub config_id:[u8;32],pub tip_bps:u16,pub message:String,pub credited_to:Pubkey }
#[derive(BorshDeserialize)]
pub struct DonatePubkeyConfigIdV1 { pub amount:u64,pub config_id:Pubkey,pub tip_bps:u16,pub message:String,pub credited_to:Pubkey }
#[derive(BorshDeserialize)]
pub struct DonatePubkeyConfigIdWithPayerV1 { pub amount:u64,pub config_id:Pubkey,pub tip_bps:u16,pub message:String,pub credited_to:Pubkey }
#[derive(BorshDeserialize)]
pub struct DonateV1 { pub amount:u64,pub config_id:[u8;32],pub tip_bps:u16,pub message:String,pub credited_to:Pubkey }
#[derive(BorshDeserialize)]
pub struct JustSwapV1 { pub jupiter_swap_ix_data:Vec<u8> }
#[derive(BorshDeserialize)]
pub struct SwapThenDistributeV1 { pub jupiter_swap_ix_data:Vec<u8>,pub shares:Vec<Share> }
#[derive(BorshDeserialize)]
pub struct UpsertMintWhitelistV1 { pub mints:Vec<Pubkey> }
