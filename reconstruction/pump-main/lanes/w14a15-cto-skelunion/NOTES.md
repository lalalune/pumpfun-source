# w14a15-cto-skelunion: union of the skeleton-positive admin_cto forms

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main cef0574cf (0.63421, 3,179 slots).
Angle: compose the forms that each move the instruction/block skeleton toward the original but lose positional ratio
through register allocation (RA) and frame. Then tune RA and size on the union instead of on main.
Ledger: approach `skelunion`, keys `0x22a10-w14-cef0574-skelunion-*`.

## Oracle

The oracle is the raw-IR capture + `opt -O3` + `llc` pipeline (w14a11 `capvar.sh`/`rx.py`, repointed to this lane).
It reproduces main exactly (`m`: 0.63421 at 27,400 B, `eq_main: true`).

New tools, in `tools/`. The w14a11 oracle files `rx.py`, `oracle.py`, `bwx.py`, `bwfm.py`, `ed.py`, `absratio.py`,
`dis.sh` and `capraw.py` must sit next to them.
- `cap.sh <genes> <slot>`: generates EDITS from `e/gen.py` and captures them.
- `run.py <queue> <out.jsonl> 2`: background screen runner. It writes ratio, bytes, fm, sk and the error-tail order.
- `ch3.py ref name..`: matched original instructions per 0x800 chunk, in three flavours: raw (jump offsets masked),
  fm (frame masked) and sk (frame and registers masked).
- `jm.py name..`: the masked ratio with jump offsets also masked. It is the ratio a build would reach if every
  jump distance matched, which is the size-repay ceiling.
- `vsmain.py a b`: median offset of b against a per 0x400 region of a. It shows where b gains or loses bytes against main.
- `splice.py` (w14a09): front-of-A plus back-of-B bound.
- `e/gen.py`: composable genes `p1 p2 e3 tu8 rar hb0 s1 cbR*`, plus every genes47 (`g.*`) and size-knob (`K.*`) gene.
  Join genes with `+`.

## Components and unions on cef0574 (raw-IR oracle)

| build | bytes | ratio | jm | fm | sk | error tail |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| main | 27,400 | **0.63421** | 0.6417 | 0.72648 | 0.85021 | 298 289 296 326 306 312 307 330 338 |
| p1 (PDA first, creator left) | 27,384 | 0.56548 | 0.57627 | 0.66017 | 0.85915 | main |
| s1 (sharing CPI `to_account_info`) | 27,368 | 0.61841 | 0.61811 | 0.72482 | 0.86331 | main |
| e3+tu8 (and-1 holder, and-1 306 tag) | 27,328 | 0.61407 | **0.64917** | 0.73616 | 0.85706 | original through 338 |
| p1+e3+tu8 | 27,352 | 0.56672 | 0.6036 | 0.67376 | 0.86597 | original |
| **p1+e3+tu8+s1** (full union) | 27,352 | 0.55712 | 0.5934 | 0.67076 | 0.86957 | original |
| p1+s1 | 27,384 | 0.55379 | | 0.65927 | 0.86275 | main |
| **e3+tu8+s1** (U2) | 27,264 | 0.6109 | **0.64754** | 0.73314 | **0.88031** | original |
| e3+f2 (rar+hb0) | 26,872 | 0.60496 | 0.63975 | 0.74682 | 0.86842 | 289 298 312 306 ... |
| e3+f2+s1 | 26,808 | 0.60115 | 0.6381 | 0.74379 | **0.89188** | 289 298 312 306 ... |

Per 0x800 orig chunk, matched instructions as raw/fm/sk deltas against main (`ch3.py`):

