# w15a33-cto-pool1684chain: blocker chain of the event accounts piece 1684=r6 and of mpo's pool pointer 359=r7 (admin_cto 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main `9120883a9`. `programs/` is unchanged on `e61121452`, the origin/main this branch merged: 0.67376, 3,124 slots, 27,400 B, 1034/1034.
Wave-15 lane continued in wave 16. The wave-15 agent died about 6 minutes after it started and left no notes, so this run restarted the angle.
Ledger: approach `pool1684chain`, keys `0x22a10-w15-9120883-pool1684chain-*-v1`.

**Result: notes only, no source change.** The 1684 chain and the mpo 359 chain both end in the long head-to-tail
interval family. That is w15a14's r9 refill chain, which the original avoids through per-arm spilled holder/cashback phis, and
that shape is already priced as a loss. No ordinary local spelling flips either colour. Two new owner-first source forms were
also priced, and both lose.

New for other lanes:
- the full greedy chain behind 1684, with one new link: the Result payload phi `%1657` sits in r8 instead of the original's r9;
- the force `1657=r9`, which gives the largest single-force L2 gain known on main (+0.0132) but changes the size by -120 B;
- `tools/dbgocc.py`, a live-interval occupancy replay of `llc -debug-only=regalloc`.

## Oracle

- `rx/m1/m.ll` is w15a12's raw-IR capture of main (`eq_main: true`).
- The private RAPRIO llc is the w14a84/w15a12/w15a18 build, the same binary as w15a24's (md5 `8d71a7aa...`). It is an llvm-dbg
  build, so it also accepts `-debug-only=regalloc`. That prints every live interval with its slot segments and weight, the
  hints, the eviction candidates and every assign/unassign.
- `tools/dbgocc.py <ra.txt> <vreg> [regs]` replays the assign/unassign lines up to the vreg's `selectOrSplit`. For each register
  it prints the intervals that overlap the vreg, with their weights and spans. This answers "who holds r6 at that step"
  exactly, from live ranges, not from register-name votes. The dumps are in `data/greedy-steps-9120883.txt`.
- `tools/evck.py <fn.bin>` prints the event-region colours: the accounts reload registers, pool_updated, and the sources of nf, old_fee and swept.

## 1. The chain on main 9120883 (greedy steps from the RAPRIO log, intervals from `-debug-only=regalloc`)

| step | vreg | value | decision | why |
| ---: | --- | --- | --- | --- |
| 1172 | `%1684` | event accounts piece, a split product of `%0` (created at step 1169), `[66936,68336)` | **r8** (free) | It misses its hint r2 because the range spans calls. **r6** holds `%1649` pool_updated `[66936,67824)` and `%1396` (`mov r6,r10; add r6,-1552`, the emit_cpi buffer pointer) `[68304,68336)`. r7 holds `%1391` (event data pointer, w 4.9e-6). r9 holds nf `%358`. **r8 is free.** |
| 588 | `%1649` | pool_updated (MOV 0 / MOV 1 phi) | evicts old_fee `%288` from r6 | r7 and r8 hold the Result tag/payload phis `%1658`/`%1657` (w 2.9e-4 / 4.3e-4) over the pool-CPI result check `(66624,66752)`. old_fee in r6 (w 1.37e-6) is cheaper than nf in r9 (w 1.47e-6). Both have the same use frequency; old_fee's range is longer (3,456 vs 3,184 slots), which is the whole weight difference. |
| 432 | `%1657` | Result **payload** phi of the shared return block bb67 (`stxdw [r4+8],r8`) | **r8** (free) | r6 = `%60` (sweep-gate flag) and r9 = `%465` (`!holder`) both overlap its segments. The first is the wallet's line-556 `CtoCreatorAccountNotWritable` `?` site `(23136,23248)`. In all, `%465`, `%466`, `%389` and `%56` overlap it at the same 6-7 wallet/sharing-check sites. |
| 330 | `%60` | sweep-gate flag | evicts the sharing tag `%56` from r6 | r9 = `%465` (w 3.4e-5). The tag drops to the split stage until step 1216 (w14a91 found this link). |

**Original:** the Result payload phi is **r9**. 22 of the 24 jumps into the return block at 0x5868 arrive with the payload
loaded straight into r9 (`ldxdw r9,[..]; ldxdw r7,[..]; ja ret`). The other two are `mov64 r9,r1` copies:
- 0x55a8;
- the tail-merged trampoline at 0x54e0. The sharing CPI check (0x4aa0), the pool CPI check (0x4e48) and an Rc-drop error
  path (0x5588) all reach it with the payload in r1, because swept holds r9 across those CPIs. So at the pool-CPI check the original's r8 is free. pool_updated takes r8, the tag piece keeps r6
to 0x4f28, and the event accounts value splits into an r2 piece (0x4e80) and an r6 piece (0x4f38).

So 1684=r6 needs two conditions. pool_updated must leave r6, which needs r8 free at the pool-CPI check, which needs the
payload phi in r9, which needs r9 free at every wallet error site. And `%1396` must leave r6. Neither has a local lever:
- The weight flip between old_fee and nf only moves pool_updated to r9. old_fee then keeps r6 to the event, and 1684 still takes the free r8.
- `%1396` is emit_cpi! code.

## 2. RA what-ifs on the main capture (`data/forces-9120883.jsonl`)

