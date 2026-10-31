# w14a87-cto-skelunion2: structural-composite oracle re-run on current main

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main 0d04cf4 (0.66507, M 2,220), then main 95a64ba (#3409, 0.66986, M 2,236). It re-runs w14a15-cto-skelunion
(#3240), which last ran on cef0574.
Ledger: approach `skelunion2`, keys `0x22a10-w14-<main7>-skelunion2-*`.

No source change. No zero-loss gain.

## Oracle

- Raw-IR capture, then `opt -O3`, then `llc` (w14a15 `cap.sh`/`capvar.sh`/`run.py`/`rx.py`). The `m` capture reproduces
  both mains token for token (`eq_main: true`).
- Two post-opt components, applied to every capture:
  - **B** is w14a78-valerrplace's original-like validate block order. `tools/relayn.py` applies the w14a78 `relay.py`
    branch-aware relayout by IR block name. `Bspec.txt` holds the order, recovered by diffing w14a78's `ident.s`
    against its `B.s`. On 0d04cf4 it reproduces their 0.67325 @ 27,440, jm 0.70798 exactly.
  - **h7** is the w14a54/w14a66 7-byte target hoist. `tools/h7.py` is a generic version keyed on the memcpy operands,
    not on block names.
- `tools/sc.py` scores a build and reports:
  - M: matched original tokens, the scorer's count, with `ratio = 2M/(3339+n)`;
  - jM: M with jump offsets masked;
  - per 0x800 original chunk deltas.
- `tools/fbound.py` gives the RA/frame bounds for step 3:
  - **fR**: the legal-frame bound. Align the skeleton (registers, frame offsets and jumps masked), vote candidate
    r10 offset to original offset over aligned accesses (ld/st and `mov rX,r10; add64 rX,imm` leas), take a greedy
    bijection, rewrite the offsets, then count raw M. It is a frame relayout with the same colouring, like w14a18
    slotpin.
  - **rfR**: fR with registers also masked, i.e. perfect register assignment plus a legal frame.
  - **rfjR**: rfR with jump offsets also masked.
  - **skM**: everything masked, including frame offsets with no legality. This is close to w14a74's L2.
- The B/h7 x base grid is `tools/post.py`.

## Components and unions (95a64ba; `tbl_rank_95a64ba.md`, ranked by rfR)

Component **Br** is B with branch-condition reversal allowed (`relayn.run_rev`). A block whose fall-through is no longer
next flips its conditional instead of getting a `ja`. That is what a source polarity flip (`==` against `!=`) would
give. There are 4 flips, in bb7.i, bb14.i, bb16.i and bb23.i, and they save 32 of B's 40 B at the same M.

| base | post-opt | bytes | M | jM | fR | rfR | rfjR | skM |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| t1 | h7+Br | 27,384 | 2,263 | 2,378 | 2,316 | **2,664** | **2,753** | 2,882 |
| main | B | 27,440 | **2,264** | 2,380 | **2,319** | 2,661 | 2,750 | 2,885 |
| main | Br | 27,408 | **2,264** | 2,378 | 2,319 | 2,660 | 2,748 | 2,882 |
| main | h7+Br | 27,376 | 2,264 | 2,378 | 2,317 | 2,658 | 2,749 | 2,878 |
| a1 | Br | 27,384 | 2,259 | 2,375 | 2,313 | 2,659 | 2,750 | 2,883 |
| **K.L_fee_unwrap_again** | Br | **27,400** | 2,260 | 2,372 | 2,316 | 2,661 | 2,747 | 2,879 |
| k75 (w14a75 and-1 basin) | - | 27,352 | 2,201 | 2,317 | 2,242 | 2,623 | 2,709 | 2,821 |
| t1 | - | 27,408 | 2,231 | 2,264 | 2,276 | 2,622 | 2,624 | 2,811 |
| **main** | - | 27,400 | 2,236 | 2,264 | 2,281 | 2,620 | 2,620 | 2,807 |
| a1 | - | 27,376 | 2,230 | 2,261 | 2,274 | 2,618 | 2,622 | 2,808 |
| s1+t1 | B | 27,424 | 2,155 | 2,280 | 2,219 | 2,610 | 2,631 | **2,959** |
| s1 | B | 27,416 | 2,157 | 2,280 | 2,221 | 2,605 | 2,627 | 2,955 |
| p1 | B | 27,456 | 1,981 | 2,102 | 2,035 | 2,590 | 2,693 | 2,898 |
| s1 | - | 27,368 | 2,134 | 2,168 | 2,188 | 2,570 | 2,501 | 2,881 |
| q2+tu8 | - | 27,320 | 2,148 | 2,268 | 2,200 | 2,560 | 2,662 | 2,831 |
| p1 | - | 27,408 | 1,956 | 1,990 | 2,001 | 2,556 | 2,594 | 2,826 |

The 0d04cf4 grid (`tbl_rank_0d04cf4.md`, 21 builds x 4) has the same ranking. There t1+B has rfR 2,665, main+B 2,662,
s1+t1+B 2,641 and main 2,620.

Per 0x800 chunk, M/jM against main 95a64ba (`tbl_chunks_95a64ba.txt`):

| chunk | B / Br | a1 | t1 | s1 | p1 | k75 |
| --- | --- | --- | --- | --- | --- | --- |
| 0x0000 | 0/+16 | -1/0 | -1/0 | 0 | **+13/+12** | +2/+15 |
| 0x0800 | **+28/+100** | 0 | 0 | 0 | +1/0 | +9/+80 |
| 0x1000 | 0 | 0 | 0 | 0 | +1/0 | -5/-5 |
| 0x2800-0x3800 | 0 | 0 | 0 | -5/-5 | **-249/-240** | -14/-11 |
| 0x4000-0x4800 | 0 | 0 | 0 | **-96/-91** | -19/-24 | -3/-3 |
| 0x5000-0x6800 | 0 | -2 | -1 | 0 | -10 | -20/-20 |
| total | +28/+116 | -6/-3 | -5/0 | -102/-96 | -280/-274 | -35/+53 |

## Findings

1. **B is the only structural component with an RA-recoverable gain.** It adds +28 M, all in orig 0x800-0x1000,
   and +40 rfR. Its raw gain is mostly jump distances: jM +116 and rfjR +130. It touches only validate, so it
   composes additively with a1, t1, h7 and size knobs. Those are disjoint from validate and RA-neutral there.
   - **B's size cost is mostly polarity.** Br keeps M 2,264 at +8 B instead of +40 B.
   - The original has 19 `ja` in its first 700 instructions. Main has 17, Br 18 and B 22.
2. **The best pinned composite (oracle only) is K.L_fee_unwrap_again + Br: 0.67705 at 27,400 B, M 2,260.** That is
   +24 M over main 0.66986.
   - The knob is `curve.creator_fee_bps=fee.unwrap_or(old_fee);`, the same edit as `K.g_fee_unwrap` and
     `K.cu_fee_oldunwrap`. Alone it gives -8 B at -5 M.
   - Full knob x Br table: `tbl_knobs_Br_95a64ba.md`. 14 knobs are token-identical to main, and no knob is
     M-neutral at -8 B.
3. **s1 and p1 are not RA-recoverable under a legal frame.** Their skeleton gains show up only with every frame
   offset masked: s1+B skM +148 and p1+B skM +91 over main. Under the legal-frame bound they fall below main:
   s1 rfR -50, s1+B -15, p1 -64, p1+B -30.
   - s1's skeleton gain sits in frame-slot identity that no bijective relayout reaches. The original uses different
     slot sharing in the sharing CPI.
   - p1's -249 in orig 0x2800-0x3800 is the cashback-r8 register cascade (w14a09/w14a15). Its frame slots shift
     too.
   - **The swarm should not move to an s1 or p1 base.**
4. **The and-1 basin (k75 = p3u+tu8+RVJ+st_ql_first) is a weaker source-side B.**
   - In validate it gains +9/+80 against B's +28/+100, and it loses -35 M elsewhere (0x3800, 0x5800, 0x6000).
   - Its rfR equals main's (+3).
   - On 95a64ba it is token-identical to its 0d04cf4 build, because its hb binding overrides #3409's holder
     re-derivation.
   - Its unions are lower: s1+k75 2,106, t1+k75 2,200, a1+k75 2,196.
5. **h7 is size-only.** It removes 32 B at M +-0 on main, a1 and t1. It does not apply to and-1 bases, where the same
   memcpy pattern carries a different value.

## Re-check on main ecea702 (#3430: validate volatile placeholder at 334, 0.67076, M 2,239; `tbl_rank_ecea702.md`)

- **B shrinks to +14 M** (27,448 B), and Br to +14 M at 27,416 B. The validate chunks still gain +26, but the rest
  loses -12, mostly orig 0x2000 (-8).
  - #3430's placeholder has the same block structure. Blocks are only renumbered: `relayn.alias` maps them by
    nearest number.
- **t1 now composes with B better than main does.** t1+B reaches M 2,262 at 27,448 B, and t1+h7+Br M 2,265 at
  27,384 B. That is the best on every bound: rfR 2,666 and rfjR 2,754.
- Source-only pinned composites are all below main:
  - t1+`g.s_su_iflet` 0.66956 at 27,400 (+Br: 27,408 B, M 2,263);
  - t1+`g.e_reset` 0.66956;
  - t1+`K.L_fee_unwrap_again` 0.66777.
- s1 (rfR 2,571-2,599) and k75 (2,622) stay at or below main's 2,623.

## Hand-off to source search (step 4)

- The structural base to move to is **main's own RA plus the validate error-block order B with the polarity of Br**.
  It is not an s1, p1 or and-1 base.
- A source form of B (w14a78-valerrplace) should flip the conditions of the bb7.i, bb14.i, bb16.i and bb23.i tests
  along with the order. Then it costs only +8 B, and `curve.creator_fee_bps=fee.unwrap_or(old_fee)` repays that
  exactly (oracle 0.67705 at 27,400).
- Without the flips, B costs +40 B. The repay is then a1 (-24 B, -6 M) plus a -16 B knob, or h7, which has no
  source form.
- genes47 x Br screen (first 22 of 163 genes on 95a64ba, then the full list on ecea702; out dir `pl4_95a6.jsonl`,
  `pl5.jsonl`, and the ledger):
  - `g.s_su_iflet` (`if let Some(val)=sharing_update{..}` instead of `match`) is -8 B at M +1 alone on 95a64ba.
  - With Br it lands at exactly 27,400 B with M 2,266 (+30), the best pinned oracle composite on 95a64ba.
  - `g.e_reset` is -8 B / +1 alone, and +25 with Br.

## Tools (in `tools/`, oracle-only)

- `sc.py`: M, jM, fM, skM and per-chunk scores.
- `fbound.py`: fR, rfR and rfjR.
- `relayn.py`: B by IR block names (`run`), and Br with condition reversal (`run_rev`), with `Bspec.txt`.
- `relay.py`: w14a78's relayout.
- `h7.py`
- `post.py`: the base x {-, h7, B, h7+B} grid. `postr.py` adds the Br variants, and `postlean.py` gives M-only Br
  screens.
- `run.py`, `cap.sh`, `capvar.sh`: the w14a15 capture runner.
- `e/gen.py`: the w14a15 genes, plus `k75`, `t1`, `a1` and `nB`, and a `_holder` binding fix for genes written
  before #3409. The extra genes are in `e/extra.py`.
