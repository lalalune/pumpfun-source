# w14a98-cto-brtarget: the target/fee half of Br, per block (notes only)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 963d1eefb (0.67226, 3,123 slots, M 2,244, jM 2,271). This lane is the companion of w14a97-cto-brhead and
uses w14a87-cto-skelunion2's oracle (#3416). Ledger: approach `brtarget`, keys `0x22a10-w14-963d1ee-brtarget-*`
(41 spelling rows and 6 analysis rows).

**Result: no landable change. The best zero-loss measurement is still main (0.67226 @ 27,400).** The target half of Br
cannot be separated from the head half. Its value shows up only with main's register assignment, and the 41 source
spellings of lines 298-338 are all either identical to main or worse.

## 0. Fix for the shared oracle: `B` misaliases on 963d1ee (affects brhead too)

`relayn.run(..,'B')` with a87's `Bspec.txt` gives only **M 2,258** on 963d1ee (Br 2,258 @ 27,416). The spec's `bb94.i`
still exists on 963d1ee, but now it names a block at the function tail (LBB0_79). The block that follows `bb44.i` was
renumbered to `bb95.i`, so the relayout pulls the tail block into validate. `Bspec963.txt` holds the renumbered names
(`bb95.i`, `bb3.i30.i`, `exit31.i`, `bb3.i37.i`, `bb3.i58.i`, `exit59.i`, `bb3.i292`, `exit38.i`, `bb3.i23.i`,
`exit24.i`, `exit293`, `bb3.i51.i`). With it, B is **2,272 @ 27,440** and Br is **2,272 @ 27,408** (+28 M, 4 flips),
the same gain a87 measured on 95a64ba.

For variants, the name aliasing is also unreliable: eq_main variants came out at 2,051-2,270. `tools/sub.py
border2/resolve_content` maps the spec blocks to the variant's asm by instruction content (labels masked) and falls
back to IR names only when that fails. With it, every eq_main variant gets exactly 2,272 @ 27,408.

## 1. Per-unit prices at fixed RA (main 963d1ee, `tools/units.py`, `tools/usub.py`, `tbl_units_963d1ee.txt`)

Units are B's contiguous groups, each an error's test, to_string or alloc-fail, or Err exit. For each unit:
- **alone** moves that unit to its B predecessor;
- **LOO** (leave-one-out) moves it back to its main predecessor in B;
- **subsets** apply the B moves of a subset in B order.

Flips are allowed in every case.

| subset | M | bytes |
| --- | ---: | ---: |
| main | 2,244 | 27,400 |
| B (all 17 units) | **2,272** | 27,408 |
| task "target" list (bb23 bb27 exit31 bb79 exit59 bb44/95 bb48 bb28/37/38 exit38 exit293 bb39) | 2,215 | 27,408 |
| task "head" list (bb10 bb14 bb16 bb22 bb17 exit24) | 2,213 | 27,408 |
| exit38.i only (Err306 exit after bb38.i) | **2,258** | 27,408 |
| exit38.i + bb23.i flip | 2,259 | 27,416 |

- **The halves are not separable.** Each half alone loses about 30 M, and only the union gains +28.
- Greedy forward selection: exit38.i gives +14 (jM only +3, so the gain is jump distance), then bb23.i +1. Every
  further target unit adds 0 or loses until the head units (bb17.i, bb10.i) join, and then the total jumps to +28.
- Leave-one-out from B, in M: bb28/37/38 chain -27, bb27.i -13, exit38.i -15, bb39.i -5, bb44/95 -3. bb23.i, bb48.i,
  exit293 and bb79.i cost 0.
  - The head and exit units cost more: exit31.i -58, exit59.i -25, exit24.i -23, bb17.i -20, bb10.i -19.

## 2. The B moves are not source-reachable without moving RA

BPF's MachineBlockPlacement runs **after** register allocation. RA sees the pre-RA block order (= post-opt IR order) and
the block frequencies (= branch probabilities). Every source lever that moves placement changes one of these two.
Br's +28 is a placement change with main's RA held fixed.

- **IR order** (`tools/irord.py`: reorder the post-opt IR, real llc). Moving cold Err exits anywhere in the IR gives
  byte-identical output, because MBP places them again. Moving a block on the main path changes RA:
  - `bb38.i` next to `exit38.i` gives -107 M;
  - the full B order in the IR gives 2,115 @ 27,392 (-129).
  - Err306 after bb38.i, the +14 unit, is not MBP-legal at all. bb38.i ends in a conditional branch, so it is glued to
    its IR successor bb39.i (BPF `analyzeBranch`, see w14a78 §2). The relayout oracle pays a `ja` for it.
- **Branch weights** (`irord.py --prof`, post-opt `!prof`, real llc):

