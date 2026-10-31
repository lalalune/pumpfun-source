//! PumpSwap LP `deposit` and `withdraw`.
//!
//! A pure model of which check stops the call, the account bytes committed
//! afterwards, the event that is logged and the token / self-CPI payloads.
//! Account bodies are read from raw bytes the way the captured program reads
//! them. Owners, the user signature, writable flags and whether the pool
//! signer seeds resolve come in from the caller.
//! `tests/test_pump_amm_liquidity_captured.py` runs the same inputs on
//! `evidence/original/pump_amm/deployed.so`; agreement there is matching
//! behaviour on those inputs, not a byte-identity claim.
//!
//! Limits. Quote transfer fees are the Token-2022 config whose amount TLV sits
//! directly after the account-type byte (`kind = 2`, `len = 8`). Base mints are
//! not fee-bearing here, token accounts are not native SOL, and a pool signer
//! mismatch is reported as the caller classified it (`valid` / `invalid` /
//! `mismatch`). A non-zero effective virtual reserve scales `virtual_quote_reserves`.

pub const INSTRUCTION_FALLBACK_NOT_FOUND: u32 = 101;
pub const INSTRUCTION_DID_NOT_DESERIALIZE: u32 = 102;
pub const CONSTRAINT_MUT: u32 = 2000;
pub const CONSTRAINT_TOKEN_OWNER: u32 = 2015;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const ACCOUNT_NOT_ENOUGH_KEYS: u32 = 3005;
pub const ACCOUNT_OWNED_BY_WRONG_PROGRAM: u32 = 3007;
pub const INVALID_PROGRAM_ID: u32 = 3008;
pub const ACCOUNT_NOT_SIGNER: u32 = 3010;
pub const EXCEEDED_SLIPPAGE: u32 = 6004;
pub const UNSUPPORTED_QUOTE_MINT: u32 = 6007;
pub const INVALID_BASE_MINT: u32 = 6008;
pub const INVALID_QUOTE_MINT: u32 = 6009;
pub const INVALID_LP_MINT: u32 = 6010;
pub const INVALID_POOL_BASE: u32 = 6014;
pub const INVALID_POOL_QUOTE: u32 = 6015;
pub const DISABLED_DEPOSIT: u32 = 6018;
pub const DISABLED_WITHDRAW: u32 = 6019;
pub const OVERFLOW: u32 = 6023;
pub const TRUNCATION: u32 = 6024;
pub const DIVISION_BY_ZERO: u32 = 6025;
pub const SEED_LOCK: u32 = 6067;
pub const SELF_TRANSFER: u32 = 6087;

pub const INSUFFICIENT_FUNDS: u32 = 1;
pub const MINT_MISMATCH: u32 = 3;
pub const OWNER_MISMATCH: u32 = 4;
pub const FIXED_SUPPLY: u32 = 5;
pub const INVALID_STATE: u32 = 13;
pub const TOKEN_OVERFLOW: u32 = 14;
pub const ACCOUNT_FROZEN: u32 = 17;

pub const POOL_DISCRIMINATOR: [u8; 8] = [0xf1, 0x9a, 0x6d, 0x04, 0x11, 0xb1, 0x6d, 0xbc];
pub const CONFIG_DISCRIMINATOR: [u8; 8] = [149, 8, 156, 202, 160, 252, 176, 217];
pub const DEPOSIT_DISCRIMINATOR: [u8; 8] = [242, 35, 198, 137, 82, 225, 242, 182];
pub const WITHDRAW_DISCRIMINATOR: [u8; 8] = [183, 18, 70, 156, 148, 109, 161, 34];
pub const DEPOSIT_EVENT: [u8; 8] = [0x78, 0xf8, 0x3d, 0x53, 0x1f, 0x8e, 0x6b, 0x90];
pub const WITHDRAW_EVENT: [u8; 8] = [0x16, 0x09, 0x85, 0x1a, 0xa0, 0x2c, 0x47, 0xc0];

pub const POOL_SERIALIZED: usize = 287;
pub const CONFIG_MIN: usize = 907;

pub const OWNER_OTHER: u8 = 0;
pub const OWNER_AMM: u8 = 1;
pub const OWNER_TOKEN: u8 = 2;
pub const OWNER_TOKEN22: u8 = 3;

/// `0` the seeds derive this pool, `1` they are not a valid address,
/// `2` they derive some other address.
pub const SIGNER_OK: u8 = 0;
pub const SIGNER_INVALID: u8 = 1;
pub const SIGNER_MISMATCH: u8 = 2;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Kind {
    Deposit,
    Withdraw,
}

#[derive(Clone, Debug)]
pub struct Acc {
    pub owner: u8,
    pub writable: bool,
    pub data: Vec<u8>,
    pub key: [u8; 32],
}

