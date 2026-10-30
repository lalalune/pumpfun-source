# w14a05-cto-sibclone: sibling clone-run idioms in admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 23322b07c (#3200), admin_cto 0.62882 (3,287 slots), fm 0.72049, rm 0.84781.
Ledger keys: `0x22a10-w14-23322b0-sibclone-*-v1`.

Every number comes from the raw-IR capture + `opt -O3` + `llc` oracle (w14a01 `capvar.sh`/`rx.py`;
the base capture equals main, `eq_main: true`). fm masks frame offsets and jump targets; rm also masks
registers (w13a50 `abs.py`).

## Which matched siblings inline AccountInfo clones

Counting inline `ldxb [acct+0x2a]` clone loads per function in the identity build (all of these are
byte-matched):

| function | inline clones |
| --- | ---: |
| `migrate_v2::create_pool` | 19 |
| `migrate_v2::init_pump_amm_boost_v2` | 15 |
| `holder_distribution::execute`, `migrate::create_pool` | 13 |
| `migrate_v2::create_token_account_v2` | 12 |
| `migrate::init_pump_amm_boost`, `payments::initialize_mayhem`, `create_v2::mint_supply` | 11 |
| `admin_cto::execute` | 19 |

Every sibling writes its CPI accounts as plain `x.to_account_info()` and LLVM inlines the derived
`AccountInfo::clone`, giving the canonical load run `ldxb +0x2a, +0x29, +0x28; ldxdw +0x20, +0x18, +0x0`.
No sibling uses `create_idempotent`, and none writes literal `AccountInfo{..}` constructors.
`collect_creator_fee.rs` and `migrate_bonding_curve_creator.rs` have no clone runs, so they are not
references for this.

## Finding: the original sharing CPI is plain `to_account_info()`

Main's sharing CPI (`admin_cto_sharing_config`) builds 5 of its 7 accounts as literal `AccountInfo{..}`
constructors with permuted field orders. These came from earlier field-order searches. Writing all seven as plain
`a.x.to_account_info()` (the `migrate::create_pool` idiom, trial **s1**):

- keeps the clones inlined (157 calls, the same as main) and the account evaluation order (0x98, 0x68, 0x0,
  0x8, 0x10, 0x90, 0xa0, 0x98);
- reproduces the original's canonical per-clone load order and its interleaving through the whole sharing
  region. orig 0x3d88-0x4a00 now differs from s1 only in register names and spill-slot offsets. The original's three dead
  reloads before the program clone (`ldxdw r1,[r10-0x920/918/910]`) also appear in s1;
- lifts **rm from 0.84781 to 0.86091** and fixes 5 of main's 6 missing spills (hist: spills -6 -> -1, reloads
  -31 -> -29).

The positional ratio drops to 0.61271 at 27,368 B (-32 B). `regmatch.py` puts the loss in the sharing region:
-37 exact tokens in orig 0x4000-0x4800 and -19 in 0x4800-0x5000. Every other bin is unchanged.
Main's literal forms matched some tokens there by coincidence, and s1 gives those matches up. Two RA effects
remain:

1. **Spill colors.** In the sharing region, s1's clone-field spill slots sit exactly 3 slots (0x18) deeper than
   the original's (`slotmap.py`: orig 0x9e8 -> s1 0xa00, 0x9f0 -> 0xa08, ...). A what-if that shifts s1's
   0x9b0-0xad8 offsets in 0x3d00-0x4960 by -0x18 gives 0.6286 (`remap.py`). That equals main, so the color offset
   alone does not win.
2. **Accounts-pointer residency.** The original spills the accounts pointer (`[r10-0x8d8]`, 34 accesses) and
   reloads it before every clone. s1 and main keep it in r7/r5. That accounts for the 32 B. Rebinding
   `a`, reading `ctx.accounts.x`, or helper boundaries do not change it: they are byte-identical to s1 or worse.

## Trials (all rejected for ratio; rm is the structural signal)

| trial | form | bytes | ratio | fm | rm |
| --- | --- | ---: | ---: | ---: | ---: |
| main 23322b0 | | 27,400 | 0.62882 | 0.72049 | 0.84781 |
| s1 | sharing CPI all `to_account_info()` | 27,368 | 0.61271 | 0.71882 | **0.86091** |
| s1t_p2 | s1 + TCF accounts `program:` as `a.pump_amm.to_account_info()` | 27,368 | 0.60432 | **0.72092** | **0.86181** |
| s1t_at / p1 / p12 / all | s1 + other TCF literal clones as `to_account_info()` | 27,368-27,384 | 0.58166-0.60132 | 0.713-0.719 | 0.860-0.862 |
| s2 / s7 | s1 in a plain or `#[inline]` nested `fn share(&Context,..)` | 27,336 | 0.60888 | 0.71506 | 0.85543 |
| s3 | s1 in `fn share(&AdminCto,..)` | 27,296 | 0.60003 | 0.70449 | 0.84647 |
| s5 | s1 as a migrate.rs `move \|signer_seeds\|` closure | 27,392 | 0.52614 | 0.67356 | 0.80779 |
| s6 | s2 with `#[inline(always)]` | = s1 | | | |
| c1-c3, c7, c8 | s1 + `ctx.accounts.x` or `let a=&ctx.accounts` rebinding in the arm | = s1 / s1t_p2 | | | |
| c4 / c5 / c6 | s1 + accounts struct, CpiContext or program bound to a local first | 27,336-27,368 | 0.52968-0.60888 | | |
| p1 | s1 + `if let Some(val)=sharing_update` | 27,360 | 0.6125 | 0.71893 | 0.86104 |
| p3 | s1 + `let bump=ctx.bumps.pool_authority` (migrate seeds) | 27,368 | 0.61151 | | 0.85971 |
| p4 | s1 + inline pool-authority seeds in the sharing call | 27,512 | 0.59441 | | |
| p6 | s1 + `match &sharing_update` | 27,360 | 0.60201 | | |
| A_/P_ knob screen | s1 / s1t_p2 + each applicable #3137 size knob (24 run) | | best 0.61333 (`sh_key_borrow`, 27,288) | | |

The TCF clone run (orig 0x2690-0x3b40) is already structurally faithful on main: main and s1 both have 36 structural
mismatches there and s1t_p2 has 30. What remains there is register assignment and spill placement.

## Tools (`tools/`)

- `side.py orig.dis cand.dis lo hi`: register-masked side-by-side alignment for an orig range (`~` = register or
  frame offset only, `!` = structural).
- `slotmap.py orig.dis cand.dis`: orig spill slot -> candidate slot votes through the masked alignment.
- `remap.py fn.bin lo hi slo shi delta`: what-if spill-offset shift, re-scored with the exact metric.
- `regmatch.py ref.bin cand.bin...`: exact-metric matched tokens per 0x800 orig bin, relative to the first file.
- `calls.py unstripped.so dis`: callee names for execute's calls.
