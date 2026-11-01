//! Host driver for `legacy_whitelist_admission.rs`, used by
//! `tests/test_legacy_whitelist_admission_captured.py`. One request per line:
//! `handler fault fault ...`, where `handler` is `sell|buy|exact` and a fault
//! is `<slot>.<kind>`. No faults is the expected account set of the whitelisted
//! user. Answers are
//! `pass`, `transfer:<code>`, `error:<code>` or `data`
//! (`InvalidAccountData`).
#[path = "legacy_whitelist_admission.rs"]
mod legacy_whitelist_admission;

use legacy_whitelist_admission::{
    admit, Accumulator, Gates, Handler, Outcome, Payee, ProgramSlot, Request, Slot, Stop, Trailing,
};
use std::io::{self, BufRead, Write};

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

fn request(line: &str) -> Request {
    let mut words = line.split_whitespace();
    let handler = match words.next().unwrap() {
        "sell" => Handler::Sell,
        "buy" => Handler::Buy,
        _ => Handler::BuyExactSol,
    };
    let empty = Slot::default();
    let mut r = Request {
        handler,
        global: empty,
        fee_recipient: empty,
        fee_payee: Payee::default(),
        mint: empty,
        bonding_curve: empty,
        curve_has_quote_mint: false,
        curve_token: empty,
        user_token: empty,
        user_unsigned: false,
        system_program_ok: true,
        token_program: ProgramSlot::default(),
        creator_vault: empty,
        event_authority_ok: true,
        program_ok: true,
        global_volume: empty,
        accumulator: empty,
        accumulator_shape: Accumulator::default(),
        fee_config: empty,
        fee_config_wrong_bump: false,
        fee_config_truncated: false,
        fee_program_ok: true,
        trailing: Trailing::default(),
        buyback_payee: Payee::default(),
        gates: Gates::default(),
    };
    for word in words {
        let (slot, kind) = word.split_once('.').unwrap();
        match (slot, kind) {
            ("global", k) => mark(&mut r.global, k),
            ("fee_recipient", "unlisted") => r.fee_payee = Payee::Unlisted,
            ("fee_recipient", "zero") => {} // the default key is admitted, and nothing is paid
            ("fee_recipient", k) => mark(&mut r.fee_recipient, k),
            ("mint", k) => mark(&mut r.mint, k),
            ("bonding_curve", "quote") => r.curve_has_quote_mint = true,
            ("bonding_curve", k) => mark(&mut r.bonding_curve, k),
            ("associated_bonding_curve", k) => mark(&mut r.curve_token, k),
            ("associated_user", k) => mark(&mut r.user_token, k),
            ("user", _) => r.user_unsigned = true,
            ("system_program", _) => r.system_program_ok = false,
            ("token_program", "t22") => r.token_program = ProgramSlot::OtherInterface,
            ("token_program", _) => r.token_program = ProgramSlot::Invalid,
            ("creator_vault", k) => mark(&mut r.creator_vault, k),
            ("event_authority", _) => r.event_authority_ok = false,
            ("program", _) => r.program_ok = false,
            ("global_volume_accumulator", k) => mark(&mut r.global_volume, k),
            ("user_volume_accumulator", k) => mark(&mut r.accumulator, k),
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
            ("buyback", "unlisted") => r.buyback_payee = Payee::Unlisted,
            ("buyback", "zero") => r.buyback_payee = Payee::Zero,
            ("buyback", "readonly") => {} // nothing is paid to it
            ("buyback", "absent") => r.trailing = Trailing::CurveV2Only,
            ("buyback", "extra") => {} // a third trailing account is ignored
            ("curve_v2", "key") => {} // the key is never compared
            ("curve_v2", "absent") => r.trailing = Trailing::None,
            ("curve_v2", "swapped") => r.trailing = Trailing::Swapped,
            ("h", "complete") => r.gates.complete = true,
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
        Outcome::AfterPricing(c) => format!("transfer:{c}"),
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
