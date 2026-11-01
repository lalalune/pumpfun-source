# w17a32-shim-c1spill: the original's per-clone accounts reloads as RA spills (admin_cto 0x22a10, shim track)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main `83bfb5c3e` (admin_cto bytes identical to `8bee07558` / `53ec7fb53`): 0.68754, slim-oracle M 2,295,
3,096 slots, 27,400 B. Ledger: approach `c1spill`, keys `0x22a10-w17-83bfb5c-c1spill-<item>-v1`.

## Result: KILL (bound table committed, no source change)

Forcing the accounts pointer's clone-run split piece to spill reproduces the original's reload structure in the
sharing clone run (C1 rfj +5), but M is below main in every form, with and without sticky forces:

- C1 alone: -13 (27,480 B); -6 with the forced spill's dead reload modelled away (27,472 B).
- C1 after a symmetric sticky climb: -8 against main climbed the same way (2,328 @27,440 vs 2,336 @27,384).
- T1: main has no separate T1 piece. Every force that ends the W1..T1 piece before the creator_vault clone
  re-basins T1 (-99 .. -137).
- Both: -137 .. -272.

The kill condition (bound below +10 M for C1, T1 and both, with and without sticky forces) holds, so step 3
(the original's competition) and the realisation search were not run.

## What main does (RAPRIO log of the slim oracle, `accpieces.py m0`)

`%0` (accounts, `ctx.accounts`) is assigned r8 at dequeue 2, evicted by `%392`, and split at dequeue 1174 (stage
2, priority 51,712) into 17 pieces. The remainder `%1676` is spilled to `[r10-0x8d8]`, with reloads
1693..1698. The pieces that matter here:

| piece | reg | uses | main offsets | region |
|---|---|---:|---|---|
| %1688 | r8 | 35 | 0x1d50 .. 0x3b68 | W1, S1 and T1 up to the event_authority clone |
| %1683 | r8 (INF) | 1 | 0x3208 | `ldxdw r8,[r8+0x78]` (event_authority pointer) |
| %1696 | r1 | 1 | 0x3318 | remainder reload, T1 program clone (= orig 0x3330) |
| %1689 | r5 | 10 | 0x3d50 .. 0x4418 | C1: +0x98, +0x68, +0x0, +0x68 again, +0x8, +0x10, +0x90, +0xa0, +0xa0 again |
| %1692 | r5 | 2 | 0x4460, 0x4490 | C1 tail (+0x98 program clone) |

The original has 34 `[r10-0x8d8]` accesses, main has 24. C1 reloads at 0x3d88, 0x3e30, 0x3f38, 0x4050, 0x4178,
0x42a0, 0x43c8 and 0x44f8 (+0x98, +0x68, +0x0, +0x8, +0x10, +0x90, +0xa0, +0x98), each with a single use. That
is the shape of per-use spill reloads. The T1 tail is different: the original ends its r8 piece at 0x30e8 and then
reloads into r4 (0x3128, five creator_vault field uses: a split piece, not per-use spills), r3 (0x3218,
event_authority) and r1 (0x3330, program).

Main's two "again" uses in C1 are IR-level re-reads, not RA rematerialisation: `%_151` (pool_authority
`rent_epoch:a.pool_authority.rent_epoch`) and `%_196`/`%_203` (pump_fees_event_authority, read three times through
the w17a08/w17a03 Rc-window shims). The original loads each account pointer once per clone.

## Bound table (private RAPRIO llc on the slim post-opt module; rc.py true-LCS region deltas vs main)

