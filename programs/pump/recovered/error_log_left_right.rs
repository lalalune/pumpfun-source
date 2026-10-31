//! Captured Pump `Left:` / `Right:` error log lines: which two keys a failing
//! constraint compares, for the sites the captured tests reach.
//!
//! Checked against `evidence/original/pump/deployed.so` on LiteSVM by
//! `tests/test_error_log_left_right_captured.py`, which records the failing
//! transactions of the other captured tests and adds a small fixture of its
//! own for the v3 buyback-recipient owner check (`trade_v3.rs:172`), driven
//! with a system-owned and a Token-2022-owned account in that slot against
//! the SPL Token expectation. When a Pump instruction fails at
//! one of the sites below, the error line Anchor logs is followed at once by
//! four lines
//!
//! ```text
//! Left:
//! <left key>
//! Right:
//! <right key>
//! ```
//!
//! and each side of the pair is the value its `Side` names: a constant key, the
//! key passed in an instruction account slot, the owner of the account passed
//! in a slot, a field stored in an account, or — for a seeds constraint — the
//! address the constraint derives. Each row was read from logs of the captured
//! program and matched against the transaction and the pre-state that produced
//! it. This is not a byte-identity claim.
//!
//! Two families print a constant pair by construction: a not-equal guard logs
//! the checked value next to the forbidden value, and the two are equal
//! whenever the guard fires — the zero key at the sites that refuse an unset
//! or zero mint, and the wrapped-SOL mint at the two whitelist-eligibility
//! guards.
//!
//! Unconfirmed (outside the checked inputs): the `Right:` side of the seeds
//! rows is pinned as the derived address by its position in the pair — the
//! test does not recompute seed recipes, so the derivation itself is not
//! checked. Sites that log a pair but whose operands this packet does not pin
//! stay unconfirmed: `programs/pump/src/buy_v2.rs:121` (its expected side was
//! not identified), the create_v2 quote-chain guards at
//! `create_v2.rs:220`/`:243`/`:258`/`:348`/`:353`/`:437`/`:442` and
//! `creator/distribute_fee_to_holders.rs:122` (operands from remaining
//! accounts and stored lists), the `multi_hop_curve_swap` occurrences of
//! `trade_v3.rs:180` and `multi_hop_curve_swap.rs:262` (remaining-account hop
//! mints), and the `claim_cashback_v2` sites in
//! `token_incentives/claim_token_incentives.rs` (token-incentives handlers).
//! Error sites that log no pair at all are the subject of `error_sites.rs`
//! and its siblings.

/// How the line names the place that failed.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Kind {
    /// `AnchorError thrown in programs/pump/src/<file>:<line>.`
    Thrown,
    /// `AnchorError caused by account: <name>.`
    Account,
    /// `ProgramError caused by account: <name>.`
    Program,
    /// `AnchorError occurred.`
    Occurred,
}

