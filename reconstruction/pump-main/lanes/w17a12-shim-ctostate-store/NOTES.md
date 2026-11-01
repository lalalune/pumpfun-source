# w17a12-shim-ctostate-store: CtoState flag-store order and early curve-flag loads (shim track)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Regions E2/E3 of the w17a01 Ghidra region table (original 0x280-0x708).
Bases: main 9336aafff (0.67675, M 2,259) for the first grids, then main af6ca66a2 / fc2dce0a7 (0.67825, M 2,264,
3,220 slots) after #3961 landed. Ledger approach `shim-ctostate-store`, keys `0x22a10-w17-<sha7>-ctostore-*-v1`.

**Result: no gain.** No source or IR form of this angle reaches main's M at 27,400 B. About 6,300 post-opt IR cells
and one source shim capture were scored. Main moved to e679b59e9 (0.67915) during the lane; its two new lines are
w17a04 weighted Rc clones in the sweep, outside this region. The structural finding below is exact and reusable, but its register and
spill-slot cascade costs 113-205 M.

## 1. What the original does in E2/E3 (and what main does)

CtoState has the same layout in both programs. `st` sits at [r10-0x38..-0xb]: creator -0x38..-0x20, max_fee -0x18,
and the flags mayhem -0x10, holder_reward -0xf, cashback -0xe, quote_locked -0xd, holder_enabled -0xc and
fee_configurable -0xb. Neither program reloads any flag byte from `st`, so the six `stxb` are dead stores in both.
They survive because `st.creator` is read through memory (orig +0xdc8).

| step | original (window offset) | main af6ca66 |
| --- | --- | --- |
| curve flags | `ldxb` +0xa3 (cashback), +0xa5 (holder_reward), +0xa2 (mayhem) at +0x290..+0x2b0, **before** the quote-mint copy. Cashback and holder_reward spill to -0x8e8/-0x8e0; mayhem stays in r8 | loaded after quote_locked (+0x450..+0x460), in the order a2, a5, a3 |
| global ptr | `ldxdw r6,[r8+0x8]` once at +0x288, kept in r6 for `contains` and the CtoState loads | reloaded in the `contains` block and again after the join |
| creator GEP | `stxdw [r10-0x910],r9; add64 r9,8` in the quote block (+0x350) | none (the copy uses `[r7+0x8..]`, descending) |
| after the quote_locked join | max_fee, +0x43f, +0x43e loads; `stxb` -0xe, -0xf, -0x10; creator copy ascending; `and 1` + `stxb` -0xd; `stxb` -0xb, -0xc; max_fee -0x18 | fee_configurable load, creator copy, max_fee, holder_enabled; `stxb` -0xd first; then -0xb, -0xc, -0xe, -0xf, -0x10, -0x18 |
| cashback bool | not materialised in the entry | `!holder && cashback` materialised with `mov 1; jne; mov 0` and spilled (the constant 1 at +0x300) |

## 2. Exact IR reconstruction of the original sequence (`tools/ce2.py`, cell `ve1n`)

On main's named post-opt module (`opt -passes=instnamer`, byte-identical to main), the edit does three things:

- moves the three curve-flag loads into bb5, right after the curve pointer load, in the order a3, a5, a2;
- moves the global pointer load into bb5 and drops the `contains` block's reload;
- writes bb11 as: loads max_fee, holder_enabled, fee_configurable; volatile stores cashback, holder_reward,
  mayhem; creator memcpy; volatile stores quote_locked, fee_configurable, holder_enabled, max_fee.

`llc` then emits the original E2/E3 sequence almost instruction for instruction (`ps/ve1n/fn.lst` at +0x268..+0x518):
- the global pointer and curve pointer loads;
- `ldxb` a3 with a spill, a5 with a spill, a2 into a callee-saved register;
- the quote-mint copy and the three memcmps;
- max_fee, 0x43f and 0x43e loads, then `stxb` -0xe, -0xf, -0x10;
- the creator copy, then `mov; and64 1; stxb -0xd`, `stxb -0xb`, `stxb -0xc`, `stxdw -0x18`.

Per region (M of the original's tokens, main → ve1n): E2 35 → 35, E3 20 → 29 (the 9336aaf form gave E2 35 → 37,
E3 20 → 31). The whole function drops, though:

