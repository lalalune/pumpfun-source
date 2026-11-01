# w17a17-shim-docoinr8: the wallet do_coin flag in r8 (admin_cto 0x22a10, shim track)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Region W2, the wallet body (orig 0x5c18-0x6b08).
Base: main `bf01b5fd9`. `programs/pump` is identical on origin/main `d20fb326e`. admin_cto is 0.68005, M 2,270, 3,170 slots,
27,400 B. W2 has 372 of 473 tokens exact.
Ledger: approach `docoinr8`, keys `0x22a10-w17-bf01b5f-docoinr8-<item>-v1`.

**Result: notes only, no landable change.** On bf01b5f the sticky bound was still above the kill line, at +13 M for
-24 B. But no marked shim on the wallet, and no shim on the head values that compete for its registers, puts do_coin in
r8 without an RA cascade. The only landable shim found (bfn2, a fence, +1 M at 27,400 B) was absorbed by w17a15's
do_coin passthrough when main moved to ac37d74. On ac37d74 the bound itself collapses (section 4b).
The flag's register is decided by a chain of five head and tail values. The analysis below names each link with its
greedy step. It also gives the one shim-expressible lever that moves part of the chain: the Result payload phi into
r9, the original's register.

## 1. Oracle

- `ir/m0.s.ll` is w17a13's slim pre-opt capture of main (`m2`). Its `fx.py` output has **0 masked-token differences**
  from the baseline `unstripped.so`: M 2,270, 27,400 B.
- RA tools use w16a20's private RAPRIO llc (`$C/lanes/w16a20-cto-s3flagcolour/llvmb/bin/llc`), which is
  byte-identical to the SDK llc without env, and the debug llc (`$C/llvm-dbg/build/bin/llc -debug-only=regalloc`).
- `tools/rf.py <m.ll> <tag> FORCE=.. PRIO=.. STICKY=1 [--asm]` runs one RAPRIO what-if and prints M, bytes, the
  per-region exact-LCS deltas from w17a14's `rc.py`, and the W2 count. `--asm` also writes a `RAPRIO_TAG` listing,
  with the vreg of every operand.
- `tools/occ.py <ra.txt> <vreg> [n]` replays a `-debug-only=regalloc` trace up to the n-th `selectOrSplit` of the
  vreg. For each of r6..r9 it lists the assigned intervals that overlap the vreg, with weights and spans. This is
  w15a33's `dbgocc.py` idea, rewritten.
- `tools/screen2.py` is w17a06's single/pair edit screen. It adds the W2 delta and a do_coin colour count: the number of
  `mov64 r8, imm` (the original has 6, main 0).
- `tools/greedy.py` is a greedy IR beam toward a byte target. `tools/pw.py` adds `!prof` weights to post-opt branches.
  `tools/cap.sh`, `mk.py` and `edits.py` hold every source variant (exact edits, line count asserted).

## 2. Why do_coin is spilled on main (greedy chain, bf01b5f)

do_coin's root is `%1600` (an i1 phi, weight 1.80e-8, size 5,802 slots). Its only register-eligible homes are the
CSRs r6-r9, because its range crosses about 30 calls.

| step | event | consequence |
| ---: | --- | --- |
| 0-4 | `%386`, `%387`, `%0` (the accounts pointer), `%389`, `%388` take r6..r9 | `%0` sits in r8 |
| 315 | `%469` (`!holder`, the cashback AND operand that MachineSink sinks to the curve store, size 44,798) takes r9 | r9 is busy from the head to the curve store |
| 323 | the ATA AccountInfo buffer `%746` (`mov rX,r10; add rX,-1104`, which has a copy hint, so it gets priority bit 30) evicts coin_empty `%724` from r7 | buffer in **r7** (orig r9) |
| **386** | **do_coin's first dequeue**: r6 `%60` (sweep-gate flag, 4.45e-6, the whole range), r7 buffer + `%1668` (Result tag, 2.9e-4), r8 `%0` (1.5e-4), r9 `%469` (3.4e-5) | it cannot evict anything, so it goes to `RS_Split` |
| 423 | `%394` (w 4.9e-4) evicts `%0` from r8 | r8 is now free over the wallet |
| 435 | the Result **payload** piece `%1667` (w 4.3e-4; it is the collect result word `[_41+16]` at 27760 and the return phi) takes r8, the first free CSR, because r9 holds `%469` | payload in **r8** (orig r9), over do_coin's `[27760,28512)` |
| 1173 | `%0` is split; its wallet piece `%1682` takes the first free CSR, **r8** (r6 do_collect, r7 buffer) | accounts in r8 (orig r7) |
| 1429 | do_coin's second dequeue (`RS_Split`, no eviction): r8 holds `%1682` + `%1667`, r9 the gate-flag piece `%1745` | region split, `%1874` spilled: 3 stores to [r10-0x928] |

