# w14a111-cto-tag660: the 660 sweep-site tag test (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: the open lead in w14a88-cto-sweeptagmem (#3460, Part 1). The original re-tests the sweep Result tag at the AMM-frozen
660 site (orig 0x24fd8..0x25028: `ldxdw r9; ldxdw r7; ldxdw r1,[r10-0x950]; jne r7,2,<exit 0x28278>; ja <bb89 0x26678>`).
Ours ends that site with `ja` to the shared join.
Bases: main 963d1eefb (0.67226, M 2,244, 3,123 slots) for step 1, then main **13fe4536b** (#3480, 0.67256, M 2,245,
3,123 slots) for everything else. Main moved during the lane.
Ledger approach `tag660`, keys `0x22a10-w14-963d1ee-tag660-*` and `0x22a10-w14-13fe453-tag660-*` (22 rows).

`M` = matched masked tokens, `ratio = 2M/(3339+n)`, `n = bytes/8 - 88`. "site 1" = token-arm 660 (orig 0x24c00, ours ~0x2200),
"site 2" = AMM-frozen 660 (orig 0x24fd8, ours ~0x25c8, IR `bb16.i120`).

**Result: no source change, notes only.** The copy needs three things at once: a J2-free single join, reloads of values
that are live across the join inside the join block, and a layout-mode tail-dup decision. No source form produces any of
them without collapsing. The slot gain of the IR copy turns out to be pure alignment. `tools/shiftmap.py` maps that
alignment value for any size-neutral pair of changes (section 4).

## 1. Step 1: the IR copy (w14a88 `dup.py`, made name-independent)

| oracle | base | bytes | M | slots | site-2 shape |
| --- | --- | ---: | ---: | ---: | --- |
| main | 963d1ee | 27,400 | 2,244 | 3,123 | `ld r3; ld r7; ja join` |
| dup660 (`e/d660b.py`) | 963d1ee | 27,400 | 2,242 (-2) | **2,920 (-203)** | `ld r3; ld r7; jeq r7,2,bb89; mov64 r8,r3; ja exit` |
| main | 13fe453 | 27,400 | 2,245 | 3,123 | same as above |
| dup660 / dup660 `ne` polarity | 13fe453 | 27,400 | 2,243 (-2) | **2,919 (-204)** | same as on 963d1ee |
| dup into each other `bb56.i` pred (bb52, bb62, bb82, bb60, to_string.exit) | 963d1ee | 27,400-27,416 | 1,708-2,240 | | only the AMM 660 site is a candidate |

An instruction-level diff of dup660 against main has exactly two hunks: `+jeq r7,2; +mov64 r8,r3` at site 2, and the near-exit
`ja; mov64 r8,r3` block removed (ours ~0x5b00, right after J2). So **the -204 slots are pure alignment**: ours [0x25e0, 0x5b00) moves +2 slots,
which puts orig 0x3000-0x3800 at drift 0 (`tools/drift2.py`). The -2 M is the cost of the copied tokens (`jeq`/`mov64 r8,r3`
against the original's `ldxdw r1,[0x950]; jne; ja` with the payload in r9).

## 2. Step 2: which trigger makes the copy appear (post-opt IR + llc)

| trigger | oracle | result |
| --- | --- | --- |
| non-fallthrough join, block order (963d1ee) | m1-m7: bb89 / bb88 / both to the end, bb88 after exit, exit to the end / after bb36, bb56.i after bb16 | M 2,101 / 2,234@27,392 / 1,704@27,528 / 2,096@27,392 / 1,614 / 1,613 / 1,661. m3/m5/m6/m7 copy the test into **both** 660 sites (the original only has it at site 2), with the payload in r3/r6 and no reload |
| same, exhaustive (963d1ee) | `mvscan.py`: bb56.i after each of the 279 other blocks | only its current place keeps 2,244; every other placement is at most 1,901 |
| J2 removed (w14a51 `r4d`: empty asm in exit + Rent lifetime moved) | native-zero weights 7:5 / 3:1 / none | 1,953@27,448 / **2,223@27,384** / 2,094@27,448; no copy at either 660 site |
| J2 removed + 660-edge weights | `e/r4dw.py`, P = 1:100 / 1:1 / 100:1 | 2,232 / 2,223 / 2,134 @27,384; no copy even with the 660 path hot |
| J2 removed + placement tail-dup knobs | llc `-tail-dup-placement-threshold=4`, `-aggressive-threshold=6`, `-penalty=0` | identical to r4d: the J2-free join is a single `jne` with no reloads, so MBP has nothing to copy |
| live-across holder flag (IR) | `e/h1.py`: curve is_holder_reward from a new tree phi-of-constants; `e/x.py` with r4d and/or the pool CPI arg | 2,215@27,432 (h1, with or without dup660); x_rhc/x_rc/x_hc/x_c 1,914 / 1,727 / 2,082 / 1,837. The flag's reload goes into the **preds** (`ldxdw r1,[0x8e8]` before site 1's `ja`), never into the join block |
| global llc flags | `-tail-dup-size=1/3/4`, `-disable-early-taildup` / `-disable-tail-duplicate`, `-tail-dup-placement=false`, `-tail-merge-size=2/4` | 2,085 / 1,659 / 1,659 / 1,538 / others = main |

