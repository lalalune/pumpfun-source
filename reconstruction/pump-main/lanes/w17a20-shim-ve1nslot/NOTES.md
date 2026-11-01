# w17a20-shim-ve1nslot: ve1n (the original's E2/E3) and its spill-slot order (notes; KILL at the bound)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. Wave 17 shim track.
This lane continues w17a12-shim-ctostate-store (#3998, handoff 1). It uses w17a08-shim-sscorder's exact
StackSlotColoring simulator (`sscsim.py`, `votes.py`).

- Bases: main 8330455eb (0.68244, M 2,278), then main a51791e2e (0.68544, M 2,288, which has a new CtoState field order
  and `ptp(23)`/`ptp(24)` passthroughs).
- Ledger approach `shim-ve1nslot`, keys `0x22a10-w17-<sha7>-ve1nslot-<item>-v1`.
- No source change is proposed, so this lane has no build and no landing.

## Result: KILL (step 2)

The angle's kill test was: "KILL if the relabelled M is not above main's 2,278". It holds on both bases, and on the
latest main it holds even for an illegal relabel.

| base | cell | M @ bytes | legal colour-order ceiling | votes-ideal (illegal) | main |
| --- | --- | --- | ---: | ---: | ---: |
| 8330455 | ve1n (IR, `tools/ce3.py`) | 2,159 @27,264 | 2,202 | 2,282 | 2,278 |
| 8330455 | ve1n, accounts first and r3 at the original k8 | - | 2,154 (r3 at k1..k6: 2,172) | - | 2,278 |
| 8330455 | ve1nP (ve1n + PDA-first, IR) | 2,156 @27,224 | 2,240 | 2,341 | 2,278 |
| a51791e | sh1h2 (ve1n as source) | 2,158 @27,256 | 2,201 | **2,281** | **2,288** |

- **Legal ceiling.** The best colouring that StackSlotColoring can actually produce on the cell's fixed code, under any
  processing order. It was searched with annealing on the scorer's difflib M (`tools/sa2.py`) and with a fast true-LCS
  proxy (`tools/fsa.py`: rapidfuzz `LCSseq`, 2 ms per evaluation, 24k iterations), then re-scored with difflib.
  On main, neither search finds a better order (w17a08's +4 ceiling).
- **Votes-ideal.** Every aligned spill interval is relabelled to the colour the original uses at those accesses
  (`votes.py`), whether or not that colouring is legal. It needs 28-60 pairs of overlapping intervals to share a colour.
  This is the strict upper bound on what any spill-slot repair could give.
- **Why the legal ceiling stays below main.** The original's colour map is not a legal colouring of our intervals,
  because their live-range extents differ. A different processing order (weights, traps, volatile reloads, `dvec`/`combo`)
  cannot get past that ceiling. Edits that leave register allocation unchanged move only spill-colour weights, so they
  are capped at 2,201-2,240.
- **The rest of the gap is register naming.** With registers, frame offsets and jumps masked, ve1n's skeleton is no better than
  main's:

| cell | exact | frame masked | regs masked | frame+regs | frame+regs+jumps |
| --- | ---: | ---: | ---: | ---: | ---: |
| main 8330455 | 2,278 | 2,386 | 2,571 | 2,652 | 2,842 |
| ve1n | 2,159 | 2,294 | 2,507 | 2,643 | 2,850 |
| ve1nP (IR) | 2,156 | 2,359 | 2,477 | 2,643 | **2,861** |
| k8 (source PDA-first, 27,400 B) | 1,958 | 2,131 | 2,432 | **2,679** | 2,847 |
| main a51791e | 2,288 | 2,393 | 2,579 | 2,659 | 2,842 |
| sh1h2 on a51791e | 2,158 | 2,295 | 2,503 | 2,645 | 2,852 |

On af6ca66, w17a12 measured ve1n at +70 fully masked. Main's later shims (w17a15 passthroughs and others) absorbed
almost all of that: ve1n is now +8/+10 fully masked and -9/-14 with frame and registers masked. Even perfect naming
would leave ve1n's skeleton level with main's.

## 1. ve1n on the current main

- **IR form** (`tools/ce3.py`: w17a12 `ce2.py` ported to main 8330455's value names). The edits are: early `a3`/`a5`/`a2`
  loads and the global pointer in bb5; in bb12, the loads mf, he, fc; volatile stores cashback, holder_reward, mayhem;
  the creator memcpy; then quote_locked, fee_configurable, holder_enabled, max_fee.
  - Result: M 2,159 @27,264 (-119 M, -136 B).
  - Per region: E3 21→28, E1 35→32, T1 491→435, C1 229→205, S1 193→180, W2 372→360.
- **Source form `sh1h2`** (`tools/vars.py`, all on line 339). It reproduces the IR cell: same M, same size, and only 8
  tokens differ (the creator copy order). The pieces:
  - `let g:&Account<Global>=&a.global;`
  - `let (cb0,hr0,my0)=(a.bonding_curve.is_cashback_coin,a.bonding_curve.is_holder_reward,a.bonding_curve.is_mayhem_mode);`
    placed before `quote_locked`, whose `contains` goes through `g`;
  - `MaybeUninit<CtoState>` with `let (mf0,he0,fc0)=(g.max..,g.is_holder_reward_enabled,g.creator_fee_configurable);`
    hoisted, the seven `write_volatile` stores in the original order, `(*p).creator=a.bonding_curve.creator`, and
    `validate(st,..)`.

  The w17a12 handoff asked for "the sh1 source form with the loads hoisted". Hoisting alone is not enough. These three
  spelling details matter:
  - **plain** early reads, not `read_volatile`. A volatile `bool` read has no `!range`, so it adds three `and64 rX,1`, and
    `!holder&&cashback` becomes a `select`. With volatile reads (`sh1h`) the result is 2,017 @27,408;
  - `(*p).creator=..`, not `ptr::write`, which lowers to a `memmove`;
  - the global loads bound before the first volatile store. The unhoisted form (`sh1`, w17a12) gives 2,080 @27,368.

  Only the seven stores need a `/*shim:*/` marker; the early reads are ordinary Rust.
- **Grid re-screen** on 8330455 (`tools/grid1.py`, 64 cells). It crosses the early-flag subsets with: global early
  (yes/no), store order (main or original) and volatile stores (yes/no). Nothing beats main. The only cell at
  27,400 B is main itself. The best other cells are volatile stores in main order (2,257 @27,304) and `my` early +
  volatile (2,254 @27,384).

## 2. The entry spill map: original vs main vs ve1n

The first spill stores, by colour k (k = 0 at -0x8d8, 8 B per colour). Original colours come from the original listing
and from the `votes.py` alignment.

| value | original | main | ve1n |
| --- | --- | --- | --- |
| accounts pointer (r8) | k0 | k0 | k1 |
| sharing_config AccountInfo ptr, later holder_reward flag | k1 | - (k1 = stack arg) | holder_reward flag k6 |
| cashback flag (curve+0xa3) | k2 | not spilled early | k5 |
| mayhem flag (curve+0xa2) | kept in r8 | not spilled early | k7 |
| curve pointer | k7 | - | k3 |
| r1 (sret) | k3 | k3 | k8 |
| r3 (`holder` arg) | **k8** | k2 | **k0** |
| r4 (fee tag) | k10 | k6 | k11 |
| r2 (ctx) | k12 | k12 | k13 |

`tools/sscd.py` reports this table for any module (`data/entry-colours-8330455.txt`). The share of entry intervals on
the original's colour is: main 5/8, every ve1n form 0/12, k8 4/8, holder-late (below) 2/9.

Mechanism for r3:
- **Original.** It spills r3 at entry and reloads it once, after the mayhem test (orig +0x610:
  `ldxdw r8,[r10-0x918]; and64 r8,1`). That reload sits in a block with frequency below 1, so the interval is light and
  is coloured late (k8). The `holder` bool then lives as its own value, spilled to -0x950 and stored to the curve at P1.
- **Main.** It computes `!holder` (`and -3`, `jeq`) and the `cashback` bool in the CtoState block (frequency 1).
  r3's weight is 2.0038 (rank 2, k2). Its P1 reload weighs only about 0.004.
- **ve1n.** CodeGenPrepare sinks the `and`/`icmp` pair into its users. That adds a second r3 reload after the mayhem
  test (ve1n +0x5c8). The weight rises to 2.3788, so r3 is coloured first (k0) and every other entry colour shifts
  by one.

## 3. Minimal entry set: none of the tested sets yields the original's entry order

Combinations scored on 8330455 (IR unless "src"). "ideal" is the votes-ideal bound; main's is 2,373.

| cell | M @ bytes | f+r+j | ideal | entry on orig colour | note |
| --- | --- | ---: | ---: | --- | --- |
| main | 2,278 @27,400 | 2,842 | 2,373 | 5/8 | |
| ve1n | 2,159 @27,264 | 2,850 | 2,282 | 0/12 | r3 k0 |
| ve1nP (+ PDA-first) | 2,156 @27,224 | 2,861 | 2,341 | 0/12 | E1 exact 35→55 |
| ve1n + h1b (holder and-1 computed once, reused at P1) | 2,157 @27,264 | 2,851 | 2,279 | 0/11 | r3 weight unchanged |
| m0P (PDA-first alone) | 1,925 @27,368 | 2,841 | 2,128 | 5/9 | = w17a09 k8 collapse |
| m0 hl1 (holder late in bb6.i, cashback at its use) | 1,983 @27,472 | 2,870 | 2,126 | 1/6 | C1 fully masked 343→375 |
| ve1n hl2 (holder + cashback late in bb6.i) | 2,008 @27,520 | 2,851 | 2,217 | 2/9 | **r3 k7, r4 k9** (orig k8/k10) |
| ve1n hl2P | 2,018 @27,592 | **2,880** | 2,223 | 2/11 | best skeleton |
| src k8 | 1,958 @27,400 | 2,847 | 2,115 | 4/8 | best frame+regs (2,679) |
| src sh1h2k8 | 2,009 @27,272 | - | 2,286 | 0/12 | |

- **Holder late** (hopt's test computed after the mayhem test, as in the original) is the only piece that moves r3
  and r4 toward their original late colours. They land one colour short, at k7/k9. With it, though, the early-flag
  spills (weight 2.38-2.41) outrank the accounts pointer (2.06), so accounts drops from k0 to k2. The original
  needs both at once: light flag intervals that come after accounts and the sharing_config pointer, and a late `holder`
  reload. No tested set achieves both.
- **Code shape costs more than the spill colours.** Every structural piece (PDA-first, holder late, early flags) moves
  the fully masked match up by +8 to +38. But each one collapses exact M by 120 to 350, and its votes-ideal stays below main.
  The loss is register naming in T1/C1 (accounts r6 instead of r8, T1 temps renamed). That is the RA-basin re-tune
  problem w17a09 described for PDA-first, and spill colouring cannot fix it.

## 4. Tools (`tools/`, experiment only; screening aids, not acceptance tools)

- `ce3.py`: the ve1n IR edit on main 8330455's instnamer'd post-opt module, unit by unit (`ce3.build(early, G, block,
  volst)`). Rebuild `ir/m0n.ll` with `opt -passes=instnamer` on a fresh fx `m.ll` when main moves, and re-check the value names.
- `sscd.py <module> <name> [--sa s]`: builds `ssc/<name>` (private llc `-debug-only=stack-slot-coloring`, with and
  without slot sharing). It reports M, votes on the current colour, the votes-ideal bound and the entry spill table.
- `fsa.py <ssc-dir> <seed> <secs>`: fast legal colour-order annealing with a true-LCS proxy (rapidfuzz), re-scored with
  difflib. `sa2.py` anneals on difflib M directly (slow). `vsa.py` anneals on the votes proxy (weak: it found 2,177).
- `regmm.py`: per-region exact and fully masked matches. `mdiff2.py`: masked block-move diff of two blobs.
- `h1.py`, `hl.py`, `pfirst.py`, `grid1.py`: the IR edits of sections 1 and 3.
- `vars.py` + `capv.py`: source variants (k8, sh1, sh1h, sh1h2, sh1h2k8, on main a51791e's text), each captured with
  w17a06's exact slim oracle (`capraw` + `preslim` + `fx`, about 20-50 s and one build slot).
- `sscsim.py` and `votes.py` are w17a08's, with only the oracle import path changed.

Pitfall: `oracle.elf_fn` raises `SystemExit` when a function is missing. Inside a `multiprocessing.Pool` that kills a
worker, and `imap_unordered` then waits forever. Catch `BaseException` in pool jobs, or guard the call.

## 5. Handoffs

1. **Do not pursue ve1n's E2/E3 by spill-order repair.** Its legal colour ceiling (2,201) and even its illegal
   votes-ideal (2,281) are below main a51791e (2,288).
2. **The source spelling of ve1n is `sh1h2`.** It uses plain early reads and seven volatile stores, and it reproduces
   the IR cell exactly. Use it if a future RA re-tune adopts the original's entry.
3. **The r3 colour is set by where `holder` is computed** (original: after the mayhem test, and-1). Main's `!holder` /
   `cashback` in the CtoState block makes r3 heavy. A lane that re-tunes the entry should combine holder late with light
   early-flag intervals.
4. **Best skeleton is ve1n hl2P** (f+r+j 2,880, +38 over main's 2,842), and src k8 has the best frame+regs (+27).
   Both need a full RA-basin re-tune (w17a09/w17a14 territory) before exact M can follow.
