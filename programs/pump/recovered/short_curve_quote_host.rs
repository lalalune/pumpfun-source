//! Host driver for `short_curve_quote.rs`, used by
//! `tests/test_short_curve_quote_captured.py`.
//! One request per line: `<curve bytes in hex>,<curve lamports>`. One answer
//! per line: `ok,<top-up>,<effective account in hex>`, `invalid`, `bool`, or
//! `error:<code>`.
#[path = "short_curve_quote.rs"]
mod short_curve_quote;

use short_curve_quote::Stop;
use std::io::{self, BufRead, Write};

fn answer(line: &str) -> String {
    let (hex, lamports) = line.split_once(',').unwrap();
    let data: Vec<u8> = (0..hex.len() / 2).map(|i| u8::from_str_radix(&hex[2 * i..2 * i + 2], 16).unwrap()).collect();
    let result = short_curve_quote::effective(&data).and_then(|image| {
        let top_up = short_curve_quote::top_up(&image, lamports.parse().unwrap())?;
        Ok((top_up, image))
    });
    match result {
        Ok((top_up, image)) => {
            let text: String = image.iter().map(|byte| format!("{byte:02x}")).collect();
            format!("ok,{top_up},{text}")
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
