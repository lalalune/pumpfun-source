//! Captured `msg!` lines of the Pump handlers: the text each no-op path leaves
//! in the log, and the full `{:?}` dump of the GlobalVolumeAccumulator that
//! `admin_update_token_incentives` prints. The state models of these
//! instructions end at "nothing moved"; the line is all that tells the paths
//! apart.
//!
//! Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_handler_logs_captured.py`. Not linked into the SBF crate. This
//! is not a byte-identity claim.
//!
//! The `admin_cto` lines are out of scope here.

/// Account lengths `extend_account` grows to.
pub const GLOBAL_SIZE: u64 = 1088;
pub const CURVE_SIZE: u64 = 166;
pub const GVA_SIZE: u64 = 600;
pub const UVA_SIZE: u64 = 137;
/// The dump shows this many stored bytes, then `..`.
pub const DUMPED_BYTES: usize = 64;

pub fn rent_minimum(data_len: u64) -> u64 {
    (128 + data_len) * 6960
}

const ALPHABET: &[u8; 58] = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";

pub fn base58(key: &[u8; 32]) -> String {
    let mut digits: Vec<u8> = Vec::new();
    for &byte in key {
        let mut carry = byte as u32;
        for digit in digits.iter_mut() {
            carry += (*digit as u32) << 8;
            *digit = (carry % 58) as u8;
            carry /= 58;
        }
        while carry > 0 {
            digits.push((carry % 58) as u8);
            carry /= 58;
        }
    }
    let zeros = key.iter().take_while(|b| **b == 0).count();
    let leading = std::iter::repeat(b'1').take(zeros);
    let rest = digits.iter().rev().map(|d| ALPHABET[*d as usize]);
    String::from_utf8(leading.chain(rest).collect()).unwrap()
}

/// `sweep_protocol_fee` (bucket 0) and `sweep_creator_fee` (bucket 1).
pub fn sweep(creator: bool, amount: u64) -> Vec<String> {
    if amount == 0 {
        return vec![format!("Nothing to sweep for fee bucket {}", creator as u8)];
    }
    vec![]
}

pub fn claim_tokens(amount: u64) -> Vec<String> {
    if amount == 0 {
        return vec!["No tokens to claim".to_string()];
    }
    vec![]
}

pub fn sync(user: &[u8; 32], claimed_before: u64, claimed_after: u64) -> Vec<String> {
    if claimed_before == claimed_after {
        return vec![format!("No changes in accumulator for user={}", base58(user))];
    }
    vec![]
}

/// `claim_cashback` and the native route of `claim_cashback_v2`.
pub fn cashback_native(lamports: u64, size: u64) -> Vec<String> {
    if lamports.saturating_sub(rent_minimum(size)) == 0 {
        return vec!["No cashback to claim".to_string()];
    }
    vec![]
}

/// The token route of `claim_cashback_v2`: `None` is a missing accumulator ATA.
pub fn cashback_token(balance: Option<u64>) -> Vec<String> {
    if balance.unwrap_or(0) == 0 {
        return vec!["No cashback to claim".to_string()];
    }
    vec![]
}

pub enum Collect {
    Native,
    /// A token vault: the rent checks of the native route do not apply.
    Token(u64),
}

/// `collect_creator_fee` and `collect_creator_fee_v2`.
pub fn collect(executable: bool, lamports: u64, data_len: u64, vault: u64, quote: Collect) -> Vec<String> {
    if executable {
        return vec!["Creator account is executable, so it cannot receive lamports".to_string()];
    }
    let amount = match quote {
        Collect::Token(amount) => amount,
        Collect::Native => vault.saturating_sub(rent_minimum(0)),
    };
    if amount == 0 {
        return vec!["No creator fee to collect".to_string()];
    }
    if matches!(quote, Collect::Native) && lamports.saturating_add(amount) < rent_minimum(data_len) {
        return vec!["Creator account does not have enough rent-exemption lamports".to_string()];
    }
    vec![]
}

/// The length `extend_account` grows an account of this type to.
pub fn target_size(kind: &str) -> Option<u64> {
    match kind {
        "global" => Some(GLOBAL_SIZE),
        "bc" => Some(CURVE_SIZE),
        "gva" => Some(GVA_SIZE),
        "uva" => Some(UVA_SIZE),
        _ => None,
    }
}

pub fn extend(current_size: u64, new_size: u64) -> Vec<String> {
    if current_size == new_size {
        return vec!["Account already has the correct size".to_string()];
    }
    if current_size > new_size {
        return vec![format!("Account already has more than {new_size} bytes: {current_size}")];
    }
    vec![]
}

/// `set_creator` (a metadata without creators falls back to the argument) and
/// `set_metaplex_creator`.
pub fn assign_creator(metaplex: bool, curve_has_creator: bool, metadata_has_creators: bool) -> Vec<String> {
    if curve_has_creator {
        return vec!["Bonding curve has creator already set".to_string()];
    }
    if metaplex && !metadata_has_creators {
        return vec!["Missing metaplex creators".to_string()];
    }
    vec![]
}

/// `migrate` and `migrate_v2`: a complete curve with all four reserves at zero.
pub fn migrate(reserves: [u64; 4]) -> Vec<String> {
    if reserves == [0; 4] {
        return vec!["Bonding curve already migrated".to_string()];
    }
    vec![]
}

pub fn unable_to_distribute(recipient: &[u8; 32]) -> Vec<String> {
    vec![format!(
        "Unable to distribute to {}. Shareholder is a program account, use pump_fees::update_fee_shares to remove the shareholder from the team",
        base58(recipient)
    )]
}

pub fn insufficient_fees(minimum_vault_balance: u64) -> Vec<String> {
    vec![format!(
        "Insufficient fees for distribution. Minimum vault balance needed: {minimum_vault_balance} lamports. Use get_minimum_distributable_fee instruction to check the minimum distributable amount."
    )]
}

pub struct Dump<'a> {
    pub start_time: i64,
    pub end_time: i64,
    pub seconds_in_a_day: i64,
    pub mint: &'a [u8; 32],
    pub total_token_supply: &'a [u64],
    pub sol_volumes: &'a [u64],
    pub key: &'a [u8; 32],
    pub owner: &'a [u8; 32],
    pub lamports: u64,
    /// The account bytes: the handler prints before they are written back, so
    /// the typed fields show the new values and these still show the old ones.
    pub stored: &'a [u8],
}

pub fn schedule_dump(d: &Dump) -> String {
    let data: String = d.stored[..DUMPED_BYTES].iter().map(|b| format!("{b:02x}")).collect();
    format!(
        "GlobalVolumeAccumulator=Account {{ account: GlobalVolumeAccumulator {{ start_time: {}, end_time: {}, seconds_in_a_day: {}, mint: {}, total_token_supply: {:?}, sol_volumes: {:?} }}, info: AccountInfo {{ key: {}, owner: {}, is_signer: false, is_writable: true, executable: false, rent_epoch: 18446744073709551615, lamports: {}, data.len: {}, data: {}, .. }} }}",
        d.start_time,
        d.end_time,
        d.seconds_in_a_day,
        base58(d.mint),
        d.total_token_supply,
        d.sol_volumes,
        base58(d.key),
        base58(d.owner),
        d.lamports,
        d.stored.len(),
        data,
    )
}
