//! Host driver for `holder_distribution_admission.rs` and
//! `holder_distribution_token.rs`, used by
//! `tests/test_holder_distribution_admission_captured.py`. One request per line:
//! `native|wrapped|token fault fault ...`, where a fault is `<slot>.<kind>`. Answers
//! are `error:<code>`, `error:<name>`, or
//! `ok,<events>,<holder-rewards lamports>,<source tokens>`.
#[path = "holder_distribution_admission.rs"]
mod admission;
#[allow(dead_code)]
#[path = "holder_distribution_token.rs"]
mod holder_distribution_token;

use admission::{admit, first_payout, Load, Request, Rewards, SourceSlot, Stop};
use holder_distribution_token::{distribute, Ata, Case, Payee, Program, Source};
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

fn stop(s: Stop) -> String {
    match s {
        Stop::Code(c) => format!("error:{c}"),
        Stop::InvalidAccountData => "error:invalid_account_data".to_string(),
        Stop::InvalidArgument => "error:invalid_argument".to_string(),
        Stop::ExternalLamportSpend => "error:external_lamport_spend".to_string(),
    }
}

fn answer(line: &str) -> String {
    let mut words = line.split_whitespace();
    let route = words.next().unwrap();
    let mut r = Request::default();
    r.source = SourceSlot { present: route != "native", ..SourceSlot::default() };
    let mut rewards = Rewards::default();
    let mut rewards_lamports = 1_000_000_000;
    let (mut source_key_wrong, mut source_t22, mut quote_t22, mut quote_other) = (false, false, false, false);
    let mut source_short = false;
    let (mut authority_ok, mut slots_ok, mut wrong_event_program) = (true, true, false);
    let mut entries = vec![(Payee::Wallet(0), 1000, Ata::Exists), (Payee::Wallet(1), 2000, Ata::Empty)];
    for word in words {
        let (slot, kind) = word.split_once('.').unwrap();
        match (slot, kind) {
            ("global", "key") => r.global_wrong_address = true,
            ("global", k) => load(&mut r.global, k),
            ("holder_reward_claim_authority", "unsigned") => r.authority_unsigned = true,
            ("holder_reward_claim_authority", _) => r.authority_read_only = true,
            ("mint", "key") => r.rewards_wrong_address = true,
            ("mint", _) => {} // unchecked, and only its key is used
            ("holder_rewards", "key") => r.rewards_wrong_address = true,
            ("holder_rewards", "readonly") => r.rewards_read_only = true,
            ("holder_rewards", "owner") => rewards.foreign_owner = true,
            ("holder_rewards", "data") => rewards.has_data = true,
            ("holder_rewards", _) => {
                rewards = Rewards::default(); // the slot's last fault wins
                rewards_lamports = 0;
            }
            ("holder_rewards_token_account", "key") => source_key_wrong = true,
            ("holder_rewards_token_account", "none") => {
                source_key_wrong = false;
                r.source = SourceSlot::default();
            }
            // The optional slot holds no account: these change nothing.
            ("holder_rewards_token_account", _) if !r.source.present => {}
            ("holder_rewards_token_account", "readonly") => r.source.read_only = true,
            ("holder_rewards_token_account", "ownerdata") if !source_short => r.source.wrong_authority = true,
            ("holder_rewards_token_account", "mintdata") if !source_short => r.source.wrong_mint = true,
            ("holder_rewards_token_account", "ownerdata" | "mintdata") => {}
            ("holder_rewards_token_account", "t22") => {
                source_t22 = true;
                if r.source.load == Load::WrongOwner {
                    // This fault sets the owner too, and keeps the data.
                    r.source.load = if source_short { Load::Short } else { Load::Stored };
                }
            }
            ("holder_rewards_token_account", k) => {
                source_short |= k == "short";
                load(&mut r.source.load, k);
            }
            ("quote_mint", "other") => quote_other = true,
            ("quote_mint", k) => load(&mut r.quote_mint, k),
            ("quote_token_program", "key") => {
                r.quote_token_program_wrong = true;
                quote_t22 = false;
            }
            ("quote_token_program", _) => {
                r.quote_token_program_wrong = false; // the slot's last fault wins
                quote_t22 = true;
            }
            ("associated_token_program", _) => r.associated_program_wrong = true,
            ("system_program", _) => r.system_program_wrong = true,
            ("event_authority", _) => r.event_authority_wrong = true,
            ("program", _) => wrong_event_program = true,
            ("h", "authority") => authority_ok = false,
            ("h", "slots") => slots_ok = false,
            ("h", "over") => entries[1].1 = 1_000_000_000_000,
            ("h", "empty") => entries.clear(),
            ("h", "lastwrong") => {
                entries = vec![(Payee::Wallet(0), 1000, Ata::Exists), (Payee::Wallet(1), 2000, Ata::Wrong)];
            }
            other => panic!("unknown fault {other:?}"),
        }
    }
    r.authority_wrong = !authority_ok;
    r.source.wrong_mint |= quote_other;
    r.source.wrong_program = source_t22 != quote_t22;
    // A wrong key with no account behind it is an absent account, not an absent option.
    if source_key_wrong && !r.source.present {
        r.source.present = true;
        r.source.load = Load::Missing;
    }
    if let Err(s) = admit(&r) {
        return stop(s);
    }
    let native = route != "token" && !quote_other;
    let amount = if route == "wrapped" { 5_000 } else { 1_000_000 };
    if quote_t22 && !native {
        // Recipient accounts derive from the quote token program.
        for entry in &mut entries {
            entry.2 = Ata::Wrong;
        }
    }
    if native && slots_ok && entries.iter().any(|entry| entry.1 != 0) {
        if let Err(s) = first_payout(&rewards) {
            return stop(s);
        }
    }
    let count = entries.len() as u64;
    let case = Case {
        signed: true,
        authority_ok: true,
        native,
        program: if quote_t22 { Program::Token2022 } else { Program::Token },
        mint_program: Program::Token,
        source: r.source.present.then_some(Source { authority_ok: true, mint_ok: true, program_ok: true, amount }),
        rewards_lamports,
        recipient_accounts: if slots_ok { 2 * count } else { 2 * count + 3 },
        entries,
    };
    match distribute(&case) {
        Err(holder_distribution_token::Stop::Code(c)) => format!("error:{c}"),
        Err(other) => panic!("the fixture does not reach {other:?}"),
        Ok(_) if wrong_event_program && r.source.present => "error:missing_account".to_string(),
        Ok(done) => format!("ok,1,{},{}", done.rewards_lamports, done.source_amount.unwrap_or(0)),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
