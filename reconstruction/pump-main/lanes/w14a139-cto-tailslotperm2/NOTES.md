# w14a139-cto-tailslotperm2: legal colour pin and per-element colour order of the sharing CPI tail (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main ebe5387 (#3495): 0.67316, 3,123 slots, M 2,247, 1034/1034 (taken from `$BASE`, not rebuilt).
This lane re-runs w14a135-cto-tailslotperm. That lane turned out to have finished after all: its notes are on
`origin/swarm/w14a135-cto-tailslotperm` (6150921a2), and it has no PR. This lane adds its next idea 1: an interval-level,
liveness-checked pin of the tail spill intervals. w14a135's bounds were arm-local rewrites, which are only an upper bound.
Ledger: approach `tailslotperm2`, keys `0x22a10-w14-ebe5387-tailslotperm2-{legalpin,canon-legalpin,elemorder-mech,canon-scprog}-v1`.

**Result: no source change (notes only).**
- A legal colouring of the tail at the same frame is worth **+43 M, 0.68604 (+0.0129)**.
- The colour order that gives it is the clone-run window form, as w14a135 found.
- The original's canonical window form (w14a122 canon_all) gains +90 M under the same legal pin. That still only reaches
  about M 2,251, which ties main (+4) and is 39 M below main with the pin.
- No ordinary source lever separates the colouring from the window form. Every window-form move screened so far loses.

## 1. Legal interval-level pin (`tools/mirperm.py`; no build slot, ~2 s)

Inputs, all from the SDK llc and the shared debug llc on the slim post-opt module (`rx.py main --keep` -> `m.ll`):
- `pre.mir`: `-stop-before=stack-slot-coloring`. Spill FIs are still one per spilled interval here.
- `ssc.mir`: `-stop-after=stack-slot-coloring`. Its body lines map 1:1 to `pre.mir`'s (5,458 lines each).
- `ssc.log`: `-debug-only=stack-slot-coloring`, giving each interval's live segments, its weight and `Assigning fi#A to fi#B`.

What the tool does:
- It finds the sharing-CPI tail (the last run of 40 or more `LDD %stack.N` -> `ST* _55.i98, off` pairs in `pre.mir`).
- It gives each tail interval the colour of the original's slot for the same array piece (colour `c` is at offset
  `0x8e0 + 8*(c-179)` on this frame).
- It re-homes any other interval that now overlaps a pinned one onto the first existing colour it does not overlap.
  Overlap is checked on the logged live segments.
- It rewrites `ssc.mir` per instruction and runs `llc -start-after=stack-slot-coloring`.
- Calibration: the plain `ssc.mir` round trip (`rt`) is not byte-identical to main. It loses 19 M, all outside the region
  (0x4c00-0x6400). The pins change nothing there, so all deltas below are taken against `rt`.

| base | rt M | pin | pinned intervals | re-homed | dM vs rt | estimate vs real base |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| main ebe5387 (real M 2,247) | 2,228 | legal (`valid`) | 47 / 50 | 5 | **+43** (0x3c00 +1, 0x4000 +9, 0x4400 +9, 0x4800 +24) | **M 2,290 = 0.68604** |
| main | 2,228 | all 50 (3 illegal) | 50 | 2 | +50 | 2,297 (not realisable) |
| canon_all (real M 2,161) | 2,142 | legal | 47 / 50 | 5 | +90 | ~2,251 (main +4) |
| canon_all | 2,142 | all 50 | 50 | 2 | +96 | ~2,257 |

- The frame is unchanged in every row (max colour 285), so the pinned colourings fit main's frame.
- The 3 illegal pins want colours 179/184/185 (0x8e0/0x908/0x910, the original's key/lamports slots for global, sharing
  and pool_authority). In ours, function-long spills SS#181/185/186 hold those colours. This matches w14a13: in ours,
  10 long-lived spills cross the region, against 8 in the original.
- w14a135's arm-local rewrite bound for 0x4600-0x4a00 (+49 M) was close to this legal one (+43 M).

