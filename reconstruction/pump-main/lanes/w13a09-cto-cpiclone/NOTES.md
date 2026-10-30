# Lane w13a09-cto-cpiclone (wave 13): CPI AccountInfo clone placement in admin_cto

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main 3912c47ac (0.48772), 085e5dffb (#2885, 0.48922), b78bf199a (0.49071; programs identical to 43946852e).
Angle: the sharing-CPI AccountInfo clone run (orig 0x26798..0x27048, regionmap segments 0x41f0/0x45f0, about
100 + 80 tokens unmatched even with a perfect frame).

## What the residual is

The clone order is already the original's: pump_fees (0x98), pool_authority (0x68), authority (0x0),
global (0x8, Box deref), mint (0x10), sharing_config (0x90), event_authority (0xa0), program (0x98 again).
The only difference is register allocation of the AdminCto accounts pointer:

| | original | ours (all mains above) |
| --- | --- | --- |
| accounts pointer in the clone run | reloaded from its spill slot `[r10-0x8d8]` before every account (`ldxdw r1,[r10-0x8d8]; ldxdw r1,[r1+0x98]`) | reloaded once into `r6` (`ldxdw r6,[r10-0x8b8]`) and kept there for all 8 clones |
| `tools/clonefeat.py` spill/reg | **6/2** | 2/6 |
| accounts-pointer reloads in the whole function | 34 | 25 |
| first AccountInfo's key/lamports/data/owner | kept in r5/r0/r7/r6 to the final array stores | spilled at once |
| `swept` across both CPIs | r9 from the sweep exit to the event store (`stxdw [r10-0x218], r9`) | spilled at the sweep exit (`[r10-0x948]`), reloaded for the event |

So the region is a greedy-RA outcome (the accounts pointer gets a region split into a free callee-saved
register in ours, spill-everywhere in the original), not a source-order difference in the CPI.

## Source spellings of the CPIs: none moves the clone-run RA

Every variant below keeps clonefeat 2/6 and the 0x41f0 segment at 102-113 pf-unmatched tokens.

| variant (CPI) | base | bytes | ratio | note |
| --- | --- | ---: | ---: | --- |
| `let program=..;let accounts=..;` before CpiContext (sh) | 3912c47 | 27,368 | 0.48591 | 0x45f0 36% -> 11% |
| same, program only (sh) | b78bf19 | 27,368 | 0.48861 | |
| program only (po, cc, ci, ch) | 3912c47/085e5df | 27,400 | = main | byte-identical |
| program only (tf) | 085e5df | 27,368 | 0.48741 | |
| `let accounts=..;` first, program clone last (sh/po/tf/cc/ci/ch) | | 27,280-27,400 | 0.27-0.47 | frame and clone order break |
| plain nested `fn sharing_cpi(&AdminCto,..)` / `(&Context,..)` | 3912c47 | 27,288 / 27,368 | 0.47193 / 0.48591 | LLVM-inlined, same RA |
| `let cpi=CpiContext::new_with_signer(..);` | 3912c47 | 27,400 | 0.45147 | abs_ratio = main; frame shift only |
| `CpiContext::new(..).with_signer(seeds)` (sh / po) | | 27,376-27,440 / 27,400 | 0.466-0.471 | clone runs worse |
| migrate.rs closure idiom `(move\|signer_seeds\|cpi(..))(signer_seeds)` (sh / po / both) | 085e5df | 27,424 / 27,032 / 26,992 | 0.473 / 0.311 / 0.288 | |
| immediately-called `(move\|\|cpi(..))()` (sh / tf / cc) | 085e5df | 27,456 / 27,360 / 26,992 | 0.473 / 0.349 / 0.351 | |
| `match &sharing_update{Some(val)=>..*val}` | 3912c47 | 27,392 | 0.45543 | |
| `ctx.accounts.X` instead of `a.X` | (w12b11) | | | byte-identical: GVN folds the loads |

## IR probes (llc oracle on main 3912c47's IR, `tools/ir_*.py`, about 1 s each)

All keep the clone run in a register:
- branch weights on the sharing arm (`icmp ne tag,2`) from 1:2000 to 2000:1, and Ok-biased weights on the
  sharing CPI, pool CPI and `Clock::get` result checks;
- a fresh `load ctx.accounts` + GEP for every clone (gives ctx-register double loads, worse);
- inline-asm pins of r9, r6, r8, r9+r0, r9+r0+r5 across the clone run, and of r9/r8/r7/r6 across the whole
  `swept` range (sweep exit -> event store): the pointer just moves to another free register (r0, r7).
- The only llc setting that reproduces the original's 6/2 pattern is `-grow-region-complexity-budget` 0 or 100
  (x1-cto-llc-size-cap-oracle builds `llc-grcb0/100`: 0x41f0 50%, 0x45f0 77% pf-matched), which
  changes ~300 other windows; 500 and above equal the default. Not a candidate, but it confirms the
  mechanism: the original did not region-split the accounts pointer in this run.

## Builds that have the original's clone RA (scan of 5,998 swarm builds with clonefeat)

6/2 (the original's pattern): `w10r1-admincto-hillclimb/hc/keep/7fb9a5e3e7a2` (27,400 B, 0x41f0 73%,
0x45f0 88% pf-matched; genes n298_iflet, sharing_key_once, n306_okorelse, fee_unwrap_or, su_iflet_match,
curve_edit_first on main 1b1f7112), `w10r1-admincto-stitch/out/c4_shared_bitand`, `c4_shared_owner_first`,
`w10r1-admincto-errseq/out/t03_feesfn_ia_unwrap`, `admincto-reconstruction/out/t4`, `w3-adminCTO/out/e14`.
5/3: `hc/keep/f6eb16639005` (ql_before_shared, validate_keys_ref). 4/4: about 40 builds (ql_inline_ctostate,
cashback_end, shared_empty_first, ...). The flips come from unrelated validate-region genes on old bases,
the same coupling w12a02-cto-iroracle measured (clone RA follows validate's block frequencies through spill
weights). In 7fb9a5e3e7a2, as in the original, r9 holds `swept` across the clone run.

## Sweep-result spellings (side trials)

On 085e5df, `let mut swept=0; if !skip{swept=sweep(..)?;}` was 27,392 / 0.48959 and, with the reset flag
back in the event, 27,400 / **0.48951** (> 0.48922, 0 losses), but main moved to b78bf19 (0.49071) first;
on b78bf19 every swept spelling (`let mut`, `if skip{Ok(0)}else{..}?`, `match skip`, late `let`) is
byte-identical to main.

## Ledger

Approach `cpi-clone-placement`, keys `0x22a10-w13-3912c47-cpiclone-*`.