| variant | forces / edit | M | dM | bytes | LCS d | C1 | T1 | other regions (exact) | C1 rfj |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|
| main 83bfb5c (m0) | - | 2295 | +0 | 27400 | +0 | +0 | +0 |  | +0 |
| C1: FORCE 1689=spill | 1689=spill | 2282 | -13 | 27480 | -5 | +2 | -1 | V1:-1 S1:-2 W2:-3 | +5 |
| C1: same, dead split reload removed (model) | rmins 0x3d50 | 2289 | -6 | 27472 | +0 | +7 | -1 | V1:-1 S1:-2 W2:-3 | +5 |
| C1: FORCE 1689,1692=spill | 1689,1692=spill | 2283 | -12 | 27496 | -3 | +4 | -1 | V1:-1 S1:-2 W2:-3 | +6 |
| C1: 1689,1692 nodead (model) | rmins 0x3d50 | 2289 | -6 | 27488 | +0 | +7 | -1 | V1:-1 S1:-2 W2:-3 | +6 |
| C1: FORCE 1692=spill | 1692=spill | 2290 | -5 | 27416 | -5 | +2 | -1 | V1:-1 S1:-2 W2:-3 | +2 |
| main + sticky climb (14 forces) | climb | 2336 | +41 | 27384 | +41 | +13 | +4 | E2:+1 V1:+1 V2:-1 J1:-1 J2:+1 P1:+2 EV:+9 S2:+2 W2:+10 | +0 |
| C1 spill + sticky climb (16 forces) | climb | 2328 | +33 | 27440 | +36 | +20 | +2 | E1:+1 E2:+5 E3:+1 V1:-1 S1:-2 P1:+2 EV:+1 W2:+7 | +5 |
| main + 5 forces | 1691=r6,1679=r7,1626=r3,1316=r7,473=r3 sticky | 2318 | +23 | 27392 | +23 | +0 | +4 | V1:+1 V2:-1 J1:-1 J2:+1 P1:+2 EV:+8 S2:+2 W2:+7 | +0 |
| C1 spill + same 5 forces | same + 1689=spill | 2304 | +9 | 27472 | +17 | +2 | +3 | V1:-1 V2:-1 J1:-1 J2:+1 S1:-2 P1:+2 EV:+8 S2:+2 W2:+4 | +5 |
| T1: FORCE 1688=spill (W1..T1 piece) | 1688=spill | 2026 | -269 | 27648 | -173 | -4 | -136 | V1:-1 W1:-3 S1:-15 TL:-2 S2:-1 W2:-11 | +0 |
| T1: FORCE 2173=r8 (creator_vault local piece) | 2173=r8 | 2161 | -134 | 27416 | -130 | -4 | -99 | V1:-1 W1:-3 S1:-12 TL:-4 S2:-1 W2:-6 | +0 |
| T1: all 5 field pieces to r8 | 2173..2181=r8 | 2117 | -178 | 27416 | -157 | -4 | -126 | V1:-1 W1:-3 S1:-12 TL:-4 S2:-1 W2:-6 | +0 |
| T1: PRIO 208-212 before the %0 split | PRIO 60000 | 2146 | -149 | 27424 | -122 | -4 | -107 | V1:-1 S1:-7 W2:-3 | +0 |
| T1: sticky blockers on r6 | 2173=r8 + 215/1183/1723/1733=r6 sticky | 2152 | -143 | 27440 | -143 | -6 | -1 | V1:-1 S1:-4 P1:-8 TL:-103 W2:-20 | +2 |
| both: 1689=spill + 2182=r8 | - | 2158 | -137 | 27496 | -124 | +3 | -100 | V1:-1 W1:-3 S1:-12 TL:-4 S2:-1 W2:-6 | +5 |
| both: 1689=spill + 1688=spill | - | 2023 | -272 | 27728 | -168 | +2 | -137 | V1:-1 W1:-3 S1:-15 TL:-2 S2:-1 W2:-11 | +5 |
| no re-read (IR) rr1 _151=x | - | 2288 | -7 | 27392 | -7 | +0 | -1 | V1:-1 S1:-2 W2:-3 | +0 |
| no re-read rr1 + C1 spill | 1688=spill | 2282 | -13 | 27464 | -4 | +3 | -1 | V1:-1 S1:-2 W2:-3 | +5 |
| no re-read rr12 (all 3) | - | 2261 | -34 | 27344 | -27 | -22 | -1 | V1:-1 V2:+1 S1:-1 W2:-3 | +0 |
| no re-read rr12 + C1 spill | 1687=spill | 2240 | -55 | 27432 | -19 | -16 | -1 | V1:-1 J2:+3 S1:-2 TL:+1 W2:-3 | +7 |
| T1 MIR COPY split (exact MIR oracle) | - | 2157 | -138 | 27392 | -77 | -4 | -65 | V1:-1 S1:-4 W2:-3 | +0 |

Notes on the rows:
- **The forced spill's dead reload.** When `%1689` is dequeued, the remainder `%1676` is already spilled, so the
  split COPY that defines `%1689` has been folded into a reload. Spilling `%1689` leaves that load dead
  (`d1699`, 8 B), and it also disturbs the C1 head alignment. `rmins.py` deletes it and fixes the jumps. That
  model is the closest stand-in for "greedy never made a C1 piece": C1 +7 and LCS equal to main's, so the C1 gain
  is re-attributed away from the other regions, and difflib M is -6.
- **Climbs.** Genes are `rvote.py` votes on each base, priced as single sticky forces. The climb runs greedily over
  the gainful genes at any size (`climbb.py`). The two climbs are path-dependent and use different numbering after
  vreg 1698, but the five-force row applies the same forces to both bases. The main climb only replicates
  w17a27-shim-forcereal's force family (its 2,332 @27,400) as the baseline for the marginal comparison. It is not a
  new result: those forces belong to w17a27.