#[derive(Clone, Debug)]
pub struct Call {
    pub kind: Kind,
    pub payload: Vec<u8>,
    pub count: usize,
    pub user_signer: bool,
    pub epoch: u64,
    pub timestamp: i64,
    pub signer: u8,
    pub program_ok: bool,
    pub event_ok: bool,
    pub token_ok: bool,
    pub token22_ok: bool,
    /// pool, global_config, user, base_mint, quote_mint, lp_mint,
    /// user_base, user_quote, user_lp, vault_base, vault_quote.
    pub accounts: Vec<Acc>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Moved {
    pub pool: Vec<u8>,
    pub user_base: Vec<u8>,
    pub user_quote: Vec<u8>,
    pub user_lp: Vec<u8>,
    pub vault_base: Vec<u8>,
    pub vault_quote: Vec<u8>,
    pub lp_mint: Vec<u8>,
    pub event: Vec<u8>,
    /// `(0 spl_token, 1 token-2022, 2 amm, data)`.
    pub cpi: Vec<(u8, Vec<u8>)>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Outcome {
    Error(u32),
    InvalidAccountData,
    BorshIoError,
    UninitializedAccount,
    IncorrectProgramId,
    PrivilegeEscalation,
    ProgramFailedToComplete,
    MissingAccountAfterEvent(Moved),
    BorshIoErrorAfterEvent(Moved),
    Ok(Moved),
}

#[derive(Clone, Copy)]
struct Fee {
    epoch: u64,
    max: u64,
    bps: u16,
}

struct Pool {
    lp_supply: u64,
    protocol_fees: u64,
    creator_fees: u64,
    virtual_quote: i128,
}

fn key_at(data: &[u8], at: usize) -> [u8; 32] {
    let mut out = [0u8; 32];
    out.copy_from_slice(&data[at..at + 32]);
    out
}

fn u64_at(data: &[u8], at: usize) -> u64 {
    u64::from_le_bytes(data[at..at + 8].try_into().unwrap())
}

fn put_u64(data: &mut [u8], at: usize, value: u64) {
    data[at..at + 8].copy_from_slice(&value.to_le_bytes());
}

fn flag(byte: u8) -> Result<bool, Outcome> {
    match byte {
        0 => Ok(false),
        1 => Ok(true),
        _ => Err(Outcome::BorshIoError),
    }
}

fn need(call: &Call, index: usize) -> Result<(), Outcome> {
    if call.count <= index {
        Err(Outcome::Error(ACCOUNT_NOT_ENOUGH_KEYS))
    } else {
        Ok(())
    }
}

fn acc<'a>(call: &'a Call, index: usize) -> &'a Acc {
    &call.accounts[index]
}

fn token_owned(owner: u8) -> Result<(), Outcome> {
    match owner {
        OWNER_TOKEN | OWNER_TOKEN22 => Ok(()),
        OWNER_AMM | OWNER_OTHER => Err(Outcome::Error(ACCOUNT_OWNED_BY_WRONG_PROGRAM)),
        _ => Err(Outcome::Error(ACCOUNT_OWNED_BY_WRONG_PROGRAM)),
    }
}

fn read_pool(data: &[u8]) -> Result<Pool, Outcome> {
    if data.len() < 8 || data[..8] != POOL_DISCRIMINATOR {
        return Err(Outcome::InvalidAccountData);
    }
    let n = data.len();
    if n < 211 {
        return Err(Outcome::InvalidAccountData);
    }
    let mut pool = Pool { lp_supply: u64_at(data, 203), protocol_fees: 0, creator_fees: 0, virtual_quote: 0 };
    // Length gates match `Pool::try_deserialize`. A layout that stops early leaves
    // the unread tail at zero, and only the bools that layout reads can fail.
    if n >= 244 {
        flag(data[243])?;
    }
    if n >= 245 {
        flag(data[244])?;
    }
    if n >= 261 {
        pool.virtual_quote = i128::from_le_bytes(data[245..261].try_into().unwrap());
    }
    if n >= 270 {
        flag(data[269])?;
    }
    if n >= 271 {
        flag(data[270])?;
    }
    if n >= 287 {
        pool.protocol_fees = u64_at(data, 271);
        pool.creator_fees = u64_at(data, 279);
    }
    Ok(pool)
}

fn read_config(data: &[u8]) -> Result<u8, Outcome> {
    if data.len() < 8 || data[..8] != CONFIG_DISCRIMINATOR || data.len() < CONFIG_MIN {
        return Err(Outcome::InvalidAccountData);
    }
    flag(data[417])?;
    flag(data[642])?;
    if data.len() >= 940 {
        flag(data[939])?;
    }
    if data.len() >= 949 {
        flag(data[940])?;
    }
    Ok(data[56])
}

fn read_mint(data: &[u8]) -> Result<(), Outcome> {
    if data.len() < 82 {
        return Err(Outcome::InvalidAccountData);
    }
    let tag = u32::from_le_bytes(data[0..4].try_into().unwrap());
    if tag > 1 {
        return Err(Outcome::BorshIoError);
    }
    flag(data[45])?;
    if data[45] == 0 {
        return Err(Outcome::UninitializedAccount);
    }
    let freeze = u32::from_le_bytes(data[46..50].try_into().unwrap());
    if freeze > 1 {
        return Err(Outcome::BorshIoError);
    }
    Ok(())
}

