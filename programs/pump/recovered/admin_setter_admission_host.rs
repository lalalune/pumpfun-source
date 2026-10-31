//! Host driver for `admin_setter_admission.rs`, used by
//! `tests/test_admin_setter_admission_captured.py`. One request per line:
//! `<setter> fault fault ...`, where a fault is `<slot>.<kind>`. Answers are
//! `error:<code>`, `error:missing_account`, or
//! `ok,<events>,<first changed byte of Global>,<last changed byte>`.
#[path = "admin_setter_admission.rs"]
mod admin_setter_admission;

use admin_setter_admission::{admit, Load, Request, Stop};
use std::io::{self, BufRead, Write};

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

/// What a passing call on the test's arguments writes: events, first, last byte.
fn written(setter: &str) -> (u32, u32, u32) {
    match setter {
        "add_quote_mint" | "remove_quote_mint" => (0, 1013, 1044),
        "update_buyback_config" => (0, 997, 997),
        "set_max_curve_depth" => (0, 1087, 1087),
        "set_virtual_quote_reserves" => (0, 1005, 1005),
        "update_creator_fee_config" => (1, 1045, 1047),
        "update_holder_reward_config" => (0, 1054, 1086),
        "toggle_create_v2" => (0, 450, 450),
        "toggle_mayhem_mode" => (0, 515, 515),
        "toggle_cashback_enabled" => (0, 740, 740),
        "update_global_authority" => (1, 9, 40),
        other => panic!("unknown setter {other}"),
    }
}

fn answer(line: &str) -> String {
    let mut words = line.split_whitespace();
    let setter = words.next().unwrap();
    let (events, first, last) = written(setter);
    let takes_authority_mut = setter != "update_global_authority";
    let mut r = Request { authority_needs_mut: takes_authority_mut, emits_event: events == 1, ..Request::default() };
    for word in words {
        let (slot, kind) = word.split_once('.').unwrap();
        match (slot, kind) {
            ("global", "key") => r.global_wrong_address = true,
            ("global", "readonly") => r.global_read_only = true,
            ("global", "stored") => r.stored_authority_differs = true,
            ("global", k) => load(&mut r.global, k),
            ("authority", "unsigned") => r.authority_unsigned = true,
            ("authority", _) => r.authority_read_only = true,
            ("event_authority", "key") => r.event_authority_wrong = true,
            ("program", "key" | "token") => r.program_wrong = true,
            (_, "dropped") => r.account_dropped = true,
            ("h", _) => r.short_arguments = takes_authority_mut,
            other => panic!("unknown fault {other:?}"),
        }
    }
    match admit(&r) {
        Err(Stop::Code(c)) => format!("error:{c}"),
        Err(Stop::MissingAccount) => "error:missing_account".to_string(),
        Ok(()) => format!("ok,{events},{first},{last}"),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
