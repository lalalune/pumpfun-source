//! Line host for `creator_fee_collect.rs`, used by
//! `tests/test_creator_fee_collect_captured.py`.
//!
//! Input: `fees,exec,creator_lamports,creator_data_len,vault_lamports,quote`
//! where quote is `native` or `spl:<vault_tokens or ->:<creator_ata 0/1>`.
//! Output: `ok,lamports,tokens,event` or `error:<6050|invalid_account_data|arithmetic_overflow>`.

#[path = "creator_fee_collect.rs"]
mod creator_fee_collect;

use creator_fee_collect::{collect, Collect, CollectError, Quote};
use std::io::{self, BufRead, Write};

fn parse(line: &str) -> Collect {
    let f: Vec<&str> = line.split(',').collect();
    let num = |s: &str| s.parse::<u64>().expect("number");
    let quote = if f[5] == "native" {
        Quote::Native
    } else {
        let q: Vec<&str> = f[5].split(':').collect();
        Quote::Spl {
            vault_tokens: if q[1] == "-" { None } else { Some(num(q[1])) },
            creator_ata_exists: q[2] == "1",
        }
    };
    Collect {
        creator_owned_by_fees: f[0] == "1",
        creator_executable: f[1] == "1",
        creator_lamports: num(f[2]),
        creator_data_len: num(f[3]),
        vault_lamports: num(f[4]),
        quote,
    }
}

fn main() {
    let stdin = io::stdin();
    let mut out = io::stdout().lock();
    for line in stdin.lock().lines() {
        let line = line.expect("line");
        let answer = match collect(&parse(line.trim())) {
            Ok(c) => format!("ok,{},{},{}", c.lamports, c.tokens, c.event as u8),
            Err(CollectError::Custom(code)) => format!("error:{code}"),
            Err(CollectError::InvalidAccountData) => "error:invalid_account_data".to_string(),
            Err(CollectError::ArithmeticOverflow) => "error:arithmetic_overflow".to_string(),
        };
        writeln!(out, "{answer}").expect("write");
    }
}