fn read_token(data: &[u8]) -> Result<(), Outcome> {
    if data.len() < 165 {
        return Err(Outcome::InvalidAccountData);
    }
    for at in [72usize, 129] {
        let tag = u32::from_le_bytes(data[at..at + 4].try_into().unwrap());
        if tag > 1 {
            return Err(Outcome::BorshIoError);
        }
    }
    let native = u32::from_le_bytes(data[109..113].try_into().unwrap());
    if native > 1 {
        return Err(Outcome::BorshIoError);
    }
    match data[108] {
        0 => Err(Outcome::UninitializedAccount),
        1 | 2 => Ok(()),
        _ => Err(Outcome::BorshIoError),
    }
}

fn mint_supply(data: &[u8]) -> u64 {
    u64_at(data, 36)
}

fn mint_decimals(data: &[u8]) -> u8 {
    data[44]
}

fn mint_authority(data: &[u8]) -> Option<[u8; 32]> {
    let tag = u32::from_le_bytes(data[0..4].try_into().unwrap());
    if tag == 1 {
        Some(key_at(data, 4))
    } else {
        None
    }
}

fn token_amount(data: &[u8]) -> u64 {
    u64_at(data, 64)
}

fn token_mint(data: &[u8]) -> [u8; 32] {
    key_at(data, 0)
}

fn token_owner(data: &[u8]) -> [u8; 32] {
    key_at(data, 32)
}

fn fee_account(data: &[u8]) -> bool {
    data.len() >= 178 && data[165] == 2 && data[166..170] == [2, 0, 8, 0]
}

fn read_fee(bytes: &[u8]) -> Fee {
    Fee {
        epoch: u64::from_le_bytes(bytes[0..8].try_into().unwrap()),
        max: u64::from_le_bytes(bytes[8..16].try_into().unwrap()),
        bps: u16::from_le_bytes(bytes[16..18].try_into().unwrap()),
    }
}

fn decode_fees(data: &[u8]) -> Result<Option<(Fee, Fee)>, ()> {
    if data.len() == 82 {
        return Ok(None);
    }
    if data.len() < 167 || data[82..165].iter().any(|b| *b != 0) || data[165] != 1 {
        return Err(());
    }
    let tlv = &data[166..];
    let mut fees = None;
    let mut offset = 0usize;
    loop {
        let remaining = tlv.get(offset..).ok_or(())?;
        if remaining.len() < 2 {
            return Ok(fees);
        }
        let kind = u16::from_le_bytes(remaining[..2].try_into().unwrap());
        if kind == 0 {
            return Ok(fees);
        }
        if remaining.len() < 4 {
            return Err(());
        }
        let length = u16::from_le_bytes(remaining[2..4].try_into().unwrap()) as usize;
        let entry = length + 4;
        let value = remaining.get(4..entry).ok_or(())?;
        if kind == 1 {
            if fees.is_some() || length < 108 {
                return Err(());
            }
            fees = Some((read_fee(&value[72..90]), read_fee(&value[90..108])));
        }
        offset = offset.checked_add(entry).ok_or(())?;
    }
}

fn quote_fee(owner: u8, data: &[u8], epoch: u64) -> Result<Option<Fee>, Outcome> {
    if owner != OWNER_TOKEN22 {
        return Ok(None);
    }
    let pair = decode_fees(data).map_err(|_| Outcome::Error(UNSUPPORTED_QUOTE_MINT))?;
    Ok(pair.map(|(older, newer)| if epoch >= newer.epoch { newer } else { older }))
}

fn ceil_div(numerator: u128, denominator: u128) -> Result<u128, Outcome> {
    if denominator == 0 {
        return Err(Outcome::Error(DIVISION_BY_ZERO));
    }
    numerator
        .checked_add(denominator)
        .ok_or(Outcome::Error(OVERFLOW))?
        .checked_sub(1)
        .ok_or(Outcome::Error(OVERFLOW))?
        .checked_div(denominator)
        .ok_or(Outcome::Error(DIVISION_BY_ZERO))
}

fn fit_u64(value: u128) -> Result<u64, Outcome> {
    u64::try_from(value).map_err(|_| Outcome::Error(TRUNCATION))
}

fn calculate_fee(fee: &Fee, amount: u64) -> Result<u64, Outcome> {
    if amount == 0 || fee.bps == 0 {
        return Ok(0);
    }
    let raw = (amount as u128)
        .checked_mul(fee.bps as u128)
        .ok_or(Outcome::Error(OVERFLOW))?
        .checked_add(10_000)
        .ok_or(Outcome::Error(OVERFLOW))?
        .checked_sub(1)
        .ok_or(Outcome::Error(OVERFLOW))?
        / 10_000;
    let raw = u64::try_from(raw).map_err(|_| Outcome::Error(OVERFLOW))?;
    Ok(raw.min(fee.max))
}

