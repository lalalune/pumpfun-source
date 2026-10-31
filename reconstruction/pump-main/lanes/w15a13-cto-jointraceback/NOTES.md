# w15a13-cto-jointraceback: the validate-exit join and sweep head, run by run (notes only)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
The first screen (27 trials) ran on main ed47ac7 (0.67346, 3,124 slots). Main then moved to 86e2a6b (#3666, 0.67376,
3,124 slots, M 2,249), and every later screen ran there. 9120883 has the same admin_cto.
Ledger: approach `jointrb`, keys `0x22a10-w15-ed47ac7-jointrb-*-v1` and `0x22a10-w15-86e2a6b-jointrb-*-v1`.
About 255 source trials and 13 post-opt IR trials. A few `-v1` keys (`q3`, `q5`, `q1p`, `q4p`) have an extra
compile-failed row from a queue glitch (missing `e/` file). The later row is the real measurement.

**Result: no landable change.** The best zero-loss measurement is main: 0.67376, 3,124 slots, 27,400 B.

- Every source spelling of the join tree, the Ok hop, the wallet gate and the creator override does one of three things:
  - it gives main's bytes;
  - it costs 1-5 M, or saves bytes that no size knob can repay;
  - it falls into one of two collapse basins: A (27,448 B, M ~1,711) or B (27,440 B, M ~1,777).
- The one structural lead in the region is the skip polarity of the sweep gate. That is the original's `[r10-0x8e0]`
  flag: spilled at the join, reloaded at the gate, `jne -> post`, falling through into the sweep.
  - Every skip-polarity spelling compiles to byte-identical basin-B code.
  - Section 3 gives the mechanism.

## Tools (`tools/`, experiment only)

- Raw-IR oracle: `cs.sh`, `q.sh` and `rec.py`. This is the w14a118 chunkrw15 oracle (capraw + opt -O3 + llc, as fastbuild),
  with this lane's paths. The unedited `m0` capture is `eq_main` on both bases.
- `sbs.py <cand> olo ohi clo chi [mask]` prints a full side-by-side true-LCS traceback: `=` equal, `~` equal under the
  mask, `-` orig-only, `+` ours-only. It is w14a128's `lcsalign.py` with every row printed, so each run reads in context.
  It needs w14a128's `lcs.py`, `fact.py`, `xled.py`, `dis.py` and `oracle.py` next to it.
- `mvblk.py <rx> <out> blk:after...` moves blocks in the post-opt IR, then runs llc and scores. It runs `opt -passes=instnamer`
  first, so numbered values stay legal after the move. On m0 it reproduces main.
- `gatew.py <rx> <out> a b [moves]` puts `!prof` branch weights a:b on the sweep gate `br` (`bb34`), then runs llc and scores.
- `gen.py`, `gen2.py`, `gen3.py` and `e/` hold the screened source idioms: exact `EDITS`, line count kept.
  `screens.md` has every trial's bytes, M and ratio.

## 1. Per-run cause table (main 86e2a6b, orig 0x1700-0x2600 against ours 0x1700-0x2600, true-LCS rfj)

The region's true-LCS rfj is 403 of 456 orig tokens. The orig chunks 0x1800, 0x1c00, 0x2000 and 0x2400 have 125, 121, 120 and
124 tokens. Main matches 104, 115, 115 and 116 of them under rfj, and 69, 103, 105 and 94 under the full-token mask, so 119 of
490 tokens differ in full. Perfect code in this region would therefore be worth at most about +0.036 ratio. Of that, only
about 40 tokens are skeleton (rfj). The rest is register and frame.

