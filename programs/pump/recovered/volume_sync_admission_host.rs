//! Host driver for `volume_sync_admission.rs`, used by
//! `tests/test_volume_sync_admission_captured.py`. One request per line:
//! `route fault fault ...`, where `route` is `reset|idle` and a fault is
//! `<slot>.<kind>`. Answers are `error:<code>`, `error:missing_account`, or
//! `ok,<events>,<total claimed tokens>`.
#[path = "volume_sync_admission.rs"]
mod volume_sync_admission;

use std::io::{self, BufRead, Write};
use volume_sync_admission::{admit, Load, Request};

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

fn answer(line: &str) -> String {
    let mut words = line.split_whitespace();
    let reset = words.next().unwrap() == "reset";
    let mut r = Request::default();
    let mut program_wrong = false;
    for word in words {
        let (slot, kind) = word.split_once('.').unwrap();
        match (slot, kind) {
            ("user", _) => r.user_wrong_address = true,
            ("global_volume_accumulator", "key") => r.global_wrong_address = true,
            ("global_volume_accumulator", k) => load(&mut r.global, k),
            ("user_volume_accumulator", "key") => r.user_accumulator_wrong_address = true,
            ("user_volume_accumulator", "readonly") => r.user_accumulator_read_only = true,
            ("user_volume_accumulator", k) => load(&mut r.user_accumulator, k),
            ("event_authority", _) => r.event_authority_wrong = true,
            ("program", _) => program_wrong = true,
            other => panic!("unknown fault {other:?}"),
        }
    }
    match admit(&r) {
        Err(c) => format!("error:{c}"),
        Ok(()) if !reset => "ok,0,50".to_string(),
        Ok(()) if program_wrong => "error:missing_account".to_string(),
        Ok(()) => "ok,1,0".to_string(),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
