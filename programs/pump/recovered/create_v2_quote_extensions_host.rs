//! Host driver for `create_v2_quote_extensions.rs`, used by
//! `tests/test_create_v2_quote_extensions_captured.py`. One request per line:
//! `spl_program,gate,mint_data` where `gate` is `-`, `before:<code>`,
//! `after:<code>`, `late:<code>` or `exists`, and `mint_data` is hex. Answers:
//! `error:<code>`, `IllegalOwner`, or `ok,<quote account size>`.
#[path = "create_v2_quote_extensions.rs"]
#[allow(dead_code)]
mod create_v2_quote_extensions;

use create_v2_quote_extensions::{Gate, Stop};
use std::io::{self, BufRead, Write};

fn unhex(text: &str) -> Vec<u8> {
    (0..text.len() / 2).map(|i| u8::from_str_radix(&text[2 * i..2 * i + 2], 16).unwrap()).collect()
}

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let gate = match f[1].split_once(':') {
        Some(("before", code)) => Some(Gate::Before(code.parse().unwrap())),
        Some(("after", code)) => Some(Gate::After(code.parse().unwrap())),
        Some(("late", code)) => Some(Gate::Late(code.parse().unwrap())),
        _ if f[1] == "exists" => Some(Gate::QuoteAccountExists),
        _ => None,
    };
    match create_v2_quote_extensions::check(&unhex(f[2]), f[0] == "1", gate) {
        Ok(size) => format!("ok,{size}"),
        Err(Stop::Code(code)) => format!("error:{code}"),
        Err(Stop::IllegalOwner) => "IllegalOwner".to_string(),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
