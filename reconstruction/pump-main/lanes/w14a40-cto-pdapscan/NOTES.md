# w14a40-cto-pdapscan: pscan coordinate descent on the PDA-first base (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: continue w14a02-cto-validatecr (#3209), w14a09-cto-pdara (#3234) and w14a11-cto-headchain (#3227). The original
computes the holder_key `find_program_address` before the `shared` memcmp chain; main does the reverse. PDA-first
(`p1`: w14a11 `src_edits/p1.py`, `creator==key()` operand order) wins on skeleton but loses on register naming in the
orig 0x3000-0x3800 AccountInfo clone runs. Earlier lanes never ran pscan (AccountInfo literal placement) on a PDA-first
base. This lane does that, as a coordinate descent over every scannable TCF and sharing CPI clone.
Bases: main faf9962 (0.65129), 28ab23a (0.65488), 0fbf8da (0.65578). Main reached 0fbf8da -> 6330811 (0.65698) while the lane ran.
Ledger: approach `pda-pscan`, keys `0x22a10-w14-<sha7>-pdapscan-*`.

**Result: no zero-loss gain, no source change.** The literal descent recovers most of the TCF-region register loss
(orig 0x3000-0x3800 exact 2 -> 156, main 183). But PDA-first plus the tuned literals tops out at **0.63088 @27,352 B**
on 0fbf8da (main 0.65578), 0.025 below main. The same state on main 6330811 (0.65698) gives 0.63028. It is also 48-56 B short of 27,400, and no faithful knob set repays that.

## Oracle and tools (`tools/`, experiment only)

The raw-IR capture plus `rx.py` (opt -O3 + llc) comes from w14a30/w14a23 (`capvar.sh`, `capraw.py`, `rx.py`, `pscan.py`;
copy them from `$C/lanes/w14a30-cto-shareauthport/tools` or from w14a23 `tools/`). It reproduces every main exactly
(`eq_main`: faf9962 0.65129, 28ab23a 0.65488, 0fbf8da 0.65578).

- **Post-opt IR must go through `opt -passes=instnamer` before pscan.** Without it, moving numbered (`%497`) values breaks
  llc's numbering rule, and about half of the `pp` orders fail to compile. The instnamer'd module gives llc output
  identical to the original module (checked on base and p1).
- `cdesc.py <start.ll> <dir> <rounds> <lo> <hi> clones..`: the coordinate descent. For each clone it runs `MODE=place`
  (729 placements), then `pp` on the top-4 placements and on the current placement. It accepts the best result if the
  ratio improves with bytes in [lo,hi], rescores the dumped module, and iterates rounds until no clone moves.
  About 1-1.5 min per clone at 6 threads, on a loaded machine.
- `lab2src.py <out.py> <base.py> <log.jsonl>..`: turns accepted pscan labels into source literals
  `{let x:&AccountInfo=a.X.as_ref();AccountInfo{..}}` in the TCF / sharing CPI. Existing field expressions such as
  `data:a.pump_amm.data.clone()` are kept. The IR-name maps (`C`, `C1`, `C2`) are per base. Every source capture of a
  descent state reproduced the IR ratio exactly (p1r0 0.58256, p1cd2r0 0.62939).
- `mkrc.py` / `mkrc_lib.py`: the Rc-order swap. For each clone it writes a variant with the lamports/data clones swapped
  in source, on top of the accepted state.
- `genh.py`: hand-written inline-field literals for `coin_creator` (cc) and `pump_creator_vault` (pcv), the
  tcflit s1 forms that pscan cannot reach.
- `reg.py` / `regm.py`: exact matches per 0x800 orig region (plain, register-masked R, register+stack-offset-masked RF).
  `side.py <rx name> lo hi` gives an orig/candidate side-by-side. `clones.py` lists AccountInfo clone base values.
  `ovl.py` (from w14a09, now takes the last selectOrSplit) lists vregs overlapping a vreg on a register in a
  `-debug-only=regalloc` log (`$C/llvm-dbg/build/bin/llc`).

