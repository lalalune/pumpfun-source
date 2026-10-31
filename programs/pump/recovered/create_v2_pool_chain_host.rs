//! Host driver for `create_v2_pool_chain.rs`, used by
//! `tests/test_create_v2_pool_chain_captured.py`. One request per line:
//! `vtr,vsr,rtr,ivqr,migration_fee,max_depth,n` followed by `n` curve
//! blocks and `n` record blocks. A curve block is
//! `depth,mayhem,complete,vt,vq,rt,rq,supply,root,valid` where `root` is
//! `sol`, `whitelisted`, `unlisted` or `listed:<reserves>`. A record block
//! is `tail,has_pool` (tail counts the accounts from the curve to the end
//! of the stream, has_pool says a pool account follows the curve) or, when
//! has_pool is 1, `tail,has_pool,key_ok,owner_ok,len,discriminator_ok,
//! base_key_ok,quote_key_ok,<base vault>,<quote vault>,adjustment` where a
//! vault is `owner_ok,len,state,account_type,amount` and describes the
//! account read in that vault slot. One answer per line:
//! `ok,<reserves>,<depth>` or `error:<code>`.
#[path = "create_v2_pool_chain.rs"]
mod create_v2_pool_chain;

use create_v2_pool_chain::{price, Curve, Global, Record, Root, Vault};
use std::io::{self, BufRead, Write};

struct Fields<'a> {
    f: Vec<&'a str>,
    at: usize,
}

impl Fields<'_> {
    fn n(&mut self) -> u64 {
        let value = self.f[self.at].parse().unwrap();
        self.at += 1;
        value
    }
    fn flag(&mut self) -> bool {
        self.n() != 0
    }
    fn vault(&mut self) -> Vault {
        Vault { owner_ok: self.flag(), len: self.n() as usize, state: self.n() as u8,
                account_type: self.n() as u8, amount: self.n() }
    }
    fn curve(&mut self) -> Curve {
        let depth = self.n() as u8;
        let mayhem = self.flag();
        let complete = self.flag();
        let (vt, vq, rt, rq, supply) = (self.n(), self.n(), self.n(), self.n(), self.n());
        let root_field = self.f[self.at];
        self.at += 1;
        let root = match root_field {
            "sol" => Root::Sol,
            "whitelisted" => Root::Whitelisted,
            "unlisted" => Root::Unlisted,
            listed => Root::Listed(listed.strip_prefix("listed:").unwrap().parse().unwrap()),
        };
        Curve { depth, mayhem, complete, virtual_token_reserves: vt, virtual_quote_reserves: vq,
                real_token_reserves: rt, real_quote_reserves: rq, token_total_supply: supply,
                root, valid: self.flag() }
    }
    fn record(&mut self) -> Option<Record> {
        let tail = self.n() as usize;
        if !self.flag() {
            // No pool account follows the curve. If the stream still has
            // four accounts from here, the next one is read as the pool and
            // fails the key check; the vault fields are never reached.
            let blank = Vault { owner_ok: false, len: 0, state: 0, account_type: 0, amount: 0 };
            return Some(Record { tail, key_ok: false, owner_ok: false, len: 0,
                                 discriminator_ok: false, base_key_ok: false, quote_key_ok: false,
                                 base: blank, quote: blank, adjustment: 0 });
        }
        let record = Record { tail, key_ok: self.flag(), owner_ok: self.flag(), len: self.n() as usize,
                              discriminator_ok: self.flag(), base_key_ok: self.flag(), quote_key_ok: self.flag(),
                              base: self.vault(), quote: self.vault(),
                              adjustment: self.f[self.at].parse().unwrap() };
        self.at += 1;
        Some(record)
    }
}

fn answer(line: &str) -> String {
    let mut fields = Fields { f: line.split(',').collect(), at: 0 };
    let global = Global {
        initial_virtual_token_reserves: fields.n(),
        initial_virtual_sol_reserves: fields.n(),
        initial_real_token_reserves: fields.n(),
        initial_virtual_quote_reserves: fields.n(),
        pool_migration_fee: fields.n(),
        max_curve_depth: fields.n() as u8,
    };
    let count = fields.n() as usize;
    let curves: Vec<Curve> = (0..count).map(|_| fields.curve()).collect();
    let records: Vec<Option<Record>> = (0..count).map(|_| fields.record()).collect();
    match price(&global, &curves, &records) {
        Ok((reserves, depth)) => format!("ok,{reserves},{depth}"),
        Err(code) => format!("error:{code}"),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
