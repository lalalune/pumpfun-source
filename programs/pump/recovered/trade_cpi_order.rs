//! Captured order of the cross-program invocations a successful Pump trade
//! makes: legacy `buy` / `buy_exact_sol_in` / `sell`, native and token quote
//! `buy_v2` / `buy_exact_quote_in_v2` / `sell_v2`, and `buy_v3` / `sell_v3`.
//!
//! The amounts come from the existing trade models; this one only says which
//! call runs when, and which calls a zero amount drops. Checked against
//! `evidence/original/pump/deployed.so` and the captured Fees, SPL Token,
//! Token-2022 and Associated Token programs by
//! `tests/test_trade_cpi_order_captured.py`. Not linked into the SBF crate.
//! This is not a byte-identity claim.
//!
//! Lamport moves out of the program-owned curve are direct and make no CPI, so
//! a native sell's quote, fee and buyback movements do not appear here.
//!
//! Unconfirmed (미확인, outside the checked inputs): failed runs, Token-2022
//! transfer fees on v3 quotes, multi-hop swaps, and the order among a user
//! volume accumulator creation, a curve rent top-up and token account creation
//! when two of them happen in the same run.

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Family {
    Legacy,
    V2Native,
    V2Quote,
    V3Native,
    V3Quote,
}

#[derive(Debug, PartialEq, Eq)]
pub struct Trade {
    pub family: Family,
    pub buy: bool,
    pub base: u64,
    /// Quote between the user and the curve. Native v3 buys pay the gross
    /// amount here and the curve pays the buyback recipient directly.
    pub curve_quote: u64,
    pub recipient: u64,
    pub buyback: u64,
    pub creator: u64,
    /// A cashback coin credits the user volume accumulator, not the vault.
    pub cashback: bool,
    pub vault_rent: u64,
    pub curve_rent: u64,
    pub volume_account_created: bool,
    pub token_accounts_created: u64,
    /// Whitelisted v2 users skip the Fees quote; v3 reads FeeConfig directly.
    pub fee_cpi: bool,
    pub completes: bool,
}

fn side(quote: bool, name: &str) -> String {
    if quote { format!("{name}_quote") } else { name.to_string() }
}

/// Pays `name` from the user, or from the curve on a token quote sell.
fn pay(steps: &mut Vec<String>, t: &Trade, quote: bool, name: &str, amount: u64) {
    if amount == 0 {
        return;
    }
    let from = side(quote, if t.buy { "user" } else { "curve" });
    let kind = if quote { "token" } else { "system" };
    steps.push(format!("{kind}:{from}>{}:{amount}", side(quote, name)));
}

fn base_transfer(steps: &mut Vec<String>, t: &Trade) {
    let (from, to) = if t.buy { ("curve", "user") } else { ("user", "curve") };
    steps.push(format!("token:{from}_base>{to}_base:{}", t.base));
}

fn rent(steps: &mut Vec<String>, name: &str, amount: u64) {
    if amount != 0 {
        steps.push(format!("system:user>{name}:{amount}"));
    }
}

fn events(steps: &mut Vec<String>, t: &Trade) {
    steps.push("event".to_string());
    if t.completes {
        steps.push("event".to_string());
    }
}

/// Legacy and v2: Fees, base tokens, vault rent, creator, curve, then the
/// protocol split. Legacy pays the buyback first, a v2 buy pays it last, and a
/// token quote sell pays it first. Rent for the curve comes first on a sell
/// and after the events on a buy.
fn fee_quoted(t: &Trade) -> Vec<String> {
    let quote = t.family == Family::V2Quote;
    let mut steps = Vec::new();
    if t.volume_account_created {
        steps.push("init".to_string());
    }
    if !t.buy {
        rent(&mut steps, "curve", t.curve_rent);
    }
    for _ in 0..t.token_accounts_created {
        steps.push("ata".to_string());
    }
    if t.fee_cpi {
        steps.push("fees".to_string());
    }
    base_transfer(&mut steps, t);
    rent(&mut steps, "vault", t.vault_rent);
    if t.buy || quote {
        pay(&mut steps, t, quote, if t.cashback { "uva" } else { "vault" }, t.creator);
        pay(&mut steps, t, quote, if t.buy { "curve" } else { "user" }, t.curve_quote);
        if t.family == Family::Legacy || !t.buy {
            pay(&mut steps, t, quote, "buyback", t.buyback);
            pay(&mut steps, t, quote, "recipient", t.recipient);
        } else {
            pay(&mut steps, t, quote, "recipient", t.recipient);
            pay(&mut steps, t, quote, "buyback", t.buyback);
        }
    }
    events(&mut steps, t);
    if t.buy {
        rent(&mut steps, "curve", t.curve_rent);
    }
    steps
}

/// v3 has no Fees call, tops the curve up first on both sides, and has a
/// single fee recipient.
fn direct(t: &Trade) -> Vec<String> {
    let quote = t.family == Family::V3Quote;
    let mut steps = Vec::new();
    if t.volume_account_created {
        steps.push("init".to_string());
    }
    rent(&mut steps, "curve", t.curve_rent);
    base_transfer(&mut steps, t);
    if t.buy || quote {
        pay(&mut steps, t, quote, if t.buy { "curve" } else { "user" }, t.curve_quote);
    }
    if quote {
        pay(&mut steps, t, quote, "buyback", t.buyback);
    }
    events(&mut steps, t);
    steps
}

pub fn trace(t: &Trade) -> Vec<String> {
    match t.family {
        Family::V3Native | Family::V3Quote => direct(t),
        _ => fee_quoted(t),
    }
}
