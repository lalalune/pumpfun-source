use anchor_lang::prelude::*;

/// Permanent source membership. No close/reinitialization instruction exists.
#[account]
pub struct BridgeSourceV1 {}

/// Permanent payment membership, independent of the source identity.
#[account]
pub struct BridgePaymentV1 {}
