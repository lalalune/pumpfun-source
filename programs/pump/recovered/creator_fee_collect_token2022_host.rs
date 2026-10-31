//! Host driver for `creator_fee_collect_token2022.rs`, used by
//! `tests/test_creator_fee_collect_token2022_captured.py`. One request per line:
//! `creator_owned_by_fees,creator_executable,token_program,mint_owner,fee,epoch,
//!  hook_set,paused,addresses_ok,vault_ata,creator_ata`
//! where `fee` is `-` or `older_bps:older_max:newer_epoch:newer_bps:newer_max`
//! and an ATA is `missing|truncated|uninitialized` or `[wrong:]` followed by
//! `balance:frozen:fee_extension:owner_matches:mint_matches:memo:cpi_guard:non_transferable`.
#[path = "creator_fee_collect.rs"]
#[allow(dead_code)]
mod creator_fee_collect;
#[path = "creator_fee_collect_token2022.rs"]
#[allow(dead_code)]
mod creator_fee_collect_token2022;

use creator_fee_collect_token2022::{Ata, CollectToken2022, Holding, Mint, MintOwner, Stop, TokenProgram, TransferFee};
use std::io::{self, BufRead, Write};

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
    let c = CollectToken2022 {
        creator_owned_by_fees: n(0) != 0,
        creator_executable: n(1) != 0,
        token_program: match f[2] {
            "t22" => TokenProgram::Token2022,
            "spl" => TokenProgram::Spl,
            _ => TokenProgram::Other,
        },
        mint: Mint {
            owner: match f[3] {
                "t22" => MintOwner::Token2022,
                "spl" => MintOwner::Spl,
                _ => MintOwner::Other,
            },
            fee: fee(f[4]),
            hook_set: n(6) != 0,
            paused: n(7) != 0,
        },
        epoch: n(5),
        addresses_ok: n(8) != 0,
        vault_ata: ata(f[9]),
        creator_ata: ata(f[10]),
    };
    match creator_fee_collect_token2022::collect(&c) {
        Err(Stop::Code(code)) => format!("error:{code}"),
        Err(Stop::InvalidAccountData) => "invalid_account_data".to_string(),
        Err(Stop::UninitializedAccount) => "uninitialized_account".to_string(),
        Err(Stop::IncorrectProgramId) => "incorrect_program_id".to_string(),
        Ok(r) => format!("ok,{},{},{}", r.tokens, r.withheld, u8::from(r.event)),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