| weights | M | bytes | jM | fM | errseq |
| --- | ---: | ---: | ---: | ---: | --- |
| main | 2,244 | 27,400 | 2,271 | 2,376 | 298 289 296 326 306 312 307 |
| bb23.i (306 tag) 1:1 | 2,216 | 27,408 | 2,267 | 2,373 | |
| bb23.i 1:4 / 4:1 | 2,232 / 2,213 | 27,392 / 27,424 | | | |
| bb7.i + bb14.i (holder) 1:1 | 2,051 | 27,424 | 2,193 | 2,311 | |
| bb7.i + bb14.i + bb23.i 1:1 (= and-1 union) | 2,230 | 27,424 | **2,350** | **2,437** | **289 298 306 296 326 312 307** (original) |
| ... + bb45.i 20:12 (greedy best) | 2,245 | 27,432 | 2,363 | 2,444 | original |
| greedy from main, 15 validate branches x 6 weights | 2,245 (bb37.i 20:12) | 27,400 | | | |

- The and-1 union gets the original layout almost exactly: `bb10 bb14 bb23 bb27 exit31 bb16 ... bb22 bb79 exit59 bb44
  bb95 bb48 bb28 bb37 bb38 bb39 exit38 exit24 exit293`. Only ts296 and ts312 differ from B.
  - But it loses 14 M to RA.
  - Legal-frame bound (a87 `fbound.py`): fR 2,243 against main's 2,290, rfR 2,614 against 2,622. B with main's RA has
    fR 2,328 and rfR 2,662.
  - Relaying B on top of the union gives 2,256: the RA loss stays.
- The target half's own weight (bb23.i 1:1) is -28 alone and +179 on top of the head weights. **brtarget and brhead
  have to land as one change.**

## 3. Source screen of lines 298-338 (`v/gen.py`, `tbl_spellings_963d1ee.txt`)

Raw-IR capture (`--emit=llvm-ir`, w14a73 `capraw2.py`), then opt -O3, then llc. The main capture is `eq_main: true`. Columns:
- **M** is the plain result;
- **Br** is the content-mapped Br on top;
- **hw** adds the head weights bb7/bb14 at 1:1;
- **hw23** adds bb23 at 1:1 as well.

The rows for main itself: M 2,244 @ 27,400; Br 2,272 @ 27,408; hw 2,051; hw23 2,230 @ 27,424.

| spelling family | variants | result |
| --- | --- | --- |
| 306: `match` Some/None-first, `_` arm, `if let None`, `&new`, `is_none()`/`is_some()`+unwrap in if/else, `(is_some(),new)` match | mS mN mW ifN ref isne iss tp | **identical to main** |
| 306: let-else, `if new.is_none(){..}let t=new.unwrap();` | le306 isn306 | 2,229 @ 27,400 (-15). The only change is the frame slots of ts306. hw23 2,234 (+4 over main+hw23) |
| 306: `ok_or_else(..)?` | oke306 | 2,102 @ 27,304 |
| 306 via a bool: CtoState `has_new` field, `has:bool` param, `(st.has_new,new)` match | hs1 hs1n hs1m hp1 | 1,547-1,908. The unwrap_or_default/select forms collapse |
| 298: `if let Some(_)`, `!is_none()`, `!=None`, `match` | ifl ne nn m298 | identical |
| 307: `Pubkey::default()==t` | sw307 | 2,242 |
| 312: `\|\|` operands swapped, reversed compares | sw312 rv312 | 2,237 / 2,241 |
| 312: two ifs, `[..].contains` | sp312 ct312 | 1,885 / 1,658 |
| 312: success-first `t!=a&&t!=b{t}else{err}` (original fallthrough polarity) | nd312 (+fNf, +le306, +t1, operands swapped) | 2,130-2,138. 330/338 come forward (errseq 298 289 330 296 326 338 306 312); Br 2,189-2,228 |
| cashback: `!holder&&st.cashback`, `if !holder`, `cashback==true` | cb314a cb314c cb330 | identical |
| cashback: `st.cashback&&!holder` | cb314b | 2,081 |
| fee: `None` arm first | fNf | identical |
| fee: `if let`, let-else early return | fil fle | 2,157 / 1,768 |
| fee bps: `f>max\|\|f==0`, `!(1..=max).contains`, `f<1\|\|..` | f338a-c | identical |
| t1 (w14a89, execute tree `new.is_none()`) | t1 | 2,243 @ **27,376** (ratio 0.67226, -24 B). Br 2,269 @ 27,384; hw23 2,229 @ 27,400 |

