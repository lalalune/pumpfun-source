//! Host driver for `sweep_fees_token2022.rs`, used by
//! `tests/test_sweep_fees_token2022_captured.py`. One request per line:
//! `bucket,mayhem,quote_mint,creator_fee,protocol_fees,curve_lamports,recipient,
//!  recipient_lamports,token_program,mint_owner,fee,epoch,hook,pausable,
//!  non_transferable,default_frozen,curve_ata_address_ok,recipient_ata_address_ok,
//!  curve_ata,recipient_ata`
//! where `fee` is `-` or `older_bps:older_max:newer_epoch:newer_bps:newer_max`
//! and an ATA is `missing|wrong_program|truncated|uninitialized|wrong_mint` or
//! `balance:frozen:fee_extension:owner_matches:memo:cpi_guard:non_transferable`.
#[path = "sweep_fees.rs"]
#[allow(dead_code)]
mod sweep_fees;
#[path = "sweep_fees_token2022.rs"]
#[allow(dead_code)]
mod sweep_fees_token2022;

use std::io::{self, BufRead, Write};
use sweep_fees::{Bucket, QuoteMint, Recipient};
use sweep_fees_token2022::{Ata, Holding, Hook, Mint, MintOwner, Pausable, Stop, Sweep, TokenProgram, TransferFee};

fn flag(text: &str) -> bool {
    match text {
        "0" => false,
        "1" => true,
        other => panic!("flag must be 0 or 1, got {other}"),
    }
}

fn ata(text: &str) -> Ata {
    match text {
        "missing" => Ata::Missing,
        "wrong_program" => Ata::WrongProgram,
        "truncated" => Ata::Truncated,
        "uninitialized" => Ata::Uninitialized,
        "wrong_mint" => Ata::WrongMint,
        _ => {
            let f: Vec<&str> = text.split(':').collect();
            assert_eq!(f.len(), 7, "holding requires seven fields");
            Ata::Held(Holding {
                balance: f[0].parse().unwrap(),
                frozen: flag(f[1]),
                fee_extension: flag(f[2]),
                owner_matches: flag(f[3]),
                memo_required: flag(f[4]),
                cpi_guard: flag(f[5]),
                non_transferable: flag(f[6]),
            })
        }
    }
}

fn fee(text: &str) -> Option<TransferFee> {
    if text == "-" {
        return None;
    }
    let f: Vec<u64> = text.split(':').map(|v| v.parse().unwrap()).collect();
    assert_eq!(f.len(), 5, "transfer fee requires five fields");
    Some(TransferFee { older_bps: u16::try_from(f[0]).expect("older bps exceeds u16"), older_max: f[1], newer_epoch: f[2], newer_bps: u16::try_from(f[3]).expect("newer bps exceeds u16"), newer_max: f[4] })
}

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    assert_eq!(f.len(), 20, "request requires twenty columns");
    let n = |i: usize| f[i].parse::<u64>().unwrap();
    let s = Sweep {
        // Each of these columns has a closed set of documented tokens. The
        // catchalls used to read anything else as a real value, so a misspelt
        // or shifted column silently selected a different case.
        bucket: match f[0] {
            "protocol" => Bucket::Protocol,
            "creator" => Bucket::Creator,
            other => panic!("unknown bucket {other}"),
        },
        mayhem: flag(f[1]),
        quote_mint: match f[2] {
            "quote" => QuoteMint::CurveQuote,
            "other" => QuoteMint::Other,
            other => panic!("unknown quote mint {other}"),
        },
        creator_fee: n(3),
        protocol_fees: n(4),
        curve_lamports: n(5),
        recipient: match f[6] {
            "fee_recipient" => Recipient::FeeRecipient,
            "fee_list" => Recipient::FeeList,
            "reserved" => Recipient::ReservedFeeRecipient,
            "reserved_list" => Recipient::ReservedList,
            "vault" => Recipient::CreatorVault,
            "other" => Recipient::Other,
            "zero" => Recipient::Zero,
            other => panic!("unknown recipient {other}"),
        },
        recipient_lamports: n(7),
        token_program: match f[8] {
            "t22" => TokenProgram::Token2022,
            "spl" => TokenProgram::Spl,
            "other" => TokenProgram::Other,
            other => panic!("unknown token program {other}"),
        },
        mint: Mint {
            owner: match f[9] {
                "t22" => MintOwner::Token2022,
                "spl" => MintOwner::Spl,
                "other" => MintOwner::Other,
                other => panic!("unknown mint owner {other}"),
            },
            fee: fee(f[10]),
            hook: match f[12] {
                "none" => Hook::None,
                "unset" => Hook::Unset,
                "set" => Hook::Set,
                other => panic!("unknown hook {other}"),
            },
            pausable: match f[13] {
                "none" => Pausable::None,
                "running" => Pausable::Running,
                "paused" => Pausable::Paused,
                other => panic!("unknown pausable {other}"),
            },
            non_transferable: flag(f[14]),
            default_frozen: flag(f[15]),
        },
        epoch: n(11),
        curve_ata_address_ok: flag(f[16]),
        recipient_ata_address_ok: flag(f[17]),
        curve_ata: ata(f[18]),
        recipient_ata: ata(f[19]),
    };
    match sweep_fees_token2022::sweep(&s) {
        Err(Stop::Code(code)) => format!("error:{code}"),
        Err(Stop::InvalidAccountData) => "invalid_account_data".to_string(),
        Err(Stop::UninitializedAccount) => "uninitialized_account".to_string(),
        Err(Stop::IncorrectProgramId) => "incorrect_program_id".to_string(),
        Ok(r) => format!(
            "ok,{},{},{},{},{},{},{}",
            r.amount, r.withheld, r.curve_rent_top_up, r.recipient_ata_rent, r.recipient_ata_len, r.buckets.0, r.buckets.1
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
