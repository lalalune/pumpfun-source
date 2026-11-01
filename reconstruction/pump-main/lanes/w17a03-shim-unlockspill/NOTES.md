# w17a03-shim-unlockspill: memory-op shims for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 1647da0f2 (programs/ as on 599891304): 0.67436, 3,141 slots, M 2,251 at 27,400 B, Pump Main 1034/1034.
Wave 17 SHIM track (owner decision 2026-11-01): marked steering constructs are allowed in `admin_cto.rs` only.
Ledger: approach `unlockspill`, keys `0x22a10-w17-5998913-unlockspill-<mechanism>-v1`.

## Result

**Landed: #3936 (merge 2c470820b, merged by the account owner while land.py ran; the published baseline is 0.67466).
One marked shim, +1 M at the pinned size:** the sweep's `TransferCreatorFeesToPumpV2` CpiContext program clone reads
its `owner` with `unsafe{core::ptr::read_volatile(&x.owner)}/*shim: ...*/` (line 659, no line added).

| build | ratio | slots | bytes | normalized / raw | losses |
| --- | ---: | ---: | ---: | --- | --- |
| main 599891304 | 0.67436 | 3,141 | 27,400 | 1034 / 1034 | - |
| v4320 (this PR) | **0.67466** | 3,141 | 27,400 | 1034 / 1034 | 0 / 0 |

The source build reproduces the IR oracle's prediction exactly (`L4320`: 0.67466 @27,400).

**Second gain, landed as #3965 (merge 9336aafff; land.py on main e2d200343 with w17a02's #3934: 0.67645 -> 0.67675,
3,141 slots, 27,400 B, 1034/1034, 0 losses, differential 388/0): the program clone's `a.pump_fees` reload pinned inside the
event_authority lamports Rc increment** (line 749, no line added; `data/pf5746.py`):