| cell | M | bytes | ratio | M masked frame+reg | M masked frame+reg+jump |
| --- | ---: | ---: | ---: | ---: | ---: |
| main af6ca66 | 2,264 | 27,400 | 0.67825 | 2,651 | 2,785 |
| ve1n (IR, the original's E2/E3 shape) | 2,151 | 27,344 | 0.64507 | 2,645 | **2,855** |
| sh1 (source shim, section 3) | 2,059 | 27,368 | 0.61721 | 2,587 | 2,752 |

The skeleton is closer to the original (+70 with frame, registers and jumps masked) but the naming is further away.
The loss sits in T1 (TCF clone run), C1 (sharing clone run), W2 and S1, not in E2/E3. The main cause is spill
colouring:
- the accounts pointer leaves -0x8d8, its slot in both the original and main, for -0x8e0. That changes 21-22 aligned
  accesses (`tools/fmap.py`);
- the `holder` argument (r3) takes -0x8d8. The original spills r3 to -0x918 and main to -0x8e8.

-0x8d8 has 34 accesses in the original, 24 in main and 6 in ve1n. The early flags add two long call-crossing live
ranges, the greedy allocator spills r3 first, and every later spill slot shifts. **A lane that adopts the early-flag
structure must also make the allocator create the accounts pointer's spill slot first and spill r3 late, as the
original does.** That likely needs the original's other entry differences too: the `new` pieces at +0x4d8 (w17a10)
and the PDA-first order with the -0x2d0 sret slot (w17a09).

## 3. Source shim (cell `sh1`, `tools/vars.py`)

The source form, on line 339 with no added line:

- `let (cb0,hr0,my0)=unsafe{(read_volatile(&curve.is_cashback_coin),read_volatile(&..is_holder_reward),read_volatile(&..is_mayhem_mode))}`
  before `quote_locked`;
- `MaybeUninit::<CtoState>`, with `write_volatile` through `addr_of_mut!` in the original order (cashback,
  holder_reward, mayhem | `ptr::write` creator | quote_locked, fee_configurable, holder_enabled, max_fee), then
  `assume_init_ref()`;
- `validate(st,..)`.

It was captured with capraw and scored with the w17a06 slim oracle. The main capture `m1` equals the baseline
exactly (M 2,264, sig be08f1ba7a56). The acceptance store order holds in the candidate .lst: `stxb` -0xe, -0xf,
-0x10, creator, -0xd, -0xb, -0xc, -0x18. The result is **0.61721, M 2,059 @27,368** (T1 482 → 338, V1 72 → 43,
V5 67 → 45). In the source form the global loads interleave with the volatile stores as ld/st pairs, because each
non-volatile load is chained after the previous volatile store; the original loads all three first. It was not built
with measure.sh, because the oracle bound is far below main.

## 4. Grids (all llc-only on named post-opt IR; all below main)

| screen | base | cells | best at 27,400 | best any size |
| --- | --- | ---: | --- | --- |
| early-flag subsets × global early × order main/orig × volatile stores × volatile loads (`s2`) | 9336aaf | 120 | main only | 2,249 @27,296 (volatile stores in main order) |
| + creator GEP early × cashback bool late (`s3`) | 9336aaf | 96 | 2,120 | 2,120 |
| + holder as and-1 / computed after the mayhem test (`s4`) | 9336aaf | 72 | 1,529 | 2,087 @27,168 |
| load-unit order permutations, stores in main order (`s5 L`) | 9336aaf | 1,200 | 2,259 = main (25 permutations reproduce main) | main |
| volatile store-order permutations × memcpy position (`s6`) | af6ca66 | 1,500 | 2,244 | 2,247 @27,424 |
| PDA-first × early flags × global early × order × volatile (`ce2` grid) | af6ca66 | 32 | main only | 2,254 @27,296 |
| single volatile pins in bb5..bb11 | af6ca66 | 23 | 2,264 (identical) | cashback pin 2,264 @27,384 (-16 B); holder_enabled pin 2,264 @27,376 (-24 B) |
| cashback / holder_enabled pin × every other load/store volatile (`s7`), then triples | af6ca66 | 2,004 + 42 | 2,264 (ties only) | 2,266 @27,392 (cashback pin + `ix` Vec drop-glue cap load, not source-addressable) |
| every subset of the 7 field stores volatile × order main / orig stores / orig loads+stores (`s10`) | af6ca66 | 384 | 2,264 (ties; volatile holder_enabled store is an equal-M different signature) | main |
| ve1n (original-shaped E2/E3) × every load/store of execute volatile (`s8`) | af6ca66 | 996 | - | 2,161 @27,344 (ve1n 2,151) |
| ve1n × 2000:1 / 1:2000 `!prof` on each of execute's 146 branches (`s9`, w17a04-style spill re-sort) | af6ca66 | 292 | - | 2,157 @27,336 |

The non-volatile original store order without the early loads collapses (M 1,606 @27,312), so the memcpy position is
load-bearing (as w17a03 found). Non-volatile reorders otherwise mostly reschedule back to main.

## 5. Tools (`tools/`, experiment only)

- `pscore.py`: llc + extract + M/ratio of a post-opt module, about 0.2 s, with an optional objdump listing at window
  offsets (`fn.lst`).
- `ctoedit.py` (9336aaf) and `ce2.py` (af6ca66): unit-level edits of execute's CtoState block on the instnamer'd
  post-opt module: early units, block order, volatile stores and loads, global early, PDA first. Run
  `opt -passes=instnamer` on fx's `m.ll` first, because numbered values cannot be moved in textual IR.
- `regm.py`: per-region M attribution by original offset, using the Ghidra region table.
- `mmask.py`: M with frame, register and jump masks. `fmap.py`: aligned (orig → cand) r10-offset pairs.
- `vars.py`: the source shim variants (capv.py format from w17a06).

## 6. Handoffs

1. The early-flag CtoState shape (section 2) is the original's E2/E3, and its skeleton is closer (+70 masked). It
   pays only if a joint entry rewrite also restores the spill-slot creation order: accounts pointer first (-0x8d8),
   r3 late (-0x918). No single volatile pin (`s8`, best +10) and no single 2000:1 branch weight (`s9`, best +6)
   repairs the -113 cascade. Combine it with w17a10 (`new` pieces) and w17a09 (PDA sret slot) before you judge it.
2. Repay knobs on af6ca66: the cashback pin (`read_volatile(&a.bonding_curve.is_cashback_coin)` in the CtoState
   literal) is -16 B at 0 M, and the holder_enabled pin is -24 B at 0 M. No volatile-pin partner turns either into a
   gain at 27,400 B.
3. Volatile CtoState stores in any order never beat main (3,000+ cells over two bases). Do not repeat that screen.
