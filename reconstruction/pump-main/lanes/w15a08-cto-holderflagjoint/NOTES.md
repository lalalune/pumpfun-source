# w15a08-cto-holderflagjoint: joint price of the holder flag with a perfect spill frame (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. Base: main 90300f9d2,
0.67346, 3,124 slots, M 2,248 (taken from `$BASE`; `programs/pump/src` is unchanged since e88f9d5, so w14a142's post-opt
capture `rx/main/m.ll` is main's and reproduces 0.67346 / 27,400 exactly). Continues w14a142-cto-holderflagtm (#3628) and
w14a121-cto-delwin (#3524): this lane runs their joint next idea. Ledger: approach `holderflagjoint`, keys
`0x22a10-w15-90300f9-holderflagjoint-*`.

**Result: notes only, no source change.** Pricing the per-arm holder flag together with a perfect spill frame gives
**main +1 to +4 M before the +24 B size repay** (+2 with every spill slot permuted at its best). The flag has no code-shape
value. The original's flag differs from ours only in register-allocation roles, and no flag form reproduces those roles.
The angle is exhausted, so no gene hill-climb was run: its precondition, a joint bound above main, does not hold.

## 1. Spill-permutation bound (`tools/relab.py`, no build slot, about 1 s)

A permutation of a build's own 8 B spill-slot offsets (the `type: spill-slot` objects in `-stop-after=prologepilog` MIR)
is always a legal colouring of the same code, because every interference relation is unchanged. Its best score therefore
bounds what any spill-colour order can give that code. This is a tighter, consistent version of frame-masked M.
`bestperm` aligns the frame-masked token streams with the original and votes `cand_off -> orig_off` on aligned memory
instructions. It then solves the assignment (scipy `linear_sum_assignment`) and iterates. `tools/permhc.py` adds a
pairwise-swap hill climb (`FULL=1` tries every pair).

| build | bytes | M | Mperm (vote+assignment) | Mhc (swap climb) | frame-masked M (fm.py) | frame+reg masked |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| main 90300f9 | 27,400 | 2,248 | 2,292 | 2,299 (0.68874) | 2,510 | 2,787 |
| e1 = hphi+hcs+hev (w14a142 per-arm flag, event from `%0`) | 27,424 | 1,993 | 2,294 | 2,301 (0.68903) | 2,508 | 2,790 |
| e0 = hev only (+8 B knob) | 27,408 | 2,245 | 2,286 | | | |

- Main's own spill-colour headroom is +51 M with the full swap climb (all 5,778 pairs, converged in 2 rounds). The best
  permutation has 4 independent cycles:
  - an 18-cycle in `-2464..-3120` (the clone-run and tail spill slots; compare w14a139's +43 tail pin): **+28**;
  - an 11-cycle, **+13**, that moves **main's sharing tag `-2272` to the original's holder slot `-2384`** (main's `-2384`
    occupant goes to `-2416`, and `-2488` goes to `-2272`). The tag alone swapped with `-2384` gives +6, and with the
    `-2416` home +11;
  - two 2-cycles, +4 and −5.
  Per bin, the gains are 0x2c00 +9, 0x3400 +10, 0x4800 +8 and 0x5800 +9.
  The tag cycle is the role swap of section 4 seen in the frame: the slot that the original gives its flag is best filled,
  in our code, by the value that has the flag's register-allocation role.
- e1's whole M loss (−255) is spill-colour numbering. Its code with the best colouring ties main's code with the best
  colouring (+2).

## 2. The angle's exact joint move (`tools/joint.py`)

e1's spill slots are main's with one extra slot inserted, the flag at `-2304`, and the `-2304..-2392` window reshuffled
(e1→main votes: 97 slots move by +8, 10 stay, 2 move by +24). The pin:
- every e1 slot goes back to main's offset for the same value;
- the flag goes to the original's `[r10-2384]` (`0x950`);
- main's `-2384` occupant, the sweep clone-run `r5` spill, goes to the one free slot.

| pin | M | ratio | bytes |
| --- | ---: | ---: | ---: |
| main | 2,248 | 0.67346 | 27,400 |
| J0: undo the shift, flag at the frame bottom | 2,249 | | 27,424 |
| **J1: flag -> -2384, clone-run spill -> free slot** | **2,250** | **0.67375** | 27,424 |
| J1 with the clone-run spill at its best home (-2376/-2416/-2448) | 2,252 | | 27,424 |

So freeing `-2384` for the flag is worth +1 M, and the whole joint move +2 to +4 M. That is before the 24 B repay. No
size knob in `sizeknobs-cto.json` removes 24 B at a cost of 4 M or less (e0 alone costs −3 M for +8 B), and J1 is a binary
relabel with no known source spelling. Looking for an ordinary spelling that frees `-2384` is therefore moot.

## 3. Pool-CPI and tree-phi forms, priced at main's layout

| variant (post-opt IR edits, `e/ir/` from w14a142/w14a132) | default llc M / bytes | layout break | restored M | restored Mperm |
| --- | ---: | --- | ---: | ---: |
| e1 + hpa (pool CPI r4 from the flag) | 1,855 / 27,448 | error group bb5.i..to_string moves to 0x3bf8 | 1,963 (27,408) | 2,261 |
| hc = hphi+hcs (w14a142) | 1,728 / 27,480 | bb56.i split (3 `COPY r6`) | 2,047 (27,440) | 2,190 |
| fl_c = hphi+hcs+hpa (the original's "tree phi to curve store and pool r4") | 1,708 / 27,464 | bb56.i split | 2,024 (27,424) | 2,168 |
| fl_pa = fl_c + event from the flag | 1,708 / 27,464 | bb56.i split | 2,024 (27,424) | 2,168 |
| e1 + cbphi (per-arm cashback phi) | 1,976 / 27,184 | | | 2,118 (unrestored) |
| hpa0 (pool r4 from `and %0,1`) | 2,109 / 27,432 | | | 2,149 (unrestored) |

New mechanism (e1+hpa): the error-group move is **not** the bb56.i r5 split. It comes from the dead sharing-tag reloads
(`dead $rN = LDD_V1 $r10, -2272`, the r9 tag split's leftovers; main has 27 dead reloads before branch folding). With hpa
they move from bb85.i/bb89.i142 to bb95.i129/bb44.i135/bb39.i131. bb95.i129 then keeps a non-mergeable
`$r3 = LDD -712; dead $r1 = LDD -2272` tail, stays a separate fall-through predecessor of bb56.i, and MBP places the 8-block
error group in front of it. `tools/mdel.py` (delete lines in named pre-branch-folder blocks) removes the 3 dead loads and
restores main's layout exactly. The flag then still costs 0x4c00 −13 (pool CPI) and 0x5c00 −11 (wallet).

## 4. What the original's flag actually is (role swap, read from the original's bytes)

- The original stores the flag **per arm** inside validate (`mov 0/1; stxdw [r10-2384]` at 0xe40, 0x1130, 0x14e0, and from
  r6 at 0x1830 and 0x18b0). e1 stores it once after the merge (0x1770 `stxdw [r10-2304], r2`).
- At every sweep-exit join the original reloads the flag into r1, and the reload is dead: `ldxdw r9,[payload];
  ldxdw r7,[tag]; ldxdw r1,[r10-2384]; jne r7,2` at 0x24a8, 0x2610, 0x3c60, 0x4aa0 (r2), 0x62d8 and 0x6398. At 0x62d8 and
  0x6390 main has the same instruction on `[r10-2272]`, the sharing tag.
- Store-backs: the original has 3, all on `-2384` (0x1d48, 0x44c8, 0x5b30). Main and e1 have 4 on `-2272`, e1+hpa has 6
  on `-2272`, and hc/fl_c have 0.
- So in the original, the flag takes the region-split role that the sharing tag takes in ours. fl_c, restored, already
  matches the original's r9 payload register at the joins, but it carries the accounts pointer (r5, `[r10-2264]`) across
  them instead of the flag. Every flag form tried scores at most main +3 with frame and registers masked (2,780–2,790
  against 2,787), so the remaining difference is register-allocation roles, which w14a142's RAPRIO forcing also failed to
  reproduce.

## Tools (`tools/`, experiment only; they import w14a142's `rx.py` from the same directory)

- `relab.py`: spill-permutation bound. `spills(pei.mir)`, `binspills(bin)` (binary-only approximation, a superset),
  `apply`, `M`, `votes`, `bestperm`. `python3 relab.py <dir>...` with `<dir>/f.o` and `<dir>/pei.mir`.
- `permhc.py <dir>`: bestperm plus a swap hill climb (`FULL=1` for all pairs).
- `scr.py <name> <edit.py>...`: post-opt IR edits on `rx/main/m.ll` -> obj + PEI MIR -> M, bytes, Mperm (`LAY=1` adds the
  block-placement layout, `KEEPLL=1` keeps `m.ll`).
- `mdel.py <in.mir> <out.mir> <blocks> <regex>`: delete matching lines in named pre-BF blocks (the dead-reload restore).
- `mscore.py <obj> <pei.mir>`: M and Mperm for a resumed (`rt.sh`) object.
- `joint.py <dir>`: the section-2 pins.

## 5. Why the tag gets `-2272` and not `-2384` (StackSlotColoring log, main)

`llcd -debug-only=stack-slot-coloring` on main's module: colour `fi#179` is `-2272`, and its members are SS#186 (the
long-lived sharing-tag piece starting at 17992r, weight 1.077, 8th heaviest of 181) and SS#260 (weight 0.0008).
Colour `fi#193` is `-2384`, with members SS#194 (weight 0.050, rank 16), SS#262 and SS#320. Colours are handed out in
weight order, so the tag takes an early colour because it is one of the heaviest spills. For the tag to land on `-2384`,
it would have to be about the 16th heaviest, the rank of the original's holder flag. That means less reload traffic on
the spilled piece, which the r9 region split decides, not source. This is the same register-allocation role swap, so the
+13 cycle has no ordinary-source lever known.
