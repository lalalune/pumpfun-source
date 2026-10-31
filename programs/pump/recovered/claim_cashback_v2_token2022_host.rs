//! Host driver for `claim_cashback_v2_token2022.rs`, used by
//! `tests/test_claim_cashback_v2_token2022_captured.py`. One request per line:
//! `user,token_program_ok,mint_owner_ok,mint_truncated,fee,hook_set,paused,epoch,
//!  uva_ata_address_ok,uva_ata,user_ata,uva_lamports,uva_data,timestamp`
//! where `user` and `uva_data` are hex, `fee` is `-` or
//! `older_bps:older_max:newer_epoch:newer_bps:newer_max`, and an ATA is
//! `missing|truncated|uninitialized` or `[wrong:]` followed by
//! `balance:frozen:fee_extension:owner_matches:mint_matches:memo:cpi_guard:non_transferable`.
//! Answers: `error:<code>`, `panic`, `invalid_account_data`,
//! `uninitialized_account`, `incorrect_program_id`, or
//! `ok,<tokens>,<withheld>,<uva hex>,<event hex or ->`.
#[path = "claim_cashback_v2.rs"]
#[allow(dead_code)]
mod claim_cashback_v2;
#[path = "claim_cashback_v2_token2022.rs"]
#[allow(dead_code)]
mod claim_cashback_v2_token2022;

use claim_cashback_v2_token2022::{Ata, ClaimToken2022, Holding, Mint, Stop, TransferFee};
use std::io::{self, BufRead, Write};

fn unhex(text: &str) -> Vec<u8> {
    (0..text.len() / 2).map(|i| u8::from_str_radix(&text[2 * i..2 * i + 2], 16).unwrap()).collect()
}

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}

fn holding(text: &str) -> Holding {
    let f: Vec<u64> = text.split(':').map(|v| v.parse().unwrap()).collect();
    Holding {
        balance: f[0],
        frozen: f[1] != 0,
        fee_extension: f[2] != 0,
        owner_matches: f[3] != 0,
        mint_matches: f[4] != 0,
        memo_required: f[5] != 0,
        cpi_guard: f[6] != 0,
        non_transferable: f[7] != 0,
    }
}

fn ata(text: &str) -> Ata {
    match text {
        "missing" => Ata::Missing,
        "truncated" => Ata::Truncated,
        "uninitialized" => Ata::Uninitialized,
        _ => match text.strip_prefix("wrong:") {
            Some(rest) => Ata::WrongProgram(holding(rest)),
            None => Ata::Held(holding(text)),
        },
    }
}

fn fee(text: &str) -> Option<TransferFee> {
    if text == "-" {
        return None;
    }
    let f: Vec<u64> = text.split(':').map(|v| v.parse().unwrap()).collect();
    Some(TransferFee { older_bps: f[0] as u16, older_max: f[1], newer_epoch: f[2], newer_bps: f[3] as u16, newer_max: f[4] })
}

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let n = |i: usize| f[i].parse::<u64>().unwrap();
    let data = unhex(f[12]);
    let c = ClaimToken2022 {
        user: unhex(f[0]).try_into().unwrap(),
        token_program_ok: n(1) != 0,
        mint: Mint {
            owner_matches_program: n(2) != 0,
            truncated: n(3) != 0,
            fee: fee(f[4]),
            hook_set: n(5) != 0,
            paused: n(6) != 0,
        },
        epoch: n(7),
        uva_ata_address_ok: n(8) != 0,
        uva_ata: ata(f[9]),
        user_ata: ata(f[10]),
        uva_lamports: n(11),
        uva_data: &data,
    };
    match claim_cashback_v2_token2022::claim(&c, f[13].parse().unwrap()) {
        Err(Stop::Code(code)) => format!("error:{code}"),
        Err(Stop::Panic) => "panic".to_string(),
        Err(Stop::InvalidAccountData) => "invalid_account_data".to_string(),
        Err(Stop::UninitializedAccount) => "uninitialized_account".to_string(),
        Err(Stop::IncorrectProgramId) => "incorrect_program_id".to_string(),
        Ok(r) => format!(
            "ok,{},{},{},{}",
            r.claimed.tokens,
            r.withheld,
            hex(&r.claimed.uva_data),
            r.claimed.event.map_or("-".to_string(), |e| hex(&e))
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
