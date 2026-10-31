//! Host for `same_tx.rs`: one line = limit, signatures, then `failure:units:trace:signatures:builtin:names_mint`
//! per step, split by `;` (`-` = no limit, `ok` = no failure).
#[path = "same_tx.rs"]
mod same_tx;

use same_tx::{run, Outcome, Step};
use std::io::BufRead;

fn step(text: &str) -> Step {
    let f: Vec<&str> = text.split(':').collect();
    Step {
        failure: (f[0] != "ok").then(|| f[0].to_string()),
        units: f[1].parse().unwrap(),
        trace: f[2].parse().unwrap(),
        signatures: f[3].parse().unwrap(),
        builtin: f[4] == "1",
        names_mint: f[5] == "1",
    }
}

fn main() {
    for line in std::io::stdin().lock().lines() {
        let line = line.unwrap();
        let mut parts = line.split(';');
        let limit = parts.next().unwrap();
        let limit = (limit != "-").then(|| limit.parse().unwrap());
        let signatures = parts.next().unwrap().parse().unwrap();
        let steps: Vec<Step> = parts.map(step).collect();
        match run(&steps, limit, signatures) {
            Outcome::Passed { fee, saved, units, trace } => println!("ok,{fee},{saved},{units},{trace}"),
            Outcome::Failed { index, failure, fee } => println!("fail,{index},{failure},{fee}"),
        }
    }
}
