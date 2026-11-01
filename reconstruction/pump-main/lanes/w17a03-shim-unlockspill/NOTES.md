# w17a03-shim-unlockspill: memory-op shims for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 1647da0f2 (programs/ as on 599891304): 0.67436, 3,141 slots, M 2,251 at 27,400 B, Pump Main 1034/1034.
Wave 17 SHIM track (owner decision 2026-11-01): marked steering constructs are allowed in `admin_cto.rs` only.
Ledger: approach `unlockspill`, keys `0x22a10-w17-5998913-unlockspill-<mechanism>-v1`.

## Result

**One marked shim, +1 M at the pinned size:** the sweep's `TransferCreatorFeesToPumpV2` CpiContext program clone reads
its `owner` with `unsafe{core::ptr::read_volatile(&x.owner)}/*shim: ...*/` (line 659, no line added).

| build | ratio | slots | bytes | normalized / raw | losses |
| --- | ---: | ---: | ---: | --- | --- |
| main 599891304 | 0.67436 | 3,141 | 27,400 | 1034 / 1034 | - |
| v4320 (this PR) | **0.67466** | 3,141 | 27,400 | 1034 / 1034 | 0 / 0 |

The source build reproduces the IR oracle's prediction exactly (`L4320`: 0.67466 @27,400).

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

## Why the pins are small

The gap is register assignment and spill colouring (w16 decomposition: masking registers, frame and jumps lifts M to
2,799), and a volatile pin changes neither the live ranges nor the spill weights by much. It only fixes the order of one
load relative to the other memory operations in its block. The original's accounts-pointer reloads in the sharing clone
run (34 slot accesses against our 24) are RA splits of one long interval; no addressable memory holds that pointer, so
`read_volatile` cannot reproduce a spill-slot reload (it would read `ctx.accounts` and cost a second load), and a local
copy read through `read_volatile` becomes an alloca that shifts the whole frame by 8 B.