The original's `[r10-0x950]` is the **holder flag**, a phi of constants from the head tree (stores `mov r1,0` at 0x23848,
`mov r1,1` at 0x23b38, 0 at 0x23ee8, `r6` at 0x24240 and 0x242c0). It is stored to curve +0xa5 (`is_holder_reward`, 0x27578) and
passed as the pool CPI's r4 (0x27830). w14a91 found the same from the CPI side. The original reloads it **in the join**
(0x26660), at site 2 and at the 648 site. Site 1 enters the join one instruction later (`ja +0x344` -> 0x26668), which skips that
reload. With the w14a51 map (section 5 idea 2: the original's copies at 0x24a8 / 0x2610 / 0x6398 are layout-mode
tail-dups that exist only once J2 is gone), the chain is:

1. a single sweep join with conditional preds, so early tail-dup leaves it alone (w14a51 section 1);
2. reloads of the live-across holder flag and `[0x8f8]` placed inside that join, which makes it long enough to copy;
3. MBP's layout-mode tail duplication into the call-result preds (site 2 among them).

Ours has none of them. Step 1 has no source form (w14a51). Step 3 never fires on a reload-free join. The holder-flag
liveness that step 2 needs puts the reloads in the wrong place and costs +8..+72 B.

## 3. Step 3: source forms (raw-IR capture + rx opt/llc oracle on 13fe453, main M 2,245)