/// What one side of a logged pair is.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Side {
    /// The zero key, `11111111111111111111111111111111`.
    Zero,
    /// The wrapped-SOL mint, `So11111111111111111111111111111111111111112`.
    Wsol,
    /// The Pump program itself.
    Pump,
    /// The SPL Token program.
    Token,
    /// The Token-2022 program.
    Token2022,
    /// The associated token account program.
    AtaProgram,
    /// The Pump fees program, `pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ`.
    FeesProgram,
    /// The Metaplex token metadata program.
    MetaplexProgram,
    /// The rent sysvar.
    RentSysvar,
    /// The Mayhem program id the create_v2 address constraint expects.
    MayhemProgram,
    /// The Pump IDL account the admin idl-authority address constraint expects.
    IdlAccount,
    /// The key passed in the named instruction account slot.
    Slot(&'static str),
    /// The owner of the account passed in the named instruction account slot.
    OwnerOf(&'static str),
    /// The authority stored in the global account (data bytes 9..41).
    StoredAuthority,
    /// The withdraw authority stored in the global account (data bytes
    /// 113..145); the migrate handlers authorize against it.
    StoredWithdrawAuthority,
    /// The set-creator authority stored in the global account (data bytes
    /// 386..418).
    StoredSetCreatorAuthority,
    /// The holder-reward claim authority stored in the global account (data
    /// bytes 1054..1086).
    StoredHolderRewardClaimAuthority,
    /// The mint stored in the sharing config account (data bytes 11..43).
    StoredSharingMint,
    /// The address a seeds constraint derives from the passed accounts.
    Derived,
}

impl Side {
    /// The constant key this side prints, when it is a constant.
    pub fn constant(self) -> Option<&'static str> {
        Some(match self {
            Side::Zero => "11111111111111111111111111111111",
            Side::Wsol => "So11111111111111111111111111111111111111112",
            Side::Pump => "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P",
            Side::Token => "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
            Side::Token2022 => "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",
            Side::AtaProgram => "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL",
            Side::FeesProgram => "pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ",
            Side::MetaplexProgram => "metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s",
            Side::RentSysvar => "SysvarRent111111111111111111111111111111111",
            Side::MayhemProgram => "MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e",
            Side::IdlAccount => "AYgC53tU5BbP2NAnv5nConJxAdpQZctvmZK88pu69xRs",
            _ => return None,
        })
    }

    /// Short name of the form, as the host driver reports it.
    pub fn form(self) -> String {
        match self {
            Side::Zero => "zero".to_string(),
            Side::Wsol => "wsol".to_string(),
            Side::Pump => "pump".to_string(),
            Side::Token => "token".to_string(),
            Side::Token2022 => "token2022".to_string(),
            Side::AtaProgram => "ata_program".to_string(),
            Side::FeesProgram => "fees_program".to_string(),
            Side::MetaplexProgram => "metaplex_program".to_string(),
            Side::RentSysvar => "rent_sysvar".to_string(),
            Side::MayhemProgram => "mayhem_program".to_string(),
            Side::IdlAccount => "idl_account".to_string(),
            Side::Slot(name) => format!("slot:{name}"),
            Side::OwnerOf(name) => format!("owner:{name}"),
            Side::StoredAuthority => "stored_authority".to_string(),
            Side::StoredWithdrawAuthority => "stored_withdraw_authority".to_string(),
            Side::StoredSetCreatorAuthority => "stored_set_creator_authority".to_string(),
            Side::StoredHolderRewardClaimAuthority => "stored_holder_reward_claim_authority".to_string(),
            Side::StoredSharingMint => "stored_sharing_mint".to_string(),
            Side::Derived => "derived".to_string(),
        }
    }
}