- **Numbering.** T1 rows use main's numbering for the first force only. Later forced pieces are renumbered by the
  forces before them, so the multi-force T1 rows evict whatever the number names in that run, as the RAPRIO log
  shows.

## Why it fails (mechanism)

1. **The C1 structure gain is small, and naming eats it.** The per-use reloads match the original (rfj +5..+7).
   The same spill moves the registers of the other C1 values: the field temps go to r8 where the original uses
   r6, and the first clone's key goes to r4, spilled at once to -0x928, where the original keeps it in r5 until
   0x3f30 and spills it to -0x910. The spill-slot colours of C1 do not move toward the original (C1 `s` mask +6 to
   +11 vs exact +2 to +7).
2. **Main's C1 source is tuned to the unspilled accounts pointer.** The three IR re-reads (pool_authority
   `rent_epoch`, pump_fees_event_authority x3) are load-bearing: removing them costs -7 to -34. The spill does not
   repay their removal (-13 to -55). A faithful C1 with one pointer per clone plus the spill would need a different
   C1 allocation that no single force produces.
3. **T1 has no piece to spill.** T1's accounts uses live in `%1688`, the r8 piece covering W1, S1 and T1 up to
   0x3208. The original's piece ends at 0x30e8, then a local reload piece in r4 holds the five creator_vault field
   uses. Making r8 busy in the T1 tail evicts `%1688` whole. It then takes r6 by cascade (215, 1183, 1723, 1733)
   instead of being split, and T1 re-basins. The field pieces 208-212 are split after `%0`'s split (stage-2
   priority 1,888 against 51,712). Reordering them with PRIO re-basins as well.
4. **Slot gaps are an RA lever (new finding).** In the exact MIR oracle, a `COPY %0` inserted before the coalescer
   is joined back into `%0`. The deleted COPY still leaves a 16-unit slot-index gap, so every interval spanning it
   grows (`%0` 51,712 -> 51,728, `%55` 43,932 -> 43,948 ...), priorities and weights shift, and greedy re-basins
   (-138). Any instruction that exists at "Slot index numbering" and is deleted later (coalesced copies, for
   example) acts on RA through interval sizes even though it emits nothing.

## Tools (`tools/`, experiment only; they write under the parent of their own directory, like w17a27's)

Copy them next to w17a27's `tools/` (`oracle.py`, `fscr.py`, `rf.py`, `rc.py`, `al.py`, `d.py`, `skel.py`, `rvote.py`).

- `climbb.py <m.ll> <log> --base f,.. --genes votes.jsonl [--sticky] [--par N] [--size 27400|any]` prices every
  vote gene as a single force on top of fixed base forces (for example `1689=spill`), then climbs greedily over
  the gainful genes.
- `accpieces.py <tag>` lists the split pieces of `%0` (register, use count, candidate range, spill children) from
  `ra/<tag>.log` and `ra/<tag>.s` (`rf.py ... --asm`). Use it to find the C1 piece number in any variant.
- `rmins.py <in.bin> <out.bin> off..` deletes instructions and fixes jump offsets. It is a bound model for
  "this instruction would not be emitted".
- `side.py <cand.bin> olo ohi clo chi` aligns an original range side by side with a candidate range.
- `irsub.py <in.ll> <out.ll> old=new ..` replaces an IR value with another and deletes its definition (the
  "read once" model).
- `mirfix.py` holds the **exact MIR oracle** fixup. `llc <flags> m.ll -stop-after=twoaddressinstruction -o m.mir`,
  then `llc <flags> -start-after=twoaddressinstruction m.mir -filetype=obj`, reproduces main (same greedy trace)
  except the 19 outgoing stack-arg stores, which land at `[r10+X]` instead of `[r10-0x1000+X]`; `mirfix.fix()`
  rebases them, and the result is equal to main masked. `-stop-before=greedy` does not round-trip: the coalescer's
  slot gaps are renumbered densely, giving 28,528 B.

## Next ideas (not run; the kill condition stopped the lane)

- The C1 structural gain (+5..+7 rfj, +7 exact once climbed) is real. It only pays together with a C1 allocation
  where the first clone's key keeps r5 to the third clone and the field temps take r6. A joint search would need
  the original's C1 interference, which this lane did not map: who holds r5/r1/r2 across C1, and the weight of
  `%0`'s piece.
- Slot-gap lever: find source constructs that leave a coalescable COPY at a chosen point. Such a COPY is zero
  footprint like passthrough, but it acts on interval sizes, so on greedy priority and weight, rather than on folds.
