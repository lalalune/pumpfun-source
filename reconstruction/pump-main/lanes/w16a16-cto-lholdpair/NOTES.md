# w16a16-cto-lholdpair: a source lever for the L-basin holder-piece force pair (admin_cto 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 599891304 (admin_cto.rs as on 1f4e396b5): 0.67436, M 2,251, 3,141 slots (capture `m0`: 0.67436, `eq_main: true`).
L_vol = `mv_5_1+t1n+m_crl2+vol334_back` (cashback before creator in the CtoState literal, `if new.is_none()` in the shared
arm, `let cr=` creator binding, only the line-334 read_volatile dropped): 0.66986, M 2,236, Mperm 2,309, Mhc 2,318, 3,091
slots at 27,400 B (`rx/Lv`, the w16a11 capture). Continues w16a04-cto-lanchorceil next idea 1 (#3855, section 4) and
w15a32-cto-lbasinweight next idea 2 (#3823). Ledger: approach `lholdpair`, keys `0x22a10-w16-5998913-lholdpair-*-v1`.

**Result: notes only, kill test met.** No ordinary source form reproduces the pair. The pair is decided by
two independent facts: (1) list-ilp's critical-path window places L's `!holder && cashback` select before the max_fee /
holder_enabled / mayhem / holder_reward loads, and that early select IS L's 40 B and Mperm lead; (2) in the resulting bb12
the max_fee piece evicts the cheapest of four near-tied pieces (holder 2.157e-3 < new tag 2.269e-3 < new pointer 2.378e-3 <
fee_configurable 2.902e-3), and only the third or fourth choice gives the +28 M. 36 ordinary-source forms (raw-IR captures)
and 148 + 10 IR edits on L_vol's post-opt module show neither the unforced marker nor M above main's 2,251 at a repayable
size. Main stays the best zero-loss measurement (0.67436 / 3,141 slots / 27,400 B).

## 1. The pair on 599891304 (step 1)

On L_vol the vreg ids are one higher than on w16a04's L (devol): the holder argument is `%385` (r3, entry `COPY $r3` at 48r),
its local piece over bb8 .. validate head is **1704** (size 712, w 2.157e-3), and the max_fee bb12 piece (split of `%10`,
`ldxdw [global+1072]`) is **2096** (size 420, w 2.925e-3). `tools/fx.py` (RAPRIO sticky llc, no SSC hook) and `tools/ire.py`
(same llc plus `-debug-only=stack-slot-coloring`, prints the holder-arg spill weight and rank):

| forces on L_vol | ratio @ bytes | M | rot | holder arg SS#184 weight (rank) |
| --- | --- | ---: | ---: | --- |
| none | 0.66986 @27,400 | 2,236 | 11 | 2.379 (0, takes c0 = -2264) |
| `1704=r5,2096=r6` | **0.67835 @27,392** | 2,264 | 6 | 2.004 (2); cashback byte SS#317 1.378 |
| `1704=r5,2096=r6,2175=r0` | 0.67855 @27,400 | 2,265 | 6 | 2.004 |
| `1704=r5,2096=r0` | 0.67805 @27,416 | 2,264 | 6 | 2.004 |
| `1704=r5,2096=r7` | 0.67086 @27,392 | 2,239 | 10 | 2.004, but the `new` pointer goes to 2.383 |
| `1704=r5` / `2096=r6` | 0.67086 @27,392 / 0.66946 @27,384 | 2,239 / 2,234 | 10 / 10 | |

Eviction at `selectOrSplit %2096` (`llc -debug-only=regalloc` replay, `tools/dbgocc.py`): every register is taken in bb12.
Evictable candidates, cheapest first: r5 **1704** holder piece 2.157e-3 < r7 **2034** `new` tag-byte piece (split of `%15`)
2.269e-3 < r6 **1954** `new` pointer piece 2.378e-3 < r0 **2065** fee_configurable piece 2.902e-3 (r1, r2, r3, r4, r8, r9
hold intervals heavier than 2096 or INF). Greedy evicts the cheapest, 1704. The pair works only when 2096 lands on r6 or r0;
landing on r7 (the next-cheapest) moves the double reload onto the `new` pointer and keeps the rotation. **So a pure weight
lever must make the `new` pointer piece 1954 the cheapest (about 62 slot units, 4 instructions, longer), or lift both 1704
and 2034 above it.** One weight fact is not enough.

## 2. Why the cashback select lands before the max_fee loads (new mechanism)

`llc -debug-only=pre-RA-sched` on IR block bb11 (`data/dagdepth-bb11.txt`):

- BPF has no setcc, so `cashback=!holder&&st.cashback` becomes two `Select_Ri` pseudos and an `AND_rr`; the custom inserter
  splits the machine block at the selects, so whatever list-ilp schedules after them lands in bb12.
- In L_vol the cashback load is before the creator memcpy, so it is chained only to `lifetime.start(st)` (depth 2). The
  `AND_rr` has **depth 4**; the sk1-copy stores at the bottom of the block have depth 12. list-ilp's critical-path rule
  (`MaxReorderWindow` = 6) defers the shallower node while the spread exceeds 6, so `AND_rr` is scheduled at bottom-up step
  41 instead of 20. The two selects then carry height 42 against the quote_locked store's 34 and lose the height rule; the
  loads' TokenFactor is scheduled, and the max_fee / holder_enabled / mayhem / holder_reward loads (RegPressureDiff 0 / -1)
  beat the selects (+1 / +2). Program order: memcpy, selects, then the four loads in bb12.
- In main the cashback load is chained after the memcpy TokenFactor: `AND_rr` depth 7 (spread 5), scheduled at step 20, the
  selects at 42-43 before the loads are free, so the loads stay in bb8 and max_fee takes r6 there.
- Oracle `llc -max-sched-reorder=8` (whole function): L_vol's holder is fixed (2.004) but the code grows to 27,440 B with M
  2,213 (main under the same flag: 2,232). **L's -40 B and its Mperm lead ARE the early select**: any change that puts the
  selects back after the loads (w15a32 E1, this flag, deeper select operands) gives the 40 B back. So the schedule is not
  the lever; only the RA eviction choice in bb12 is.

## 3. IR oracle on L_vol's post-opt module (step 2; `tools/ire.py`, `tools/bbscan.py`, edits in `e/`)

| edit | M | bytes | rot | holder weight (rank) |
| --- | ---: | ---: | ---: | --- |
| (b) split bb11 before the select / after it / before max_fee (`b1`-`b3`) | 2,236 | 27,400 | 11 | identical to L_vol: CGP merges the split |
| (c) cashback select as a branch diamond, holder first / cashback first (`c1`/`c2`) | 1,992 / 1,990 | 27,368 / 27,392 | 10 / 7 | 2.004 (2) |
| (a) select reads st.cashback back after the stores (`a1`) | 2,236 | 27,400 | 11 | identical (DAGCombiner forwards the reload) |
| (a) holder test through a stack copy (`a2`, volatile, oracle only) | 1,609 | 27,336 | 5 | 2.004 (2) |
| (d) validate's holder branches test the materialised !holder byte, no bb6.i holder use (`d1`) | 1,682 | 27,376 | 11 | 2.003 (3) |
| (e)/(a) cashback from `new.is_some()` (equal on every Ok path), after the new tag load (`cbn1`/`cbn2`) | 1,620 | 27,424 | 11 | 1.379 (4); accounts 3.425, new 2.383 |
| every legal single move of 11 bb11 units (7 field stores, holder test, cashback and, new tag load, sk1 copy): 148 variants (`data/bbscan_Lv.jsonl`) | best with marker 2,249 (`u13to8`: ql store before the holder_enabled load) | 27,448 | 4 | 2.004 (2) |
| | `u18to14` (new tag load between the ql and he stores) 2,234 | 27,400 | 7 | 2.004 (3) |
| | `u15to5` (fee_cfg store before the max_fee load) 2,247 | 27,376 | 10 | 2.004 (3) |

No IR edit shows the unforced marker with M above 2,251. Every edit that keeps the holder in r5 either undoes the early
select (L's 40 B) or perturbs the global colouring (M 1,600-2,000).

## 4. Ordinary-source screens on L_vol (step 3; raw-IR capture + opt + llc, `tools/genes_lh.py`)

| form (on L_vol) | change | bytes | M | Mperm | Mhc | rot | holder weight (rank) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| main m0 | | 27,400 | 2,251 | 2,295 | 2,302 | 0 | 2.004 (2) |
| L_vol | | 27,400 | 2,236 | 2,309 | 2,318 | 11 | 2.379 (0) |
| Lv_t1a | shared arm `args.0.is_none()` | 27,408 | 2,237 | 2,310 | 2,319 | 11 | 2.379 (0) |
| Lv_hb | `let hopt=holder;let holder=..` before the CtoState literal | 27,400 | 2,236 | 2,309 | 2,318 | 11 | 2.379 (0) |
| Lv_cbl | `let cashback=..` just before validate | 27,400 | 2,236 | 2,309 | 2,318 | 11 | 2.379 (0) |
| Lv_gb | `let g=&a.global;` for the literal's Global reads | 27,400 | 2,236 | 2,309 | 2,318 | 11 | 2.379 (0) |
| Lv_bcb | `let bc=&a.bonding_curve;` for the literal | 27,400 | 2,236 | 2,309 | 2,318 | 11 | 2.379 (0) |
| Lv_gbcb | both bindings | 27,400 | 2,236 | 2,309 | 2,318 | 11 | 2.379 (0) |
| Lv_sth | CtoState built by a plain helper `cto_state(a,quote_locked)` | 27,400 | 2,236 | 2,309 | 2,318 | 11 | 2.379 (0) |
| Lv_sthg | helper taking `(&Global,&BondingCurve,quote_locked)` | 27,400 | 2,236 | 2,309 | 2,318 | 11 | 2.379 (0) |
| Lv_cvsk | validate(.., &a.sharing_config.key()) | 27,400 | 2,236 | 2,309 | 2,318 | 11 | 2.379 (0) |
| Lv_cvhk | validate(.., &hk.0, ..) | 27,400 | 2,236 | 2,309 | 2,318 | 11 | 2.379 (0) |
| Lv_cbif2 | `cashback=if !holder{st.cashback}else{false}` | 27,400 | 2,236 | 2,309 | 2,318 | 11 | 2.379 (0) |
| Lv_evh | event `is_holder_reward` from the holder argument | 27,400 | 2,235 | 2,308 | 2,317 | 11 | 2.384 (0) |
| Lv_g0L | shared arm `target=st.creator` (bc pointer not needed after validate) | 27,384 | 2,235 | 2,308 | 2,317 | 11 | 2.379 (0) |
| Lv_hc2 | `let args=&(new,)` between hopt and holder | 27,376 | 2,234 | 2,311 | 2,318 | 10 | 2.379 (1) |
| Lv_ar1 | `let args` right after the literal | 27,376 | 2,234 | 2,311 | 2,318 | 10 | 2.379 (1) |
| Lv_arsk | `args` and `sk` right after the literal | 27,376 | 2,234 | 2,311 | 2,318 | 10 | 2.379 (1) |
| Lv_xcba | `cashback=st.cashback&&!holder` | 27,408 | 2,230 | 2,303 | 2,312 | 11 | 2.379 (0) |
| Lv_evboth | event cashback flag + holder argument | 27,408 | 2,227 | 2,300 | 2,309 | 12 | 2.384 (0) |
| Lv_hrv | validate line 289 `!holder` instead of `!(hopt==Some(true))` | 27,400 | 2,222 | 2,295 | 2,304 | 11 | 2.379 (0) |
| Lv_evcb | event `is_cashback_coin:cashback` | 27,400 | 2,204 | 2,281 | 2,288 | 11 | 2.379 (0) |
| Lv_h1 | `curve.is_holder_reward=_holder` | 27,424 | 2,201 | 2,278 | 2,287 | 13 | 2.459 (0) |
| Lv_sk2 | `let sk` before `let args` | 27,272 | 2,197 | 2,252 | 2,258 | 10 | 2.004 (1) |
| Lv_sk1 | `let sk` right after the literal | 27,272 | 2,197 | 2,252 | 2,258 | 10 | 2.004 (1) |
| Lv_qlo3 | quote_locked inline in the literal (L order) | 27,336 | 2,081 | 2,177 | 2,185 | 13 | 2.004 (6) |
| Lv_h1evh | h1 + evh | 27,456 | 1,998 | 2,278 | 2,287 | 11 | 2.376 (0) |
| Lv_evhb | event `is_holder_reward:_holder` | 27,456 | 1,997 | 2,277 | 2,286 | 10 | 2.379 (0) |
| Lv_S3n | w16a08 S3n per-arm holder out-param flag (`hf`) on L_vol | 27,416 | 1,988 | 2,301 | 2,308 | 11 | 2.376 (0) |
| Lv_S3ncb2 | S3n + per-arm cashback out-param `cf` (no early !holder) | 27,208 | 1,827 | 2,153 | 2,154 | 12 | 1.376 (3) |
| Lv_sutg | shared arm `sharing_update=Some(Some(target))` | 27,312 | 1,801 | 1,989 | 1,992 | 13 | 2.004 (1) |
| Lv_S3ncb1 | S3n + `*cf=cashback` after validate's cashback | 27,336 | 1,660 | 1,767 | 1,773 | 13 | 1.376 (4) |
| Lv_qlo1 | quote_locked inline, original head read order (cb, hr, mayhem, ql, max_fee, he, fee_cfg, creator) | 27,360 | 1,648 | 1,733 | 1,743 | 11 | 2.379 (1) |
| Lv_qlo4 | quote_locked inline, (cb, hr, mayhem, ql, fee_cfg, creator, max_fee, he) | 27,504 | 1,648 | 1,729 | 1,739 | 10 | 2.379 (1) |
| Lv_qlo2 | quote_locked inline, (cb, hr, mayhem, ql, creator, max_fee, he, fee_cfg) | 27,504 | 1,647 | 1,728 | 1,738 | 10 | 2.379 (1) |
| Lv_xhm | execute `matches!(hopt,Some(true))` | 27,528 | 1,631 | 1,660 | 1,660 | 8 | - |
| Lv_cvar | validate(.., args.0, ..) | 27,936 | 1,485 | 1,525 | 1,525 | 11 | 2.379 (1) |
| Lv_vhm | validate `matches!(hopt,Some(true))` | 27,520 | 1,404 | 1,446 | 1,467 | 9 | 2.375 (1) |

36 forms. None shows the unforced marker (holder kept in r5, at most 6 rotated slots), and none has M above 2,251:
- 9 forms are byte-identical to L_vol (`fn.bin` cmp): hb, cbl, cbif2 (statement order and spelling of hopt/holder/cashback),
  gb, bcb, gbcb (Global/BondingCurve bindings), sth, sthg (the plain constructor helper is inlined) and cvsk. cvhk differs
  in bytes but ties L_vol's M, Mperm and Mhc.
- Forms that remove the second holder reload all lose code: `sk1`/`sk2` (sharing-key copy before `args`) -128 B and M 2,197
  (holder 2.004); `qlo3` 2,081; S3ncb1/S3ncb2 (cashback via validate, no early !holder select) 1,660/1,827 (holder 1.376).
- Forms that move the `new` tag load earlier (`ar1`, `hc2`, `arsk`) make both the holder and the `new` pointer heavy (2.379,
  2.383) at -24 B: the eviction moves, the rotation stays.
- Flags as phis on L_vol: S3n 1,988 (Mperm 2,301) at +16 B, the same spill-numbering blocker w16a08 found on main.

## 5. Reading for other lanes

- The L basin's code gain and its holder eviction have one cause: the early `!holder && cashback` select (list-ilp's
  critical-path window on IR bb11). A lever that only frees a register in bb12 cannot be source-reached without moving
  that select, and moving it gives the 40 B back.
- The RA fact itself needs two weight changes (1954 cheapest, or 1704 and 2034 both above 1954). Slot ranges on L_vol:
  1704 [3160, 3872) (bb8 `and 253` copy to the bb6.i `and -3` copy), 2034 [3616, 3840) (new tag load to the bb12 exit),
  1954 [3668, 3872) (split point after the tag load, across the sk1 copy, to the bb6.i `new+1` copy), 2096 [3408, 3828).
  Instructions added inside the shared tail [3668, 3840) lighten 2034 at least as fast as 1954, so they cannot make 1954
  the cheapest; only about 10 instructions at the head of bb6.i, before `new+1` and the holder test, could (1954 then falls
  below 1704 at k > 153 slot units). Nothing in the original sits there: its holder_key copy (orig 0x598-0x5d0) is before
  the mayhem test, and its faithful form (validate takes `holder_key` by value, b01) costs about 80 B and collapses the
  colouring on main (w15a11 0.536).
- `ire.py`'s holder-weight/rank column is a quick screen for any L-basin variant: rank 0 (weight about 2.38) means the
  double reload and the 11-slot rotation; the pair and main show 2.004 at rank 2.

## Tools (`tools/`, experiment only; paths point at this lane's `$OUT`)

- `fx.py <m.ll> <tag> [FORCE]...`: RAPRIO sticky llc (w15a24 patch, w16a04 copy), M / ratio / slots / bytes / window rotation.
- `ire.py <m.ll> <name> <edits.py|-> [FORCE]`: post-opt IR edit + the same llc with `-debug-only=stack-slot-coloring`; adds
  the holder-arg spill weight (the SS interval that starts at 48r) and its rank. The marker is rank > 0 and rot <= 6.
- `bbscan.py <named m.ll> <out.jsonl> [procs]`: every legal single move of the bb11 units (needs `opt -passes=instnamer`).
- `genes_lh.py`: the screened source genes (on top of `Lv` from w16a11 `genes_pt.py`).
- `dbgocc.py` (w15a33): interference per register at a vreg's `selectOrSplit`.
