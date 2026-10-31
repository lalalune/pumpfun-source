//! stdin/stdout driver for `anchor_idl.rs`, used by
//! `tests/test_anchor_idl_captured.py`. The first line is
//! `<pump>,<empty-seed PDA>,<canonical IDL address>` in hex. Each later line is
//! one case: `<args hex>` then, separated by `;`, one account per slot as
//! `<key>,<signer>,<writable>,<owner>,<lamports>,<executable>,<data hex>` with
//! `<owner>` one of `s`, `p`, `o`. Answers are `error:<code>:<account or ->`,
//! `system:<code>`, `runtime:<name>`, `panic`, or `ok:<log>` followed by the
//! accounts as `;<key>,<owner>,<lamports>,<data hex>`.
use std::io::{self, BufRead, Write};

#[path = "anchor_idl.rs"]
mod anchor_idl;
use anchor_idl::*;

fn bytes(text: &str) -> Vec<u8> {
    (0..text.len() / 2).map(|i| u8::from_str_radix(&text[2 * i..2 * i + 2], 16).unwrap()).collect()
}

fn hex(data: &[u8]) -> String {
    data.iter().map(|b| format!("{b:02x}")).collect()
}

fn key(text: &str) -> Key {
    bytes(text).try_into().unwrap()
}

fn account(text: &str) -> Account {
    let f: Vec<&str> = text.split(',').collect();
    Account {
        key: key(f[0]),
        signer: f[1] == "1",
        writable: f[2] == "1",
        owner: match f[3] {
            "s" => Owner::System,
            "p" => Owner::Pump,
            _ => Owner::Other,
        },
        lamports: f[4].parse().unwrap(),
        executable: f[5] == "1",
        data: bytes(f[6]),
    }
}

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    let first = lines.next().unwrap().unwrap();
    let f: Vec<&str> = first.trim().split(',').collect();
    let keys = Keys { pump: key(f[0]), base: key(f[1]), canonical: key(f[2]) };
    let mut out = io::stdout().lock();
    for line in lines {
        let line = line.unwrap();
        let mut parts = line.trim().split(';');
        let args = bytes(parts.next().unwrap());
        let slots: Vec<Account> = parts.map(account).collect();
        let answer = match run(&keys, &args, &slots) {
            Err(Failure::Code(code, name)) => format!("error:{code}:{}", name.unwrap_or("-")),
            Err(Failure::System(code)) => format!("system:{code}"),
            Err(Failure::Runtime(name)) => format!("runtime:{name}"),
            Err(Failure::Panic) => "panic".to_string(),
            Ok(done) => {
                let mut text = format!("ok:{}", done.log);
                for a in &done.accounts {
                    let owner = match a.owner {
                        Owner::System => 's',
                        Owner::Pump => 'p',
                        Owner::Other => 'o',
                    };
                    text += &format!(";{},{owner},{},{}", hex(&a.key), a.lamports, hex(&a.data));
                }
                text
            }
        };
        writeln!(out, "{answer}").unwrap();
    }
}
