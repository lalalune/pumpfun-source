# w14a93-cto-pdaheadra: PDA-first entry re-screen with RA tools (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: re-screen the original's entry order (holder_key PDA first, then the `shared` chain, then the curve bools, then
`quote_locked`) after #3409, using the RA tools that earlier PDA-first lanes did not have: w14a84's private greedy llc,
`colmap.py` and `cclimb.sh`, plus w14a87's legal-frame bound `fbound.py`.
Bases: main ecea702 (#3430, 0.67076 / 3,123) for the RA work, and main 963d1ee (#3437, 0.67226 / 3,123) after the merge
for the head-order screen and the re-checks. Both oracles reproduce their main (`eq_main: true`).
Ledger: approach `pdaheadra`, keys `0x22a10-w14-ecea702-pdaheadra-*` (963d1ee rows carry a `-963d1ee` trial suffix).

**Result: no zero-loss gain and no source change.** No PDA-first composite reaches main, even with RA decisions
forced. The best PDA-first build is a new order, PDA -> curve bools -> quote_locked -> shared (`o_PQSF`). It gives
0.65256 at 27,296 B on 963d1ee (main 0.67226), and its RA-recoverable ceiling is 0.66977 at 27,336 B on ecea702
(main 0.67076). Earlier lanes' best PDA-first builds were 0.6309 (w14a40) and 0.574 (w14a09).

## 1. Ceilings per entry composite (ecea702; 963d1ee in brackets)

- plain, regonly, L1 and L2 come from `regceil.py` (w14a84):
  - regonly masks registers only, so it is a perfect colouring at the same frame;
  - L1 masks frame offsets;
  - L2 masks frame offsets and registers.
- M, fR, rfR and rfjR come from w14a87 `fbound.py`:
  - M is the scorer's matched tokens;
  - fR is M after a legal (bijective) frame relayout;
  - rfR is fR with a perfect colouring;
  - rfjR is rfR with jump offsets also masked.
- "RA climb" is `cclimb.sh`: colour-target forces from the private llc, then forward selection. It shows how far RA
  decisions alone can take the composite, at any size.

| composite | bytes | plain | regonly | L1 | L2 | M | rfR | rfjR | RA climb (forces) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| **main** | 27,400 | **0.67076** [0.67226] | 0.76723 | 0.70072 | 0.78490 | 2,239 [2,244] | **2,623** [2,622] | 2,621 | **0.68085** @27,384 (8); 0.68065 @27,400 |
| fl | 27,368 | 0.64119 | 0.75600 | 0.66157 | 0.77998 | 2,139 | 2,586 | 2,594 | - |
| hkc | 27,464 | 0.53950 | 0.63016 | 0.69689 | 0.78636 | 1,803 | 2,580 | **2,715** | - |
| pda | 27,392 | 0.58906 | 0.71161 | 0.63071 | 0.78712 | 1,966 | 2,573 | 2,611 | 0.65806 @27,312 (11) |
| pda+hL | 27,392 | 0.58996 [0.58538 @27,400] | 0.71191 | 0.63161 | 0.78742 | 1,969 | 2,574 | 2,612 | 0.65896 @27,312 (11) |
| pda+hL, shared phi forced to spill | 27,288 | 0.58301 | 0.67938 | 0.67547 | **0.81207** | 1,942 | 2,559 | 2,599 | 0.65486 @27,280 (12) |
| pda+hL+hkc | 27,456 | 0.52162 | 0.63654 | 0.63085 | 0.78887 | 1,743 | 2,530 | 2,676 | - |
| pda+hL+fl (original order) | 27,488 | 0.47166 [0.47346] | 0.55361 | 0.47734 | 0.60745 | 1,577 | 1,896 | 2,049 | 0.51187 @27,568 (7) |
| pda+hL+fl, J relaid (sec. 3) | 27,496 | 0.59240 [0.59420] | 0.72548 | 0.63876 | 0.79605 | 1,981 | 2,548 | 2,637 | - |
| pda+hL+fl+hkc (full original entry) | 27,576 | 0.42759 [0.42968] | 0.52075 | 0.47925 | 0.60973 | 1,432 | 1,996 | 2,123 | 0.61260 @27,456 (12) |
| full entry, J relaid | 27,584 | 0.51530 [0.51739] | 0.63174 | 0.64039 | 0.79803 | 1,726 | 2,565 | **2,713** | - |
| pda+hL+qlB (PDA, QL, shared) | 27,360 | 0.58162 [0.58372] | 0.68296 | 0.65088 | 0.77530 | 1,940 | 2,505 | 2,541 | - |
| **pda+hL+fl+qlB = o_PQSF** | 27,296 | **0.65226** [**0.65256**] | 0.74741 | 0.69278 | 0.76872 | 2,173 [2,174] | 2,583 [2,581] | 2,586 | **0.66977** @27,336 (6) |

Readings:
- **Every PDA-first composite stays below main under a legal frame, even with a perfect colouring.** rfR is 40 to 120
  below main's 2,623. On 95a64ba, w14a87 found the same for `p1`. The RA climbs agree: pda and pda+hL top out at about
  0.659, and o_PQSF at 0.66977. Each of those is below main's plain ratio, and main's own RA ceiling is 0.68085.
- The PDA-first skeleton is better. L2 is +0.002 for pda+hL, +0.011 for pda+hL+fl once J is relaid, and +0.013 for the
  full entry once J is relaid. The full entry also leads under rfjR (+92 M), so jump distances are what keeps it
  behind. Those are code-size differences between branches and targets: the full entry is 184 B larger than the
  original. It is the "skeleton yes, frame/registers/size no" pattern every PDA-first lane has found.

## 2. Greedy step and occupant behind the `%0` cascade (ecea702, `tools/head.py`)

The private llc logs every greedy decision (`RAPRIO_LOG`). `head.py` names the head values from the pre-greedy MIR:
- the arg copies;
- `%0`, the accounts pointer (`LDD %ctx, 8`);
- the sharing pointer (`[%0+144]`);
- the curve pointer (`[%0+56]`);
- the `shared` phi (the first `MOV_ri 0`).

| build | who takes R6 / R7 / R9 over the shared chain | `%0` evicted from R8 | by |
| --- | --- | --- | --- |
| main (shared first) | R6 `shared` phi (step 12), R7 sharing pointer (step 19), R9 args `r5` copy (step 24) | step 168 | `%390`, a later value |
| pda+hL | R6 `shared` phi (step 12, evicts the sret `r1` copy), R7 curve pointer (step 8, evicts the `r2` copy), R9 args (step 18) | **step 21** | **the sharing pointer `%2 = [%0+144]`** |
| original (from its code) | r6 args (`mov r6,r5`), r7 the `new` pointer (`[r6-0xff8]`), r9 curve, r8 `%0` | never | - (sharing pointer spilled to -0x8e0, shared phi spilled to -0x920, sret spilled to -0x8f0) |

- **Mechanism:** with the PDA first, the curve pointer is loaded before the chain (hL) and lives across the first
  memcmp. The sharing pointer is live across the memcmp, the owner memcmp and `data_is_empty`, so it needs a CSR. At
  dequeue step 21, R6, R7 and R9 are taken. The cheapest victim is `%0`, whose spill weight is 1.3e-4 against the
  sharing pointer's 2.0e-3, so `%0` loses R8 at the head.
  - `%0` is then region-split. Its pieces over the TCF/sharing clone runs follow r6. That is w14a77's 24-site
    r8->r6 cascade over orig 0x2000-0x3800, which `colmap.py` shows as `%1683` r6 vs orig r8, 29 misses.
  - In main the curve pointer is not live across the chain, because main reloads it after the chain. The sharing
    pointer therefore fits in R7 and `%0` keeps R8 for the whole head.
- **The original spills the `shared` phi.** It writes `mov r1,0; stxdw [r10-0x920],r1` before the chain and
  `xor r0,1; stxdw [r10-0x920],r0` after `data_is_empty`. These are 64-bit stores, so they are spill slots, not a bool
  alloca.
  - Forcing that spill on pda+hL (`RAPRIO_FORCE=6=spill`) gives the original's head colouring: args take R6 and
    `%0` keeps R8. L2 rises to 0.81207, the best skeleton of any build in this lane.
  - The plain ratio falls (0.58301), and rfR falls to 2,559. Most of the L2 jump is the validate 289/298 error-block
    pair re-pairing in orig 0x800-0x1000 (+87 L2 there).
  - On main the same spill loses: `3=spill` gives 0.6191.
- Forcing the original's whole head (shared phi and sharing pointer spilled, curve r9, args r6) makes MBP flip the
  validate exit join (section 3). Relaid, it is 0.57245 (`j_fsp3`).

## 3. Why the original order (pda+hL+fl) collapses: the validate-exit join flips

pda+hL+fl and the full entry fall to 0.47 and 0.43, with L2 0.607. That is not a register cascade. `tools/cc.py`
diffs the candidates against each other. In pda+hL+fl, about 800 instructions move as one block: the join `%bb56.i`
(validate's `Result` exit, `jne r7,2`) and its continuation `%bb89 ...`.
- In main and pda+hL, the join is laid out after the last validate arm (`%bb84.i140`). The original agrees: its
  orig 0x4000-0x5000 aligns with main.
- In pda+hL+fl, the join falls through from the `to_string` error arm (`..ToString..to_string..exit.i`), so the arm
  chain `%bb9.i116 .. %bb93.i` lands behind it.
- The flip is decided after RA, by block placement and branch folding. It is RA- and size-sensitive: RA
  forces on pda+hL can trigger it, and the full-entry RA climb undoes it.

`tools/jfix.py` is a post-RA asm relayout oracle. It uses w14a87's `relay.py`, which handles BPF fallthroughs, to move
the arm chain back in front of the join:
- pda+hL+fl goes from 0.47166 to 0.59240;
- the full entry goes from 0.42759 to 0.51530 (L2 0.79803, rfjR 2,713).

Both stay well below main. The flip explains the collapse, but undoing it does not reach main.

## 4. Head-value lever screen (#3409 class, on pda+hL, ecea702)

Every row keeps `%0` evicted at step 21 by the sharing pointer, except the two quote_locked moves.

| lever | edit | ratio @bytes | `%0` evictor / args reg |
| --- | --- | --- | --- |
| hb | shared arm tests `hopt==Some(true)` | 0.58996 (= pda+hL) | sharing ptr / R9 |
| hbm / hbu | `holder=matches!(hopt,Some(true))` / `hopt.unwrap_or(false)` | 0.55069 @27,336 | - |
| mkl | mint copy after the PDA, seeds `a.mint.key()` | 0.58429 @27,472 | - |
| mkr / mki | `&a.mint.key()` / inline only | compile error (the event uses `mint`) | - |
| hkd / hkt / hkl | `let holder_key=hk.0` / `let (holder_key,_)=` / `holder_key=hk.0` after QL | 0.58936 / 0.53663 / 0.58966 | sharing ptr / R9 |
| sif / smut / sc / bc | shared as if-expr / mut+assign / `&a.sharing_config` / `&a.bonding_curve` | 0.58996 / 0.58898 @27,400 / 0.58996 / 0.58996 | sharing ptr / R9 |
| sai | `a.sharing_config.to_account_info()` binding | 0.43035 @27,976 | - |
| st_* | CtoState field order cxmhbqfe / cmhbqxef | 0.58996 | sharing ptr / R9 |
| **qlA** | quote_locked before the PDA | 0.57121 @27,352 | **phi / R6** |
| **qlB** | quote_locked between the PDA and shared | 0.58162 @27,360 | **phi / R6**, colmap misses 703 -> 516 |
| fl+hb / fl+smut / fl+hbm / fl+mkl | on pda+hL+fl | 0.47166 / 0.47039 / 0.4922 / 0.46618 | J flipped |
| **fl+qlB** | PDA, bools, QL, shared | **0.65226 @27,296** | phi / R6; J not flipped |

Only a quote_locked move changes who occupies the head CSRs. With QL between the PDA and shared, the args copy takes
R6 as in the original. With fl as well (o_PQSF), the `%0` cascade over 0x2800-0x3800 is gone: orig 0x2800/0x3000 exact goes from 123/29 (pda+hL) to 186/155.
The head itself gets worse, though (orig 0x0-0x800 L2 141 against pda+hL's 185), and the build is 104 B short.

## 5. Head-order screen (963d1ee, all 30 orders of S=shared, P=PDA, Q=quote_locked, F=bool locals)

`o_<order>` genes in `e/genes.py`. Main is 0.67226. The only order that ties main's tokens is `o_SPQ` (main with hL,
0.67046). The rest, in ratio order:

| order | ratio | bytes | | order | ratio | bytes |
| --- | ---: | ---: | --- | --- | ---: | ---: |
| PQSF | 0.65256 | 27,296 | | PQS | 0.58372 | 27,360 |
| SPQF | 0.64893 | 27,224 | | FQPS | 0.58076 | 27,384 |
| QPSF | 0.63294 | 27,280 | | QPS | 0.57301 | 27,352 |
| SPFQ (= fl) | 0.63148 | 27,352 | | QSFP / QSP / QSPF | 0.565 / 0.561 / 0.561 | 27,192-27,256 |
| SQP | 0.63071 | 27,240 | | PQFS / QPFS / QFPS | 0.558 / 0.548 / 0.540 | 27,328-27,360 |
| SQFP | 0.62896 | 27,312 | | PSQF | 0.54554 | 27,400 |
| FQSP | 0.61605 | 27,312 | | FSPQ / SFPQ / QFSP | 0.490 / 0.487 / 0.486 | 27,512-27,552 |
| SFQP | 0.59976 | 27,400 | | PFSQ / FPSQ / FSQP | 0.484 / 0.484 / 0.479 | 27,448-27,664 |
| PFQS | 0.58621 | 27,352 | | **PSFQ (original)** / SQPF | 0.47346 / 0.47203 | 27,488 / 27,344 |
| PSQ (= pda+hL) | 0.58538 | 27,400 | | | | |

No order beats main. SPQF (-176 B, -57 M) is not a size knob worth pairing.

## Tools (`tools/`, experiment only; private-llc tools need `llc-patch/build.sh` from w14a84)

- `head.py <m.ll> <tag> [--force F]`: head RA summary. It reports:
  - who evicts `%0` from R8, and at which greedy step;
  - the final register of each head value (named from the pre-greedy MIR);
  - colmap misses, plain/regonly/L1/L2, and per-0x800 L0/L1/L2 from `reg8.py`.

  `hsum.sh name...` prints one line per rx build.
- `reg8.py fn.bin...`: matched orig instructions per 0x800 orig region at L0, L1 and L2 (global alignment).
- `cc.py a.bin b.bin`: candidate-vs-candidate L2 diff. It finds whole-region block moves such as the J flip.
- `where.py fn.bin lo hi`: local alignment of an orig slice against the whole candidate.
- `jfix.py <m.ll> <tag>`: post-RA relayout oracle for the validate-exit join (section 3). With `RAPRIO_FORCE` set, it
  uses the private llc. It needs w14a87's `relay.py`, `fbound.py`, `sc.py` and `oracle.py` next to it, plus
  `asm2bin.sh`.
- `batch.sh g1+g2 ...`: 2-wide capvar + rx runner over `e/genes.py`. Pass the names word-split: the tool shell is zsh,
  where `$L` does not split.
- `screen.py` / `cclimb.sh`: w14a84's tools with `SCREEN_BASE_FORCE`, so a climb can run on top of a base force set.
- `e/genes.py`: every edit set above, including the `o_*` head orders.

## Next ideas

- The original's head colouring needs the `shared` phi and the sharing pointer to lose their CSRs. Under PDA-first
  they win because the curve pointer is live across the chain (hL). A source form that reloads the curve after the
  chain, as the original does (`ldxdw r9,[r8+0x38]` at orig 0x268), without moving the creator operand would remove
  the step-21 eviction. No spelling in section 4 does that.
- o_PQSF is the only PDA-first base whose tail RA survives. Its RA climb is 0.66977 @27,336 against main 0.67076.
  Any future lever that lifts main's tail RA should be re-priced on o_PQSF too, not on pda+hL.
- The full original entry is +92 M over main under rfjR. Its loss is jump distance, so code size between branches and
  targets: it is 184 B over the original. A size-knob search that cuts bytes inside validate and the sweep, not at the
  tail, is the only route to make that base competitive. That needs the J flip fixed in source first.
