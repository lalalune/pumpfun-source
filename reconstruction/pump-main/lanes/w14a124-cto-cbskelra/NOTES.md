# w14a124-cto-cbskelra: the sharing-CPI "skeleton" lead is an alignment artifact (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute`, pinned at 27,400 B. Base: main ebe5387 (0.67316, M 2,247, 3,123 slots).
Result: **no gain. This is a notes-only PR.** Ledger keys `0x22a10-w14-ebe5387-cbskelra-*`.

## Question

Two lanes found the same lead, and neither priced it:
- w14a108 (#3513): `ev_cb_local` raises rfjM from 2,810 to 2,872 in the sharing-CPI clone region, but M drops to 2,222.
- w14a106 (#3490): F0 is +58 L2 in orig 0x4000-0x4800, read as "main lays the first sharing clone run one block early".

The question was which block moves, and whether that placement can be recovered.

## Answer: no block moves. The gain comes from global difflib alignment.

1. **Skeleton diff, main -> ev_cb_local (`vs.py`).** About 25 single-instruction spill and copy inserts/deletes change. No block changes.
   The Rc-clone account order (+0x98, +0x68, [0], [[0]], +0x10, +0x90, +0xa0, +0x98) is the same in main, ev_cb_local and the original, and so are the clone positions.
2. **Anchored comparison (`tools/segcmp.py`).** The orig clone run (301 tokens) is split at its 16 Rc-overflow `ja` anchors. Segment k is paired with segment k, with no global alignment.
   The "global" rows count matches inside the same orig range under one difflib alignment of the whole function.

| clone run, orig ~0x3cd8-0x4610 | M | rM | fM | rfM | skM |
| --- | ---: | ---: | ---: | ---: | ---: |
| main, anchored | 126 | 183 | 154 | 233 | **246** |
| ev_cb_local, anchored | 118 | 176 | 144 | 230 | **247** |
| F0 (w14a106 xF0), anchored | 97 | 181 | 119 | 229 | **245** |
| main, global | 122 | 149 | 144 | 122 | **129** |
| ev_cb_local, global | 110 | 143 | 110 | 118 | 192 |
| F0, global | 94 | 138 | 121 | 115 | 186 |

   - Main's skeleton is as good as either variant's (246 against 247 and 245).
   - Main's global *skeleton-level* alignment drifts off the diagonal through the repetitive Rc-clone code (129 against 246). Any small perturbation re-diagonalises it, which "gains" about 60 skM or L2. That is the whole +62 / +58.
   - At the scorer mask the global alignment stays on the diagonal (122 global against 126 anchored), so real M has nothing to recover here.
3. **Whole function (`tools/segall.py`).** The function is split into 199 segments at 154+3 calls plus the Rc anchors; orig and cand have the same anchor count. Anchored skM is 2,917 for main and 2,917 for ev_cb_local (delta 0), and 2,913 for F0 (-4).
4. **What ev_cb_local actually loses.** It loses at every mask level, so jump-distance drift is not the cause (`tools/jfr.py`).

| | M | jM | fM | rM | fjM |
| --- | ---: | ---: | ---: | ---: | ---: |
| main | 2,247 | 2,273 | 2,346 | 2,562 | 2,525 |
| ev_cb_local | 2,222 | 2,253 | 2,315 | 2,542 | 2,490 |

   `cashback` stays live across the sharing CPI and the pool CPI, which adds a spill slot. That spill re-lays the frame (fM -31) and the colouring (rM -20).
   The anchored perfect-colour-and-frame bound (rfM) is 2,800 for ev_cb_local against 2,804 for main. No RA or frame repair of ev_cb_local can pass the same repair applied to main.
5. **ev_cb_local is also unfaithful.** The original event re-reads the curve (`ldxb r3,[r3+0xa3]`, orig 0x4fe8), as main already does. The original's cashback phi `[r10-0x958]` feeds only the curve store (orig 0x4aa8).

## (c) candidates

| candidate | result |
| --- | --- |
| ev_cb_local + one +8 B knob at 27,400 (rP_back / cu_unwrapcur / wl_writ_eq / p_colnat) | 0.66537 / 0.66507 / 0.66507 / 0.66477 (M 2,219-2,221), all below main 0.67316 (`repay_rows.txt`) |
| cashback read once, as the orig phi `[r10-0x958]` | already dead in the ledger: w14a29 hcbools (validate param, per-arm tuple, post-validate, n_e*: 0.46-0.60), w13 cbflagphi / tostring296 (validate returns `(Pubkey,bool)`: -160 B collapse), w14a116 cbnosink (IR asm un-sink 0.604; RA ceiling 0.653) |
| cashback tested before the sharing arm | `if holder{false}else{st.cashback}` / match / `&` forms fold to main's tokens (hcbools d_if, c_match, a_amp); the post-validate placement collapses (n_cbpost 0.562) |

No placement lever exists in the angle's region, because the placement already equals the original's.

## Alignment-free gap map of main ebe5387 (`tools/segall.py main`)

Anchored totals over 3,339 orig tokens: M 2,194, rM 2,537, fM 2,415, rfM 2,804, skM 2,917. In tokens:

| cause | tokens |
| --- | ---: |
| code shape (tok - skM) | ~422 |
| jump / lea / call immediates (skM - rfM) | ~113 |
| colouring (rfM - fM) | ~389 |
| frame offsets (rfM - rM) | ~267 |

The global scorer M (2,247) is above the anchored M everywhere except +2 in two segments (`tools/offdiag.py`), so the scorer has no off-diagonal artifact to exploit.

Per orig 0x800 chunk:

| chunk | tok | shape | imm | colour | frame |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0x0000 | 247 | 97 | 7 | 33 | 20 |
| 0x0800 | 268 | 95 | 12 | 9 | 31 |
| 0x1000 | 255 | 85 | 4 | 16 | 22 |
| 0x1800 | 230 | 18 | 8 | 11 | 18 |
| 0x2000 | 225 | 12 | 15 | 15 | 3 |
| 0x2800 | 265 | 5 | 8 | 48 | 18 |
| 0x3000 | 352 | 13 | 7 | 69 | 27 |
| 0x3800 | 153 | 17 | 5 | 29 | 23 |
| 0x4000 | 327 | 44 | 10 | 67 | 72 |
| 0x4800 | 195 | 15 | 3 | 23 | 5 |
| 0x5000-0x6b00 | 822 | 21 | 34 | 69 | 28 |

- **Code shape is in the head and validate region.** 277 of the ~422 code-shape tokens are in orig 0x0-0x1800.
  - The largest gaps are segments where whole blocks sit in a different call interval: seg 20 (orig 0xd60, 56 tokens against our 7), seg 24 (0x10d0, 45 against 7), seg 41 (0x17e8, 44 against our 73), seg 1 (0x100, 26 against 12) and seg 22 (0xf68, 16 against 26).
  - Seg 20 is the original validate-Ok join: the cashback phi at 0xd78-0xdb8, the shared test `[r10-0x920]`, the twin target-piece copies to `0x4e8..`/`0x530..`, and the fee-tag test `[r10-0x928]`. Ours lays that code after the post-validate join (cand ~0x1740).
- **The sharing clone run (0x3800-0x4800)** is about 61 tokens of code shape (intra-clone load/store interleave, owned by w14a122 shareclonealias), 96 of colouring (w14a117 occ3ea0) and 95 of frame.
- `anchored_main_ebe5387.txt` lists the top 30 code-shape segments.

**Advice for other lanes:** do not read chunkprof/skel L2/skM deltas in orig 0x3800-0x4800 as block moves. Check them with `segcmp.py` or `segall.py --ref main` first.

## Tools (experiment only; run from this directory, needs only `$BASE` and the original window)

- `tools/segall.py <cand|main> [--top N] [--ref <cand2>]`: whole-function anchored profile; `--ref` gives per-segment deltas.
- `tools/segcmp.py [--o lo:hi] [--c lo:hi] <cand>...`: anchored comparison of a clone run (default: the sharing CPI).
- `tools/regM.py lo hi <cand>...`: global-alignment matches inside an orig range, per mask level.
- `tools/offdiag.py <cand>`: global scorer-M against anchored M per segment.
- `tools/jfr.py`, `tools/skops.py`, `tools/dump.py`.
- `tools/cv.sh` / `tools/my.py`: raw-IR capture plus rx oracle (from w14a108). `oracle.py`, `xled.py`, `dis.py`, `fr.py`, `vs.py`, `side.py` and `chunkprof.py` are copies from w14a108, w14a80 and w14a118.
- `<cand>` is an rx name under `$OUT/rx/<name>/fn.bin`, a `.bin`/`.so` path, or `main`.
