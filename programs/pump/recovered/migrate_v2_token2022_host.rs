//! Host driver for `migrate_v2_token2022.rs`, used by
//! `tests/test_migrate_v2_token2022_captured.py`. One request per line: the
//! fields of `migrate_v2_host.rs` (`faults` stays `-`), then
//! `program,mint_owner,malformed_layout,malformed_extensions,fee,epoch,hook_set,paused,mint_non_transferable,
//!  mint_writable,vault_held,pool_authority`
//! where a program is `t22|spl`, `fee` is `-` or
//! `older_bps:older_max:newer_epoch:newer_bps:newer_max`, and an account is
//! `missing` or `frozen:fee_extension:memo:cpi_guard:non_transferable:hook_extension`.
//! Answers: `error:<code>`, `borsh`, `arith`, `rent`, an instruction error name,
//! `noop,<curve lamports>`, or `ok,<init_boost>,<curve lamports>,<vault>,<moved>,
//! <withheld>,<quote>,<closed>,<pool quote size>,<harvested>`.
#[path = "migrate_v2.rs"]
#[allow(dead_code)]
mod migrate_v2;
#[path = "migrate_v2_token2022.rs"]
#[allow(dead_code)]
mod migrate_v2_token2022;

use migrate_v2::{AmmConfig, MigrateV2, Stop as BaseStop};
use migrate_v2_token2022::{Holding, Migrated, MigrateToken2022, Mint, Stop, TransferFee};
use std::io::{self, BufRead, Write};

fn holding(text: &str) -> Holding {
    let f: Vec<u64> = text.split(':').map(|v| v.parse().unwrap()).collect();
    Holding {
        frozen: f[0] != 0,
        fee_extension: f[1] != 0,
        memo_required: f[2] != 0,
        cpi_guard: f[3] != 0,
        non_transferable: f[4] != 0,
        hook_extension: f[5] != 0,
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
    let m = MigrateToken2022 {
        base: MigrateV2 {
            faults: Vec::new(),
            wrong_amm_event_authority: false,
            token_quote: true,
            complete: n(2) as u8,
            virtual_token_reserves: n(3),
            virtual_quote_reserves: n(4),
            real_token_reserves: n(5),
            real_quote_reserves: n(6),
            post_complete_quote_in: n(7),
            pool_migration_fee: n(8),
            creator_fee: n(9),
            protocol_fees: n(10),
            is_mayhem_mode: n(11) != 0,
            is_cashback_coin: n(12) != 0,
            creator_fee_bps: n(13),
            can_edit_creator_fee: n(14) != 0,
            is_holder_reward: n(15) != 0,
            amm_config: if f[16] == "-" {
                None
            } else {
                let c: Vec<u64> = f[16].split(':').map(|x| x.parse().unwrap()).collect();
                Some(AmmConfig { len: c[0] as usize, discriminator_ok: c[1] != 0, boost_byte: c[2] as u8 })
            },
            remaining_accounts: n(17) as usize,
            curve_lamports: n(18),
            quote_vault: u64::MAX,
        },
        vault_balance: n(19),
        mint: Mint {
            owner_matches_program: f[20] == f[21],
            spl_program: f[20] == "spl",
            malformed_layout: n(22) != 0,
            malformed_extensions: n(23) != 0,
            fee: fee(f[24]),
            hook_set: n(26) != 0,
            paused: n(27) != 0,
            non_transferable: n(28) != 0,
            writable: n(29) != 0,
        },
        epoch: n(25),
        vault: holding(f[30]),
        pool_authority: if f[31] == "missing" { None } else { Some(holding(f[31])) },
    };
    match migrate_v2_token2022::migrate(&m) {
        Err(Stop::Code(code) | Stop::Base(BaseStop::Code(code))) => format!("error:{code}"),
        Err(Stop::Base(BaseStop::InvalidBool)) => "borsh".to_string(),
        Err(Stop::Base(BaseStop::ArithmeticOverflow)) => "arith".to_string(),
        Err(Stop::Base(BaseStop::CurveBelowRent)) => "rent".to_string(),
        Err(other) => format!("{other:?}"),
        Ok(Migrated::AlreadyMigrated { curve_lamports }) => format!("noop,{curve_lamports}"),
        Ok(Migrated::Moved(r)) => format!(
            "ok,{},{},{},{},{},{},{},{},{}",
            r.init_boost as u8,
            r.curve_lamports,
            r.vault,
            r.moved,
            r.withheld,
            r.quote,
            r.closed as u8,
            r.pool_quote_size,
            r.harvested
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
