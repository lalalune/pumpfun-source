//! Host driver for `sweep_fees.rs`, used by `tests/test_sweep_fees_captured.py`.
//! One request per line:
//! `bucket,native,mayhem,quote_mint,real_quote,creator_fee,protocol_fees,
//!  curve_lamports,recipient,recipient_lamports,curve_quote_ata,recipient_ata`
//! where `bucket` is `protocol|creator`, `quote_mint` is `native|quote|other`,
//! `recipient` is `fee_recipient|fee_list|reserved|reserved_list|vault|other|zero`,
//! and `curve_quote_ata` is a balance or `-` when the ATA does not exist.
#[path = "sweep_fees.rs"]
mod sweep_fees;

use std::io::{self, BufRead, Write};
use sweep_fees::{Bucket, QuoteMint, Recipient, Stop, Sweep};

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let n = |i: usize| f[i].parse::<u64>().unwrap();
    let s = Sweep {
        bucket: if f[0] == "creator" { Bucket::Creator } else { Bucket::Protocol },
        native: n(1) != 0,
        mayhem: n(2) != 0,
        quote_mint: match f[3] {
            "native" => QuoteMint::Native,
            "quote" => QuoteMint::CurveQuote,
            _ => QuoteMint::Other,
        },
        real_quote_reserves: n(4),
        creator_fee: n(5),
        protocol_fees: n(6),
        curve_lamports: n(7),
        recipient: match f[8] {
            "fee_recipient" => Recipient::FeeRecipient,
            "fee_list" => Recipient::FeeList,
            "reserved" => Recipient::ReservedFeeRecipient,
            "reserved_list" => Recipient::ReservedList,
            "vault" => Recipient::CreatorVault,
            "other" => Recipient::Other,
            "zero" => Recipient::Zero,
            other => panic!("unknown recipient {other}"),
        },
        recipient_lamports: n(9),
        curve_quote_ata: if f[10] == "-" { None } else { Some(n(10)) },
        recipient_quote_ata_exists: n(11) != 0,
    };
    match sweep_fees::sweep(&s) {
        Err(Stop::Code(code)) => format!("error:{code}"),
        Err(Stop::ArithmeticOverflow) => "arithmetic".to_string(),
        Err(Stop::CurveBelowRent) => "rent".to_string(),
        Ok(r) => format!(
            "ok,{},{},{},{},{},{}",
            r.amount, r.curve_rent_top_up, r.vault_top_up, r.recipient_ata_rent, r.buckets.0, r.buckets.1
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
