# w12a08-cto-errorder: admin_cto error-block order

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: the order and form of validation checks and error blocks.
Bases: main 20a1ae9c0 (#2642, 0.43919/3352), then main b5975fa67 (k4 from #2749, 0.45147/3308).
Builds and scratch files: `~/.cache/pumpfun-reconstruction/lanes/w12a08-cto-errorder/` (not in git).
Ledger keys: `0x22a10-w12-<base7>-errorder-*`.

## Error-site census (Source line immediates in layout order)

| build | sequence |
| --- | --- |
| original | 289 298 306 296 326 312 307 330 338 334 410 719 648 660 284 556 |
| main 20a1ae9 and main b5975fa (k4) | 298 289 330 296 326 306 312 307 338 410 334 719 648 660 284 556 |

The original's `to_string` is inlined at 284/289/298/306/296/326 (hot) and outlined at 312/307/330/334/338 (cold).
Main is the same except that 312 and 307 are inlined.

## Oracles (no build slot)

- `tools/orc.py <slim.ll> <prefix>`: llc on rustc's optimized IR (slimmed to execute). It reproduces main's
  execute exactly: 27,400 B, ratio 0.43919 on 20a1ae9 and 0.45147 on k4. The ratio is identical to
  `target_metric.py`, because the tokens mask call and lddw immediates and keep relative jump offsets. Run time is under 1 s.
- `tools/rawx.sh <name> <edits.py> <rawslim.ll>`: raw-IR oracle. It takes the `-C save-temps` no-opt module, slims it with
  w12a10's `mkslim4.py` (the `llvm-extract --recursive` closure of execute), then runs `opt -O3` (SDK v1.44 rustlib opt) and llc.
  It reproduces main exactly on both bases (k4: 27,400 B, 0.45147), and it predicted k01's source build exactly
  (27,128 B, 0.44986). Each run takes about 40 s CPU.
- `tools/skel.py <dis> [lo hi]`: CFG skeleton (branches, calls, LINE/code stores).
  `tools/regmatch.py <dis>`: original tokens matched per 0x800 bucket.

## Mechanisms measured

| change | level | bytes | ratio | error order |
| --- | --- | ---: | ---: | --- |
| main 20a1ae9 | | 27,400 | 0.43919 | 298 289 330 296 326 306 312 307 338 410 334 |
| holder test as `trunc` (orig `and64 r8,1`) | raw IR | 27,216 | 0.43710 | **289 298** 330 296 306 326 312 307 338 410 334 |
| `new` tag loads without `!range` (test stays `trunc`, orig `and64 r1,1`) | raw IR | 27,440 | 0.42479 | 330 298 289 296 326 306 338 312 307 410 334 |
| both | raw IR | 27,256 | 0.42716 | 330 **289 298 306 296 326 312 307** 338 410 334 |
| `new` param without `readonly` (emulates a mutated `new`) | raw IR | 27,656 | 0.41503 | unchanged |
| v04: `if shared&&!holder{target=st.creator}` before sharing_update | source | 27,496 | 0.43032 | ... 338 **334** 410 |
| v02: `holder.unwrap_or(false)`, cashback with `&&` | source | 27,432 | 0.32695 | 289 298 338 296 306 ... |
| v09: `mut new`, `if holder{new=None}`, sharing_update `Some(new)` | source | 27,704 | 0.41615 | unchanged |
| v11: validate takes `holder_key: Pubkey` by value | source | 27,376 | 0.38573 | unchanged |
| v10: v09 + v11 | source | 27,848 | 0.35086 | unchanged |
| v03: sharing_update computed before validate | source | 27,696 | 0.22941 | unchanged |
| main b5975fa (k4) | | 27,400 | 0.45147 | 298 289 330 296 326 306 312 307 338 410 334 |
| k01: `holder.unwrap_or(false)`, cashback `!holder&st.cashback` | source = raw IR | 27,128 | 0.44986 | **289 298** 330 296 306 326 312 307 338 410 334 |
| k4 + `new` tag without `!range` | raw IR | 27,360 | 0.43292 | 330 298 289 ... |
| k4 + both | raw IR | 27,240 | 0.43750 | 330 289 298 306 296 326 312 307 338 410 334 |
| k02: validate takes `holder_key: Pubkey` by value | source | 27,312 | 0.43631 | unchanged |
| k04: validate takes `shared`, non-holder arm returns `if shared{st.creator}else{t}` (t06 on k4) | source | 27,352 | 0.27676 | unchanged; AnchorError temp moves -0x2b8 to -0x2b0 |
| k14: k01 + k04 | source | 27,168 | 0.25064 | 289 298 330 ... |
| k4 + validate's `new` copy kept alive (extra store into the arg copy) | raw IR | 27,600 | 0.41427 | unchanged; tag load only sinks after the mayhem test |
| k4 + 1:2000 / 1:40 / 1:10 weights on the 307/312 memcmp branches | raw IR | 26,920 to 26,976 | 0.41191 to 0.41509 | 307 is moved to the cold tail; weights are no proxy for "cold for inlining only" |

## Why the original lays the blocks out this way (BPI/MBFI)

- MachineBlockPlacement places each error block's second half from the worklist in falling block-frequency
  order, so the error order is a readout of branch probabilities.
- In the original, `holder` (`and64 r8,1`) and the `new` tag (`ldxdw [r10-0x8f8]; and64 r1,1`) are `trunc` tests.
  BPI has no heuristic for those, so they are 50/50. Main's tests are `icmp ne (x&-3),0` and `icmp eq tag,0`.
  The zero heuristic gives those 62.5/37.5, which puts 298 before 289 and 306 after 296.
- Under the original's probabilities (mayhem and holder/new 50/50, `hr==0` and the memcmp tests 37.5%), validate's BFI
  puts 307, 312, 330, 334 and 338 under 2% of entry frequency (cold, so `to_string` is not inlined) and 289, 298, 306, 296 and 326
  above it. This matches the original's inlined/outlined pattern exactly.
- 334 directly after 338 in the original: the fee_configurable test is `jeq r1,0` (zero heuristic: P(error)=37.5%),
  while the range-OK edge is about 0.625 x 0.5 = 31%. The 334 block therefore outranks the OK path in `selectBestCandidateBlock`.
  Main instead lays out the non-holder arm continuation (0x1608) after 338, and places 334 after 410.
- The `new` tag gets `and 1` only when its load carries no `!range`. That happens when the value comes from an
  SROA-split copy. The original loads all of `new`'s SROA pieces before the mayhem test (0x4d8 to 0x538: tag, [1,8) 7 B,
  [8,16), [16,24), [24,33) 9 B). This is the same split as main's `target.i.sroa.*`, so the copy into
  validate's argument was materialized at the top. Removing the deduced `readonly` (r1/v09) only hoists the tag load
  after the mayhem test, and loses 0.02.
- The original also threads the fee checks per arm. The holder arm has its own fee-tag test and ql test that jump straight to FEE2
  (334/338), skipping 330. The non-holder arm tests `shared` inside validate (t06 shape, 0xd98) before
  FEE1 (326/330). Main has one merged fee block that re-tests `holder` before 330.

Status and results of the remaining trials are in `SUMMARY.json`.

Tool inputs: `orc.py` and `regmatch.py` compare against `$OUT/an/orig.dis` (`ORIG_DIS`), which is the original window
disassembled with function-relative absolute jump targets: `dis.py`-style output of `evidence/original/pump/deployed.so` at 0x22a10, 27,400 B.
`rawx.sh` needs the slimmed no-opt module. To make it: capture with `--emit=link,llvm-ir -C save-temps`, then `llvm-dis` the
`*no-opt*.bc`, run `llvm-extract --recursive --func=<execute>` (the w12a10 debug LLVM has it), and run w12a10's `mkslim4.py`.
