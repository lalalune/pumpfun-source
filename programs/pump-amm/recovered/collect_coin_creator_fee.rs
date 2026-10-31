//! PumpSwap `collect_coin_creator_fee`.
//!
//! A pure model of which check stops the call, the token balances afterwards
//! and the `CollectCoinCreatorFeeEvent` the program logs. Mint and token
//! accounts are read from raw bytes the way the captured program reads them.
//! Owners, lamports, the token-program id and the PDA matches arrive as facts
//! worked out by the caller.
//!
//! `tests/test_pump_amm_collect_coin_creator_fee_captured.py` runs the same
//! inputs on `evidence/original/pump_amm/deployed.so` with the captured SPL
//! Token and Token-2022 programs. Agreement there is matching behaviour on
//! those inputs, not a byte-identity claim.
//!
//! Limits. A mint is the base 82 bytes and a token account the base 165.
//! The captured token programs reject a zero-padded tail. A Token-2022
//! extension makes the account longer and changes the credit (a transfer-fee
//! mint pays `amount - fee`); that layout is not decoded. A native wrapped-SOL
//! source also moves lamports and can fail the rent check after the event is
//! logged. `is_native` is not read.

/// Anchor and program error numbers.
pub const INSTRUCTION_FALLBACK_NOT_FOUND: u32 = 101;
pub const CONSTRAINT_MUT: u32 = 2000;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const CONSTRAINT_ASSOCIATED: u32 = 2009;
pub const CONSTRAINT_TOKEN_MINT: u32 = 2014;
pub const CONSTRAINT_TOKEN_OWNER: u32 = 2015;
pub const CONSTRAINT_TOKEN_TOKEN_PROGRAM: u32 = 2021;
pub const CONSTRAINT_ASSOCIATED_TOKEN_TOKEN_PROGRAM: u32 = 2023;
pub const ACCOUNT_NOT_ENOUGH_KEYS: u32 = 3005;
pub const ACCOUNT_OWNED_BY_WRONG_PROGRAM: u32 = 3007;
pub const INVALID_PROGRAM_ID: u32 = 3008;
pub const ACCOUNT_NOT_INITIALIZED: u32 = 3012;
pub const CREATOR_VAULT_MIGRATED: u32 = 6048;

/// Errors observed from the captured SPL Token and Token-2022 programs.
pub const TOKEN_MINT_MISMATCH: u32 = 3;
pub const TOKEN_OVERFLOW: u32 = 14;
pub const TOKEN_ACCOUNT_FROZEN: u32 = 17;

/// `sha256("global:collect_coin_creator_fee")[..8]`.
pub const DISCRIMINATOR: [u8; 8] = [160, 57, 89, 42, 181, 139, 43, 66];
/// `sha256("event:CollectCoinCreatorFeeEvent")[..8]`.
pub const EVENT_DISCRIMINATOR: [u8; 8] = [232, 245, 194, 238, 234, 218, 58, 89];

pub const MINT_LEN: usize = 82;
pub const TOKEN_LEN: usize = 165;
pub const MINT_INITIALIZED: usize = 45;
pub const TOKEN_MINT: usize = 0;
pub const TOKEN_OWNER: usize = 32;
pub const TOKEN_AMOUNT: usize = 64;
pub const TOKEN_STATE: usize = 108;

/// Which well-known program owns an account, as the caller classified it.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Owner {
    /// Not SPL Token and not Token-2022. A missing account is this, with zero lamports.
    Other,
    SplToken,
    Token2022,
}

impl Owner {
    fn is_token(self) -> bool {
        matches!(self, Owner::SplToken | Owner::Token2022)
    }
}

/// The `quote_token_program` account's address.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum TokenProgram {
    /// Neither SPL Token nor Token-2022.
    Other,
    SplToken,
    Token2022,
}

impl TokenProgram {
    fn matches(self, owner: Owner) -> bool {
        matches!(
            (self, owner),
            (TokenProgram::SplToken, Owner::SplToken) | (TokenProgram::Token2022, Owner::Token2022)
        )
    }
}

