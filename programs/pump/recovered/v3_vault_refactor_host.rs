#[path = "v3_vault_refactor.rs"]
mod v3_vault_refactor;
use std::io::{self, BufRead};
use v3_vault_refactor::*;

fn fill(v: &[u64]) -> Fill {
    Fill { quote: v[0], protocol_fee: v[1], creator_fee: v[2], buyback_fee: v[3] }
}

fn main() {
    for line in io::stdin().lock().lines() {
        let line = line.unwrap();
        let f: Vec<&str> = line.split(',').collect();
        match f[0] {
            // pay,q,p,c,b[,q2,p2,c2,b2]
            "pay" => {
                let v: Vec<u64> = f[1..].iter().map(|s| s.parse().unwrap()).collect();
                let post = if v.len() == 8 { Some(fill(&v[4..])) } else { None };
                match buy_payment(fill(&v[..4]), post) {
                    Ok(p) => println!("ok,{},{},{}", p.user_out, p.curve_in, p.recipient_in),
                    Err(e) => println!("error,{e}"),
                }
            }
            // admit,<native>,<base_ok>,<quote: 0 wrong address, 1 ready, 2 absent>
            "admit" => {
                let quote = match f[3] {
                    "0" => QuoteVault::WrongAddress,
                    "1" => QuoteVault::Ready,
                    "2" => QuoteVault::Absent,
                    other => panic!("unknown quote vault {other}"),
                };
                match admit_vaults(f[1] == "1", f[2] == "1", quote) {
                    Ok(()) => println!("ok"),
                    Err(r) => println!("error,{},{}", rejection_code(r), rejection_site(r)),
                }
            }
            other => panic!("unknown op {other}"),
        }
    }
}
