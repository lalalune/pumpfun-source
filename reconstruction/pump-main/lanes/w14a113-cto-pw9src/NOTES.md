# w14a113-cto-pw9src: `new` entry spellings and payload word-1 colouring (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
This lane continues w14a96 and w14a102 (`pw9entry`), which both stopped early. They build on w14a82-cto-walletweight
(#3409, notes #3432). The lead was that payload word 1 belongs in r9: on main, `regmap.py` shows `r9->r8` 21 times.
Bases:
- main 963d1ee (0.67226 / 3,123): the v table, captured by w14a102;
- main 13fe453 (0.67256 / 3,123): the new w screens, the knob pairs and the RA forces;
- main ebe5387 (0.67316 / 3,123): re-check of the key rows.

All three oracles reproduce their main (`eq_main: true`).
Ledger: approach `pw9src`, keys `0x22a10-w14-{963d1ee,13fe453}-pw9src-*`.

**Result: no source change, and the angle is exhausted.** Every `new` entry spelling either matches main's tokens or loses.
- Ten of the fourteen v spellings, and the entry-copy oracles `nfa` / `ne`, collapse for the same reason: the validate-exit
  join flips in MachineBlockPlacement (section 2).
- Undoing that flip after RA, with a legal frame and a perfect colouring, still leaves each of them below main.
- Forcing word 1 into r9 with the private RA llc (no asm perturbation) also loses at the plain ratio (0.66717 against
  0.67256). It only wins with frame and jump offsets masked, and it shrinks the function by 120 B.

## 1. The pw9 table (v01-v14 on 963d1ee, w01-w12 on 13fe453)

Column definitions:
- **ratio** comes from the raw-IR oracle (rx).
- **J** is the number of asm blocks that `jfix2.py` moves back in front of the validate-exit join. 0 means the join was
  not flipped.
- **relaid** is plain / regonly / L1 / L2 after that relayout (`regceil.py`).
- **rfR** and **rfjR** come from `fbound.py`. Main's values are 2,622 and 2,620 on 963d1ee, and 2,623 and 2,622 on 13fe453.
- **r9->r8** is the `regmap.py` count (21 on main).

| key | spelling | ratio @bytes | J | relaid plain / regonly / L1 / L2 | rfR | rfjR | r9->r8 |
| --- | --- | --- | ---: | --- | ---: | ---: | --- |
| v01 | `let new=new;` | 0.67226 = main | 0 | = main | 2622 | 2620 | 21 |
| v02 | `let args=&(new,)` at top | 0.42951 @27,560 | 119 | 0.50859 / 0.61789 / 0.58832 / 0.73735 | 2533 | 2557 | 0 |
| v03 | validate reads `args.0` | 0.43437 @27,808 | 0 | 0.43437 / 0.5084 / 0.44805 / 0.59402 | 2004 | 2034 | 16 |
| v04 | v02 + v03 | 0.41031 @27,688 | 119 | 0.4889 / 0.50052 / 0.58692 / 0.73797 | 2530 | 2580 | 0 |
| v05 | `new` last CtoState field, `st.new` | 0.23703 @27,520 | 119 | 0.24148 / 0.39629 / 0.60251 / 0.77406 | 2480 | 2622 | 0 |
| v06 | v05 + sharing `Some(st.new)` | 0.23492 @27,456 | 119 | 0.31209 / 0.40934 / 0.62388 / 0.77588 | 2475 | 2612 | 0 |
| v07 | `new` first CtoState field | 0.19066 @27,616 | 119 | 0.19541 / 0.40036 / 0.60382 / 0.77595 | 2490 | **2633** | 0 |
| v08 | mut new + `new.take()` (sharing) | 0.41031 @27,688 | 119 | = v04 | 2530 | 2580 | 0 |
| v09 | `new.map(\|k\|k)` | 0.39916 @27,544 | 0 | 0.39916 / 0.45922 / 0.60711 / 0.7078 | 2435 | 2482 | 0 |
| v10 | match rebind | 0.39916 @27,544 | 0 | = v09 | 2435 | 2482 | 0 |
| v11 | args by value `(new,)` | 0.47992 @27,368 | 119 | 0.59434 / 0.7379 / 0.59464 / 0.77476 | 2566 | 2618 | 20 |
| v12 | `&Option<Pubkey>` param | 0.43437 @27,808 | 0 | = v03 | 2004 | 2034 | 16 |
| v13 | `(has_new,nk)` destructure | 0.42107 @27,912 | 119 | 0.50772 / 0.61276 / 0.61929 / 0.76855 | 2549 | 2598 | 0 |
| v14 | mut new + validate `new.take()` | 0.44746 @27,592 | 119 | 0.52888 / 0.65214 / 0.61812 / 0.77153 | 2555 | 2600 | 0 |
| w01 | args right after `mint` | 0.42742 @27,560 | 119 | 0.50888 / 0.63461 / 0.60027 / 0.77229 | | | 0 |
| w02 | args after `shared` | 0.43287 @27,440 | 119 | 0.51931 / 0.51003 / 0.60341 / 0.77252 | | | 0 |
| w03 | args after `holder_key=hk.0` | 0.59573 @27,224 | 0 | | | | 20 |
| **w04** | args after `quote_locked` (before the st block) | **0.66587 @27,360** | 0 | | | | 20 |
| w05 | args first in the st block | = w04 | 0 | | | | 20 |
| w06 | args after `let hopt=holder` | 0.67256 @27,400, slots 3,123 (tokens != main) | 0 | | | | 21 |
| w07 | sharing `Some(Some(target))` | 0.52567 @27,288 | 0 | | | | 0 |
| w08 | sharing `Some(new)`, no args | 0.47992 @27,368 | 119 | 0.59434 (= v11) | | | 20 |
| w10 | holder arm `if let Some(_)=new` | byte-identical | 0 | | | | 21 |
| w11 / w12 | `(&new,)` / `&new` borrow | 0.47992 @27,368 | 119 | 0.59434 (= v11) | | | 20 |
| nfa (IR) | original-like SROA entry copy | 0.21024 @27,416 | 119 | 0.27789 / 0.37281 / 0.63213 / 0.77916 | 2547 | 2580 | |
| ne (IR) | 33-byte entry copy | 0.22245 @27,648 | 119 | 0.29308 / 0.29905 / 0.56947 / 0.77549 | 2570 | 2582 | |
| pb8 / pb9 (IR) | asm `{r8}` / `{r9}` hint on word 1 | 0.60855 / 0.62397 | 0 | regonly 0.70758 / 0.70736 | 2535 / 2535 | 2577 / 2579 | 21 / 0 |

Readings:
- **r9->r8 vanishing is not progress by itself.** Every row that clears it trades it for larger swaps, such as `r2<->r1`
  50-60 times or `r7->r8` 35-54 times.
- **pb9 gains nothing over pb8 once colouring is perfect**: rfR is 2,535 for both. Its +52 M is colour only, and the asm
  perturbation costs about 0.05.
- **v05 and v07 tie or beat main only with jumps masked as well** (rfjR 2,622 / 2,633). That is the "skeleton yes, frame no"
  pattern: putting `new` in CtoState adds 33 B to the struct and shifts the frame.
- **w04 is a free -40 B lever with no join flip**: 0.66587 on 13fe453 and 0.66647 on ebe5387. Repaying it with size knobs
  loses (section 4), but it is a -40 B lever for lanes that need one.

## 2. The validate-exit join flip (`nfa` and ten spellings)

`tools93/cc.py` (w14a93's candidate-vs-candidate L2 diff) on base vs `nfa` shows the move. Base `0x3c38-0x5578` (about
800 instructions) reappears at nfa `0x24a8-0x3dc8`. `blk.py` names the blocks:
- in base, the to_string error arm, then the second validate arm chain `%bb9.i114 .. %bb84.i138` (blocks 85-202), then the
  join `%bb56.i` at `0x3c38` with its continuation `%bb89 ..`;
- in nfa, the to_string arm, then the join (two blocks, `0x24a8`), then the continuation, then the arm chain
  (blocks 175-293), then `%bb5.i`.

This is the same flip that w14a93 found for its pda+hL+fl composite.

Mechanism, from `-stop-after=block-placement` MIR and `-debug-only=block-placement` on base vs v11:
- Before block placement, base's join is one block with twelve predecessors. One of them is the hot conditional edge
  `bb106.i: JEQ r2,2` at 50%. On the second chain-building pass, MBP rejects the join as the to_string arm's successor:
  "Not a candidate ... (non-cold CFG conflict)". The to_string arm is followed by `%bb9.i116` instead, and the join ends up
  after `%bb84.i140`, as in the original.
- In v11 (and every flipped row), greedy leaves a reload at the join's head on the cold edges only
  (`$r5 = LDD_V1 $r10,-2264` in a separate block `bb56.i`). The hot `bb106.i` / `bb108.i` edges and three others enter the
  second half directly, with `$r5 = COPY $r6`.
- The reload head has only cold predecessors, so it loses the CFG conflict. MBP selects it as the to_string arm's best
  successor ("Candidate ... (CFG break) ... Selected"), and the whole arm chain lands behind the join's continuation.
- So the flip is an RA artifact: a spill reload on a subset of the join's incoming edges. Any `new` spelling that perturbs
  RA around the validate exit can trigger it.
- Pricing: `jfix2.py` (w14a93's `jfix.py`, generalised to any `%bb9.iN` name) moves the arm chain back in front of the join
  after RA. Every relaid row stays well below main. The best is 0.59434 (v11 / w08 / w11 / w12), and the best legal-frame
  rfR is 2,566 against main's 2,622. The nfa entry copy itself relays to 0.27789. Its L1 is 0.632 because the two new
  allocas shift the frame, and its rfR is 2,547. **The entry copy of `new` does not pay even with the flip undone, the
  frame relaid and the colouring perfect.**

## 3. Word 1 forced with the private RA llc (13fe453 / ebe5387, no asm)

`colmap.py` names payload word 1 as `%1657` (r8, the original has r9, 22/22 misses; the same on ebe5387). The private llc
is w14a84's RAPRIO build, checked `cmp`-identical to the SDK llc with no hooks. `tools/force.sh` runs it with
`RAPRIO_FORCE`.

| force | plain @bytes | regonly / L1 / L2 | M / fR / rfR / rfjR | r9->r8 |
| --- | --- | --- | --- | --- |
| none (main 13fe453) | 0.67256 @27,400 | 0.76753 / 0.70252 / 0.7855 | 2245 / 2293 / 2623 / 2622 | 21 |
| `1657=r9` | 0.66717 @27,280 (ebe5387: 0.66777) | 0.76955 / **0.72241** / **0.79898** | 2222 / 2263 / 2616 / **2654** | 0 |
| `1657=spill` | 0.66397 | 0.76148 / 0.69329 / 0.76806 | | |
| `1657=r7` | 0.59162 | | | |
| `1657=r6` | 0.48675 | | | |
| `1657=r9,1729=r9` | 0.66647 @27,288 | 0.76944 / 0.69529 / 0.77124 | 2220 / 2257 / 2614 / 2653 | |
| `1729=r9` (swept class) | 0.51445 | | | 21 |

- **Word 1 in r9 removes all 21 `r9->r8` and raises L1 by 0.020 and L2 by 0.013**, but the function shrinks by 120 B, and
  most of the L1/L2 gain comes from that shorter length.
- With the original frame (fR) it loses 30 M. With a perfect colouring (rfR) it loses 7 M. It wins only with jumps masked
  too (rfjR +32 M, at most about +0.009). Reaching that would need the RA decision (no source form found) plus a 120 B repay
  placed exactly where the original's extra jump distance is.
- That matches w14a84 (5e and the colour singles on 95a64ba: `1655=r9` 0.66727 against main 0.66986).

## 4. Size repay of w04 (-40 B) with catalog knobs (13fe453)

There are 44 knobs from the w14a91 `kq` and w14a82 `kn` / `kn2` catalogs. A knob's edit is kept when its old text occurs
once in main; edits already present are skipped. These were screened on top of w04:

| best rows | ratio @bytes |
| --- | --- |
| `ev_auth_deref`, `L_share_none_first` | 0.66587 @27,360 (= w04) |
| `cu_replace` | 0.66557 @27,360 |
| `wl_ts_clockvar`, `g_w_clock_local` | 0.66477 @27,376 |
| `w_ev_creator_first` | 0.66028 @27,424 |
| `x_po` (the only pinned-size pair) | 0.62642 @27,400 |

Fourteen knobs were run before the screen was cut back to the size-raising ones. They are listed in `knobs_w04_13fe453.txt`.
No pair reaches main.

## 5. Next ideas (not this lane's)

- The join flip is a general trap for any change near the validate exit, such as entry or head reorders and validate
  rewrites. Before writing off a collapsed spelling, run `tools/jfix2.py <m.ll> <tag>`: if `moved` is about 119, price
  the relaid ratio rather than the plain one.
- If a lane finds a spelling whose relaid rfR beats main, the trigger to remove is the cold-edge reload at the join head
  (`LDD_V1 $r10,-2264` here). That needs the value it reloads to be in its spill slot, or in the same register, on every
  incoming edge.
- The word-1 colouring is bounded at rfjR +32 M and needs a 120 B jump-placed repay. It is not worth more source screens.

## Tools (text only; experiment only)

- `tools/jfix2.py <m.ll|x.s> <tag>`: post-RA relayout of the validate-exit join. It needs w14a93's `relay.py`,
  `asm2bin.sh`, `regceil.py`, `fbound.py` and `cls.py` next to it (from `origin/swarm/w14a93-cto-pdaheadra` and
  `origin/swarm/w14a87-cto-skelunion2`).
- `tools/blk.py x.s [lo hi]`: execute's asm blocks with byte offset, instruction count and IR block name.
- `tools/force.sh <m.ll> <spec|->`: private RAPRIO llc force, then ratio, `regmap` r9->r8 and regceil.
- `tools/scr.sh` / `tools/batch.sh`: w14a102's pw9 screen plus the jfix2 pass. `e/gen_v.py` and `e/gen_w.py` generate the
  v and w spellings.
- `relay_v_963d1ee.txt`, `screen_w_13fe453.txt` and `knobs_w04_13fe453.txt` hold the raw tables.
