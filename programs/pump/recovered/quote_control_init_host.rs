//! Host driver for `quote_control_init.rs`, used by
//! `tests/test_quote_control_init_captured.py`. One request per line: a list of
//! `<slot>.<kind>` faults, or `-` for the plain call. Answers are
//! `error:<code>`, `error:<runtime name>`, or `ok,<paid>,<account lamports>`.
#[path = "quote_control_init.rs"]
mod quote_control_init;

use quote_control_init::{initialize, rent, Key, Meta, Request, Stop, Stored, INIT_LEN};
use std::io::{self, BufRead, Write};

const FUNDED: u64 = 10_000_000_000;
const SMALL: u64 = 1_000;

fn stored(lamports: u64, has_data: bool, system_owned: bool) -> Stored {
    Stored { lamports, has_data, system_owned }
}

fn answer(line: &str) -> String {
    let needed = rent(INIT_LEN);
    let mut control_key = Key::QuoteControl;
    let mut user_key = Key::User;
    let mut system_key = Key::System;
    let mut control = stored(0, false, true);
    let mut user = stored(FUNDED, false, true);
    let (mut control_ro, mut control_dropped, mut control_signed) = (false, false, false);
    let (mut user_ro, mut user_dropped, mut user_signed) = (false, false, true);
    let (mut system_dropped, mut extra) = (false, false);
    for word in line.split_whitespace().filter(|w| *w != "-") {
        // A later fault on the same slot replaces the stored shape.
        match word {
            "quote_control.key" => control_key = Key::Other(1),
            "quote_control.readonly" => control_ro = true,
            "quote_control.signed" => control_signed = true,
            "quote_control.funded" => control = stored(needed, false, true),
            "quote_control.richer" => control = stored(needed + 1, false, true),
            "quote_control.one_short" => control = stored(needed - 1, false, true),
            "quote_control.partial" => control = stored(SMALL, false, true),
            "quote_control.spaced" => control = stored(needed, true, true),
            "quote_control.spaced_partial" => control = stored(SMALL, true, true),
            "quote_control.pump" => control = stored(needed, true, false),
            "quote_control.foreign" => control = stored(needed, true, false),
            "quote_control.foreign_empty" => control = stored(needed, false, false),
            "quote_control.foreign_partial" => control = stored(SMALL, false, false),
            "quote_control.dropped" => control_dropped = true,
            "user.unsigned" => user_signed = false,
            "user.readonly" => user_ro = true,
            "user.absent" => user = stored(0, false, true),
            "user.poor" => user = stored(SMALL, false, true),
            "user.exact" => user = stored(needed, false, true),
            "user.exact_partial" => user = stored(needed - SMALL, false, true),
            "user.dust" => user = stored(needed + SMALL, false, true),
            "user.data" => user = stored(FUNDED, true, true),
            "user.poor_data" => user = stored(SMALL, true, true),
            "user.foreign" => user = stored(FUNDED, false, false),
            "user.foreign_poor" => user = stored(SMALL, false, false),
            "user.foreign_data" => user = stored(FUNDED, true, false),
            "user.self" => user_key = control_key,
            "user.dropped" => user_dropped = true,
            "system_program.key" => system_key = Key::Other(2),
            "system_program.token" => system_key = Key::Other(3),
            "system_program.dropped" => system_dropped = true,
            "h.trailing" => {}
            "h.extra" => extra = true,
            other => panic!("unknown fault {other}"),
        }
    }
    let mut accounts = Vec::new();
    if !control_dropped {
        accounts.push(Meta { key: control_key, signer: control_signed, writable: !control_ro });
    }
    if !user_dropped {
        accounts.push(Meta { key: user_key, signer: user_signed, writable: !user_ro });
    }
    if !system_dropped {
        accounts.push(Meta { key: system_key, signer: false, writable: false });
    }
    if extra {
        accounts.push(Meta { key: Key::Other(4), signer: false, writable: false });
    }
    // A transaction holds one set of flags per key.
    let merged = accounts.clone();
    for meta in &mut accounts {
        for other in merged.iter().filter(|m| m.key == meta.key) {
            meta.signer |= other.signer;
            meta.writable |= other.writable;
        }
    }
    let request = Request { accounts, control, user };
    match initialize(&request) {
        Ok(done) => format!("ok,{},{}", done.paid, done.lamports),
        Err(Stop::Code(code)) => format!("error:{code}"),
        Err(Stop::PrivilegeEscalation) => "error:privilege_escalation".to_string(),
        Err(Stop::InvalidArgument) => "error:invalid_argument".to_string(),
        Err(Stop::ExternalAccountLamportSpend) => "error:external_lamport_spend".to_string(),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
