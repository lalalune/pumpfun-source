//! stdin/stdout driver for `account_lifecycle.rs`, used by
//! `tests/test_account_lifecycle_captured.py`. One case per line:
//! `init,<holder>,<lamports>,<payer_available>`,
//! `close,<holder>,<lamports>,<user_signed>`, or
//! `extend,<user_signed>,<owned_by_pump>,<kind>,<len>,<lamports>,<user_lamports>`,
//! where `<holder>` is `missing`, `system`, `system_data`, `other`, or
//! `pump:<len>:<disc_ok>`.
use std::io::{self, BufRead, Write};

#[path = "account_lifecycle.rs"]
mod account_lifecycle;
use account_lifecycle::*;

fn holder(text: &str) -> Holder {
    match text {
        "missing" => Holder::Missing,
        "system" => Holder::SystemEmpty,
        "system_data" => Holder::SystemWithData,
        "other" => Holder::OtherOwner,
        _ => {
            let parts: Vec<&str> = text.split(':').collect();
            assert_eq!(parts[0], "pump");
            Holder::Pump { len: parts[1].parse().unwrap(), disc_ok: parts[2] == "1" }
        }
    }
}

fn kind(text: &str) -> Kind {
    match text {
        "bc" => Kind::BondingCurve,
        "uva" => Kind::UserVolumeAccumulator,
        "gva" => Kind::GlobalVolumeAccumulator,
        "global" => Kind::Global,
        _ => Kind::Other,
    }
}

fn stop(s: Stop) -> String {
    match s {
        Stop::Code(code) => format!("error:{code}"),
        Stop::BelowRent => "rent".to_string(),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        let line = line.unwrap();
        let f: Vec<&str> = line.split(',').collect();
        let n = |i: usize| -> u64 { f[i].parse().unwrap() };
        let answer = match f[0] {
            "init" => match init(holder(f[1]), n(2), n(3)) {
                Ok(r) => format!("ok,{},{}", r.payer_paid, u8::from(r.created)),
                Err(s) => stop(s),
            },
            "close" => match close(holder(f[1]), n(2), f[3] == "1") {
                Ok(refund) => format!("ok,{refund}"),
                Err(s) => stop(s),
            },
            "extend" => match extend(f[1] == "1", f[2] == "1", kind(f[3]), n(4), n(5), n(6)) {
                Ok(r) => format!("ok,{},{}", r.new_len, r.user_paid),
                Err(s) => stop(s),
            },
            other => panic!("unknown op {other}"),
        };
        writeln!(out, "{answer}").unwrap();
    }
}
