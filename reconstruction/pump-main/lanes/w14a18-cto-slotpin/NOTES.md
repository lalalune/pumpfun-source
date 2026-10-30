# w14a18-cto-slotpin: MIR spill-slot pin oracle and the frame bound of every skeleton-positive admin_cto base

Target: `0x22a10 admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main f8dc9016f (0.63481, 3,173 slots; #3241) for the full table, and cef0574cf (0.63421) to check against the
w14a08 numbers. Continues w14a08-cto-outlinefill (#3232), next idea 1.
Ledger: approach `slotpin`, keys `0x22a10-w14-{f8dc901,cef0574}-slotpin-<base>-<weights>-v1` (26 rows).

**Result: a calibrated MIR-level frame-pin oracle (two stages) and the bound table. With any legal frame, no
skeleton-positive base beats main by 0.005. The best, U2 = e3+tu8+s1, is +13 matched instructions on f8dc and +17 on
cef0574, and it is 128 B short. The frame-masked "M" that ranked these bases is not a frame bound: most of what it
credits needs per-access offsets that no slot assignment can produce. No source change.**

## 1. The oracle (`tools/slotpin.py`)

The captures come from the w14a08 raw-IR pipeline (`fw.py` + `fg.py`: rustc raw IR, `opt -O3`, extract execute, `llc`).
`fw.py` with `KEEP=1` keeps `ex.bc`. The main capture reproduces the baseline exactly: 0.63481 at 27,400 B on f8dc,
0.63421 on cef0574.

Two stages, both resumed with the release `llc` (`-O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections`):

- **Colour level** (`prep <ex.bc> <dir>`). `-stop-before=prologepilog` gives the frame after StackSlotColoring. `run`
  rewrites execute's `stack:` objects as `fixedStack:` objects at chosen offsets, renames every `%stack.N` to
  `%fixed-stack.M`, and resumes with `-start-before=prologepilog`. The MIR round trip prints outgoing stack-argument stores
  as `[r10 + X]`, where the direct build has `[r10 - (0x1000 - X)]`, so `fntext` rewrites those lines back.
  - Calibration: the identity pin (each object at its own PEI offset) gives byte-identical execute text to the direct
    build (the RAR capture and main f8dc).
  - Check: VS (sk by value) has the same code as RAR+w12 and differs only by a -40/+32 B frame shift. Pinned to RAR+w12's
    slots it gives M 2,103, against RAR+w12's 2,101. So the vote mapping recovers a pure frame shift completely.
- **Interval level** (`prep <ex.bc> <dir> stack-slot-coloring`). `-stop-before=stack-slot-coloring` keeps one frame index
  per spilled live interval: 184 intervals on main, coloured into 109 slots. Resuming there leaves LiveStacks empty, so
  StackSlotColoring does nothing. The code is identical to the real build except for frame offsets.
  - The MIR parser renumbers frame indices, so `prep` maps objects by position.
  - `colmap` reads each interval's real colour offset off the line-aligned real build.
  - Calibration: pinning every interval to its colour reproduces main f8dc and cef0574 byte for byte (`cal=True` for
    all 26 bases).
  - `mkmap2` maps each interval or alloca to a target slot by votes over the frame-masked alignment against the reference.
    Intervals may share a target only if their live ranges are disjoint. The live ranges are parsed from
    `llvm-dbg llc -debug-only=stack-slot-coloring`. Allocas stay one-to-one. So every pinned frame is a legal colouring.
- Each trial takes about 0.3 s, with no build slot.

## 2. Bound table (`data/bound.jsonl`, `data/bound2.jsonl`)

- M = ratio x (3339 + n) / 2 is the number of matched original instructions. Compare M, not ratio, off the pin.
- masked M is w14a08's frame-blind number (`mratio2.py`).
- Colour pin uses one-to-one colours, mode b (the original's slots), spill slots / all objects.
- Interval pin is the legal-colouring bound against the original. Main-frame pin pins the base to main's own slots
  at interval level.

| base | genes | weights | bytes | ratio | M | masked M | colour pin M (spill/all) | interval pin ratio | **interval pin M** | main-frame pin M |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| main f8dc | (main) | - | 27400 | 0.63481 | 2119 | 2260 | 2187/2194 | 0.67645 | **2258** | 2119 |
| | RAR | 1:2 | 26920 | 0.63494 | 2101 | 2298 | 2166/2173 | 0.67573 | **2236** | 2090 |
| | RAR | - | 27368 | 0.62410 | 2082 | 2206 | | 0.66397 | **2215** | 2079 |
| | e3+tu8 | - | 27336 | 0.61338 | 2045 | 2374 | 2183/2197 | 0.67906 | **2264** | 2102 |
| | s1 | - | 27368 | 0.61900 | 2065 | 2255 | 2178/2185 | 0.67926 | **2266** | 2093 |
| | **U2 = e3+tu8+s1** | - | 27272 | 0.61021 | 2032 | 2365 | 2186/2200 | 0.68198 | **2271** | 2095 |
| | RAR+V2N | 1:2 | 26936 | 0.56133 | 1858 | 2332 | 2116/2187 | 0.68310 | **2258** | 2085 |
| | RAR+HK0 | 1:2 | 26920 | 0.55848 | 1848 | 2298 | 2096/2175 | 0.67694 | **2240** | 2096 |
| | RAR+VS | 1:2 | 26920 | 0.56059 | 1855 | 2298 | 2097/2169 | 0.67423 | **2228** | 2093 |
| | RAR+B3 | 1:2 | 26880 | 0.57493 | 1901 | 2166 | 2155/2162 | 0.67171 | **2221** | 2058 |
| | f2 = RAR+HB0 (w14a07) | - | 26912 | 0.62868 | 2080 | 2296 | 2146/2153 | 0.67009 | **2217** | 2077 |
| | RAR+V1 | 1:2 | 26872 | 0.52995 | 1752 | 2104 | 2015/2086 | 0.65003 | **2149** | 1991 |
| | RAR+V2 | 1:2 | 27104 | 0.51709 | 1717 | 2125 | 1905/2007 | 0.62049 | **2056** | 1899 |
| | f2+V1 | - | 26864 | 0.52277 | 1728 | 2089 | 1991/2039 | 0.63561 | **2101** | 1972 |
| | RAR+PDA-first | 1:2 | 26968 | 0.56461 | 1870 | 2064 | 1949/1955 | 0.60296 | **1997** | 1875 |
| main cef0574 | (main) | - | 27400 | 0.63421 | 2117 | 2258 | 2185/2192 | 0.67585 | **2256** | 2117 |
| | RAR | 1:2 | 26920 | 0.63433 | 2099 | 2296 | 2164/2171 | 0.67513 | **2234** | 2088 |
| | **RAR+V1** | 1:2 | 26912 | 0.57095 | 1889 | **2325** | 2108/2179 | 0.68158 | **2255** | 2076 |
| | RAR+V2N | 1:2 | 26912 | 0.56068 | 1855 | 2325 | | 0.68160 | **2252** | 2079 |
| | RAR+B3 | 1:2 | 26912 | 0.58093 | 1922 | 2193 | | 0.68158 | **2255** | 2077 |
| | RAR+HK0 | 1:2 | 26920 | 0.55787 | 1846 | 2296 | | 0.67634 | **2238** | 2094 |
| | RAR+QLIN | 1:2 | 26808 | 0.56269 | 1858 | 2297 | | 0.67293 | **2219** | 2061 |
| | RAR+PDA-first | 1:2 | 26968 | 0.56552 | 1873 | 2066 | | 0.60326 | **1998** | 1878 |
| | e3+tu8 | - | 27328 | 0.61407 | 2047 | 2375 | | 0.67977 | **2266** | 2104 |
| | s1 | - | 27368 | 0.61841 | 2063 | 2253 | | 0.67866 | **2264** | 2091 |
| | U2 | - | 27264 | 0.61090 | 2034 | 2366 | | 0.68269 | **2273** | 2097 |

The cef0574 rows reproduce w14a08 exactly: main M 2,117 / masked 2,258, RAR+w12 2,099 / 2,296, and RAR+V1 1,889 / 2,325.

Findings:

- **RAR+V1 has no frame-limited gain.** w14a08 credited it with +67 masked M over main. With the original's frame at
  interval level it reaches 2,255, against main's 2,256. Pinned to RAR+w12's or main's own frame it gets 1,996 or 2,076.
- **The masked-M lead is mostly unreachable by any frame.** For main, masked M (2,260) and the per-access remap bound
  (`splitb.py`, 2,266) both sit close to the interval pin (2,258). For e3+tu8, masked M is 2,374 and the per-access bound
  2,371, but the legal interval pin is only 2,264. `diag2.py` puts the difference in single objects whose accesses align to
  two or more original slots. The biggest is the 32 B alloca `_112.i` (ours 0x470), which the original splits between
  0x470 and 0x488 (22 vs 19 accesses in e3+tu8). The rest is in `_54.i`, `holder_key`, `sharing_update14.sroa.3` and
  `_109.i`. These are StackColoring alloca merges and value identity, not spill order.
- **With the original's frame, main is already about as good as any base.** The interval pin puts main at 2,258 (+139,
  ratio 0.676). The bases sit between 1,997 and 2,273. Only U2 (+13 / +17), s1 (+8) and e3+tu8 (+6 / +10) are above main,
  and all three are short, so they would also need a size repay.
- **Pinned to main's frame, every base is below main** (the best is e3+tu8 at 2,102 against 2,119). No base keeps
  main's colouring.
- **Colour-level (one-to-one, PEI-stage) pins are about 65 M below interval pins** (main: 2,194 against 2,258). Most
  of the frame gap is colouring, meaning which intervals share a slot, not slot order.

Step 4 of the angle (find the 1-3 flipped spill intervals of a base that beats main by at least 0.005 when pinned) does
not apply: no base clears the bar. U2 is at +0.004/+0.005 by M and needs 128 B of size repay.

## 3. Main's own frame levers (`data/perint_main_f8dc.txt`, `data/perobj_main_f8dc.txt`)

- **Single intervals are small.** Moving one interval at a time to its original slot on top of main's real colouring
  gains at most +12 M: SS#180, the accounts-pointer reload interval, moved to -0x8d8. Next come SS#275 (+7),
  SS#179 (+6), and SS#299, #280 and #258 (+5 each). The whole interval pin is worth +139, spread over about 100 intervals.
- **The head of the spill area is where the colours differ.**
  - Colour-level regional pins on main: the head 0x8d8-0x9c8 gives +46 M (0.64859). The middle of the area alone gives
    -13. A -8 shift of the 0xbb0+ tail alone gives -4.
  - On ours, the head colour -0x8d8 holds `holder` (arg r3; its interval has weight 2.459: an entry store plus reloads at
    0x470 and 0x5c0, feeding `and 0xfd` and `and -3`). The original keeps the accounts pointer there and spills `holder`
    to -0x918, with one reload at 0x610 feeding `and 1`.
- **Mechanism.** StackSlotColoring sorts spill intervals by weight, where weight is the sum of the block frequencies of
  their spill and reload instructions. Each new colour takes the next lowest spill frame index, and PEI lays frame indices
  out in order. So the slot order of the spill area is the order of hot-path spill weights. RAGreedy's spill order only
  supplies the indices.
  - On ours, `holder`'s entry-block reloads outweigh the accounts pointer, which reloads in colder blocks.
  - In the original, the single `and 1` holder representation (e3/a1, w14a10) has one entry reload. Moving the accounts
    pointer to the head is worth at most the +12 above.
- **The ratio itself is fragile.** `difflib`'s greedy block matching (which `score.py`/`oratio.py` also uses) makes M
  non-monotone in local edits. `objsplit.py` remaps only the 36 accesses of `_112.i` to their per-access original offsets
  (17 changed lines), and M drops from 2,119 to 2,055. Per-object deltas are therefore noisy at the ±10 M level.

## 4. For other lanes

- **skelunion (w14a15) and sharingslots.** Rank bases by **interval-pin M** (`bound2.py <tag>`; it needs `bw/<tag>/ex.bc`
  from `fw.py` with `KEEP=1`), not by frame-masked M.
  - Ranking (f8dc): U2 2,271 > s1 2,266 > e3+tu8 2,264 > main = V2N 2,258 > HK0 2,240 > RAR+w12 2,236 > VS 2,228 > B3 2,221
    > f2 2,217 > RAR 2,215 > V1 2,149 > f2+V1 2,101 > V2 2,056 > PDA-first 1,997.
  - U2 is the only union worth carrying, and its ceiling with a perfect legal frame is +0.004.
- **Frame lanes.** The remaining frame value on main (+139 M, ratio 0.676 at a legal original-like frame) is colouring.
  Moving an interval means changing hot-path spill weights or alloca StackColoring merges (`_112.i`/`_109.i`, the w12
  "8/24 target split"), not reordering bindings.

## Tools (`tools/`)

- `slotpin.py`
  - `prep`/`run`/`map`: colour-level pin.
  - `prep ... stack-slot-coloring`, `colmap`, `map2`: interval-level pin with a liveness-checked legal colouring.
  - `MERGE=1 map`: many-to-one colour pin (upper bound).
- `bound.py`: colour-level table. `bound2.py`: interval-level table and calibration check.
- `perobj.py`, `perint.py`: single-object and single-interval gains.
- `diag.py`, `diag2.py`: vote and loss breakdown.
- `splitb.py`: per-access (text) frame bound. `objsplit.py`: per-object per-access remap. `iter2.py`: re-alignment
  iteration (it does not improve on iteration 0).
- `recb.py`: ledger rows.
- Capture: `fw.py`, `fg.py` (w14a08 genes plus e3/tu8/s1/HB0 from w14a15 `gen15.py`, V1H = V1 on top of HB0, B3c/QLINc
  for cef0574), `batch.py`, `brw.py`, `capraw.py`, `xo.sh`.
- Paths point at this lane's out dir (`~/.cache/pumpfun-reconstruction/lanes/w14a18-cto-slotpin`). `fw.py` takes
  `BASEVAR=c3` for the cef0574 base copy.
