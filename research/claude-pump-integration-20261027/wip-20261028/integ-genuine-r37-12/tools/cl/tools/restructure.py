#!/usr/bin/env python3
"""coordlib round 2: genuine structure recovery for lib.rs-origin Source sites (no line padding).

Applies to a crate dir (Cargo.toml + src/) that still has the i1 layout. Moves, in the original's lib.rs item order:
  * declare_program!(pump_amm) / declare_program!(pump_fees) to the top, before #[program]   (orig lib.rs:83 / :84)
  * set_params handler body (set_params.rs execute) inline into the #[program] handler     (orig lib.rs:222..278)
  * create handler body (create.rs execute) inline into the #[program] handler              (orig lib.rs:334)
  * #[account] Global after the #[program] module + error enum, followed by impl Global     (orig 1815, 1870..1986)
  * reserved_bonding_curve_fees (trade_types.rs) after impl Global                          (orig 2562)
  * Initialize / Create / LegacyBuy #[derive(Accounts)] structs at the end of lib.rs        (orig 2778 / 2811 / 2871)
  * remaining lib.rs Accounts structs / events / helpers after them (no Source sites)
Usage: restructure.py <crate dir>
"""
import re, sys
from pathlib import Path

S = Path(sys.argv[1]) / 'src'


def rd(p):
    return (S / p).read_text()


def wr(p, t):
    (S / p).write_text(t)


def cut_block(text, start_line_pred, end_exact='}', include_prev=0):
    """cut lines [i-include_prev .. j] where i is the first line matching start_line_pred and j the first line == end_exact after i."""
    lines = text.split('\n')
    i = next(k for k, l in enumerate(lines) if start_line_pred(l))
    j = next(k for k in range(i, len(lines)) if lines[k] == end_exact)
    blk = lines[i - include_prev:j + 1]
    rest = lines[:i - include_prev] + lines[j + 1:]
    return '\n'.join(blk), '\n'.join(rest)


# ------------------------------------------------------------------ global_init.rs: Initialize -> lib.rs
g = rd('global_init.rs')
init_blk, g = cut_block(g, lambda l: l.startswith('pub struct Initialize<'), include_prev=1)
assert init_blk.startswith('#[derive(Accounts)]\npub struct Initialize'), init_blk[:60]
assert 'use crate::Global;' in g
g = g.replace('use crate::Global;', 'use crate::Initialize;', 1)
wr('global_init.rs', g)

# ------------------------------------------------------------------ create.rs: Create struct + execute body -> lib.rs
c = rd('create.rs')
create_blk, c = cut_block(c, lambda l: l.startswith('pub struct Create<'), include_prev=2)
assert create_blk.startswith('#[event_cpi]\n#[derive(Accounts)]\npub struct Create<'), create_blk[:80]
lines = c.split('\n')
i = next(k for k, l in enumerate(lines) if l.startswith('pub fn execute(ctx:Context<Create>,name:String,symbol:String,uri:String,creator:Pubkey)->Result<()>{'))
j = next(k for k in range(i, len(lines)) if lines[k] == '}')
create_body = lines[i + 1:j]
del lines[i:j + 1]
c = '\n'.join(lines)
wr('create.rs', c)
create_blk = (create_blk
              .replace("Box<Account<'info,Mint>>", "Box<Account<'info,anchor_spl::token::Mint>>")
              .replace("Box<Account<'info,TokenAccount>>", "Box<Account<'info,anchor_spl::token::TokenAccount>>")
              .replace("Program<'info,Token>", "Program<'info,anchor_spl::token::Token>")
              .replace("Program<'info,AssociatedToken>", "Program<'info,anchor_spl::associated_token::AssociatedToken>")
              .replace("Program<'info,MetadataProgram>", "Program<'info,create::MetadataProgram>"))
create_body = [l.replace(' token::mint_to(', ' anchor_spl::token::mint_to(').replace('token::MintTo{', 'anchor_spl::token::MintTo{')
               .replace(' token::set_authority(', ' anchor_spl::token::set_authority(').replace('token::SetAuthority{', 'anchor_spl::token::SetAuthority{')
               .replace(',token::spl_token::', ',anchor_spl::token::spl_token::')
               for l in create_body]
assert not any(re.search(r'(?<![:\w])token::', l) for l in create_body), [l for l in create_body if re.search(r'(?<![:\w])token::', l)]

# ------------------------------------------------------------------ buy.rs: LegacyBuy struct -> lib.rs
b = rd('buy.rs')
buy_blk, b = cut_block(b, lambda l: l.startswith('pub struct LegacyBuy<'), include_prev=1)
assert buy_blk.startswith('#[derive(Accounts)]\npub struct LegacyBuy<')
assert 'use crate::legacy_sell::{LegacyFeeConfig,LegacyFeesProgram};\n' in b
b = b.replace('use crate::legacy_sell::{LegacyFeeConfig,LegacyFeesProgram};\n', 'use crate::LegacyBuy;\n', 1)
wr('buy.rs', b)
buy_blk = (buy_blk
           .replace("InterfaceAccount<'info,Mint>", "InterfaceAccount<'info,anchor_spl::token_interface::Mint>")
           .replace("InterfaceAccount<'info,TokenAccount>", "InterfaceAccount<'info,anchor_spl::token_interface::TokenAccount>")
           .replace("Interface<'info,TokenInterface>", "Interface<'info,anchor_spl::token_interface::TokenInterface>")
           .replace("Account<'info,BondingCurve>", "Account<'info,trade_types::BondingCurve>")
           .replace("Account<'info,LegacyFeeConfig>", "Account<'info,legacy_sell::LegacyFeeConfig>")
           .replace("Program<'info,LegacyFeesProgram>", "Program<'info,legacy_sell::LegacyFeesProgram>"))