| chunk | main | p1 | s1 | e3+tu8 | full union | U2 = e3+tu8+s1 |
| --- | --- | --- | --- | --- | --- | --- |
| 0x0000 | 90/132/167 | +15/+25/+35 | 0 | +28/+1/+3 | +40/+31/+38 | +28/+1/+3 |
| 0x0800 | 82/120/129 | +0/+3/+0 | 0 | +71/+79/+79 | +71/+77/+78 | +71/+79/+79 |
| 0x1000 | 142/154/166 | -1/+1/-1 | 0 | -7/-59/-65 | -7/-59/-63 | -7/-59/-65 |
| 0x3000 | 192/221/253 | **-181/-209/-1** | 0 | -2/0/0 | -181/-209/-1 | -2/0/0 |
| 0x3800 | 160/192/233 | -6/-5/-1 | -42/-6/+2 | -2/0/+1 | -12/-17/-30 | -11/-6/+3 |
| 0x4000 | 83/127/167 | 0 | -38/-1/+40 | -59/+6/0 | -34/+18/+41 | -58/-1/+72 |
| total | 2142/2425/2838 | -219/-222/+29 | -80/-7/+42 | +22/+29/+19 | -163/-188/+62 | +14/+16/+93 |

Findings:
- **The skeleton gains add up.** In the full union, sk is the sum of the three components (+0.019). U2 (without p1)
  reaches sk 0.88031, +0.030 over main, because s1 and e3+tu8 together gain +72 sk in orig 0x4000-0x4800.
- **p1 is not usable in the union.** Its orig 0x3000-0x3800 clone-run loss (-181 raw) is a single temporary
  register. The original reloads the run's spilled clone fields through r1, and so does main (191 of 256 aligned
  register slots are r1=r1). The union uses r3 (170 slots). r1 is busy in the union because the last clone's `data`
  RcBox pointer (`ldxdw rX,[info+0x10]`) is held in r1 until its store at `[r10-0x68]`. The original and main hold it
  in r8, but r8 is taken in the union. This is the same cascade w14a09 traced: with the PDA first, `cashback` takes
  r8 and the payload class moves to r6.
- Splice bound (`splice.py`, union front up to orig X, main after X): 0.64128 at X=0x18a0, i.e. +0.007 over main.
  That bound only holds if the tail keeps main's RA. For e3+tu8 alone the bound is 0.63698.
- **U2 is the usable union.** jm 0.64754 > main's jm 0.6417: with every jump distance right it would beat main.
  What it loses in plain ratio is mostly jump offsets. It is 136 B short. `vsmain.py m U2` puts the deficit at
  -32 B through the validate tail (0x1c00-0x3c00), a further -24..-48 B in the s1 sharing region (0x4000-0x4800),
  -32 B at 0x4c00 and -24 B at 0x6000.
- U2 RA (w14a06 `coal.py`): Err payload on r8, `%0` split on r8 in 3 bundles, clonefeat 2/6. Main has the same,
  except that its `%0` split covers 94 bundles. The original has the payload on r9 and clonefeat 6/2, so U2 keeps
  main's tail RA class. Its residual RA losses are in the fee-check chunk (orig 0x1000, -59 fm) and in s1's
  sharing-region spill colours (orig 0x3c00-0x4400 frame +0x18, as w14a05 found).
- Tail-decoupling partners for the union's `cashback` lifetime are all negative: `cbR` (`if holder{curve.is_cashback_coin=false;}`),
  `cbR2` (`!holder&&curve.is_cashback_coin`).
- U2 single-weight IR map (`bwfm.py sweep`): the best is `global_quote.exit` 20:12, 0.61474 at 27,296 B (not
  reachable from source).

## Screens

- q1: full union plus each applicable genes47 / size-knob gene (157 after dedupe), stopped after 32 rows. 15 rows are
  byte-identical to the union. None of the rest is above it except removing p1.
- q2: U2 plus each applicable gene (182), running. Results are in the lane's out dir as `r2.jsonl`.

## Step 2: the RA-compatible union (B3)

w14a10's `p2` position for the and-1 holder bool (`let hb=holder.unwrap_or(false);` right after the PDA, gene `q2`
here) keeps main's tail RA: q2+tu8 is 0.63289 at 27,360 B (w14a10 measured the same). On that base, full s1 is
strongly negative (q2+tu8+s1 0.61188), because the sharing-CPI clone run reshuffles. The fix is to convert **only
the `program:` clone** of the sharing CPI to `a.pump_fees.to_account_info()` (gene `s_pr`):

