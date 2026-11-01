# w17a09-shim-pdaslot: the E1 holder-rewards PDA slot (admin_cto 0x22a10, shim track)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Region E1 (original 0x0-0x280, `w17a01-ghidra-decomp` REGIONS.md): the original calls
`find_program_address` first, into the aligned scratch `[r10-0x2d0]` that `sk` and `Pubkey::default()` reuse, with
the seeds array at `[r10-0x450]`, and copies `holder_key` out as 4 aligned descending pairs to `[r10-0x6a0..-0x688]`.
Main tests `shared` first and writes the `(Pubkey,u8)` result to the odd slot `-0x679` (hk alive to the end),
with the seeds at `-0x2d0` and odd-offset copies.

## Result (landable shim, zero loss)

| build | admin_cto ratio | M | slots | bytes | normalized/raw | differential |
|---|---:|---:|---:|---:|---|---|
| main ae14cbeb4 (baseline at landing) | 0.67945 | 2,268 | 3,170 | 27,400 | 1034/1034 | 388/0 |
| **h7 (this PR, merged with ae14cbeb4)** | **0.67975** | 2,269 | 3,170 | 27,400 | 1034/1034, no losses | 388/0 |
| same edit on main fd78179 | 0.67855 -> 0.67885 | | 3,220 | 27,400 | 1034/1034 | 388/0 |
| same edit on main af6ca66 (n7) | 0.67825 -> 0.67855 | 2,264 -> 2,265 | 3,220 | 27,400 | 1034/1034 | 388/0 |
| same edit on main 442ae70 (v7) | 0.67615 -> 0.67645 | 2,257 -> 2,258 | 3,141 | 27,400 | 1034/1034 | 388/0 |

Mechanism (`/*shim:*/`-marked, on the existing line 339, no line added):

```rust
let mut hkx=core::mem::MaybeUninit::<[u64;9]>::uninit();/*shim: holder_key in a 72 B slot ...*/
let holder_key:&Pubkey=unsafe{hkx.as_mut_ptr().cast::<Pubkey>().write(Pubkey::find_program_address(..).0);&*hkx.as_ptr().cast::<Pubkey>()}/*shim: PDA result is a temp ...*/;
```

and `validate(..,holder_key,..)`, `sweep(&ctx,holder_key)` take the reference.

- The `(Pubkey,u8)` result is now a statement temporary, so StackColoring merges it into the big `-0x2d0` host:
  the out-param is `-0x2d0` and the seeds move to `-0x450`, exactly as in the original. The holder_key copy is the
  original's 4 aligned pairs `-0x2b8..-0x2d0 -> -0x688..-0x6a0` in the original's descending order. Original
  0x80-0x138 (24 tokens: seeds, call, copy) is now byte-identical.
- Making hk short-lived alone (w13a39 hkshort, w13a32 hk3, v3 below) loses 40 B of frame: every object below moves up
  (mint `-0x6c0 -> -0x698`) and costs about -0.075. The 72 B holder_key keeps the key at `-0x6a0` and its 40 B tail
  occupies `-0x680..-0x658`, the bytes hk used to hold. In the original that region holds the target[8..32) host
  (24 B at `-0x680`, J1/J2 at orig 0x243b0) and the 9 B `new` piece (`-0x668/-0x660`, E3). **Peel path:** when the
  newpieces/x24host work materialises those objects, shrink `[u64;9]` back to a Pubkey.
- The LCS gain is only +1 because the PDA block still follows the shared test. The order is the next step (below).

## PDA-first (the E1 call order) is structurally right but hits a greedy-RA cascade

`v8` = this shim with the PDA moved before `shared`. Its pre-RA machine code for E1 is the original's (curve load
before the creator memcmp, curve reload after `data_is_empty`, shared phi spilled with a `mov r1,0` default), and the
listing at orig 0x38-0x138 is byte-identical (E1 +24 tokens). Fully masked LCS (regs+frame+jumps) is 2,808 vs main
2,793, so the skeleton is +15 better. But the exact M collapses: slim oracle M 1,954 @27,440 B vs main 2,258 (on 442ae70).

