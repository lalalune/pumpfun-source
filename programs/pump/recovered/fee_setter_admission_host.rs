//! Host driver for `fee_setter_admission.rs` and `fee_params.rs`, used by
//! `tests/test_fee_setter_admission_captured.py`. One request per line:
//! `<setter> fault fault ...`, where a fault is `<slot>.<kind>`. Answers are
//! `error:<code>`, `error:missing_account`, or
//! `ok,<events>,<first changed byte of Global>,<last changed byte>`.
#[allow(dead_code)]
#[path = "fee_params.rs"]
mod fee_params;
#[path = "fee_setter_admission.rs"]
mod fee_setter_admission;

use fee_params::{set_params, set_reserved_fee_recipients, Admin, Recipient, LAMPORTS_PER_BYTE};
use fee_setter_admission::{admit, Load, Request};
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

fn params(supply: u64) -> Vec<u8> {
    let mut args = Vec::new();
    for value in [1_073_000_000_000_000u64, 30_000_000_000, 793_100_000_000_000, supply, 95] {
        args.extend_from_slice(&value.to_le_bytes());
    }
    args.extend_from_slice(&[31; 32]);
    args.push(1);
    for value in [15_000_001u64, 5] {
        args.extend_from_slice(&value.to_le_bytes());
    }
    args.extend_from_slice(&[32; 32]);
    args.extend_from_slice(&[33; 32]);
    args
}

fn recipient(fill: u8) -> Recipient {
    Recipient { key: [fill; 32], lamports: 128 * LAMPORTS_PER_BYTE, data_len: 0, executable: false }
}

fn answer(line: &str) -> String {
    let mut words = line.split_whitespace();
    let setter = words.next().unwrap();
    let reserved = setter == "set_reserved_fee_recipients";
    let mut r = Request { authority_needs_mut: !reserved, ..Request::default() };
    let mut recipients: Vec<Recipient> = (0..8).map(|i| recipient(100 + 10 * i)).collect();
    let (mut supply, mut program_wrong) = (1_000_000_000_000_000, false);
    for word in words {
        let (slot, kind) = word.split_once('.').unwrap();
        match (slot, kind) {
            ("global", "key") => r.global_wrong_address = true,
            ("global", "readonly") => r.global_read_only = true,
            ("global", "stored") => r.stored_authority_differs = true,
            ("global", k) => load(&mut r.global, k),
            ("authority", "unsigned") => r.authority_unsigned = true,
            ("authority", _) => r.authority_read_only = true,
            ("event_authority", "key") => r.event_authority_wrong = true,
            ("program", "key" | "token") => program_wrong = true,
            (_, "dropped") => r.account_dropped = true,
            ("h", "args") => r.short_arguments = true,
            ("h", "seven") => recipients.truncate(7),
            ("h", "zero") => recipients[6].key = [0; 32],
            ("h", "poor") => recipients[5].lamports = 1,
            ("h", "unsorted") => recipients.swap(3, 4),
            ("h", "program") => {
                // The Pump program account: executable and out of order.
                recipients[2].key = [255; 32];
                recipients[2].executable = true;
            }
            ("h", "supply") => supply = 1,
            other => panic!("unknown fault {other:?}"),
        }
    }
    if let Err(c) = admit(&r) {
        return format!("error:{c}");
    }
    let admin = Admin { authority_signs: true, authority_matches: true };
    let mut global = vec![0; 1088];
    let (done, first, last) = if reserved {
        (set_reserved_fee_recipients(admin, &[34; 32], &recipients, 0, &mut global), 451, 739)
    } else {
        (set_params(admin, &params(supply), &recipients, 0, &mut global), 41, 449)
    };
    match done {
        Err(c) => format!("error:{c}"),
        Ok(_) if program_wrong => "error:missing_account".to_string(),
        Ok(_) => format!("ok,1,{first},{last}"),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
