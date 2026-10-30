# w14a35-cto-walletr8: why the wallet `do_coin` flag is spilled (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: w14a24-cto-walletlit (#3293) next_idea 2 (IR bound for the sweep/Err payload copy), building on w14a03-2 (#3228)
and w14a06 (#3219). The wallet register-naming residual is worth +0.036 by byte splice (w14a24). It was attributed to one
cause: ours spills the `do_coin` flag at -0x938, where the original keeps it in r8.
Bases: main 06967d378 (0.64649, 3,169 slots) for all trials. The key results were re-run on 81d3d9abe (0.65069).
Ledger: approach `walletr8`, keys `0x22a10-w14-06967d3-walletr8-*` (25 rows).

**No source change is proposed.** No IR variant puts `do_coin` in r8, and no source form beats main. This PR holds the
cause chain, the IR bounds and the tools.

## 1. Cause chain (debug greedy on main, `tools/dcocc.sh`, `tools/occat.py`)

The payload copy is still at 0x5b18 on 06967d3 and 81d3d9a (`mov64 r8, r2`, the shared sweep Err exit LBB315). It is not
what blocks r8. At the time of `do_coin`'s (`%1602`) second greedy round, this is what occupies the callee-saved registers
over its live range [24384, 31216):

| reg | ours (main) | original |
| --- | --- | --- |
| r6 | `do_collect` `%1600`, then sweep values | `do_collect` (same) |
| r7 | ATA clone buffer `%745` (`r10-0x450`), Result tag class `%1673`, collect-arm clone buffers | accounts pointer reloaded per use from `[r10-0x8d8]` |
| r8 | accounts-pointer split `%1686` through the ATA create clone run (25368-26048), then the **payload class `%1672`** in the collect arm (27648-28400) | **`do_coin`** (0x5c30 to the coin gate at 0x6858) |
| r9 | **`%1752`, the live-through split of the `sharing_update` tag `%60`**, over the whole wallet (and sweep) | ATA clone buffer (0x5cf0 `mov r9,r10; add r9,-0x450`), payload class (`ldxdw r9,[r10-0x2c0]`) |
| spilled | `do_coin` (-0x938), tag pieces at its uses (-0x8e8) | `coin_present` (-0x918), tag (-0x950) |

In the collect arm, the payload class is the `collect()` result pair (+8, +16 of the sret), loaded once before the Ok/Err
branch and used both by the event and by the Err-return phi. The original has the same shared loads
(`ldxdw r9,[r10-0x2c0]; ldxdw r7,[r10-0x2c8]` at 0x61e0). Only its register differs.

So the chain is: the tag's live-through split (`%60` RS_Split, "Split for $r9 in 99 bundles") takes r9. The ATA clone buffer
then moves r9 -> r7, and the accounts reload moves r7 -> r8. `do_coin` is live through the ATA create (bb.96 -> bb.94), so
r8 has no free gap for it. Its spill weight (1.9e-8) loses every eviction, and RS_Split reports "no positive bundles" for all
ten registers. The root is the tag split, which belongs to w14a12-cto-tagreg (#3251). It is not the payload copy.

## 2. IR bounds (post-opt IR + llc, `tools/pe2.sh`; main 06967d3 = 0.64649)

`F` is the frame-masked match: registers kept, r10 offsets and jump offsets masked (`tools/wf.py`). `Fw` is F's matched
tokens inside orig [0x5c40, 0x6b08), which has 468 tokens. Main has Fw = 392.

| variant | what it does | bytes | ratio | do_coin | Fw |
| --- | --- | ---: | ---: | --- | ---: |
| main | | 27,400 | 0.64649 | spilled -0x938 | 392 |
| a1 (task a) | collect Err edge reloads the payload words itself (Err phi no longer uses the shared loads) | 27,248 | 0.64954 | spilled | 382 |
| a2 (task a) | the Ok event stores reload +8/+16 | 27,248 | 0.64984 | spilled | |
| b1 (task b) | collected / quote word stored into the event alloca at the definition | 27,232 | 0.31976 | not in a register | |
| c1 (task c) | wallet Err edges return on their own (removed from the shared Err-return phi) | 27,272 | 0.52943 | layout moved | |
| p1 / p2 | `asm "{r8}"` use of do_coin at the gate (and at bb27) | 27,304 / 27,320 | 0.58884 / 0.58866 | spilled (the pin only adds a reload into r8); payload class -> r9 | |
| e3 (w14a06 port) | sweep AMM Err threaded into the sweep Err edge (swept coalesces) | 27,424 | 0.56655 | spilled | 384 |
| e3 + swept `{r9}` / `{r8}` | | 27,280 | 0.53445 / 0.51644 | spilled (do_collect moves to r7) | 399 |
| accblk / accuse | accounts pointer reloaded per block / per use inside wallet() | 27,600 / 27,648 | 0.57335 / 0.56985 | spilled | 363 |
| t1 | tag through its own i8 alloca (its r9 split disappears) | 27,296 | 0.61084 | spilled; r9 goes to `coin_present` | 385 |
| g1 | coin gate on `do_coin` only (the original's `and r8,1; jne`) | 27,368 | 0.64359 | spilled | 388 |
| **t1 + g1** | tag out of registers + original gate | 27,256 | 0.6131 | **r9** (the first state with do_coin in a register); `coin_present` in r8 instead of spilled | 384 |
| t1 + g1 + `{r8}` pin | | 27,192 | 0.54436 | | 384 |
| llc greedy options | exhaustive search, local reassign, split-spill-mode, CSR cost, deferred spilling, region budget, huge split | 27,216-27,584 | 0.538-0.64649 | unchanged or worse | |

On 81d3d9a (0.65069): a1 gives 0.65315 @ 27,248, g1 gives 0.64778 @ 27,368, t1 gives 0.60832 @ 27,280, and t1+g1 gives 0.61088 @ 27,240.
a1 re-allocates the whole function (47 hunks from 0x498 to 0x6ac8). Its gain comes with -152 B, and its shape is not the
original's: the original also shares the loads before the branch.

**The r8 chain is not reachable through the payload copy.** Moving the payload class (p1, e3r9) or splitting the Err phi
(a1, c1) never frees r8 for `do_coin`. Taking the tag out of r9 (t1+g1) gives `do_coin` a register, but r9 rather than r8, and
the frame-masked wallet match is still lower than main's (384 vs 392). Every bound loses at the pinned size.

## 3. Source forms (raw-IR capture + oracle = identity build; `edits/src/`)

| form | bytes | ratio (06967d3) |
| --- | ---: | ---: |
| s1 `if do_coin{` (w14a24 next_idea 1) | 27,400 | 0.6444 (81d3d9a: 0.64859 vs 0.65069) |
| s12 s1 + `if let Err(e)=wallet(&ctx){return Err(e);}` | 27,400 | 0.6444 |
| s18 `let skip_coin=!coin_present\|\|token_frozen(..)?; if coin_present&!skip_coin{` | 27,400 | 0.6435 (81d3d9a: 0.64769) |
| s2 wallet `if let Err(e)=..{return Err(e)}`; s3 wallet `.map_err(\|e\|e)?`; s5 / s13 token_frozen `match`; s8 `let r=collect(..)?`; s16 collect `.map_err(\|e\|e)?`; s17 ATA `.map_err(\|e\|e)?` | 27,400 | = main (same tokens) |
| s6 ATA create `if let Err(e)=..{return Err(e);}` | 27,400 | 0.57639 |
| s4 collect `match{Ok(v)=>v,Err(e)=>return Err(e)}` / s14 `let r=..; if let Err(e)=r{..} if let Ok(Some(..))=r{` | 27,192 / 27,200 | 0.4806 / 0.48083 |
| s11 event `timestamp:0` + `e.timestamp=Clock::get()?..` (store collected at the definition) | 27,232 | 0.64313 |

The per-call-site Err spellings fold back to main's tokens (SimplifyCFG/GVN re-merge the Err edges), or they re-lay the
wallet CFG.

## 4. Next ideas

1. The lever is the tag's (`%60`) region split, not the wallet. If a tag form ever makes greedy split it to r6 in the tail
   and spill it in the middle (the original's shape, w14a12 section 2), retest `if do_coin{` (g1/s1) on top. t1+g1 shows
   that `do_coin` then gets a register.
2. After that, the `coin_present`/`do_coin` naming (t1+g1 gives r8/r9 where the original has spilled/r8) is the w14a03 w10
   use-count trick in reverse. The original's two `coin_present` reloads come from tail-duplicated ATA-gate blocks
   (orig 0x5c50, 0x6108).

## Tools (`tools/`, experiment only; they sit next to the w14a03 `rx.py`/`capvar.sh`/`q.sh` in the lane scratch dir)

- `pe2.sh <name> <edits.py> [base m.ll]`: post-opt IR edit, then `wr.py` and w14a06 `coal.py`.
- `wr.py <m.ll|fn.bin|.so>`: ratio, bytes, slots, M (matched tokens), Mw (matched in the wallet), and a do_coin register guess.
- `wf.py <m.ll>`: the frame-masked, register-kept match, F and Fw.
- `dcocc.sh <m.ll>`: finds the do_coin vreg in the greedy MIR, prints its fate and the physreg occupancy at its last
  `selectOrSplit` (`occat.py`; `occ.py` gives the final assignment).
- `docoin.sh`, `dll.sh`, `ra.sh`: wallet flag-init sequence, llc + disassembly, debug-greedy log.
