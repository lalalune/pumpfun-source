# w15a12-cto-walletmain: wallet RA partner on main without rw7 (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main `90300f9d2` (source identical on `ed47ac72a`): 0.67346, M 2,248, skM 2,810, 3,124 slots, 27,400 B, 1034/1034.
The unedited raw-IR capture `m0` reproduces main exactly (`eq_main: true`).
Re-checked on main `86e2a6b74` (#3666, 0.67376, M 2,249, a head-only CtoState change). The step-386 occupants and the
wallet colouring are identical there, and the sticky h8 bound is M 2,258 @27,384 (+9 M).
Angle: w15a05-cto-rw7walletr8 (#3643) next idea 1. Drop rw7 and find an ordinary `wallet()` spelling on main that puts
do_coin in r8 and the accounts piece `%1671` in r7.
Ledger: approach `walletmain`, keys `0x22a10-w15-90300f9-walletmain-<trial>-v1` (10 source rows) plus the
`stickybound` and `chain386` analysis rows.

**Result: notes only, no gain. The angle is exhausted.** No wallet-local spelling changes the wallet colouring. The colouring
is fixed before greedy reaches the wallet, by four head values that hold r6-r9. A new private-llc mode (sticky forces, below)
shows that even a stable original-style do_coin/accounts colouring is worth only about +9 M on main's structure.

## 1. Source screen (raw-IR capture + opt/llc oracle; `data/src-screen-90300f9.txt`, `data/wck-src.txt`)

`tools/wck.py` aligns each candidate with the original (skeleton alignment from w15a05 `side.py`). It prints our
instruction at the original's do_coin defs (orig 0x5c30/0x5ca0/0x5cb8/0x6100 = `mov r8,0/1/0/0`), the accounts reload
(0x5cc0 `ldxdw r7,[r10-0x8d8]`), the ATA buffer (0x5cf0 `mov r9,r10`) and the two coin gates (0x5e50, 0x6858 `and r8,1`).
Every candidate must show `mov r8,*` with no spill store and `ldxdw r7` at 0x5cc0 before it is worth a build.
The main gate `coin_present&do_coin` is kept in every row.

| trial | form | bytes | M | ratio | do_coin defs | 0x5cc0 accounts | 0x5cf0 buffer |
| --- | --- | ---: | ---: | ---: | --- | --- | --- |
| m0 | main | 27,400 | 2,248 | 0.67346 | `mov r1` + spill [-0x928] | r8 | r7 |
| w01 | do_coin bound before do_collect | 27,392 | 2,179 | 0.65288 | CFG re-laid (frozen(coin) first) | - | - |
| w02 | `let mut do_coin=coin_present;if do_coin{do_coin=!frozen?}` | 27,376 | 2,193 | 0.65728 | r1 + spill | r8 | r7 |
| w03 | `coin_present&!frozen?` (non-short-circuit) | 27,376 | 2,159 | 0.64709 | r1 + spill | r8 | r7 |
| w04 | `!frozen?&&coin_present` | 27,376 | 2,159 | 0.64709 | r1 + spill | r8 | r7 |
| w05 | do_collect as `if native{true}else{..}` | 27,400 | 2,248 | 0.67346 | = main | | |
| w06 | `let (coin_present,do_coin)={let p=..;(p,p&&!frozen?)}` after do_collect | 27,424 | 2,233 | 0.66866 | r1 + spill | r8 | r7 |
| w07 | `match coin_present{false=>false,true=>!frozen?}` | 27,400 | 2,248 | 0.67346 | = main | | |
| w08 | `coin_present=data_is_empty()==false` | 27,400 | 2,248 | 0.67346 | = main | | |
| w09 | ATA gate `!native\|\|do_coin\|\|coin_present` (raises do_coin's use count) | 27,400 | 2,248 | 0.67346 | = main (folded) | | |
| w10 | `coin_empty` binding, every gate on `!coin_empty` | 27,400 | 2,240 | 0.67106 | r1 + spill | r8 | r7 |

What the screen shows:
- Every form either folds to main (w05, w07, w08, w09) or changes the wallet CFG and loses 8-89 M (w01-w04, w06, w10).
- None of them changes which value gets a CSR. do_coin is spilled, the accounts piece is in r8 and the buffer is in r7 in
  all ten.
- The task's other levers were not re-run, because the ledger already covers them:
  - use-count flips (`reread` / `opswap` / `bitand` rows of w14a73, w14a95 and w14a118);
  - the sibling `collect_creator_fee.rs` binding order: that file has no coin/ATA flags at all, only `quote_mint==native_mint`;
  - tag and sweep-gate forms of `%60` (983 `skip` rows, w14a46 and w15a09).

## 2. Why no wallet spelling can work: the RA state at do_coin's first dequeue

On main, w14a84's RAPRIO log (`colmap.py` writes it as `<prefix>.ra.log`) shows do_coin's root `%1588` (w 1.86e-8,
sz 5,802) first dequeued at step 386. `tools/rastate.py` (w14a116) gives the CSR occupants over its range at that step:

| reg | occupant at step 386 | weight | original over the wallet |
| --- | --- | ---: | --- |
| r6 | sweep gate flag `%60` (the `!skip` phi) | 4.6e-6 | do_collect |
| r7 | ATA buffer `%742` (evicted coin_present `%720` at step 322) | 7.4e-8 | accounts piece |
| r8 | **unsplit accounts pointer `%0`** (sz 51,728) | 1.47e-4 | **do_coin** |
| r9 | `!holder` `%465` (the cashback AND operand that MachineSink sinks) | 3.4e-5 | ATA buffer |

do_coin cannot evict any of them, so it goes straight to the split stage.
- `%0` is split at step 1169. Its wallet piece `%1671` takes the first free CSR, which is r8, because r7 holds the buffer.
- At step 1425 do_coin's region split finds `%1671` in r8 over the ATA region, so do_coin is spilled.

Every link of this chain is decided by values that are defined in the head and live across the wallet. Nothing inside
`wallet()` changes their weights or their queue order. The counterfactuals below are private-llc spills:

| force | what takes r9 at the buffer's dequeue | wallet result | bytes | M | skM |
| --- | --- | --- | ---: | ---: | ---: |
| `465=spill` | `%466` (st.cashback) | accounts r8, buffer r7, do_coin spilled | 27,392 | 2,204 | **2,873** |
| `465=spill,466=spill` | `%384` (holder byte) | same | 27,392 | 2,204 | 2,873 |
| `60=spill` (flag) | | same wallet; sweep collapses | 27,400 | 1,933 | 2,802 |

**Pointer for the holder465 lane:** spilling `%465` gains **+63 skM**, and all of it is in orig 0x3e00-0x4400 (the cashback /
curve store; `chunkprof.py` dsk -30/-30/-18 there). The original reloads that value instead of keeping it in a register.
M still drops by 44, from register naming in the same chunks (fM +28 at 0x4200). A sticky climb of 30 single forces on top
of it (`data/sticky-climb-465spill.log`) only recovers 0.66037 -> 0.66926 @27,424. That is still below main, so any ordinary
source that removes `%465` needs a matching rename elsewhere.

## 3. Sticky forces: the first stable bound for the wallet colouring

The earlier force bounds (w14a116, w15a05) use one-shot forces, and later evictions undo them:
- `1863=r8` is evicted again by `%2151` and do_coin ends up spilled anyway (`F 1863 R8 evicting ...; E 1863 from R8 by 2151`).
- `1588=r8` evicts the unsplit `%0` at step 386, which is a cascade and not the original state.

So the 0.627 and 0.669 "do_coin in r8" rows in #3504 and #3643 never actually had do_coin in r8.

`llc-patch/RegAllocGreedy.patch` is w14a84's patch plus one option. With `RAPRIO_STICKY=1`, a forced vreg gets cascade
0x7ffffff0 after its assignment, so no non-urgent eviction can undo it. `build.sh <out>` builds it in about 10 s from the
shared llvm-dbg tree. With the patched llc, `colmap.py` and `screen.py` read `RPLLC` for the llc path (lane copies only).

| sticky force (on m0 unless noted) | do_coin defs | accounts 0x5cc0 | buffer | bytes | M | ratio | skM |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| main | spilled | r8 | r7 | 27,400 | 2,248 | 0.67346 | 2,810 |
| `1588=r8` (root, at step 386) | r8 | r6 | r7 | 27,456 | 1,858 | 0.55604 | 2,832 |
| `1588=r8`, prio 1588=1000 (dequeued after `%0` splits) | r8 | r6 | r7 | 27,424 | 2,238 | 0.67016 | 2,807 |
| + `1671=r7` | r8 | r7 | r6 | 27,424 | 2,245 | 0.67226 | 2,807 |
| **+ `1586=r6` (do_collect), no 1671 force (h8)** | **r8** | **r7** | rematerialised | 27,384 | **2,257** | 0.67636 | 2,805 |
| h8 + best stable single (`819=spill`) | r8 | r7 | | 27,400 | 2,255 | 0.67555 (3,120 slots) | |
| `1588=r8,1671=r7,742=r9`, prio 1588=1000 (the original's buffer too) | r8 | r7 | r9 | 27,400 | 1,949 | 0.58388 | 2,698 |
| rw7 + sticky `91=r8,1585=r6`, prio 91=1000 | r8 | r7 | remat | 27,392 | 2,253 | 0.67506 | 2,809 |

Reading:
- A **stable** original-style wallet colouring (do_coin r8, accounts r7, do_collect r6) is worth **+9 M at -16 B** on main's
  structure, about +0.003. skM goes down by 5 and L2 goes from 0.7855 to 0.7842, so it is register naming only.
- The original's buffer in r9 cascades (r9 is `%465`'s over the head, so forcing it evicts `%384`).
- On rw7, a stable do_coin r8 makes both coin gates match the original exactly (`and r8,1; jne`, tail-duplicated at 0x5e50).
  It is still 4 M below main + h8. This confirms w15a05: drop rw7.
- Queue order alone does not do it. `prio 1588=1000` without a force is byte-identical to main. `prio 1588=max` (dequeued
  first) gives 0.60433 @27,208, and do_coin is still spilled. do_coin keeps r8 only when it is protected from eviction, because
  its weight (1.9e-8) is below every competitor's. An ordinary spelling would have to raise that weight about 10x. The ten
  forms above and the ledger's use-count forms leave it unchanged.
- So the angle's ceiling on main is about +0.003, and reaching it needs the head chain of section 2 to change. That is the
  holder465 lane's lever and the sweep-gate lanes' lever, not a wallet one.

## Next (for other lanes)

1. The holder465 lane: `%465` spilled is +63 skM. Pair any ordinary `!holder` / cashback form with
   `rastate.py <ra.log> <line of D 742>`: r9 must be free at the buffer's dequeue (step ~322). Then re-run `tools/wck.py` on
   the result: the wallet chain (buffer r9 -> accounts r7 -> do_coin r8) should follow without wallet edits.
2. Use `RAPRIO_STICKY=1` for any RA bound that names a long-lived value. One-shot forces on long-lived values are usually
   undone, and the reported ratios then describe a cascade, not the forced state.

## Tools (in this directory)

- `tools/wck.py <fn.bin>...`: wallet colour check against the original (needs w15a05 `side.py` and `oracle.py` next to it).
- `tools/sclimb.py <m.ll> <singles.jsonl> <out.jsonl> <base_force> [K] [rounds] [--size N]`: greedy climb of sticky forces on
  a fixed base (uses w14a84/w14a143 `screen.py`).
- `llc-patch/`: the RAPRIO patch with `RAPRIO_STICKY`, and `build.sh`.
- `edits/`: the ten source trials (cs.sh EDITS format; `c.py` holds the shared anchors).
