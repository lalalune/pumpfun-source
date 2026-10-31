# w15a18-cto-s1greedy: RA-faithful s1 ceiling with a patched greedy (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: w15a06-cto-swepts1joint (#3656) next idea 1. s1 (all seven `AdminCtoSharingConfig` fields as plain
`to_account_info()`) bounds at M 2,416 with the legal tail pin plus ideal register naming, but physreg pins cost about 0.22.
This lane replaces the pins with greedy queue-priority, cascade and spill-weight overrides in a private llc, so every cell is
an allocation greedy itself can produce. It then asks which IR property sets the winning overrides and whether a source
spelling of s1 produces them.

Bases: s1 and main `m0` raw-IR captures on 90300f9 (w15a06's, re-scored: s1 M 2,145 @27,376, main M 2,248 @27,400);
s1 re-captured on main 86e2a6b for the source screen (s1x, 0.64319 @27,376, M 2,146). Main 86e2a6b is 0.67376.
Ledger: approach `s1greedy`, keys `0x22a10-w15-{90300f9,86e2a6b}-s1greedy-*`.

**Result: notes only, no source change.**
- With greedy decisions alone (no physreg pins), s1 passes main: 6 overrides give M 2,255 @27,352 (main 2,248), and 13 give
  M 2,276 @27,320 (ratio 0.68287; unmasked true LCS 2,279 against main's 2,253). The pin cell rises with it: pinV 2,325
  against main's 2,291.
- The same override class on main is nearly flat (best M 2,251 after a two-step climb; see section 3).
- The overrides do not map to one IR property. They are a chain of eviction decisions among the 56 sharing clone pieces,
  each needing a large weight or priority change (spill weight x3, not x1.4). 52 source spellings of s1 (literal evaluation
  order, program clone after the struct) are all at 0.632-0.654 as built. None reaches main.
- Verdict: s1 is RA-recoverable in principle (+131 M from greedy decisions), but no ordinary source lever moves those
  decisions. s1 is worth more lanes only with a new mechanism that changes the clone pieces' spill-weight densities by
  integer factors (for example fewer simultaneously live pieces), not by reordering.

## 1. Private llc (`tools/build.sh`, `tools/extra.py`)

w14a84-cto-raprio's RAPRIO llc (copy its `llc-patch/*.patch` next to `build.sh`) plus three hooks added by `extra.py`:
- `RAPRIO_CASC="309=0x7ffffff0"`: set the vreg's eviction cascade at its first enqueue. A high value means nothing with a
  lower cascade can evict it, and it can evict anything older. On these bases it behaves exactly like `RAPRIO_WEIGHT=*10`
  (every pair of casc/w10 singles is byte-identical), so it is a spill-weight lever.
- `RAPRIO_WEIGHT="309=*3,338=2e-6"`: override a vreg's spill weight right after `calculateSpillWeightsAndHints`.
- `SF <vreg> orig <root> fi <slot>` log lines: which original vreg each spill slot (FI) belongs to. This maps
  StackSlotColoring FIs (w15a06 `coldiff.py` / `colmap.py`) back to greedy vregs.
- Build: about 12 s (two TUs). With no hooks set the object is byte-identical to the SDK llc (s1 0.64289, main 0.67346).

Scoring (`tools/cell.sh`, `tools/scr.py`, `tools/climb.py`):
- `cell.sh <m.ll> <dir>` runs the private llc (env honoured) to stack-slot-coloring, then w15a06's exact `mirperm.py`
  round trip. It prints three cells: free (as allocated), pinV (legal tail colour pin) and pinA (all 50 tail pieces pinned).
  It takes about 0.6 s.
- `scr.py <m.ll> <jobs.jsonl> <out.jsonl> [n]` runs a parallel screen over jobs given as
  `{"prio":..,"casc":..,"weight":..,"force":..}`.
- `climb.py <m.ll> <singles> <log> <M|pinV|pinA> [rounds] [topk] [base]` does forward selection from the singles.

## 2. s1 decision map (90300f9; M = matched masked tokens)

Single screens:
- s1 has 1,615 queued vregs. 635 sharing-clone-family singles (127 vregs x top/bottom priority, cascade, weight x10/x0.1)
  and 2,419 wide singles (top/bottom/cascade) were screened. 2,190 of them are no-ops.
- Best singles:
  - free M: casc %309, 2,181 @27,368;
  - pinV: casc %331, 2,279.
- Family-wide rules all lose (`r5`): E0-first or E6-first queue order (1,925 / 2,013), cascade-protect E0 (2,066),
  E0 weight x10 (2,098), flat weight (2,118).
- So "keep E0's Rc and owner pointers in registers" (w15a06's reading) is destructive when applied as a policy.

Forward selection (`cl_U`, then a whole-pool rescreen each round):

| step | override | value (root def, `vname.py`) | M | bytes | pinV |
| ---: | --- | --- | ---: | ---: | ---: |
| 0 | - | s1 | 2,145 | 27,376 | 2,250 |
| 1 | casc %309 | E2 (global) lamports Rc ptr `LDD %307,8`; evicted from r0 by E5.own %338 | 2,181 | 27,368 | 2,257 |
| 2 | top %321 | E3 (mint) rent_epoch `LDD %316,32` | 2,213 | 27,320 | 2,277 |
| 3 | top %334 | E5 (event_authority) AccountInfo ptr `LDD %0,144` (sunk addr) | 2,227 | 27,352 | 2,289 |
| 4 | bottom %354 | pump_fees lamports Rc ptr `LDD %352,8` (`%352 = [%0+152]`) | 2,230 | 27,312 | 2,289 |
| 5 | casc %348 | E6 (program) rent_epoch `LDD %343,32` | 2,247 (0.67376) | 27,352 | 2,310 |
| 6 | bottom %339 | E5 rent_epoch `LDD %334,32` | **2,255** (0.67616) | 27,352 | 2,310 |
| 7 | bottom %302 | E1 (authority) owner `LDD %298,24` | 2,260 | 27,352 | 2,310 |
| 8 | bottom %1614 | `LD_imm64 @vtable.4` piece (bb32.i) | 2,263 | 27,352 | 2,313 |
| 9 | casc %226 | TCF clone lamports Rc ptr `LDD %224,8` | 2,265 | 27,336 | 2,315 |
| 10 | bottom %2184 | piece of `%209 = [%0+232]` | 2,271 | 27,328 | 2,320 |
| 11 | casc %1755 | piece of `%129 = LDD %127,0` (bb22.i144) | 2,274 | 27,328 | 2,323 |
| 12-13 | top %460, bottom %2050 | bb12 locals | **2,276** (0.68287) | 27,320 | 2,325 (pinA 2,329) |

Main as built for comparison: 2,248 @27,400 (pinV 2,291, pinA 2,298).

True LCS against main (w14a128 `lcschunk.py`):

| mask | main | s1 | s1 + 3 overrides | s1 + 6 overrides | s1 + 13 overrides |
| --- | ---: | ---: | ---: | ---: | ---: |
| unmasked (`---`) | 2,253 | 2,205 | 2,240 | 2,259 | 2,279 |
| default (rfj) | 3,007 | 3,029 | 3,027 | 3,035 | 3,028 |

The whole gain is in 0x3c00-0x4c00, the sharing clone run and tail (+19..+24 at 0x4400).

Tail colours (`coldiff.py`, ours slot minus the original's, in 8 B units):
- After steps 1-3, w15a06's +3 shift on E1-E3 becomes 0 or +1 (E1 `+0 +0 +0 +0 +0`, E2 `+0 +0 +0 +0`).
- With 13 overrides, E1-E5 are within 0-2 of the original's slots. E0.own -25, E3.data/own -18/-20 and E1.lam +23 remain.
- So the shift w15a06 found is an RA cascade that a few greedy decisions undo: the E2/E3/E5 pieces must win the evictions
  that s1 gives to the later clones' pieces.

## 3. Same override class on main (fairness check)

- Main m0, 122 sharing-family vregs x 5 ops (`rm2`): 348 of 610 change the code, and the best single is M 2,250 (bottom %338).
- A forward climb stops at 2,251 after two steps (bottom %338, bottom %1873), with pinV unchanged at 2,291.
- Main is at a local optimum for these levers; s1 is not. s1 with 6 decisions (2,255) beats main's same-class ceiling.
- The wide-pool main climb is in section 6 (`cl_mU`).

## 4. Which IR property sets the decisions

| decision | lever | threshold | IR property |
| --- | --- | --- | --- |
| casc %309 | spill weight | `*1.4` beats the first evictor (%338) but loses further down; only `*3` reproduces casc (M 2,180) | weight density (uses / size): a 3x density change, not one extra use |
| top %321 | queue priority (size) | absolute 0xa0000000 + 6,000 (size 2,880 -> 6,000) gives 2,175; 4,000-5,000 is worse than s1 | interval size; it needs to be dequeued before the E0/E1 pieces (5,152-5,984) |
| casc %348, casc %226, casc %1755 | spill weight | x10-equivalent | weight density |
| bottom %339, %302, %354, %2184 | queue priority | allocated last | smaller or later interval |

The clone pieces form an eviction chain by spill-weight density. Each piece has the same two uses (field load, CPI array
store), so its weight is about 1/size, and every later (shorter) clone's piece evicts an earlier one
(`E 309 from R0 by 338`, `E 294 from R0 by 309`, ...). The original's colouring needs specific earlier pieces to win
evictions against later ones, which a uniform order or density change cannot give (section 2, family rules). In IR terms the
pieces' relative weights would have to change by integer factors, which means different use counts or live-range lengths per
piece, not a different clone order.

## 5. Source spellings tried (raw-IR capture + opt + llc on main 86e2a6b; 1 build slot each, about 1 minute)

All free cells (main 0.67376 / M ~2,249 @27,400):

| variant | ratio | bytes | M |
| --- | ---: | ---: | ---: |
| s1x (s1 re-captured on 86e2a6b) | 0.64319 | 27,376 | 2,146 |
| sharing_config first (`p_scfirst`) | 0.65028 | 27,360 | 2,169 |
| program first (`q_prpaauglmiscev`, best of 44 orders) | 0.65418 | 27,384 | - |
| reverse order | 0.63909 | 27,368 | 2,132 |
| event_authority, program first | 0.63559 | 27,360 | 2,120 |
| global, mint first | 0.64189 | 27,384 | 2,142 |
| sharing_config last | 0.64258 | 27,352 | 2,143 |
| ctx after (`let ac=AdminCtoSharingConfig{..}; CpiContext::new_with_signer(prog, ac, ..)`) | 0.64387 | 27,344 | 2,147 |
| 44 literal orders (each of sharing_config / pool_authority / program at all 7 positions, plus 26 random) | 0.632-0.654 | 27,328-27,416 | - |

- The literal evaluation order moves s1 by at most +0.011, and no order approaches main.
- The best order's greedy ceiling (`p_scfirst` + climb over its sharing-family singles) is M 2,192 @27,352, which is below
  s1's own climb.
- Definition order is therefore not the property behind the decisions.
- No codegen-forcing construct was tried (BRIEF RULE).

## 6. Next ideas

- s1 + 6 greedy decisions is the RA-faithful lead: 0.67616 / M 2,255 @27,352 (pinV 2,310). It needs a source form in which
  the E2/E3/E5/E6 pieces carry 3x or more spill-weight density than their evictors.
  - Candidates are forms that make those pieces' live ranges short. For example, store each clone's pieces into the CPI
    account array at clone time. That needs `Vec`/array-literal CPI forms, which earlier lanes priced only on main's
    literal structure.
  - The other candidate is forms that give them more uses: a second consumer of the same field, if any legitimately exists.
- A fully RA-faithful upper bound for s1 at 27,400 is not known, because every override set shrinks s1 (27,320-27,368 B).
  The size-knob catalog (`$SWARM/w11/sizeknobs-cto.json`) would have to repay 32-80 B.
- `tools/cell.sh` + `tools/scr.py` + `tools/climb.py` turn any raw-IR candidate into an "RA ceiling" in about 10 minutes.
  Other lanes can use it to tell whether a structural loss is RA-recoverable before spending builds on partners.
