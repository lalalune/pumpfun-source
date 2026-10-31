# w14a135-cto-tailslotperm: spill-slot permutation of the sharing CPI array tail (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main ebe5387 (#3495): 0.67316, 3,123 slots, M 2,247, 1034/1034. Continues w14a122-cto-shareclonealias (#3522).
Ledger: approach `tailslotperm`, keys `0x22a10-w14-ebe5387-tailslotperm-{perm-bound,slotorder-mech,canon-perm}-v1`.

**Result: no source change (notes only).** A perfect spill-slot permutation in the tail is worth up to +0.0147, but the
permutation is not an independent order. StackSlotColoring sets it from the spill-store position along the clone chain,
so it follows the clone run's window form. The original's window form (canon_all) stays below main even with perfect
tail colouring.

## 1. Permutation bound (`tools/permb.py`, no build slot, ~1 s)

`permb.py <cand> <orig_lo> <orig_hi> [--global] [--rw cand_lo:cand_hi]`:
- skeleton-aligns cand with the original (xled `fmask`);
- collects (cand slot -> orig slot) votes from aligned 8-byte r10 accesses in the orig range;
- builds a bijection sigma (vote-greedy, displaced slots closed onto vacated ones, 8-byte clean slots only);
- rewrites every access of those slots, either function-wide or only inside `--rw`;
- scores the result with px2 `score_bin` (M, ratio, slots, per-0x400 chunk dM).

| orig range voted | rewrite scope | sigma slots | M | ratio |
| --- | --- | ---: | ---: | ---: |
| (main) | - | - | 2,247 | 0.67316 |
| 0x4800-0x4a00 | function-wide | 28 | 2,256 | 0.67585 |
| 0x4700-0x4a00 | function-wide | 35 | 2,269 | 0.67975 |
| 0x4800-0x4a00 | sharing arm (cand 0x3b00-0x49a8) | 28 | 2,279 | 0.68274 |
| 0x4700/0x4600-0x4a00 | sharing arm | 35/42 | **2,296** | **0.68784** |
| 0x3c00-0x4a00 | sharing arm | 48 | 2,273 | 0.68095 |

- The arm-local rows are upper bounds. They give the tail's values their own colours, which a real colouring can do only
  if the shared colours' other live ranges allow it.
- The function-wide rows lose in 0x2800 and 0x3800 (-8 to -13 M). The same colours carry TCF clone-run values there.
- Gains split as: 0x4800 chunk +26, 0x4400 +10, 0x4000 +11 (the clone-run spill stores of the same values), 0x3c00 +3.

## 2. Mechanism: what orders the tail slots (debug llc `-debug-only=stack-slot-coloring` on main's m.ll)

- execute has 362 spill intervals.
- StackSlotColoring stable-sorts them by weight (the sum of relative block frequencies of their refs), with ties in FI
  order. Each interval then takes the lowest used colour it does not overlap, or else the next free one.
- In the clone run, the weights fall monotonically along the chain: the 2-ref flag/field spills go from 7.807072e-04
  (SS#195) through 7.807062e-04 to 7.807054e-04 (SS#213/214), and the 3-ref ones sit near 1.17106e-03.
  Each Rc `strong == 0` overflow branch removes a little frequency, so a value stored later in the chain gets a later
  (deeper) colour.
- `tail_main.txt` and `tail_canon.txt` (`tools/slotord.py`) list the tail reloads with each slot's last spill store.
  Sorted by store position, the tail slots are monotonic in both the original and main, apart from shared colours
  (marked `*`, reused from earlier, higher-weight intervals):
  - orig: `970 968 960 948* 978 980 910* 8e0* 9a8 9a0 998 990 988 9b0 918* 900 9d8 ...`
  - main: `928* 990 988 980 978 970 998 940* 900* 9a8 9a0 9b8* 9b0 9c0 9c8 9d8 ...`
- So the permutation is a function of which Rc window holds each field load and its spill store. That is the
  literal-vs-canonical window form (w14a122 section 1), plus which earlier colours are free to share. No second
  degree of freedom (eviction order, split order, FI order) can be moved separately: within a block, ties fall back to
  FI order, and that only flips adjacent same-block pairs.
- Colouring with sharing is what the original used: `llc -no-stack-slot-sharing` gives 0.60365 and
  `-disable-ssc` gives 0.59227.

## 3. Canonical form with perfect colouring

| form | M | + tail perm (0x4800) | + tail perm (0x4600) |
| --- | ---: | ---: | ---: |
| main | 2,247 | 2,279 | 2,296 |
| w14a122 canon_all (original window form) | 2,161 | 2,228 | 2,256 |

The canonical form's tail colouring explains only about half of its 86 M loss. Even perfectly coloured, it stays 40-51 M
below main. So moving toward the original's window map to fix the colouring does not pay on the current structure.

## 4. Step 2 (source levers)

The bound is above +0.003, but section 2 shows the tail permutation is tied to the clone-run window form. The brief's
candidate levers act only through that form, and every one has already been screened below main:
- field order of the sharing CPI accounts / to_account_infos order;
- the order of the Rc clones' consumers;
- binding the CpiContext once versus inline;
- the position of the CPI result `?`.

The screens are w14a122 (source reverts: all below main), w14a81 (62-form literal/plain lattice x gate weights: all 310
below main) and w14a47. No new build was spent.

## 5. Next ideas

- An interval-level legal pin (w14a18 `slotpin.py`, stop-before=stack-slot-coloring) restricted to the tail intervals
  would turn the arm-local +49 M ceiling into a legal one. It needs porting to ebe5387's capture.
- Weight levers: a value's colour depends on the block frequency of its spill store. A source change that adds or removes
  one Rc clone (and so one overflow branch) between two clone windows shifts every later weight by the same factor, so it
  never reorders colours. Only moving a field load across a window boundary does, and that is the window form again.
- If a future main changes the clone-run window form, rerun `permb.py main 0x4600 0x4a00 --rw <arm>` and
  `slotord.py`. The gap between the two shows how much colouring is left to recover.

## Tools

- `tools/permb.py`: permutation bound (above).
- `tools/slotord.py <cand> <lo> <hi>`: per tail reload, the orig and cand slot, the last store position and the number of
  store sites.

Both run from a directory holding w14a122's tool set (`oracle.py`, `xled.py`, `dis.py`, `px2.py`, `rx.py`, `eseq.py`).
