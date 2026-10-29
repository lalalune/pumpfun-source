//! Line host for `global_lifecycle`.
//!
//! `initialize <flags> <user_lamports> <global_lamports> <user_hex> <data_or_->`
//! `toggle <name> <flags> <arg_hex> <data_hex>`
//! `authority <flags> <timestamp> <global_hex> <new_hex> <data_hex>`
//!
//! Attribution: SpaceXAI grok-4.7-high-fast, Cursor cloud agent.
#[path = "global_lifecycle.rs"]
mod global_lifecycle;

use global_lifecycle::{initialize, rotate_authority, toggle, InitAdmission, Stop};
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

fn key(bytes: &[u8]) -> [u8; 32] {
    bytes.try_into().expect("32-byte key")
}

fn answer(line: &str) -> String {
    let mut parts = line.split_whitespace();
    let kind = parts.next().expect("kind");
    match kind {
        "initialize" => {
            let flags: u32 = parts.next().unwrap().parse().unwrap();
            let user_lamports: u64 = parts.next().unwrap().parse().unwrap();
            let global_lamports: u64 = parts.next().unwrap().parse().unwrap();
            let user = key(&decode_hex(parts.next().unwrap()));
            let data = decode_hex(parts.next().unwrap());
            match initialize(InitAdmission::from_flags(flags), user_lamports, global_lamports, user, &data) {
                Ok(done) => format!(
                    "ok {} {} {}",
                    done.lamports,
                    encode_hex(&done.data),
                    done.user_lamports.map(|n| n.to_string()).unwrap_or_else(|| "-".to_string())
                ),
                Err(Stop::Code(code)) => format!("err {code}"),
                Err(Stop::Privilege) => "privilege".to_string(),
                Err(Stop::MissingAccount) => "missing".to_string(),
            }
        }
        "toggle" => {
            let name = parts.next().unwrap();
            let flags: u32 = parts.next().unwrap().parse().unwrap();
            let arg = decode_hex(parts.next().unwrap());
            let data = decode_hex(parts.next().unwrap());
            match toggle(name, flags, &arg, &data) {
                Ok(next) => format!("ok {}", encode_hex(&next)),
                Err(Stop::Code(code)) => format!("err {code}"),
                Err(Stop::Privilege) => "privilege".to_string(),
                Err(Stop::MissingAccount) => "missing".to_string(),
            }
        }
        "authority" => {
            let flags: u32 = parts.next().unwrap().parse().unwrap();
            let timestamp: i64 = parts.next().unwrap().parse().unwrap();
            let global = key(&decode_hex(parts.next().unwrap()));
            let new_authority = key(&decode_hex(parts.next().unwrap()));
            let data = decode_hex(parts.next().unwrap());
            match rotate_authority(flags, timestamp, global, new_authority, &data) {
                Ok((next, event)) => format!("ok {} {}", encode_hex(&next), encode_hex(&event)),
                Err(Stop::Code(code)) => format!("err {code}"),
                Err(Stop::Privilege) => "privilege".to_string(),
                Err(Stop::MissingAccount) => "missing".to_string(),
            }
        }
        _ => panic!("unknown kind"),
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
