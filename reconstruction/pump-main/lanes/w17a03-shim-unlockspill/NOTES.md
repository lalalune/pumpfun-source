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

**Second gain (branch `swarm/w17a03-shim-unlockspill-2`): the program clone's `a.pump_fees` reload pinned inside the
event_authority lamports Rc increment** (line 749, no line added; `data/pf5746.py`):

| build | ratio | slots | bytes | normalized / raw | losses |
| --- | ---: | ---: | ---: | --- | --- |
| main 6d498c5e6 (#3936) + pf5746 | 0.67496 (oracle 0.67496) | 3,141 | 27,400 | 1034 / 1034 | 0 / 0 |
| main 442ae70ca (#3936 + w17a04 #3950, 0.67615) + pf5746 | **0.67645** | 3,141 | 27,400 | 1034 / 1034 | 0 / 0 |

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

## Maintainer qualification after #3934 (2026-10-31)

The reviewed composition preserves #3965 ancestry and adds two compile-time
size/alignment checks for the concrete `Program<LegacyFeesProgram>` wrapper.
Its temporary lamports handle now uses `Rc::into_raw`,
`Rc::increment_strong_count`, then `Rc::from_raw`, so the increment receives
the documented raw-pointer provenance and exactly one added owner is dropped
with the constructed `AccountInfo`. The pinned Anchor 0.31.1 `Program` source
has only `info: &AccountInfo` plus `PhantomData`; its private field shape and
the compile checks establish the reference offset for this build. This is
not a stable Anchor ABI guarantee. The live original Rc and non-unwinding
read/increment interval remain required; overflow follows pinned std abort.

An independent fresh main #3934 build and repaired source build measured
2258 → 2259 matching CTO tokens (0.67645 → 0.67675), 27,400 bytes, 3,141
slot differences, 154 internal calls and three syscalls unchanged. All 1,034
raw/normalized exact windows remain matched, with no losses. Both repaired
images equal the unmodified #3965 composition images. Only 114 text bytes
inside CTO change versus #3934; the unstripped symbol table also changes
four local basic-block addresses.

Fresh captured-program comparisons pass 388 cases with zero mismatches and
776 nonempty valid signed transaction vectors. The persistent lifecycle
passes nine cases, 20 unique transactions per image, 78 individual signature
checks and exact deterministic replay, including state continuity/rollback
and genuine signed dependency CPIs. These finite fixtures do not establish
whole-program equivalence. Earlier IR screens above remain historical
research; stopped claim-token-incentive campaigns remain excluded.

Repaired source snapshot: `31ddc1e89d22ebde38a90c7397371d63e1f691041c5197e65f3e8d7ab4e17b10`.
Unstripped image: `c1cc9abba1ca4add9ed7be71e3de68e12a0ed4e9cf1916428b55c524c47f7772`.
Stripped image: `57ffa6f2dd94ff75b675f75aea2d23bb4b3a998896b635b7920c3e2566d1f0c9`.
