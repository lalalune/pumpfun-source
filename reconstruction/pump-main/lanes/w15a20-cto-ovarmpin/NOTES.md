# w15a20-cto-ovarmpin: why the ov family hoists the sharing-CPI arm, a carrier that stops it, and the price at main's layout (notes only)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. Base: main 86e2a6b74
(0.67376, 3,124 slots). admin_cto.rs is unchanged on 9120883a9. This lane continues w15a11-cto-valtraceback (#3683), next
idea 1. Ledger: approach `ovarmpin`, keys `0x22a10-w15-86e2a6b-ovarmpin-<trial>-v1` (18 rows).
Oracle: w15a11's raw-IR capture, `opt -O3` and `llc` (`tools/cv2.sh`, `tools/rx.py`); `m0` reproduces main exactly (`eq_main`).
True-LCS metrics use w14a128's DP (`tools/evm.py`, `tools/evc.py`).

**Result: no landable change. Main is still the best zero-loss measurement (0.67376 @ 27,400 B).** All three steps of the
angle ran:

1. The pass is named. It is not IR jump threading.
2. An ordinary carrier keeps the arm in place.
3. At main's layout every ov form is still below main, so class F does not come back.

## 1. What moves the sharing-CPI arm (step 1)

- **The IR is not the cause.** After `opt -O3`, the block order of `execute` is the same in m0 and ov1a. The
  `admin_cto_sharing_config` call block has index 250 in m0 and 253 in ov1a (3 extra validate blocks). The post-sweep
  `Result` join `bb56.i` is the same IR in both. `-debug-only=jump-threading` (private llvm-dbg opt) shows the same
  execute threads in m0 and ov1. Only validate's Result tag and the sweep result are threaded, and `shared` is never involved.
- **The cause is MachineBlockPlacement, after a branch-folder tail merge splits `bb56.i`.** This is the mechanism
  w14a142-cto-holderflagtm (#3628) found for its holder flag. Here the extra live-in is a different value:
  - main: `bb56.i` has live-ins `$r3, $r7`. The `sharing_update` tag lives in `[r10-2272]` and is reloaded in bb88.
  - ov1a/ov1b: greedy carries the **`sharing_update` tag in r5** across the join (`tools/jp.py`). Six predecessors reload
    `$r5 = LDD [r10-2272]`, and three (bb82.i, bb16.i, bb93.i) use `$r5 = COPY killed $r6`.
  - ov2/ov3/ov4: the same happens with **r9 = `[r10-2400]`**.
  - The extra common tails make the branch folder merge bb95.i into bb60.i and split `bb56.i` in two. The to_string error
    predecessor then falls into the 5-predecessor half. Placement puts chunk B at 0x2458, ahead of the sweep body (chunk A).
    Chunk B is bb56.i, bb88, bb35, the 799-instruction sharing arm and the tail.
  - `llc -enable-tail-merge=false` hoists the arm in **main too** (0x3758), so main's placement depends on that merge.
- Reproduction: `tools/mbb.py` (block order after placement), `tools/succ.py` (successor probabilities before
  placement), `tools/blkdump.py` (MIR before branch-folder) and `tools/llcv.py <name> <tag> [llc args]` (sharing-call offset).

## 2. Carriers (step 2)

`tools/restore.sh` / `tools/mired2.py` is the MIR join-restore oracle. It stops before branch-folder, removes the extra
live-in defs from the join predecessors, reloads the value at the head of bb88, and resumes. With no edit, the round trip
is `cmp`-identical.

| trial | change | sharing call | ratio @ bytes | true-LCS rfj vs main |
| --- | --- | --- | --- | ---: |
| main (m0) | | 0x4a20 | 0.67376 @27,400 | 0 |
| ov1a | validate takes `shared`, non-holder arm `if shared{st.creator}else{t}` | 0x3280 | 0.42682 @27,448 | -534 |
| ov1a, MIR restore (3 preds) | oracle | 0x4a48 | 0.52838 @27,408 | **-13** |
| ov2 | whole tree in validate's arms (tuple) | 0x3328 | 0.37545 @27,688 | -541 |
| ov2, MIR restore (r9 off the join) | oracle | late | 0.41724 @27,640 | **-38** (1000:+11, 1800:-23, 3000:-14) |
| m_rs | main + event `sharing_config_reset:shared` | 0x4a10 | 0.59081 @27,288 | -19 |
| **o_rs** | **ov1a + `sharing_config_reset:shared`** | **0x4a28 (kept)** | 0.52042 @27,272 | -26 |
| ov1_rs | ov1 (tree no longer overrides target) + reset | 0x49b0 (kept) | 0.52671 @27,152 | -31 |
| ov2_rs | ov2 + reset | 0x4a90 (kept) | 0.41204 @27,424 | -51 |
| m_sl / o_sl | `sharing_update` built after the sweep from `shared`/`_holder`/`new` | hoisted | 0.386 / 0.397 | -547 / -545 |
| m_il / o_il | `if let Some(val)=sharing_update` | kept / hoisted | 0.67236 / 0.42658 | 0 / -534 |
| m_sr / o_sr | sl + reset | hoisted | 0.399 / 0.392 | -545 / -541 |

- **`sharing_config_reset:shared` is an ordinary carrier that blocks the hoist.** With it, the tag has no use after the
  sharing match, so greedy no longer keeps it in a register across the sweep join. The arm stays at main's position in
  every ov form tried (o_rs, ov1_rs, ov2_rs). It costs 128 B and -19 tokens on main itself.
- Building `sharing_update` after the sweep (`sl`) moves the tag's live range but hoists in all forms.

## 3. Price at main's layout: class F does not come back (step 3)

- The restore oracle is the bound for any carrier whose only job is placement. It gives ov1a -13 and ov2 -38 true-LCS rfj,
  with ratio 0.528 and 0.417. Validate gains at most +11 (ov2, orig 0x1000), and the tree region at orig 0x1800 loses -23.
  Main already matches the original's tree there.
- **Why ov does not produce class F.** The original's class F is fee-None threading. Its non-holder arm tests `shared`
  before the fee checks (orig 0xdc0). Each fee-None edge then jumps straight into its tree arm (orig 0xe38 → 0x1850 and
  0x1500 → 0x18f8). That shape comes from the **second JumpThreading run** threading the tree tests (bb18 `holder`, bb21) through
  the tree-test block bb75. In main and in every ov form, JT refuses: `Not threading BB 'bb18' - Cost is too high: 8 for
  PredBB` (BBDupThreshold 6).
  - bb75 holds **10 memcpys** of the 7/9 B target pieces, cost 20 (`tools/pjt.py`), along the hop chain
    `target.i → _49 (Result<Pubkey>) → _411 → _48 → val → target`. That chain is the validate return, the `?`, the block
    tuple and the `Ok::<_,Error>((..))?` hop.
  - `-jump-threading-threshold=20` (oracle) makes JT thread exactly bb75+bb18 and bb75+bb21. The threading is worth at most
    +9 validate tokens: m0 -49 (800:+3, 1800:+6, 0x4800 -44), ov1 -45, ov1a -39, o_rs -15, m_rs -17.
- The faithful out-param forms of w13a18 (`lv3`, `vb`), ported to 86e2a6b, still thread in-pipeline. That gives the
  original three-way fee-None threading. Their prices:
  - `vb` keeps the arm late, but scores 0.2419 @27,104 with rfj -114. Validate is flat, and 0x5000-0x6400 loses -90 (a
    tail-chunk move).
  - `lv3` hoists: 0.21547, rfj -503.
  - `reset:shared` does not rescue either: lv3_rs -502, vb_rs -116.

So no ordinary carrier pays. The placement collapse can be blocked (o_rs), or bounded by the MIR oracle at 0 placement loss.
Either way the ov forms stay 13-51 true-LCS tokens below main, and 0.15-0.25 below it in exact-byte ratio. The validate
class F tokens need fee-None threading. That threading needs a cheap tree-test block (≤ 3 target memcpys), which means
removing hops whose frame order main depends on (w13a16 #2974 added the Ok hop for +0.009).

## Next ideas (untried here)

1. Pair `o_rs`/`ov1_rs` (layout kept) with a frame compensator for the -128 B and the 8 B frame shifts (`tools/fhist.py`
   from w15a11), and price it against w14a142's frame-masked metric. Restored ov1a is -13 rfj, so it can only pay with an
   original-faithful frame.
2. Collapse the bb75 hop chain to ≤ 3 memcpys while keeping the frame order. One example: carry `target` in the Ok hop
   only, not in the block tuple too. Then check `Threading through 'bb75' and 'bb18'` in the debug-opt trace
   (`-debug-only=jump-threading`).
3. Any variant that shows the 6 KB chunk A/B swap should run `tools/jp.py` on its `-stop-before=branch-folder` MIR first. A
   tag or accounts-pointer live-in at `bb56.i` means it is this tail merge, and `tools/restore.sh` prices it at main's layout.

## Tools (`tools/`, experiment only; paths point at this lane's `$OUT`)

- `cv2.sh` / `rx.py`: w15a11's capture and oracle. `rx.py` takes extra opt flags through `OPTX=`.
- `llcv.py`: llc with extra flags; prints ratio, bytes and the sharing-call offset.
- `mbb.py`, `succ.py`, `blkdump.py`, `blk.py`: MBB order after placement, successor probabilities, MIR block dumps, IR
  block order.
- `jp.py`: join predecessors of the post-sweep `bb56.i` with their register defs (from w14a142; also finds `bb56.iNNN`).
- `restore.sh`, `mired.py`, `mired2.py`: join-restore MIR oracle (line replace; or delete defs and insert a reload).
- `pjt.py`: JT duplication-cost breakdown of one block, from `-print-before=jump-threading -filter-print-funcs=<fn>`.
- `evm.py` / `evc.py`: true-LCS deltas by mask, and per orig 0x800 chunk, against `$BASE/unstripped.so`.
- `e/`: edit sets (`gen.py`, `gen2.py`) and the ledger script `rec.py`.
