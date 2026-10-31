//! Stdin host for `distribution_alias.rs`. One case per line:
//! `v1|payer,vault,curve,config,mint,ea,h0,h1|slots` or
//! `v2|tokens|init|roles with a token account|slots`, where slots are
//! `role:bps:w` or `role:bps:r`, joined by `;`.

#[path = "distribution_alias.rs"]
mod distribution_alias;

use distribution_alias::*;
use std::io::BufRead;

const NAMES: [&str; ROLES] = ["payer", "vault", "curve", "config", "mint", "ea", "h0", "h1", "pump", "system"];
const ALL: [Role; ROLES] = [Role::Payer, Role::Vault, Role::Curve, Role::Config, Role::Mint, Role::EventAuthority,
                            Role::Holder0, Role::Holder1, Role::Program, Role::System];

fn role(name: &str) -> Role {
    ALL[NAMES.iter().position(|n| *n == name).unwrap()]
}

fn slots(text: &str) -> Vec<Slot> {
    text.split(';').filter(|s| !s.is_empty()).map(|s| {
        let parts: Vec<&str> = s.split(':').collect();
        Slot { role: role(parts[0]), bps: parts[1].parse().unwrap(), writable: parts[2] == "w" }
    }).collect()
}

fn stop(s: &Stop) -> String {
    match s {
        Stop::Code(code) => format!("error:{code}"),
        Stop::PrivilegeEscalation => "PrivilegeEscalation".into(),
        Stop::IllegalOwner => "IllegalOwner".into(),
    }
}

fn numbers(values: &[u64]) -> String {
    values.iter().map(u64::to_string).collect::<Vec<_>>().join(",")
}

fn main() {
    for line in std::io::stdin().lock().lines() {
        let line = line.unwrap();
        let f: Vec<&str> = line.split('|').collect();
        let answer = if f[0] == "v1" {
            let held: Vec<u64> = f[1].split(',').map(|v| v.parse().unwrap()).collect();
            let list = slots(f[2]);
            let mut balances = [0u64; ROLES];
            balances[..8].copy_from_slice(&held);
            let mut data_len = [0u64; ROLES];
            data_len[Role::Curve as usize] = 166;
            data_len[Role::Config as usize] = 80 + 34 * list.len() as u64;
            data_len[Role::Mint as usize] = 82;
            match distribute(&Lamports { balances, data_len }, &list) {
                Ok(p) => format!("ok,{},{},{}", p.distributed, u8::from(p.event), numbers(&p.balances[..8])),
                Err(s) => stop(&s),
            }
        } else {
            let mut ata_exists = [false; ROLES];
            ata_exists[Role::Vault as usize] = true;
            for name in f[3].split(',').filter(|s| !s.is_empty()) {
                ata_exists[role(name) as usize] = true;
            }
            let tokens = Tokens { vault_tokens: f[1].parse().unwrap(), ata_exists, initialize_ata: f[2] == "1" };
            match distribute_tokens(&tokens, &slots(f[4])) {
                Ok(p) => format!("ok,{},{},{}", p.distributed, p.created, numbers(&p.balances[..8])),
                Err(s) => stop(&s),
            }
        };
        println!("{answer}");
    }
}
