//! Host driver for `migrate_v2.rs`, used by `tests/test_migrate_v2_captured.py`.
//! One request per line:
//! `faults,token_quote,complete,vtr,vqr,rtr,rqr,post_complete_quote_in,fee,
//!  creator_fee,protocol_fees,mayhem,cashback,creator_fee_bps,can_edit,holder,
//!  config,remaining,curve_lamports,quote_vault`
//! where `faults` is `-` or letters from `WRMAPOCLVTE` (see `fault`; `E` is
//! the pump_amm event authority), and `config` is `-` (no account) or
//! `len:disc_ok:byte`.
#[path = "migrate_v2.rs"]
mod migrate_v2;

use migrate_v2::{AmmConfig, Fault, MigrateV2, Outcome, Stop};
use std::io::{self, BufRead, Write};

fn fault(c: char) -> Fault {
    match c {
        'W' => Fault::WithdrawAuthority,
        'R' => Fault::WithdrawReadonly,
        'M' => Fault::QuoteMint,
        'A' => Fault::CurveQuoteAccount,
        'P' => Fault::Pool,
        'O' => Fault::PoolAuthorityQuoteAccount,
        'C' => Fault::AmmGlobalConfig,
        'L' => Fault::LpMint,
        'V' => Fault::PoolQuoteAccount,
        'T' => Fault::Rent,
        other => panic!("unknown fault {other}"),
    }
}

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let n = |i: usize| f[i].parse::<u64>().unwrap();
    let letters = if f[0] == "-" { "" } else { f[0] };
    let m = MigrateV2 {
        faults: letters.chars().filter(|&c| c != 'E').map(fault).collect(),
        wrong_amm_event_authority: letters.contains('E'),
        token_quote: n(1) != 0,
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
        quote_vault: n(19),
    };
    match migrate_v2::migrate_v2(&m) {
        Err(Stop::Code(code)) => format!("error:{code}"),
        Err(Stop::InvalidBool) => "borsh".to_string(),
        Err(Stop::ArithmeticOverflow) => "arith".to_string(),
        Err(Stop::CurveBelowRent) => "rent".to_string(),
        Ok(Outcome::AlreadyMigrated { curve_lamports }) => format!("noop,{curve_lamports}"),
        Ok(Outcome::Migrated { pool: p, init_boost, curve_lamports, quote_vault }) => format!(
            "ok,{},{},{},{},{},{},{},{},{}",
            p.quote_amount_in,
            p.is_mayhem_mode as u8,
            p.is_cashback_coin as u8,
            p.creator_fee_bps,
            p.can_edit_creator_fee as u8,
            p.is_holder_reward as u8,
            init_boost as u8,
            curve_lamports,
            quote_vault
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
