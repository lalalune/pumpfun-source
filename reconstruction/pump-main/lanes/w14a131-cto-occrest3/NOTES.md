# w14a131-cto-occrest3: the three unpriced RA forces of main's ceiling (notes only)

Target `0x22a10` `admin_cto::execute`, pinned 27,400 B. Base main `ebe5387e1` (0.67316 / 3,123).
Forces from w14a105 (#3494, 963d1ee numbering): 2077=r4, 1711=r4, 2256=r2. Ledger keys `0x22a10-w14-ebe5387-occrest3-*`.

**Result: no source change. None of the three is worth +0.001 at the pinned size.**

## Oracle
Raw-IR capture of ebe5387 (w14a117 `capraw.py`/`capvar.sh`) + `rx.py`: `eq_main: true`, 0.67316 / 3,123 @ 27,400.
Private greedy llc rebuilt from w14a84 `llc-patch/build.sh`; `screen.py` on `rx/main/m.ll`. Raw data: `data/forces-ebe5387.jsonl`.

## Renumbering (963d1ee -> ebe5387: offset -5 above ~1700, same as a117's 1911->1906, 1622->1617)

| 963d1ee | ebe5387 | root (colmap chain) | sites (orig) | value | greedy step |
| --- | --- | --- | --- | --- | --- |
| 2077=r4 | **2072** | %8 (2072 <- 8) | 0x428, 0x4d0 (head) | piece of head vreg %8 (took R8 at D488, evicted by %12, region-split at D1723 into 2071/2072/2073) | D1725: 2072 -> R0, **free choice, no eviction** |
| 1711=r4 | **1706** | %465 (1706 <- 465) | 0x4a98, 0x4ab0 x2, 0x4b78 (curve store) | **`!holder` bool %465** (the a82 #3409 claim still holds); MachineSink-sunk cashback AND operand | %465 R9 at step 315, evicted by %16, split into 1704-1708; 1706 -> R3 **free, no eviction** |
| 2256=r2 | **2251** | %347 (2251 <- 2249 <- 347) | 0x46a8, 0x46b0 (sharing clone run) | stage-6 spill temp (sz 8, w INF) of %347 (R6 at D630 evicting %330, evicted by %1288 at D1087, split at D1993) | D1996: 2251 -> R1 **free, no eviction** |

All three are free choices: greedy gives each one the first free register in allocation order, so no competing vreg
evicts it, and there is no competitor whose live range a source change could move. The original's r4/r2 come from a
different set of occupants at those points.

## Prices (private llc, ebe5387)

| forces | ratio | bytes |
| --- | ---: | ---: |
| main | 0.67316 | 27,400 |
| 1706=r4 | 0.67376 (+0.0006) | 27,400 |
| 2072=r4 | 0.67356 | 27,392 |
| 2251=r2 | 0.67206 | 27,416 |
| 1706+2072 | 0.67416 | 27,392 |
| 1706+2251 | 0.67266 | 27,416 |
| 2072+2251 | 0.67246 | 27,408 |
| all three | 0.67306 | 27,408 |

Only 1706=r4 keeps the pinned size, at +0.0006 (below the +0.001 bar for step (c)). 2072 and 2251 change size alone,
so they only count inside a size-neutral composite. In w14a117's 8-force climb, 1706 added +0.0006 and 2251 +0.0003.
1706 is the `!holder` / cashback interval, which belongs to the cashback lanes (w14a124/w14a128) and w14a116 sec. 3.

## Next
- 1706: only the cashback/`!holder` interval moves it (owned elsewhere; w14a116 t2/t2b kill %465 at -0.16).
- 2072/2251: size effects (-8/+16 B) dominate; price them only inside a composite paired with sizeknobs-cto.json.
- On this machine (load ~90-120) one rx run took 1,007 s; budget accordingly.