| build (cef0574) | bytes | ratio | jm | fm | sk |
| --- | ---: | ---: | ---: | ---: | ---: |
| main | 27,400 | 0.63421 | 0.6417 | 0.72648 | 0.85021 |
| q2+tu8 | 27,360 | 0.63289 | 0.66647 | 0.73362 | 0.85654 |
| **B3 = q2+tu8+s_pr** | 27,344 | **0.63398** | **0.66727** | 0.73354 | 0.8583 |
| q2+tu8+s_po / s_gl / s_ev / s_mi | 27,360 / 27,360 / 27,320 / 27,336 | 0.63139 / 0.63049 / 0.62106 / 0.61548 | | | |
| B3 + s_po / s_gl / s_ev / s_mi | | 0.63188 / 0.63248 / 0.61795 / 0.62088 | | | |
| q3+tu8 (hb after quote_locked) / +s1 | 27,344 / 27,312 | 0.63278 / 0.61455 | | | |

- B3 is 0.0002 below main at -56 B, and its jm is +0.026 above main's. Per chunk (raw/fm/sk against main) it gains
  +71/+78/+79 in orig 0x800 and +25 in 0x0, and loses only fm in 0x1000 (-59, validate fee-check registers).
- The 56 B deficit (`vsmain.py`): -32 B are e3's removal of main's curve-store bool normalisation
  (`and64 r2,0xff; mov r1,1; jne; mov r1,0` before `stxb [curve+0xa5]`). The original has no such code either, so
  this is a faithful loss. The other -24 B are tail spill differences.
- **Pad bound (oracle only, `tools/pad.py`, `tools/padgreedy.py`).** It inserts 8-B `ja +0` inline-asm pads at
  the top of IR blocks. One pad in almost any block gives 0.63448, already above main. Greedy rounds: `bb3.i19.i`
  (to_string unwrap_failed, validate) 0.63478, + `bb82.i` (sweep) 0.63529, + `bb2` (shared-chain
  `data_is_empty`) 0.63549, + `bb1` (shared-chain owner==FEES) 0.6357, + `bb86.i` (sweep native
  `Rent::minimum_balance`) 0.6359 at 27,384 B. Past that, pads shift RA (27,408 B, 0.63621-0.63642). **B3's ceiling
  at 27,400 B with a pure fill is about 0.636.**
- Where the original has that code: its entry reloads the sharing_config pointer from `[r10-0x8e0]` before the
  owner memcmp and before `data_is_empty` (2 x 8 B, the pressure of PDA-first). B3 keeps the pointer in r7. In the
  sharing CPI the original reloads the accounts pointer `[r10-0x8d8]` before each clone (w14a01). B3 lacks 4-6 of
  those reloads (`netreg.py`: orig has +64 B more than B3 in 0x4000-0x4800). Both are RA spill code, not source
  statements, so no faithful source fill has been found for them.
- Negative or neutral on B3: `cs` (curve stores holder-first, the original order) is identical; cashback spellings
  `cb1-3`; hb spellings `q2c` (`==Some(true)`, 0.60665), `q2d`, `q2u`; TCF clone forms `tc` 0.6203, `tp` 0.62558,
  `ta` 0.63248; shared-chain spellings `shA` (owner first) 0.61578, `shB` 0.43114, `shC` 0.63218, `shD` identical;
  w14a14's quote_locked inline (`ql`, #3241: 0.63481 alone) 0.63065 at 27,296 B; catalog knobs (first 30): none above B3.
  The byte-adding ones cost at least 0.001 per 16 B (`K.g_w_clock_local` 0.63289 at 27,360 B).

## Step 3: judged by M, and re-checked on later mains

