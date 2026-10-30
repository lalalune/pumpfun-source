# w13a50-cto-perarmval: per-arm validate helpers and holder/cashback phis (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main 6ff770f7a (0.62403, wave-13 attempt that died with the network loss) and main 53abf28b1
(0.62672, 3,305 slots; wave-14 continuation). Ledger keys `0x22a10-w13-{6ff770f,53abf28}-perarmval-*-v1`.

**Result: no zero-loss gain. The per-arm helper angle is exhausted.** Every source form of the angle
either loses ratio at about the same size (+48 B helper split) or is the known holder phi, which shrinks
execute by about 200 B. No programs/ change.

Every number below comes from the raw-IR capture + `opt -O3` + extracted-`llc` oracle (`tools/capvar.sh` ->
`tools/rx.py`). On 53abf28 the base capture reproduces main exactly (`eq_main: true`, 0.62672 @ 27,400).
fm and rm come from `tools/abs.py`: fm masks frame offsets and jump targets, rm also masks registers.
"val rm" is the rm-matched count of orig 0x0-0x1800 (`tools/reg.py`, three 0x800 bins).

## Source trials

| trial | form | bytes | ratio | fm | rm | val rm |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| main 53abf28 | | 27,400 | 0.62672 | 0.72169 | 0.84991 | 429 (131/138/160) |
| P1 | validate's target arms as nested plain fns `hold(new,&hk)->Result<Pubkey>` / `other(new,&hk,&sk)->Result<Pubkey>`, `let target=if holder{hold(..)?}else{other(..)?}` | 27,448 | 0.61419 | 0.71805 | 0.84645 | 420 (131/124/165) |
| P2 | P1 with `let (target,holder)=if holder{(hold()?,true)}else{(other()?,false)}` | 27,448 | = P1 | | | |
| P3 | P2 + h2 out-param phi (`ho:&mut bool`) + holder-first curve stores + `pargs=(target,holder,fee)` | 27,256 | 0.59057 | | | |
| H2b | w13a38 h2 alone (`ho:&mut bool` holder phi, cashback from the arg test before validate, holder-first stores, pool holder from the phi) | 27,200 | 0.60232 | 0.72140 | 0.85280 | 431 (135/135/161) |
| F1 | fee checks 326-338 as nested plain `fee_ok(st,fee,cashback)->Result<()>` called at the end of each target arm | 26,288 | 0.48305 | | | |
| F3 | F1 + h2 holder phi | 26,128 | 0.50322 | | | |
| V2 | w13a43 v2: 289 as `if st.holder_reward{if !holder{Err}}` (holder threading, original outline set) | 26,968 | 0.51902 | 0.66214 | 0.80525 | 358 |
| V2H | V2 + h2 | 26,704 | 0.54923 | 0.69822 | 0.82294 | 353 |
| V2P | V2 + P1 | **27,400** | 0.51917 (slots 3,275) | 0.64919 | 0.79479 | 344 |

On 6ff770f (main 0.62403) the same forms gave P1/P2 0.61209 @ 27,448, P3 0.59048 @ 27,264, P4 (`*ho=true`
after `hold()?`) 0.59027 @ 27,256 and h2 0.60192 @ 27,208.

- The helper split (P1/P2) is inlined back by LLVM (157 calls, 88 lddw), but it adds 48 B and loses 14 rm-matched
  instructions in orig 0x800-0x1000. The holder tuple inside validate is folded away (P2 = P1).
