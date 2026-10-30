//! stdin/stdout driver for `creator_assignment.rs`, used by
//! `tests/test_creator_assignment_captured.py`. One case per line:
//! `<op>,<signed>,<authority_ok>,<metadata>,<metadata_address_ok>,<creators>,
//! <curve_len>,<curve_address_ok>,<curve_creator>,<holder_reward>,<creator_fee>,
//! <argument>,<sharing>,
//! <sharing_address_ok>,<sharing_mint_ok>,<sharing_admin>,<sharing_key>`
//! where `<op>` is `set`, `metaplex` or `migrate`, a load state is `ok`,
//! `missing`, `owner`, `disc` or `data`, and `<creators>` is `none`, `empty`
//! or ids joined by `+`.
use std::io::{self, BufRead, Write};

#[path = "creator_assignment.rs"]
mod creator_assignment;
use creator_assignment::*;

fn state(text: &str) -> Load {
    match text {
        "ok" => Load::Ok,
        "missing" => Load::Missing,
        "owner" => Load::WrongOwner,
        "disc" => Load::BadDiscriminator,
        "data" => Load::BadData,
        other => panic!("unknown load state {other}"),
    }
}

fn creators(text: &str) -> Option<Vec<u8>> {
    match text {
        "none" => None,
        "empty" => Some(Vec::new()),
        list => Some(list.split('+').map(|id| id.parse().unwrap()).collect()),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        let line = line.unwrap();
        let f: Vec<&str> = line.split(',').collect();
        let flag = |i: usize| f[i] == "1";
        let id = |i: usize| -> u8 { f[i].parse().unwrap() };
        let case = Case {
            signed: flag(1),
            authority_ok: flag(2),
            metadata: state(f[3]),
            metadata_address_ok: flag(4),
            creators: creators(f[5]),
            curve_len: f[6].parse().unwrap(),
            curve_address_ok: flag(7),
            curve_creator: id(8),
            holder_reward: flag(9),
            creator_fee: f[10].parse().unwrap(),
            argument: id(11),
            sharing: state(f[12]),
            sharing_address_ok: flag(13),
            sharing_mint_ok: flag(14),
            sharing_admin: id(15),
            sharing_key: id(16),
        };
        let result = match f[0] {
            "set" => set_creator(&case),
            "metaplex" => set_metaplex_creator(&case),
            "migrate" => migrate_bonding_curve_creator(&case),
            other => panic!("unknown op {other}"),
        };
        let answer = match result {
            Ok(done) => {
                let event = match done.event {
                    Event::None => "none".to_string(),
                    Event::SetCreator => "set".to_string(),
                    Event::SetMetaplexCreator => "metaplex".to_string(),
                    Event::Migrate { old } => format!("migrate:{old}"),
                };
                format!("ok,{},{event}", done.creator)
            }
            Err(Stop::Code(code)) => format!("error:{code}"),
            Err(Stop::InvalidAccountData) => "invalid_data".to_string(),
            Err(Stop::BorshRead) => "borsh_read".to_string(),
            Err(Stop::BorshWrite) => "borsh_write".to_string(),
            Err(Stop::Panic) => "panic".to_string(),
        };
        writeln!(out, "{answer}").unwrap();
    }
}