| change | ratio | bytes | L2 | event colours (accounts / pool_updated / nf / old_fee) |
| --- | ---: | ---: | ---: | --- |
| main | 0.67376 | 27,400 | 0.7852 | r8 / r6 / r9 / spill |
| force 1684=r6 | **0.67645** | 27,400 | 0.7858 | r6 / r9 / spill / spill |
| 1684=r6 + 1671=r7 | 0.67855 | 27,400 | | |
| 1649=r8 / r9 / r7 | 0.58871 / 0.67006 / 0.58958 | 27,424 / 27,408 / 27,264 | | |
| weight nf < old_fee (`358=1.2e-6` or `288=1.6e-6`) | 0.66946 | 27,408 | 0.7833 | r8 / r9 / spill / **r6** |
| weight 1649 low / 288 low / 1396 low | 0.66926 / 0.67136 / = main | 27,400 | | |
| 465=spill | 0.65978 | 27,416 | 0.7841 | |
| 60=r9 (sticky 0.61328) | 0.60864 | 27,304 | 0.7617 | |
| sticky 56=r6 (tag never split) | 0.56389 | 27,336 | 0.7921 | |
| **1657=r9** (payload phi in the original's register) | 0.66867 | 27,280 | **0.79838** | r2 then r9 (two reloads, like the original's r2 then r6) / r6 / r8 / spill |
| 1657=r6 | 0.48817 | 27,416 | 0.5957 | |

Joint cells with w15a14's head-to-tail spill set (key `s4payload`):

| forces | ratio | bytes | L2 | event colours (accounts / pool_updated / nf) |
| --- | ---: | ---: | ---: | --- |
| 465=spill + 1657=r9 | 0.65676 | 27,272 | **0.7997** | r3 / r6 / r8 |
| 465,466,389=spill + 1657=r9 | 0.63504 | 27,280 | 0.7771 | r3 / r6 / r8 |
| 465,466,389,56=spill | 0.59724 | 27,304 | 0.7788 | r2 then r3 / r9 / r6 |
| 465,466,389,56=spill + 1657=r9 | 0.61285 | 27,304 | 0.7788 | r2 then r3 / **r8** (orig) / r6 |

`1657=r9` is the largest single-force L2 gain I know of on main: +0.0132, with L2-matched instructions going from 2,621 to 2,659.
Most of the gain is in validate's error-formatting run 0x800-0x1000, where L2-matched instructions go from 107 to 197 and the
payload loads become `ldxdw r9`. Its -120 B is spread over about 40 small RA edits: fewer `[r10-2272]` tag reloads, and the
holder/fee spill shuffle around 0x4230-0x4990. It is not one block. It is an RA-only result, but it names the register that the
original's whole error-return skeleton uses.

## 3. mpo: why the owner-first gate puts the pool pointer `%359` in r6 (original r7)

mpo = main + `let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();`, the original's gate order at 0x4bc0. The capture
reproduces w15a04: 0.63374 @27,440.

- `%359` covers `[64624,64928)`. It has a hint (r1, the data_is_empty argument copy), which it misses because the range spans
  memcmp. The hint gives it priority `0xE0000130`, above every unhinted global range, including the sharing tag `%56` (`0xA000ABAC`).
- At its dequeue, r6, r7 and r9 are all free over the gate and r8 holds `%0`, so it takes r6 by allocation order.
- To get r7, as in the original, some interval dequeued even earlier must already hold r6 over the gate. In the original
  that is the tag piece. In ours, nothing hinted spans the gate.

| trial (raw-IR oracle) | form | bytes | ratio | pool pointer |
| --- | --- | ---: | ---: | --- |
| mpo | owner-first gate | 27,440 | 0.63374 | r6 |
| mpo_pu | mpo + `pargs` (with the holder byte) built before the gate | 27,456 | 0.63205 | r6; the holder byte takes r7 |
| mpo_hrpre | mpo + `let hrw=a.bonding_curve.is_holder_reward;` before the gate, `pargs=(target,hrw,fee)` | 27,456 | 0.63205 | r6 |

The other pool-region forms are already priced, all at about 0.633 or byte-identical:
- w14a120: pool_updated as the value of the if/match, event `ctx.accounts` rebinding, n1, of1/of2;
- w14a143: pr1;
- w14a106: p1-p5, n4;
- w15a04: pobind, pomatch, poc1/3, porst, pohr, pop2, pu1, hr1;
- w14a107: pa_hb.

## 4. Reading

- On main's code shape, 1684 and mpo's 359 are symptoms of one fact: the long head-to-tail intervals hold r9 (and r6) at
  the wallet error sites (`%465` / `%466` / `%389` / `%56`, w15a14's r9 refill chain).
- Because of that, the Result payload phi cannot take r9. pool_updated then cannot take r8, and the tag cannot keep r6 across the second half.
- The original avoids this with per-arm spilled holder/cashback phis, and that whole-region shape is already priced as a loss
  (w13a38, w15a08 `cbphi`, w14a142, w15a14).
- So no single-region spelling in the pool/event tail can give 1684 or 359 their forced colours.

## 5. Next ideas

- A whole-region validate rewrite that removes all four head-to-tail intervals would free r9 for the payload phi. That is worth
  about +0.013 L2 by itself (`1657=r9`). It needs a size repay of about +120 B plus the frame slot that w15a14 found missing.
  Price it as one joint cell with `1657=r9` as the RA target, not value by value.
- If such a base exists, check whether swept then takes r9 across the CPIs. The payload phi would then split at the two CPI
  checks into the original's `mov64 r9,r1` trampoline at 0x54e0.

## Files

- `tools/dbgocc.py` and `tools/evck.py`: described above.
- `data/greedy-steps-9120883.txt`: dbgocc dumps for 1684, 1649, 1657, 60, 288, 358 (main) and 359 (mpo).
- `data/forces-9120883.jsonl`: every force and weight cell above.
- `edits/`: mpo, mpo_pu, mpo_hrpre (EDITS format for w15a12 `cs.sh`).