Per element on main (legal pin of one element's pieces only, dM vs rt): E0 +5, E1 +10, E2 +4, E3 +7, E4 +4, E5 +9, E6 0.
Per field across all elements: data +9, owner +10, rent +4. No single element or field carries the bound.

## 2. Per-element colour order (`tools/tailfi.py`, `elem_table_main.md`, `elem_table_canon_all.md`)

`tailfi.py pre.mir ssc.log` prints, for every tail reload: the pre-colour FI, its weight, its colour and offset, the
array offset it feeds, and the MIR line of its spill store. The tables give `ours/orig` slots per array element
(element k is at array offset 24+48k). The pieces are key +0, lamports +8, data +16, owner +24, rent +32, then the
signer/writable/executable bytes at +40/+41/+42.

- **Original:** in each element, the six trailing pieces take consecutive colours in the order data < owner < rent < signer
  < writable < executable. That is the derived `AccountInfo::clone` load order (`solana-account-info` 2.3.0 is
  `#[derive(Clone)] #[repr(C)]`, fields key, lamports, data, owner, rent_epoch, is_signer, is_writable, executable).
  Key and lamports sit on shared colours.
- **main:** for E2, E3 and E4, rent, signer, writable and executable already have exactly the original's colours (bold
  marks a difference). Only data and owner are displaced:
  - data_k is spilled after exec_k, so it takes the colour the original gives the next element's run;
  - owner_k lands on a shared colour (0x958, 0xa98, 0x940) or late.
- **canon_all:** each element's order is data < owner < signer < writable < executable, the original's, but the run is
  displaced:
  - key joins the run just before data;
  - rent falls onto a shared colour (0x968/0x970/0xa90);
  - colour shifts against the original are mostly +1 to +6 (histogram in the ledger row).

Mechanism (agrees with w14a135 section 2): StackSlotColoring sorts by weight, and the weight falls along the chain with
each Rc overflow branch. So a colour follows its spill store's block. InlineSpiller puts the spill right after the def,
so a spill store's block is its load's block. In MIR, element E4's rent and flag loads and spills sit in its own
lamports-clone window (bb.306), before its data clone (bb.308/bb.310), so data and owner spill later. The colour
permutation is therefore exactly the window form, with no separate degree of freedom.

## 3. Step-2 screen (IR oracle on w14a122 `pl/mn.ll`)

`tools/canon_sc.py` is w14a122's `canon.py` limited to the two plain `to_account_info` bases that `canon.py` excluded
(`%_439` at `_270+152`, the first clone of the arm, and `%_473`). It applies the canonical move: owner/rent/flags go to
the block after the data clone, and key goes to the lamports block.

| move | M | bytes |
| --- | ---: | ---: |
| main | 2,247 | 27,400 |
| canon `%_439` | 2,220 | 27,392 |
| canon `%_473` | 2,183 | 27,416 |
| both | 2,159 | 27,408 |

Both lose, with the same sign as the literal canon moves. The source levers the brief lists all act only through the window
form, and all were already screened below main by w14a122 (source reverts), w14a81 (62-form literal/plain lattice) and
w14a135. So no build was spent.

## 4. What is left

- The +43 M is real colour headroom at the same frame. It needs one of two things:
  - the window form to move without losing skeleton matches elsewhere; no such form is known;
  - two fewer function-long spills crossing the region (the 179/184/185 conflicts, w14a13's swept and holder/cashback
    spills), which would also free the original's key/lamports slots.
- canon_all + legal pin ~ main. So if a future main removes the two extra long-lived spills, re-run
  `mirperm.py` on canon_all: it is the cheapest test of whether the faithful window form has started to pay.

## Tools (experiment only)

- `tools/mirperm.py <dir> [all|valid|<array offsets,...>]` (env `EXCL=179,184,185` excludes pins to those colours). `<dir>`
  holds `pre.mir`, `ssc.mir`, `ssc.log` and `llc.sh` (SDK llc with fastbuild flags, `"$@"`). It imports `px2.py`
  (w14a114/w14a122 tool set), so put it next to `px2.py`, `rx.py` and `eseq.py`.
- `tools/tailfi.py pre.mir ssc.log`: the per-tail-reload FI, weight and colour table.
- `tools/canon_sc.py`: the section-3 screen (needs w14a122's `cbmv.py`).
- To recapture: `rx.py main --keep` (about 10 min of opt on a loaded machine), then the three llc dumps above on
  `rx/main/m.ll`.