- The per-arm fee helper (the angle's variant c) is never inlined: it has two call sites, so the call count changes.
  w10r1 already showed that `#[inline(always)]` duplicates 326/334/338 (163 calls). The original has one fee block.
- V2P lands exactly on 27,400 B with fewer positional diffs (3,275 vs 3,305), but the helpers undo the 289 threading
  (88 lddw, `to_string` inlined again), so the ratio is 0.519.
- The angle's fallback target (fm > 0.7213 and val rm > 430) is met only by H2b: fm 0.72140, val rm 431, -200 B.
  On this main, main's own fm is 0.72169, so H2b is no longer above main on fm.

## Where the missing bytes are (instruction-class histogram, `tools/hist.py`)

Each class shows the candidate count minus the original count. "reload" and "spill" are `ldxdw`/`stxdw` on
r10-0x800..-0x9ff, and "frame" is the rest of the frame.

| class | orig | main | V2 (orig outline set) | H2b |
| --- | ---: | ---: | ---: | ---: |
| ldxdw reload | 232 | -31 | -40 | -49 |
| stxdw spill | 103 | -6 | -16 | -14 |
| mov64 imm | 175 | -12 | -12 | -12 |
| mov64 reg | 292 | +16 | +17 | +20 |
| ldxdw mem | 347 | +12 | +12 | +11 |
| stdw frame | 154 | +12 | **0** | +12 |
| lddw | 86 | +2 | **0** | +2 |
| stb / ldxw frame | 25 / 13 | +2 / -2 | **0 / 0** | +2 / -2 |

- With the original's outline set (V2), the remaining ~430 B gap is almost entirely **spill traffic**: 40 reloads
  and 16 spills (448 B), minus 17 extra register moves. The original keeps more values in spill slots and reloads
  them more often. Faithful structure that removes code (threading, holder phi) lowers spill traffic further, so
  it cannot repay its own size.
- Per-slot traffic (orig vs main, r10-0x8d8..-0x958): the accounts pointer (orig -0x8d8) has **2 stores / 32 reloads**
  in the original against 1 / 20 in main (-0x8e0). The holder phi (orig -0x950) has 8 / 18 against h2's 2 / 4.
  Most of the extra accounts-pointer reloads are in the CPI clone region (0x3d88-0x44f8), which matches the
  w13a40/44 clone-run RA finding.
- The holder-phi reloads in the original sit right before branches into multi-predecessor joins: 0x1d28 (post-validate
  and sweep gate, 7 preds), 0x3c58 (sweep-exit test, 6 preds) and 0x5868 (the global Err return, 24 preds). They also
  include one reload/re-spill pair at the sweep entry (0x1d48/0x1d50). These are greedy-RA split artifacts of a holder
  value that lives across the whole sweep. A source form that only makes holder a phi (h2) does not create them.

## Error-site order (`tools/errline.py`, `stw` line immediates)

| | order |
| --- | --- |
| orig | 289 298 306 296 326 312 307 330 338 334 410 719 648 660 284 556 |
| main | 298 289 296 326 306 312 307 330 338 410 334 719 648 660 284 556 |
| P1 / H2b | = main |
| V2 | 298 289 312 296 326 306 307 330 338 410 334 ... |

## Tools (`tools/`)

- `capvar.sh <name> <edits.py> <slot>`, `capraw.py`, `rx.py`, `batch.sh`: raw-IR capture (one identity build) + opt/llc
  oracle (from w13a23/w13a38; paths point at this lane's cache; `rx.py` imports w13a23's `oracle.py`).
- `abs.py` (fm/rm), `reg.py` (per-0x800 matched counts), `slots.py`, `errseq.py`: from w13a38/w13a29.
- New: `hist.py <m.o>..` (instruction-class histogram vs the original), `errline.py <m.o>..` (error sites as
  offset:line), `vdiff.py <m.o> [lo hi]` (rm-normalized orig/candidate hunks in an orig range).
- `e/*.py`: the `EDITS` lists of every trial above (`e/common.py` holds the anchors for main 53abf28).

## Next ideas (not this lane's angle)

- The ~430 B that the faithful forms lack is spill and reload traffic. A form has to raise register pressure across
  the sweep and the CPI clone region (extra long-lived values, e.g. the holder phi used after the sweep, or the
  accounts pointer re-read through `ctx.accounts` after the CPIs) at the same time as it adds the threading and the
  holder phi. Single genes cannot do this, because each one removes pressure.
- w13a43 (e2n: validate keys by value + bool locals + nested 289 = the original outline set at -32 B) is the closest
  size-balanced faithful form on 53abf28. Its loss is RA in the CPI clone region, which is the same spill-traffic gap.