| run (orig / ours) | tokens | what it is | source construct | status |
| --- | ---: | --- | --- | --- |
| orig 0x1700-0x17a0 | 18 | the line-334 error block prefix (to_string pair, `stw 334`) | none: a window-clip artefact. Ours has the same block at 0x16a8-0x16f8, just before the clipped range | not a miss |
| orig 0x1800-0x1810 `stxdw [0x918],r4; [0x948],r3; mov r7,1` | 3 | the fee-Some validate exit spills, and the fee tag as a phi of constants (r7=1) | the original threads the post-validate tree into each validate exit (OV form, w14a89). Its fee tag is known per exit | OV is priced at 0.44-0.55 (w14a89). The fee-tag forms (w14a54) are all rejected |
| orig 0x1830/0x1850/0x18b0-0x18c0 `stxdw [0x950],r6 / [0x958],r5` | 4 | the holder and cashback flags, as per-exit phis spilled in the arms | validate's own holder/cashback flow to the curve store | holder: excluded (w15a08). Cashback phi: w14a142 and w15a09 c1, rejected |
| orig 0x1888-0x1898 `ldxb [0x660] -> stxb [0x540]; mov r3,1` | 3 | the 1-byte piece of `new` copied by value into the sharing payload, plus the skip constant | `Some(args.0)`. Ours copies through the `&(new,)` pointer (ours-only 0x1870-0x18b8) | excluded (w15a10 newentrycopy). Variants `Some(new)` and args placement collapse (w14a107/113/127) |
| orig 0x1978-0x1980 `mov r1,2; stxdw [0x8f8]` | 2 | a second `sharing_update=None` tag store in the JT-duplicated non-shared arm | JT duplicates the non-shared arm head (w14a89 `bb21.thread`) | not reachable without OV |
| orig 0x1990-0x1998 `stxdw [0x8e0],r3; [0x8e8],r7` | 2 | join phi spills: **skip** (not `!skip`) and the fee tag | the skip polarity of the sweep gate (section 3) | every source spelling collapses (section 2f) |
| orig 0x19a8-0x19c8 `[0x520..0x530] -> [0x670..0x680]` | 5 | a 24 B copy of target[8..32) (the 8/24 target split, E32/X24) | the Ok/? memcpy chain and the target split (w13a02 target824, w13a16 e32late) | all rejected there |
| orig 0x1a50 `ldxdw r8,[0x8d8]` | 1 | accounts-pointer reload before `prepare_bonding_curve` | register allocation (ours keeps r8 live) | RA bound (w14a84) |
| orig 0x1d30-0x1d38 `ldxdw r6,[0x8f8]; ldxdw r1,[0x8e0]` | 2 | gate: reload of the sharing tag into r6 for the skip edge, and reload of the skip flag | skip polarity. Ours keeps `!skip` in r9 across the wallet, which is w14a46's r9 occupant | section 3 |
| orig 0x1d48-0x1d50 `ldxdw r1,[0x950]; stxdw [0x950],r1` | 2 | holder flag reload and re-spill: a regalloc split artefact | holder flag live across the sweep | excluded (w15a08) |
| ours 0x1758-0x1798 | 8 | the validate Ok payload pieces (7/1/8/1 B) copied into the target's SROA slots at the single validate exit | single exit plus `?`. The original has per-exit copies (OV) | match/if-let forms: w14a66 m1-m4, rejected |
| ours 0x17b8-0x1800 | 8 | shared-arm head: `r9=1` (the `!skip` phi), `r6=0` (collect_old), `and r8,255` (holder), sharing tag 0 into `[0x8e0]` | the tree's constants. With main's polarity the gate phi is inverted (section 3) | a1-a10 (section 2a) |
| ours 0x1810-0x1868 | 11 | `target=a.bonding_curve.creator`, copied through the curve pointer into `[0x2d0..0x2b8]` | the shared-arm target override. The original picks st.creator in the validate arm (OV) | g0/g1/g11/g13/h* (section 2e). Best: g1, +120 B for +2 M |
| ours 0x1870-0x18b8 | 12 | `Some(args.0)` read through the pointer r0=`&(new,)` | `let args=&(new,)` | excluded (w15a10) |
| ours 0x1928-0x1930, 0x1a40-0x1a48 | 4 | non-shared arm spills of r4/r5, and the target pieces stored at unaligned `[0x579]/[0x571]` in the 0x580 tuple temp | tuple layout and phi coalescing. The original's 0x580 temp has the target aligned first | b3-b8: field order does not move it |
| orig 0x1f48/0x1f70/0x2060 | 3 | sweep: the r8+264 pointer spilled into the dead skip slot `[0x8e0]`, and the bump spilled to `[0x910]`. Ours keeps both in r6/r9 | RA, driven by the free r9 (skip flag spilled) | follows the polarity |
| orig 0x2138/0x2158/0x24a0/0x2528 and ours 0x24f0-0x25f8 | 10 | sweep error exits: the original tail-duplicates the sweep.exit tag test (`jne r7,2 -> err; ja post`) into its preds and reloads holder `[0x950]`. Ours uses `jeq r7,2,ok; ja 25e0` and shared `ja 3c38` exits | MBP tail duplication of sweep.exit (w14a88, w14a111), plus the holder flag | IR-only. Source forms rejected there |

