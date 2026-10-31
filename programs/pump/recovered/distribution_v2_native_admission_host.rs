//! Host driver for `distribution_v2_native_admission.rs` and
//! `creator_fee_distribution.rs`, used by
//! `tests/test_distribution_v2_native_admission_captured.py`. One request per line:
//! `native fault fault ...`, where a fault is `<slot>.<kind>`. Answers are
//! `error:<code>`, `error:<name>`, or `ok,<lamports paid>,<events>`.
#[allow(dead_code)]
#[path = "creator_fee_distribution.rs"]
mod creator_fee_distribution;
#[path = "distribution_v2_native_admission.rs"]
mod distribution_v2_native_admission;

use creator_fee_distribution::{amounts, Distribution, Shareholder, Slot};
use distribution_v2_native_admission::{admit, vault_transfer, Load, NativeVault, Request, Stop, TokenProgramSlot};
use std::io::{self, BufRead, Write};

const ZERO_RENT: u64 = 890_880;

fn load(slot: &mut Load, kind: &str) {
    // The owner is checked first; a later data fault does not hide it.
    match kind {
        "missing" => *slot = Load::Missing,
        "owner" => *slot = Load::WrongOwner,
        _ if *slot == Load::WrongOwner => {}
        "short" => *slot = Load::Short,
        "disc" => *slot = Load::BadDiscriminator,
        "trunc" if *slot == Load::Stored => *slot = Load::Truncated,
        "trunc" => {} // keeps the data fault before it
        other => panic!("unknown load fault {other}"),
    }
}

fn stop(s: Stop) -> String {
    match s {
        Stop::Code(c) => format!("error:{c}"),
        Stop::InvalidAccountData => "error:invalid_account_data".to_string(),
        Stop::InvalidArgument => "error:invalid_argument".to_string(),
        Stop::ExternalLamportSpend => "error:external_lamport_spend".to_string(),
    }
}

fn answer(line: &str) -> String {
    let mut r = Request::default();
    let mut vault = NativeVault::default();
    let mut vault_lamports = ZERO_RENT + 1_000_000_000;
    let (mut active, mut creator_fee, mut slots) = (true, 0, true);
    let (mut mint_other, mut curve_quote) = (false, false);
    for word in line.split_whitespace().skip(1) {
        let (slot, kind) = word.split_once('.').unwrap();
        match (slot, kind) {
            ("payer", "unsigned") => r.payer_unsigned = true,
            ("payer", _) => r.payer_read_only = true,
            ("mint", "key") => r.mint_wrong_address = true,
            ("mint", k) => load(&mut r.mint, k),
            ("bonding_curve", "key") => r.curve_wrong_address = true,
            ("bonding_curve", k) => load(&mut r.curve, k),
            ("sharing_config", "key") => r.creator_mismatch = true,
            ("sharing_config", "matched") => r.config_wrong_address = true,
            ("sharing_config", k) => load(&mut r.config, k),
            ("creator_vault", "key") => r.vault.wrong_address = true,
            ("creator_vault", "readonly") => r.vault.read_only = true,
            ("creator_vault", "owner") => vault.foreign_owner = true,
            ("creator_vault", "data") => vault.has_data = true,
            ("creator_vault", _) => {
                vault = NativeVault::default(); // the slot's last fault wins
                vault_lamports = 0;
            }
            ("system_program", _) => r.system_program_wrong = true,
            ("event_authority", _) => r.event_authority_wrong = true,
            ("program", _) => r.program_wrong = true,
            ("creator_vault_quote_token_account", "key") => r.vault_token.wrong_address = true,
            ("creator_vault_quote_token_account", "readonly") => r.vault_token.read_only = true,
            ("creator_vault_quote_token_account", _) => {} // nothing reads it
            ("quote_mint", "key") => r.quote_mint_seed_mismatch = true,
            ("quote_mint", "other") => {
                r.quote_mint_seed_mismatch = false; // the slot's last fault wins
                mint_other = true;
            }
            ("quote_mint", k) => load(&mut r.quote_mint, k),
            ("quote_token_program", "key") => r.token_program = TokenProgramSlot::Invalid,
            ("quote_token_program", _) => r.token_program = TokenProgramSlot::OtherInterface,
            ("associated_token_program", _) => r.associated_program_wrong = true,
            ("h", "inactive") => active = false,
            ("h", "unswept") => creator_fee = 1,
            ("h", "creator") => r.creator_mismatch = true,
            ("h", "configmint") => r.config_mint_mismatch = true,
            ("h", "noslots") => slots = false,
            ("h", "quote") => curve_quote = true,
            other => panic!("unknown fault {other:?}"),
        }
    }
    // This fault rewrites the curve's creator, over any other fault of it.
    r.creator_mismatch &= !r.config_wrong_address;
    r.quote_mint_not_curves = mint_other != curve_quote;
    if let Err(s) = admit(&r) {
        return stop(s);
    }
    if !active {
        return "error:6051".to_string();
    }
    if creator_fee != 0 {
        return "error:6095".to_string();
    }
    if curve_quote {
        // The curve's own mint: the quote route, which reads the vault's token account.
        return stop(Stop::InvalidAccountData);
    }
    let share = |bps| Shareholder {
        bps,
        slot: slots.then_some(Slot::Holder { lamports: 1_000_000_000, data_len: 0 }),
    };
    let d = Distribution {
        vault_lamports,
        shareholders: vec![share(5000), share(3000), share(2000)],
        active,
        creator_fee,
        curve_creator_is_config: true,
        curve_has_quote_mint: false,
        config_mint_matches: true,
    };
    match amounts(&d) {
        Err(c) => format!("error:{c}"),
        Ok(a) if a.available < a.minimum_distributable => "ok,0,1".to_string(),
        Ok(a) => match vault_transfer(&vault) {
            Err(s) => stop(s),
            Ok(()) => format!("ok,{},1", a.transfers.iter().sum::<u64>()),
        },
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
