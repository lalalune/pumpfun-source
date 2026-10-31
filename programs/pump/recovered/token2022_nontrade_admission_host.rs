//! Line host for `token2022_nontrade_admission.rs`.
//!
//! One line per case: the route name, then one `slot` field per slot, written
//! `<program>:<body>:<mint>:<authority>`. Program is `t` or `s`, the rest hex.
//! One line of output: `ok` or `error:<name>`.

use std::io::{self, BufRead, Write};

#[path = "token2022_nontrade_admission.rs"]
mod model;

use model::{Ending, Slot};

fn hex(text: &str) -> Vec<u8> {
    (0..text.len() / 2).map(|i| u8::from_str_radix(&text[2 * i..2 * i + 2], 16).unwrap()).collect()
}

fn slot(text: &str) -> Slot {
    let parts: Vec<&str> = text.split(':').collect();
    Slot {
        data: hex(parts[1]),
        right_program: parts[0] == "t",
        expected_mint: hex(parts[2]),
        expected_authority: hex(parts[3]),
    }
}

fn answer(line: &str) -> String {
    let mut fields = line.split_whitespace();
    let stops = model::route(fields.next().unwrap()).unwrap();
    let slots: Vec<Slot> = fields.map(slot).collect();
    match model::ending(stops, &slots) {
        Ending::Ok => "ok".to_string(),
        Ending::Code(code) => format!("error:{code}"),
        Ending::InvalidAccountData => "error:invalid_account_data".to_string(),
        Ending::UninitializedAccount => "error:uninitialized_account".to_string(),
        Ending::IncorrectProgramId => "error:incorrect_program_id".to_string(),
    }
}

fn main() {
    let stdin = io::stdin();
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in stdin.lock().lines() {
        writeln!(out, "{}", answer(&line.unwrap())).unwrap();
    }
}
