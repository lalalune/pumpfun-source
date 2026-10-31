//! Host driver for `v2_account_admission.rs`, used by
//! `tests/test_v2_account_admission_captured.py`. One request per line:
//! `handler route fault fault ...`, where `handler` is `sell|buy|exact`,
//! `route` is `native|token` and a fault is `<slot>.<kind>`. No faults is the
//! expected account set. Answers are `pass`, `transfer:<code>`, `system`,
//! `error:<code>` or `data` (`InvalidAccountData`).
#[path = "v2_account_admission.rs"]
mod v2_account_admission;

use std::io::{self, BufRead, Write};
use v2_account_admission::{admit, Accumulator, Gates, Handler, Outcome, Payee, ProgramSlot, Request, Slot, Stop};

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
    let empty = Slot::default();
    let mut r = Request {
        handler,
        native: words.next().unwrap() == "native",
        global: empty,
        base_mint: empty,
        quote_mint: empty,
        native_other_mint: false,
        base_token_program: ProgramSlot::default(),
        quote_token_program: ProgramSlot::default(),
        associated_token_program_ok: true,
        fee_recipient: empty,
        fee_payee: Payee::default(),
        fee_quote: empty,
        buyback: empty,
        buyback_payee: Payee::default(),
        buyback_quote: empty,
        bonding_curve: empty,
        curve_base: empty,
        curve_quote: empty,
        user_unsigned: false,
        user_base: empty,
        user_quote: empty,
        creator_vault: empty,
        vault_quote: empty,
        sharing_config: empty,
        global_volume: empty,
        accumulator: empty,
        accumulator_shape: Accumulator::default(),
        accumulator_quote: empty,
        fee_config: empty,
        fee_config_wrong_bump: false,
        whitelisted: false,
        fee_config_truncated: false,
        fee_program_ok: true,
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
            ("quote_mint", "native_other") => r.native_other_mint = true,
            ("quote_mint", k) => mark(&mut r.quote_mint, k),
            ("base_token_program", k) => r.base_token_program = program(k),
            ("quote_token_program", k) => r.quote_token_program = program(k),
            ("associated_token_program", _) => r.associated_token_program_ok = false,
            ("fee_recipient", "unlisted") => r.fee_payee = Payee::Unlisted,
            ("fee_recipient", "zero") => r.fee_payee = Payee::Zero,
            ("fee_recipient", k) => mark(&mut r.fee_recipient, k),
            ("associated_quote_fee_recipient", k) => mark(&mut r.fee_quote, k),
            ("buyback_fee_recipient", "unlisted") => r.buyback_payee = Payee::Unlisted,
            ("buyback_fee_recipient", "zero") => r.buyback_payee = Payee::Zero,
            ("buyback_fee_recipient", k) => mark(&mut r.buyback, k),
            ("associated_quote_buyback_fee_recipient", k) => mark(&mut r.buyback_quote, k),
            ("bonding_curve", k) => mark(&mut r.bonding_curve, k),
            ("associated_base_bonding_curve", k) => mark(&mut r.curve_base, k),
            ("associated_quote_bonding_curve", k) => mark(&mut r.curve_quote, k),
            ("user", _) => r.user_unsigned = true,
            ("associated_base_user", k) => mark(&mut r.user_base, k),
            ("associated_quote_user", k) => mark(&mut r.user_quote, k),
            ("creator_vault", k) => mark(&mut r.creator_vault, k),
            ("associated_creator_vault", k) => mark(&mut r.vault_quote, k),
            ("sharing_config", k) => mark(&mut r.sharing_config, k),
            ("global_volume_accumulator", k) => mark(&mut r.global_volume, k),
            ("user_volume_accumulator", k) => mark(&mut r.accumulator, k),
            ("associated_user_volume_accumulator", k) => mark(&mut r.accumulator_quote, k),
            ("uva", "absent" | "funded") => r.accumulator_shape = Accumulator::Absent,
            ("uva", "sysdata") => r.accumulator_shape = Accumulator::AbsentWithData,
            ("uva", "len8") => r.accumulator_shape = Accumulator::Truncated,
            ("uva", "len136") => r.accumulator_shape = Accumulator::WrongSize,
            ("uva", "short") => r.accumulator.short = true,
            ("uva", "user") => {} // the stored user field is never read
            ("fee_config", "bump") => r.fee_config_wrong_bump = true,
            ("fee_config", "len100") => r.fee_config_truncated = true,
            ("fee_config", k) => mark(&mut r.fee_config, k),
            ("fee_program", _) => r.fee_program_ok = false,
            ("system_program", _) => r.system_program_ok = false,
            ("event_authority", _) => r.event_authority_ok = false,
            ("program", _) => r.program_ok = false,
            ("h", "whitelisted") => r.whitelisted = true,
            ("h", "complete") => r.gates.complete = true,
            ("h", "cashback") => {} // v2 trades do not refuse a cashback coin here
            ("h", "zero") => r.gates.zero_amount = true,
            ("h", "zero_quote") => r.gates.zero_quote = true,
            ("h", "over") => r.gates.over_amount = true,
            other => panic!("unknown fault {other:?}"),
        }
    }
    r
}

fn answer(line: &str) -> String {
    match admit(&request(line)) {
        Outcome::Pass => "pass".to_string(),
        Outcome::Transfer(c) => format!("transfer:{c}"),
        Outcome::NativeFeeToSystemProgram => "system".to_string(),
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
