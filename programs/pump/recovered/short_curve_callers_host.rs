//! Host driver for `short_curve_callers.rs`, used by
//! `tests/test_short_curve_callers_captured.py`. One request per line:
//! `<op>,<curve bytes in hex>,<curve lamports>`. One answer per line:
//! `ok,<top-up>,<grows|read|stores>,<effective account in hex>`, `invalid`,
//! `bool`, or `error:<code>`.
#[path = "short_curve_callers.rs"]
mod short_curve_callers;

use short_curve_callers::{caller, effective, top_up, Caller, Stop};
use std::io::{self, BufRead, Write};

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let hex = f[1];
    let data: Vec<u8> = (0..hex.len() / 2).map(|i| u8::from_str_radix(&hex[2 * i..2 * i + 2], 16).unwrap()).collect();
    let role = caller(f[0]).unwrap();
    let result = effective(&data).and_then(|image| {
        let paid = if role == Caller::Grows { top_up(&image, f[2].parse().unwrap())? } else { 0 };
        Ok((paid, image))
    });
    match result {
        Ok((paid, image)) => {
            let text: String = image.iter().map(|byte| format!("{byte:02x}")).collect();
            let name = match role {
                Caller::Grows => "grows",
                Caller::ReadOnly => "read",
                Caller::StoresShort => "stores",
            };
            format!("ok,{paid},{name},{text}")
        }
        Err(Stop::InvalidAccountData) => "invalid".to_string(),
        Err(Stop::InvalidBool) => "bool".to_string(),
        Err(Stop::Code(code)) => format!("error:{code}"),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
