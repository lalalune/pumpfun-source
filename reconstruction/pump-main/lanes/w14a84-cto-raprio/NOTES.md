# w14a84-cto-raprio: private greedy-RA llc, per-vreg colour map against the original, RA decision map (notes only)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: w14a69-cto-sweptr9's open idea 2 (#3389). It needs a private patched llc that can change greedy's queue priority for
named vregs, force a vreg to a register or to a spill, and log every greedy decision. With that llc, find the smallest set of
RA decisions that moves our colouring toward the original's.
Bases:
- main 0d04cf4 (0.66507 / 3,228), used for the first screens and s1;
- main 95a64ba (#3409, 0.66986 / 3,204), used for the colour map and the final tables.

Scratch is in `~/.cache/pumpfun-reconstruction/lanes/w14a84-cto-raprio/`. The private build dir is deleted at the end;
`llc-patch/build.sh` rebuilds it in about a minute. Ledger: approach `raprio`, keys `0x22a10-w14-{0d04cf4,95a64ba}-raprio-*`.

**Result: no source change.** RA decisions alone are worth at most about +0.005 at 27,400 B (+0.010 at other sizes).
s1 cannot pass main through RA decisions. The colour map, below, names the vregs whose register differs from the
original's, and every gain the search finds is one of them.

## 1. Private llc (`llc-patch/`)

- `build.sh <out>` copies `~/.cache/pumpfun-reconstruction/llvm-dbg/build` (444 MB, never modified) to `<out>/llvmb`.
  It patches private copies of `RegAllocGreedy.cpp` and `SBFAsmPrinter.cpp`, recompiles only those two TUs, re-archives
  `libLLVMCodeGen.a` / `libLLVMSBFCodeGen.a` (dropping ninja's trailing `touch` of the shared archive) and relinks `bin/llc`.
- Environment hooks (unset means stock behaviour):
  - `RAPRIO_PRIO="382=0xfffffff0,13=+100"`: absolute or relative queue priority per vreg, applied at every enqueue;
  - `RAPRIO_FORCE="1681=r6,1626=spill"`: at the first dequeue, assign the register (evicting the interfering vregs, which
    get the forced vreg's cascade) or spill through InlineSpiller;
  - `RAPRIO_HINT="12=r9"`: set a simple hint after `calculateSpillWeightsAndHints`;
  - `RAPRIO_NOHINT="1681,1669"` or `split`: clear the simple hint of the listed vregs, or of every vreg created during greedy,
    at enqueue;
  - `RAPRIO_LOG=<file>`: one line per enqueue (`Q vreg p= st= sz= w=`), dequeue (`D`), result (`R vreg -> reg new: ...`),
    eviction (`E victim from reg by vreg`), spill (`S`), force (`F`), and the final assignment (`A vreg reg|stack`);
  - `RAPRIO_TAG=1` (with `-filetype=asm`): every final instruction that survives from greedy carries
    `# rp <block>.<idx> d<vreg>=<reg> u<vreg>=<reg>`. The tag is keyed by MachineInstr and opcode; COPYs expanded after RA
    are untagged.
- Checks: with no hooks, and with `RAPRIO_LOG` or `RAPRIO_TAG`, the object is `cmp`-identical to the SDK llc and to the
  shared debug llc on both mains. One llc run takes 0.15 s, and screening costs about 0.7 s per variant, with no build slot.

## 2. Tools (`tools/`, text only)

- New:
  - `screen.py <m.ll> <jobs.jsonl> <out.jsonl> [n]`: parallel override screen, scored by ratio/slots/bytes/eq_main (+L1/L2);
  - `mkjobs.py`: single-override jobs (top / bottom / global-bit toggle for every queued vreg, force r6-r9/spill for global
    ones) on top of a base set;
  - `climb.py`: greedy forward selection of override sets (`--size 27400` keeps the pinned size);
  - `colmap.py <m.ll> <prefix>`: **per-vreg colour map**. It aligns our window with the original at L2 (frame and
    registers masked) and, for each aligned pair, votes for the original's register in that field, for every vreg whose register
    appears in a dst/src field (from the `RAPRIO_TAG` asm). Output: vreg, our register, the original's majority register,
    misses, split-ancestry root, and sites;
  - `vname.py <ra.log> <pre.mir> <post.mir> <vreg>...`: split ancestry, the root's defining MIR instruction and IR name, the
    vreg's blocks, queue priority, hint bit, global bit;
  - `vreginfo.py`: defs and uses in a MIR dump;
  - `regceil.py`: plain, register-only masked (a perfect colouring at the same structure and frame), L1, L2;
  - `ev.py`: ratio, fmr L1/L2, clonefeat, regmiss in the clone run and the sweep join.
- From w14a69 / w14a79: `rx.py`, `capraw.py`, `objscore.py`, `clonefeat.py`, `ctoracle.py`, `coal.py`, `fmr.py`,
  `cls.py`, `regmiss.py`, `bdis.py`, `sbs2.py`, `occ.py` (paths changed to this lane).

## 3. How much colour is worth (`regceil.py`)

| base | bytes | plain | regs masked | L1 | L2 |
| --- | ---: | ---: | ---: | ---: | ---: |
| main 0d04cf4 | 27,400 | 0.66507 | 0.75944 | 0.70132 | 0.78310 |
| s1 on 0d04cf4 | 27,360 | 0.63589 | 0.75221 | 0.69135 | 0.81247 |
| s1 + best 3 RA overrides | 27,416 | 0.66128 | 0.77478 | 0.69931 | 0.81162 |
| main 0d04cf4 + best 4 RA overrides | 27,336 | 0.67487 | 0.76275 | 0.70456 | 0.77175 |

A perfect colouring of main's current structure and frame would be worth +0.094. Greedy-decision overrides reach about a
tenth of that.

## 4. Colour map on 95a64ba (`colmap.py`)

There are 2,617 L2-aligned pairs (307 untagged: post-RA COPY expansions and prologue stores). 1,041 vregs get votes, 202 of
them miss, with 444 misses in total. Top rows:

| vreg | ours | orig | misses | value (`vname.py`) |
| --- | --- | --- | ---: | --- |
| %1655 | r8 | r9 | 22/22 | Err-payload class (`LDD %stack, 8` after each `?`), 30 blocks |
| %1679 | r8 | r6/r3 | 14/14 | accounts pointer `%0` (`ctx.accounts`) piece, bb38-bb44 (post-sweep / sharing gate) |
| %1727 | r3 | r9 | 12/12 | swept (`%1623`, `MOV_ri 0` / sweep Ok) piece, 22 blocks |
| %468 | r3 | r2 | 7/7 | bb12 local (validate inputs) |
| %1669 | r8 | r7 | 7/7 | accounts pointer piece in `wallet()` bb24.i (collect_coin_creator_fee clone run) |
| %1279 | r3 | r2 | 6/6 | sharing clone-run local |
| %2143 | r7 | r9 | 5/5 | `%4` = `[%0+56]` (bonding_curve AccountInfo) piece, bb6-bb12 |
| %1678 | r8 | r8 | 5/34 | accounts pointer piece over the TCF clone run (bb84 .. clones), right register |
| %1680 | r5 | r1 | 5/5 | accounts pointer piece over the sharing clone run (bb36 ..); the original reloads it per clone |
| %1681 | r8 | r6 | 5/5 | accounts pointer piece in event emission bb125 (hinted r8) |

w14a69's payload r9 / swept r9 findings appear here as rows 1 and 3. Five of the top ten rows are pieces of the accounts
pointer `%0`: the original gives each region's piece a different register (r6, r7, r1 by reload), while greedy hints them
all to `%0`'s r8.

## 5. RA decision map (vreg -> value -> override -> ratio delta)

### 5a. Pinned 27,400 B, colour-target forces (95a64ba, `climb.py --size 27400` over the colour-map targets)

| step | override | value | ratio | slots | L1 |
| ---: | --- | --- | ---: | ---: | ---: |
| 0 | - | main 95a64ba | 0.66986 | 3,204 | 0.69982 |
| 1 | %1669 -> r7 | accounts pointer piece, wallet clone run | 0.67196 | 3,197 | 0.70192 |
| 2 | %1901 -> r6 | `%295` piece (sharing first clone `rent_epoch`, `[%290+32]`) | 0.67316 | 3,197 | 0.70461 |
| 3 | %1615 -> r3 | Rc `inc_strong` overflow flag (MOV 1 / MOV 0) in the TCF clones | 0.67406 | 3,197 | 0.70551 |
| 4 | %1704 -> r4 | `%465` (bb12 MOV 1/0 flag) piece in bb38 | 0.67436 | 3,197 | 0.70581 |
| 5 | %2125 -> r0 | `%292` piece (sharing first clone lamports Rc ptr) | 0.67466 | 3,196 | 0.70641 |

L2 stays at 0.78400 throughout, so every step is pure register naming.

### 5b. Any size (95a64ba)

| step | override | ratio | bytes | L1 | L2 |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | %1681 -> r6 (accounts pointer piece, event emission) | 0.67506 | 27,392 | 0.70532 | 0.78502 |
| 2 | + %1669 -> r7 | 0.67715 | 27,392 | 0.70742 | 0.78502 |
| 3 | + %467 -> r2 (`[%0+144]` local, bb12) | 0.67856 | 27,376 | 0.71003 | 0.78585 |
| 4 | + %1615 -> r3 | 0.67945 | 27,376 | 0.71092 | 0.78585 |

### 5c. Priority and force screens on 0d04cf4 (`s/r1.jsonl`, 5,859 runs; `s/r2.jsonl`, a second pass)

- 2,580 of 5,859 single overrides are byte-identical. Priority-only overrides at 27,400 add at most +0.0003
  (bb12 flag loads `%459/%461/%493/%515` allocated first).
- The best singles are colour forces again: %1686 -> r6 (+0.0027; the 0d04cf4 name of 95a64ba's %1681) and %1673 -> r7
  (+0.0018; 95a64ba's %1669).
- The best set at 27,400 after two passes is 0.67346 / 3,220 (+0.0084, 7 overrides). The best set at any size is
  `288=r8,1671=spill` with bottom priority for %11 and %1649: 0.67487 at 27,336.
  - `%288` is `old_creator_fee_bps`, loaded in bb38 and stored to the event in bb122. Keeping it in r8 is +0.0055 at
    -128 B. The ledger has 492 old_fee rows.

### 5d. s1 (w14a81's s1 capture on 0d04cf4, 0.63589 at 27,360)

| override | value | ratio | bytes |
| --- | --- | ---: | ---: |
| %1681 spill | accounts pointer piece over the sharing clone run (s1 keeps it in r7; the original reloads it per clone) | 0.65978 | 27,416 |
| %319 bottom priority | sharing clone lamports Rc pointer, live from the clone to the CPI array store (clonefeat 2/6 -> 5/3) | 0.65507 | 27,360 |
| best set: %1681 spill, %353 -> r7, %2181 -> r7 | | 0.66128 | 27,416 |

The best s1 set has L1 0.69931, still below main's 0.70132. The +0.029 L2 gain of s1 (w14a47/w14a74) cannot be cashed in
through greedy decisions. With registers masked, s1 + overrides (0.77478) would beat main (0.75944). That gain needs the
original's whole-function colouring, and no priority, hint or force change near the sharing CPI produces it.

### 5e. swept / payload class registers (0d04cf4, CFG unchanged, unlike w14a69's asm pins)

| force | ratio | bytes |
| --- | ---: | ---: |
| swept %1626 -> r9 | 0.60354 | 27,304 |
| swept %1626 -> r7 | 0.63557 | 27,336 |
| payload %1659 -> r9 | 0.66397 | 27,296 |
| swept top priority + r9 | 0.66148 | 27,472 |
| payload -> r9 and swept -> r6 | 0.66397 | 27,296 |

Every row loses. Putting swept or the payload on r9 re-colours the whole function: their live ranges span 30 blocks, so the
force evicts the accounts-pointer pieces and the cascade costs more than the 22 + 12 hits gained.

## 6. Source properties behind the map (step 4)

| vreg (95a64ba) | why greedy picks our register | source property that would change it | status |
| --- | --- | --- | --- |
| accounts pointer pieces (%1669, %1681, %1679, %1680) | region-split products of `%0` keep the copy hint to `%0`'s r8 (prio bit 30 set on %1681). r8 is free in those regions, so each piece takes r8 | something else must hold r8 in each region (the original has a flag or swept there), or the piece must not be copy-related to `%0` | IR experiment: a fresh `load ptr %3` (ctx.accounts) in wallet bb24.i, plain or volatile, gives 0.66627 at 27,448 (-0.0036). `ctx` is `noalias readonly`, so GVN folds any source re-read |
| payload %1655, swept %1727 | largest global intervals; allocated before the r9 occupants | none local (5e) | w14a69, w14a74 |
| sharing clone Rc pointers (%292 / %319 family) | global ranges live from the clone to the CPI array store; size is the priority | a shorter clone-to-store distance (build the CPI account array next to each clone) | the w14a30/w14a47 literal and order screens already cover the spellings |
| `old_creator_fee_bps` %288 | live from bb38 to the event in bb122; spilled after eviction by a sharing value | read at the event site | 492 ledger rows; GVN keeps one load |
| bb12 locals %459/%467/%468 | local ranges in instruction order | load order in the validate inputs | +0.0003 only |

## 7. Conclusion and next ideas

- The greedy decisions that differ from the original are mostly the register names of `%0`'s split pieces, the payload class
  and swept. The search finds no small set of priority changes that fixes them. Colour forces at the pinned size give +0.0048
  on 95a64ba. Of the 125 colour-target forces (the original's register for each missed vreg), only 16 gain on their own; the
  others start a cascade that costs more than they fix.
- For the s1 and PDA-first lanes, the RA bound on s1 is 0.66128 (0d04cf4), 0.004 below that main.
- Ideas for other lanes, ranked:
  1. Run `colmap.py` on any candidate. A source change that removes accounts-pointer piece misses (rows %1669, %1681)
     without adding others is worth about +0.002 each at 27,400.
  2. Run `climb.py` on a candidate's `m.ll` to learn how much of its loss is RA (an RA-recoverable loss shows up as a
     colour-force gain), before spending builds on partners.
  3. Tested here, and dead: hint-free split pieces (`RAPRIO_NOHINT`). Clearing the simple hint of the accounts-pointer pieces
     (%1669, %1681, %1679, %1680, %1678, alone or together) is byte-identical to main. r8 is the first free callee-saved
     register in those regions, not a hint. Clearing every split/spill product's hint (`RAPRIO_NOHINT=split`) gives 0.5062.
     The original's r6/r7 pieces mean r6/r7 are free there in the original, so the cause is occupancy (what else is live
     across those regions), not the hint.
