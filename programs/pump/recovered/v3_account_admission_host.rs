//! Host driver for `v3_account_admission.rs`, used by
//! `tests/test_v3_account_admission_captured.py`. One request per line:
//! `handler route fault fault ...`, where `handler` is `sell|buy|exact`,
//! `route` is `native|token` and a fault is `<slot>.<kind>`. No faults is the
//! expected account set. Answers are `pass`, `transfer:<code>`, `error:<code>`
//! or `data` (`InvalidAccountData`).
#[path = "v3_account_admission.rs"]
mod v3_account_admission;

use std::io::{self, BufRead, Write};
use v3_account_admission::{admit, Accumulator, Gates, Handler, Outcome, ProgramSlot, Request, Slot, Stop};

fn mark(slot: &mut Slot, kind: &str) {
    match kind {
        "key" => slot.wrong_address = true,
        "owner" => slot.wrong_owner = true,
        "missing" => slot.missing = true,
        "disc" => slot.bad_discriminator = true,
        "short" => slot.short = true,
        "readonly" => slot.read_only = true,
        "mint" => slot.wrong_mint = true,
        "auth" => slot.wrong_authority = true,
        other => panic!("unknown fault {other}"),
    }
}

fn program(kind: &str) -> ProgramSlot {
    match kind {
        "t22" | "other" => ProgramSlot::OtherInterface,
        "moved" => ProgramSlot::OtherInterfaceMoved,
        _ => ProgramSlot::Invalid,
    }
}

fn request(line: &str) -> Request {
    let mut words = line.split_whitespace();
    let handler = match words.next().unwrap() {
        "sell" => Handler::Sell,
        "buy" => Handler::Buy,
        _ => Handler::BuyExactQuote,
    };
    let mut r = Request {
        handler,
        native: words.next().unwrap() == "native",
        global: Slot::default(),
        base_mint: Slot::default(),
        quote_mint: Slot::default(),
        base_token_program: ProgramSlot::default(),
        quote_token_program: ProgramSlot::default(),
        bonding_curve: Slot::default(),
        curve_base: Slot::default(),
        curve_quote: Slot::default(),
        user_unsigned: false,
        user_base: Slot::default(),
        user_quote: Slot::default(),
        accumulator: Slot::default(),
        accumulator_shape: Accumulator::default(),
        fee_config: Slot::default(),
        fee_config_shape: Default::default(),
        recipient: Slot::default(),
        recipient_shape: Default::default(),
        system_program_ok: true,
        event_authority_ok: true,
        program_ok: true,
        gates: Gates::default(),
    };
    for word in words {
        let (slot, kind) = word.split_once('.').unwrap();
        match (slot, kind) {
            ("global", k) => mark(&mut r.global, k),
            ("base_mint", k) => mark(&mut r.base_mint, k),
            ("quote_mint", k) => mark(&mut r.quote_mint, k),
            ("base_token_program", k) => r.base_token_program = program(k),
            ("quote_token_program", k) => r.quote_token_program = program(k),
            ("bonding_curve", k) => mark(&mut r.bonding_curve, k),
            ("associated_base_bonding_curve", k) => mark(&mut r.curve_base, k),
            ("associated_quote_bonding_curve", k) => mark(&mut r.curve_quote, k),
            ("user", _) => r.user_unsigned = true,
            ("associated_base_user", k) => mark(&mut r.user_base, k),
            ("associated_quote_user", k) => mark(&mut r.user_quote, k),
            ("user_volume_accumulator", k) => mark(&mut r.accumulator, k),
            ("uva", "absent" | "funded") => r.accumulator_shape = Accumulator::Absent,
            ("uva", "sysdata") => r.accumulator_shape = Accumulator::AbsentWithData,
            ("uva", "len8") => r.accumulator_shape = Accumulator::Truncated,
            ("uva", "len136") => r.accumulator_shape = Accumulator::WrongSize,
            ("uva", "short") => r.accumulator.short = true,
            ("uva", "user") => {} // the stored user field is never read
            ("fee_config", "bump") => r.fee_config_shape.wrong_bump = true,
            ("fee_config", "len100") => r.fee_config_shape.truncated = true,
            ("fee_config", k) => mark(&mut r.fee_config, k),
            ("buyback_fee_recipient", "unlisted") => r.recipient_shape.unlisted = true,
            ("buyback_fee_recipient", "zero") => r.recipient_shape.zero = true,
            ("buyback_fee_recipient", "listed") => {}
            ("buyback_fee_recipient", k) => mark(&mut r.recipient, k),
            ("system_program", _) => r.system_program_ok = false,
            ("event_authority", _) => r.event_authority_ok = false,
            ("program", _) => r.program_ok = false,
            ("h", "complete") => r.gates.complete = true,
            ("h", "cashback") => r.gates.cashback = true,
            ("h", "zero") => r.gates.zero_amount = true,
            ("h", "zero_quote") => r.gates.zero_quote = true,
            ("h", "over") => r.gates.over_amount = true,
            ("h", "overflow") => r.gates.reserve_overflow = true,
            other => panic!("unknown fault {other:?}"),
        }
    }
    r
}

fn answer(line: &str) -> String {
    match admit(&request(line)) {
        Outcome::Pass => "pass".to_string(),
        Outcome::Transfer(c) => format!("transfer:{c}"),
        Outcome::Stop(Stop::Code(c)) => format!("error:{c}"),
        Outcome::Stop(Stop::InvalidAccountData) => "data".to_string(),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
