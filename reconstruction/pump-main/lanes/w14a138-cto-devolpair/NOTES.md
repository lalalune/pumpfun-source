# w14a138-cto-devolpair: both validate placeholders out at once (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute`, pinned at 27,400 B. Bases: main ebe5387e1 (0.67316, 3,123 slots, M 2,247), then main 90300f9d2 after #3621 (0.67346, 3,124 slots, M 2,248).
Continues w14a115-cto-devol338st (#3510) and w14a119-cto-devol334t1 (#3575), plus w14a121-cto-delwin's (#3524) next idea 2.
Ledger approach `devolpair`, keys `0x22a10-w14-ebe5387-devolpair-<variant>-v1`.

All numbers come from the raw-IR oracle (capraw identity capture of the varied crate, then opt -O3 and llc, scored with
masked tokens; `tools/scr3.py`, a copy of w14a119's scr2 pointed at this lane). M is the count of matched masked tokens and
ratio = 2M/(6676+(bytes-27400)/8). To tie main, a variant needs 27,400 B and M >= 2,247.

The base for every row is **w14a115's devol338st source**: `validate(st:&mut CtoState,..)`, `let hr=st.holder_reward;`
reused at line 298, and `st.fee_configurable=false;` in place of the line-338 `read_volatile`. Gene names are from the
stitch13 / w14a119 library (`tools/genes*.py`, `tools/mine108.py`) plus `q_*` validate spellings in `tools/genes_p.py`.

## Pair table (devol338st base)

| key | genes | bytes | dB | M | dM |
| --- | --- | ---: | ---: | ---: | ---: |
| P0 | (devol338st only) | 27400 | 0 | 2247 | 0 |
| P1 | vol334_back+I6s | 27400 | 0 | 2244 | -3 |
| P2 | vol334_back+I6 (VI6) | 27408 | +8 | 2247 | 0 |
| P3 | vol334_back | 27392 | -8 | 2246 | -1 |

P0 ties main exactly (w14a115). P1 and P2 reproduce w14a119's I6s / VI6 numbers on the devol338st base, so the 338 store
and the 334 removal do not interact.

## The 334 placeholder is 8 bytes of pure fill (P3 vs P0)

P3 differs from P0 in exactly one instruction: P0's `ldxb r1,[r10-0x6a0]` at 0x1580 (the line-334 volatile, the head of the
fee_configurable test block) is gone, and every later jump target shifts by 8. Nothing else in the window changes. So the
placeholder's whole effect is 8 B of fill whose +1 M comes from re-aligning jumps that cross 0x1580.

## Insertion map (`tools/insmap.py`, new oracle; inverse of w14a119's delmap.py)

`insmap.py fn.bin out.json` inserts one non-matching 8-byte slot before each instruction in turn, re-fixes the jumps and
reports M. On P3 (M 2,246) a junk slot anywhere in **0x180-0x1a0, 0x6d8-0x8b8, 0x978-0xeb8, 0xf10-0x14a8, 0x1588-0x18d0,
0x19c0-0x1a90** (519 positions) gives back M 2,247. No single insertion gives 2,248. So any ordinary source change that adds
exactly one instruction in the validate region (0x6d8-0x18d0) and changes nothing else ties main with no placeholder; one
whose instruction also matches the original would beat it.

## Result: negative for the pair; no placeholder-free form ties or beats main without a dead store

Best placeholder-free form at 27,400 B with no dead store: `vol334_back + I6s` (ebe5387: M 2,244, -3) and its #3621 analogue
`vol334_back + N6s` (90300f9: M 2,245, -3 against main's 2,248). Nothing screened repays it.

The only placeholder-free tie is w14a115's two-store form, re-priced on 90300f9 as `Z1` (`st.mayhem=false;` at 334 plus the
devol338st `st.fee_configurable=false;` at 338): **27,400 B, M 2,248, 3,124 slots = main exactly**. Both stores write a local
copy that is never read again, so they are dummy writes under the BRIEF RULE. I am not proposing that as source; the owner
can decide on it (it is the #3510 form plus one more store). `st.max_fee=1` at 334 (`Z2`) is catastrophic on 90300f9
(27,320 B, M 2,220).

## Pair table on main 90300f9 (after #3621 per-arm sharing_update local)

| key | genes | bytes | M | dM vs main |
| --- | --- | ---: | ---: | ---: |
| main | - | 27400 | 2248 | 0 |
| Q0 | devol338st | 27400 | 2248 | 0 (3,124 slots, tie) |
| Q3 | + vol334_back | 27392 | 2247 | -1 |
| QV | + vol334_back + N6 (`target=a.bonding_curve.creator;sharing_update=Some(args.0);(false,true)`) | 27408 | 2248 | 0 |
| QS | + vol334_back + N6s (`target=st.creator;sharing_update=Some(args.0);..`) | 27400 | 2245 | -3 |
| QT | + vol334_back + N0s (`sharing_update=Some(args.0);target=st.creator;..`) | 27384 | 2245 | -3 |
| Q0s | N0s only (334 volatile kept) | 27392 | 2245 | -3 |
| Z1 | + `st.mayhem=false` at 334 (two dead stores) | 27400 | 2248 | 0 (3,124 slots, tie) |
| Z2 | + `st.max_fee=1` at 334 | 27320 | 2220 | -28 |
| R3_cu_unwrapcur / p_colnat / m_t1 | Q3 + gene | 27400 | 2245 / 2244 / 2244 | -3 / -4 / -4 |
| R3_m_crl2 | Q3 + crl2 | 27464 | 2248 | 0 at +64 B |

`insmap.py` on Q3 gives the same map as on P3 (519 positions restore M 2,248; none gives 2,249).

## Screens on ebe5387 (devol338st base; M relative to main 2,247)

Everything is additive: on P3 (vol334_back, 27,392 / 2,246) a gene costs what it costs on main, minus 1. No gene repays.

| family | base | rows | at 27,400 | best M at 27,400 | notes |
| --- | --- | ---: | ---: | ---: | --- |
| `q_*` validate spellings (fee range `max<f`, `!(1..=max).contains`, `f<1`, operand swap, `==true`, if-let, `None` first, cashback expr, `let false=`) | P3 | 15 | 3 | 2,204 | 11 are byte-identical to P3; `q_fcneg`/`p_feecfg` (`!=true`/`==false`) cost 43 M; `q_iflet` -86; `q_cbst` +24 B / -163 |
| same on VI6 | VI6 | 6 | 0 | - | all byte-identical to VI6 (27,408 / 2,247) or worse |
| `h_*` state-field local bindings in validate (`fc`, `mx`, `ql`, `cb`, `he`, `may`; at entry, at fee arm, at 334) | P3 / VI6 / I6s | 30 | 10 | 2,244 | all 30 byte-identical to their base (MIR CopyProp / LLVM fold them) |
| I6 shared-arm spellings (I6b, I6sb, I6a, I6t, I6st, I6n, I6nb, T1s, T3s) | P3 | 9 | 1 | 2,244 | I6a/I6t/I6b = VI6 (27,408 / 2,247); I6n/I6nb (`Some(new)`) -644; T1s/T3s -32 B / -3 |
| stitch13 + mine108 library, genes that apply and are not byte-identical to main or known losers | P3 | 109 | 11 | 2,244 | best overall m_crl2/m_crl3 27,464 (+64 B) / 2,247 |
| same | VI6 | 33 | 3 | 2,241 | best m_crl2/m_crl3 27,480 / 2,248 |

The library scan was stopped at about 40% (the remaining genes are untested on P3/VI6, mostly `evo_*`/`lf*`/`tl_*` orders
that lose 30-500 M on main) when main moved to 90300f9; its later rows carry `e88f9d5` in their ledger keys although their source
was still the ebe5387 devol338st crate.

## VI6's extra copy (next idea 2 of w14a119)

VI6 against P3: `ldxdw r2,[r10-0x940]; mov64 r1,r2` at 0x600 (the `new` Option tag, spilled at 0x5b0 from `ldxb r0,[r9+0]`),
plus a reload `ldxdw r2,[r10-0x940]` at 0x1480 in the shared arm and an r4/r5/r0 rotation in 0xa90-0x1a40. The copy exists
because I6 keeps the tag live into the shared arm's `Some(args.0)`. Every spelling of that arm that keeps `args.0` gives the same
bytes (I6a, I6t); spelling it from `new` directly collapses the arm (-644 M). No validate- or entry-side spelling screened
removes the copy.

## Next ideas

1. Faithful repay for the 334 fill: the original carries fee-arm phi constants (`mov64 r6,0` before the cashback test at orig
   0x1550, `mov r6,1; mov r7,0; mov r5,0` at 0x1100, `mov r7,1` at the 338 exit). One instruction of that data flow in
   0x6d8-0x18d0 is all that is needed (insmap), but #3485 priced the whole flow at -276 M; find a partial form (one constant).
2. crl2/crl3 on Q3 tie main's M at +64 B: pair it with a -64 B M-neutral knob (the crl_L repay of #3495 found only cs_blk).
3. Finish the library scan on Q3 (90300f9) for the genes not reached (`evo_*`, `lf*`, `tl_*`, `wl_*`, `K_*` remainder).

## Tools (experiment only)

- `tools/scr3.py`: w14a119 scr2 pointed at this lane (capraw identity capture + rx.py + exact M, ledger rows).
- `tools/genes_p.py`: `q_*`, `h_*`, I6/N6 variants, `st334*` on top of the stitch13 / w14a119 library.
- `tools/insmap.py`: insertion map (junk slot before each instruction, jumps re-fixed).
- `tools/gaps.py`: LCS gaps between the original and a candidate over a candidate address range.
