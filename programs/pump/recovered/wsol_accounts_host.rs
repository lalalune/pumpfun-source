//! Stdin host for `wsol_accounts.rs`. One case per line:
//! `reserve-or-new,amount,unsynced`; the answer is `lamports,reserve`.

#[path = "wsol_accounts.rs"]
mod wsol_accounts;

use std::io::BufRead;

fn main() {
    for line in std::io::stdin().lock().lines() {
        let line = line.unwrap();
        let f: Vec<&str> = line.split(',').collect();
        let answer = wsol_accounts::settled(f[0].parse().ok(), f[1].parse().unwrap(), f[2].parse().unwrap());
        match answer {
            Some((lamports, reserve)) => println!("{lamports},{reserve}"),
            None => println!("overflow"),
        }
    }
}
