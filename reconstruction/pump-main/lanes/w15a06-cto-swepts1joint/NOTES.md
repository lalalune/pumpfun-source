# w15a06-cto-swepts1joint: the three sharing-CPI leads priced together (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 90300f9d2 (admin_cto 0.67346, 3,124 slots, M 2,248; unchanged on ed47ac72a). Numbers are from `$BASE`; no main rebuild.
Ledger: approach `swepts1joint`, keys `0x22a10-w15-90300f9-swepts1joint-{grid-pin,r9-physpin,regideal-joint,evict3,colourshift,latecolour,multipin}-v1`.
Build slots used: 1 (the s1 raw-IR capture). Everything else is IR/MIR + llc, seconds each.

**Result: notes only, no source change.** The three leads are strongly super-additive, but only through two
levers that have no source spelling: the legal tail colour pin and ideal register naming. Forcing `swept` into
r9 as a physreg costs about 0.22 on every base. With the pin and the swept-only register rename together, s1 ties
main (M 2,300 against 2,302). s1 wins only when the whole region's registers are ideal: M 2,416, which is +63 over
main in the same cell and +168 over main as built. No cell that a source change can reach beats main by 15 M.

## 1. Oracles (all exact round trips, `tools/`)

- **Bases.**
  - `m0` is main's raw IR (`rx.py`, `eq_main: true`).
  - `s1` is all seven sharing AccountInfos as plain `to_account_info()`. w14a85 `edits/gen.py` regenerates it; it was
    captured on 90300f9 and measures 0.64289, M 2,145 at 27,376 B.
  - `canon_all` is w14a122 `canon.py` (via w14a139) run on the renumbered `m0` module: M 2,162, 0.64769.
- **Post-RA colour pin.** `mkdbg.sh` writes pre.mir, ssc.mir and ssc.log, and `mirperm.py` is w14a139's tool.
  **Fix:** scoring now applies the SBF outgoing-arg bias (`fixfs.py`, from w14a69 `objscore.py`). With it the
  ssc.mir round trip is byte-exact: M 2,248 on main, where w14a139's `rt` lost 19 M at 0x4c00-0x6400. So the deltas
  below are absolute. Two of mirperm's patterns had the slot name `_55.i98` hard-coded; it is now `_55.i9\d`.
- **Pre-RA swept pin (`swr9.py`, `swfind.py`, `r9run.sh`).**
  - In MIR before `register-coalescer`, the event `+184` store's vreg has a single def,
    `%286 = COPY %1630`, at the top of the sweep-exit join `bb.269.bb88`.
  - The tool rewrites that def and its uses (in blocks dominated by the join) to `$r9`, and adds `liveins: $r9` to
    the 59 blocks on the path.
  - The unedited round trip is exact (0.67346). Note that a round trip from MIR taken before `greedy` is NOT exact
    (0.6067 at 27,288 B, because live-interval value numbering is lost), so pre-RA pins must be applied before
    register-coalescer.
- **Register bound.** w14a85 `regideal.py`, over orig 0x3c00-0x5040. `RF=9` rewrites only the pairs where ours
  uses r9, which is the swept effect. Its noise on main is about 0.007.
- **Scores.** `objsc.py` gives M and ratio. w14a128 `lcs.py` / `lcschunk.py` give the true LCS.

## 2. The joint grid (M = matched masked tokens; main as built = 2,248)

| base | free | + legal pin | + all-50 pin | + r9 physreg pin | + regideal r9 | + pin + regideal r9 | + regideal all | + pin + regideal all |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| main | 2,248 | **2,291** (0.68634) | 2,298 | 1,525 (0.45686) | 2,255 | 2,302 | 2,252 | 2,353 (0.70491) |
| s1 (27,376 B) | 2,145 | 2,250 | 2,257 | 1,513 | 2,171 | 2,300 | 2,284 | **2,416 (0.72411)** |
| canon_all | 2,162 | 2,252 | 2,258 | 1,543 | 2,164 | 2,256 | 2,232 | 2,322 |

True LCS, unmasked tokens (`---`):

| cell | main | s1 |
| --- | ---: | ---: |
| free | 2,253 | 2,205 |
| + legal pin | 2,292 | 2,258 |
| + pin + regideal r9 | 2,303 | 2,303 |
| + pin + regideal all | 2,353 | 2,416 |

`data/lcschunk-grid-90300f9.txt` has each cell's per-0x400 chunk deltas. All of the s1 gain is in 0x3c00-0x5000.

What the grid shows:
- **Super-additive.**
  - On main: the pin gives +43, regideal +4, and both together +105.
  - On s1: the pin gives +105, regideal +139, and both together +271.
  - The legal pin fixes the frame offsets of the clone-run spill and reload instructions, and register naming fixes
    their registers. The same instructions need both to match.
- **s1 gains more from the pin than main does** (+105 against +43), but s1 + pin still sits 41 M below main + pin.
- **The swept-only rename does not separate s1 from main** (2,300 against 2,302). s1's advantage needs the whole
  caller-saved rotation. That matches w14a85: the two thirds outside r9 have no lever.
- **The swept physreg pin is destructive everywhere**, about -0.22. It re-colours the whole function from the entry
  (`mov r7,r5; mov r8,r1`) and re-lays the event blocks, as w14a69 found for c1+pin.
  - mirperm cannot run on top of it, because the frame changed.
  - Extra physreg pins on the original's registers make it worse or fail to allocate: entry r5 -> r6 gives 0.599,
    accounts `%0` -> r8 gives 0.552, r9 + `%0`=r8 gives 0.590, and all three together fail to allocate.

