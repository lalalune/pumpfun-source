//! stdin/stdout driver for `holder_distribution_token.rs`, used by
//! `tests/test_holder_distribution_token_captured.py`. One case per line:
//! `<signed>,<authority_ok>,<native>,<program>,<mint_program>,<source>,
//! <rewards_lamports>,<recipient_accounts>,<entries>` where programs are `t`
//! or `t22`, `<source>` is `-` or `<authority_ok><mint_ok><program_ok>:<amount>`
//! and `<entries>` is `-` or `payee:amount:ata` joined by `+`, a payee being
//! `w<id>`, `r` or `ro<id>` and ata `e` (exists), `n` (empty) or `x` (wrong).
//! Answers are `ok,<rewards_lamports>,<authority_paid>,<source_amount>,
//! <recipients>,<total>,<credits>,<created>` (`-` for none), `error:<code>`,
//! `escalation` or `incorrect-program-id`.
use std::io::{self, BufRead, Write};

#[path = "holder_distribution_token.rs"]
mod holder_distribution_token;
use holder_distribution_token::*;

fn program(text: &str) -> Program {
    if text == "t22" {
        Program::Token2022
    } else {
        Program::Token
    }
}

fn payee(text: &str) -> Payee {
    if text == "r" {
        Payee::Rewards
    } else if let Some(id) = text.strip_prefix("ro") {
        Payee::Readonly(id.parse().unwrap())
    } else {
        Payee::Wallet(text.strip_prefix('w').unwrap().parse().unwrap())
    }
}

fn joined<T>(items: &[T], show: impl Fn(&T) -> String) -> String {
    if items.is_empty() {
        "-".to_string()
    } else {
        items.iter().map(show).collect::<Vec<_>>().join("+")
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        let line = line.unwrap();
        let f: Vec<&str> = line.split(',').collect();
        let source = if f[5] == "-" {
            None
        } else {
            let (flags, amount) = f[5].split_once(':').unwrap();
            let flag = |i: usize| flags.as_bytes()[i] == b'1';
            Some(Source { authority_ok: flag(0), mint_ok: flag(1), program_ok: flag(2), amount: amount.parse().unwrap() })
        };
        let entries = if f[8] == "-" {
            Vec::new()
        } else {
            f[8].split('+')
                .map(|item| {
                    let parts: Vec<&str> = item.split(':').collect();
                    let ata = match parts[2] {
                        "e" => Ata::Exists,
                        "n" => Ata::Empty,
                        _ => Ata::Wrong,
                    };
                    (payee(parts[0]), parts[1].parse().unwrap(), ata)
                })
                .collect()
        };
        let case = Case {
            signed: f[0] == "1",
            authority_ok: f[1] == "1",
            native: f[2] == "1",
            program: program(f[3]),
            mint_program: program(f[4]),
            source,
            rewards_lamports: f[6].parse().unwrap(),
            recipient_accounts: f[7].parse().unwrap(),
            entries,
        };
        let answer = match distribute(&case) {
            Ok(done) => format!(
                "ok,{},{},{},{},{},{},{}",
                done.rewards_lamports,
                done.authority_paid,
                done.source_amount.map_or("-".to_string(), |n| n.to_string()),
                done.recipients,
                done.total,
                joined(&done.credits, |(id, n)| format!("{id}:{n}")),
                joined(&done.created, |id| id.to_string())
            ),
            Err(Stop::Code(code)) => format!("error:{code}"),
            Err(Stop::PrivilegeEscalation) => "escalation".to_string(),
            Err(Stop::IncorrectProgramId) => "incorrect-program-id".to_string(),
        };
        writeln!(out, "{answer}").unwrap();
    }
}
