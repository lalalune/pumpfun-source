//! Host driver for `error_log_left_right.rs`, used by
//! `tests/test_error_log_left_right_captured.py`. One request per line,
//! tab-separated: `forms,handler,kind,place,code` answers the two side forms
//! a site logs; `block,handler,kind,place,code,left,right` answers the logged
//! block, tab-joined, when the site is in the table and every constant side
//! equals the value given. `kind` = `thrown|account|program|occurred`.
#[path = "error_log_left_right.rs"]
mod error_log_left_right;

use error_log_left_right::Kind;
use std::io::{self, BufRead, Write};

fn kind(name: &str) -> Kind {
    match name {
        "thrown" => Kind::Thrown,
        "account" => Kind::Account,
        "program" => Kind::Program,
        _ => Kind::Occurred,
    }
}

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split('\t').collect();
    match f[0] {
        "forms" => match error_log_left_right::forms(f[1], kind(f[2]), f[3], f[4].parse().unwrap()) {
            Some((left, right)) => format!("{},{}", left.form(), right.form()),
            None => "unknown".to_string(),
        },
        "block" => error_log_left_right::block(f[1], kind(f[2]), f[3], f[4].parse().unwrap(), f[5], f[6])
            .unwrap_or_else(|| "unknown".to_string()),
        _ => "unknown".to_string(),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim_end_matches('\n'))).unwrap();
    }
}
