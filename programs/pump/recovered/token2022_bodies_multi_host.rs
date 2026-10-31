//! One line in, one line out, for `tests/test_token2022_bodies_multi_captured.py`.
//!
//! Three line forms. Endings are `ok`, a number or a runtime error name;
//! `-` stands for an input the model cannot need on that line.
//!
//! `pair <family> <buy|sell> <slot> <body> <rank> <slot> <body> <rank> <a alone> <b alone> <probe a> <probe b>`
//! `duo <family> <buy|sell> <slot> <body> <rank> <fault> <fault> <pair plain> <pair probe>`
//! `trio <family> <buy|sell> <slot> <body> <rank> <slot> <body> <rank> <fault> <fault plain> <pair captured>`
//!
//! A rank is the sub-transfer a quote destination's stop lands in (0 for
//! any other slot). Out: the ending in the same form.
#[path = "token2022_bodies_multi.rs"]
mod token2022_bodies_multi;

use std::io::BufRead;
use token2022_bodies_multi::{duo_stop, pair_stop, trio_stop, Body, DuoCase, Ending, Family, PairCase, Side, Slot, TrioCase};

fn ending(text: &str) -> Ending {
    match text {
        "ok" | "-" => Ending::Ok,
        _ => match text.parse() {
            Ok(code) => Ending::Code(code),
            Err(_) => Ending::Named(text.to_string()),
        },
    }
}

fn family(text: &str) -> Family {
    match text {
        "legacy" => Family::Legacy,
        "v2" => Family::V2,
        "v3" => Family::V3,
        other => panic!("family {other}"),
    }
}

fn side(text: &str) -> Side {
    if text == "buy" { Side::Buy } else { Side::Sell }
}

fn slot(text: &str) -> Slot {
    match text {
        "base_mint" => Slot::BaseMint,
        "quote_mint" => Slot::QuoteMint,
        "curve_base" => Slot::CurveBase,
        "user_base" => Slot::UserBase,
        "curve_quote" => Slot::CurveQuote,
        "user_quote" => Slot::UserQuote,
        "payee" => Slot::Payee,
        other => panic!("slot {other}"),
    }
}

fn body(text: &str) -> Body {
    match text {
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
        "fee_config" => Body::FeeConfig,
        "close_authority" => Body::CloseAuthority,
        "confidential_mint" => Body::ConfidentialMint,
        "default_state" => Body::DefaultState,
        "interest_bearing" => Body::InterestBearing,
        "permanent_delegate" => Body::PermanentDelegate,
        "hook_none" => Body::HookNone,
        "group_pointer" => Body::GroupPointer,
        "fee_amount" => Body::FeeAmount,
        "confidential_account" => Body::ConfidentialAccount,
        "hook_account_on" => Body::HookAccountOn,
        other => panic!("body {other}"),
    }
}

fn print(ending: Ending) {
    match ending {
        Ending::Ok => println!("ok"),
        Ending::Code(code) => println!("{code}"),
        Ending::Named(name) => println!("{name}"),
    }
}

fn main() {
    for line in std::io::stdin().lock().lines() {
        let line = line.unwrap();
        let f: Vec<&str> = line.split_whitespace().collect();
        match f[0] {
            "pair" => {
                assert_eq!(f.len(), 13, "{line}");
                print(pair_stop(&PairCase {
                    side: side(f[2]),
                    slot_a: slot(f[3]),
                    body_a: body(f[4]),
                    rank_a: f[5].parse().unwrap(),
                    slot_b: slot(f[6]),
                    body_b: body(f[7]),
                    rank_b: f[8].parse().unwrap(),
                    a_alone: ending(f[9]),
                    b_alone: ending(f[10]),
                    probe_a: ending(f[11]),
                    probe_b: ending(f[12]),
                }));
            }
            "duo" => {
                assert_eq!(f.len(), 10, "{line}");
                print(duo_stop(&DuoCase {
                    family: family(f[1]),
                    side: side(f[2]),
                    slot: slot(f[3]),
                    body: body(f[4]),
                    rank: f[5].parse().unwrap(),
                    fault_f: f[6].to_string(),
                    fault_g: f[7].to_string(),
                    pair_plain: ending(f[8]),
                    pair_probe: ending(f[9]),
                }));
            }
            "trio" => {
                assert_eq!(f.len(), 12, "{line}");
                print(trio_stop(&TrioCase {
                    family: family(f[1]),
                    side: side(f[2]),
                    slot_a: slot(f[3]),
                    body_a: body(f[4]),
                    rank_a: f[5].parse().unwrap(),
                    slot_b: slot(f[6]),
                    body_b: body(f[7]),
                    rank_b: f[8].parse().unwrap(),
                    fault: f[9].to_string(),
                    fault_plain: ending(f[10]),
                    pair_captured: ending(f[11]),
                }));
            }
            other => panic!("line kind {other}"),
        }
    }
}