## 3. Mechanism: s1's tail colours are the original's sequence, shifted (`coldiff.py`, `colmap.py`)

`data/coldiff-90300f9.txt` gives, per tail piece, ours minus the original's slot in 8 B units:
- **s1, E1-E3** (owner, rent, signer, writable, executable): exactly the original's order, at a constant +3 slots.
- **s1, E4 and E5:** +2 and +1.
- **main:** E2-E4 rent and flags are already exact (0); the data and owner pieces are scattered.

The +3 comes from pieces that s1 spills early into low colours, in the original's E0-flag run (0x960-0x978):
- E0.lam at 0x960 (the original has it at 0xac8, the last colour);
- an E3.data split piece at 0x968;
- E0.own at 0x970 (the original's 0xa48);
- E0.rent at 0x978 (the original's 0x948).

In the original, these Rc and owner pointers stay in caller-saved registers through most of the run (w14a85's r0/r7
shuffles) and are spilled late, at low weight, so they take the top colours. **The s1 frame error is therefore the RA
cascade itself, not a separate frame lever.** This is why the pin and the register bound only pay together on s1.

Main's literal pool_authority already puts E0.lam and E0.data on the original's slots (0xac8, 0xa88). That is part
of why main beats s1 as built.

## 4. The three illegal pins (`mirperm2.py` EVICT, `longsp.py`, `sscsim.py`)

- Ours has 9 function-long spills across the tail, and the original 6. The extra ones are:
  - SS#181, the entry r4 arg spill, on colour 185 (0x910);
  - SS#185 on colour 184 (0x908);
  - SS#186 on colour 179 (0x8e0).
- The original's tail key and lamports pieces for E0, E4 and E2 sit on exactly those slots. The original's 0x910,
  0x908 and 0x8e0 are long-lived slots too, used from 0x350/0x420/0x150 to past 0x5a00. So the original's tail reads
  an earlier, long-lived copy of the same key (a CSE of the key load) and does not spill a fresh piece.
- Moving the three to fresh slots costs 1 M. Pinning all 50 on top of that gives only +7 over the legal pin
  (main 2,297, s1 2,256, canon 2,257), so these colours are not where the value is.
- `sscsim.py` emulates StackSlotColoring: the logged processing order, first fit over used colours ascending,
  otherwise the next unused FI. It reproduces 181 of 181 FI assignments exactly on main and s1.
  - Colouring SS#181/185/186 last re-colours 163-178 FIs across the whole function.
  - That costs 195-230 M (main 2,053, s1 2,016, canon 2,003).
  - So the original must have a different *set* of function-long spills, not a different order of the same set.
- Note: on this toolchain the colouring order is not a plain weight sort. Use the order of the logged
  `Assigning` lines (`sscsim.py`).

## 5. Bound and verdict

- Every cell above main by 15 M or more needs the legal tail pin (+43 on main), ideal register naming, or both.
  - w14a139 showed that the pin's colour order is decided by the clone-window source form, and every window form
    screened so far loses.
  - w14a85 and w14a84 bound register-only fixes at about +0.007 on main's structure.
  - This lane adds that on s1 the two are one RA effect. There, s1's frame mismatch is a +3 shift caused by early
    spills of E0's Rc and owner pointers.
- No combination of the three leads gives a source-reachable cell above main.
- **Joint bound (oracle, not landable):**
  - s1 + legal pin + ideal region registers = 0.72411 at 27,376 B (M 2,416);
  - main with the same = 0.70491 (M 2,353);
  - the realisable swept-only part ties main (2,300 against 2,302).

## 6. Next ideas (untried)

1. An RA-faithful oracle for s1 would need a patched greedy (a priority or cascade override) in a private llvm-dbg
   build, not physreg pins. Physreg pins only add interference (section 2).
2. Key-load CSE: the original reuses long-lived key slots for the E0/E2/E4 key pieces. A source spelling that binds
   those keys once, early, and uses `key: k` in the literals might drop the tail key reloads. Its colour value is
   bounded at +7 M (section 4), plus any code change from removing the loads, which is unmeasured.
3. Use `sscsim.py` as a fast filter for frame-order ideas. It reproduces StackSlotColoring exactly from ssc.log in
   under a second, so "which interval set must change" questions no longer need a build.

## Tools (`tools/`, experiment only)

- `grid.sh <name> <m.ll>`: one base's cells (free, pinV, pinA, r9, r9+pin).
- `mkdbg.sh <m.ll|.mir> <dir> [start args]`: pre.mir, ssc.mir, ssc.log and an exact rt.o.
- `objsc.py`, `fixfs.py`: score with the SBF outgoing-arg bias fix.
- `swr9.py`, `swfind.py`, `r9run.sh`: the swept physreg pin before register-coalescer.
- `vpin.py`: whole-function vreg-to-physreg pin.
- `mirperm.py` (w14a139, slot-name fix), `mirperm2.py` (`EVICT=` for long spills), `mirmap.py`: apply a full FI
  colour map.
- `sscsim.py`: StackSlotColoring emulator; `--late` colours the given FIs last.
- `coldiff.py`, `colmap.py`, `longsp.py`, `tailfi.py`: per-piece colour tables and the long spills across the tail.
- `osc.py`: score helper.

Inputs come from w14a118 `tools/` (rx.py, capraw.py, cs.sh, mm.py, oracle.py), w14a139 `tools/` (px2.py, eseq.py,
canon.py, cbmv.py, renum.py), w14a85 `tools/` (regideal.py, bdis.py, cls.py) and w14a128 `tools/` (lcs.py,
lcschunk.py, fact.py, xled.py).
