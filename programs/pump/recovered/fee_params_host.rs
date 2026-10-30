//! Host driver for `fee_params.rs`, used by `tests/test_fee_params_captured.py`.
//! One request per line:
//! `ix,authority_signs,authority_matches,timestamp,args,global,recipients`
//! where `ix` is `set_params|set_reserved_fee_recipients`, `args` (instruction
//! data after the discriminator) and `global` (Global account bytes) are hex,
//! and `recipients` is `key/lamports/data_len/executable` items joined by `+`
//! (`key` in hex; empty for none). Answers `error:<code>` or
//! `ok,<global hex>,<event hex>`.
#[path = "fee_params.rs"]
mod fee_params;

use fee_params::{Admin, Recipient};
use std::io::{self, BufRead, Write};

fn unhex(text: &str) -> Vec<u8> {
    (0..text.len()).step_by(2).map(|i| u8::from_str_radix(&text[i..i + 2], 16).unwrap()).collect()
}

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}

fn recipient(item: &str) -> Recipient {
    let f: Vec<&str> = item.split('/').collect();
    Recipient {
        key: unhex(f[0]).try_into().unwrap(),
        lamports: f[1].parse().unwrap(),
        data_len: f[2].parse().unwrap(),
        executable: f[3] == "1",
    }
}

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let admin = Admin { authority_signs: f[1] == "1", authority_matches: f[2] == "1" };
    let timestamp: i64 = f[3].parse().unwrap();
    let args = unhex(f[4]);
    let mut global = unhex(f[5]);
    let remaining: Vec<Recipient> = f[6].split('+').filter(|s| !s.is_empty()).map(recipient).collect();
    let result = match f[0] {
        "set_params" => fee_params::set_params(admin, &args, &remaining, timestamp, &mut global),
        "set_reserved_fee_recipients" => {
            fee_params::set_reserved_fee_recipients(admin, &args, &remaining, timestamp, &mut global)
        }
        other => panic!("unknown instruction {other}"),
    };
    match result {
        Err(code) => format!("error:{code}"),
        Ok(event) => format!("ok,{},{}", hex(&global), hex(&event)),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
