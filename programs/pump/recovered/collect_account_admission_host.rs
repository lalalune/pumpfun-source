//! Host driver for `collect_account_admission.rs` and
//! `creator_fee_collect.rs`, used by
//! `tests/test_collect_account_admission_captured.py`. One request per line:
//! `handler fault fault ...`, where `handler` is `v1|v2_sol|v2_spl` and a fault
//! is `<slot>.<kind>`. Answers are `error:<code>`, `error:<name>`, or
//! `ok,<lamports>,<tokens>,<event>`.
#[path = "collect_account_admission.rs"]
mod collect_account_admission;
#[allow(dead_code)]
#[path = "creator_fee_collect.rs"]
mod creator_fee_collect;

use collect_account_admission::{
    admit, native_transfer, token_transfer, Handler, MintSlot, Request, Stop, TokenProgramSlot, TokenState, VaultShape,
};
use creator_fee_collect::{collect, Collect, CollectError, Quote, MIGRATED_TO_SHARING_CONFIG, ZERO_BYTE_RENT};
use std::io::{self, BufRead, Write};

#[derive(Default)]
struct Input {
    request: Request,
    creator_fees: bool,
    creator_executable: bool,
    empty: bool,
    vault_missing: bool,
    vault_shape: VaultShape,
    source: TokenState,
    destination: TokenState,
    program_wrong: bool,
}

fn state(token: &mut TokenState, kind: &str) {
    match kind {
        "owner" => token.foreign_owner = true,
        "short" | "missing" => token.unreadable = true,
        "mintdata" => token.wrong_mint = true,
        "ownerdata" => token.wrong_authority = true,
        "frozen" => token.frozen = true,
        other => panic!("unknown token fault {other}"),
    }
}

fn parse(words: &[&str]) -> Input {
    let mut i = Input::default();
    i.request.associated_program_ok = true;
    i.request.system_program_ok = true;
    i.request.event_authority_ok = true;
    for word in words {
        let (slot, kind) = word.split_once('.').unwrap();
        let r = &mut i.request;
        match (slot, kind) {
            ("creator", "readonly") => r.creator_read_only = true,
            ("creator_token_account", "key") => r.creator_token.wrong_address = true,
            ("creator_token_account", "readonly") => r.creator_token.read_only = true,
            ("creator_token_account", k) => state(&mut i.destination, k),
            ("creator_vault", "key") => r.vault.wrong_address = true,
            ("creator_vault", "readonly") => r.vault.read_only = true,
            ("creator_vault", "owner") => i.vault_shape = VaultShape::ForeignOwner,
            ("creator_vault", "data0") => i.vault_shape = VaultShape::HoldsData,
            ("creator_vault", "missing") => i.vault_missing = true,
            ("creator_vault_token_account", "key") => r.vault_token.wrong_address = true,
            ("creator_vault_token_account", "readonly") => r.vault_token.read_only = true,
            ("creator_vault_token_account", k) => state(&mut i.source, k),
            ("quote_mint", "key") => r.mint_wrong_address = true,
            ("quote_mint", "owner") => r.mint = MintSlot::WrongOwner,
            // The owner is checked before the data is read.
            ("quote_mint", "short") if r.mint == MintSlot::Expected => r.mint = MintSlot::Short,
            ("quote_mint", "short") => {}
            ("quote_mint", "missing") => r.mint = MintSlot::Missing,
            ("quote_token_program", "key") => r.token_program = TokenProgramSlot::Invalid,
            ("quote_token_program", "t22") => r.token_program = TokenProgramSlot::OtherInterface,
            ("associated_token_program", _) => r.associated_program_ok = false,
            ("system_program", _) => r.system_program_ok = false,
            ("event_authority", _) => r.event_authority_ok = false,
            ("program", _) => i.program_wrong = true,
            ("h", "fees") => i.creator_fees = true,
            ("h", "exec") => i.creator_executable = true,
            ("h", "empty") => i.empty = true,
            other => panic!("unknown fault {other:?}"),
        }
    }
    i
}

fn stop(s: Stop) -> String {
    match s {
        Stop::Code(c) => format!("error:{c}"),
        Stop::InvalidAccountData => "error:invalid_account_data".to_string(),
        Stop::ExternalLamportSpend => "error:external_lamport_spend".to_string(),
        Stop::InvalidArgument => "error:invalid_argument".to_string(),
        Stop::ExternalDataModified => "error:external_data_modified".to_string(),
        Stop::MissingAccount => "error:missing_account".to_string(),
    }
}

fn answer(line: &str) -> String {
    let words: Vec<&str> = line.split_whitespace().collect();
    let handler = match words[0] {
        "v1" => Handler::V1,
        "v2_sol" => Handler::V2Native,
        _ => Handler::V2Token,
    };
    let i = parse(&words[1..]);
    if let Err(s) = admit(handler, &i.request) {
        return stop(s);
    }
    let token_path = handler == Handler::V2Token;
    let vault_lamports = if i.vault_missing {
        0
    } else if i.empty {
        ZERO_BYTE_RENT
    } else {
        ZERO_BYTE_RENT + 1_000_000
    };
    let vault_tokens = if i.source.unreadable {
        None
    } else if i.empty {
        Some(0)
    } else {
        Some(1_000_000)
    };
    let quote = if token_path {
        Quote::Spl { vault_tokens, creator_ata_exists: true }
    } else {
        Quote::Native
    };
    let collected = collect(&Collect {
        // An executable creator stands alone in the test: the Pump Fees owner
        // needs a data account.
        creator_owned_by_fees: i.creator_fees && !i.creator_executable,
        creator_executable: i.creator_executable,
        creator_lamports: if i.creator_executable { 0 } else { 1_000_000_000 },
        creator_data_len: 0,
        vault_lamports,
        quote,
    });
    let moved = match collected {
        Ok(moved) => moved,
        Err(CollectError::Custom(c)) => {
            debug_assert_eq!(c, MIGRATED_TO_SHARING_CONFIG);
            return format!("error:{c}");
        }
        Err(CollectError::InvalidAccountData) => return stop(Stop::InvalidAccountData),
        Err(CollectError::ArithmeticOverflow) => panic!("no overflow in these inputs"),
    };
    if moved.event {
        let transfer = if token_path {
            token_transfer(&i.source, &i.destination)
        } else {
            native_transfer(i.vault_shape)
        };
        if let Err(s) = transfer {
            return stop(s);
        }
        if i.program_wrong {
            return stop(Stop::MissingAccount);
        }
    }
    format!("ok,{},{},{}", moved.lamports, moved.tokens, u8::from(moved.event))
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