w14a14 (#3241) showed that `ratio = 2M/(3339+n)`, where M is the number of matched original instructions and n is
the candidate's instruction count. A shorter build therefore scores higher at the same M. Ranked by M, B3 is **not**
ahead of main:

| main | main ratio / M | best union | union ratio @ bytes | union M |
| --- | --- | --- | --- | ---: |
| cef0574 | 0.63421 / 2,117 | B3 = q2+tu8+s_pr | 0.63398 @ 27,344 | 2,114 |
| f8dc901 (#3241, quote_locked inline) | 0.63481 / 2,119 | ql+q5+tu8+s_pr | 0.63426 @ 27,320 | 2,114 |
| b174038 (#3250) | 0.63571 / 2,122 | q5+tu8+s_pr | 0.63276 @ 27,320 | 2,109 |
| b174038 | | main + s_pr + `g.e_reset` (not a union) | 0.6363 @ 27,376 | **2,123** |
| b174038 | | the same, filled to 27,400 (`K.g_w_clock_local`+`g.e_cb_local`) | 0.63391 @ 27,400 | 2,116 |
| 06967d3 (#3300) | 0.64649 / 2,158 | q5+tu8 | 0.63897 @ 27,328 | 2,130 |

- The jm metric is misleading as a ceiling (`jloss.py`). It realigns the whole function, so main's 0x800 chunk drops
  from 124 raw matches to 63 jm matches. Region by region, B3's raw M is +13 over main in 0x0-0x1800 (outside
  0x1000) and -16 scattered over the tail. That is parity, not a lead.
- Pad oracle on main+s_pr+e_reset (b174038): one 8 B pad in the wallet exit block `bb65.i` shifts RA to exactly
  27,400 B at 0.63661 (3,172 slots, +0.0009 over that main). That RA basin exists, but no source fill reaching it
  was found.
- Screens on the s_pr+e_reset base (60 of 230 genes, stopped when main moved to #3300): no byte-adder keeps M.
  `K.g_w_clock_local` gives M 2,120, `g.e_cb_local` M 2,119, `g.x_cp_inline` M 2,112.

## Conclusion (RA ceiling of the skeleton union)

- **No zero-loss gain; nothing landed.** The best union measured is B3 = q2+tu8+s_pr: 0.63398 at 27,344 B on
  cef0574 (fm 0.73354, sk 0.8583, M 2,114 against main's 2,117). With a pure fill it reaches about 0.636 at 27,400 B.
- The skeleton gains of p1, e3+tu8, s1 and f2 add up (sk +0.019 for p1+e3+tu8+s1 and +0.030 for e3+tu8+s1, against
  main's 0.85021). The RA cost adds up too:
  - **p1** blocks the union. With the PDA first, `cashback` takes r8. The clone run then uses r3 instead of r1
    for its reload temporaries (-181 raw in orig 0x3000-0x3800). The cost is independent of the partner forms: 32
    union partners plus `cbR*` were tried.
  - **Full s1** blocks it in every hb position that keeps main's tail RA (q2/q5: -0.021). Only the single
    `program:` clone (`s_pr`) composes.
  - **The e3 entry position** (hb bound at the top of execute) leaves main's RA basin (e3+tu8 0.614). The bool
    must be bound after the PDA (q2/q4) or after quote_locked (q3/q5/q6).
  - f2 (rar+hb0) moves into the outline basin (-528 to -592 B), which needs a fill that no lane has found.
- Coalescing / accounts pointer (w14a06 `coal.py`):
  - Full union: payload on r6, `%0` split on r5 (12 bundles), clonefeat 3/5.
  - U2 and B3: payload on r8, split on r8 (3 bundles), clonefeat 2/6.
  - Main: r8, r8 in 94 bundles, 2/6. The original: payload on r9, clonefeat 6/2.
  - No union puts the payload on r9 or the clone-run accounts pointer on spill reloads.
- Main meanwhile moved from 0.63421 to 0.64649 (#3241, #3250, #3295, #3298, #3300) by tuning the RA basin it already
  had. On 06967d3 the best union form (q5+tu8) is 28 M behind.