/// Handler, line form, place, code, left side, right side.
pub const PAIRS: &[(&str, Kind, &str, u64, Side, Side)] = &[
    ("add_quote_control_mint", Kind::Account, "quote_control", 3007, Side::OwnerOf("quote_control"), Side::Pump),
    ("add_quote_control_mint", Kind::Thrown, "quote_control/state.rs:62", 6069, Side::Zero, Side::Zero),
    ("add_quote_control_mint", Kind::Thrown, "quote_control/state.rs:67", 6069, Side::Wsol, Side::Wsol),
    ("add_quote_mint", Kind::Account, "event_authority", 2006, Side::Slot("event_authority"), Side::Derived),
    ("add_quote_mint", Kind::Account, "global", 2006, Side::Slot("global"), Side::Derived),
    ("add_quote_mint", Kind::Account, "global", 3007, Side::OwnerOf("global"), Side::Pump),
    ("add_quote_mint", Kind::Account, "global", 6000, Side::StoredAuthority, Side::Slot("authority")),
    ("add_quote_mint", Kind::Thrown, "lib.rs:1950", 6069, Side::Zero, Side::Zero),
    ("add_quote_mint", Kind::Thrown, "lib.rs:1955", 6069, Side::Wsol, Side::Wsol),
    ("admin_set_idl_authority", Kind::Account, "global", 6000, Side::StoredAuthority, Side::Slot("authority")),
    ("admin_set_idl_authority", Kind::Account, "idl_account", 2012, Side::Slot("idl_account"), Side::IdlAccount),
    ("admin_set_idl_authority", Kind::Account, "program_signer", 2006, Side::Slot("program_signer"), Side::Derived),
    ("buy", Kind::Account, "user_volume_accumulator", 3007, Side::OwnerOf("user_volume_accumulator"), Side::Pump),
    ("buy_exact_quote_in_v3", Kind::Thrown, "trade_v3.rs:172", 6010, Side::OwnerOf("buyback_fee_recipient"), Side::Token),
    ("buy_v3", Kind::Thrown, "buy_v2.rs:116", 6004, Side::Slot("base_mint"), Side::Slot("quote_mint")),
    ("buy_v3", Kind::Thrown, "trade_v3.rs:172", 6010, Side::OwnerOf("buyback_fee_recipient"), Side::Token),
    ("buy_v3", Kind::Thrown, "trade_v3.rs:180", 6004, Side::Slot("base_mint"), Side::Slot("quote_mint")),
    ("buy_v3", Kind::Thrown, "trade_v3.rs:188", 2006, Side::Slot("buyback_fee_recipient"), Side::Derived),
    ("claim_cashback", Kind::Account, "user_volume_accumulator", 2006, Side::Slot("user_volume_accumulator"), Side::Derived),
    ("claim_cashback", Kind::Account, "user_volume_accumulator", 3007, Side::OwnerOf("user_volume_accumulator"), Side::Pump),
    ("close_user_volume_accumulator", Kind::Account, "user_volume_accumulator", 3007, Side::OwnerOf("user_volume_accumulator"), Side::Pump),
    ("create", Kind::Account, "bonding_curve", 2006, Side::Slot("bonding_curve"), Side::Derived),
    ("create", Kind::Account, "metadata", 2006, Side::Slot("metadata"), Side::Derived),
    ("create", Kind::Account, "mint_authority", 2006, Side::Slot("mint_authority"), Side::Derived),
    ("create", Kind::Thrown, "lib.rs:334", 6030, Side::Zero, Side::Zero),
    ("create_v2", Kind::Account, "associated_token_program", 3008, Side::Slot("associated_token_program"), Side::AtaProgram),
    ("create_v2", Kind::Account, "bonding_curve", 2006, Side::Slot("bonding_curve"), Side::Derived),
    ("create_v2", Kind::Account, "event_authority", 2006, Side::Slot("event_authority"), Side::Derived),
    ("create_v2", Kind::Account, "global_params", 2006, Side::Slot("global_params"), Side::Derived),
    ("create_v2", Kind::Account, "mayhem_program_id", 2012, Side::Slot("mayhem_program_id"), Side::MayhemProgram),
    ("create_v2", Kind::Account, "mayhem_state", 2006, Side::Slot("mayhem_state"), Side::Derived),
    ("create_v2", Kind::Account, "mint_authority", 2006, Side::Slot("mint_authority"), Side::Derived),
    ("create_v2", Kind::Account, "sol_vault", 2006, Side::Slot("sol_vault"), Side::Derived),
    ("create_v2", Kind::Account, "system_program", 3008, Side::Slot("system_program"), Side::Zero),
    ("create_v2", Kind::Account, "token_program", 3008, Side::Slot("token_program"), Side::Token2022),
    ("create_v2", Kind::Thrown, "create_v2.rs:732", 6030, Side::Zero, Side::Zero),
    ("distribute_creator_fees", Kind::Account, "sharing_config", 6004, Side::StoredSharingMint, Side::Slot("mint")),
    ("distribute_creator_fees_v2", Kind::Account, "sharing_config", 6004, Side::StoredSharingMint, Side::Slot("mint")),
    ("distribute_fee_to_holders", Kind::Account, "global", 6000, Side::StoredHolderRewardClaimAuthority, Side::Slot("holder_reward_claim_authority")),
    ("distribute_fee_to_holders", Kind::Account, "holder_rewards", 2006, Side::Slot("holder_rewards"), Side::Derived),
    ("extend_account", Kind::Account, "account", 2004, Side::OwnerOf("account"), Side::Pump),
    ("get_minimum_distributable_fee", Kind::Account, "sharing_config", 6004, Side::StoredSharingMint, Side::Slot("mint")),
    ("init_user_volume_accumulator", Kind::Account, "user_volume_accumulator", 3007, Side::OwnerOf("user_volume_accumulator"), Side::Pump),
    ("initialize", Kind::Account, "global", 2006, Side::Slot("global"), Side::Derived),
    ("initialize", Kind::Account, "system_program", 3008, Side::Slot("system_program"), Side::Zero),
    ("migrate", Kind::Account, "amm_global_config", 2006, Side::Slot("amm_global_config"), Side::Derived),
    ("migrate", Kind::Account, "global", 6000, Side::StoredWithdrawAuthority, Side::Slot("withdraw_authority")),
    ("migrate", Kind::Account, "lp_mint", 2006, Side::Slot("lp_mint"), Side::Derived),
    ("migrate", Kind::Account, "pool", 2006, Side::Slot("pool"), Side::Derived),
    ("migrate", Kind::Account, "pump_amm_event_authority", 2006, Side::Slot("pump_amm_event_authority"), Side::Derived),
    ("migrate", Kind::Account, "rent", 2012, Side::Slot("rent"), Side::RentSysvar),
    ("migrate_bonding_curve_creator", Kind::Account, "bonding_curve", 2006, Side::Slot("bonding_curve"), Side::Derived),
    ("migrate_bonding_curve_creator", Kind::Account, "sharing_config", 2006, Side::Slot("sharing_config"), Side::Derived),
    ("migrate_bonding_curve_creator", Kind::Account, "sharing_config", 3007, Side::OwnerOf("sharing_config"), Side::FeesProgram),
    ("migrate_bonding_curve_creator", Kind::Account, "sharing_config", 6004, Side::StoredSharingMint, Side::Slot("mint")),
    ("migrate_v2", Kind::Account, "amm_global_config", 2006, Side::Slot("amm_global_config"), Side::Derived),
    ("migrate_v2", Kind::Account, "associated_quote_bonding_curve", 2006, Side::Slot("associated_quote_bonding_curve"), Side::Derived),
    ("migrate_v2", Kind::Account, "global", 6000, Side::StoredWithdrawAuthority, Side::Slot("withdraw_authority")),
    ("migrate_v2", Kind::Account, "lp_mint", 2006, Side::Slot("lp_mint"), Side::Derived),
    ("migrate_v2", Kind::Account, "pool", 2006, Side::Slot("pool"), Side::Derived),
    ("migrate_v2", Kind::Account, "pool_authority_quote_account", 2006, Side::Slot("pool_authority_quote_account"), Side::Derived),
    ("migrate_v2", Kind::Account, "pool_quote_token_account", 2006, Side::Slot("pool_quote_token_account"), Side::Derived),
    ("migrate_v2", Kind::Account, "rent", 2012, Side::Slot("rent"), Side::RentSysvar),
    ("migrate_v2", Kind::Thrown, "migrate_v2.rs:243", 2006, Side::Slot("pump_amm_event_authority"), Side::Derived),
    ("remove_quote_control_mint", Kind::Account, "quote_control", 3007, Side::OwnerOf("quote_control"), Side::Pump),
    ("remove_quote_control_mint", Kind::Thrown, "quote_control/state.rs:92", 6069, Side::Zero, Side::Zero),
    ("remove_quote_mint", Kind::Thrown, "lib.rs:1975", 6069, Side::Zero, Side::Zero),
    ("sell", Kind::Thrown, "lib.rs:1879", 6062, Side::Zero, Side::Zero),
    ("sell_v3", Kind::Thrown, "trade_v3.rs:172", 6010, Side::OwnerOf("buyback_fee_recipient"), Side::Token),
    ("set_creator", Kind::Account, "bonding_curve", 2006, Side::Slot("bonding_curve"), Side::Derived),
    ("set_creator", Kind::Account, "global", 6000, Side::StoredSetCreatorAuthority, Side::Slot("set_creator_authority")),
    ("set_creator", Kind::Account, "metadata", 2006, Side::Slot("metadata"), Side::Derived),
    ("set_creator", Kind::Account, "metadata", 3007, Side::OwnerOf("metadata"), Side::MetaplexProgram),
    ("set_mayhem_virtual_params", Kind::Account, "sol_vault_authority", 2006, Side::Slot("sol_vault_authority"), Side::Derived),
    ("set_mayhem_virtual_params", Kind::Account, "token_program", 3008, Side::Slot("token_program"), Side::Token2022),
    ("set_metaplex_creator", Kind::Account, "bonding_curve", 2006, Side::Slot("bonding_curve"), Side::Derived),
    ("set_metaplex_creator", Kind::Account, "metadata", 2006, Side::Slot("metadata"), Side::Derived),
    ("set_metaplex_creator", Kind::Account, "metadata", 3007, Side::OwnerOf("metadata"), Side::MetaplexProgram),
    ("set_params", Kind::Account, "global", 6000, Side::StoredAuthority, Side::Slot("authority")),
    ("set_params", Kind::Thrown, "lib.rs:249", 6014, Side::Zero, Side::Zero),
    ("set_quote_control_admin", Kind::Account, "global", 6000, Side::StoredAuthority, Side::Slot("authority")),
    ("set_quote_control_admin", Kind::Account, "quote_control", 3007, Side::OwnerOf("quote_control"), Side::Pump),
    ("set_quote_control_mint_reserves", Kind::Account, "quote_control", 3007, Side::OwnerOf("quote_control"), Side::Pump),
    ("set_quote_control_reserves_admin", Kind::Account, "quote_control", 3007, Side::OwnerOf("quote_control"), Side::Pump),
    ("set_reserved_fee_recipients", Kind::Account, "global", 6000, Side::StoredAuthority, Side::Slot("authority")),
    ("set_reserved_fee_recipients", Kind::Thrown, "set_reserved_fee_recipients.rs:60", 6028, Side::Zero, Side::Zero),
    ("sweep_creator_fee", Kind::Thrown, "sweep_fees.rs:123", 6000, Side::Zero, Side::Zero),
    ("sweep_creator_fee", Kind::Thrown, "sweep_fees.rs:145", 2006, Side::Slot("recipient"), Side::Derived),
    ("sweep_protocol_fee", Kind::Thrown, "sweep_fees.rs:123", 6000, Side::Zero, Side::Zero),
    ("toggle_create_v2", Kind::Account, "event_authority", 2006, Side::Slot("event_authority"), Side::Derived),
    ("toggle_create_v2", Kind::Account, "global", 6000, Side::StoredAuthority, Side::Slot("authority")),
    ("update_global_authority", Kind::Account, "event_authority", 2006, Side::Slot("event_authority"), Side::Derived),
    ("update_global_authority", Kind::Account, "global", 6000, Side::StoredAuthority, Side::Slot("authority")),
];

/// The two side forms a site logs, when the site is in the table.
pub fn forms(handler: &str, kind: Kind, place: &str, code: u64) -> Option<(Side, Side)> {
    PAIRS.iter()
        .find(|(h, k, p, c, _, _)| *h == handler && *k == kind && *p == place && *c == code)
        .map(|(_, _, _, _, left, right)| (*left, *right))
}

/// The logged block for a site and its two values, tab-joined as
/// `Left:` / left / `Right:` / right, when the site is in the table and every
/// constant side equals the value given.
pub fn block(handler: &str, kind: Kind, place: &str, code: u64, left: &str, right: &str) -> Option<String> {
    let (want_left, want_right) = forms(handler, kind, place, code)?;
    for (side, value) in [(want_left, left), (want_right, right)] {
        if let Some(constant) = side.constant() {
            if constant != value {
                return None;
            }
        }
    }
    Some(format!("Left:\t{left}\tRight:\t{right}"))
}