## Descent

Each pscan coordinate is one AccountInfo clone. A label is `<P per field key,owner,rent,signer,writable,exec>:<read order>`.
P0 means before the lamports Rc clone, P1 between the two Rc clones, P2 after the data clone.

| step | base | ratio | bytes | orig 0x2800 / 0x3000 / 0x4000 exact | note |
| --- | --- | ---: | ---: | --- | --- |
| main | faf9962 | 0.65129 | 27,400 | 160 / 183 / 113 | |
| p1 | faf9962 | 0.56963 | 27,360 | 138 / **2** / 87 | p2 (`key()==creator`) 0.56873 |
| cd1 round 0 (11 TCF clones, 9 moved) | faf9962 | 0.58256 | 27,384 | 150 / 25 / 89 | source-confirmed |
| cd1 round 1 | faf9962 | 0.60483 | 27,376 | 124 / 132 / 87 | pump_creator_vault_ata `202221` +0.016 |
| cd1 round 2 (final) | faf9962 | 0.61709 | 27,352 | 127 / **156** / 87 | first pump_amm, ATA program |
| main | 28ab23a | 0.65488 | 27,400 | 159 / 183 / 113 | |
| p1 | 28ab23a | 0.5716 | 27,344 | | |
| cd1 literals ported (p1cd1) | 28ab23a | 0.62058 | 27,336 | 128 / 156 / 87 | |
| cd2 round 0 (+7 sharing clones) | 28ab23a | **0.62939** | 27,352 | | TCF +0.0006, sharing +0.0082 |
| cd2 round 1 (TCF part) | 28ab23a | 0.62939 | 27,352 | | TCF clones at fixpoint |
| main | 0fbf8da | 0.65578 | 27,400 | | |
| p1cd2r0 ported | 0fbf8da | 0.62609 | 27,352 | | |
| + pump_creator_vault_ata Rc swap (data first) | 0fbf8da | 0.62948 | 27,344 | | best of 17 Rc swaps |
| cd3 round 0 (TCF + sharing) | 0fbf8da | **0.63088** | 27,352 | | event_authority `222112`, sharing CpiContext pump_fees key-first |
| cd3 round 1 | 0fbf8da | 0.63088 | 27,352 | | **fixpoint**: no TCF or sharing clone moves |
| main | 6330811 | 0.65698 | 27,400 | | |
| best state ported (source) | 6330811 | 0.63028 | 27,352 | | -0.0267 against main |

