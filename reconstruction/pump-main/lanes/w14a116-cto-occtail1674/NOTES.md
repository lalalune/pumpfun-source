# w14a116-cto-occtail1674: who holds r7 over the 1674=r7 piece (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main `ebe5387e1` (#3495, 0.67316 / 3,123). The raw-IR capture gives `eq_main: true`.
Angle: w14a105-cto-tcftai (#3494) main RA climb force `1674=r7`. The task called it an accounts-pointer `%0` piece in the
pool/event tail at main 0x5cc0. The job: find what occupies r7 there and move it with ordinary source.
Tools: w14a84's private RAPRIO llc (`llc-patch/build.sh`, rebuilt in `$OUT/llvmb`), `colmap.py`, `cclimb.sh` and
`screen.py`, all repointed to this lane. New in `tools/`: `tagdump.py`, `rastate.py`, `regflow.py` and `pe.py`.
Ledger: approach `occtail1674`, keys `0x22a10-w14-ebe5387-occtail1674-*`.

**Result: notes only, no gain.** The piece is not in the pool/event tail. On ebe5387 it is `%1671`, the clone-run piece of
`%0` in **wallet() bb24.i**, which is the `create_idempotent` ATA CPI at 0x5cc0-0x5d98. This is w14a84's `%1669` and
w14a82's "first clone run". Its r8 comes from a chain of greedy queue-order decisions, and the w14a82 / w14a35 / w14a46
rotation analysis already describes that chain. No ordinary-source spelling and no single occupant move reaches it without
a larger cascade.

## 1. Re-priced on ebe5387 (private llc, `data/climb-cc_main0-ebe5387.log`)

| | force | ratio | slots | bytes |
| --- | --- | ---: | ---: | ---: |
| main | - | 0.67316 | 3,123 | 27,400 |
| single | **1671=r7** (963d1ee's 1674) | **0.67525** | 3,116 | 27,400 |
| single | 1684=r6 (963d1ee's 1687, w14a91) | 0.67585 | 3,123 | 27,400 |
| pair | 1671=r7 + 1684=r6 | 0.67795 | 3,116 | 27,400 |
| 8-force climb | 1684=r6, 1671=r7, 1906=r6, 1617=r3, 1706=r4, 1384=r5, 1314=r7, 2251=r2 | 0.68185 | 3,116 | 27,400 |

None of the other "tail" forces is in the wallet region:
- 1706=r4 is the cashback piece at the curve store, 0x4a98;
- 1384=r5 is in the event, 0x4fe0;
- 1314=r7 is the pool AccountInfo, 0x4bc0;
- 2251=r2 is in the sharing clone run, 0x46a8.

Each is worth +0.0003 to +0.0006 alone.

## 2. Occupants over bb24.i (`data/sbs-0x5b80-0x5e00-ebe5387.txt`, `data/tags-wallet-bb24i-ebe5387.txt`)

| value (pre-greedy MIR) | original | ours |
| --- | --- | --- |
| collection_native memcmp result | r9 (0x5be0) | r7 (%722) |
| coin_present `data_is_empty` | spilled `[r10-2328]` | spilled `[r10-2328]` |
| do_collect (`MOV 0`, %1586) | r6 | r6 |
| do_coin (phi 0/1/0, root %1588 -> %1863) | **r8** | spilled `[r10-2344]` |
| accounts `%0` piece (%1671) | **r7** | **r8** |
| ATA CPI account-array base (`MOV_rr %stack _129.i`, [r10-1104], %742) | r9 | **r7** |
| sweep gate `%60` (`%_554` phi, `!skip`) piece %1734 | spilled at its def (`stxdw [r10-2272],r3` 0x1990, reload 0x1d38) | **r9** over the whole wallet (`regflow.py`: defs 0x17c8/0x18d0/0x1908, read 0x1d30) |

The decision chain on ebe5387, from `rastate.py` and `data/ralog-steps311-329-ebe5387.txt`:
1. Step 315: `%465` takes r9 and evicts `%466`.
   - `%465` is `!holder`, that is `(holder&-3)==0` (MIR `AND_ri %384,253` in bb11). Its size is 44,702.
   - `%466` is `st.cashback`.
   - Both are the operands of the cashback `AND`, which MachineSink sinks into the curve-store block (w14a29). So both
     stay live from the head to bb38.
2. Step 322: the account-array base `%742` needs a CSR.
   - r6 holds the tag `%59`, r8 holds `%0` (still unsplit) and r9 holds `%465`.
   - So `%742` evicts coin_present `%720` from r7.
3. Step 1169: `%0` is region-split. Its bb24.i piece `%1671` is dequeued at step 1183.
   - r6 holds do_collect `%1586` and r7 holds `%742`.
   - r8 is the first free CSR, so `%1671` takes r8. Clearing the hint is byte-identical (w14a84).
   - `%1671`'s weight (1.8e-07) exceeds `%742`'s (7.4e-08), but greedy takes a free register before it evicts.
4. Step 1245: the gate piece `%1734` evicts the tag pieces from r9 over the wallet.
5. do_coin finds every CSR busy, so it is split and spilled.

So the r7 occupant is the ATA account-array base. It is there because r9 was busy with `!holder` at step 322. The original
has a single cashback value that is spilled, no `!holder` interval, the buffer in r9 and the accounts piece in r7.

## 3. Priced moves (private llc forces; stock-llc IR and source oracles)

| key | what | ratio | bytes |
| --- | --- | ---: | ---: |
| g1734sp / g60sp | gate piece / whole gate spilled (the original's gate spill) | 0.57913 / 0.58898 | 27,424 / 27,400 |
| g1734sp + 1671=r7 | | 0.58122 | 27,424 |
| fl1863r8 / fl1588r8 | do_coin in r8 (piece / root) | 0.66896 / 0.62504 | 27,424 / 27,416 |
| fl1863r8 + 1671=r7 | | 0.67106 | 27,424 |
| w_all | the original's wallet colouring {gate spill, do_coin r8, accounts r7, buffer r9, memcmp r9} | 0.58152 | 27,424 |
| w_no_sp | the same without the gate spill | 0.67106 | 27,424 |
| 742=r9, 722=r9 | buffer / memcmp to r9 (the force is undone by later evictions) | = main | |
| 465=spill / 465=r6 / 465=r8 / 466=spill | the `!holder` occupant | 0.66007 / 0.65358 / = main / = main | 27,392 / 27,384 |
| prio 465 bottom / 742 top | queue order | 0.65428 / 0.60403 | 27,376 / 27,208 |
| IR cbA / cbB (cbA0 control) | cashback `AND` kept in the head (asm use of the zext / of the i1 `and`) | 0.57404 / 0.60356 (0.67276) | 27,368 / 27,408 |
| cbB + RA climb | colour-target climb on cbB: any size / pinned | 0.66008 / 0.65339 | 27,464 / 27,400 |
| src t2 / t2b | tuple `cashback=!hopt.unwrap_or(false)&&st.cashback` / `st.cashback&&!hopt.unwrap_or(false)` (kills `%465`) | 0.51615 / 0.51308 | 27,496 / 27,504 |

Notes on the table:
- Under cbA and cbB the bb24.i piece is still r8.
- The cbB loss is all colouring: L2 is 0.78508 against main's 0.7855.
- Spellings that the ledger already covers were not re-run: the do_coin / do_collect forms, the ATA gate, the
  wallet(&ctx) signature, the per-arm (target,cashback) form and the cashback spellings. See the w14a03, w14a24, w14a29, w14a35,
  w14a46, w14a56, w14a70 and w14a82 rows.

## 4. Reading / next

- 1674=r7 (ebe5387 `%1671`) is the wallet rotation from w14a82 section 2. The forced r7 helps only as an isolated naming
  fix. Every move of a real occupant (gate, do_coin, `!holder`, buffer) cascades and costs 0.002-0.09.
- The upstream causes are the long `!holder` / `st.cashback` intervals (MachineSink-sunk cashback) and the unsplit `%0` in r8
  until step 424. Payload word 1 in r9 (pw9, owned by w14a102 / w14a113 / w14a107) is the only measured lever that flips
  the first clone run to the original's colouring. Pair any pw9 source candidate with `rastate.py <ra.log> <line of D %742>`:
  r9 must be free when the account-array base is dequeued.
- On any candidate, check the decision with `colmap.py <m.ll> <p>` and then `tagdump.py <p> 0x5cc0 0x5da0`. The accounts
  piece must load into r7 (`ldxdw r7,[r10-2264]` at 0x5cc0).
