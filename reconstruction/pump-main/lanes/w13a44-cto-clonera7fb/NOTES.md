# w13a44-cto-clonera7fb: why the sharing-CPI clone run keeps the accounts pointer in a register

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 16c10e631 / 52c0b087c (same admin_cto tokens; 0.62043, 3,306 slots, clonefeat 2/6).
Angle: continues w13a09-cto-cpiclone next ideas 1-2 (diff 7fb9a5e3e7a2's regalloc against main). The w13a40
lane (same angle, started earlier) did the 6/2-gene screen with full builds; this lane did the regalloc trace.
Scratch: `~/.cache/pumpfun-reconstruction/lanes/w13a44-cto-clonera7fb/` (not in git).
Debug LLVM with `-debug-only=regalloc`: `~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/llc` (18.1.7 + asserts,
same output as the SDK llc on these modules).

No source change is proposed yet. This PR holds the mechanism, oracles and tools.

## 1. The clone run follows one global-split decision

The AdminCto accounts pointer is `%0` (`LDD %ctx,8` at MIR slot 96). Its `RS_Split` round (`tools/rsplit.py ra.log 0`):

| | chosen | static / total cost | region bundles | clone run (bundles ~165-210) |
| --- | --- | --- | --- | --- |
| main 16c10e6 | `$r6` | 3.013 / 3.068 (r8 2.12/3.15, r9 static 4.03 rejected) | 96 | **inside** the r6 region |
| 7fb9a5e3e7a2 (6/2) | `$r9` | 2.144 / 3.218 (r6 3.53, r8 3.53) | 57 | outside (region ends at EB#155) |

On main, `%0`'s r6 piece is later split into a clone-run component (`%1686`) that is reloaded once and gets a free
`$r5` (2/6). In 7fb9 the clone-run blocks are in the stack complement and every use reloads (6/2, the original's form).
r9's region stops before the clone run in 7fb9 because r9 is busy there: it holds the Err-payload class (below).

## 2. 6/2 needs swept coalesced into the Err-payload class

`tools/payreg.py` reads the return block's payload register and the registers that store `swept` into the event
(`[r10-0x218]`):

| build | clonefeat | Err payload reg | event swept from | merged |
| --- | --- | --- | --- | --- |
| original | 6/2 | r9 | r9 | yes |
| hc/keep/7fb9a5e3e7a2 | 6/2 | r9 | r9 | yes |
| w3-adminCTO/out/e14 | 6/2 | r9 | r9 | yes |
| w10r1-admincto-stitch c4_shared_bitand | 6/2 | r8 | r8 | yes |
| w10r1-admincto-errseq t03_feesfn_ia_unwrap | 6/2 | r7 | r7 | yes |
| hc/keep/f6eb16639005 | 5/3 | r9 | r9 | yes |
| admincto-reconstruction t4 | 6/2 | r6 | r1/r3/r2 | no (old shape) |
| **main** | **2/6** | r8 | r1 (reload of `[r10-0x968]`) | **no** |

In the original the class is visible directly:
- orig 0x5868 return block: `ldxdw r4,[r10-0x8f0]; stxdw [r4+8],r9; stxdw [r4],r7; exit`.
- The sweep exit test `0x3c60 jne r7,2` and the sweep AMM-transfer `?` (`0x3b98 ldxdw r9,[r10-0x7e8]; ja 0x5868`)
  go straight to it. `swept` stays in r9 from 0x3c40 to the event store at 0x5030.
- Post-sweep CPI errors (sharing 0x4aa0, pool 0x4e48, 0x5588) meet in **0x54e0 `mov64 r9, r1`**. That copy survived
  coalescing, so the post-sweep error chain was kept apart from the class that already held `swept`.

Ours: the sweep exit's Err edge goes through a copy block (`0x60c0 mov64 r8, r2; ja return`), `swept` is spilled at
0x3bf8 and reloaded for the event, and the post-sweep CPI errors load the payload straight into r8.

## 3. Why main does not coalesce swept: coalescer block order

RegisterCoalescer visits blocks by loop depth, then pred+succ count, then block number (`coal.txt` from
`tools/radbg.sh`):
- `bb.360.bb62` (post-sweep Err merge: sharing CPI, pool CPI, bb60 event/Clock errors; 3 preds + 1 succ) holds
  `%1658 = COPY %380`. It runs first and joins the post-sweep chain into the Err-payload class `%1658`.
- `bb.269.bb81` (sweep exit Err edge; 2 preds + 1 succ; it exists because the error phi in `bb64` needs
  `inttoptr` of the i64 sweep payload) holds `%1658 = COPY %284`, where `%284`/`%1629` is the sweep payload that is
  also `swept`. It runs later and fails: `interference at %1658:29@64304r`. That is the sharing-CPI result copy,
  placed before the branch, where `swept` is live on the Ok edge.
- In 7fb9 the sweep exit block has 10 predecessors and no separate Err-edge block (the payload phi is ptr-typed, and
  the Ok/native path is threaded around it). The swept/payload copy sits in that block and coalesces first
  (`56320B %1669 = COPY %285`). The final-block join of the post-sweep chain then fails, as in the original.

## 4. IR oracles: coalescing is necessary, not sufficient

The llc oracle runs on main's post-opt slim module (`tools/llcb.py`; `rx.py` for raw-IR edits). It reports ratio,
clonefeat and segstat 0x3e00-0x4a00.

| oracle | swept merged | payload reg | clonefeat | bytes | ratio |
| --- | --- | --- | --- | ---: | ---: |
| main | no | r8 | 2/6 | 27,400 | 0.62043 |
| o1: hoist bb81's `inttoptr` into sweep.exit (bb81 empty) | yes | r7 | 2/6 | 27,432 | 0.48024 (tail-dup of the exit test lost, return block moves to 0x3f18) |
| o9: bb60 (event/Clock errors) straight to bb64, so bb62 has 2 preds | yes | r7 | 2/6 | 27,456 | 0.54317 |
| lt58 (w13a27): drop `dest` lifetime.end in bb58, so sweep `?` edges thread to the return | yes | r7 | 2/6 | 27,552 | 0.44182 |
| llc `-grow-region-complexity-budget` 0 / 100 / 200 | no | | 6/2 | 27,504 / 27,344 / 27,456 | 0.437 / 0.557 / 0.563 |
| same budget at 400 and above | | | 2/6 | 27,400 | = main |

Each R1 oracle (swept in the class) puts the class on **r7**. `%0`'s split still picks r6 with the clone run inside it,
because r7's static cost in validate's `%0` use blocks is 5.16 (r9 4.01).

So the clone-run RA needs two things:
- **R1**: the swept copy coalesces into the Err-payload class before the post-sweep chain does.
- **R2**: the class lands on the register that `%0`'s global split chooses, and that register is cheap in
  validate's use blocks (r9 static 2.14 in 7fb9 vs 4.03 on main).

R2 is the validate-region frequency/interference coupling that w13a09 saw: every 6/2 build got it from
validate-region genes. No single-gene port achieves it on main (w13a40's screen). The budget knob only shows that
main sits far from the flip: the threshold is between 200 and 400, against a default of 10,000.

## Tools (`tools/`)

- `llcb.py <m.ll> [--dbg] [llc args]`: llc a slim execute module, print ratio/slots/clonefeat/segstat.
- `llcdis.sh <m.ll>`: function disassembly from the llc object. `sodis.py <so|orig>`: from an unstripped build.
- `radbg.sh <dir>`: debug-llc regalloc log plus MIR (`mi0.txt`) and coalescer (`coal.txt`) sections.
- `rsplit.py <ra.log> <vreg>`: per-register global-split candidates (static/total cost, bundle list).
- `regstate.py <ra.log> <vreg> <reg>`: what occupies a register when `%vreg` enters its split round.
- `payreg.py <so|dis>`: Err-payload register and the registers that store `swept` into the event.
- From w13a01/w13a40/w13a09/w13a14: `rx.py`, `capraw.py`, `ctoracle.py`, `clonefeat.py`, `segstat*.py`, `obj.py`;
  `swedit.py` from w13a27.

## Ledger

Approach `clone-ra-mechanism`, keys `0x22a10-w13-16c10e6-clonera44-*`.
