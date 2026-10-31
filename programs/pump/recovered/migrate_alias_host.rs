//! Runs `migrate_alias.rs` on one case per stdin line. See
//! `tests/test_migrate_alias_captured.py`.
#[path = "migrate_alias.rs"]
#[allow(dead_code)]
mod migrate_alias;

use migrate_alias::{boost, run, Migration, Route, Second, Vault};
use std::io::BufRead;

fn route(text: &str) -> Route {
    match text {
        "native" => Route::Native,
        "spl" => Route::Spl,
        "t22" => Route::Token2022,
        other => panic!("route {other}"),
    }
}

fn second(text: &str) -> Second {
    match text {
        "wallet" => Second::Wallet,
        "user" => Second::User,
        "curve" => Second::Curve,
        "authority" => Second::Authority,
        "pool" => Second::Pool,
        "lp_mint" => Second::LpMint,
        "pool_base" => Second::PoolBase,
        "pool_quote" => Second::PoolQuote,
        "closed" => Second::Closed { lp: false },
        "closed_lp" => Second::Closed { lp: true },
        "pump" => Second::Pump,
        "program" => Second::Program,
        "bystander" => Second::Bystander,
        other => panic!("slot {other}"),
    }
}

fn vault(text: &str) -> Vault {
    match text {
        "right" => Vault::Right,
        "empty" => Vault::Empty,
        "pump" => Vault::Pump,
        "owner" => Vault::OtherOwner,
        "mint" => Vault::Mint,
        "other_mint" => Vault::TokenOtherMint,
        "other_authority" => Vault::TokenOtherAuthority,
        other => panic!("vault {other}"),
    }
}

fn main() {
    for line in std::io::stdin().lock().lines() {
        let line = line.unwrap();
        let f: Vec<&str> = line.split(',').collect();
        let num = |i: usize| f[i].parse::<u64>().unwrap();
        let m = Migration { route: route(f[0]), second: second(f[1]), fee: num(2), start: num(3), real_quote: num(4), creates_vault: f[7] == "1" };
        let answer = boost(f[5] == "1", vault(f[6])).and_then(|_| run(&m));
        match answer {
            Ok(paid) => println!("ok,{},{},{}", paid.user_paid, paid.key_change, paid.extra_quote),
            Err(code) => println!("error:{code}"),
        }
    }
}
