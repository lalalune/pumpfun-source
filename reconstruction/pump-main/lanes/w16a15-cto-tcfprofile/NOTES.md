# w16a15-cto-tcfprofile: TCF clone-run per-clone length profile and the c2 tax (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 599891304 (admin_cto source = 1f4e396b5): 0.67436, M 2,251, 3,141 slots at 27,400 B, 1034/1034.
Ledger approach `tcfprofile`, keys `0x22a10-w16-1f4e396-tcfprofile-<cell>-v1`.

**Status: in progress (notes first).** Sections below are filled as the screens land.

## 1. The abort-jump profile (tool `tools/prof.py`)

The Rc-overflow abort block is the first TCF clone's `call abort` (orig 0x26e0, main 0x26b0). It is the target of
**41** `ja` jumps, not 25: the 25 TCF clone checks (orig 0x2728-0x3430) **and the 16 sharing-CPI clone checks** (orig
0x3de0-0x45d0) all jump back to it. A jump's displacement is right exactly when the code between the abort block and the
jump has the original's length, so the profile is the cumulative drift `cum[k] = (jump_k - abort) - (orig_jump_k - 0x26e0)`.

Main (cum, B; 0 = displacement right):

| jumps | values | good |
| --- | --- | ---: |
| TCF 0-24 | 8 8 8 0 0 -8 -8 0 0 -8 -8 0 0 8 8 0 32 32 8 16 32 32 24 40 40 | 7 |
| sharing 25-40 | 0 0 0 0 40 40 24 24 16 24 -56 -64 -80 -80 -104 -40 | 4 |

So main has 11 of 41 right. The 4 sharing jumps are right only because the TCF tail (+40) and the gap between the last
TCF jump and the first sharing jump (-40) cancel: any TCF-tail fix must be paid by the same amount in the gap or it
breaks those 4.

## 2. Per-clone census (tool `tools/census.py`, `data/census_main.json`)

Segment k ends at abort jump k. Each AccountInfo clone is two segments (lamports Rc, data Rc). Clone order (= original):
1 ctx program (a1 manual), 2 payer, 3 quote_mint, 4 token_program, 5 system_program, 6 associated_token_program,
7 coin_creator, 8 coin_creator_vault_authority, 9 coin_creator_vault_ata (a2 manual), 10 pump_creator_vault,
11 pump_creator_vault_ata (a3 manual, the only data-first clone), 12 event_authority, 13 program (a4 manual).

| seg | clone/part | main-orig B | main-only / orig-only instructions |
| ---: | --- | ---: | --- |
| 0 | 1 dat | +8 | main spills the ctx-program data Rc pointer (`stxdw [r10-0x9c0],r4`) |
| 3 | 3 lam | -8 | orig spills two clone keys after clone 2 (`[r10-0x970] r6`, `[r10-0x978] r5`), main one |
| 5 | 4 lam | -8 | orig spills two keys (`[r10-0x988] r7`, `[r10-0x990] r9`), main one |
| 7 | 5 lam | +8 | main spills two keys (`[r10-0x988] r7`, `[r10-0x980] r5`), orig one |
| 9 | 6 lam | -8 | orig `stxdw [r10-0x9a8],r6` (second key spill) |
| 11 | 7 lam | +8 | main `stxdw [r10-0x9a8],r7` |
| 13 | 8 lam | +8 | main `stxdw [r10-0x998],r5` |
| 15 | 9 lam | -8 | orig reloads the cvata lamports Rc pointer (`ldxdw r1,[r10-0x9b8]`); main keeps it in r1 |
| 16 | 9 dat | +32 | main loads the cvata key in the data part and shuffles r5/r9 (`mov64 r9,r5`, `ldxdw r5,[r2]`, a second `stxdw [r4],r1` slot, `ldxdw r5,[r10-0x998]`) |
| 18 | 10 dat | -24 | orig has three dead key reloads into r3 (`[r10-0x9b0]`, `[r10-0x978]`, `[r10-0x8e0]`) |
| 19/20 | 11 lam/dat | +8/+16 | pcva clones data first in main (lamports first in orig): `ldxdw r6,[r1+0x10]` vs `ldxdw r9,[r1+8]`, four dead reloads vs three |
| 22 | 12 dat | -8 | orig `stxdw [r10-0xbf0],r1` |
| 23 | 13 lam | +16 | main loads and spills the event-authority owner (`ldxdw r8,[r1+0x18]; stxdw [r10-0xbf8],r8`); orig does it after the run |

