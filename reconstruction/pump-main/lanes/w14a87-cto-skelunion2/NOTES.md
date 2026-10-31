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

| base | post-opt | bytes | M | jM | fR | rfR | rfjR | skM |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| t1 | B | 27,456 | 2,255 | 2,376 | 2,310 | **2,658** | **2,750** | 2,885 |
| main | B | 27,448 | **2,259** | 2,376 | **2,314** | 2,655 | 2,746 | 2,881 |
| a1 | h7+B | **27,392** | 2,256 | 2,373 | 2,308 | 2,654 | 2,749 | 2,878 |
| a1 | B | 27,424 | 2,254 | 2,373 | 2,308 | 2,654 | 2,748 | 2,882 |
| main | h7+B | 27,416 | 2,259 | 2,376 | 2,312 | 2,653 | 2,747 | 2,877 |
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

The 0d04cf4 grid (`tbl_rank_0d04cf4.md`, 21 builds x 4) has the same ranking: t1+B rfR 2,665, main+B 2,662, s1+t1+B 2,641,
main 2,620.

Per 0x800 chunk, M/jM against main 95a64ba (`tbl_chunks_95a64ba.txt`):

| chunk | B | a1 | t1 | s1 | p1 | k75 |
| --- | --- | --- | --- | --- | --- | --- |
| 0x0000 | +0/+16 | -1/0 | -1/0 | 0 | **+13/+12** | +2/+15 |
| 0x0800 | **+28/+100** | 0 | 0 | 0 | +1/0 | +9/+80 |
| 0x1000 | -5/-4 | 0 | 0 | 0 | +1/0 | -5/-5 |
| 0x2800-0x3800 | 0 | 0 | 0 | -5/-5 | **-249/-240** | -14/-11 |
| 0x4000-0x4800 | 0 | 0 | 0 | **-96/-91** | -19/-24 | -3/-3 |
| 0x5000-0x6800 | 0 | -2 | -1 | 0 | -10 | -20/-20 |
| total | +23/+112 | -6/-3 | -5/0 | -102/-96 | -280/-274 | -35/+53 |

## Findings

1. **B is the only structural component with an RA-recoverable gain.** It adds +23 M (+28 in orig 0x800-0x1000)
   and +35 rfR. Its raw gain is mostly jump distances: jM +112, rfjR +126. It touches only the validate chunks, so it
   composes additively with a1, t1 and h7. Those three are disjoint and RA-neutral there.
2. **s1 and p1 are not RA-recoverable under a legal frame.** Their skeleton gains show up only with every frame
   offset masked: s1+B skM +148 and p1+B skM +91 over main. Under the legal-frame bound they fall below main:
   s1 rfR -50, s1+B -15, p1 -64, p1+B -30.
   - s1's skeleton gain sits in frame-slot identity that no bijective relayout reaches. The original uses different
     slot sharing (colouring) in the sharing CPI.
   - p1's -249 in orig 0x2800-0x3800 is the cashback-r8 register cascade (w14a09/w14a15). It survives even with
     ideal registers because the slots shift too.
   - **The swarm should not move to an s1 or p1 base.**
3. **The and-1 basin (k75 = p3u+tu8+RVJ+st_ql_first) is a weaker source-side B.**
   - In validate it gains +9/+80 against B's +28/+100, and it loses -35 M elsewhere (0x3800, 0x5800, 0x6000).
   - Its rfR equals main's (+3). Its rfjR is +89, against +126 for B.
   - On 95a64ba it is token-identical to its 0d04cf4 build, because its hb binding overrides #3409's re-derived
     holder.
   - Every union on it is lower: s1+k75 2,106, t1+k75 2,200, a1+k75 2,196.
4. **h7 is size-only.** It removes 32 B at M +-0 on main, a1 and t1. It is not usable on and-1 bases, where its
   memcpy pattern is a different value.
5. **Best composite base: a1 + h7 + B.** It reaches M 2,256 at 27,392 B (+20 M over main, 8 B short) and is
   oracle-only. Main+B alone needs -48 B and t1+B needs -56 B. a1 pays 24 B of B's +48 B at -6 M, and h7 pays the
   rest.

## Hand-off to source search (step 4)

- The structural base the swarm should move to is **main's own RA with the validate error-block order B**, plus the
  size-only partners (a1 -24 B, h7 -32 B). It is not an s1, p1 or and-1 base.
- The source of B belongs to w14a78-valerrplace. B costs +48 B (6 extra `ja`) under fixed RA, so a source form must
  bring its own -48 B repay, or keep fall-throughs that the relay oracle had to break.
- A size-knob screen on main x B is running (`r3.jsonl`). It looks for knobs that repay B's 48 B without touching
  validate. Its results are in the ledger rows `0x22a10-w14-95a64ba-skelunion2-K.*`.

## Tools (in `tools/`, oracle-only)

- `sc.py`: M, jM, fM, skM and per-chunk scores.
- `fbound.py`: fR, rfR and rfjR.
- `relayn.py`: B by IR block names, with `Bspec.txt`.
- `relay.py`: w14a78's relayout.
- `h7.py`
- `post.py`: the base x {-, h7, B, h7+B} grid.
- `run.py`, `cap.sh`, `capvar.sh`: the w14a15 capture runner.
- `e/gen.py`: the w14a15 genes, plus `k75`, `t1`, `a1` and `nB`, and a `_holder` binding fix for genes written
  before #3409. The extra genes are in `e/extra.py`.
