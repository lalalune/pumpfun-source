//! Host driver for `claim_cashback_v2.rs`, used by `tests/test_claim_cashback_v2_captured.py`.
//! One request per line:
//! `user,native,token_program_ok,mint_owner_ok,uva_quote_balance,quote_user,uva_lamports,uva_data,timestamp`
//! where `user` and `uva_data` are hex, flags are `0|1`, `uva_quote_balance` is
//! a balance or `-`, and `quote_user` is `user|stranger|absent`. Answers
//! `error:<code>`, `panic`, or `ok,<lamports>,<tokens>,<uva hex>,<event hex or ->`.
#[path = "claim_cashback_v2.rs"]
mod claim_cashback_v2;

use claim_cashback_v2::{Claim, QuoteUser, Stop};
use std::io::{self, BufRead, Write};

fn unhex(text: &str) -> Vec<u8> {
    (0..text.len()).step_by(2).map(|i| u8::from_str_radix(&text[i..i + 2], 16).unwrap()).collect()
}

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let data = unhex(f[7]);
    let c = Claim {
        user: unhex(f[0]).try_into().unwrap(),
        native: f[1] == "1",
        token_program_ok: f[2] == "1",
        mint_owner_ok: f[3] == "1",
        uva_quote_balance: if f[4] == "-" { None } else { Some(f[4].parse().unwrap()) },
        quote_user: match f[5] {
            "user" => QuoteUser::User,
            "stranger" => QuoteUser::Stranger,
            "absent" => QuoteUser::Absent,
            other => panic!("unknown quote user {other}"),
        },
        uva_lamports: f[6].parse().unwrap(),
        uva_data: &data,
    };
    match claim_cashback_v2::claim(&c, f[8].parse().unwrap()) {
        Err(Stop::Code(code)) => format!("error:{code}"),
        Err(Stop::Panic) => "panic".to_string(),
        Ok(r) => format!(
            "ok,{},{},{},{}",
            r.lamports,
            r.tokens,
            hex(&r.uva_data),
            r.event.map_or("-".to_string(), |e| hex(&e))
        ),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
