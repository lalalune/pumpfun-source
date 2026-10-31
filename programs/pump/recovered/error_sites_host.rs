//! Host driver for `error_sites.rs`, used by `tests/test_error_sites_captured.py`.
//! One request per line, tab-separated:
//! `line,handler,kind,place,code` with `kind` = `thrown|account|program|occurred`;
//! `sites,handler,code`; `error,code`.
#[path = "error_sites.rs"]
mod error_sites;

use error_sites::Kind;
use std::io::{self, BufRead, Write};

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split('\t').collect();
    match f[0] {
        "line" => {
            let kind = match f[2] {
                "thrown" => Kind::Thrown,
                "account" => Kind::Account,
                "program" => Kind::Program,
                _ => Kind::Occurred,
            };
            error_sites::line(f[1], kind, f[3], f[4].parse().unwrap()).unwrap_or_else(|| "unknown".to_string())
        }
        "sites" => error_sites::thrown_sites(f[1], f[2].parse().unwrap()).join(","),
        _ => match error_sites::name_and_message(f[1].parse().unwrap()) {
            Some((name, message)) => format!("{name}\t{message}"),
            None => "unknown".to_string(),
        },
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim_end_matches('\n'))).unwrap();
    }
}