| form | bytes | M | note |
| --- | ---: | ---: | --- |
| v_m1 `swept=match (!skip).then(..).transpose(){Err(e)=>return Err(e),Ok(v)=>v.unwrap_or(0)}` (Err arm first) | 27,400 | 2,245 | eq_main |
| v_m2 `match (!skip).then(..){Some(Err(e))=>return Err(e),Some(Ok(v))=>v,None=>0}` | 27,400 | 2,245 | eq_main |
| v_m3 `match (!skip).then(..){None=>0,Some(r)=>r?}` | 27,400 | 2,245 | eq_main |
| v_a1 660: `if amm_frozen&&token_raw_amount(..)?!=0{return Err(error!(..))}` | 27,384 | 1,953 | layout collapse, no copy |
| v_a2 660: `require!(!amm_frozen\|\|token_raw_amount(..)?==0,..)` | | | compile error |
| v_h1 `curve.is_holder_reward=_holder` (tree bool live across the sweep) | 27,408 | 2,202 | no copy |
| v_h6 tuple carries a 4th holder flag as a phi of constants (`true`/`false`/`holder` per arm) + v_h1 | 27,408 | 2,202 | = v_h1 tokens |
| v_h8 the v_h6 tuple alone (flag unused) | 27,400 | 2,245 | eq_main (control) |
| v_h4 `pargs=(target,_holder,fee)` (pool CPI arg from the tree, as the original's r4) | 27,448 | 1,902 | site 1 gains `ldxdw r1,[0x8e0]` before `ja`: a live-across reload, but in the pred and at the wrong site |
| v_h3 / v_h7 v_h1 or v_h6 + v_h4 | 27,472 / 27,448 | 2,069 / 1,902 | |
| v_h1m1 v_h1 + v_m1 | 27,408 | 2,202 | |

The tag-consumer spellings (Err-first arms) are byte-identical, like w14a88's f2b/f4. The 660 early-return spellings collapse.
Making the holder flag live across the sweep from the tree is the only form that creates a live-across reload, and it costs
at least 8 B with no copy.

Step 4 (a +2 M same-size partner) was not reached. No source form of the copy exists to pair with. The w14a88 knob screens
on 963d1ee show no -8 B lever at M cost 0 that could carry it.

## 4. New oracle: the alignment value of a size-neutral pair (`tools/shiftmap.py`)

slots_diff is positional, so a +8k B change at ours offset p plus a -8k B change at ours offset q moves ours [p,q) by k slots.
Ignoring the changed instructions themselves, the slot gain is `(P_k[q+k]-P_k[p+k]) - (P_0[q+k]-P_0[p])`, where
`P_k` is the prefix count of `orig[j]==ours[j-k]` (masked like target_metric). It runs in 0.3 s on any candidate.
On main 13fe453 (3,123 slots):

| k (slots) | best gain | insert window (ours) | delete window (ours) |
| --- | ---: | --- | --- |
| +1 | 42 | 0x1f00-0x2f80 | ~0x3388 |
| **+2** | **215** | **0x1e00-0x3400** (213-215 anywhere inside) | **0x3be0-0x5de0** (195-208); 0x5de0-0x67e0 still 143-187 |
| +3 | 162-173 | 0x1d00-0x1d28 | ~0x6888 |
| +4 | 158 | 0x1f00 | ~0x5b88 |
| -1 | 60 | 0x0300-0x0c88 | ~0x1690 |
| -2 / -3 / -4 | <= 10 | | |

dup660 (insert at 0x25e0, delete at ~0x5b00, k=+2) is predicted at 204 and measures 204.
On main ebe5387e1 (#3495, 0.67316, 3,123 slots), which landed while this lane was writing up, the map is unchanged:
k=+2 gives 215 (insert from 0x1d28, delete at 0x5c88), k=+1 gives 42 and k=-1 gives 60.
**Read: +16 B anywhere in the sweep body (ours 0x1e00-0x3400, source lines 647-700) plus -16 B anywhere in the
post-sweep region (ours 0x3be0-0x5de0: sharing CPI, curve store, pool CPI, event) is worth about -200 slots.** If the two
changes together are M-neutral, the pair is landable: land.py ranks by ratio, then slots. Unmatched ours segments in the
delete window that a source change could remove include J2 (`jne r7,2,+1; ja` at ~0x5af8) and the `[0x8e0]` reload/store-back
pairs at 0x3ce0 and 0x5938 (`ldxdw r1,[0x8e0]; stxdw [0x8e0],r1`, absent from the original). The near-exit
`ja; mov64 r8,r3` block is the one dup660 removes.

## Tools (`tools/`, `e/`, `ev/`; experiment only; paths point at this lane's `$OUT`)

- `dup.py`: w14a88's join-test copier, now name-independent (`_\d+.sroa` phis, metadata taken from the block, scoped to execute).
- `px.py`: post-opt llc oracle (w14a88) with `LLCARGS` for llc flags.
- `mvscan.py`: block-move scan that also records slots and keeps objects with M >= 2,236.
- `site.sh <name>`: prints the instructions after each 660 site's `Error::from` call (`PXD` selects px/ or rx/).
- `drift2.py <m.o>`: matching-block drift (ours - orig, in slots) per 0x800 of orig.
- `shiftmap.py [cand] [--k 1,2,3]`: section 4.
- `e/d660b.py` (dup660 on 13fe453), `e/r4dw.py` (w14a51 r4d + 660-edge weights), `e/h1.py`, `e/x.py` (tree holder flag),
  `ev/*.py` (section 3 source edits for `capvar.sh`).
