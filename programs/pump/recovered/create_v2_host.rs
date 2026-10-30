//! Host driver for `create_v2.rs`, used by `tests/test_create_v2_captured.py`.
//! One request per line:
//! `faults,mayhem_byte,tail,creator_zero,name,symbol,uri,quote,quote_owner_wrong,
//!  quote_ata_wrong,quote_ata_exists,mayhem_params,create_v2,mayhem_on,holder_on,
//!  configurable,max_bps,max_depth,vtr,vsr,rtr,supply,ivqr,migration_fee`
//! where `faults` is `-` or letters (see `fault`), `tail` is hex or `-`, the
//! strings are byte lengths, and `quote` is a name (see `quote`), `listed:N`,
//! or `curve:depth:mayhem:complete:vt:vq:rt:rq:supply:root` with `root` one of
//! `sol|whitelisted|unlisted|N` (a listed root with reserves N).
#[path = "create_v2.rs"]
mod create_v2;

use create_v2::{Create, Fault, Global, Quote, QuoteCurve, QuoteMint, Root, Stop};
use std::io::{self, BufRead, Write};

fn fault(letter: char) -> Fault {
    match letter {
        'g' => Fault::GlobalMissing,
        'B' => Fault::GlobalBadBool,
        'X' => Fault::SystemProgram,
        'P' => Fault::TokenProgram,
        'I' => Fault::AssociatedTokenProgram,
        'U' => Fault::MintInUse,
        'A' => Fault::MintAuthority,
        'C' => Fault::BondingCurve,
        'T' => Fault::CurveAta,
        'Y' => Fault::MayhemProgram,
        'Q' => Fault::GlobalParams,
        'V' => Fault::SolVault,
        'S' => Fault::MayhemState,
        'E' => Fault::EventAuthority,
        'R' => Fault::MayhemReadOnly,
        other => panic!("unknown fault {other}"),
    }
}

fn quote(text: &str) -> Quote {
    let f: Vec<&str> = text.split(':').collect();
    let n = |i: usize| f[i].parse::<u64>().unwrap();
    match f[0] {
        "none" => Quote::None,
        "short" => Quote::TooFewAccounts,
        "badprogram" => Quote::WrongProgram,
        "noexec" => Quote::ProgramNotExecutable,
        "native" => Quote::NativeMint,
        "blocked" => Quote::BlockedMint,
        "whitelisted" => Quote::Whitelisted,
        "listed" => Quote::Listed(n(1)),
        "ctl_absent" => Quote::ControlAbsent,
        "ctl_key" => Quote::ControlWrongKey,
        "ctl_owner" => Quote::ControlWrongOwner,
        "unlisted" => Quote::Unlisted,
        "curve_invalid" => Quote::QuoteCurveInvalid,
        "curve" => Quote::QuoteCurve(QuoteCurve {
            depth: n(1) as u8,
            mayhem: n(2) != 0,
            complete: n(3) != 0,
            virtual_token_reserves: n(4),
            virtual_quote_reserves: n(5),
            real_token_reserves: n(6),
            real_quote_reserves: n(7),
            token_total_supply: n(8),
            root: match f[9] {
                "sol" => Root::Sol,
                "whitelisted" => Root::Whitelisted,
                "unlisted" => Root::Unlisted,
                _ => Root::Listed(n(9)),
            },
        }),
        other => panic!("unknown quote {other}"),
    }
}

fn hex(text: &str) -> Vec<u8> {
    if text == "-" {
        return Vec::new();
    }
    (0..text.len() / 2).map(|i| u8::from_str_radix(&text[2 * i..2 * i + 2], 16).unwrap()).collect()
}

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let n = |i: usize| f[i].parse::<u64>().unwrap();
    let c = Create {
        faults: if f[0] == "-" { Vec::new() } else { f[0].chars().map(fault).collect() },
        mayhem_byte: n(1) as u8,
        tail: hex(f[2]),
        creator_is_zero: n(3) != 0,
        name_bytes: n(4) as usize,
        symbol_bytes: n(5) as usize,
        uri_bytes: n(6) as usize,
        quote: quote(f[7]),
        quote_owner_wrong: n(8) != 0,
        quote_ata_wrong: n(9) != 0,
        quote_ata_exists: n(10) != 0,
        mayhem_params: n(11) != 0,
        global: Global {
            create_v2_enabled: n(12) != 0,
            mayhem_mode_enabled: n(13) != 0,
            is_holder_reward_enabled: n(14) != 0,
            creator_fee_configurable: n(15) != 0,
            max_configurable_creator_fee_bps: n(16),
            max_curve_depth: n(17) as u8,
            initial_virtual_token_reserves: n(18),
            initial_virtual_sol_reserves: n(19),
            initial_real_token_reserves: n(20),
            token_total_supply: n(21),
            initial_virtual_quote_reserves: n(22),
            pool_migration_fee: n(23),
        },
    };
    match create_v2::create_v2(&c) {
        Err(Stop::Code(code)) => format!("error:{code}"),
        Err(Stop::MissingAccount) => "missing".to_string(),
        Err(Stop::IllegalOwner) => "illegal_owner".to_string(),
        Ok(r) => format!(
            "ok,{},{},{},{},{},{},{},{},{},{},{},{}",
            r.virtual_token_reserves,
            r.virtual_quote_reserves,
            r.real_token_reserves,
            r.token_total_supply,
            r.initial_virtual_quote_reserves,
            (r.quote_mint == QuoteMint::Passed) as u8,
            r.creator_fee_bps,
            r.depth,
            r.mayhem as u8,
            r.holder_reward as u8,
            r.minted,
            r.quote_ata as u8,
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
