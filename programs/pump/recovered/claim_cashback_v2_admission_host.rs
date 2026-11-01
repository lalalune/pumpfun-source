//! Host driver for `claim_cashback_v2_admission.rs`, used by
//! `tests/test_claim_cashback_v2_admission_captured.py`. One request per line:
//! `route fault fault ...`, where `route` is `native|token` and a fault is
//! `<slot>.<kind>`. Answers are `error:<code>`, `error:<name>`, or
//! `ok,<lamports>,<tokens>,<events>`.
#[path = "claim_cashback_v2_admission.rs"]
mod claim_cashback_v2_admission;

use claim_cashback_v2_admission::{admit, token_route, AccumulatorLoad, MintState, Request, Route, Stop, TokenState};
use std::io::{self, BufRead, Write};

const LAMPORTS: u64 = 1_000_000;
const TOKENS: u64 = 500_000;

fn state(token: &mut TokenState, kind: &str) {
    match kind {
        "owner" => token.foreign_owner = true,
        "short" => token.short = true,
        "missing" => token.missing = true,
        "mintdata" => token.wrong_mint = true,
        "ownerdata" => token.wrong_authority = true,
        "frozen" => token.frozen = true,
        other => panic!("unknown token fault {other}"),
    }
}

fn stop(s: Stop) -> String {
    match s {
        Stop::Code(c) => format!("error:{c}"),
        Stop::InvalidAccountData => "error:invalid_account_data".to_string(),
        Stop::ExternalDataModified => "error:external_data_modified".to_string(),
    }
}

fn valid_fault(slot: &str, kind: &str) -> bool {
    match slot {
        "user" => matches!(kind, "readonly"),
        "user_volume_accumulator" => matches!(kind, "key" | "readonly" | "owner" | "short" | "disc" | "trunc" | "missing"),
        "quote_mint" => matches!(kind, "key" | "short" | "missing"),
        "quote_token_program" => matches!(kind, "key" | "program"),
        "associated_token_program" => matches!(kind, "key"),
        "associated_user_volume_accumulator" => matches!(kind, "key" | "readonly" | "owner" | "short" | "mintdata" | "ownerdata" | "frozen" | "missing"),
        "associated_quote_user" => matches!(kind, "key" | "readonly" | "owner" | "short" | "mintdata" | "ownerdata" | "frozen" | "missing"),
        "system_program" => matches!(kind, "key"),
        "event_authority" => matches!(kind, "key"),
        "program" => matches!(kind, "key" | "token"),
        "h" => matches!(kind, "empty"),
        _ => false,
    }
}

fn answer(line: &str) -> String {
    let mut words = line.split_whitespace();
    let token = match words.next() {
        Some("native") => false,
        Some("token") => true,
        other => panic!("unsupported route {other:?}"),
    };
    let mut r = Request::default();
    let mut mint = MintState::default();
    let mut source = TokenState::default();
    let mut destination = TokenState::default();
    let mut empty = false;
    for word in words {
        let (slot, kind) = word.split_once('.').expect("fault must be slot.kind");
        assert!(valid_fault(slot, kind), "unsupported fault {word}");
        match (slot, kind) {
            ("user", _) => r.user_read_only = true,
            ("user_volume_accumulator", "key") => r.accumulator.wrong_address = true,
            ("user_volume_accumulator", "readonly") => r.accumulator.read_only = true,
            // Data and owner mutations cannot recreate a removed account.
            ("user_volume_accumulator", _) if r.accumulator_load == AccumulatorLoad::Missing => {}
            // The owner is checked first; a later data fault does not hide it.
            ("user_volume_accumulator", "owner") => r.accumulator_load = AccumulatorLoad::WrongOwner,
            ("user_volume_accumulator", _) if r.accumulator_load == AccumulatorLoad::WrongOwner && kind != "missing" => {}
            ("user_volume_accumulator", "short") => r.accumulator_load = AccumulatorLoad::Short,
            ("user_volume_accumulator", "disc") => r.accumulator_load = AccumulatorLoad::BadDiscriminator,
            ("user_volume_accumulator", "trunc") if r.accumulator_load == AccumulatorLoad::default() => {
                r.accumulator_load = AccumulatorLoad::Truncated
            }
            ("user_volume_accumulator", "trunc") => {} // keeps the data fault before it
            ("user_volume_accumulator", "missing") => r.accumulator_load = AccumulatorLoad::Missing,
            ("quote_mint", "key") => r.mint_wrong_address = true,
            ("quote_mint", "short") if mint != MintState::Missing => mint = MintState::Short,
            ("quote_mint", "short") => {}
            ("quote_mint", "missing") => mint = MintState::Missing,
            ("quote_token_program", _) => r.token_program_wrong = true,
            ("associated_token_program", _) => r.associated_program_wrong = true,
            ("associated_user_volume_accumulator", "key") => r.accumulator_token.wrong_address = true,
            ("associated_user_volume_accumulator", "readonly") => r.accumulator_token.read_only = true,
            ("associated_user_volume_accumulator", k) => state(&mut source, k),
            ("associated_quote_user", "key") => {} // no address check
            ("associated_quote_user", "readonly") => r.user_token_read_only = true,
            ("associated_quote_user", k) => state(&mut destination, k),
            ("system_program", _) => r.system_program_wrong = true,
            ("event_authority", _) => r.event_authority_wrong = true,
            ("program", _) => r.program_wrong = true,
            ("h", "empty") => empty = true,
            other => panic!("unknown fault {other:?}"),
        }
    }
    if let Err(s) = admit(&r) {
        return stop(s);
    }
    if !token {
        let moved = if empty { 0 } else { LAMPORTS };
        return format!("ok,{moved},0,{}", u8::from(moved > 0));
    }
    match token_route(mint, &source, &destination, empty) {
        Route::Empty => "ok,0,0,0".to_string(),
        Route::Transfer => format!("ok,0,{TOKENS},1"),
        Route::Stop(s) => stop(s),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
