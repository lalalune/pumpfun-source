//! stdin/stdout driver for `error_sites_rest.rs`, used by
//! `tests/test_error_sites_rest_captured.py`. One case per line, tab separated:
//! `<handler>\t<kind>\t<place>\t<code>` with `<kind>` one of `thrown`, `account`,
//! `program`, `occurred`. The answer is the log line, or `unknown`.
use std::io::{self, BufRead, Write};

#[path = "error_sites_rest.rs"]
mod error_sites_rest;
use error_sites_rest::*;

fn main() {
    let stdin = io::stdin();
    let mut out = io::stdout().lock();
    for line_text in stdin.lock().lines() {
        let line_text = line_text.unwrap();
        let f: Vec<&str> = line_text.trim_end_matches('\n').split('\t').collect();
        let kind = match f[1] {
            "thrown" => Kind::Thrown,
            "account" => Kind::Account,
            "program" => Kind::Program,
            _ => Kind::Occurred,
        };
        let answer = line(f[0], kind, f[2], f[3].parse().unwrap());
        writeln!(out, "{}", answer.unwrap_or_else(|| "unknown".to_string())).unwrap();
    }
}