Accepted coordinates (final, in source order) are in `SUMMARY.json` (`best_state`). `src/best_state.py` is the
capvar EDITS/T file for the best state (set `PDAPSCAN_TOOLS` to this lane's `tools/`). Descent logs: `cd{1,2,3}_log.jsonl`.
Rc swap rows: `rc_swap.jsonl`. Hand-literal and entry-copy rows: `handlit.jsonl`.

Rc-order swap screen on p1cd2r0 (0fbf8da, 0.62609), one clone at a time: pump_creator_vault_ata **0.62948** (-8 B),
TCF program 0.62789, event_authority/sharing_config = base, all others lose (sharing pool_authority 0.61589,
coin_creator_vault_ata 0.62159). pcv_ata+program together give 0.62768.

Hand-written inline-field literals (tcflit s1 forms) on p1r0 (faf9962, 0.58256 @27,384): pcv owner-mid `KLODRSWE`
0.58632 @27,424 (+0.0038, +40 B), cc owner-mid 0.58431 @27,416, other orders 0.553-0.577. On p1cd1 (28ab23a, 0.62058)
the same pcv form loses (0.57914 @27,368), and pcv+cc gives 0.55737. Like the literal orders, they help only in one RA
state.

## How much of the register shift the descent recovers

Exact matches in orig 0x3000-0x3800 (the TCF clone runs, accounts pointer orig r8): 2 (p1) -> 25 -> 132 -> 156, against
main's 183. Most of the gain comes in round 1, from the pump_creator_vault_ata placement `202221` (25 -> 124). The
accounts pointer itself stays on **r6** in every descent state: each `ldxdw rX,[r6+0xd8/0xe8/0x48..]` still differs from
the original's `[r8+..]`, as `side.py cd1r1_x12i 0x3000 0x3300` shows. What the literals recover is everything around those
loads in the clone runs: the field-copy registers, the spill slots and the Rc overflow-check blocks, which now line up
with the original again. So the remaining 27 lost there are mostly the accounts-pointer loads. What stays lost is outside the clone run:

- orig 0x2800-0x3000 (the wallet ATA / collect clone run just before the TCF CPI): 160 (main) -> 127. There the accounts
  pointer is still `[r6+..]` instead of the original `[r8+..]`.
- orig 0x4000-0x4800: 113 -> 87, unchanged by every round.
- With registers masked (R), p1cd1 is 0.73065 against main's 0.75285. With registers, stack offsets and jump offsets
  masked (skeleton), p1 is **0.83491** against main's 0.82385 on 28ab23a, and the descent keeps it (p1cd1 0.83413).
  p1's skeleton gain (+0.011) does compound with the literal tuning. It is the register/frame layer that stays below main.

## Mechanism (debug llc, p1cd1 vs main on 28ab23a)

The accounts pointer `%0` is assigned r8 first in both. In p1 it is evicted early by `%2`, the sharing_config
AccountInfo pointer (`LDD %0,144` at 688r). That pointer is live across the PDA call's two `shared` memcmps
(688r-1536r, in the entry blocks). On main it is not live there. When `%0` is later region-split, its r8 static cost is
4.18 in p1 against 3.01 on main, so the split goes to r6 (static 3.13). The long-lived Err-payload class (`%1651/%1652`,
span 4944-71744) sits on r8 on main and on r6 in p1. That is the w14a09 cascade, still present on 28ab23a.
The original instead spills the sharing pointer (to -0x8e0) and keeps r8 = accounts, r6 = args, r9 = curve and
r7 = `new` pointer at entry. Literal placement realigns the code around the accounts-pointer loads (0x3000 recovered to 156), but `%0` stays on r6 in
every state. It cannot remove `%2`'s entry-block interference, and that interference is what costs 0x2800, 0x4000 and
the remaining accounts-pointer loads.

## Size

PDA-first is -56 B against main on 28ab23a and 0fbf8da (-40 on faf9962, -16 on 769f331). The descent states sit at
27,336-27,384. The best state is 27,352 (needs +48). The w14a31 +8 knobs (k3, n_ensiflet, wl_writ_eq) and s_rent_get
(+16) add up to only +40, and each costs 4-10 M on main. Of the ~2,600 descent rows that land exactly on 27,400, the
best is 0.61204 (slots 3,154, positionally closer than main's 3,279, but ratio-ranked).

## Next ideas

- PDA-first only pays if `%2` (the sharing pointer) stops being a callee-saved-register value across the entry
  memcmps, so that it spills as in the original. That needs 4-register pressure at entry: the `new` pointer held from
  orig 0x1e0 to 0x538, plus curve and args (w14a09 idea 2). Screen pda again on any base that holds `new` live at entry.
- Rejected here: an entry copy of `new` (`let args=&(new,)` moved to entry or before the PDA) on the best state gives
  0.44458 / 0.44189 @27,544 B. The plain source tuple does not give the original's entry pressure.
- Re-run `cdesc.py` from the best pda state after each main move. main's own TCF/sharing literal tuning (#3334, #3340,
  #3344, #3354) is tuned to the shared-first basin and does not carry over. Each port loses ~0.003 until it is re-descended.
- The wallet/collect clone run (orig 0x2800-0x3000) has no scannable clone in this module (its AccountInfo clones are
  outlined or inline-field). A literal form for those clones would give the descent the coordinate it lacks.