| build | ratio | slots | bytes | normalized / raw | losses |
| --- | ---: | ---: | ---: | --- | --- |
| main 6d498c5e6 (#3936) + pf5746 | 0.67496 (oracle 0.67496) | 3,141 | 27,400 | 1034 / 1034 | 0 / 0 |
| main 442ae70ca (#3936 + w17a04 #3950, 0.67615) + pf5746 | 0.67645 | 3,141 | 27,400 | 1034 / 1034 | 0 / 0 |
| main e2d200343 (+ w17a02 #3934, 0.67645) + pf5746 (land.py) | **0.67675** | 3,141 | 27,400 | 1034 / 1034 | 0 / 0 |

Runtime differential: 388 cases, 0 mismatches. The source:
`let pf:&AccountInfo;` before the sharing CPI; the event_authority literal's
`lamports:unsafe{let r=ptr::read(&..lamports);if Rc::strong_count(&r)==0{unreachable_unchecked()}pf=read_volatile(&a.pump_fees ..);Rc::increment_strong_count(Rc::as_ptr(&r));r}`
(the count load, then the pinned pointer load, then the increment, whose own count load GVN forwards from the first);
and the program clone's `lamports:pf.lamports.clone()`.

## Method: a volatile-pin oracle on the post-opt IR

- `rx/m0n/m.ll` is w16a08's raw-IR capture of main 5998913 after `opt -O3` and slimming (`eq_main: true`); `llc` on it
  takes about 3 s.
- `tools/vscreen.py <m.ll> <lo> <hi> <out.jsonl> [workers] [load|store|memcpy]` marks ONE load (store, memcpy) of
  `execute` volatile, runs `llc`, and scores it with the scorer's masked difflib ratio. A volatile load in the post-opt IR
  is what `core::ptr::read_volatile` of the same field produces at the same place: the load can no longer be merged,
  folded or moved across other memory operations by the DAG and the scheduler, but nothing else changes.
- `tools/vcomb.py <m.ll> <out> L<line>,S<line>,M<line> ...` scores sets of such pins.
- `tools/mv.sh <name> <edits.py> <slot>` copies the crate, applies exact single-occurrence edits (line count kept) and
  runs `measure.sh`.

## Screens on main 5998913 (all single pins)

| screen | candidates | keep 27,400 | best at 27,400 | best off-size |
| --- | ---: | ---: | --- | --- |
| volatile loads (`data/vload-5998913.jsonl`) | 446 | 327 (225 byte-identical) | **L4320 0.67466** | L2735 / L2737 0.67456 @27,384 |
| volatile stores (`data/vstore-5998913.jsonl`) | 559 | 394 | 0.67436 (none above main) | 0.67396 @27,408 |

- L4320 is `%_189.i`, the `owner` load of the sweep's TCF program clone (`a.pump_amm`, accounts+88).
- L2735 is the CtoState `cashback` byte (`a.bonding_curve.is_cashback_coin`, curve+163) and L2737 the `holder_enabled`
  byte (`a.global.is_holder_reward_enabled`, global+1087). Each gives +1 M at -16 B; with L4320 the pins add
  (L4320+L2735: 0.67486 @27,384, M 2,252), but a +16 B repay costs more than 1 M in every catalog knob.
- Volatile stores never beat main: the scheduler already keeps main's stores in IR order.
- Most pins are byte-identical: the BPF DAG scheduler already emits those loads in IR order.

Follow-up screens (same oracle):

| screen | result |
| --- | --- |
| volatile `llvm.memcpy` (29 plain memcpys of execute) | all byte-identical to main |
| second round: every load pin on top of L4320 (`b2`, 445 pins) | nothing above 0.67466 at 27,400; L2735 / L2737 still +1 M at -16 B (0.67486 @27,384) |
| pairs of the 18 best code-changing pins at 27,400, on top of L4320 (153 pairs) | best 0.67436: no pair beats L4320 alone |
| move + pin (`tools/mvscreen.py`): each clone-run / entry load moved to the top of its block, before the block's last store, or before the terminator, volatile | sweep TCF clones (212): none above main. Sharing clone run (114): **L5713 before the event_authority data Rc store 0.67496 @27,400 (slots 3,139)**, with L4320 **0.67525 @27,400 (M 2,254)**. Entry (CtoState): none. |
| position scan of L5713 (`tools/posscan.py`, every legal insertion point from its block to the sharing CPI call, on top of L4320) | only the event_authority `data.clone()` window works: after the strong-count load and before its store (IR 5727-5730), 0.67525. In place 0.65468 @27,392, at the top of the next block 0.64969 @27,384, any other window 0.658-0.665 off-size. |
| Rc-window scan (`tools/winscan.py`, on top of L4320): every clone-run load moved EARLIER into a preceding clone's Rc window, volatile | sweep TCF (211): none. Sharing run (91): **L5784 into the event_authority `lamports` window, 0.67496 @27,400 (+1 M)**. L5784 is the program clone's second `a.pump_fees` load (accounts+0x98, for `lamports:a.pump_fees.lamports.clone()`). |
| position scan of L5784 (`tools/posscan.py`) | 0.67496 only inside the event_authority lamports Rc increment (after the count load: IR 5743-5748) or at the head of the next block (5755, the event_authority `key` field). |
| account-pointer pins on that base (`tools/accscan.py`: every `[accounts+K]` reload of the sharing run moved to every earlier block head, volatile) | nothing above 0.67496 |

**Realising L5784.** The source form `pf=read_volatile(&a.pump_fees)` at the head of the event_authority `key` field
(deferred local `pf`, program clone `lamports:pf.lamports.clone()`) builds to 0.67266 @27,392 (`data/pf5784.py`), not the
oracle's 0.67496. LLVM GVN forwards the volatile load into the program clone's later non-volatile `a.pump_fees` load
(MemDep treats a MustAlias preceding volatile load as a Def), so the two reloads merge; the IR with one merged load is
exactly 0.67266 @27,392. The pin pays only while the two loads stay separate, so the volatile read has to sit before a
may-alias store: inside the event_authority lamports Rc increment. That is the `pf5746` form: the lamports clone is
written as `ptr::read` of the Rc + `Rc::strong_count` (the count load) + the volatile read + `Rc::increment_strong_count`.

**The L5713 bound is IR-only (+2 M over this PR's base).** L5713 is the `owner` load of `sharing_config`'s
`to_account_info()` clone. Its winning slot is inside the NEXT field's clone (`event_authority:AccountInfo{data:
a.pump_fees_event_authority.data.clone(),..}`), between the strong-count load and store. Rust evaluates struct-literal
fields in source order and moves each field operand into a temporary at its own position (MIR `as_operand` makes a temp
for place operands too), so the sharing_config `owner` cannot be read after the event_authority field starts unless the
two fields swap evaluation order, and a manual inc_strong needs `core::intrinsics::abort` (feature gate). Kept as a
handoff for a lane that rewrites the sharing CPI arm.
| CtoState stores as `write_volatile` in the original's order (orig 0x440-0x4d0: cashback, holder_reward, mayhem, creator words ascending, quote_locked, fee_configurable, holder_enabled, max_fee) | volatile in main's order 0.67267 @27,296; in the original's order 0.67147 @27,320; the creator copy as 4 volatile words collapses (0.480 @27,368); moving the creator memcpy after the field loads alone gives 0.568 @27,216 (its position is load-bearing). Non-volatile reorders are rescheduled to main. No lever. |
| every load pin on S3n (w16a08's per-arm holder flag, 0.59599 @27,416) | best 0.61177 @27,424 / 0.61114 @27,400 (L2735 / L2737 also give S3n its -16 B: 0.59617 @27,400). Pins cannot repair S3's spill-slot numbering (w16a20). |

## Why the pins are small

The gap is register assignment and spill colouring (w16 decomposition: masking registers, frame and jumps lifts M to
2,799), and a volatile pin changes neither the live ranges nor the spill weights by much. It only fixes the order of one
load relative to the other memory operations in its block. The original's accounts-pointer reloads in the sharing clone
run (34 slot accesses against our 24) are RA splits of one long interval; no addressable memory holds that pointer, so
`read_volatile` cannot reproduce a spill-slot reload (it would read `ctx.accounts` and cost a second load), and a local
copy read through `read_volatile` becomes an alloca that shifts the whole frame by 8 B.

## Re-screen on the landed state (capture `m442` = 442ae70 + pf5746, 0.67645)

- Rc-window moves (`tools/winscan.py`): sharing run 105, sweep TCF 236, with nothing above 0.67645.
- Single volatile load pins (`tools/vscreen.py`, 444): nothing above 0.67645 at 27,400. L2735 / L2737 still give +1 M at
  -16 B (0.67666 @27,384), and none of the 36 pairs with a +8..+24 B pin lands at 27,400 (best 0.67575 @27,408).
- So the memory-pin lever is used up on this base. The remaining residue is register and spill-colour naming, plus the
  two structural items below.

## Handoffs

1. **L5713, IR-only, +2 M.** `sharing_config`'s `owner` load belongs inside the event_authority `data.clone()` Rc window.
   A struct-literal field cannot be read after a later field starts, so this needs the sharing CPI literal restructured
   (event_authority evaluated first, or the account struct built differently).
2. **L2735/L2737 as a -16 B repay.** Pin `cashback:` / `holder_enabled:` in the CtoState literal with `read_volatile`
   (+0/+1 M, -16 B) for any +16 B lead that gains M.
3. **Rc-window recipe** (general): a load can be pinned inside clone X's Rc increment only if a may-alias store follows it.
   Spell X's clone as `ptr::read` + `Rc::strong_count` (the count load) + the pin + `Rc::increment_strong_count`. A pin at
   a block head with no store after it is merged by GVN into the next MustAlias load.
