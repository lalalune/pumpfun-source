//! stdin/stdout driver for `liquidity.rs`, used by
//! `tests/test_pump_amm_liquidity_captured.py`. One case per line:
//! `kind,payload_hex,count,writable_mask,user_signer,epoch,timestamp,signer,
//! program_ok,event_ok,token_ok,token22_ok,` then eleven
//! `owner,data_hex,key_hex` groups for pool, global_config, user, base_mint,
//! quote_mint, lp_mint, user_base, user_quote, user_lp, vault_base, vault_quote.
//! `kind` is `d` or `w`. `signer` is `0` valid, `1` invalid seeds, `2` mismatch.
//! Owner tags are `0` other, `1` amm, `2` spl token, `3` token-2022.
//! Answers are `error:<code-or-name>`, `event-then:<name>,<event_hex>,<cpi>` or
//! `ok,<pool>,<user_base>,<user_quote>,<user_lp>,<vault_base>,<vault_quote>,<lp_mint>,<event>,<cpi>`.
//! CPI entries are `s|2|a` plus `:` and hex, joined by `;`.
use std::io::{self, BufRead, Write};

#[path = "liquidity.rs"]
mod liquidity;
use liquidity::*;

fn unhex(s: &str) -> Vec<u8> {
    if s.is_empty() {
        return Vec::new();
    }
    (0..s.len()).step_by(2).map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap()).collect()
}

fn hex(b: &[u8]) -> String {
    b.iter().map(|x| format!("{x:02x}")).collect()
}

fn key(s: &str) -> [u8; 32] {
    unhex(s).try_into().unwrap()
}

fn cpi_text(cpi: &[(u8, Vec<u8>)]) -> String {
    cpi.iter()
        .map(|(program, data)| format!("{}:{}", ['s', '2', 'a'][*program as usize], hex(data)))
        .collect::<Vec<_>>()
        .join(";")
}

fn moved_text(kind: &str, name: &str, moved: &Moved) -> String {
    format!(
        "{kind}:{name},{},{}",
        hex(&moved.event),
        cpi_text(&moved.cpi)
    )
}

fn main() {
    let stdin = io::stdin();
    let mut out = io::stdout().lock();
    for line in stdin.lock().lines() {
        let line = line.unwrap();
        let f: Vec<&str> = line.trim().split(',').collect();
        let count: usize = f[2].parse().unwrap();
        let mask: u32 = f[3].parse().unwrap();
        let mut accounts = Vec::with_capacity(11);
        for i in 0..11 {
            let base = 12 + i * 3;
            accounts.push(Acc {
                owner: f[base].parse().unwrap(),
                writable: count > i && mask & (1 << i) != 0,
                data: unhex(f[base + 1]),
                key: key(f[base + 2]),
            });
        }
        let call = Call {
            kind: if f[0] == "d" { Kind::Deposit } else { Kind::Withdraw },
            payload: unhex(f[1]),
            count,
            user_signer: f[4] == "1",
            epoch: f[5].parse().unwrap(),
            timestamp: f[6].parse().unwrap(),
            signer: f[7].parse().unwrap(),
            program_ok: f[8] == "1",
            event_ok: f[9] == "1",
            token_ok: f[10] == "1",
            token22_ok: f[11] == "1",
            accounts,
        };
        let answer = match liquidity(&call) {
            Outcome::Error(code) => format!("error:{code}"),
            Outcome::InvalidAccountData => "error:InvalidAccountData".to_string(),
            Outcome::BorshIoError => "error:BorshIoError".to_string(),
            Outcome::UninitializedAccount => "error:UninitializedAccount".to_string(),
            Outcome::IncorrectProgramId => "error:IncorrectProgramId".to_string(),
            Outcome::PrivilegeEscalation => "error:PrivilegeEscalation".to_string(),
            Outcome::ProgramFailedToComplete => "error:ProgramFailedToComplete".to_string(),
            Outcome::MissingAccountAfterEvent(moved) => moved_text("event-then", "MissingAccount", &moved),
            Outcome::BorshIoErrorAfterEvent(moved) => moved_text("event-then", "BorshIoError", &moved),
            Outcome::Ok(moved) => format!(
                "ok,{},{},{},{},{},{},{},{},{}",
                hex(&moved.pool),
                hex(&moved.user_base),
                hex(&moved.user_quote),
                hex(&moved.user_lp),
                hex(&moved.vault_base),
                hex(&moved.vault_quote),
                hex(&moved.lp_mint),
                hex(&moved.event),
                cpi_text(&moved.cpi)
            ),
        };
        writeln!(out, "{answer}").unwrap();
    }
}