Region deltas vs main (oracle, 442ae70): E1 +24, J2 +4, W1 -3, S1 -14, **T1 -256**, C1 -36, P1 -10, W2 -9.

Root cause, from `llc -debug-only=regalloc` (debug llc, `tools/raseq.py`):

| greedy step | main (shared first) | v8 (PDA first) |
|---|---|---|
| curve box ptr | `%4@1648` (after the PDA) evicts r7 | `%5@832` (CSE'd/PRE'd across E1) evicts r7 |
| shared phi | evicts r6 | evicts r6 |
| stack-args copy (r5) | `[16,656]` evicts r9 | `[16,1056]` evicts r9 |
| sharing_config ptr `%1` | `[272,1104]` gets r7 (free: curve starts at 1648) | `[672,1536]` **evicts accounts `%0` from r8** |

Accounts then lands in r6 and the split-product hint carries r6 to every later piece (W1/S1/T1 r8<->r6 swaps), which
re-sorts T1 temps (r1 -> r3, 143-170 sites) and shifts every T1 spill slot by 8.

Fixing the first divergence is possible with two marked shims (`v10` = IR `e1abcb`): read the sharing_config
AccountInfo pointer volatile **before** the PDA (so `%1` is long and queued before the stack-args copy) and re-read
the curve box pointer volatile at `quote_locked` (no PRE across E1). The first ~25 greedy decisions then equal main's
exactly (accounts r8, sharing_config r7, shared r6, stack args r9), but later decisions still diverge (T1 spill slots
+8, C1 -69): M 1,880. A llvm.expect scan over every `br i1` of execute/validate/sweep/wallet (108 variants on each of
v8, e1ab, e1abcb) found nothing better than e1abcb+`ex5f` 1,947.

