//! Host driver for `account_lifecycle_admission.rs` and `account_lifecycle.rs`,
//! used by `tests/test_account_lifecycle_admission_captured.py`. One request per
//! line: `create|init|close|extend fault fault ...`, where a fault is
//! `<slot>.<kind>`. Answers are `error:<code>`, `error:<name>`, or
//! `ok,<events>,<subject lamports>,<subject length>`.
#[allow(dead_code)]
#[path = "account_lifecycle.rs"]
mod account_lifecycle;
#[path = "account_lifecycle_admission.rs"]
mod admission;

use account_lifecycle::{close, extend, init, rent, Holder, Kind, UVA_LEN};
use admission::{
    admit_close, admit_create, admit_existing, admit_extend, after_create, CloseRequest, ExtendRequest, Fresh,
    InitRequest, Load, Stop,
};
use std::io::{self, BufRead, Write};

const UVA_RENT: u64 = (128 + 137) * 6_960;

fn stop(s: Stop) -> String {
    match s {
        Stop::Code(c) => format!("error:{c}"),
        Stop::PrivilegeEscalation => "error:privilege_escalation".to_string(),
    }
}

fn lifecycle(s: account_lifecycle::Stop) -> String {
    match s {
        account_lifecycle::Stop::Code(c) => format!("error:{c}"),
        account_lifecycle::Stop::BelowRent => "error:rent".to_string(),
    }
}

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

fn program_fault(words: &[&str]) -> bool {
    words.iter().any(|w| w.starts_with("program."))
}

fn answer_init(words: &[&str], existing: bool) -> String {
    let mut r = InitRequest::default();
    let (mut fresh, mut poor) = (Fresh::Absent, false);
    let (mut stored, mut oversized, mut below_rent) = (Load::Stored, false, false);
    for word in words {
        let (slot, kind) = word.split_once('.').unwrap();
        match (slot, kind) {
            ("payer", "unsigned") => r.payer_unsigned = true,
            ("payer", "readonly") => r.payer_read_only = true,
            ("payer", _) => poor = true,
            ("user", _) => r.seeds_wrong = true,
            ("user_volume_accumulator", "key") => r.seeds_wrong = true,
            ("user_volume_accumulator", "readonly") => r.accumulator_read_only = true,
            ("user_volume_accumulator", "owner") if !existing => fresh = Fresh::ForeignOwner,
            ("user_volume_accumulator", "sysdata") => fresh = Fresh::SystemData,
            ("user_volume_accumulator", "funded") => fresh = Fresh::Funded,
            // Padded to 138 bytes: short bytes then read as a bad discriminator.
            ("user_volume_accumulator", "long") => match stored {
                Load::Short => stored = Load::BadDiscriminator,
                Load::Truncated => {
                    stored = Load::Stored;
                    oversized = true;
                }
                _ => oversized = true,
            },
            ("user_volume_accumulator", "poorrent") => below_rent = true,
            ("user_volume_accumulator", k) => load(&mut stored, k),
            ("system_program", _) => r.system_program_wrong = true,
            ("event_authority", _) => r.event_authority_wrong = true,
            ("program", _) => {}
            other => panic!("unknown fault {other:?}"),
        }
    }
    if existing {
        return match admit_existing(&r, stored, oversized, below_rent) {
            Err(s) => stop(s),
            Ok(()) if program_fault(words) => "error:missing_account".to_string(),
            Ok(()) => format!("ok,1,{UVA_RENT},137"),
        };
    }
    if let Err(s) = admit_create(&r, fresh) {
        return stop(s);
    }
    let (holder, lamports) = if fresh == Fresh::Funded { (Holder::SystemEmpty, 10_000_000) } else { (Holder::Missing, 0) };
    let payer = if poor { 1000 } else { 1_000_000_000_000 };
    match init(holder, lamports, payer) {
        Err(s) => lifecycle(s),
        Ok(done) => match after_create(&r) {
            Err(s) => stop(s),
            Ok(()) if program_fault(words) => "error:missing_account".to_string(),
            Ok(()) => format!("ok,1,{},{UVA_LEN}", lamports + done.payer_paid),
        },
    }
}

fn answer_close(words: &[&str]) -> String {
    let mut r = CloseRequest::default();
    for word in words {
        let (slot, kind) = word.split_once('.').unwrap();
        match (slot, kind) {
            ("user", "unsigned") => r.user_unsigned = true,
            ("user", _) => r.user_read_only = true,
            ("user_volume_accumulator", "key") => r.accumulator_wrong_address = true,
            ("user_volume_accumulator", "readonly") => r.accumulator_read_only = true,
            ("user_volume_accumulator", k) => load(&mut r.accumulator, k),
            ("event_authority", _) => r.event_authority_wrong = true,
            ("program", _) => {}
            other => panic!("unknown fault {other:?}"),
        }
    }
    if let Err(s) = admit_close(&r) {
        return stop(s);
    }
    if program_fault(words) {
        return "error:missing_account".to_string();
    }
    match close(Holder::Pump { len: UVA_LEN, disc_ok: true }, rent(UVA_LEN), true) {
        Err(s) => lifecycle(s),
        Ok(_) => "ok,1,0,0".to_string(),
    }
}

fn answer_extend(words: &[&str]) -> String {
    let mut r = ExtendRequest::default();
    let (mut kind_read, mut len, mut lamports, mut user) = (Kind::BondingCurve, 81, 1_000_000_000, 1_000_000_000);
    for word in words {
        let (slot, kind) = word.split_once('.').unwrap();
        match (slot, kind) {
            ("account", "readonly") => r.account_read_only = true,
            ("account", "owner" | "missing") => r.account_not_owned = true,
            ("account", "unknown") => kind_read = Kind::Other,
            ("account", "short") => len = 4,
            ("account", _) => lamports = 1,
            ("user", "unsigned") => r.user_unsigned = true,
            ("user", "readonly") => r.user_read_only = true,
            ("user", _) => user = 1000,
            ("system_program", _) => r.system_program_wrong = true,
            ("event_authority", _) => r.event_authority_wrong = true,
            ("program", _) => {}
            other => panic!("unknown fault {other:?}"),
        }
    }
    if let Err(s) = admit_extend(&r) {
        return stop(s);
    }
    match extend(true, true, kind_read, len, lamports, user) {
        Err(s) => lifecycle(s),
        Ok(_) if program_fault(words) => "error:missing_account".to_string(),
        Ok(done) => format!("ok,1,{},{}", lamports + done.user_paid, done.new_len),
    }
}

fn answer(line: &str) -> String {
    let words: Vec<&str> = line.split_whitespace().collect();
    match words[0] {
        "create" => answer_init(&words[1..], false),
        "init" => answer_init(&words[1..], true),
        "close" => answer_close(&words[1..]),
        _ => answer_extend(&words[1..]),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
