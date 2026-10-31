//! Host driver for `short_curve_admin_cto.rs`, used by
//! `tests/test_short_curve_admin_cto_captured.py`. One request per line:
//! `<curve bytes in hex>,<curve lamports>`. One answer per line:
//! `ok,<top-up>,<effective account in hex>`, `invalid`, `bool`, or
//! `error:<code>`.
#[path = "short_curve_admin_cto.rs"]
mod short_curve_admin_cto;

use short_curve_admin_cto::{effective, top_up, Stop};
use std::io::{self, BufRead, Write};

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let hex = f[0];
    let data: Vec<u8> = (0..hex.len() / 2).map(|i| u8::from_str_radix(&hex[2 * i..2 * i + 2], 16).unwrap()).collect();
    let result = effective(&data).and_then(|image| {
        let paid = top_up(&image, f[1].parse().unwrap())?;
        Ok((paid, image))
    });
    match result {
        Ok((paid, image)) => {
            let text: String = image.iter().map(|byte| format!("{byte:02x}")).collect();
            format!("ok,{paid},{text}")
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