The +-8 rhythm over clones 3-8 is one mechanism: each clone's key pointer (`ldxdw rK,[info+0]`, stored into the CPI
struct after the run) is held in a register for one or two clones and then spilled. The original spills two keys at
clones 3, 4 and 6; main spills two at 5, 7 and 8. The totals over clones 2-8 are equal (sum 0).

## 3. The c2 tax is the through-live `&holder_creator_vault` in r6

Debug-llc regalloc logs (`-debug-only=regalloc` on the rx `m.ll`, reproduces the captures byte for byte; `tools/dbgocc.py`):

- The original keeps the accounts+232 Rc pointer (`pump_creator_vault` data, orig 0x3078 `ldxdw r6,[r8+0xe8]`) in r6,
  moves it to r7 at 0x32f8, takes the event-authority lamports Rc pointer in r0 (0x3228), moves it to r6 at 0x3328, and
  then uses r0 for the flag/owner copy temps at 0x3370-0x33b8.
- Main and c2 (on this main): at the accounts+232 load (`%2186` main, `%2185` c2) **r6 is occupied by `%1726`/`%1725`
  = `accounts + 264` = `&a.holder_creator_vault`**, a region-split piece over [34592, 54132] that is defined at the sweep
  head and spilled only inside the run (main 0x3098 `stxdw [r10-0x9b8],r6`). So the pointer takes r0, the event-authority
  lamports pointer then takes r5 (`%2181` holds r0 over the temps in c2), and the temps take r5.
- The c2 tax force (`2178=r0` on 9bd38c7 = an is_signer temp, `%2179` here) puts the temps in r0 by evicting that
  chain. The value that really differs is upstream of the run: the head value w15a07 (#3651) and w15a26 named
  (`%121 = gep accounts,264`, spilled at its definition in the original, 0x1f48). No TCF literal spelling can free r6
  there, because the occupant is decided before the run.

Library check (`tools/scane8.py`, all 10,463 cached captures): the accounts+232 load is in r6 in only 40 captures, all
on old bases, forced RA builds (w16a04 `Ln1ra`, `Ln1pohra`, `Lpora`, w16a08 `F2p2__ra`) or far-off code (best unforced
M 2,227 at 27,344 B, w15a35 `pd_b5x11`).

## Tools (`tools/`, experiment only)

- `prof.py <fn.bin|so|orig>`: abort-jump profile (41 jumps), `abortjs.py`: ja-target clusters.
- `census.py <sbs.txt>`: per-clone census from `w16-strategy/skeleton/tools/sbs.py main 2600 3c40`.
- `mk.py`: M, profile, per-segment delta vs main and the c2 marker (accounts+0xe8 load register).
- `scanprof.py`, `tcfsplice.py`: profile scan of every cached capture and the TCF-window transplant (splice v2 restricted
  to main 0x2658-0x3b60 hunks).
- `genes_tp.py`: literal genes (`P:`/`Q:`/`G:`/`H:` + field spec over KLDORSWE, lowercase = account path; `T<n>:` turns
  the n-th TCF `to_account_info()` into a manual literal; lit.py permutations).
- `scr.py`/`capraw.py`/`rx.py`/`splice.py`/`jdiff.py`/`drift.py`: w16a02's oracle, re-pointed.
- `tab.py`, `dp.py`, `joint.py`: tabulation, additive joint DP over one spelling per literal group, exact splice pricing.