Priority what-if (`PRIO=1600=2684358950`, so do_coin is dequeued right after step 423): do_coin **gets r8** at
`RS_Assign`. At step 435, `%1667` then evicts it, because r9 is still held by `%469`. So the original colouring needs
the payload phi in r9 first, which needs `!holder` out of r9. That is w15a33's `1657=r9` lead and w15a12's `465`
lead: one chain, not three.

## 3. Bounds (RAPRIO what-ifs on the exact main module)

| force | M | bytes | W2 exact | note |
| --- | ---: | ---: | ---: | --- |
| main | 2,270 | 27,400 | 372 | |
| **h8**: sticky `1600=r8`, `1598=r6` (do_collect), prio `1600=1000` | **2,283 (+13)** | 27,376 | 388 (+16) | accounts r7 (orig), buffer spilled (orig r9), gates still `xor/and` |
| h8 + buffer `746=r9` | 2,029 | 27,408 | 400 (+28) | T1 -98, TL -101 |
| h8 + `469=spill` | 2,244 | 27,352 | 383 | |
| h8 without `1598=r6` | 2,262 | 27,416 | 367 | do_collect is evicted later |
| rw7 (`if do_coin`) + h8 | 2,276 | 27,384 | 382 | both gates `and r8,1; jne`, tail-duplicated like the original |
| **`1682=r7`** (accounts piece, non-sticky) | **2,277 (+7)** | **27,400** | 379 | a zero-size, RA-only lead: buffer to r8, do_coin still spilled |
| `1667=r9` (payload) | 2,241 | 27,304 | 378 | C1 -32 |
| `746=r6/r8/r9`, `724=r7` | = main or -101 | | | the buffer's first choice is not the lever |
| `60=spill`, `1745=spill` (gate flag) | 1,949 / 1,990 | | | T1 -177 / -121 |
| `!prof` on the wallet entry branches (bb28/bb33/bb2.i79/bb4.i/bb66.i82) | 1,826-2,149 | | | the layout moves |

The bound is above the +3 kill line, so the lane continued to step 2.

## 4. Shims on the flag and on its competitors

Source variants (slim raw-IR oracle; captures in `edits.py`):

| id | shim | M | bytes |
| --- | --- | ---: | ---: |
| rw7 | gate `if do_coin` (no shim) | 2,263 | 27,400 |
| va1 | ATA create re-derives `ctx.accounts` (`read_volatile(transmute::<&&mut AdminCto,*const &AdminCto>(..))`) | 2,270 | 27,416 |
| va2 | the same re-derivation for the whole wallet body | 2,124 | 27,480 |
| cb1 | `curve.is_cashback_coin=read_volatile(&cashback)` (ends `%469`, `!holder`, in the head) | 1,824 | 27,296 |
| cb3 | `curve.is_holder_reward=read_volatile(&holder)` | 1,943 | 27,296 |
| pe2 | validate `?` through `map_err(volatile box word)` | 1,873 | 27,304 |
| pm0 | control: validate `?` written as `match` (no shim) | 936 | 22,592 |
| pv1/pv2 | volatile read (+write) of the validate error's box word before `?` | 1,709/1,710 | 27,552/27,544 |
| bfn1 | `black_box(())` fence inside the `&&` else arm (lands in both MIR copies) | 2,256 | 27,408 |
| **bfn2** | `if collection_native&&!coin_present{black_box(())}` after the do_coin line | **2,271 (+1)** | **27,400** |

