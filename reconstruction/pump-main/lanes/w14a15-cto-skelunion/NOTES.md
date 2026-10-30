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
