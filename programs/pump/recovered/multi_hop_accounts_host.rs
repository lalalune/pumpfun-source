//! stdin/stdout driver for `multi_hop_accounts.rs`, used by
//! `tests/test_multi_hop_accounts_captured.py`. One case per line, four parts
//! joined by `;`: the route line of `multi_hop_route_host.rs`; the faults as
//! `name:hop` joined by `,` or `-`; curve lengths and lamports as `len:lamports`
//! joined by `,`; and the user's lamports. Answers are those of the route host,
//! with `error:invalid-data` for `InvalidAccountData`.
use std::io::{self, BufRead, Write};

#[allow(dead_code)]
#[path = "multi_hop_route.rs"]
mod multi_hop_route;
#[path = "multi_hop_accounts.rs"]
mod multi_hop_accounts;
use multi_hop_accounts::*;
use multi_hop_route::{Curve, Route};

fn list(s: &str) -> Vec<u64> {
    if s == "-" {
        return vec![];
    }
    s.split(':').map(|x| x.parse().unwrap()).collect()
}

fn parse_route(line: &str) -> Route {
    let mut blocks = line.split('|');
    let f: Vec<&str> = blocks.next().unwrap().split(',').collect();
    let n = |i: usize| f[i].parse::<u64>().unwrap();
    let curves = blocks
        .map(|b| {
            let v: Vec<u64> = b.split(',').map(|x| x.parse().unwrap()).collect();
            Curve {
                virtual_token_reserves: v[0],
                virtual_quote_reserves: v[1],
                real_token_reserves: v[2],
                real_quote_reserves: v[3],
                creator_fee: v[4],
                protocol_fees: v[5],
                has_creator: v[6] == 1,
                cashback: v[7] == 1,
                complete: v[8] == 1,
                mayhem: v[9] == 1,
                base_mint: v[10] as u8,
                quote_mint: v[11] as u8,
                base_vault: v[12],
                quote_vault: v[13],
                ..Curve::default()
            }
        })
        .collect();
    Route {
        amount_in: n(0),
        hop_fees: list(f[1]).iter().map(|&x| x as u8).collect(),
        remaining_accounts: n(2) as usize,
        source_mint: n(3) as u8,
        destination_mint: n(4) as u8,
        source_balance: n(5),
        recipient_mint: n(6) as u8,
        pool_migration_fee: n(7),
        buyback_bps: n(8),
        tier_bps: (n(9), n(10)),
        flat_bps: (n(11), n(12)),
        hops: list(f[13]).iter().map(|&x| x as usize).collect(),
        curves,
    }
}

fn top_fault(name: &str) -> Option<Top> {
    use Top::*;
    Some(match name {
        "owner:global_" => GlobalOwner,
        "tiny:global_" | "empty:global_" => GlobalNoDiscriminator,
        "disc:global_" => GlobalDiscriminator,
        "cut:global_" => GlobalBody,
        "addr:global_" => GlobalAddress,
        "owner:fee" => FeeConfigOwner,
        "tiny:fee" | "empty:fee" => FeeConfigNoDiscriminator,
        "disc:fee" => FeeConfigDiscriminator,
        "cut:fee" => FeeConfigBody,
        "addr:fee" | "bump:fee" => FeeConfigAddress,
        "nosign:amm" => AmmConfigNotSigner,
        "addr:amm" => AmmConfigAddress,
        "nosign:user" => UserNotSigner,
        "ro:user" => UserReadOnly,
        "unauth:authority" => AuthorityNotSigner,
        "owner:source" | "sys:source" => SourceOwner,
        "empty:source" | "short:source" => SourceData,
        "ro:source" => SourceReadOnly,
        "owner:destination" | "sys:destination" => DestinationOwner,
        "empty:destination" | "short:destination" => DestinationData,
        "ro:destination" => DestinationReadOnly,
        "ro:recipient" => RecipientReadOnly,
        "prog:token" => TokenProgram,
        "prog:token22" => Token2022Program,
        "prog:system" => SystemProgram,
        "prog:program" => PumpProgram,
        "addr:event" => EventAuthorityAddress,
        _ => return None,
    })
}

