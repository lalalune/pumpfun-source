# w15a28-cto-flaghoistrepay: the F0 flaghoist bound table (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 9120883a9: 0.67376, 3,124 slots, M 2,249, 1034/1034. The raw-IR capture `m0` reproduces main (`eq_main: true`).
Angle: port w14a106's F0 (`let (cb0,hr0,my0)=(curve.is_cashback_coin, curve.is_holder_reward, curve.is_mayhem_mode)` before
`quote_locked`, as in the original's loads at orig 0x290-0x2b0), price it with the frame and RA bounds, and repay its 48 B
only if the bound beats main. This continues w15a22 (#3708, next idea 1) and w14a106 (#3490).
Ledger: approach `flaghoistrepay`, keys `0x22a10-w15-9120883-flaghoistrepay-{m0,F0bound,F0origcolour,GFbound,GPFbound,F0pass2}-v1`.

**Result: the kill test fails, so there is no repay and no source change.** F0's alloca-unshift + spill-permutation bound is
2,205 M, against main's 2,300. Even with 16 sticky RA forces and a perfect spill colouring, F0 (2,322) stays below main
with the same oracles (2,338). Under true LCS, F0's "+62 skeleton" is +1 rfj token. That confirms w14a124/w14a128: the +62 was
a difflib greedy-alignment artifact.

## Bound table (raw-IR oracle on 9120883; M = matched masked tokens)

| variant | bytes | ratio | M | Mperm | Mhc (= shperm, shift 0) | true LCS `---` / `rfj` vs main |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| main m0 | 27,400 | 0.67376 | 2,249 | 2,293 | **2,300** | 0 / 0 |
| F0 (bools first) | 27,352 | 0.63478 | 2,117 | 2,197 | 2,205 | -106 / +1 |
| GF (g binding + bools first) | 27,384 | 0.63021 | 2,103 | 2,198 | 2,206 | -121 / +0 |
| GPF (PDA first + g + bools first) | 27,344 | 0.58719 | 1,958 | 2,173 | 2,183 | -200 / **+19** |

`fobj.py` shows that F0's frame objects (allocas) are the same as main's: same objects, same offsets, 108 spill slots
either way. So there is no alloca shift to undo, and `shperm.py <rx> 0x568 0x8d8 0` equals `permhc`'s Mhc.

## RA pass: sticky RAPRIO climbs, with every variant priced the same way

Method: `colmap.py` (w14a84) votes the original's register for each vreg. Each of the top 80 misses is forced to that register
with `RAPRIO_STICKY=1` (llc from w15a24's patch). Then `sclimb.py` does greedy forward selection over the top 30, with no size
restriction. Pass 2 reruns `colmap` under the pass-1 forces and climbs again on top of them. "Joint" is `permhc` on the
forced build. That bounds RA forces plus a perfect spill colouring.

| variant | pass-1 climb | pass-2 climb | M (forced) | joint Mhc | true LCS `---` / `rfj` |
| --- | --- | --- | ---: | ---: | --- |
| main | 7 forces 0.68245 @27,376 | 9 forces **0.68395** @27,376 | 2,282 | **2,338** | +35 / +2 |
| F0 | 9 forces 0.66237 @27,352 | 16 forces 0.67447 @27,296 | 2,247 | 2,322 | +18 / -3 |
| GF | 12 forces 0.66096 @27,296 | (not run) | 2,202 (p1) | 2,285 (p1) | -42 / +3 (p1) |
| GPF | 3 forces 0.64398 @27,360 | 14 forces 0.66667 @27,368 | 2,224 | 2,306 | -12 / +30 |

- F0 recovers +0.040 from RA forces, against main's +0.010. That is consistent with the cascade story: most of F0's loss is
  register naming. But its RA-and-frame ceiling stays 16 M below main's ceiling, and it sits at 27,296 B, which would need
  +104 B of repay.
  - The top F0 forces are `%1684` (r6 to r8: the accounts-pointer `%0` piece over the sweep head, orig 0x1d68-0x1fb8,
    29/29 sites) and `%1660` (r8 to r9: the Err-payload class).
  - Vreg numbers are per build. Main's own top force, also numbered `%1684`, is a different `%0` piece, in the event
    region at 0x4e80, moved r8 to r6.
- GPF is the only head variant with a real skeleton gain: true LCS rfj +19, or +30 with RA. All of it is in orig 0x0-0x800
  (+31), from the PDA-first order. Its joint bound is still 32 M below main's.
  - A single force, `%249=r8`, lifts GPF from 0.58719 to 0.64149. That decision is the head's biggest RA cascade.
  - `%249` is `add64 rX, 72` on the held accounts pointer in `wallet()`, between `token_frozen` and `token_raw_amount` on the
    same account: GPF 0x20e8 vs orig 0x20e8 `add64 r8, 72`. The original keeps `ctx.accounts` in r8 there; GPF has r6.
- **The common mechanism.** Every head-order variant (F0's `%1684`, GPF's `%249`) recolours the accounts pointer `%0` over
  the wallet/sweep head (orig 0x1d68-0x20f8) from the original's r8 to r6. This is the largest single cost of moving the
  head loads. The longer live ranges of the curve bools and the PDA in the head change greedy's split of `%0`. A source
  route that keeps `%0` in r8 over `wallet()` and the sweep head is the prerequisite for any class-A/B head order.

## The original's bool colouring is not the missing piece

The original holds mayhem (a2) in r8 and spills cashback (a3) to -0x8e8 and holder_reward (a5) to -0x8e0. F0 loads in the
same order, but it holds cashback in r8 (`%2011`) and spills holder_reward and mayhem (`%2143`). Forcing the original's choice
loses every time (`data/F0-origcolour.jsonl`):

| forces | on F0 (0.63478) | on F0 + 9 pass-1 forces (0.66237) |
| --- | --- | --- |
| `%2011` cashback to spill | 0.62999 | 0.65947 @27,344 |
| `%2143` mayhem to r8 | 0.63420 @27,376 | 0.65398 @27,376 |
| both | 0.62969 | 0.64958 @27,368 |

## Verdict

The 48 B repay step was not run. It is gated on F0's bound beating main, and F0's bound loses by 95 M (frame) or 16 M
(frame + RA). Class B (w15a11) is therefore not worth taking alone. The only head-order form whose skeleton beats main is
GPF (PDA first), and the w14a04/w14a09/w14a93/w15a03 PDA-first lanes already price its cost elsewhere.

## Tools (`tools/`, experiment only)

- `pipe.sh <rx>` runs the whole bound pipeline on one raw-IR capture: Mperm, colmap, sticky single screen, sticky climb,
  joint perm and true LCS. It uses w15a19's `t2/` (rx.py, mp.sh, permhc.py, evall.py), w14a84's `colmap.py`/`screen.py`, and
  w15a24's sticky llc.
- `pass2.sh <rx> <tag> <forces>` runs the second colour pass under a base force set.
- `sclimb.py` is w15a24's, patched so an empty base force set works.
- `edits/F0.py`, `GF.py` and `GPF.py` are rx `cv2.sh` edit sets. They apply to 9120883 with unchanged line counts.
  w14a106's GF/GPF no longer apply after #3666, which moved `fee_configurable` first in the CtoState literal.
- `data/climb-*.log` holds the climb trajectories, with the force sets in each row.