/// Account-level facts that need the runtime or an address comparison.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Accounts {
    /// How many account metas the instruction carries.
    pub count: usize,
    /// Address of `quote_token_program`.
    pub token_program: TokenProgram,
    pub mint_owner: Owner,
    pub mint_lamports: u64,
    /// `coin_creator` is owned by the Pump Fees program. Zero lamports are not
    /// observed as that owner: the runtime presents no account.
    pub creator_owned_by_fees: bool,
    pub creator_lamports: u64,
    /// `coin_creator_vault_authority` is `["creator_vault", coin_creator]`.
    pub authority_ok: bool,
    pub vault_writable: bool,
    pub vault_owner: Owner,
    pub vault_lamports: u64,
    /// `coin_creator_vault_ata` is the ATA of the authority for this mint and token program.
    pub vault_ata_ok: bool,
    pub dest_writable: bool,
    pub dest_owner: Owner,
    pub dest_lamports: u64,
    /// `event_authority` is `["__event_authority"]`.
    pub event_ok: bool,
    /// `program` is PumpSwap itself. Checked only when an event is emitted.
    pub program_ok: bool,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Outcome {
    Error(u32),
    InvalidAccountData,
    UninitializedAccount,
    /// `emit!` ran and the following self-CPI could not find PumpSwap.
    /// The token accounts are left unchanged.
    MissingAccount {
        event: Vec<u8>,
    },
    /// The vault balance is zero: success, no transfer, no event.
    Idle,
    /// The vault balance moved onto the destination. `vault_amount` is zero.
    Collected {
        vault_amount: u64,
        dest_amount: u64,
        event: Vec<u8>,
    },
}

struct TokenAccount {
    mint: [u8; 32],
    owner: [u8; 32],
    amount: u64,
    frozen: bool,
    program: Owner,
}

fn key_at(data: &[u8], at: usize) -> [u8; 32] {
    let mut out = [0u8; 32];
    out.copy_from_slice(&data[at..at + 32]);
    out
}

fn valid_option_tag(data: &[u8], at: usize) -> bool {
    u32::from_le_bytes(data[at..at + 4].try_into().unwrap()) <= 1
}

fn load_mint(owner: Owner, lamports: u64, data: &[u8]) -> Result<(), Outcome> {
    if lamports == 0 {
        return Err(Outcome::Error(ACCOUNT_NOT_INITIALIZED));
    }
    if !owner.is_token() {
        return Err(Outcome::Error(ACCOUNT_OWNED_BY_WRONG_PROGRAM));
    }
    // SPL Token and Token-2022 both reject a mint that is not the base 82 bytes
    // when the tail is not a real extension. Only the base size is accepted.
    if data.len() != MINT_LEN {
        return Err(Outcome::InvalidAccountData);
    }
    // Unpack validates both COption tags before checking initialization.
    // The inactive payload of None is not required to be zero.
    if !valid_option_tag(data, 0) || !valid_option_tag(data, 46) {
        return Err(Outcome::InvalidAccountData);
    }
    match data[MINT_INITIALIZED] {
        0 => Err(Outcome::UninitializedAccount),
        1 => Ok(()),
        _ => Err(Outcome::InvalidAccountData),
    }
}

fn load_token(owner: Owner, lamports: u64, data: &[u8]) -> Result<TokenAccount, Outcome> {
    if lamports == 0 {
        return Err(Outcome::Error(ACCOUNT_NOT_INITIALIZED));
    }
    if !owner.is_token() {
        return Err(Outcome::Error(ACCOUNT_OWNED_BY_WRONG_PROGRAM));
    }
    // Same rule as the mint: the base 165-byte account, not a padded tail.
    if data.len() != TOKEN_LEN {
        return Err(Outcome::InvalidAccountData);
    }
    if !valid_option_tag(data, 72) || !valid_option_tag(data, 109) || !valid_option_tag(data, 129) {
        return Err(Outcome::InvalidAccountData);
    }
    let frozen = match data[TOKEN_STATE] {
        0 => return Err(Outcome::UninitializedAccount),
        1 => false,
        2 => true,
        _ => return Err(Outcome::InvalidAccountData),
    };
    Ok(TokenAccount {
        mint: key_at(data, TOKEN_MINT),
        owner: key_at(data, TOKEN_OWNER),
        amount: u64::from_le_bytes(data[TOKEN_AMOUNT..TOKEN_AMOUNT + 8].try_into().unwrap()),
        frozen,
        program: owner,
    })
}

fn event_bytes(
    timestamp: i64,
    creator: [u8; 32],
    amount: u64,
    vault: [u8; 32],
    dest: [u8; 32],
) -> Vec<u8> {
    let mut out = Vec::with_capacity(120);
    out.extend_from_slice(&EVENT_DISCRIMINATOR);
    out.extend_from_slice(&timestamp.to_le_bytes());
    out.extend_from_slice(&creator);
    out.extend_from_slice(&amount.to_le_bytes());
    out.extend_from_slice(&vault);
    out.extend_from_slice(&dest);
    out
}

