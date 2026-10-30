//! stdin/stdout driver for `quote_control.rs`, used by
//! `tests/test_quote_control_captured.py`. One case per line:
//! `<op>,<arg_a>,<arg_b>,<signed>,<signer>,<signer_lamports>,<global_authority>,
//! <holder>,<admin>,<reserves_admin>,<len>,<lamports>,<mints>`
//! where `<op>` is `init`, `add`, `remove`, `reserves`, `admin` or
//! `reserves_admin`, `<holder>` is `missing`, `system`, `owner`, `disc`,
//! `short` or `control`, and `<mints>` is `-` or `mint:reserves` pairs joined
//! by `+`. Answers are `ok,<paid>,<len>,<lamports>,<admin>,<reserves_admin>,
//! <old>,<mints>` or `error:<code>`.
use std::io::{self, BufRead, Write};

#[path = "quote_control.rs"]
mod quote_control;
use quote_control::*;

fn mints(text: &str) -> Vec<(u8, u64)> {
    if text == "-" {
        return Vec::new();
    }
    text.split('+')
        .map(|pair| {
            let (mint, reserves) = pair.split_once(':').unwrap();
            (mint.parse().unwrap(), reserves.parse().unwrap())
        })
        .collect()
}

fn holder(text: &str) -> Holder {
    match text {
        "missing" => Holder::Missing,
        "system" => Holder::System,
        "owner" => Holder::WrongOwner,
        "disc" => Holder::BadDiscriminator,
        "short" => Holder::Short,
        "control" => Holder::Control,
        other => panic!("unknown holder {other}"),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        let line = line.unwrap();
        let f: Vec<&str> = line.split(',').collect();
        let n = |i: usize| -> u64 { f[i].parse().unwrap() };
        let id = |i: usize| -> u8 { f[i].parse().unwrap() };
        let op = match f[0] {
            "init" => Op::Initialize,
            "add" => Op::Add { mint: id(1), reserves: n(2) },
            "remove" => Op::Remove { mint: id(1) },
            "reserves" => Op::SetReserves { mint: id(1), reserves: n(2) },
            "admin" => Op::SetAdmin { new_admin: id(1) },
            "reserves_admin" => Op::SetReservesAdmin { new_admin: id(1) },
            other => panic!("unknown op {other}"),
        };
        let control = Control { admin: id(8), reserves_admin: id(9), mints: mints(f[12]), len: n(10), lamports: n(11) };
        let answer = match apply(op, f[3] == "1", id(4), n(5), id(6), holder(f[7]), &control) {
            Ok(done) => {
                let c = done.control;
                let list: Vec<String> = c.mints.iter().map(|(m, r)| format!("{m}:{r}")).collect();
                let list = if list.is_empty() { "-".to_string() } else { list.join("+") };
                format!("ok,{},{},{},{},{},{},{list}", done.paid, c.len, c.lamports, c.admin, c.reserves_admin, done.old)
            }
            Err(code) => format!("error:{code}"),
        };
        writeln!(out, "{answer}").unwrap();
    }
}
