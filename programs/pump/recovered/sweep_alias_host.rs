//! Stdin host for `sweep_alias.rs`. One case per line:
//! `role,native,mayhem,wrong_quote,real_quote,creator_fee,protocol_fees,curve_lamports,recipient_lamports,curve_ata,recipient_ata`.

#[allow(dead_code)]
#[path = "sweep_fees.rs"]
mod sweep_fees;
#[path = "sweep_alias.rs"]
mod sweep_alias;

use std::io::BufRead;
use sweep_alias::{sweep_alias as run, AliasStop, Case, Role};
use sweep_fees::Stop;

fn main() {
    for line in std::io::stdin().lock().lines() {
        let line = line.unwrap();
        let f: Vec<&str> = line.split(',').collect();
        let role = match f[0] {
            "payer" => Role::Payer,
            "curve" => Role::Curve,
            "ea" => Role::EventAuthority,
            "pump" => Role::Program,
            "zero" => Role::Zero,
            _ => Role::Ordinary,
        };
        let n = |i: usize| f[i].parse::<u64>().unwrap();
        let case = Case {
            role,
            native: f[1] == "1",
            mayhem: f[2] == "1",
            wrong_quote: f[3] == "1",
            real_quote: n(4),
            creator_fee: n(5),
            protocol_fees: n(6),
            curve_lamports: n(7),
            recipient_lamports: n(8),
            curve_quote_ata: n(9),
            recipient_quote_ata_exists: f[10] == "1",
        };
        let answer = match run(&case) {
            Ok(m) => format!(
                "ok,{},{},{},{},{},{},{}",
                m.swept.amount, m.payer_spends, m.payer_gets, m.curve_after, m.recipient_after, m.tokens, m.swept.buckets.1
            ),
            Err(AliasStop::Code(code)) | Err(AliasStop::Base(Stop::Code(code))) => format!("error:{code}"),
            Err(AliasStop::Base(Stop::ArithmeticOverflow)) => "ArithmeticOverflow".into(),
            Err(AliasStop::Base(Stop::CurveBelowRent)) => "InsufficientFundsForRent".into(),
            Err(AliasStop::UnbalancedInstruction) => "UnbalancedInstruction".into(),
        };
        println!("{answer}");
    }
}
