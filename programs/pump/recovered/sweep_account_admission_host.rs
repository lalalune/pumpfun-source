//! Host driver for `sweep_account_admission.rs` and `sweep_fees.rs`, used by
//! `tests/test_sweep_account_admission_captured.py`. One request per line:
//! `route fault fault ...`, where `route` is `<protocol|creator>_<native|token>`
//! and a fault is `<slot>.<kind>`. Answers are `error:<code>`, `error:<name>`,
//! or `ok,<lamports>,<tokens>,<events>`.
#[path = "sweep_account_admission.rs"]
mod sweep_account_admission;
#[allow(dead_code)]
#[path = "sweep_fees.rs"]
mod sweep_fees;

use std::io::{self, BufRead, Write};
use sweep_account_admission::{admit, token_route, Load, Request, Stop, TokenProgramSlot, TokenState};
use sweep_fees::{sweep, Bucket, QuoteMint, Recipient, Sweep};

fn load(slot: &mut Load, kind: &str) {
    // The owner is checked first; a later data fault does not hide it.
    match kind {
        "missing" => *slot = Load::Missing,
        "owner" => *slot = Load::WrongOwner,
        _ if *slot == Load::WrongOwner => {}
        "short" => *slot = Load::Short,
        "disc" => *slot = Load::BadDiscriminator,
        other => panic!("unknown load fault {other}"),
    }
}

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
    }
}

fn answer(line: &str) -> String {
    let mut words = line.split_whitespace();
    let (bucket, kind) = words.next().unwrap().split_once('_').unwrap();
    let creator = bucket == "creator";
    let native = kind == "native";
    let mut r = Request::default();
    let (mut source, mut destination) = (TokenState::default(), TokenState::default());
    let (mut empty, mut stranger, mut program_wrong) = (false, false, false);
    for word in words {
        let (slot, kind) = word.split_once('.').unwrap();
        match (slot, kind) {
            ("payer", "unsigned") => r.payer_unsigned = true,
            ("payer", _) => r.payer_read_only = true,
            ("global", "key") => r.global_wrong_address = true,
            ("global", k) => load(&mut r.global, k),
            ("base_mint", "key") => r.base_mint_wrong_address = true,
            ("base_mint", k) => load(&mut r.base_mint, k),
            ("quote_mint", "key" | "other") => r.quote_mint_wrong = true,
            ("quote_mint", k) => load(&mut r.quote_mint, k),
            ("quote_token_program", "key") => r.token_program = TokenProgramSlot::Invalid,
            ("quote_token_program", _) => r.token_program = TokenProgramSlot::OtherInterface,
            ("associated_token_program", _) => r.associated_program_wrong = true,
            ("system_program", _) => r.system_program_wrong = true,
            ("bonding_curve", "key") => r.curve_slot.wrong_address = true,
            ("bonding_curve", "readonly") => r.curve_slot.read_only = true,
            ("bonding_curve", k) => load(&mut r.curve, k),
            ("associated_quote_bonding_curve", "key") => r.curve_token.wrong_address = true,
            ("associated_quote_bonding_curve", "readonly") => r.curve_token.read_only = true,
            ("associated_quote_bonding_curve", k) => state(&mut source, k),
            ("recipient", "readonly") => r.recipient_read_only = true,
            ("recipient", _) => stranger = true,
            ("associated_quote_recipient", "key") => r.recipient_token.wrong_address = true,
            ("associated_quote_recipient", "readonly") => r.recipient_token.read_only = true,
            ("associated_quote_recipient", k) => state(&mut destination, k),
            ("event_authority", _) => r.event_authority_wrong = true,
            ("program", _) => program_wrong = true,
            ("h", "empty") => empty = true,
            other => panic!("unknown fault {other:?}"),
        }
    }
    if let Err(s) = admit(&r) {
        return stop(s);
    }
    let (creator_fee, protocol_fees) = match (empty, creator) {
        (true, true) => (0, 7_000_000),
        (true, false) => (3_000_000, 0),
        _ => (3_000_000, 7_000_000),
    };
    let real_quote_reserves = 5_000_000_000;
    let recipient = match (stranger, creator) {
        (true, _) => Recipient::Other,
        (_, true) => Recipient::CreatorVault,
        _ => Recipient::FeeRecipient,
    };
    let reserved = if native { real_quote_reserves + creator_fee + protocol_fees } else { 0 };
    let swept = sweep(&Sweep {
        bucket: if creator { Bucket::Creator } else { Bucket::Protocol },
        native,
        mayhem: false,
        quote_mint: if native { QuoteMint::Native } else { QuoteMint::CurveQuote },
        real_quote_reserves,
        creator_fee,
        protocol_fees,
        curve_lamports: reserved + sweep_fees::CURVE_RENT_MINIMUM,
        recipient,
        recipient_lamports: 1_000_000_000,
        curve_quote_ata: Some(10_000_000_000),
        recipient_quote_ata_exists: true,
    });
    let moved = match swept {
        Ok(moved) => moved,
        Err(sweep_fees::Stop::Code(c)) => return format!("error:{c}"),
        Err(other) => panic!("no such stop in these inputs: {other:?}"),
    };
    if moved.amount == 0 {
        return "ok,0,0,0".to_string();
    }
    if !native {
        if let Err(s) = token_route(&source, &destination) {
            return stop(s);
        }
    }
    if program_wrong {
        return "error:missing_account".to_string();
    }
    if native {
        format!("ok,{},0,1", moved.amount)
    } else {
        format!("ok,0,{},1", moved.amount)
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