# ------------------------------------------------------------------ set_params.rs: execute body -> lib.rs handler
s = rd('set_params.rs')
lines = s.split('\n')
i = next(k for k, l in enumerate(lines) if l.startswith('pub fn execute(ctx:Context<SetParams>,'))
j = next(k for k in range(i, len(lines)) if lines[k] == '}')
sp_body = lines[i + 1:j]
del lines[i:j + 1]
wr('set_params.rs', '\n'.join(lines))

# ------------------------------------------------------------------ trade_types.rs: reserved_bonding_curve_fees -> lib.rs
t = rd('trade_types.rs')
lines = t.split('\n')
k = next(i for i, l in enumerate(lines) if l.startswith('pub fn reserved_bonding_curve_fees('))
assert lines[k - 1] == '#[inline(never)]'
j = next(i for i in range(k, len(lines)) if lines[i] == '}')
rbcf_blk = '\n'.join(lines[k - 1:j + 1]).replace('(curve: &BondingCurve)', '(curve: &trade_types::BondingCurve)')
end = j + 2 if lines[j + 1] == '' else j + 1
del lines[k - 1:end]
t = '\n'.join(lines)
assert t.startswith('use anchor_lang::prelude::*;')
t = t.replace('use anchor_lang::prelude::*;', 'use anchor_lang::prelude::*;\nuse crate::reserved_bonding_curve_fees;', 1)
wr('trade_types.rs', t)

# ------------------------------------------------------------------ lib.rs
L = rd('lib.rs')
lines = L.split('\n')
# 1. declare_program! to the top (before declare_id!)
dp = ['declare_program!(pump_amm);', 'declare_program!(pump_fees);']
for d in dp:
    assert lines.count(d) == 1, d
    lines.remove(d)
while lines and lines[-1] == '':
    lines.pop()
di = next(i for i, l in enumerate(lines) if l.startswith('declare_id!('))
lines[di:di] = dp + ['']

# 2. handler bodies inline
def handler_idx(prefix):
    return next(i for i, l in enumerate(lines) if l.startswith(prefix))

si = handler_idx('    pub fn set_params(ctx:Context<SetParams>,')
sig = lines[si]
assert sig.endswith('{set_params::execute(ctx,initial_virtual_token_reserves,initial_virtual_sol_reserves,initial_real_token_reserves,token_total_supply,fee_basis_points,withdraw_authority,enable_migrate,pool_migration_fee,creator_fee_basis_points,set_creator_authority,admin_set_creator_authority)}')
head = sig[:sig.index('->Result<()>{') + len('->Result<()>{')]
lines[si:si + 1] = [head] + ['    ' + l for l in sp_body] + ['    }']

ci = handler_idx('    pub fn create(ctx:Context<Create>,')
sig = lines[ci]
assert sig.endswith('{create::execute(ctx,name,symbol,uri,creator)}')
head = sig[:sig.index('->Result<()>{') + len('->Result<()>{')]
lines[ci:ci + 1] = [head] + ['    ' + l for l in create_body] + ['    }']

# 3. split the rest of lib.rs after the #[program] module into items
pm = handler_idx('#[program]')
pe = next(i for i in range(pm, len(lines)) if lines[i] == '}')
head_part = lines[:pe + 1]
tail = lines[pe + 1:]


def take(pred_start, end_exact='}', prev=0):
    global tail
    i = next(k for k, l in enumerate(tail) if pred_start(l))
    j = next(k for k in range(i, len(tail)) if tail[k] == end_exact)
    blk = tail[i - prev:j + 1]
    tail = tail[:i - prev] + tail[j + 1:]
    return blk

global_blk = take(lambda l: l == 'pub struct Global {', prev=1)
assert global_blk[0] == '#[account]'
impl1 = take(lambda l: l == 'impl Global {')
impl2 = take(lambda l: l == 'impl Global {')
assert any('set_buyback_basis_points' in l for l in impl1) and any('add_quote_mint' in l for l in impl2)
err_blk = take(lambda l: l == 'pub enum PumpError {', prev=1)
assert err_blk[0] == '#[error_code]'
# drop blank lines left over; keep remaining items (accounts structs, events, helpers) in their order
rest = '\n'.join(tail).strip('\n').split('\n')
rest = [l for i, l in enumerate(rest) if not (l == '' and i + 1 < len(rest) and rest[i + 1] == '')]

out = head_part + [''] + err_blk + [''] + global_blk + [''] + impl1 + [''] + impl2 + [''] + rbcf_blk.split('\n') + [''] \
    + init_blk.split('\n') + [''] + create_blk.split('\n') + [''] + buy_blk.split('\n') + [''] + rest + ['']
wr('lib.rs', '\n'.join(out))
print('restructure applied')
