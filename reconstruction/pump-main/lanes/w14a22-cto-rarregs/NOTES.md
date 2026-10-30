# w14a22-cto-rarregs: register assignment in the outline basins of admin_cto::execute

Target: `0x22a10 admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Continues w14a07-cto-cold306 (#3223, next idea 3) and w14a08-cto-outlinefill (#3232).
Bases: main 1b0ae70 (0.63661, M 2,125), then main 7e6aa9c (0.64140, M 2,141).
Ledger keys: `0x22a10-w14-{1b0ae70,7e6aa9c}-rarregs-*-v1`.

**Result: notes only, no landable change. The register gap this lane was meant to fix is gone, and no basin
loses on registers: on registers alone, every basin matches main or does better. The basins' deficit is block
placement, frame/spill colouring and diffuse jump-offset drift.**

Every number comes from the raw-IR capture + `opt -O3` + extracted-`llc` oracle (w13a43/w14a08 `src.sh`, `fw.py`).
It reproduces main exactly on both bases (0.63661 and 0.64140 at 27,400 B).
M = ratio x (3339 + n) / 2 is the number of matched original instructions. A pinned candidate beats main only with a
higher M.

## 1. Re-measure (step a)

| form | 1b0ae70 | M | 7e6aa9c | M |
| --- | --- | ---: | --- | ---: |
| main | 0.63661 @ 27,400 | 2,125 | 0.64140 @ 27,400 | **2,141** |
| RAR | 0.62530 @ 27,368 | 2,083 | 0.62830 @ 27,368 | 2,093 |
| RAR + 1:2 Some:None on the raw 306 switch (oracle) | 0.63645 @ 26,920 | 2,106 | 0.64158 @ 26,920 | 2,123 |
| f2 = RAR + HB0 (w14a07 has+tag, source) | 0.62989 @ 26,912 | 2,084 | 0.63564 @ 26,912 | 2,103 |
| f2 + llc None:Some 2:1 on the and-1 306 test (ceiling) | 0.63443 @ 26,912 | 2,099 | 0.64017 @ 26,912 | 2,118 |
| p3u+tu8 (w14a10 and-1 outline, source) | 0.63317 @ 27,336 | 2,111 | 0.63578 @ 27,344 | 2,120 |

- After #3241 put the accounts pointer in r8 at entry, the **w14a07 regcmp hunks at 0x1900 (-13) and 0x2580 (-11)
  are gone**. RAR+w12 is -1 and 0 there on 1b0ae70, and f2 is -1 and 0.
- RAR+w12 now loses at orig 0x640-0x1900 (-22). Main and the original place the t-copy block (the 306 Some arm:
  32 B copy of `t`, then the default/holder/sharing memcmps) **before** the 306 error block. The basin places it after
  306/296/326. Error-site order with the t-copy:
  - orig: `289 298 tcopy 306 296 326 312 307`
  - main: `298 289 tcopy 296 326 306 312 307`
  - f2 + 2:1: `298 289 306 296 326 tcopy 312 307`
  - f2: `298 289 296 tcopy 312 306 326 307`
  - p3u+tu8: `289 298 tcopy 306 296 326 312 307` (= orig)
- llc single-weight scan (`tools/scanw.py`, validate branches x {20:12, 12:20}) on f2 + 2:1: the best is +3 M (2,102 on
  1b0ae70). No llc weight closes the f2 gap.

## 2. Register census (step b): no basin has a register deficit

`tools/mm.py` gives M with registers masked, frame offsets masked, or both. `tools/rh.py` counts aligned instructions
that differ from the original **only in registers**.

| 7e6aa9c | raw M | reg-masked | frame-masked | both | register-only mismatches (rh.py) |
| --- | ---: | ---: | ---: | ---: | ---: |
| main | 2,141 | 2,501 | 2,288 | 2,656 | 421 |
| RAR+w12 | 2,123 | 2,485 | 2,326 | 2,700 | 403 |
| f2 + 2:1 | 2,118 | 2,479 | 2,321 | 2,694 | |
| f2 | 2,103 | 2,459 | 2,325 | 2,700 | |
| p3u+tu8 | 2,120 | 2,495 | **2,391** | 2,780 | 412 |

(1b0ae70: main 2,125 / 2,477 / 2,260 / 2,660; RAR+w12 2,106 / 2,457 / 2,298 / 2,704; p3u 2,111 / 2,440 / 2,371 / 2,781.)

- With registers masked the basins still trail main by 6-42 M. Their register-only mismatch counts (403, 412) are
  **below** main's (421). Register assignment is not where the basins lose.
- The per-bin hunks that are one-sided (`VERBOSE=1 rh.py`) are the AccountInfo clone runs at orig 0x3d00-0x4200 and
  0x4600 (p3u +9 and +6 against main) and three r9/r8 reloads in validate's error paths (0x08e0, 0x0aa0, 0x0f28). The
  0x4000 bin goes the other way (-25 for both basins). These are the clone-run RA cascades that w14a04, w14a06,
  w14a10 and w14a17 own. They are not basin-specific.
- With frame offsets masked, the basins lead (p3u +103, RAR+w12 +38). That lead is frame colouring.
  w14a18-cto-slotpin (#3253) bounds it: with any legal frame, main stays the best base by at least 19 M.
- p3u's largest single loss on 7e6aa9c (orig 0x3800-0x3c00, -15) is a spill-slot cascade in the arg build of the
  call at orig 0x3b70. Spill-slot reads (`[r10-0x9c8]`, `0x970`, `0x988` ...) differ in slot, not register.

## 3. Fill bound (step d): a neutral fill cannot add matches

`tools/fillsim.py` inserts N non-matching 8-B instructions before candidate instruction k and fixes every jump offset
that crosses the point. It then reports scorer-style M (difflib, calls and lddw immediates masked, as `oratio.py`
does).

- p3u+tu8 (1b0ae70, -64 B, 8 slots, every 8th position): **no insertion point raises M**. The best is the base 2,111.
  The worst is 2,058 at cand 0x3ec0.
- RAR+w12 (1b0ae70, -480 B, 60 slots): the best is +1 (2,107 at cand 0x1388), a pinned ratio of 0.63103 against main's 0.63661.
- p3u's jump-masked M is +81 over main (`tools/mj.py`), but `tools/jd.py` shows that this is diffuse offset drift: 125 of
  263 aligned jumps differ, against 112 of 252 for main, by small deltas from many regions. It is not one size shift
  that a fill at the right place could repair (`tools/shift2.py` gives the median offset per region).

So a fill must bring its own matched instructions: 18 or more for RAR+w12, and 21 or more for p3u+tu8 on 7e6aa9c.

## 4. Source screens in the basins (steps c and d, 7e6aa9c)

| trial | genes | bytes | ratio | M |
| --- | --- | ---: | ---: | ---: |
| p3u+tu8 | P3U,TU8 | 27,344 | 0.63578 | 2,120 |
| p3n (hb after quote_locked, validate `hopt:bool`) | P3N,TU8 | 27,336 | 0.63557 | 2,119 |
| p3m (`matches!` hb) / p4u (hb inside the state block) | | 27,344 | 0.63578 | 2,120 |
| p0u / p1u / p2u (earlier hb positions) | | 27,328 | 0.63057 | 2,102 |
| p3u + RAR + HB0 (and-1 holder + has form) | P3U,RARH,HB0 | 26,888 | 0.62746 | 2,075 |
| p3n + RAR + HB0 | | 26,880 | 0.62785 | 2,076 |
| p3u + HB0 (no RAR) | | 26,944 | 0.56396 | 1,867 |
| p3u + tu8 + RAR | | 27,344 | 0.62948 | 2,099 |

Knob screen on p3u+tu8 at 1b0ae70 (`data`: first 12 of the 43 applicable `sizeknobs-cto.json` knobs, before main moved):
none above 2,111. st_ql_first, L_share_none_first and cu_replace are byte-identical. g_old_fee_first gives 2,110 and
s_dest_borrow 2,099 at -80 B. prep_match gives 2,097, s_old_borrow 2,068 and s_frozen_first 2,010. The large fills
(v_fee_split, p_ev_ts_last, w_create_rev, w_ev_creator_first) give 1,656-1,918.

Reversal screen (`tools/revg.py`; each recent main landing's admin_cto edit reversed inside p3u+tu8 on 7e6aa9c,
to test whether levers tuned to main's register map hurt the basin): only reversing #3257 (`1b0ae70`, sharing program as
`to_account_info`) helps, by +2 (2,122). The other reversals give -2 to -6 (#3267 2,118, #3272 2,113, #3210 2,116, #3215/#3207 2,114,
#3200 parts 2,112-2,115, #3168 parts 2,108-2,115), and #3200's cashback `!holder`-first hunk gives 1,791.

## Next ideas

- The outline basins need a frame/spill-colouring change, not a register change. On frame-masked M, p3u+tu8 leads main
  by 103, but w14a18's legal-frame pin gives it only about +6. A source form that changes which intervals share a slot (StackColoring
  merges of `_112.i`/`_54.i`, per w14a18) is the only lever left in the basin.
- p3u+tu8 is the closest source basin (-21 M at -56 B on 7e6aa9c, -14 on 1b0ae70). Each main landing tuned to main's
  register map widens the gap, so a basin landing gets harder with each main move.

## Tools (`tools/`; the w14a08/w14a07 oracle tools, plus these)

- `mkv.py` + `genes2.py`: gene applier on `var/m3` (w14a07 genes plus `P3U` `P3N` `P0U` `P1U` `P2U` `P4U` `P3M` `TU8`
  `RARH`, and reversal genes `R_<sha7>[_i]` built from `revg.json`).
- `mm.py`: M raw, register-masked, frame-masked and both. `mms.py`: spill-slot-masked against object-masked M.
  `mj.py`: jump-offset-masked M.
- `rh.py <orig> <A> <B> [bin]`: register-only mismatches per bin; `VERBOSE=1` lists B-only hunks.
- `fillsim.py <orig> <cand> <nslots> [step]`: neutral-fill upper bound per insertion point (jump fix-up included).
- `jd.py`: aligned jumps whose offsets differ, by source and target region. `shift2.py`: median address offset per region.
- `regdiff2.py`: w14a08 regdiff with original addresses. `sw.py`: locates validate's raw 306 switch. `scanw.py`:
  w14a07 scan with a configurable line range (`LO`/`HI`/`J`). `revg.py`: reversal genes from main's admin_cto commits.