/// `payload` is the whole instruction data, discriminator included.
/// `authority` is the address passed as `coin_creator_vault_authority`.
/// The other keys are `coin_creator`, the vault ATA, the destination token
/// account and `quote_mint`. `timestamp` is the clock's `unix_timestamp`.
#[allow(clippy::too_many_arguments)]
pub fn collect_coin_creator_fee(
    payload: &[u8],
    accounts: &Accounts,
    mint: &[u8],
    vault: &[u8],
    dest: &[u8],
    creator: [u8; 32],
    authority: [u8; 32],
    vault_key: [u8; 32],
    dest_key: [u8; 32],
    mint_key: [u8; 32],
    timestamp: i64,
) -> Outcome {
    if payload.len() < 8 || payload[..8] != DISCRIMINATOR {
        return Outcome::Error(INSTRUCTION_FALLBACK_NOT_FOUND);
    }
    // Loaded in field order. Owner and layout are checked as each account is
    // reached; a missing meta fails there. Seeds, `mut` and the token
    // constraints wait until all eight metas are present.
    if accounts.count < 1 {
        return Outcome::Error(ACCOUNT_NOT_ENOUGH_KEYS);
    }
    if let Err(outcome) = load_mint(accounts.mint_owner, accounts.mint_lamports, mint) {
        return outcome;
    }
    if accounts.count < 2 {
        return Outcome::Error(ACCOUNT_NOT_ENOUGH_KEYS);
    }
    if accounts.token_program == TokenProgram::Other {
        return Outcome::Error(INVALID_PROGRAM_ID);
    }
    if accounts.count < 5 {
        return Outcome::Error(ACCOUNT_NOT_ENOUGH_KEYS);
    }
    let vault_account = match load_token(accounts.vault_owner, accounts.vault_lamports, vault) {
        Ok(account) => account,
        Err(outcome) => return outcome,
    };
    if accounts.count < 6 {
        return Outcome::Error(ACCOUNT_NOT_ENOUGH_KEYS);
    }
    let dest_account = match load_token(accounts.dest_owner, accounts.dest_lamports, dest) {
        Ok(account) => account,
        Err(outcome) => return outcome,
    };
    if accounts.count < 8 {
        return Outcome::Error(ACCOUNT_NOT_ENOUGH_KEYS);
    }
    // The authority seeds come before either token account's constraints.
    // On the vault, the token-program id and the owner field are checked
    // before the ATA address, and `mut` is last. On the destination, `mut`
    // is first and the token-program id is last.
    if !accounts.authority_ok {
        return Outcome::Error(CONSTRAINT_SEEDS);
    }
    if !accounts.token_program.matches(vault_account.program) {
        return Outcome::Error(CONSTRAINT_ASSOCIATED_TOKEN_TOKEN_PROGRAM);
    }
    if vault_account.owner != authority {
        return Outcome::Error(CONSTRAINT_TOKEN_OWNER);
    }
    if !accounts.vault_ata_ok {
        return Outcome::Error(CONSTRAINT_ASSOCIATED);
    }
    if !accounts.vault_writable {
        return Outcome::Error(CONSTRAINT_MUT);
    }
    if !accounts.dest_writable {
        return Outcome::Error(CONSTRAINT_MUT);
    }
    if dest_account.owner != creator {
        return Outcome::Error(CONSTRAINT_TOKEN_OWNER);
    }
    if dest_account.mint != mint_key {
        return Outcome::Error(CONSTRAINT_TOKEN_MINT);
    }
    if !accounts.token_program.matches(dest_account.program) {
        return Outcome::Error(CONSTRAINT_TOKEN_TOKEN_PROGRAM);
    }
    if !accounts.event_ok {
        return Outcome::Error(CONSTRAINT_SEEDS);
    }
    // A fees-owned creator is rejected even when the vault is empty.
    if accounts.creator_owned_by_fees && accounts.creator_lamports > 0 {
        return Outcome::Error(CREATOR_VAULT_MIGRATED);
    }
    if vault_account.amount == 0 {
        return Outcome::Idle;
    }
    // Frozen is reported before a mint mismatch and before Token-2022 overflow.
    // The captured SPL Token program credits with wrapping arithmetic.
    // Token-2022 returns Overflow instead of wrapping.
    if vault_account.frozen || dest_account.frozen {
        return Outcome::Error(TOKEN_ACCOUNT_FROZEN);
    }
    if vault_account.mint != mint_key {
        return Outcome::Error(TOKEN_MINT_MISMATCH);
    }
    let dest_amount = match dest_account.amount.checked_add(vault_account.amount) {
        Some(sum) => sum,
        None if accounts.token_program == TokenProgram::Token2022 => {
            return Outcome::Error(TOKEN_OVERFLOW);
        }
        None => dest_account.amount.wrapping_add(vault_account.amount),
    };
    let event = event_bytes(
        timestamp,
        creator,
        vault_account.amount,
        vault_key,
        dest_key,
    );
    if !accounts.program_ok {
        return Outcome::MissingAccount { event };
    }
    Outcome::Collected {
        vault_amount: 0,
        dest_amount,
        event,
    }
}
