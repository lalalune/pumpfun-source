# w15a29-cto-devolrepay: placeholder-free fill for validate (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute`, pinned at 27,400 B. Base main 9120883a9 (0.67376, 3,124 slots, M 2,249, two
`read_volatile(holder_key)` placeholders in `validate`). Wave-15 lane, continued in wave 16. Continues w15a01-cto-devolfill
(#3710, `devol-dmaxf.patch`), w14a115-cto-devol338st (#3510), w14a138-cto-devolpair (#3618) and w14a110-cto-devol338 (#3485).
Ledger approach `devolrepay`, keys `0x22a10-w15-9120883-devolrepay-*`.

M is the count of matched masked tokens against the original window (difflib, call/lddw immediates masked);
ratio = 2M / (6676 + (bytes - 27400) / 8). Main is M 2,249.

## Result

| build | bytes | M | ratio | slots | normalized / raw | fill in validate |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| main 9120883 | 27,400 | 2,249 | 0.67376 | 3,124 | 1034 / 1034 | 2 `read_volatile` |
| V_d_maxf (w15a01, `st.max_fee=f;` at 338) | 27,400 | 2,248 | 0.67346 | 3,124 | 1034 / 1034 | 1 dead store |
| devol (`st.fee_configurable=false;` at 338) | 27,392 | 2,248 | 0.67356 | - | - | 1 dead store |
| **S_rep338 / S_mx338 (this lane, `devol-rep338.patch`)** | **27,400** | **2,249** | **0.67376** | **3,124** | **1034 / 1034, 0 losses** | **2 dead stores** |
| S_rep338 without the `let hr` binding | 27,400 | 2,235 | - | 3,122 | - | 2 dead stores |

measure.sh of S_rep338: sha `f90a5aa11174315e`, 1034 / 1034, no losses or gains, swap_hop 1.0 / 0 slots, admin_cto
0.67376 / 3,124 slots / 27,400 B: an exact tie with main and no `read_volatile` left.

```rust
  if !st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}
  let max=core::mem::replace(&mut st.max_fee,f);if f==0||f>max{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}st.fee_configurable=false;}None=>{}}
```
plus w14a115's `validate(st:&mut CtoState,..)`, `let hr=st.holder_reward;` (reused at line 298) and `let mut st` / `&mut st`.
`let max=st.max_fee;st.max_fee=f;` (S_mx338) gives the same bytes.

The window differs from main's in exactly four tokens, all of them fill:
- main 0x1580 `ldxb r1,[r10-0x6a0]` (line-334 volatile) is gone;
- the line-334 `jeq r1,0,+30` becomes `+31`;
- `stxdw [r10-0x18],r1` (f into `st.max_fee`) is inserted between `ldxdw r1,[r10-0x930]` and `add64 r1,-1`;
- main 0x1758 `ldxb r1,[r10-0x6a0]` (line-338 volatile) becomes `stb [r10-0xb],0`.

**Not landed.** Both stores write the local `st`, which nothing reads after `validate` (only `holder_reward` and `creator`
are read later), and the original window has no store into `st` (`[r10-0x38..-0xb]`) after the entry initialisation. The
two stores are dead fill that replace the two volatile fills one for one. They are plain safe Rust with no intrinsic, so
land.py's count would fall from 6 to 4, but they are the dummy-write class of the BRIEF RULE: the same class as w14a138's
Z1 (two dead stores, tie, not proposed) and w14a115's #3510 (one dead store, tie, closed). The patch is here for the
owner's decision: `cd programs/pump && patch -p1 < ../../reconstruction/pump-main/lanes/w15a29-cto-devolrepay/devol-rep338.patch`.

## Mechanism

1. **Why V_d_maxf is -1.** Exact LCS set difference main vs V_d_maxf: the only lost token is `ldxdw r1,[r10-0x930]` at
   0x1598 (the reload of `f`, original 0x1648). `st.max_fee=f` in the range-check OK block keeps `f` live past the
   two-address `add64 r1,-1`, so RA loads `f` into r2 and copies (`ldxdw r2,..; mov64 r1,r2`). The r4/r5/r0 rotation in the
   holder/shared arm that w15a01 named is M-neutral (those registers match the original in neither build). Forcing the `f`
   vreg (1694) to r1 or a spill, or the add temp (598) to r2..r5, never recovers it: while `f` stays live, at most one of
   `ldxdw r1` / `add64 r1,-1` can match (RAPRIO llc forces, `tools/force.sh`).
2. **Every no-copy store is 27,392 / 2,248.** Post-opt IR, the OK-block store value varied: 0, 1, `f-1`, `max`, a target
   piece. All remove the copy and give 27,392 B / M 2,248, i.e. devol. The fee-tag phi (the original's `mov64 r7,1`
   data flow) costs about 255 M on our RA (27,432 / 1,994 on V_d_maxf; w14a110 priced it at -276).
3. **The two fills are separable.** The 338 placeholder is the anchor that keeps the range-check OK block non-empty
   (without it the line-334 error block moves after the shared arm: -22/-23). The 334 placeholder is one instruction of
   difflib fill (+1 anywhere in validate, w14a138 insmap). Any no-copy anchor plus one extra instruction ties main.
   IR probes on the no-copy base (`tools/irprobe_fill.py`):

   | probe | edit on the no-copy base (27,392 / 2,248) | bytes | M | slots |
   | --- | --- | ---: | ---: | ---: |
   | P1 | store `f` to st+32 in the range-check block before the add; OK block `st.fee_configurable=0` | 27,400 | 2,249 | 3,124 |
   | P2 | store `fee_configurable=0` before the line-334 test; OK block keeps the `f-1` store | 27,400 | 2,249 | 3,124 |
   | P3 / P4 | two stores in the OK block | 27,400 | 2,249 | 3,128 |
   | P5 | 334 store + `f` in the OK block (copy) | 27,408 | 2,247 | - |
   | P7 | store `f` before the add, OK block empty | 27,392 | 2,226 | - |
   | P8, P9, P10, Q3-Q6 | store `f` before the add or a 334 store, plus any OK-block store | 27,400 | 2,249 | 3,124 |
   | Q1, Q2, Q7 | store `f` before the line-334 test (bb54) | 27,408 | 2,247 | - |

   Storing `f` before the add needs no copy (the store reads r1 before `add64 r1,-1`), so it supplies the fill instruction
   without disturbing RA. `core::mem::replace(&mut st.max_fee,f)` returns the old cap for the compare, which puts the store
   in the range-check block. Storing `f` before the line-334 test (bb54) makes `f` live across that test and costs a copy.
4. **No faithful single-statement fill was found.** One store (any value, any field) is 27,392 / 2,248 or, with `f`,
   27,400 / 2,248. Two statements tie. +2 would need the inserted instruction to be an original token at the right place
   (insmatch: `mov64 r7,1`, `stxdw [r10-0x918],r4`, `stxdw [r10-0x948],r3`, `ldxdw r1,[r10-0x920]` in 0x1748-0x17a0);
   stores into `st` can only produce `[r10-0x38..-0xb]` tokens, which the original's fee arm does not have.

5. **A live (read-back) anchor does not work either.** `st.cashback=false` in the OK block is semantics-preserving (the
   line-330 check already rejects `!holder&&cashback`) and becomes live if execute computes `cashback=!holder&&st.cashback`
   after `validate`. That move collapses 232 B of code: 27,168 / 1,779 (-470), and 27,176 / 1,779 with the `f` store.

## Why the original has a non-empty OK block

The original's OK block is `stxdw [r10-0x918],r4; stxdw [r10-0x948],r3; mov64 r7,1`: two RA spills of target pieces and the
fee-tag phi constant feeding the line-757 `Some(f)` test (`mov64 r7,0` on the None paths; the tag is spilled at once to
`[r10-0x8e8]`, orig 0x1998). Our IR has the two fee switch sites `bb45.i` and `bb44.i` (`icmp eq i64 %1, 0` -> `bb75`),
which are exactly the phi's two None predecessors next to the Some-OK block `bb65.i`. GVN load PRE builds such a phi of
constants when the tag is *reloaded from memory* after those switches. Ours passes `fee` as SSA arguments (`i64 %1, i64 %2`)
and tests `%1` again at line 757, so there is no phi, the OK block is empty and the placeholders stand in for it.

Price of the faithful phi on main 9120883 (`tools/phiprobe.py`, post-opt IR, both volatiles removed):

| probe | bytes | M | vs main |
| --- | ---: | ---: | ---: |
| no volatile, no phi | 27,384 | 2,226 | -23 |
| phi feeds the line-757 test | 27,416 | 1,973 | -276 |
| phi feeds line 757 and the `admin_cto_pool` CPI tag (the `%1` argument dies in validate, as in the original) | 27,224 | 2,063 | -186 at -176 B |
| phi on 757, 334 volatile kept | 27,424 | 1,973 | -276 |

The CPI form frees the register that carries `%1` to the end of the function (-192 B), the same direction as the to_string
outline repay (#3632, about +248 B). This agrees with w14a54's source forms (validate returning or out-param fee, 0.37 to
0.59) and w14a110 f1/f1b. Every ordinary form that recreates the phi on today's code shape costs 186 M or more.

## Next ideas

1. A faithful anchor needs the fee-tag phi feeding both line 757 and the pool CPI tag (-186 M at -176 B on main). Pair it
   with the to_string 312/307 outline (+248 B, #3632) and the RA repairs from w15a24/w15a18 as one joint move, not alone.
2. If the owner accepts dead stores as fill, `devol-rep338.patch` lands as an exact tie (land.py `--allow-neutral`).
3. A store-free +1 instruction in 0x6d8-0x18d0 still ties with the 338 placeholder kept (w14a138 insmap); no ordinary
   spelling found by w14a95 / w14a138 / w15a01 / this lane adds exactly one instruction there.

## Tools (experiment only; paths point at this lane's `$OUT`)

- `tools/pv.py`: post-opt IR text edit + stock llc + M (about 2 s, no build slot).
- `tools/irprobe_fill.py`: the P / Q fill probes above on the no-copy base.
- `tools/phiprobe.py`: the faithful fee-tag phi price on main's post-opt IR.
- `tools/mdiff.py`: exact LCS matched-set difference of two windows (finds the lost token).
- `tools/force.sh`: RAPRIO private llc colour forces (w14a84/w14a120 `llvmb/bin/llc`).
- `tools/genes_w16.py`: the source genes (`devol`, `rep338`, `mx338`, `rep338q`, `devol_nohr`) as exact replacements.
