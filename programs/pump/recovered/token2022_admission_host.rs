//! One line in, one line out, for `tests/test_token2022_admission_captured.py`.
//!
//! In: `<family> <buy|sell> <slot> <body> <fault|-> <plain> <probe>`, where the
//! last two are `ok`, a number or a runtime error name. Out: the same form.
#[path = "token2022_admission.rs"]
mod token2022_admission;

use std::io::BufRead;
use token2022_admission::{first_stop, Body, Case, Ending, Family, Side, Slot};

fn ending(text: &str) -> Ending {
    match text {
        "ok" => Ending::Ok,
        _ => match text.parse() {
            Ok(code) => Ending::Code(code),
            Err(_) => Ending::Named(text.to_string()),
        },
    }
}

fn case(line: &str) -> Case {
    let f: Vec<&str> = line.split_whitespace().collect();
    assert_eq!(f.len(), 7, "{line}");
    Case {
        family: match f[0] {
            "legacy" => Family::Legacy,
            "v2" => Family::V2,
            "v3" => Family::V3,
            other => panic!("family {other}"),
        },
        side: if f[1] == "buy" { Side::Buy } else { Side::Sell },
        slot: match f[2] {
            "base_mint" => Slot::BaseMint,
            "quote_mint" => Slot::QuoteMint,
            "curve_base" => Slot::CurveBase,
            "user_base" => Slot::UserBase,
            "curve_quote" => Slot::CurveQuote,
            "user_quote" => Slot::UserQuote,
            "payee" => Slot::Payee,
            other => panic!("slot {other}"),
        },
        body: match f[3] {
            "extended" => Body::Extended,
            "bad_tlv" => Body::BadTlv,
            "bad_length" => Body::BadLength,
            "wrong_type" => Body::WrongType,
            "uninitialized" => Body::Uninitialized,
            "paused" => Body::Paused,
            "hook_set" => Body::HookSet,
            "frozen" => Body::Frozen,
            "cpi_guard" => Body::CpiGuard,
            "memo_required" => Body::MemoRequired,
            other => panic!("body {other}"),
        },
        fault: f[4].to_string(),
        plain: ending(f[5]),
        probe: ending(f[6]),
    }
}

fn main() {
    for line in std::io::stdin().lock().lines() {
        match first_stop(&case(&line.unwrap())) {
            Ending::Ok => println!("ok"),
            Ending::Code(code) => println!("{code}"),
            Ending::Named(name) => println!("{name}"),
        }
    }
}