## 2. Idioms screened, with prices (`screens.md` has every row)

M is the scorer's matched-token count. Main is 2,249 at 27,400 B on 86e2a6b, and 2,248 on ed47ac7.

**a. Join tree forms (ed47ac7).**
- a3, a6, a7 and a10 give main's M:
  - a3: skip as a `mut` local;
  - a6: `!shared` arm first;
  - a7: inner `!holder` arm first;
  - a10: `if holder_reward{false}else{..}`.
- a1, a4 and a5 fall into basin A (27,448 B, M 1,710):
  - a1: tuple order `(skip,collect_old)`;
  - a4: collect_old as a `mut` local, so the tree yields skip;
  - a5: all three outputs as `mut` locals.
  - These forms make the gate phi skip-polarity.
- a2 (skip as `!(shared&&holder)`) is 0.56869 @27,448. a9 (creator test first in collect_old) is 0.57335.
- **a8** (the target override before the sharing payload in the arm) is +16 B for M -1 (true-LCS rfj +1).
  - On 86e2a6b it is 27,416 B, M 2,248.

**b. Ok hop and block tuple (ed47ac7).**
- These give main's bytes: b1 (carries skip), b2 (carries collect_old), b4/b5 (field orders), b6/b7 (block tuple order).
- b3 `(sharing_update,target,cashback)` is -5 M. b8 (sharing_update before target in the block tuple) is -1 M.
- Field order never moves the 0x580 temp's layout.

**c. Post-join consumers (ed47ac7).**
- Wallet-gate spellings c1/c3/c4 give main's bytes. c2 (`collect_old.then(||wallet(&ctx)).transpose()?`) is -8 B for -5 M.
- Sweep-gate spellings:
  - c5 `.unwrap_or(Ok(0))?` is 0.64181 @26,768 (-632 B);
  - c6 `skip.then_some(Ok(0)).unwrap_or_else(..)?` is 0.47524 @26,816;
  - c7/c8/c9 (`if let false=skip`, `match skip`) fall into basin B (27,440 B, M 1,776).

**d. Bindings (86e2a6b).**
- d1, d2 and d3 give main's bytes: drop the `let mut target=target` rebind, drop its `mut`, drop `_holder`.
- d5 (prepare_bonding_curve before the Ok hop) is 0.55931 @27,544.
- **d8** (`let sk` before `let args`) is **-192 B for M -68** (0.65574 @27,208, true-LCS rfj -10).
- **d10** (block `holder` as `matches!(hopt,Some(true))`) is **-248 B** for M -257. It does not outline anything: calls 157, lddw 88.
- d8 and d10 are new large negative byte knobs.

**e. The creator override between g0 and g1 (w15a09 next idea 2, 86e2a6b).**

| trial | spelling | bytes | M | true-LCS ---/rfj |
| --- | --- | ---: | ---: | --- |
| main | `target=a.bonding_curve.creator` in the arm | 27,400 | 2,249 | 2,255 / 3,007 |
| g1 (re-check) | `let creator=st.creator;` before validate | 27,520 | 2,251 | 2,257 / 3,014 |
| h2 / h4 | g1 with `.clone()` / `new_from_array(to_bytes())` | = g1 | | |
| g11 / g13 / h10 | `&st.creator` before validate / creator bound at the shared-arm head (with/without clone) | 27,392 | 2,246 | 2,254 / 3,009 |
| h7 / h8 | g0 with `.clone()` / `new_from_array` | = g11 | | |
| h11 | `a.bonding_curve.creator.clone()` | = main bytes | | |
| g1c2 / g1d8 / g1d10 | g1 + c2 / d8 / d10 | 27,512 / 27,304 / 27,256 | 2,247 / 2,183 / 1,999 | |
| g14 / g14b | the non-shared memcmp tests the creator local | 27,352 / 27,368 | 1,536 | collapse |