fn amount_before_fee(fee: &Fee, post: u64) -> Result<u64, Outcome> {
    let bps = fee.bps as u128;
    match (bps, post) {
        (0, _) => Ok(post),
        (_, 0) => Ok(0),
        (10_000, _) => post.checked_add(fee.max).ok_or(Outcome::Error(OVERFLOW)),
        _ => {
            let raw = ceil_div((post as u128).checked_mul(10_000).ok_or(Outcome::Error(OVERFLOW))?, 10_000 - bps)?;
            if raw.checked_sub(post as u128).ok_or(Outcome::Error(OVERFLOW))? >= fee.max as u128 {
                post.checked_add(fee.max).ok_or(Outcome::Error(OVERFLOW))
            } else {
                fit_u64(raw).map_err(|_| Outcome::Error(OVERFLOW))
            }
        }
    }
}

fn load(call: &Call) -> Result<(Pool, u8), Outcome> {
    need(call, 0)?;
    let pool_acc = acc(call, 0);
    if pool_acc.owner != OWNER_AMM {
        return Err(Outcome::Error(ACCOUNT_OWNED_BY_WRONG_PROGRAM));
    }
    let pool = read_pool(&pool_acc.data)?;
    if !pool_acc.writable {
        return Err(Outcome::Error(CONSTRAINT_MUT));
    }
    need(call, 1)?;
    let config = acc(call, 1);
    if config.owner != OWNER_AMM {
        return Err(Outcome::Error(ACCOUNT_OWNED_BY_WRONG_PROGRAM));
    }
    let flags = read_config(&config.data)?;
    need(call, 2)?;
    if !call.user_signer {
        return Err(Outcome::Error(ACCOUNT_NOT_SIGNER));
    }
    for (index, at, code) in [(3usize, 43usize, INVALID_BASE_MINT), (4, 75, INVALID_QUOTE_MINT)] {
        need(call, index)?;
        let mint = acc(call, index);
        token_owned(mint.owner)?;
        read_mint(&mint.data)?;
        if key_at(&pool_acc.data, at) != mint.key {
            return Err(Outcome::Error(code));
        }
    }
    need(call, 5)?;
    let lp = acc(call, 5);
    token_owned(lp.owner)?;
    read_mint(&lp.data)?;
    if !lp.writable {
        return Err(Outcome::Error(CONSTRAINT_MUT));
    }
    if key_at(&pool_acc.data, 107) != lp.key {
        return Err(Outcome::Error(INVALID_LP_MINT));
    }
    for index in 6..9 {
        need(call, index)?;
        let token = acc(call, index);
        token_owned(token.owner)?;
        read_token(&token.data)?;
        if !token.writable {
            return Err(Outcome::Error(CONSTRAINT_MUT));
        }
    }
    if token_owner(&acc(call, 8).data) != acc(call, 2).key {
        return Err(Outcome::Error(CONSTRAINT_TOKEN_OWNER));
    }
    for (index, at, code) in [(9usize, 139usize, INVALID_POOL_BASE), (10, 171, INVALID_POOL_QUOTE)] {
        need(call, index)?;
        let token = acc(call, index);
        token_owned(token.owner)?;
        read_token(&token.data)?;
        if !token.writable {
            return Err(Outcome::Error(CONSTRAINT_MUT));
        }
        if key_at(&pool_acc.data, at) != token.key {
            return Err(Outcome::Error(code));
        }
    }
    need(call, 11)?;
    if !call.token_ok {
        return Err(Outcome::Error(INVALID_PROGRAM_ID));
    }
    need(call, 12)?;
    if !call.token22_ok {
        return Err(Outcome::Error(INVALID_PROGRAM_ID));
    }
    need(call, 13)?;
    if !call.event_ok {
        return Err(Outcome::Error(CONSTRAINT_SEEDS));
    }
    need(call, 14)?;
    Ok((pool, flags))
}

fn program_for(owner: u8) -> u8 {
    if owner == OWNER_TOKEN { 0 } else { 1 }
}

fn require_program(owner: u8, program: u8) -> Result<(), Outcome> {
    let expect = if program == 0 { OWNER_TOKEN } else { OWNER_TOKEN22 };
    if owner == expect { Ok(()) } else { Err(Outcome::IncorrectProgramId) }
}

fn frozen(data: &[u8]) -> Result<(), Outcome> {
    if data[108] == 2 { Err(Outcome::Error(ACCOUNT_FROZEN)) } else { Ok(()) }
}

struct Xfer {
    amount: u64,
    fee: u64,
    program: u8,
    decimals: u8,
}

