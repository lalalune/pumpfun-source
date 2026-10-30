//! Line host for `creator_fee_distribution_quote.rs`, used by
//! `tests/test_creator_fee_distribution_quote_captured.py`.
//!
//! Input: `vault_tokens|-,active,creator_fee,curve_creator_ok,config_mint_ok,quote_mint_ok,initialize_ata,holders`
//! where holders is `;`-separated `bps:wallet:ata`, wallet in
//! `ok|wrong|exec|-` and ata in `exists|absent|wrong|-` (`-` = slot not passed).
//! Output: `ok,distributed,payer_ata_rent,t1;t2;...` or `error:<code|invalid_account_data>`.

#[path = "creator_fee_distribution_quote.rs"]
mod creator_fee_distribution_quote;

use creator_fee_distribution_quote::{distribute, Ata, Failure, QuoteDistribution, Shareholder, Wallet};
use std::io::{self, BufRead, Write};

fn parse(line: &str) -> QuoteDistribution {
    let f: Vec<&str> = line.split(',').collect();
    let num = |s: &str| s.parse::<u64>().expect("number");
    let shareholders = f[7]
        .split(';')
        .filter(|s| !s.is_empty())
        .map(|s| {
            let p: Vec<&str> = s.split(':').collect();
            Shareholder {
                bps: p[0].parse().expect("bps"),
                wallet: match p[1] {
                    "ok" => Some(Wallet::Ok),
                    "wrong" => Some(Wallet::Wrong),
                    "exec" => Some(Wallet::Executable),
                    _ => None,
                },
                ata: match p[2] {
                    "exists" => Some(Ata::Exists),
                    "absent" => Some(Ata::Absent),
                    "wrong" => Some(Ata::Wrong),
                    _ => None,
                },
            }
        })
        .collect();
    QuoteDistribution {
        vault_tokens: if f[0] == "-" { None } else { Some(num(f[0])) },
        active: f[1] == "1",
        creator_fee: num(f[2]),
        curve_creator_is_config: f[3] == "1",
        config_mint_matches: f[4] == "1",
        quote_mint_matches: f[5] == "1",
        initialize_ata: f[6] == "1",
        shareholders,
    }
}

fn main() {
    let stdin = io::stdin();
    let mut out = io::stdout().lock();
    for line in stdin.lock().lines() {
        let line = line.expect("line");
        let answer = match distribute(&parse(line.trim())) {
            Ok(d) => {
                let t: Vec<String> = d.transfers.iter().map(u64::to_string).collect();
                format!("ok,{},{},{}", d.distributed, d.payer_ata_rent(), t.join(";"))
            }
            Err(Failure::Custom(code)) => format!("error:{code}"),
            Err(Failure::InvalidAccountData) => "error:invalid_account_data".to_string(),
        };
        writeln!(out, "{answer}").expect("write");
    }
}