The single-site lattice of this region is flat on 963d1ee, as autospell (#3413) found on 0d04cf4. The only free asset
is t1's 24 B of room.

## 4. Original structure of the target arm (for the next lane)

In the original (orig 0x23618-0x23950), the t-tests fall through on success. The 312 memcmp to holder_key is
`jeq r0,0 -> err`, followed by the success path. The success path then does the `shared` test ([r10-0x920]) and the fee
tag test ([r10-0x928]) inside the non-holder arm before the Err306 exit block (0x23870, `stw 0x132`). That is the OV
form (w14a89 §1). Err306 sits after the whole non-holder target/shared/fee-tag region, not between bb38.i and ts312.

So the faithful target half is OV plus a success-fallthrough at 312 (nd312). Both are known RA cascades:
- OV is 0.44 (w14a89);
- nd312 is -107 M here.

Br's cheap `+14 for Err306 after bb38.i` reaches the original only through jump distances. The structure behind it is
that region.

## 5. Fixed-RA MBP oracle: the legal ceiling of placement levers (`tools/mirprob.py`, `tools/mgreedy.py`)

`llc -stop-before=block-placement` writes the post-RA MIR. `mirprob.py` edits the successor probabilities and runs
`llc -start-before=block-placement`. The round trip reproduces main exactly. This holds main's RA fixed and lets
MachineBlockPlacement choose any layout it can legally reach. It is the ceiling for any lever that only moves
placement.

| MIR probabilities (main RA) | M | bytes | jM |
| --- | ---: | ---: | ---: |
| none (main) | 2,244 | 27,400 | 2,271 |
| bb23.i 1:1 | 2,215 | 27,408 | 2,267 |
| bb7.i + bb14.i 1:1 | 2,202 | 27,416 | 2,333 |
| bb7.i + bb14.i + bb23.i 1:1 | 2,247 | 27,424 | 2,362 |
| + bb27.i 1:1 (greedy best) | **2,248** | 27,424 | 2,362 |
| greedy from main, 22 validate branches x 6 weights, any size or ≤ 27,400 | 2,244 | 27,400 | no single change helps |

- The MBP-legal ceiling is **+4 M at +24 B**, not Br's +28. Most of Br breaks BPF fallthrough glue, which only an IR
  order change can do.
- The same weights at real RA give 2,230 (the RA costs 17).

## 6. Cold error groups in IR order (`tools/coldscan.py`, `tools/cold2.py`, `coldscan_963d1ee.jsonl`, `cold2_963d1ee.jsonl`)

`coldscan.py` moves the 14 cold groups (to_string plus alloc-fail pairs, and the Err exits) to every position in
validate's post-opt IR, with real llc. Such a move keeps fM and skM equal to main's (RA-neutral) unless it lands
between hot blocks.

- 623 singles give 44 distinct outputs, **none above M 2,244**.
- The structural best is ts296 after bb10.i: 2,242 @ 27,400 with jM 2,351 (+80). It is w14a78's lead.
- 478 pairs (top 12 by jM x top 45): none above main. The best is 289 glue + ts296 at 2,242 @ 27,392 (ratio 0.67176).
- The 306 glue flip (cold bb27.i right after bb23.i) gives 2,239.

## Next ideas (untried)

1. Price brhead and brtarget as one change. The and-1 union is the source form (e3 holder bool param + a range-free 306
   tag). It needs an RA/frame plan worth ≥ +15 M at 27,424-24 (t1) B. Under the legal-frame bound it is 47 below main,
   so nothing in hand is close.
2. t1's -24 B is ratio-neutral room on 963d1ee. A +24 B M-positive change elsewhere would land with it. No catalog knob
   does that (w14a89).

## Tools (`tools/`, experiment only)

They run from a copy in `$OUT/tools`, with `Bspec963.txt` in `$OUT/tmp/` and a87's `relayn.py`, `relay.py`, `sc.py`,
`fbound.py`, `oracle.py`, `rx.py` and `capvar.sh` next to them.
- `sub.py`: B order (`border`), content-mapped B for variants (`border2`), emit with selective flips, and `fixmix`.
- `units.py` / `usub.py` / `units_def.py`: per-unit alone, LOO and subset prices.
- `mvscan.py`: a single-unit position scan at fixed RA, which also reports MBP legality.
- `irord.py`: post-opt IR block reorder (`a,b,c` or `mv:X@Y`) and `--prof blk=T:F,...` branch weights, then real llc
  and the score. Run `opt -passes=instnamer` on m.ll first.
- `wgreedy.py` / `wgreedy2.py`: greedy branch-weight search over validate's branches.
- `post1.py`, `hw.py`, `runq.sh`, `repost.sh`: the variant pipeline (capture, Br, head weights, errseq).
- `mirprob.py` / `mgreedy.py`: the fixed-RA MBP oracle and its weight search.
- `coldscan.py` / `cold2.py`: the cold error-group IR position scans.
