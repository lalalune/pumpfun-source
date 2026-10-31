# w15a16-cto-mpermrank: Mperm re-ranking of the archived and wave-15 admin_cto leads (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. Base: main
86e2a6b74 (0.67376, 3,124 slots, M 2,249), taken from `$BASE`. Continues w15a08-cto-holderflagjoint (#3653), next idea 1.
Ledger: approach `mpermrank`, keys `0x22a10-w15-86e2a6b-mpermrank-<variant>-v1` (written by `tools/scr.py`).

**Result: notes only, no landable change.** The re-ranking finds one new code-shape lead that M-based screens could not
see, the **cashback-early + t1n basin** (section 2). At 27,400 B it is +14 to +19 Mperm and +12 frame-masked true LCS over
main, but its real M is 2,228 to 2,234 (−15 to −21), because it rotates 12 spill colours in `-2264..-2360`. Putting main's
colours back in that window is worth M 2,266 (+17, ratio about 0.6788). That relabel is legal, but no source lever for it was
found in 75 frame-repair variants on L, plus 66 basin and filler variants (sections 2 and 3).

## 0. Measures (`tools/mp.py`, about 5 s per module, no build slot)

For a slimmed post-opt module (`m.ll`), `mp.py` runs llc for the object and for `-stop-after=prologepilog` (the spill slots)
and reports the following.

- **M**: difflib masked tokens, the measure.sh metric.
- **Mperm**: w15a08's best permutation of the build's own 8 B spill offsets. Every such permutation is a legal recolouring.
- **Mhc**: a vote-suggested pairwise-swap climb on top of Mperm.
- **lcs**: true LCS (w14a128 bit-parallel), unmasked.
- **lcs_hc**: true LCS of the Mhc-relabelled code.
- **lcs_f**: frame-masked true LCS, which does not depend on the frame at all.

Main: M 2,249, Mperm 2,293, Mhc 2,300, lcs 2,255, lcs_f 2,488. On 90300f9 the same measures are 2,248 / 2,292 / 2,299 / 2,253 / 2,484.

- `tools/batch.sh <lane>/rx <prefix> <out.jsonl>`: scores every stable `rx/*/m.ll` of another lane, read-only.
- `tools/rank.py`: ranks the scored rows. It takes each row's base from the lane's `res-86e2a6b.jsonl` or from the `m.ll`
  mtime.
- `tools/scr.py`: w15a03's capraw+rx screen with `mp.py` appended. `tools/genes_mp.py` is the stitch15 library (w15a03)
  plus `fru*`, `devol`, `l2l_*`, `mv_i_j`, `ord_<perm>` and `s_tai2`.

## 1. Re-ranked table (`data/mperm-rank-swarm.txt`, 987 rows; `data/arch-mperm.jsonl`; `data/own-86e2a6b.txt`)

The table covers every `m.ll` in the rx dirs of w15a01, w15a02, w15a03, w15a04, w15a05, w15a06, w15a11, w15a12, w15a13,
w15a14 and w15a17, plus the archived rx dirs of w14a87, w14a114, w14a119, w14a134 and w14a144, plus this lane's own
screens. Columns are dMhc, dMperm, dM, dLCShc, dLCSf and dB against that row's own main.

Single leads named in the angle, rebuilt on 86e2a6b (the angle named b8586325a; `programs/pump/src` is unchanged since 86e2a6b):

| lead | dB | dM | dMperm | dMhc | dLCSf | note |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| t1n (`if new.is_none()`; w14a140 I6n+t1n family) | −24 | −1 | **+3** | +3 | +1 | the only single with Mperm above 2,295 |
| t3n | −24 | −1 | +3 | +3 | | |
| I6n | +16 | −1 | −1 | −1 | −1 | |
| I6n + t1n | −32 | −3 | +1 | +1 | 0 | |
| m_crl2 (crl2/crl3 tie, w14a138) | +72 | +1 | +1 | +1 | +1 | m_crl3: same at +72 |
| t1n + m_crl2 | +48 | 0 | +4 | +4 | +2 | additive |
| vol334_back | −8 | −1 | −1 | −1 | | |
| vol334_back + I6n | +8 | 0 | 0 | 0 | | neutral +8 with no 334 volatile |
| devol (w15a01: both read_volatile removed) | −8 | −1 | −1 | −1 | | |
| e0u / e0h (w14a142) | +8 / +32 | −4 / −225 | −3 / −21 | | | e0h's −225 is mostly frame (Mperm −21) |
| fru1 (w14a133 TCF struct update) | 0 | −9 | −12 | −11 | | a real code-shape loss, not frame noise |
| fru2..fru9 (`..*x` on literals 2-9) | 0 | 0 / −1 / −2 / −17 | | | | fru2, 3, 4, 8, 9 are eq_main: `..*x` is an equivalent spelling |
| s1 (w15a06) | −24 | −103 | −90 | −60 | −34 | |
| canon/H/S/P bases (w14a87) | −48..+8 | −6..−324 | −3..−257 | | | none above its base |
| h289 head family (w14a134) | 0 | −14 | −14 | −14 | −16 | route C IR moves were not in the cache |
| w14a114 IR-scan d1/d4/tp08 | +16/+24 | −77..−187 | −33..−50 | | | |
| s_tai2 (w15a17: TCF `program` as `to_account_info()`) | 0 | −6 | **+5** | +5 | | frame noise hides +5 |
| mv_5_0 / mv_5_1 (w15a01: cashback before creator in CtoState) | −8 | −28 | 0 | +2 | 0 | pure colour rotation, no code change on its own |

C0 (w14a72), crl_L (w14a80/w14a108), I6 and t1 no longer apply: their source is on main in another form.
Route C, bb14@bb2 and TCF rent_epoch-late are post-opt IR moves with no source spelling (w14a134, w14a112, w14a133), so
they were not rebuilt. P1, pl5/pl7 and B+Br+t1 have no `m.ll` left in any cache.

## 2. New lead: the cashback-early + t1n basin (super-additive; all at 86e2a6b)

| variant | genes | bytes | M | Mperm | Mhc | lcs_f | slots |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| main | | 27,400 | 2,249 | 2,293 | 2,300 | 2,488 | 3,124 |
| mv51_t1n | mv_5_1 + t1n | 27,336 | 2,234 | 2,307 | 2,316 | | |
| **L** | mv_5_1 + t1n + m_crl2 + devol | **27,400** | 2,234 | **2,307** | **2,316** | **2,500** | **3,075** |
| L_vol | mv_5_1 + t1n + m_crl2 + vol334_back | 27,400 | 2,234 | 2,307 | 2,316 | | 3,075 |
| **L_tai2** | L + s_tai2 | 27,400 | 2,228 | **2,312** | **2,321** | | 3,085 |
| mv51_crl2 | mv_5_1 + m_crl2 (no t1n) | 27,464 | 2,222 | 2,294 | 2,303 | | |

- The basin needs exactly cashback before creator plus t1n (or t3n). Both cashback positions 0 and 1 work. All 46 other
  single-field moves of the CtoState literal on top of t1n+m_crl2+devol give +40/+48 B and M −1/−2, the plain t1n+crl2 price
  (`spec5`).
- `mv_5_1 + t1n` is **−64 B**, not −32: cashback-early removes 40 B more once t1n is present. m_crl2 (+72) plus devol (−8)
  is the only faithful filler found that keeps the basin (`spec10`: 18 fillers; every other one costs 3 to 87 more M).
- The code gain (+12 lcs_f) is in orig 0x000-0x800, the entry and validate head. It is register assignment and load
  placement of the CtoState fields: entry `mov r6,r1` instead of a spill, `ldxb [r9+0xa3]` (cashback) hoisted, and 8 fewer
  instructions near 0x478. L's entry already begins `mov r9,r5`, `stxdw [-0x920],r4`, `mov r6,r1`.
- **The frame.** cashback-early rotates the colours of 12 spill slots in `-2264..-2360`: four 2/3-cycles. They hold the
  sharing tag (`-2272`), the accounts pointer (`-2264`) and their neighbours. The cause is a rank change among the 4-6
  heaviest spill intervals, the entry arg spills (weights 2.00-2.07, `-debug-only=stack-slot-coloring`); the near-ties
  reorder. The same rotation costs mv_5_1 alone −28 M. Relabelling just those 12 slots back to main's offsets is a
  bijection:
  - L: M **2,266** (+17 over main);
  - L_tai2: M 2,260 with the window only, and 2,271 when all 19 moved slots are restored (not a bijection, so an upper
    estimate).

## 3. Frame-repair screens on L (all 27,400 B unless noted; none moves the window)

- `spec7` (19): L + 0 B near-neutral knobs (cu_replace, K_g_old_fee_first, K_g_s7_destrev, m_k_ql, m_k_dest2, en_feesl,
  cs_old_fee_first, K_sh_fees_key, evo_*, K_g_canedit_first, I6sn, I6ssn, t3n, crl3, vol334_back) give M 2,232-2,234 and
  Mperm 2,305-2,307. The window rotation is unchanged in all of them.
- `spec8` (31): every CtoState literal order with cashback at position 0 or 1 plus one more move gives M 2,234 in 17 of
  them, with the same frame. The rest are worse or change size.
- `spec11` (16): polarity and wallet knobs. p_cb, p_shared, p_skip, p_pool, p_docoin, p_coinpres, p_elseif2,
  wl_exec_ne, wl_frozen_let, en_ownd, cd_holder_dest, K_rent_checked and K_ev_ts_map give M 2,234 with the same frame.
  p_colnat, p_feecfg and p_dc_empty add +8 B at a cost.
- `spec12` (9): entry-argument use spellings. c_sk and c_hk give 2,234. t1a (`args.0.is_none()`) is +8 B at 2,235 /
  Mperm 2,308. q_swap gives 2,227, hkmut 2,221, sunew 1,905 and c_new 1,494; c_hold does not compile.

- `spec13` (6): other spellings of the t1n holder test in the basin. `new==None`, `!new.is_some()`, `args.0==None`
  and `matches!(new,None)` give exactly L (2,234 / 2,307). `hopt.unwrap_or(false)` keeps the basin's code shape
  (Mperm 2,307) at +32 B, so the basin does not depend on reading `new`. `hopt==Some(true)` falls out of it (+56 B, 2,222).
- `spec14` (3): reading cashback earlier, into a local before `quote_locked`, the mint key or the accounts binding,
  with the literal order unchanged. These give −79 to −291 M. Cashback has to be read inside the literal.

Every row of this lane's own screens is in `data/own-86e2a6b.txt` (197 variants).

**L confirmed by a real build.** measure.sh on L gives 1,034/1,034 normalized and raw, no losses or gains, swap_hop
matched, and admin_cto 0.66926 / 3,075 slots at 27,400 B, equal to the oracle. `pump_admin_cto_differential.py` passes
388 cases with 0 mismatches. L contains **no `read_volatile`**: devol removes both placeholders. Neither fact makes it
landable, because its ratio is below main's.

## Next ideas

1. Find a source lever for the heavy-spill rank order at entry. The 4-6 arg spill intervals (defs 32r-88r and 2856r-3304r)
   have weights within 3% of each other. In L, the cashback-early order lifts the `48r` arg (r3/r4) above the `2856r`
   value. Candidates to try: one more or one fewer use of a single entry argument, such as `fee`/`new` read once versus
   through `args.0`, `holder` passed as `hopt` versus `holder`, or `ctx.accounts` bound once versus re-read. Score each on
   L with `mp.py` and the window-relabel check in section 2.
2. A stitcher should take L (or L_tai2), not main, as its base for Mperm-ranked pairs. Every main-based single that is
   M-neutral on main stays M-neutral on L (`spec7`), so pairs must target the window, not code shape.
3. The fru family shows that `..*x` struct update is an exact equivalent of five of the nine CPI AccountInfo literals.
   That is a free respelling if a future lane needs a different literal form at the same bytes.