Second divergence, traced on a clean base (main e679b59 `main4` M 2,267 vs the same shims `g10` M 1,917;
`tools/radiff.py`, `ra/*.ra.txt`): every greedy decision outside E1 is identical up to the stack-arg load range
`%394` evicting accounts `%0` from r8 (decision #424 in main, #451 in g10). Main then allocates the C1/W2 range at
slot 58176 straight into the freed r8. In g10 the volatile curve re-read is a separate long range (`%15`, start slot
3728, hint r8). It is dequeued first, evicts r9, and the re-split accounts piece keeps r8 across C1 [57952..]. The
58176 range must then evict r7, and that cascades. In main the curve pointer for `quote_locked` is `%4@1648`. It is
one of the first ranges dequeued (decision 7), because it starts right after the PDA call. So the curve range would
need main's start and size without overlapping the sharing_config range. No single source spelling found here gives
both. PDA-first therefore needs its own RA-basin re-tune, as main needed from 0.49 to 0.68, or it must wait until
E3/J1 (new pieces, target host) match the original and the RA converges.

**Caveat on the 442ae70 oracle rows:** `ir/m442.ll` (copied from w17a03's out dir) was w17a03-shim-unlockspill-2's
variant (it carries the pump_fees volatile reload at C1), not plain main. Its M 2,258 equals that PR's 0.67645, while
plain 442ae70 measures 2,257. The v-variants were captured from plain 442ae70, so v-vs-m442 region deltas carry
C1 -1 from that difference. The g-rows and every real build in this file use clean bases.

## Trials (slim raw-IR oracle unless noted; main 442ae70 oracle M 2,258 = real 2,257)

| id | change | M @ bytes | note |
|---|---|---|---|
| v1 | task proposal: PDA-first, scoped `MaybeUninit<[u64;5]>` for PDA, sk and default | 1,489 @27,496 | sk/default copies add code, T1 -480 |
| v2 | v1 with a function-long scratch | 1,563 @27,496 | |
| v3 | PDA-first `let holder_key=FPA.0` | 1,773 @27,440 | 40 B frame shift + RA cascade |
| v4 | PDA-first, main binding (hk alive) | 1,941 @27,440 | RA cascade |
| v5/v5b | main order, PDA into a long-lived aligned `[u64;5]` | 2,257 @27,400 | out-param -0x680, copy ascending |
| v6 | v5 PDA-first | 1,941 @27,440 | = v4 |
| **v7** | **main order + 72 B holder_key slot, PDA temp** | **2,258 @27,400** | **real 0.67645 on 442ae70; n7 = 0.67855 on af6ca66** |
| v8 | v7 PDA-first | 1,954 @27,440 | E1 exact 0x38-0x138, RA cascade |
| v9 | v8 + early volatile sharing_config ptr (= IR e1ab) | 1,963 @27,424 | stack-args copy evicts accounts |
| v10 | v9 + volatile curve re-read at quote_locked (= IR e1abcb) | 1,880 @27,408 | first 25 greedy steps = main |
| IR | expect true/false on E1/E2 branches; volatile shared; volatile sharing_config/curve reloads | <= 1,963 | |
| g8 / g10 | v8 / v10 on clean main e679b59 (oracle 2,267) | 1,969 / 1,917 | trace table above |
| b9/b8/b10 | b01 (validate takes holder_key by value, w17a14) on main bf01b5f (oracle 2,270) with the hkx placeholder at 9/8/10 words | 1,836 / 1,983 / 1,732 @27,360 | V1 +8..+10 at 9/10 words, but T1 -109..-255, C1 -27..-77: resizing the placeholder does not rescue b01 |

**Strongest lead (k8, PDA-first on current main bf01b5f, which already has the hkx slot):** oracle exact M 1,945 @27,384 B
vs main 2,270 @27,400, but **fully masked (regs+frame+jumps) 2,855 vs main 2,794 = +61 structure**. Per region
(fully masked): E1 +34, C1 +28, J1 +5, S1 +2, T1 -8, W2 -2. The exact loss is RA naming only (T1 -240, C1 -79,
S1 -13 exact). So PDA-first is the right skeleton, and now it shrinks the code by 16 B instead of growing it 40 B. What remains is an RA-basin
re-tune of k8: the T1/C1 spill-colour shims that main carries were tuned on the shared-first basin.
First re-tune screens on k8, both no gain: llvm.expect true/false on all 54 `br i1` (`brscan.py`, max = base 1,945), and
the probabilities of main's six expect shims (rcinc/rcincp traps, 312 `expect_p`, default-quote) over a 10-point grid
(`probscan.py`, 59 variants, max +1). `k10` = k8 + the two first-divergence shims (early volatile sharing_config
pointer, volatile curve re-read at quote_locked) gives 1,921 exact and 2,848 fully masked.

**For w17a14-shim-shimwhole (b01+p8+PF composite):** its exact loss was attributed to "hk gone, holder_key/mint
+0x28" (40 B frame shift). The landed `[u64;9]` holder_key slot (#3993) is exactly that 40 B placeholder. On current
main the PDA result is already a temporary at -0x2d0, so PF on top of main is just the statement reorder (`k8`). The
frame below -0x658 no longer moves.

## Tools (`tools/`, experiment only)

- `cap.sh <name> <slot>`: copy the worktree crate, overlay `src/<name>.rs`, capture pre-opt IR (`capraw.py`),
  `preslim.py`, score with `fx.py` (w17a06-shim-irbeam tools). About 70 s per capture under load.
- `mk.py` + `edits.py`: the exact source edits of every variant (line count asserted).
- `dis.py <fx name> [--range a-b] [--full]`: disassemble an fx `fn.bin` and diff it against the original window.
- `reg.py <names..>`: matched tokens per REGIONS.md region; `mask.py`: exact vs frame/jump vs fully masked LCS.
- `irs.py <base.s.ll> <spec.py>`: IR edit screen with region deltas; `brscan.py`: llvm.expect scan of every `br i1`;
  `probscan.py`: grid over the probability constants of the expect shims already in the module.
- `raseq.py <fx name>`: debug-llc greedy trace, first N assign/evict decisions (vreg@slot->reg); `radiff.py a b`: first divergent greedy decisions outside E1, keyed by live-range start slot.

Ledger keys: `0x22a10-w17-442ae70-pdaslot-<id>-v1`.
