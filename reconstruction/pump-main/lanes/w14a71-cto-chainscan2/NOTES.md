# w14a71-cto-chainscan2: placement-only lever census on current main, with a jump-masked check

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
This lane continues w14a36-cto-blockplace (#3325). Bases: main 304b03a (0.65788 / 3,223 slots), then 39eb377 after #3386
(0.66477 / 3,230 slots). Ledger approach `chainscan2`, keys `0x22a10-w14-<sha7>-chainscan2-*`.

**Result: no source change. Outside the validate error blocks, every placement-only gain is jump-distance compensation, not
block order. The gain disappears once jump offsets are masked. There is nothing there for an MBP-cause or branch-polarity
source lever to aim at. On 39eb377 the only real block-order lever left is E306 (+0.0009), which is excluded here because
it is a validate error block.**

## Tools (`tools/`, experiment only)

- From w14a36, repointed to this lane: `blkscan.py`, `mvblk.py`, `asmscore.py`, `rx.py`, `capraw.py`, `capvar.sh`,
  `batch.sh`, `llcscore.sh`, `eord.py`, `fm.py`, and the others.
- New `greedy.py <m.s> <out.json> --chains L,.. [--steps N] [--seed LAB:BEFORE,..]`: a greedy multi-move placement-only pass.
  At each step it tries every listed chain at every legal insertion point on the current order and applies the best
  strictly-improving move.
- New `jmcheck.py <m.s> LAB:BEFORE ..`: for each single move, prints the ratio, the **jump-masked** ratio (the `off` field of
  every jmp-class instruction zeroed) and the jump+frame-masked ratio. A move whose gain survives jump masking puts the
  block where the original has it. A move whose gain vanishes (or turns negative) under jump masking only pays because it
  lengthens or shortens jumps over other size differences.
- New `brw.py <m.ll> <line> w1:w2,..  --watch irblock,..`: a single-branch `!prof` weight oracle on post-opt IR. It runs llc,
  then scores and prints the layout neighbours of the watched blocks.

## Placement table on 39eb377 (current main; full table `chainscan-39eb377.json`, 110 chains)

| chain | IR block / error line | best insertion | d_ratio | d_jm | verdict |
| --- | --- | --- | ---: | ---: | --- |
| LBB0_39 | E306 | before LBB0_22 / LBB0_25 | +0.0009 | +0.0048 / +0.0009 | real block order (validate, excluded) |
| LBB0_290 | `bb60.i113` sweep amm `token_frozen ?` Err pad | before `bb9.i111` | +0.0006 | 0 | jump distance |
| LBB0_327 | `bb13.i` wallet native short-circuit | before LBB0_36 (validate) | +0.0006 | -0.0003 | jump distance |
| LBB0_340 | `bb81.i` wallet `collect()?` Err | before LBB0_349 | +0.0006 | -0.0006 | jump distance |
| LBB0_326/333/337 | `bb88`, `bb88.i`, `bb79.i78` pads | various | +0.0003 | <= 0 | jump distance |
| LBB0_21/24/22 | E298 / E289 / `bb10.i` | after the 289 group / bb74 | -0.004..-0.009 | +0.016..+0.021 | original order (289 before 298) needs the and-1 holder-test polarity, not placement |
| all others | | | <= 0 | | |

Greedy (6 moves, `greedy-39eb377.log`): E306, the 290 pad, bb81.i, bb88.i, bb81.i again and bb88 give **0.66806 (+0.0033)**.
Only the E306 move in that sequence is a block-order match. The rest is jump-distance compensation, a size-shift effect
that w14a64's shift map already prices.

## Placement table on 304b03a (`chainscan-304b03a.json`; same method, before #3386)

E334 +0.00659 (jm +0.00659), E306 +0.0027 (jm +0.0030) and E312 +0.0018 (jm +0.0021) were real block-order moves. Outside
validate the leads were the 289 pad (+0.0006, jm 0), bb13.i (+0.0006, jm -0.0003), the Rc `inc_strong` exit239 chain
(+0.0006, jm +0.0003, but its destination is the entry block), bb86 and bb88.i (+0.0003, jm <= 0). w14a36's earlier
bb81.i +0.0009 had dropped to 0 here; it reappears only after another move (greedy). Greedy over the non-validate chains
reached 0.66058 (+0.0027). With E334/306/312 included it reached 0.66747 (+0.0096), of which +0.0075 is validate.
#3386 (w14a66) then landed the E334 lever (0.65788 -> 0.66477), which agrees with the table.

## Weight causes (`brw.py`, 304b03a)

No single-branch weight reproduces a chainscan move with the registers fixed. On BPF, branch weights rerun register
allocation:
- `bb9.i110 -> bb60.i112` (sweep amm Err pad) at 1:2000 or 1:20 gives 0.4995 at 27,448-27,456 B, with the pad placed right
  after the call. At 2000:1 it gives 0.5781 @27,408. At 1:1 it is identical to main.
- `bb60.i -> bb13.i` (wallet native test) gives 0.6423-0.6543 from 1:4 to 1:16 and 0.5973 from 4:1 to 2000:1.
- `bb81.i` (collect Err): 4:1 is neutral (0.65788 / 3,223 slots, with bb81.i placed between bb65.i and bb79.i77, not at the scan
  position). 1:4 tail-merges bb81.i with bb53.i83 (-8 B, 0.65708).

Since the non-validate gains are jump-distance compensation anyway, they have no MBP cause to recover from source.
w14a35 and w14a37 already showed the `collect()` `?` / match / if-let / map_err spellings to be byte-identical.

## Original Err-pad map (corrects an idea tried here)

- Original 0x28d70 (`ldxdw r9,[r10-0x2c8]; ja 0x28278`) is one pad. It is shared by the sweep amm `token_frozen` /
  `token_raw_amount` `?` edges (0x24ef8, 0x24f38, 0x25068) and the wallet `token_frozen` `?` edges (0x286a8, 0x28d40), and
  it goes straight to the function Err return 0x28278. This is the known sweep-Err threading residual (w12a07, w14a48).
- In ours, the sweep pad (`ldxdw r3`) joins `bb56.i` and the wallet pad (`ldxdw r8`) joins `bb66`.
- The pads that reach the sweep join 0x26660 (0x28cf8, 0x28d90, 0x28db8) belong to the sweep token arm. That arm is laid
  out after the wallet. They are not wallet pads.
- Trials j1/j2/k1/k3/k5/k6 merged the wallet and sweep Results into one `?`. They rested on reading those pads as wallet
  pads, and all lose:

| trial | form | ratio @ bytes |
| --- | --- | --- |
| j1 | closure | 0.60926 @27,408 |
| j2 | `and_then` | 0.58174 @26,744 |
| k1 / k3 / k5 | `if !skip{sweep}else if collect_old{wallet}` | 0.23219 @27,328 |
| k6 | | 0.55047 @27,328 |

The k forms are correct semantically: `collect_old` implies `skip`, so the wallet and the sweep are mutually exclusive.

## Next

- On current main, placement-only work outside validate is finished. What remains is E306 (+0.0009, validate lanes) and the
  289/298 order. The 289/298 order is a branch-polarity question: jump masking gives +0.016 to +0.021, but raw ratio loses
  without the original's and-1 holder test (w14a10, w14a39).
- Use `jmcheck.py` before chasing any placement lead. A gain with `d_jm <= 0` is a size shift. Price it with w14a64's shift
  map instead.