fn apply_transfer(
    source: &mut Vec<u8>,
    source_key: [u8; 32],
    source_owner_program: u8,
    dest: &mut Vec<u8>,
    dest_key: [u8; 32],
    dest_owner_program: u8,
    mint_key: [u8; 32],
    mint_owner: u8,
    authority: [u8; 32],
    xfer: &Xfer,
    fee_config: bool,
) -> Result<(), Outcome> {
    if xfer.amount == 0 {
        return Ok(());
    }
    let same = source_key == dest_key;
    if same && token_owner(source) != authority {
        return Err(Outcome::Error(SELF_TRANSFER));
    }
    require_program(mint_owner, xfer.program)?;
    require_program(source_owner_program, xfer.program)?;
    if !same {
        require_program(dest_owner_program, xfer.program)?;
    }
    if fee_config && (!fee_account(source) || !fee_account(dest)) {
        return Err(Outcome::Error(INVALID_STATE));
    }
    frozen(source)?;
    if !same {
        frozen(dest)?;
    }
    if token_mint(source) != mint_key || (!same && token_mint(dest) != mint_key) {
        return Err(Outcome::Error(MINT_MISMATCH));
    }
    if !same && token_owner(source) != authority {
        return Err(Outcome::Error(OWNER_MISMATCH));
    }
    let net = xfer.amount.checked_sub(xfer.fee).ok_or(Outcome::Error(OVERFLOW))?;
    if same {
        let amount = token_amount(source);
        // A same-account transfer debits the gross and credits the net.
        let amount = amount.checked_sub(xfer.amount).ok_or(Outcome::Error(INSUFFICIENT_FUNDS))?;
        let amount = amount.checked_add(net).ok_or(Outcome::Error(TOKEN_OVERFLOW))?;
        put_u64(source, 64, amount);
        if xfer.fee > 0 {
            add_withheld(source, xfer.fee)?;
        }
        *dest = source.clone();
        return Ok(());
    }
    let src = token_amount(source);
    if src < xfer.amount {
        return Err(Outcome::Error(INSUFFICIENT_FUNDS));
    }
    put_u64(source, 64, src - xfer.amount);
    let dst = token_amount(dest).checked_add(net).ok_or(Outcome::Error(TOKEN_OVERFLOW))?;
    put_u64(dest, 64, dst);
    if xfer.fee > 0 {
        add_withheld(dest, xfer.fee)?;
    }
    Ok(())
}

fn add_withheld(data: &mut [u8], fee: u64) -> Result<(), Outcome> {
    let at = 170;
    let cur = u64_at(data, at);
    put_u64(data, at, cur.checked_add(fee).ok_or(Outcome::Error(TOKEN_OVERFLOW))?);
    Ok(())
}

fn pool_signer(call: &Call) -> Result<(), Outcome> {
    match call.signer {
        SIGNER_OK => Ok(()),
        SIGNER_MISMATCH => Err(Outcome::PrivilegeEscalation),
        SIGNER_INVALID => Err(Outcome::ProgramFailedToComplete),
        _ => Err(Outcome::ProgramFailedToComplete),
    }
}

fn push_transfer(cpi: &mut Vec<(u8, Vec<u8>)>, xfer: &Xfer) {
    if xfer.amount == 0 {
        return;
    }
    let mut data = vec![12];
    data.extend_from_slice(&xfer.amount.to_le_bytes());
    data.push(xfer.decimals);
    cpi.push((xfer.program, data));
}

fn event_bytes(kind: Kind, timestamp: i64, amount: u64, base_limit: u64, quote_limit: u64, user_base: u64, user_quote: u64, pool_base: u64, pool_quote: u64, base_amount: u64, quote_amount: u64, supply: u64, pool: [u8; 32], user: [u8; 32], ub: [u8; 32], uq: [u8; 32], ul: [u8; 32], fee: u64) -> Vec<u8> {
    let mut out = Vec::with_capacity(264);
    out.extend_from_slice(if kind == Kind::Deposit { &DEPOSIT_EVENT } else { &WITHDRAW_EVENT });
    for value in [timestamp as u64, amount, base_limit, quote_limit, user_base, user_quote, pool_base, pool_quote, base_amount, quote_amount, supply] {
        out.extend_from_slice(&value.to_le_bytes());
    }
    for key in [pool, user, ub, uq, ul] {
        out.extend_from_slice(&key);
    }
    out.extend_from_slice(&fee.to_le_bytes());
    out
}

fn finish(call: &Call, pool_supply: u64, virtual_quote: i128, accounts: &mut [Vec<u8>], event: Vec<u8>, mut cpi: Vec<(u8, Vec<u8>)>) -> Outcome {
    if !call.program_ok {
        return Outcome::MissingAccountAfterEvent(moved(call, accounts, pool_supply, virtual_quote, event, cpi));
    }
    let mut tagged = vec![0xe4, 0x45, 0xa5, 0x2e, 0x51, 0xcb, 0x9a, 0x1d];
    tagged.extend_from_slice(&event);
    cpi.push((2, tagged));
    if acc(call, 0).data.len() < POOL_SERIALIZED {
        return Outcome::BorshIoErrorAfterEvent(moved(call, accounts, pool_supply, virtual_quote, event, cpi));
    }
    Outcome::Ok(moved(call, accounts, pool_supply, virtual_quote, event, cpi))
}