MIR canonicalises every in-between spelling to either g0 or g1. No third shape exists.

**f. Skip-polarity sweep gate (86e2a6b), 13 spellings × up to 11 sweep/tail forms (gen3.py).**
- Basin B (27,440 B, M 1,777, byte-identical to each other):
  - `if skip{0}else{sweep?}`, `match skip`, `if !skip{sweep?}else{0}`;
  - `if !skip{swept=..}else{swept=0}` and its skip-first twin;
  - `if skip{None}else{Some(sweep)}.transpose()?.unwrap_or(0)`, and its `match` and `Ok(None)` variants;
  - `Some(sweep?)`;
  - `if let Err(e)=r{return Err(e)}`, the `is_err` early returns, and the in-arm match.
- Basin A (27,448 B, M 1,711): `if skip{Ok(0)}else{sweep}?`, `(if ..).map(|v|v)?`, `let mut swept=0; if !skip{..}`, and
  the tree forms pa1/pa4.
- Crossed with the sweep-internal forms (plain `?` native and token arms, n3, amm-if, require_keys_eq dest, native-after-dest,
  the wallet-gate swap, the wallet order swap, `let swept` at the assignment, the coin gate), all 55 combinations still collapse.
  The best is pg3 + native-after-dest at 0.58894 @27,376.
- In the collapsed captures the region itself does improve: true-LCS rfj is +3 at 0x1c00 and +1..+2 at 0x2000, and
  basin A also gains +15 at 0x4000 and +8 at 0x4400. But A loses 500+ tokens in 0x2400-0x5400, and B loses 200 in 0x4800-0x5c00.

**g. Size repay (86e2a6b).**
- a8, c2 and a8+c2 were each combined with the 41 `sizeknobs-cto.json` knobs that still apply (123 trials).
- None reaches 27,400 B at or above main. The pinned ones are c2 + `L_fee_unwrap_again`/`cu_fee_oldunwrap`/`g_fee_unwrap`
  (0.66866) and a8+c2 + `ev_cb_local` (0.66537).

Knob deltas on 86e2a6b (measured on a8, so dB/dM against a8 = 27,416 B / M 2,248):

| knob | dB | dM |
| --- | ---: | ---: |
| s_dest_borrow, g_s7_dborrow | -80 | -12 |
| s_old_borrow | -80 | -44 |
| sh_prog_let / cu_typed | -32 | -9 / -10 |
| sh_accs_let | -24 | -125 |
| cu_fee_replace / ev_cb_local | -8 | -13 / -22 |
| ev_reset_shared / ev_ts_presig | -128 / -592 | -245 / -281 |
| L_share_none_first, ev_auth_deref, ev_ts_map, pool_prog_let, wl_ts_map, sig_arr, pu_match, rent_checked, wl_cr_deref, g_s7_tokamtne, g_s7_tokzero | 0 | 0 |
| g_old_fee_first, cu_replace, sh_fees_key / g_s7_destrev, g_canedit_first / ev_ts_clockvar / prep_match | 0 | -1 / -2 / -10 / -19 |
| L_fee_unwrap_again, cu_fee_oldunwrap, g_fee_unwrap | +8 | -17 |
| wl_ts_clockvar, g_w_clock_local / ev_mint_key | +16 | -3 / -30 |
| w_ev_creator_first / g_s7_destscope / ev_nc_target / sig_mint_acct / p_ev_ts_last / w_create_rev | +64 / +40 / +56 / +64 / +256 / +272 | -17 / -470 / -953 / -552 / -570 / -533 |

No +8 knob is better than -17 M, so g11/g13 (-8 B, -3 M) cannot be repaid.

