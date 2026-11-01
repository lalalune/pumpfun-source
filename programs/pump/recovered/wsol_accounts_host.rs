//! Stdin host for `wsol_accounts.rs`. One case per line:
//! `reserve-or-new,amount,unsynced`; the answer is `lamports,reserve`.

#[path = "wsol_accounts.rs"]
mod wsol_accounts;

use std::io::BufRead;

fn main() {
    for line in std::io::stdin().lock().lines() {
        let line = line.unwrap();
        let f: Vec<&str> = line.split(',').collect();
        // `new` is the only spelling for a token account the call creates. A
        // `.ok()` here read every malformed reserve as `new` too, and the rent
        // it defaults to is the value most cases carry anyway, so a broken case
        // answered exactly like a valid one.
        let reserve = match f[0] {
            "new" => None,
            held => Some(held.parse().unwrap()),
        };
        let answer = wsol_accounts::settled(reserve, f[1].parse().unwrap(), f[2].parse().unwrap());
        match answer {
            Some((lamports, reserve)) => println!("{lamports},{reserve}"),
            None => println!("overflow"),
        }
    }
}
