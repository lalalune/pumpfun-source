# w14a85-cto-s1reload: register naming of the s1 sharing-CPI clone run (admin_cto::execute, 0x22a10)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main `0d04cf460` (0.66507, 3,228 slots) and, after #3409 landed mid-lane, main `95a64ba75` (0.66986, 3,204 slots).
Ledger approach `s1reload`, keys `0x22a10-w14-{0d04cf4,95a64ba}-s1reload-*-v1`.
Scratch: `~/.cache/pumpfun-reconstruction/lanes/w14a85-cto-s1reload/` (not in git).

**Result: notes only, no source change.** s1 cannot beat main by fixing its register naming. On 95a64ba, even the
IR-only per-clone accounts-pointer reload (the original's shape) brings s1 to only 0.65309 after the frame shift is
undone, 0.0168 below main. No source form screened produces that reload. The value that has to move is `swept`:
the original keeps it in r9 from the sweep exit (orig 0x3c40) to the event store (0x5030). Ours spills it, so r9
is free for clone pieces, which pushes the whole run off by one register.

s1 = all seven sharing `AccountInfo`s written as plain `to_account_info()`. `edits/gen.py` regenerates `edits/s1.py`
from the current source (w14a74's generator).

## 1. s1 on both bases (rx oracle; `m0`/`m1` reproduce main, `eq_main: true`)

| form | ratio | bytes | L1 (frame masked) | L2 (frame + regs masked) | cls 0x3c38-0x46b8 miss/fm/rm/sk | reg-only misses (ours r9) |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| main 0d04cf4 | 0.66507 | 27,400 | 0.70132 | 0.78310 | 190/24/0/166 | |
| s1 on 0d04cf4 | 0.63589 | 27,360 | 0.69135 | 0.81247 | 233/30/123/65 | 125 (29) |
| main 95a64ba | 0.66986 | 27,400 | 0.69982 | 0.78400 | 189/23/0/166 | 77 (11) |
| s1 on 95a64ba | 0.63969 | 27,368 | 0.68076 | 0.81984 | 226/0/171/55 | 155 (49) |

On 95a64ba, s1's structural lead grew (L2 +0.036 over main) and so did its register loss. 49 of its 155
register-only misses in the region are pairs where ours uses r9. The original has no r9 in the clone run, because
r9 holds swept there.

## 2. Occupants (`data/blame-s1-95a64ba.txt`, `data/regmiss-s1-95a64ba.txt`, w14a79 `blame.py`/`regmiss.py`)

The debug-llc greedy trace on s1+accprobe (0d04cf4, `rx/s1_acc/ra.log`, not kept) shows the mechanism:
- Swept is vreg `%1630`. It coalesces 24 values: the sweep's 0 and amount defs, the sweep-exit phi and the
  `%_95` join phi. Its weight is 9.9e-7, the lowest class.
- In round 1 it cannot get one callee-saved register for its whole range, which runs from 21280 to 68016 across
  every call in the sweep.
- In round 2 the region split reports `$r9 no positive bundles`. It splits the range into `$r3` around 5 def
  bundles and spills everything after the sweep exit to the stack slot `[r10-0x968]`.
- r9 across the arm is then held by clone-run pieces: split products of the clone keys `%309` and `%330`, the lamports
  Rc pointers `%301`, and the `%1863`/`%1872` families. These are loaded early and stored into the `AdminCtoSharingConfig`
  struct at the end.

The original also splits swept, but it gives the post-sweep piece r9.

Who wins r9 in ours, and the original's counterpart:
- In ours, r9 is won by the CpiContext program clone's lamports and data Rc pointers. These are `%1863 = LDD %290,8` and
  `%1872 = LDD %290,16`, live from the first clone (57136) to the struct store (63032), with weights 2.0e-6 and 2.4e-6
  against swept's 9.9e-7. They hold r9 and r8 across the run.
- The original holds the same two pointers in **caller-saved** r0 and r7 (orig 0x3d98 `ldxdw r0,[r1+8]`, 0x3de8 `ldxdw r7,[r1+16]`).
  It shuffles them at 0x4270 `mov r8,r7`, 0x4298 `mov r7,r0` and 0x4388 `mov r0,r7`. These are the "three long-lived values
  shuffled through r6/r7/r8/r0".
- In ours r7 is the accounts pointer for the whole run. Its first load is 3d58 `ldxdw r7,[r10-0x8d8]`. That pushes the two Rc
  pointers into r8/r9, which leaves swept no register. The original reloads the accounts pointer into r1 per clone,
  and r1 becomes the AccountInfo pointer at once.

| occupant (ours, s1 95a64ba) | value | misses |
| --- | --- | ---: |
| r5 <- 3d68 `ldxdw r5,[r1+8]` | clone 1 (CpiContext program) lamports Rc | 19 |
| r6 <- 3dc0 `ldxdw r6,[r1+16]` | clone 1 data Rc | 18 |
| r4 <- 4270 `ldxdw r4,[r0+8]` | clone 6 (event_authority, +144) lamports Rc | 15 |
| r0 <- 4268 `ldxdw r0,[r7+144]` | clone 6 AccountInfo ptr | 9 |
| r1 <- 44b8 `add64 r1,1` | clone 8 Rc count | 9 |
| r3 <- 4138 / 42e0 | clone 5 / 6 pieces | 15 |
| r7 <- 3d58 `ldxdw r7,[r10-0x8d8]` | **accounts pointer, held in r7 for the whole run** | 5 |

## 3. Priced probes (post-opt IR + llc; `tools/llcx.py`; plain ratio after `tools/fixframe.py` frame undo)

`fixframe.py` undoes the probe alloca's +8 frame shift. It maps the probe slot onto the existing accounts-pointer
spill slot, the one a real reload would use, and shifts every other offset back by 8. Its null probe (alloca and
store only) gives 0.6301 against s1's 0.63589 on 0d04cf4 (the extra entry store costs about 0.006), so the corrected
plain ratios are slightly pessimistic.

| probe | base | bytes | plain (frame undone) | L1 | L2 | ours-r9 misses |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| per-clone accounts reload, all 8 clones (w14a01 `accprobe.py`, sharing arm only) | s1 0d04cf4 | 27,416 | 0.65379 | 0.69931 | 0.81342 | 29 -> 15 |
| same, from clone 3 | s1 0d04cf4 | 27,408 | 0.65508 | 0.70001 | 0.81444 | |
| same, all 8 | s1 95a64ba | 27,416 | 0.64121 | 0.68553 | 0.82270 | 49 -> 18 |
| same, from clone 4 (best) | s1 95a64ba | 27,424 | **0.65309** | 0.69352 | 0.80222 | 49 -> 10 |
| same, all 8 | main 0d04cf4 | 27,464 | | 0.69240 (-0.009) | 0.78217 | |
| + spill-at-def of each of 73 arm loads (`spscreen.sh`) | s1+acc 0d04cf4 | | | best 0.71495 | | |
| spill-at-def, 73 arm loads + 19 values live across the arm | s1 0d04cf4 | | | best 0.69724 | | |
| swept fake use (empty asm) at the CPI / arm entry / mid-run | s1+acc 0d04cf4 | 27,424 | 0.65399 / 0.65399 / 0.63363 | | | |
| swept `{r9}` asm pin at the join def / at the event store | s1, s1+acc | | | 0.495 / = base | | |
| swept re-read from a slot right after the join (orig 0x3c40) | s1, s1+acc | | | = base | | |

- **Per-clone accounts-pointer reloads are the only lever that pays on s1** (+0.018 to +0.019 plain). They pay on
  s1 but cost L1 on main, because main's literal clones reload the pointer 12 times and chunk 0x3800 drops from 199 to 172.
- The spill screens' L1 "wins" above main (`%_16.i268` 0.71495, `%_364` 0.70896, `%_371`/`%_365` 0.70567) are
  **jump-distance coincidences**, not arm gains: chunks 0x800/0x1000 jump from 94/109 to 123/150 at 27,424-27,456 B,
  while the arm chunks (0x3800+0x4000) fall below s1+acc. Rank by arm-chunk tokens, not total L1: the best arm
  tokens are `%_368` (sharing_config AccountInfo pointer, 563, but L2 drops to 0.795) and the last clone's
  owner/rent_epoch `%_5.i274`/`%_6.i275` (562, L2 0.8121). Every pair of the top four has fewer arm tokens than s1+acc (259-316 vs 325).
- Swept's spill is decided by interference, not weight: fake uses do not move it. The `{r9}` def pin in the join
  block collapses chunks 0x4000-0x5000 (also seen by w14a74 and w14a69). A fresh reload right after the join is
  rematerialised at the use.
- **What s1 needs to win, priced on 95a64ba:** swept in r9 through the arm plus per-clone reloads (L1 to about main),
  and on top of that about 0.017 of frame. The frame-undone plain ratio stays 0.017 below main even with the
  reloads. Registers alone cannot rescue s1. Its frame order (w14a81: under any colour order s1 stays 55-68 M below
  main's best) is the other half.

## 3b. How much register naming s1 needs: an ideal-register rewrite (`tools/regideal.py`)

`regideal.py` takes each L2-aligned instruction pair in a range that differs only by registers and copies the
original's register byte into ours. The frame and code shape stay as built, and the plain ratio is re-scored.
`RF=<regs>` restricts the rewrite to pairs where ours uses one of those registers.

Read this as a bound with noise. Applied to main itself, where the region has almost no true register misses, the
rewrite mis-pairs some instructions and costs 0.007 (0d04cf4: 0.66507 -> 0.65818). Treat differences under about
0.007 as noise.

| base (95a64ba unless noted) | rewrite | pairs rewritten | plain | L1 |
| --- | --- | ---: | ---: | ---: |
| main | none | | 0.66986 | 0.69982 |
| main | region 0x3c38-0x46b8 | 77 | 0.66327 | 0.69712 |
| s1 | none | | 0.63969 | 0.68076 |
| s1 | ours r9 only (the swept effect) | 48 | 0.64718 | 0.70474 |
| s1 | ours r6-r9 | 82 | 0.65168 | 0.71373 |
| s1 | ours r0-r5 | 121 | 0.67206 | 0.72362 |
| s1 | **whole region** | 155 | **0.67356** | 0.73351 |
| s1 + reload from clone 5 (frame undone) | whole region | | 0.67755 @27,408 | 0.73596 |
| s1 + reload, all clones (frame undone) | whole region | | 0.67296 @27,416 | 0.73645 |
| s1 0d04cf4 | whole region | | 0.66497 @27,360 | 0.72733 |
| s1+acc 0d04cf4 (frame undone) | whole region | | 0.68254 @27,416 | 0.72866 |

**Priced answer.** For s1 to beat main, the sharing region's register naming has to be essentially the original's.
- The bound is +0.004 over main 95a64ba at 27,368 B for s1, and +0.008 with the per-clone reload.
- Swept/r9 alone (ours-r9 pairs) is worth +0.0075. All callee-saved pairs together are worth +0.012.
- The other two thirds is the caller-saved rotation inside the run (orig to ours r3->r2, r2->r1, r1->r3, r2->r0,
  r0->r9), a cascade of the missing r9 occupant. No source lever reaches it.
- The bound does not survive the noise margin plus s1's -32 B size repay (the size-knob catalog moves about
  +-0.003 per knob), so s1 is not a base worth moving to (w14a87 #3416 reaches the same verdict through legal-frame bounds).

## 4. Source forms screened on s1 (raw-IR capture + rx oracle = build tokens, 0d04cf4)

| form | ratio | bytes | L1 | L2 | note |
| --- | ---: | ---: | ---: | ---: | --- |
| s1 | 0.63589 | 27,360 | 0.69135 | 0.81247 | |
| `CpiContext::new(..).with_signer(seeds)` | 0.63212 | 27,400 | 0.66087 | 0.81306 | arm chunk 0x4000 105 -> 64 |
| `let accs=AdminCtoSharingConfig{..}` first | 0.63058 | 27,352 | 0.68336 | 0.80870 | |
| `let program=a.pump_fees.to_account_info()` first | 0.63297 | 27,328 | 0.71216 | 0.83366 | L1 is a chunk-0x800 jump coincidence; arm worse |
| program clone reused as `program: program` (`.clone()` for the ctx) | 0.62573 | 27,152 | 0.66606 | 0.80873 | unfaithful (no 8th reload) |
| `ctx.accounts.x` per field | = s1 | | | | GVN |
| CpiContext bound to a local first | 0.54235 | 27,360 | 0.69135 | 0.81247 | frame only |

None gives per-clone reloads. This matches w14a01 on main: ctx is `noalias readonly`, so every
`ctx.accounts` re-read folds, and the original's `[r10-0x8d8]` loads are RA spill reloads. Original entry 0x280
`stxdw [r10-0x8d8], r8` is a lone spill, not a Context copy.

## 5. Tools (`tools/`, experiment only; paths point at this lane)

- `regideal.py fn.bin out.bin [lo hi]` (env `RF=r,..`): ideal-register rewrite bound for a range.
- `fixframe.py fn.bin out.bin <probe slot> <map-to slot> [shift]`: undoes one probe alloca's frame shift, so
  IR probes that add an alloca can be scored on the plain ratio.
- `score.py fn.bin...`: rx metric plus fmr L0/L1/L2 and per-0x800 L1 tokens.
- `sp1.sh`, `spscreen.sh <base.ll> <tag> <vals>`: parallel spill-at-def screen (w14a79 `spillprobe.py`) over a list of SSA values.
  `spn.sh`: chained spillprobes.
- `accprobe.py` (w14a01; the accounts value is now set by env `ACC`, e.g. `%_219` on 95a64ba), `pairs.sh`
  (two capvar builds at a time).
- `edits/post/fu.py` (swept fake uses), `pin.py` (swept register pins), `swre.py` (swept re-read at the join).
- `edits/s*.py`: the s1-based sharing-CPI source forms. `edits/gen.py` regenerates s1.
- Copied from w14a79/w14a74: `blame.py regmiss.py sbs2.py fmr.py cls.py rx.py capvar.sh capraw.py llcx.py spillprobe.py` and others.
