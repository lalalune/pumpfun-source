//! Captured behavior of Pump `distribute_creator_fees` and the token route of
//! `distribute_creator_fees_v2` when a shareholder's key is also another
//! account of the call, or appears twice in the sharing config.
//!
//! Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_distribution_alias_captured.py`. Not linked into the SBF crate.
//! This is not a byte-identity claim.
//!
//! Observed rules:
//! - Each slot is priced and checked on its own. A key that appears twice
//!   gets two shares, and its rent deficit is measured once per slot on the
//!   balance from before any payment, so the second share does not help the
//!   threshold of the first.
//! - The creator vault may be its own shareholder. Its share moves nothing
//!   but counts in `distributed`, and the System transfer still needs the
//!   balance, so the slot order decides a config above 100%.
//! - The same holds for the vault's token account: a self-transfer moves no
//!   token, but SPL Token still refuses it above the balance.
//! - A repeated wallet whose token account is absent is created once by its
//!   first slot; the second slot asks the Associated Token program to create
//!   it again and fails with `IllegalOwner` before any token moves.
//! - A read-only slot only matters when the key is not writable anywhere in
//!   the call and a non-zero payment or a new token account reaches it. On
//!   the token route the slot that counts is the token account's, so a
//!   read-only payer wallet is no help and its token account is not writable.
//! - A config above 100% can leave the vault between zero and its rent
//!   minimum; LiteSVM accepts that end state. Unconfirmed on a real cluster.

pub const OVERFLOW: u32 = 6024;
pub const EXECUTABLE_RECIPIENT: u32 = 6052;
pub const INVALID_SHARE_BPS: u32 = 6055;
pub const UNINITIALIZED_ATA: u32 = 6070;
/// System program `ResultWithNegativeLamports`, SPL Token `InsufficientFunds`.
pub const INSUFFICIENT: u32 = 1;
pub const ROLES: usize = 10;

pub fn rent_minimum(data_len: u64) -> u64 {
    (128 + data_len) * 6960
}

/// A key the sharing config can name.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Role {
    Payer,
    Vault,
    Curve,
    Config,
    Mint,
    EventAuthority,
    Holder0,
    Holder1,
    Program,
    System,
}

impl Role {
    pub fn executable(self) -> bool {
        matches!(self, Role::Program | Role::System)
    }
}

#[derive(Clone, Copy, Debug)]
pub struct Slot {
    pub role: Role,
    pub bps: u16,
    pub writable: bool,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Stop {
    Code(u32),
    PrivilegeEscalation,
    IllegalOwner,
}

fn key_writable(slots: &[Slot], role: Role, fixed: &[Role]) -> bool {
    fixed.contains(&role) || slots.iter().any(|s| s.role == role && s.writable)
}

pub struct Lamports {
    /// Balances and data sizes per `Role`, after the transaction fee.
    pub balances: [u64; ROLES],
    pub data_len: [u64; ROLES],
}

#[derive(Debug, PartialEq, Eq)]
pub struct Paid {
    pub balances: [u64; ROLES],
    pub distributed: u64,
    pub event: bool,
}

pub fn distribute(l: &Lamports, slots: &[Slot]) -> Result<Paid, Stop> {
    let vault = Role::Vault as usize;
    let available = l.balances[vault].saturating_sub(rent_minimum(0));
    let mut plan = Vec::new();
    let mut minimum = 0u64;
    for slot in slots {
        if slot.role.executable() {
            return Err(Stop::Code(EXECUTABLE_RECIPIENT));
        }
        if slot.bps == 0 {
            return Err(Stop::Code(INVALID_SHARE_BPS));
        }
        let bps = u64::from(slot.bps);
        let index = slot.role as usize;
        let deficit = rent_minimum(l.data_len[index]).saturating_sub(l.balances[index]);
        let threshold = (deficit * 10_000 + bps - 1) / bps;
        minimum = minimum.max(threshold);
        plan.push(available.checked_mul(bps).ok_or(Stop::Code(OVERFLOW))? / 10_000);
    }
    let mut balances = l.balances;
    if available < minimum {
        return Ok(Paid { balances, distributed: 0, event: false });
    }
    let mut distributed = 0u64;
    for (slot, &amount) in slots.iter().zip(&plan) {
        let index = slot.role as usize;
        if amount > 0 && !key_writable(slots, slot.role, &[Role::Payer, Role::Vault]) {
            return Err(Stop::PrivilegeEscalation);
        }
        if balances[vault] < amount {
            return Err(Stop::Code(INSUFFICIENT));
        }
        balances[vault] -= amount;
        balances[index] += amount;
        distributed += amount;
    }
    Ok(Paid { balances, distributed, event: true })
}

pub struct Tokens {
    pub vault_tokens: u64,
    /// Whether each role's token account exists, the vault's always does.
    pub ata_exists: [bool; ROLES],
    pub initialize_ata: bool,
}

#[derive(Debug, PartialEq, Eq)]
pub struct TokenPaid {
    /// Balance of each role's token account, after the call.
    pub balances: [u64; ROLES],
    pub distributed: u64,
    pub created: u64,
}

pub fn distribute_tokens(t: &Tokens, slots: &[Slot]) -> Result<TokenPaid, Stop> {
    let mut plan = Vec::new();
    let mut exists = t.ata_exists;
    let mut create = Vec::new();
    for slot in slots {
        if slot.role.executable() {
            return Err(Stop::Code(EXECUTABLE_RECIPIENT));
        }
        if slot.bps == 0 {
            return Err(Stop::Code(INVALID_SHARE_BPS));
        }
        let amount = t.vault_tokens.checked_mul(u64::from(slot.bps)).ok_or(Stop::Code(OVERFLOW))? / 10_000;
        if !exists[slot.role as usize] && !t.initialize_ata {
            return Err(Stop::Code(UNINITIALIZED_ATA));
        }
        create.push(!exists[slot.role as usize]);
        plan.push(amount);
    }
    let vault = Role::Vault as usize;
    let mut balances = [0u64; ROLES];
    balances[vault] = t.vault_tokens;
    let mut distributed = 0u64;
    let mut created = 0;
    for ((slot, &amount), &new) in slots.iter().zip(&plan).zip(&create) {
        let index = slot.role as usize;
        if new {
            if exists[index] {
                return Err(Stop::IllegalOwner);
            }
            if !key_writable(slots, slot.role, &[Role::Vault]) {
                return Err(Stop::PrivilegeEscalation);
            }
            exists[index] = true;
            created += 1;
        }
        if amount > 0 && !key_writable(slots, slot.role, &[Role::Vault]) {
            return Err(Stop::PrivilegeEscalation);
        }
        if balances[vault] < amount {
            return Err(Stop::Code(INSUFFICIENT));
        }
        balances[vault] -= amount;
        balances[index] += amount;
        distributed += amount;
    }
    Ok(TokenPaid { balances, distributed, created })
}
