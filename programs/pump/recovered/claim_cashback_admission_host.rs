//! Host driver for `claim_cashback_admission.rs` and `claim_cashback.rs`, used by
//! `tests/test_claim_cashback_admission_captured.py`. One request per line:
//! `claim|empty fault fault ...`, where a fault is `<slot>.<kind>`. Answers are
//! `error:<code>` or `ok,<events>,<lamports the user received>`.
#[allow(dead_code)]
#[path = "claim_cashback.rs"]
mod claim_cashback;
#[path = "claim_cashback_admission.rs"]
mod claim_cashback_admission;

use claim_cashback::{claim, Claim, LAMPORTS_PER_BYTE, UVA_DISC};
use claim_cashback_admission::{admit, Load, Request};
use std::io::{self, BufRead, Write};

fn load(slot: &mut Load, kind: &str) {
    // The owner is checked first; a later data fault does not hide it.
    match kind {
        "missing" => *slot = Load::Missing,
        "owner" => *slot = Load::WrongOwner,
        _ if *slot == Load::WrongOwner => {}
        "short" => *slot = Load::Short,
        "disc" => *slot = Load::BadDiscriminator,
        "trunc" | "badbool" if *slot == Load::Stored => *slot = Load::Undecodable,
        "trunc" | "badbool" => {} // keeps the data fault before it
        other => panic!("unknown load fault {other}"),
    }
}

fn answer(line: &str) -> String {
    let mut words = line.split_whitespace();
    let extra = if words.next() == Some("claim") { 1_000_000 } else { 0 };
    let mut r = Request::default();
    for word in words {
        let (slot, kind) = word.split_once('.').unwrap();
        match (slot, kind) {
            ("user", "key") => r.seeds_wrong = true,
            ("user", "readonly") => r.user_read_only = true,
            ("user", _) => {} // an absent user is credited all the same
            ("user_volume_accumulator", "key") => r.seeds_wrong = true,
            ("user_volume_accumulator", "readonly") => r.accumulator_read_only = true,
            ("user_volume_accumulator", k) => load(&mut r.accumulator, k),
            ("system_program", _) => r.system_program_wrong = true,
            ("event_authority", _) => r.event_authority_wrong = true,
            ("program", _) => r.program_wrong = true,
            other => panic!("unknown fault {other:?}"),
        }
    }
    if let Err(c) = admit(&r) {
        return format!("error:{c}");
    }
    let mut data = vec![0; 137];
    data[..8].copy_from_slice(&UVA_DISC);
    let c = Claim {
        user: [0; 32],
        user_writable: true,
        uva_lamports: (128 + 137) * LAMPORTS_PER_BYTE + extra,
        uva_owned_by_pump: true,
        uva_is_user_pda: true,
        uva_writable: true,
        uva_data: &data,
    };
    match claim(&c, 0) {
        Err(c) => format!("error:{c}"),
        Ok(done) => format!("ok,{},{}", done.event.is_some() as u8, done.amount),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
