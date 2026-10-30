# w13a17-cto-outlineport: outlined `to_string` (307/312) ported to main 74b31714a

Target: `0x22a10 admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 74b31714a (0.51348, 3,334 slots, 88 lddw, 5 inlined `to_string`). Continues w13a04 (#2912) and w13a06 (#2903).
Ledger keys `0x22a10-w13-74b3171-outlineport-*-v1`. Every ratio below was produced by the raw-IR capture + `opt -O3` +
`llc` oracle, which reproduces `measure.sh` exactly (checked on main, n4c, n7c, c3, n7n).

## 1. Ports of the w13a04 / w13a06 outlined forms (all 86 lddw, 7 `to_string` calls, 154+3 calls)

Genes are in `tools/genes.py` (w13a04 genes plus the ones added here). `abstr` = register/frame/jump-masked
ratio (`tools/gaps.py`).

| trial | genes | bytes | ratio | abstr |
| --- | --- | ---: | ---: | ---: |
| main | | 27,400 | 0.51348 | 0.86669 |
| i1 | `IN296` (= noinline-307/312 oracle) | 26,888 | 0.30299 | 0.85969 |
| n4c | `EL296 TAKE306 CBA` | 27,112 | 0.33634 | |
| n7c | `EL296 TAKE306 OVMK CBAO` | 27,192 | 0.48076 | |
| n7n | `EL296 OVMK CBAO` | 27,160 | **0.48255** | 0.84597 |
| a4 / a4t | `HM` / `HM TAKE306` (w13a06 per-site `matches!`) | 26,904 / 26,936 | 0.43017 / 0.43051 | |
| **c3** | `EL296 TAKE306 CBA FLE` | 27,176 | **0.48241** | 0.84421 |
| d3 | `EL296 OVMK CBAO FLE` | 27,256 | 0.47237 | 0.84354 |
| k2 | `EL296 OVM2 CBAO FLE` (override only in validate's arm) | 26,968 | 0.43690 | **0.85085** |
| c1/c2/d1/d2/e1 | + w13a02 fee-first `Result<(Option<u64>,Pubkey)>` (+ non-SSA `x`) | 26,888-27,096 | 0.208-0.230 | |
| h1-h3 | c3 + non-SSA `x` (three placements) | 27,104 | 0.435-0.475 | |
| g1/g3/g5/g6/g8, i2-i4, k1/k3/k4 | see ledger | | <= 0.482 | |

`FLE` = w13a05's `let Some(f)=fee else{return Ok(target)};`. On the outlined base it is what keeps fi0 (`_11.i`, the
0-byte `unwrap_failed` arg) unmerged: n4c 0.33634 -> c3 0.48241, and c3's r4 spill is the original's `-0x928`.
The fee-first X24 form collapses every outlined base (fi0 merges again and `_114.i` is not hosted).

## 2. Why the outlined forms trail main: StackColoring group table (`tools/sc.sh`, debug llc)

`sc.sh <xdir>` runs `llvm-dbg/build/bin/llc -debug-only=stack-coloring` on the extracted function and prints execute's
merge groups (representative <- members). The 7 B / 1 B pieces decide the frame:

| build | `_11.i` (1 B) | `_114.i` (16 B) | own 7 B slot | `val.sroa.6.i` |
| --- | --- | --- | --- | --- |
| main | <- `_121.i` | <- `target.sroa.0` | none | <- `target.i.sroa.0` |
| n4c | merged into `_114.i` (frame bottom -8) | <- `_11.i` | `_121.i` own at 0x449 | <- `target.sroa.0` |
| c3 | alone | <- `_40.sroa.16` (validate result piece, from FLE) | `target.sroa.0` <- `_121.i` | <- `target.i.sroa.0` |
| n7n | alone | <- `target.i.sroa.0` | `target.sroa.0` <- `_121.i` | <- `_87.i.sroa.0` |

So in every outlined form `target.sroa.0` (7 B) cannot join `_114.i` and becomes its own object at 0x660, pushing
`st`/`holder_key`/`mint` and all spills 8 B deeper (n7n/n7c also keep the 32 B entry copy `_26.sroa.5` of `new`
unmerged above `st`, +0x28). The original is 8 B *shallower* than main there (first holder_key store `-0x6a8`, main `-0x6b0`).

## 3. Frame-only ceiling of the best outlined form (IR edits, `tools/greedy.sh`)

`xo.sh` extracts execute (`opt -passes=internalize,globaldce`) and runs llc on it alone: 0.3 s per variant, same bytes
and ratio as the full module (checked on main and 20 variants). `scan.py` tries one edit per alloca
(`nolt` = drop lifetime markers, `mv` = move the alloca before `holder_key`), `greedy.sh` climbs.

| base | edits | bytes | ratio |
| --- | --- | ---: | ---: |
| main | `mv _114.i before holder_key` (w13a02 X24 lever) | 27,400 | 0.53685 |
| c3 | `mv _114.i before holder_key` | 27,176 | 0.51368 |
| c3 | + `nolt _408.sroa.6` | 27,176 | 0.51759 |
| c3 | + `nolt _40.sroa.43` | 27,128 | **0.52769** (greedy stops) |

The outlined c3 with three frame edits beats main as it is, but trails main with the same X24 lever, and it is
224-272 B short.

## 4. Where the bytes are (abstracted alignment, `tools/gaps.py orig cand`)

The abstracted ratio of every outlined form (0.842-0.851) is below main's (0.867). `IN296` alone is 0.860 at -512 B:
the original spends those bytes elsewhere, in the per-arm fee-None threading of validate's non-holder arm (orig 0x0d78-0x0e58:
cashback flag, `shared` test, `st.creator` 8/24 pieces stored to two slots, own fee-tag test, direct jump into the tree).
w13a05 measured that threading as +416 B on main in IR, about the outline's -432..-512 B.

## Tools (`tools/`)

- `gv.py <name> <base> GENE..`, `genes.py`: crate copy with genes (newline count asserted).
- `src.sh <var> [work]`: raw-IR capture (one build slot) + `opt -O3` + `xo.sh` + frame map -> `x/<var>/`; `batch.sh` runs two at a time.
- `xo.sh <bc|ll> <dir> [mir]`: extracted-function llc oracle (0.3 s) + optional PEI frame map (`mirframe.py`).
- `scan.py`, `greedy.sh`: nolt/mv single-edit scans and greedy climb on `x/<var>/ex.ll`.
- `sc.sh`, `scg.py`: StackColoring merge groups of execute (needs `~/.cache/pumpfun-reconstruction/llvm-dbg`).
- `gaps.py`: abstracted alignment, orig-only / cand-only runs.
- `recx.py`: ledger record for an oracle result.
