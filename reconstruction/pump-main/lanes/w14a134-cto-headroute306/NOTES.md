# w14a134-cto-headroute306: validate head routes priced (notes only, no gain)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main ebe5387e1 (0.67316, 3,123 slots, M 2,247, jM 2,273 @ 27,400). Continues w14a104-cto-brhead (#3489) and
w14a112-cto-irorder14 (#3514), and replaces w14a130-cto-firstref306, which produced nothing.
Ledger: approach `headroute306`, keys `0x22a10-w14-ebe5387-headroute306-*`.

**Result: no landable change. The best zero-loss measurement is main (0.67316 @ 27,400).**

Pipeline: w14a104's raw-IR capture (`capvar.sh`, `capraw.py`) -> opt -O3 -> llc (`rx.py`) -> `sc.py` (M/jM) and
`seq.py`; post-opt IR moves with w14a112's `mv2.py` through `tools/iro.sh` (run `opt -passes=instnamer` on m.ll
first); true LCS with w14a128's `lcs.py`. With the machine quiet, one raw-IR capture took about 1 minute.

## 1. Original head (orig 0x5e0-0x910)

```
05e0 jne mayhem -> Err284 (far)
0628 jeq hr,0 -> 0x710            ; hr test falls into the hr=1 arm
0640 jne holder -> 0x900          ; hr=1 holder test, falls into Err289 head
0648-0708 Err289 head (to_string, jeq r0,0 -> 0x818 tail; ja panic)
0710 jeq holder,0,+1 ; ja 0x8f8   ; hr=0 holder test, non-holder arm laid out next
0730 and tag,1; jeq tag,0,+1 ; ja 0xc08   ; 306 tag test, Err306 head next
0750-0810 Err306 head
0818 Err289 tail
08f8 jeq en,0 -> Err296           ; enabled test
0900 298 tag test (holder arm)
```

BPF has no branch reversal, so a block that ends in a conditional branch is glued to its IR successor. That makes
the original's IR order, from the head on: bb6 bb7 bb8 .. bb12 bb21 bb25 .. bb13 bb20. These are h289's names:
bb12.i is the hr=0 holder test, bb13.i the enabled test, bb20.i the holder arm (298), bb21.i the 306 tag test and
bb25.i Err306.

## 2. Head routes priced (post-opt IR moves on the h289 capture, real llc RA, ebe5387)

| layout | ratio @ bytes | M | jM | true-LCS 0x400-0xc00 (---) |
| --- | --- | ---: | ---: | ---: |
| main ebe5387 | 0.67316 @ 27,400 | 2,247 | 2,273 | 125 |
| h289 (`if st.holder_reward&&!holder`) | 0.66896 @ 27,400 | 2,233 | 2,343 | 125 |
| bb21>bb12 only | 0.65728 @ 27,400 | 2,194 | 2,302 | |
| bb25>bb21 only | 0.66487 @ 27,392 | 2,219 | 2,338 | |
| bb20>bb13 only | 0.66597 @ 27,400 | 2,223 | 2,332 | |
| bb21>bb12 + bb20>bb13 | 0.66207 @ 27,400 | 2,210 | 2,319 | |
| bb21>bb12 + bb25>bb21 | 0.67296 @ 27,392 | 2,246 | 2,338 | |
| same + enabled group (bb13 bb15 exit) after bb25 | 0.67296 @ 27,392 | 2,246 | 2,338 | |
| **route C: bb21>bb12 + bb25>bb21 + bb20>bb13** | **0.67446 @ 27,392** | **2,251** | 2,361 | 127 |
| C + bb26>bb20 | 0.67446 @ 27,392 | 2,251 | 2,361 | |
| C + bb7 first (bb12>bb3.i23) + Err284 after bb25 | 0.66127 @ 27,392 | 2,207 | 2,322 | |
| bb12>bb3.i23 alone (original bb6->bb7 fallthrough) | 0.66896 @ 27,400 | 2,233 | 2,343 | |
| main capture: bb23.i (306 test) > bb14.i | 0.65998 @ 27,400 | 2,203 | 2,311 | |

- The whole head route is worth **+4 M at -8 B** over main (0.67446 @ 27,392). All three moves are needed; any
  subset is below main.
- Gluing bb7 after bb6 (the original's hr=1 fallthrough) costs nothing and gains nothing, because MBP already lays
  bb7 there.

## 3. Why no source reaches route C in the inlined basin

Route C is the **creation order of a single holder test**: rustc creates the 0-target (non-holder arm, bb21) of
`switchInt(holder)` first, then the holder side (296 enabled test, then 298), and bb21's own switch then creates
Err306. With two holder tests (296's `holder&&..` and the target's `if holder`), the target's join block (bb19) can
only be codegened after its RPO predecessors bb13/bb14. So bb21 is always created after Err296 (w14a104's rule 1).
Every single-test form (in298, nest, closure, nested fn, match guard) falls into the outline basin, because
BFI drops the 307/312 to_string call sites below the 2% cold-callsite line (w14a104's rule 3).

- BFI arithmetic, confirmed on the post-opt IR: the mayhem and hr tests are `icmp eq i8 %b, 0`, and the zero
  heuristic gives 12:20 against the pass side. Non-holder arm frequency is 0.375 x 0.625 x 0.5 = 0.117 with two
  tests, and 0.375 x 0.375 x 0.5 = 0.070 with one. Staying inlined with one test needs either the mayhem pass edge
  or the hr=0 edge at 50/50 or better (x1.33 each, both needed). No validate-local bool spelling avoids
  `icmp eq i8 load,0`.

| spelling (all on h289, ebe5387) | result |
| --- | --- |
| tagb: `let has_new=new.is_some();` bound at validate entry, 298 tests `has_new` | identical to h289 |
| s296G: 296 as `if ..{Err(error!(..))}else{Ok(())}?;` | identical to h289 |
| s298G: 298 as Try on an if-expression | identical to h289 |
| mN306: `let t=match new{None=>return Err(..),Some(t)=>t};` (None-first) | identical to h289 |
| mN306 + s298G | identical to h289 |
| s306G: 306 as `if let Some(t)=new{Ok(t)}else{Err(..)}?` | 0.62665 @ 27,304 (M 2,088) |
| in298 (296 inside the holder arm: route C's creation order) | outline basin 0.43481 @ 26,928 |

Together with w14a104's sec. 4 and w14a112's sec. 4 tables (about 60 spellings), the tag-first, Try-wrapped,
None-first and let-order forms do not change the head's first-reference order. Only the single-test structure does,
and that structure belongs to the outline lanes (w14a123/125/126/127).

## 4. What would unlock it

1. **Outline basin plus the head.** The original outlines 307/312 and has a single-test head. A frame/RA plan for
   the outline basin (w14a08, w14a125-127) gets route C for free. Its head is in298's creation order.
2. **Inlined basin.** Route C is +4 M at -8 B, so it would also need an M-neutral +8 B knob. w14a112 sec. 5 found
   none at 27,400 for the similar lead, so even a source form would be about +0.001 at best.

## Tools (`tools/`)

- `iro.sh <m.ll> <name> moves..`: applies post-opt IR moves (w14a112 `mv2.py`), runs llc and scores with `sc.py`.
- `runpair.sh`: runs w14a104 `trial.sh` captures two at a time.
- `defs_headroute306.py`: the spellings above, in w14a104 `sp/defs.py` format.
