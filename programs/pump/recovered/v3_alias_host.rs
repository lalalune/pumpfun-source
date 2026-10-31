//! Stdin host for `v3_alias.rs`. One case per line:
//! `role,native,sell,user_base_is_curves,user_quote_is_curves,baseline`, where
//! the baseline is `error:<code>` or
//! `user_quote:curve_quote:recipient:rent_top_up:base_moved`.

#[path = "v3_alias.rs"]
mod v3_alias;

use std::io::BufRead;
use v3_alias::*;

fn main() {
    for line in std::io::stdin().lock().lines() {
        let line = line.unwrap();
        let f: Vec<&str> = line.split(',').collect();
        let role = match f[0] {
            "user" => Role::User,
            "curve" => Role::Curve,
            "ea" => Role::EventAuthority,
            "pump" => Role::Program,
            "zero" => Role::Zero,
            _ => Role::Ordinary,
        };
        let baseline = match f[5].strip_prefix("error:") {
            Some(code) => Err(code.parse().unwrap()),
            None => {
                let v: Vec<i128> = f[5].split(':').map(|x| x.parse().unwrap()).collect();
                Ok(Settled { user_quote: v[0], curve_quote: v[1], recipient: v[2], rent_top_up: v[3], base_moved: v[4] })
            }
        };
        let case = Case {
            role,
            native: f[1] == "1",
            sell: f[2] == "1",
            user_base_is_curves: f[3] == "1",
            user_quote_is_curves: f[4] == "1",
            baseline,
        };
        match trade(&case) {
            Ok(m) => println!(
                "ok,{},{},{},{},{},{},{},{}",
                m.user_lamports, m.curve_lamports, m.recipient_lamports, m.user_base, m.curve_base, m.user_quote,
                m.curve_quote, m.recipient_quote
            ),
            Err(Stop::Code(code)) => println!("error:{code}"),
            Err(Stop::UnbalancedInstruction) => println!("UnbalancedInstruction"),
        }
    }
}