fn moved(call: &Call, accounts: &mut [Vec<u8>], pool_supply: u64, virtual_quote: i128, event: Vec<u8>, cpi: Vec<(u8, Vec<u8>)>) -> Moved {
    let mut pool = acc(call, 0).data.clone();
    if pool.len() >= POOL_SERIALIZED {
        put_u64(&mut pool, 203, pool_supply);
        pool[245..261].copy_from_slice(&virtual_quote.to_le_bytes());
    }
    Moved {
        pool,
        user_base: accounts[0].clone(),
        user_quote: accounts[1].clone(),
        user_lp: accounts[2].clone(),
        vault_base: accounts[3].clone(),
        vault_quote: accounts[4].clone(),
        lp_mint: accounts[5].clone(),
        event,
        cpi,
    }
}

fn scale_virtual_quote(kind: Kind, virtual_quote: i128, fees: u64, amount: u64, supply: u64) -> Result<i128, Outcome> {
    let effective = match virtual_quote.checked_add(fees as i128) {
        Some(value) => value,
        None => return Ok(virtual_quote),
    };
    if effective == 0 {
        return Ok(virtual_quote);
    }
    let magnitude = u128::try_from(effective).map_err(|_| Outcome::Error(OVERFLOW))?;
    let product = magnitude.checked_mul(amount as u128).ok_or(Outcome::Error(OVERFLOW))?;
    let change = if kind == Kind::Deposit {
        product.checked_div(supply as u128).ok_or(Outcome::Error(DIVISION_BY_ZERO))?
    } else {
        ceil_div(product, supply as u128)?
    };
    if kind == Kind::Deposit {
        let change = i128::try_from(change).map_err(|_| Outcome::Error(OVERFLOW))?;
        virtual_quote.checked_add(change).ok_or(Outcome::Error(OVERFLOW))
    } else {
        let change = u64::try_from(change).map_err(|_| Outcome::Error(TRUNCATION))?;
        virtual_quote.checked_sub(i128::from(change)).ok_or(Outcome::Error(OVERFLOW))
    }
}

