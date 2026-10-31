# w14a141-cto-outline312: a source trigger that outlines only the 312 to_string (notes)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main ebe5387 (0.67316, M 2,247) and, after #3621, main e88f9d5 (0.67346, M 2,248, 3,124 slots).
Continues w14a126-cto-origfill (#3596) and w14a125-cto-outlinecollapse (#3587).
Ledger: approach `outline312`, keys `0x22a10-w14-{ebe5387,e88f9d5}-outline312-*-v1`.
Oracle: w14a108 raw-IR capture (`capraw.py`) + `rx.py` (opt -O3 + llc). It reproduces main exactly (`eq_main: true`).

**Result so far: step 1 is solved, step 2 (the repay) is not.** No landable change. The best zero-loss measurement is
still main.

## 1. Exact oracles for the outline decision

- **`tools/thr.py <raw.ll> [edits]`** is the ground truth. It points each to_string call site in validate at its own
  external-linkage clone (`TS_<code>`, same body, so the cost is the same and there is no last-call bonus). It then runs
  `opt -O3 -pass-remarks{,-missed}=inline` and prints `(cost, threshold)` for each `error!` line, in validate (V) and in
  execute (E). Threshold 45 means the cold-callsite rule fired (outlined). 325 means hot (inlined).
- **`tools/ibfi.py <raw.ll>`** explains the decision. It takes a snapshot of the module right before validate's CGSCC
  `InlinerPass` (`-print-before=inline -print-module-scope`) and runs `print<block-freq>` on validate. The sites with
  freq/entry < 0.02 are exactly the outlined ones: all 11 sites agree with `thr.py` on main and on every variant here.
  That includes 326 (V:O, then E:I in execute), which a BFI taken after inlining the earlier calls gets wrong. So the
  deciding BFI is validate's **pre-inline body**: InlineFunction keeps the caller's existing block frequencies.
  Branches on calls that are not inlined yet are 50/50 there, while `memcmp(..)==0` gets the zero heuristic (37.5% equal).
  w14a125's `bfi.py` used a light pipeline instead, which is why it reported a wrong COLD.

Main's pre-inline path to the 307/312 tests: `bb28` (the 306 Some test) is at 0.0755. 307 (`t==default`, memcmp) is
0.0755 x 0.375 = **0.0283**. 312 (`t==sharing || t==holder_key`) is 0.0755 x 0.625 x (0.375 + 0.625 x 0.375) =
**0.0287**. Both are hot.

## 2. Trigger spelling table (312 cold, 307 hot)

f312 = f(bb28) x P(307 passes) x P(312 condition). One change is never enough: a single 50/50 branch for 312 gives 0.0236.
Raising P(307 passes) to 0.5 (a call) with the 312 condition unchanged gives 0.0230. Both changes together give
0.0755 x 0.5 x 0.5 = **0.0189**, which is cold, while 307 rises to 0.0377 and stays hot.

| name | spelling | 307 / 312 pre-inline BFI | thr.py 312 | bytes | M | rfjM | true LCS |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| main ebe5387 | — | 0.0283 / 0.0287 | I | 27,400 | 2,247 | 2,810 | 2,252 |
| O312 (call-site noinline, IR only) | — | — | O | 27,184 | 2,194 | 2,779 | — |
| `bor312` | `if (t==*sharing)\|(t==*holder_key)` | 0.0283 / 0.0236 | I | 27,440 | 2,004 | 2,634 | — |
| `h312` | `fn invalid_creator(t,sharing,holder_key)->bool{*t==*sharing\|\|*t==*holder_key}` | 0.0283 / 0.0236 | I | 27,400 | 2,140 | 2,751 | — |
| `h307` | `fn is_zero(t:&Pubkey)->bool{*t==Pubkey::default()}` | 0.0377 / 0.0230 | I | 27,400 | 2,247 (byte-identical to main) | 2,810 | — |
| **`T` = h307 + h312** | both helpers | **0.0377 / 0.0189** | **O** | 27,184 | **2,198** | 2,765 | 2,212 |
| `h307_312r` | T with `holder_key` tested first | 0.0377 / 0.0189 | O | 27,184 | 2,192 | 2,765 | — |
| `z_bor`, `z_borr`, `hb312` | is_zero + a bitwise `\|` 312 test | 0.0377 / 0.0189 | O | 27,224 | 2,032 | 2,633 | 2,085 |
| `T2` | 307 as `same_key(&t,&Pubkey::default())` | 0.0377 / 0.0189 | O | 27,184 | = T | = T | = T |
| `T5` | `is_zero` body `t==&Pubkey::default()` | 0.0377 / 0.0189 | O | 27,184 | = T | = T | = T |
| T on main e88f9d5 | — | — | O | 27,184 | 2,199 (main 2,248) | 2,765 | 2,213 (main 2,253) |

`T` is ordinary Rust: two plain private `fn`s returning `bool`, with no `#[cold]`, weights or intrinsics. Its outline
set is the original's minus 307. It removes one of the two extra String-vtable `lddw` relocations. The internal call
count does not change (157 = 154+3), because an inlined to_string costs `name` + `fmt::write` calls and an outlined one
costs `name` + `to_string`. Every chunk from 0x1800 on is unchanged.

## 3. What the 312 outline costs: mostly a difflib artifact

True LCS (w14a128 `lcs.py`, bit-parallel DP) against the original:

| form | bytes | difflib M | true LCS --- | -fj | rfj | validate 0x0-0x1c20 LCS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| main e88f9d5 | 27,400 | 2,248 | 2,253 | 2,595 | 3,007 | 454 |
| O312 (noinline) | 27,184 | 2,195 | **2,242 (-11)** | 2,571 | 2,985 | 443 (rfj 690 = main) |
| T (source) | 27,184 | 2,199 | 2,213 (-40) | 2,551 | 2,961 | 414 |

- Outlining 312 costs only about 11 true-LCS tokens. Most of the scorer's -53 comes from the greedy matcher choosing
  different blocks: O312's frame-masked M (2,346) equals main's (2,347), and `tools/fmap.py` gives the same frame-pair
  census for both (220 mismatched, 841 equal).
- T loses a further 29 tokens to the helper's block shape. With 312 outlined, the 312 tests fall straight through to the
  fee checks, which is the original's 0xd10/0xd58 `jeq r0,0,<312>` shape. MachineBlockPlacement then lays the 330 and 338
  error blocks inside validate (error order 298 289 330 296 326 338 306 312 307 334). Main and the original keep them
  after 307 (main 296 326 306 312 307 330 338; original 306 296 326 312 307 330 338). `tools/mdiff.py` shows that the lost
  difflib tokens are the original's 330/338 blocks (0x1560-0x1720) and the 296 to_string run (0xf40-0xff0).
- IR bound: branch weights on T's cashback/330 test (2000:1, 1:2000, 20:12, 12:20; `tools/post.py`) do not bring the
  330 block back after 307. It moves to the tail at 2000:1. M is 2,191 to 2,199.

## 4. Repay fills priced on the T base (ebe5387, same oracle)

| fill | bytes | M | fM | rM | rfjM | true LCS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| T | 27,184 | 2,198 | 2,295 | 2,510 | 2,765 | 2,212 |
| T + `c_vb` (validate takes `holder:bool`) | 27,184 | 2,185 | 2,296 | 2,498 | 2,765 | 2,199 |
| T + `ov_e` (shared override `then_some/unwrap_or` in the non-holder arm) | 27,096 | 1,772 | 2,220 | 2,100 | **2,793** | 1,932 (rfj 2,991) |
| T + `ovt` (whole sharing tree per arm in validate) | **27,400** | 1,331 | 1,826 | 1,617 | 2,425 | 1,541 |

The OV family stays an RA/frame collapse on the T base, as w14a126 found on main and on base O. `ovt+T` lands at
exactly 27,400 B but is 900 M down. The original's validate-only runs (0x0d78-0x0e58, 0x10e8-0x11a8, 0x1490-0x1548 and
0x1800-0x18f0: the per-arm `shared`/fee-tag threading, decoded in w14a123 `decode_orig_runs.txt`) are the faithful
216 B. Every source form tried so far that produces them collapses register and frame assignment (w14a89, w14a106,
w14a126 and here).
The size-knob catalog has no positive-byte knob without a ratio loss (`$SWARM/w11/sizeknobs-cto.json`), so plain padding
cannot repay the 216 B either.

## Tools (experiment only; under `tools/`)

- `thr.py`, `ibfi.py`: the outline-decision oracles above (no build slot, about 8-15 s each).
- `g141.py`: genes (`T`, `h307`, `h312`, `bor312`, ...). `T` is written as substring edits, so it composes after other genes.
- `cap.sh <name> <genes> <slot>`, `par2.sh <spec>`: capture, then thr + ibfi + inl + fr + rx in one results line.
  They need the w14a126 `tools/` bundle (cv.sh, capraw.py, rx.py, fr.py, oracle.py) in `$OUT/tools`.
- `post.py <rx> <name> <edits>`: edits the post-O3 `m.ll` and runs llc (bounds only).
- `mdiff.py a b [lo hi]`: the original's offsets that a matches and b does not (difflib), with the original's disassembly.
- `fmap.py a b`: census of (original r10 offset -> candidate offset) pairs over the frame-masked alignment.
- `screen_results.txt`: every oracle row.
