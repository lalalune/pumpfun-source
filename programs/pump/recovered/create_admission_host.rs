//! Host driver for `create_admission.rs` and `legacy_create.rs`, used by
//! `tests/test_create_admission_captured.py`. One request per line:
//! `create fault fault ...`, where a fault is `<slot>.<kind>`. Answers are
//! `error:<code>`, `error:<name>`, or `ok,<events>,<virtual tokens>,<minted>`.
#[path = "create_admission.rs"]
mod create_admission;
#[allow(dead_code)]
#[path = "legacy_create.rs"]
mod legacy_create;

use create_admission::{admit, last_payment, Load, NewAccount, Request, Stop};
use legacy_create::{create, Create, Global};
use std::io::{self, BufRead, Write};

/// Taken and funded rewrite the same account: the slot's last fault wins.
fn new_account(a: &mut NewAccount, kind: &str) {
    match kind {
        "readonly" => a.read_only = true,
        "taken" => a.taken = true,
        "funded" => {
            a.taken = false;
            a.funded = true;
        }
        other => panic!("unknown init fault {other}"),
    }
}

fn load(slot: &mut Load, kind: &str) {
    // Data and owner mutations cannot recreate a removed account.
    if *slot == Load::Missing {
        return;
    }
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
        Stop::PrivilegeEscalation => "error:privilege_escalation".to_string(),
        Stop::MissingAccount => "error:missing_account".to_string(),
        Stop::IllegalOwner => "error:illegal_owner".to_string(),
    }
}

fn valid_fault(slot: &str, kind: &str) -> bool {
    match slot {
        "mint" => matches!(kind, "other" | "unsigned" | "readonly" | "taken" | "funded"),
        "mint_authority" => matches!(kind, "key"),
        "bonding_curve" => matches!(kind, "key" | "readonly" | "taken" | "funded"),
        "associated_bonding_curve" => matches!(kind, "key" | "readonly" | "taken" | "funded"),
        "global" => matches!(kind, "key" | "owner" | "short" | "disc" | "trunc" | "missing"),
        "mpl_token_metadata" => matches!(kind, "key"),
        "metadata" => matches!(kind, "key" | "readonly" | "taken" | "funded"),
        "user" => matches!(kind, "unsigned" | "readonly" | "poor"),
        "system_program" => matches!(kind, "key"),
        "token_program" => matches!(kind, "key" | "t22"),
        "associated_token_program" => matches!(kind, "key"),
        "rent" => matches!(kind, "key"),
        "event_authority" => matches!(kind, "key"),
        "program" => matches!(kind, "key" | "token"),
        "h" => matches!(kind, "badbool" | "creator" | "name"),
        _ => false,
    }
}

fn answer(line: &str) -> String {
    let mut r = Request::default();
    let (mut metadata_taken, mut no_event_program) = (false, false);
    let (mut name_bytes, mut creator_is_zero) = (4, false);
    let mut words = line.split_whitespace();
    assert_eq!(words.next(), Some("create"), "unsupported operation");
    for word in words {
        let (slot, kind) = word.split_once('.').expect("fault must be slot.kind");
        assert!(valid_fault(slot, kind), "unsupported fault {word}");
        match (slot, kind) {
            ("mint", "other") => r.mint_other = true,
            ("mint", "unsigned") => r.mint_unsigned = true,
            ("mint", k) => new_account(&mut r.mint, k),
            ("mint_authority", _) => r.mint_authority_wrong = true,
            ("bonding_curve", "key") => r.curve_wrong_address = true,
            ("bonding_curve", k) => new_account(&mut r.curve, k),
            ("associated_bonding_curve", "key") => r.curve_token_wrong_address = true,
            ("associated_bonding_curve", k) => new_account(&mut r.curve_token, k),
            ("global", "key") => r.global_wrong_address = true,
            ("global", k) => load(&mut r.global, k),
            ("mpl_token_metadata", _) => r.metadata_program_wrong = true,
            ("metadata", "key") => r.metadata_wrong_address = true,
            ("metadata", "readonly") => r.metadata_read_only = true,
            ("metadata", "taken") => metadata_taken = true,
            ("metadata", "funded") => metadata_taken = false,
            ("user", "unsigned") => r.user_unsigned = true,
            ("user", "readonly") => r.user_read_only = true,
            ("user", _) => r.user_poor = true,
            ("system_program", _) => r.system_program_wrong = true,
            ("token_program", _) => r.token_program_wrong = true,
            ("associated_token_program", _) => r.associated_program_wrong = true,
            ("rent", _) => r.rent_wrong = true,
            ("event_authority", _) => r.event_authority_wrong = true,
            ("program", _) => no_event_program = true,
            ("h", "badbool") => r.global_invalid_bool = true,
            ("h", "creator") => creator_is_zero = true,
            ("h", "name") => name_bytes = 33,
            other => panic!("unknown fault {other:?}"),
        }
    }
    if let Err(s) = admit(&r) {
        return stop(s);
    }
    let run = |name_bytes, creator_is_zero| {
        create(&Create {
            faults: vec![],
            name_bytes,
            symbol_bytes: 2,
            uri_bytes: 9,
            creator_is_zero,
            global: Global {
                initial_virtual_token_reserves: 1_073_000_000_000_000,
                initial_virtual_sol_reserves: 30_000_000_000,
                initial_real_token_reserves: 793_100_000_000_000,
                token_total_supply: 1_000_000_000_000_000,
            },
        })
    };
    // The creator check runs first, and the existing metadata account stops the
    // metadata CPI before it reads the strings.
    if let Err(c) = run(4, creator_is_zero) {
        return format!("error:{c}");
    }
    if metadata_taken {
        return "error:199".to_string();
    }
    match run(name_bytes, false) {
        Err(c) => format!("error:{c}"),
        Ok(_) if last_payment(&r).is_err() => stop(last_payment(&r).unwrap_err()),
        Ok(_) if no_event_program => "error:missing_account".to_string(),
        Ok(curve) => format!("ok,1,{},{}", curve.virtual_token_reserves, curve.minted),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