pub fn liquidity(call: &Call) -> Outcome {
    let kind_disc = if call.kind == Kind::Deposit { DEPOSIT_DISCRIMINATOR } else { WITHDRAW_DISCRIMINATOR };
    if call.payload.len() < 8 || call.payload[..8] != kind_disc {
        return Outcome::Error(INSTRUCTION_FALLBACK_NOT_FOUND);
    }
    if call.payload.len() < 32 {
        return Outcome::Error(INSTRUCTION_DID_NOT_DESERIALIZE);
    }
    let amount = u64_at(&call.payload, 8);
    let base_limit = u64_at(&call.payload, 16);
    let quote_limit = u64_at(&call.payload, 24);
    let (pool, flags) = match load(call) {
        Ok(value) => value,
        Err(outcome) => return outcome,
    };
    if call.kind == Kind::Deposit && flags & 2 != 0 {
        return Outcome::Error(DISABLED_DEPOSIT);
    }
    if call.kind == Kind::Withdraw && flags & 4 != 0 {
        return Outcome::Error(DISABLED_WITHDRAW);
    }
    let lp = acc(call, 5);
    if call.kind == Kind::Withdraw && pool.lp_supply < mint_supply(&lp.data) {
        return Outcome::Error(SEED_LOCK);
    }
    let ub = acc(call, 6);
    let uq = acc(call, 7);
    let ul = acc(call, 8);
    let vb = acc(call, 9);
    let vq = acc(call, 10);
    let base_mint = acc(call, 3);
    let quote_mint = acc(call, 4);
    let user_base_reserves = token_amount(&ub.data);
    let user_quote_reserves = token_amount(&uq.data);
    let pool_base_reserves = token_amount(&vb.data);
    let pool_quote_reserves = token_amount(&vq.data);
    let accrued = match pool.protocol_fees.checked_add(pool.creator_fees) {
        Some(value) => value,
        None => return Outcome::Error(OVERFLOW),
    };
    let quote_reserve = match pool_quote_reserves.checked_sub(accrued) {
        Some(value) => value,
        None => return Outcome::Error(OVERFLOW),
    };
    let supply = pool.lp_supply;
    let (base_amount, quote_amount) = if call.kind == Kind::Deposit {
        let base_amount = match fit_u64(match ceil_div((pool_base_reserves as u128).wrapping_mul(amount as u128), supply as u128) {
            Ok(value) => value,
            Err(outcome) => return outcome,
        }) {
            Ok(value) => value,
            Err(outcome) => return outcome,
        };
        if base_limit < base_amount {
            return Outcome::Error(EXCEEDED_SLIPPAGE);
        }
        let quote_amount = match fit_u64(match ceil_div((quote_reserve as u128).wrapping_mul(amount as u128), supply as u128) {
            Ok(value) => value,
            Err(outcome) => return outcome,
        }) {
            Ok(value) => value,
            Err(outcome) => return outcome,
        };
        (base_amount, quote_amount)
    } else {
        let base_amount = match (pool_base_reserves as u128).wrapping_mul(amount as u128).checked_div(supply as u128) {
            Some(value) => match fit_u64(value) {
                Ok(value) => value,
                Err(outcome) => return outcome,
            },
            None => return Outcome::Error(DIVISION_BY_ZERO),
        };
        if base_amount < base_limit {
            return Outcome::Error(EXCEEDED_SLIPPAGE);
        }
        let quote_amount = match (quote_reserve as u128).wrapping_mul(amount as u128).checked_div(supply as u128) {
            Some(value) => match fit_u64(value) {
                Ok(value) => value,
                Err(outcome) => return outcome,
            },
            None => return Outcome::Error(DIVISION_BY_ZERO),
        };
        (base_amount, quote_amount)
    };
    let fee_cfg = match quote_fee(quote_mint.owner, &quote_mint.data, call.epoch) {
        Ok(value) => value,
        Err(outcome) => return outcome,
    };
    let (quote_transfer, quote_fee_paid) = match &fee_cfg {
        None => (quote_amount, 0),
        Some(fee) => {
            if call.kind == Kind::Deposit {
                let gross = match amount_before_fee(fee, quote_amount) {
                    Ok(value) => value,
                    Err(outcome) => return outcome,
                };
                let paid = match gross.checked_sub(quote_amount) {
                    Some(value) => value,
                    None => return Outcome::Error(OVERFLOW),
                };
                (gross, paid)
            } else {
                let paid = match calculate_fee(fee, quote_amount) {
                    Ok(value) => value,
                    Err(outcome) => return outcome,
                };
                let net = match quote_amount.checked_sub(paid) {
                    Some(value) => value,
                    None => return Outcome::Error(OVERFLOW),
                };
                if net < quote_limit {
                    return Outcome::Error(EXCEEDED_SLIPPAGE);
                }
                (quote_amount, paid)
            }
        }
    };
    if call.kind == Kind::Deposit && quote_limit < quote_transfer {
        return Outcome::Error(EXCEEDED_SLIPPAGE);
    }
    if call.kind == Kind::Withdraw && fee_cfg.is_none() && quote_amount < quote_limit {
        return Outcome::Error(EXCEEDED_SLIPPAGE);
    }

    let mut bodies = [
        ub.data.clone(),
        uq.data.clone(),
        ul.data.clone(),
        vb.data.clone(),
        vq.data.clone(),
        lp.data.clone(),
    ];
    let mut cpi = Vec::new();
    let base_prog = program_for(base_mint.owner);
    let quote_prog = program_for(quote_mint.owner);
    let base_xfer = Xfer { amount: base_amount, fee: 0, program: base_prog, decimals: mint_decimals(&base_mint.data) };
    let quote_xfer = Xfer {
        amount: quote_transfer,
        fee: quote_fee_paid,
        program: quote_prog,
        decimals: mint_decimals(&quote_mint.data),
    };
    let user_key = acc(call, 2).key;
    let pool_key = acc(call, 0).key;
    if call.kind == Kind::Deposit {
        if let Err(outcome) = transfer_slots(&mut bodies, 0, ub.key, ub.owner, 3, vb.key, vb.owner, base_mint.key, base_mint.owner, user_key, &base_xfer, false) {
            return outcome;
        }
        push_transfer(&mut cpi, &base_xfer);
        if let Err(outcome) = transfer_slots(&mut bodies, 1, uq.key, uq.owner, 4, vq.key, vq.owner, quote_mint.key, quote_mint.owner, user_key, &quote_xfer, fee_cfg.is_some()) {
            return outcome;
        }
        push_transfer(&mut cpi, &quote_xfer);
        if let Err(outcome) = pool_signer(call) {
            return outcome;
        }
        if let Err(outcome) = mint_slots(&mut bodies, true, lp, ul, pool_key, amount) {
            return outcome;
        }
        cpi.push((1, mint_data(true, amount)));
    } else {
        // Self-transfer is rejected in the program before `invoke_signed`.
        if let Err(outcome) = reject_self(&bodies[3], vb.key, ub.key, pool_key, base_amount) {
            return outcome;
        }
        if let Err(outcome) = reject_self(&bodies[4], vq.key, uq.key, pool_key, quote_transfer) {
            return outcome;
        }
        if base_amount > 0 || quote_transfer > 0 {
            if let Err(outcome) = pool_signer(call) {
                return outcome;
            }
        }
        if let Err(outcome) = transfer_slots(&mut bodies, 3, vb.key, vb.owner, 0, ub.key, ub.owner, base_mint.key, base_mint.owner, pool_key, &base_xfer, false) {
            return outcome;
        }
        push_transfer(&mut cpi, &base_xfer);
        if let Err(outcome) = transfer_slots(&mut bodies, 4, vq.key, vq.owner, 1, uq.key, uq.owner, quote_mint.key, quote_mint.owner, pool_key, &quote_xfer, fee_cfg.is_some()) {
            return outcome;
        }
        push_transfer(&mut cpi, &quote_xfer);
        if let Err(outcome) = mint_slots(&mut bodies, false, lp, ul, pool_key, amount) {
            return outcome;
        }
        cpi.push((1, mint_data(false, amount)));
    }

    let new_supply = if call.kind == Kind::Deposit {
        match pool.lp_supply.checked_add(amount) {
            Some(value) => value,
            None => return Outcome::Error(OVERFLOW),
        }
    } else {
        match pool.lp_supply.checked_sub(amount) {
            Some(value) => value,
            None => return Outcome::Error(OVERFLOW),
        }
    };
    let new_virtual_quote = match scale_virtual_quote(call.kind, pool.virtual_quote, accrued, amount, supply) {
        Ok(value) => value,
        Err(outcome) => return outcome,
    };
    let event = event_bytes(call.kind, call.timestamp, amount, base_limit, quote_limit, user_base_reserves, user_quote_reserves, pool_base_reserves, pool_quote_reserves, base_amount, quote_amount, supply, pool_key, user_key, ub.key, uq.key, ul.key, quote_fee_paid);
    finish(call, new_supply, new_virtual_quote, &mut bodies, event, cpi)
}