## 3. Mechanism: why the skip polarity always collapses (post-opt IR, `mvblk.py` / `gatew.py`)

- Main's raw IR has `%_99 = xor i1 %skip, true; br i1 %_99, %sweep, %post`. After -O3, the gate is
  `br i1 %_553.sroa.0.0.off0 (phi false,false,false,true), %bb83 (sweep), %bb88 (post)`. The xor is folded into the
  phi of constants, so ours keeps `!skip` (`do_sweep`) live in r9, the r9 occupant w14a46 found.
- Every spelling without the `not` keeps `phi true,true,true,false` and `br skip, %post, %sweep`. That is the original's polarity.
- After sweep.exit, main's post-opt block order is `sweep.exit, bb88 (post join), bb87 (Err), bb37, bb35`. In every
  skip-polarity capture it is `sweep.exit, bb87 (Err), bb38 (post join), ...`. BPF `analyzeBranch` cannot analyse
  conditional branches, so MBP pre-merges sweep.exit with its IR-next block (w15a02). That makes the Err block
  sweep.exit's fallthrough and gives **basin B**. This order is set inside LLVM: every MIR shape gives identical bytes.
- Moving `bb87` after `bb38` in that IR (`mvblk.py q1 q1mv1 bb87:bb38`) gives **basin A** exactly (27,448 B, M 1,711).
  - The gate becomes the original's: `ldxdw r1,[r10-0x8e0]; jne r1,0 -> post`, falling through into the sweep, with the bump in r7.
  - But MBP then tail-duplicates the sweep.exit tag test into the 660 error predecessor (`jne r7,2,err`, as the original
    does at 0x24a8). It makes the post-sweep chain that block's fallthrough, pulling the whole chain to 0x2490. The original
    keeps `ja 3c68` there and leaves the chain at the end.
- Branch weights on the gate (`gatew.py`: 1:1, 1:2, 1:4, 1:16 and 2:1, alone and with the move) do not restore it. The
  best is 0.55487 @27,424.
- Debug llc (`-debug-only=block-placement`, logs at `$OUT/rx/{m0mv0,q1mv1}/bp.txt`), second MBP pass:
  - In main, `bb56.i` (the sweep.exit tag test, pre-merged with the post join `bb88`) is `non-cold CFG conflict` at the
    660 error block `to_string.exit.i` (`%bb.84`) and at `bb82.i153`. It becomes a `CFG break` candidate only at its last
    predecessor `bb84.i139`, so it is placed after the sweep chain, as in the original.
  - In q1mv1 it is already a `CFG break` candidate at `%bb.84`, so the post chain is laid out right after the 660 error.
  - This is the choice w14a89 found for the 648 block in OV/n_va.
  - The only CFG difference near the chain is the gate edge into the post join: in main it is the gate's FALSE successor,
    in q1 its TRUE successor. Both predecessor sets are {gate, sweep.exit}. Gate weights from 1:16 to 2:1 do not flip it
    back, so the flip comes from chain order, not from this edge's frequency. This is not proven.

So the skip-polarity gate needs both of these:
- an IR order that puts the post join after sweep.exit;
- an MBP decision that does not take the post chain as the fallthrough of the tail-duplicated 660 pred. This is the
  w14a89 swap mechanism, with the 660 block in place of the 648 one.

Neither is reachable from source on main's structure.

## 4. For other lanes

1. d8 (`let sk=a.sharing_config.key();` before `let args`) and d10 (`matches!(hopt,Some(true))` for the block holder)
   are new negative byte knobs: -192 B for -68 M, and -248 B for -257 M. They may serve the outline bases (w15a02 T needs
   **+**216 B, so not there), or forms that are too big by about 200 B.
2. The skip-polarity lead needs the sweep.exit+post chain to stay a `CFG conflict` at the 660 `to_string.exit.i` pred
   (section 3). Next step: compare the two debug logs' first-pass chains to find which earlier chain decision differs,
   since gate weights alone do not flip it.
3. The OV / fee-tag / holder / cashback runs of the join (section 1) are owned elsewhere and all priced negative. Nothing
   else in 0x1800-0x2600 is skeleton.
