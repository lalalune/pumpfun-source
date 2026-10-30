//! stdin/stdout driver for `holder_distribution.rs`, used by
//! `tests/test_holder_distribution_captured.py`. One case per line:
//! `<signed>,<authority_ok>,<rewards_address_ok>,<quote>,<rewards_lamports>,
//! <recipient_accounts>,<entries>` where `<quote>` is `native`, `token` or
//! `missing` and `<entries>` is `-` or `payee:amount` pairs joined by `+`,
//! a payee being `w<id>`, `r` (the rewards PDA) or `ro<id>`. Answers are
//! `ok,<rewards_lamports>,<recipients>,<total>,<credits>` with credits as
//! `id:amount` pairs joined by `+` (or `-`), `error:<code>` or `escalation`.
use std::io::{self, BufRead, Write};

#[path = "holder_distribution.rs"]
mod holder_distribution;
use holder_distribution::*;

fn payee(text: &str) -> Payee {
    if text == "r" {
        Payee::Rewards
    } else if let Some(id) = text.strip_prefix("ro") {
        Payee::Readonly(id.parse().unwrap())
    } else {
        Payee::Wallet(text.strip_prefix('w').unwrap().parse().unwrap())
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        let line = line.unwrap();
        let f: Vec<&str> = line.split(',').collect();
        let entries = if f[6] == "-" {
            Vec::new()
        } else {
            f[6].split('+')
                .map(|pair| {
                    let (who, amount) = pair.split_once(':').unwrap();
                    (payee(who), amount.parse().unwrap())
                })
                .collect()
        };
        let case = Case {
            signed: f[0] == "1",
            authority_ok: f[1] == "1",
            rewards_address_ok: f[2] == "1",
            quote: match f[3] {
                "native" => Quote::Native,
                "token" => Quote::Token,
                _ => Quote::Missing,
            },
            rewards_lamports: f[4].parse().unwrap(),
            recipient_accounts: f[5].parse().unwrap(),
            entries,
        };
        let answer = match distribute(&case) {
            Ok(done) => {
                let credits: Vec<String> = done.credits.iter().map(|(id, n)| format!("{id}:{n}")).collect();
                let credits = if credits.is_empty() { "-".to_string() } else { credits.join("+") };
                format!("ok,{},{},{},{}", done.rewards_lamports, done.recipients, done.total, credits)
            }
            Err(Stop::Code(code)) => format!("error:{code}"),
            Err(Stop::PrivilegeEscalation) => "escalation".to_string(),
        };
        writeln!(out, "{answer}").unwrap();
    }
}