fn hop_fault(name: &str) -> Option<HopFault> {
    use HopFault::*;
    Some(match name {
        "owner:base_mint" => BaseMintOwner,
        "empty:base_mint" | "short:base_mint" => BaseMintData,
        "owner:quote_mint" => QuoteMintOwner,
        "empty:quote_mint" | "short:quote_mint" => QuoteMintData,
        "owner:curve" => CurveOwner,
        "disc:curve" | "tiny:curve" => CurveData,
        "owner:base_vault" | "sys:base_vault" => BaseVaultOwner,
        "empty:base_vault" | "short:base_vault" => BaseVaultData,
        "addr:curve" | "addr:base_mint" => CurveAddress,
        "ro:curve" => CurveReadOnly,
        "addr:quote_mint" => QuoteMint,
        "ro:base_vault" => BaseVaultReadOnly,
        "ro:quote_vault" => QuoteVaultReadOnly,
        "addr:base_vault" => BaseVaultAddress,
        "addr:quote_vault" => QuoteVaultAddress,
        "sys:quote_vault" => QuoteVaultSystemOwned,
        "owner:quote_vault" => QuoteVaultOwner,
        "cut:quote_vault" => QuoteVaultData,
        "tdmint:quote_vault" => QuoteVaultMint,
        "owner:recipient" | "sys:recipient" => RecipientOwner,
        "short:recipient" | "empty:recipient" => RecipientData,
        "tdmint:recipient" => RecipientMint,
        "tdzero:recipient" => RecipientNoOwner,
        "tdowner:recipient" | "stranger:recipient" => RecipientNotListed,
        "addr:recipient" => RecipientAddress,
        _ => return None,
    })
}

fn parse(line: &str) -> Case {
    let parts: Vec<&str> = line.split(';').collect();
    let mut case = Case {
        route: parse_route(parts[0]),
        top: vec![],
        hop: vec![],
        authority: vec![],
        curve_len: vec![],
        curve_lamports: vec![],
        user_lamports: parts[3].parse().unwrap(),
    };
    if parts[1] != "-" {
        for fault in parts[1].split(',') {
            let (name, hop) = fault.rsplit_once(':').unwrap();
            let hop: usize = hop.parse().unwrap();
            if let Some(t) = top_fault(name) {
                case.top.push(t);
            } else if let Some(f) = hop_fault(name) {
                case.hop.push((hop, f));
            } else {
                case.authority.push(match name {
                    "other:authority" => Authority::Source,
                    "tdowner:base_vault" => Authority::BaseVault(hop),
                    "tdowner:quote_vault" => Authority::QuoteVault(hop),
                    // Conditions no hop looks at.
                    "addr:source" | "addr:destination" | "tdowner:destination" | "nosign:authority" => continue,
                    other => panic!("unknown fault {other}"),
                });
            }
        }
    }
    for curve in parts[2].split(',') {
        let (len, lamports) = curve.split_once(':').unwrap();
        case.curve_len.push(len.parse().unwrap());
        case.curve_lamports.push(lamports.parse().unwrap());
    }
    case
}

fn main() {
    let stdin = io::stdin();
    let mut out = io::stdout().lock();
    for line in stdin.lock().lines() {
        let line = line.unwrap();
        let answer = match run(&parse(line.trim())) {
            Err(INVALID_ACCOUNT_DATA) => "error:invalid-data".to_string(),
            Err(code) => format!("error:{code}"),
            Ok(s) => {
                let mut text = format!("ok,{},{},{},{},{},{}", s.amount_out, s.buyback_fee, s.source, s.destination, s.user_lamports, s.recipient);
                for c in &s.curves {
                    text += &format!(
                        "|{},{},{},{},{},{},{},{},{},{},{},{}",
                        c.virtual_token_reserves, c.virtual_quote_reserves, c.real_token_reserves, c.real_quote_reserves,
                        c.creator_fee, c.protocol_fees, c.post_complete_base_out, c.post_complete_quote_in,
                        c.complete as u8, c.base_vault, c.quote_vault, c.lamports
                    );
                }
                text
            }
        };
        writeln!(out, "{answer}").unwrap();
    }
}