fn transfer_slots(
    bodies: &mut [Vec<u8>; 6],
    si: usize,
    source_key: [u8; 32],
    source_owner: u8,
    di: usize,
    dest_key: [u8; 32],
    dest_owner: u8,
    mint_key: [u8; 32],
    mint_owner: u8,
    authority: [u8; 32],
    xfer: &Xfer,
    fee_config: bool,
) -> Result<(), Outcome> {
    let mut source = bodies[si].clone();
    let mut dest = bodies[di].clone();
    apply_transfer(&mut source, source_key, source_owner, &mut dest, dest_key, dest_owner, mint_key, mint_owner, authority, xfer, fee_config)?;
    bodies[si] = source;
    if si != di {
        bodies[di] = dest;
    }
    Ok(())
}

fn mint_slots(bodies: &mut [Vec<u8>; 6], mint_to: bool, lp: &Acc, ul: &Acc, pool_key: [u8; 32], amount: u64) -> Result<(), Outcome> {
    let mut mint = bodies[5].clone();
    let mut user_lp = bodies[2].clone();
    mint_or_burn(mint_to, &mut mint, &mut user_lp, lp, ul, pool_key, amount)?;
    bodies[5] = mint;
    bodies[2] = user_lp;
    Ok(())
}

fn reject_self(source: &[u8], source_key: [u8; 32], dest_key: [u8; 32], authority: [u8; 32], amount: u64) -> Result<(), Outcome> {
    if amount > 0 && source_key == dest_key && token_owner(source) != authority {
        Err(Outcome::Error(SELF_TRANSFER))
    } else {
        Ok(())
    }
}

fn mint_data(mint_to: bool, amount: u64) -> Vec<u8> {
    let mut data = vec![if mint_to { 7 } else { 8 }];
    data.extend_from_slice(&amount.to_le_bytes());
    data
}

fn mint_or_burn(mint_to: bool, mint: &mut Vec<u8>, user_lp: &mut Vec<u8>, lp: &Acc, ul: &Acc, pool_key: [u8; 32], amount: u64) -> Result<(), Outcome> {
    require_program(lp.owner, 1)?;
    require_program(ul.owner, 1)?;
    frozen(user_lp)?;
    if token_mint(user_lp) != lp.key {
        return Err(Outcome::Error(MINT_MISMATCH));
    }
    if mint_to {
        match mint_authority(mint) {
            None => return Err(Outcome::Error(FIXED_SUPPLY)),
            Some(authority) if authority != pool_key => return Err(Outcome::Error(OWNER_MISMATCH)),
            Some(_) => {}
        }
        let supply = mint_supply(mint).checked_add(amount).ok_or(Outcome::Error(TOKEN_OVERFLOW))?;
        let balance = token_amount(user_lp).checked_add(amount).ok_or(Outcome::Error(TOKEN_OVERFLOW))?;
        put_u64(mint, 36, supply);
        put_u64(user_lp, 64, balance);
    } else {
        let balance = token_amount(user_lp);
        if balance < amount {
            return Err(Outcome::Error(INSUFFICIENT_FUNDS));
        }
        let supply = mint_supply(mint);
        if supply < amount {
            return Err(Outcome::Error(INSUFFICIENT_FUNDS));
        }
        put_u64(user_lp, 64, balance - amount);
        put_u64(mint, 36, supply - amount);
    }
    Ok(())
}
