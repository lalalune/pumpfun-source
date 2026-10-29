//! Line host for `global_admin`. One request per line, one result per line.
//!
//! `name flags timestamp arg_hex data_hex remaining_hex`
//! flags bits are documented on `Admission::from_flags`.
//! Results are `ok <data_hex> <event_hex|->`, `err <code>`, or `missing`.
//!
//! Attribution: SpaceXAI grok-4.7-high-fast, Cursor cloud agent.
#[path = "global_admin.rs"]
mod global_admin;

use global_admin::{apply, Admission, Stop};
use std::io::{self, BufRead, Write};

fn decode_hex(text: &str) -> Vec<u8> {
    if text == "-" {
        return Vec::new();
    }
    assert!(text.len() % 2 == 0, "odd hex");
    (0..text.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&text[i..i + 2], 16).expect("hex"))
        .collect()
}

fn encode_hex(bytes: &[u8]) -> String {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    let mut out = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        out.push(HEX[(byte >> 4) as usize] as char);
        out.push(HEX[(byte & 0xf) as usize] as char);
    }
    out
}

fn answer(line: &str) -> String {
    let mut parts = line.split_whitespace();
    let name = parts.next().expect("name");
    let flags: u32 = parts.next().expect("flags").parse().expect("flags");
    let timestamp: i64 = parts.next().expect("timestamp").parse().expect("timestamp");
    let arg = decode_hex(parts.next().expect("arg"));
    let data = decode_hex(parts.next().expect("data"));
    let raw_remaining = decode_hex(parts.next().expect("remaining"));
    assert!(raw_remaining.len() % 32 == 0, "remaining");
    let remaining: Vec<[u8; 32]> = raw_remaining
        .chunks(32)
        .map(|chunk| chunk.try_into().unwrap())
        .collect();
    match apply(name, Admission::from_flags(flags), timestamp, &arg, &data, &remaining) {
        Ok(applied) => format!(
            "ok {} {}",
            encode_hex(&applied.data),
            applied.event.as_deref().map(encode_hex).unwrap_or_else(|| "-".to_string())
        ),
        Err(Stop::Code(code)) => format!("err {code}"),
        Err(Stop::MissingAccount) => "missing".to_string(),
    }
}

fn main() {
    let stdin = io::stdin();
    let mut stdout = io::stdout().lock();
    for line in stdin.lock().lines() {
        let line = line.unwrap();
        if line.is_empty() {
            continue;
        }
        writeln!(stdout, "{}", answer(&line)).unwrap();
    }
}