bfn2 reproduces the IR cell `bf:wallet:31113` exactly (signature `f9a932c45b76`): orig 0x6118 `ja` becomes exact.
It was the only landable shim on bf01b5f, but main moved to ac37d74 (w17a15's passthrough on the do_coin gate) before
it was built. On ac37d74 the same edit changes code with no M change (2,284 = main), so it was not proposed.

The ATA re-derivation (va1) is a single volatile load from the ctx slot (`ldxdw r1,[r10-0x938]; ldxdw r8,[r1+8]`).
The accounts value is still r8, because the buffer keeps r7 and r8 is the first free CSR.

IR screen (w17a06 `gen.py` families on the slim pre-opt module; `scr/`):
- **wallet, 369 single edits:** the best is +1. `bf:wallet:31113` (+1 M, W2 +1, 27,400 B) is a fence at the head of the
  native-path `do_coin=false` block, which MIR jump threading duplicated. `vs:wallet:31490` is +1 at 27,408 B. No wallet
  edit puts do_coin in r8.
- **execute, 693 vl/vs/rr/bf single edits:** none gains at 27,400 B. The best cell is **`vl:execute:28888`**, a volatile
  load of the validate `?` residual's box word (`%123` in bb76). It moves the **Result payload phi to r9**, the
  original's register, in every wallet error stub (`ldxdw r9,[r10-0x2c8]; ja ret`, now exact): M 2,273 (+3) at
  27,304 B (-96 B), W2 +6. Other cells reach the same basin: `vl:execute:29201` (another `?` residual, 2,265 @27,312),
  and the collect `?` arm fences `bf:wallet:31246/31258` (2,249 @27,320).
- On that basin, the accounts piece `1683=r7` (RA force) gives **M 2,284 (+14) at 27,304 B, W2 +17**. Accounts are then
  r7 and the buffer r9: the original W2 colouring except do_coin, which is still spilled, because the gate flag `%60`
  now sits in r8 over the wallet (the original spills it at its def, [r10-0x8e0]).
- Pairs and a greedy beam from `vl:execute:28888` toward 27,400 B. The best pair adds `vl:wallet:30725` (a volatile
  wallet-entry accounts load): 2,278 @27,320, W2 +13. The greedy beam reaches **M 2,282 at exactly 27,400 B** (+12 on
  bf01b5f) with seven IR edits: `vl:execute:28888 + vl:wallet:30725 + rr:wallet:30725:30910 + vs:wallet:31142 +
  vl:wallet:31338 + vs:execute:28883 + bf:execute:28930`. Only the fences and `vl:wallet:30725` have known source forms.

## 4b. Main moved to ac37d74 (w17a15 passthroughs + w17a18 stitch, 0.68424, M 2,284)

Re-captured (`ir/m1.s.ll`, masked-identical to the new baseline):
- The chain is unchanged: do_coin `%1600` is first dequeued at step 389 with the same four occupants (r6 flag `%59`,
  r7 buffer `%742`, r8 `%0`, r9 `!holder` `%466`), and is region-split and spilled at its second dequeue.
- The h8-style sticky force now evicts `%0` at do_coin's first dequeue: M 2,100 @27,416. **The bound collapsed.**
  The passthrough main no longer gives do_coin a late enough dequeue for a clean r8.
- `1682=r7` is still a clean RA-only lead: **M 2,291 (+7) at 27,400 B, W2 +7**.
- The payload-r9 basin cell is now negative: `vl:execute:28999` gives 2,277 @27,312. With `1683=r7` it is 2,288 @27,312.
- Screens on ac37d74: 179 wallet passthrough cells (w17a15 `ptgen.py`), 314 wallet vl/vs/rr/bf cells, 194 mild
  `!prof` cells (p=0.35/0.65 on the 97 inlined branches) and the execute vl/vs/rr/bf family (`scr/scr_m1_exec.jsonl`).
  None beats main at 27,400 B. The best are +1 at +8..+24 B (`vs:wallet:31308/31344`).
- Ordinary `validate(..,cashback)` (so the cashback AND has a head use and is not sunk to the curve store, where the
  original stores the spilled byte -0x950 without `and 1`) collapses: M 1,509.

No source spelling of `vl:execute:28888` was found. Every rewrite of the validate `?` (match, map_err, an in-place
volatile word) changes execute's head MIR and collapses the RA (M 936-1,873).

## 5. Conclusions for later lanes

1. do_coin=r8 is the last link of a chain: `!holder` (`%469`) out of r9 → payload phi `%1667` to r9 → r8 free at
   step 435 → do_coin (dequeued after step 423) keeps r8 → accounts piece to r7 → buffer to r9. A wallet-local
   spelling or shim cannot change it (369 cells, plus w15a12's ten source forms).
2. The payload-r9 basin is shim-reachable at the IR level, but only on bf01b5f was it positive: `vl:execute:28888`
   gave +3 M at -96 B, and a 7-edit greedy reached +12 at 27,400 B. On ac37d74 it is -7. In that basin `1683=r7`
   adds +11. The `?` residual load has no source form: every rewrite of the validate `?` collapses execute's head.
3. `1682=r7` is a clean +7 M at 27,400 B on both mains, with no shim found. The lever would be a hint: `%1682` is a
   split reload of `%0` with no copy hint, so it takes the first free CSR (r8, since r6 and r7 are taken). If r8 and r9
   were occupied instead, tryEvict would pick do_collect in r6 (4.6e-8, cheaper than the buffer's 7.1e-8), not r7. Only
   a hint, or the buffer in r9, gives r7. The buffer reaches r9 only when `!holder` (`%466`) leaves r9 before step 323.
   The original does that by keeping a spilled cashback byte (-0x950), which it stores at the curve store without
   `and 1`.
4. Step 4 of the angle (S1 `orig r9 / main r3` at 0x2148/0x2220/0x2490/0x25f8) is the same payload phi: the sweep
   results' `ldxdw r9,[..]; ldxdw r7,[..]` pairs. It moves with lead 2, not with a local flag shim.
