//! Host driver for `legacy_cashback.rs`, used by
//! `tests/test_legacy_cashback_captured.py`. One request per line:
//! `side,cashback_coin,creator_fee,creator_bps,uva,uva_lamports,uva_earned,
//!  vault_lamports,slot0,slot1,slot2`
//! where `side` is `buy|sell`, `uva` is `missing|funded|valid|foreign|baddisc`,
//! and slots are `absent|curve_v2|uva|buyback|other`.
#[path = "legacy_cashback.rs"]
mod legacy_cashback;

use legacy_cashback::{Side, Slot, Trade, Uva};
use std::io::{self, BufRead, Write};

fn slot(text: &str) -> Slot {
    match text {
        "absent" => Slot::Absent,
        "curve_v2" => Slot::CurveV2,
        "uva" => Slot::Uva,
        "buyback" => Slot::Buyback,
        "other" => Slot::Other,
        _ => panic!("unknown slot {text}"),
    }
}

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let n = |i: usize| f[i].parse::<u64>().unwrap();
    let uva = match f[4] {
        "missing" => Uva::Missing,
        "funded" => Uva::Funded(n(5)),
        "valid" => Uva::Valid { lamports: n(5), cashback_earned: n(6) },
        "foreign" => Uva::ForeignOwner,
        "baddisc" => Uva::BadDiscriminator,
        other => panic!("unknown uva {other}"),
    };
    let trade = Trade {
        side: if f[0] == "buy" { Side::Buy } else { Side::Sell },
        cashback_coin: n(1) != 0,
        creator_fee: n(2),
        creator_bps: n(3),
        uva,
        vault_lamports: n(7),
        remaining: [slot(f[8]), slot(f[9]), slot(f[10])],
    };
    match legacy_cashback::route(&trade) {
        Err(code) => format!("error:{code}"),
        Ok(r) => format!(
            "ok,{},{},{},{},{},{},{},{},{}",
            r.uva_rent,
            r.uva_credit,
            r.vault_credit,
            r.vault_top_up,
            r.cashback_earned.map_or("-".to_string(), |v| v.to_string()),
            r.event_creator_bps,
            r.event_creator_fee,
            r.event_cashback_bps,
            r.event_cashback,
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
