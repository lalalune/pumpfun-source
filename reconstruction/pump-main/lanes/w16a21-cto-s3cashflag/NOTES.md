# w16a21-cto-s3cashflag: the original's second per-arm flag (is_cashback_coin) on top of S3

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 599891304 (admin_cto.rs as on 1f4e396b5): 0.67436, 3,141 slots, M 2,251, Mperm 2,295, Mhc 2,302, stacked
(restore-aware joint, pass 2) 2,339. S3n (w16a08-cto-basinbound, #3876, `e/S3n.py`): M 1,990, Mperm 2,289, Mhc 2,296,
stacked 2,347 at 27,416 B.
Ledger: approach `s3cashflag`, keys `0x22a10-w16-5998913-s3cashflag-<cell>-v1` (one row per distinct form, plus
`-c2-stacked-v1`, `-c5-stacked-v1`, `-c14-stacked-v1`, `-c20-stacked-v1`).

**Result: kill, notes only, no source change.** Main is still the best zero-loss measurement (0.67436 / 3,141 slots /
27,400 B). The kill test holds:
- 35 spellings give 27 distinct binaries: 21 flag forms plus 6 repay composites. All are below S3n's Mhc 2,296 (best
  c20 2,157, c5 2,150).
- The four stacked ceilings are all below S3n's 2,347 and main's 2,339: c20 2,291, c5 2,289, c2 2,272, c14 2,248.

Nothing is handed to s3flagcolour, s3sweptr9 or stitch16.

What the lane did establish:

1. **Any per-arm cashback flag deletes execute's head `let cashback=!holder&&st.cashback`.** Once the curve store reads
   the flag, the head value has no use. That costs 200-232 B (S3n 27,416 → 27,168-27,216; main → 27,176 for `c5m`).
   - S3n spills two values at the head and keeps them live to the tail: `!holder` (and 253 test, `-0x908`) and
     `st.cashback` (`-0x8f8`). The curve store reloads them as `ldxdw; ldxdw; and64; and64 1`. All of that disappears.
   - Greedy then renames from the entry. c1/c5/c14 start `mov64 r6,r5`, the original's register (main and S3n use r9).
     c5 also takes the original's r8 for `ctx.accounts`. But their arg spill slots are 0x10-0x20 shallower than the
     original's (c5: -0x908/-0x8f8/-0x8e0/-0x920; orig: -0x928/-0x918/-0x8f0/-0x938).
   - The net is about -150 M on both Mperm and Mhc. The spill permutation does not recover it, so the loss is register
     naming. The skeleton holds: the true LCS with registers, frame and jumps masked (`Lrfj`) is within -12..-2 of main.
2. **The flag's IR type decides the curve-store shape.** The original's `ldxdw r4,[r10-0x958]; and64 r4,0x1`
   (0x4aa8-0x4ab0) is an i1 phi zero-extended at the store.
   - Writing the out-param in the arms (`*cf=false` / `*cf=st.cashback`, c1-c4, c15) gives an i8 phi.
     InstCombine folds `zext(trunc(load !range))` back to the load, so the store has no mask.
   - The mask appears when the incoming values are i1 SSA bools:
     - c5: `*cf=cashback` once at the end of validate, from validate's `if holder{false}else{st.cashback}`;
     - c14/c19/c20: a per-arm tuple element in execute's arms.
   - The original's wallet arm computes `mov r3,1; jne r1,0; mov r3,0` (0xd80-0xd90), which is that same
     trunc-to-i1 (`icmp ne 0`).
   - c20 also reproduces the original's four cashback-flag writers (ours 0xb48/0x17a8/0x1890/0x18b0; orig
     0xdb8/0x1138/0x1850/0x18b8). Even so it reaches only Mhc 2,157.
3. **Layout is not the problem.** No form shows the 6 KB tail swap: S3's event read of the holder argument keeps `%0`
   live, as w16a08 predicted. The sharing call stays in place (c1 0x49b0, c5 0x4988, c14 0x4a28, c20 0x49d0; main 0x4a30).
   fuev's raw `swap` flag fires on one chunk only: orig 0x4000-0x4400, the sharing-CPI Rc-clone run, whose rfj 5-grams
   alias the TCF clone run. That is 1 outlier under w16a12's definition, not a swap.
4. **Stacked ceilings (w16a08 `full.sh`: ares restore, permhc, sticky RAPRIO climb pass 1 + 2, joint permhc).**

   | cell | p1 joint (forces) | p2 joint (forces) | forced build: L--- / Lrfj vs main | per-0x800 rfj (forced) |
   | --- | ---: | ---: | --- | --- |
   | main | 2,329 (7) | 2,339 (9) | 0 / 0 | - |
   | S3n | 2,308 (7) | **2,347** (13) | +58 / +6 | 1800 +2, 2000 +2, 2800 +3, 4000 -2, 5000 +2 |
   | c5 | 2,270 (8) | **2,289** (14) | -21 / +0 | **1000 +6, 1800 +4**, 3000 -2, 5800 -7, 6000 -3 |
   | c2 | 2,210 (6) | 2,272 (14) | -73 / -14 | 1000 +3, 4800 -3, 5000 -5, 5800 -6 |
   | c14 | 2,234 (5) | 2,248 (10) | -62 / -5 | 1000 +2, 1800 +5, 3000 -2, 4000 -2, 5800 -7 |
   | c20 | 2,257 (12) | **2,291** (18) | -85 / -1 (p1) | 1000 +3, 1800 +3, 2000 +2, 3000 -7, 5800 -4 |

   - c5, c14 and c20 all win skeleton tokens in validate's arms (orig 0x1000-0x1c00, +7 to +10 rfj). That is where the
     original computes the flag.
   - They lose them again in the post-sweep tail (orig 0x5800-0x6400, -4 to -10) and the sweep (0x3000, -2 to -7).
   - Forces: `data/forces.txt`. c5 takes the post-sweep payload in r9 (`1667=r9`) like S3n (`1739=r9`). It still ends
     58 M under S3n.
5. **Repaying the freed bytes with known faithful pieces does not help.**
   - g1 (`let creator=st.creator;` before validate, the shared arm's target from it) adds only +24 B on c5. It leaves
     Mhc at 2,136 on c5 and 2,156 on c20.
   - Fa (validate reads `args.0`, the entry copy of `new`) adds +360 B and collapses both (Mhc 1,975 / 1,620), as it did
     on w16a13's tAn2.
6. **LOO: the loss is the flag's own.** `c5m` (main + c5's flag, no S3) has Mhc 2,138, -164 against main. c5 on S3 has
   2,150, -146 against S3n. The interaction is +18, so this is not an S3 interplay.
7. **Spelling is robust.** These pairs are byte-identical:
   - c1 = c7 (only the wallet arm writes) = t1/t3 (one `&mut (bool,bool)`, whole or field-wise) = c11 (writes at the arm
     heads);
   - c2 = c8 = t2 = t4 = c12 (the same forms, with the event reading the flag);
   - c9 (`!hf&&st.cashback` after validate) = c13 (`if hf{false}else{st.cashback}`).
8. **Tail liveness (w16a12 `livecs.py`).** In every out-param form, the two cashback inputs leave the tail: the curve
   store reads one flag slot.
   - At the sweep's second `find_program_address`, main, S3n and c20 hold r9 = the bump byte (`ldxb [r1+35]`). c1, c5 and
     c14 hold r9 = `COPY $r0`. No form holds `swept` in r9, which is the original's fact.
   - At the pool gate the live callee-saved registers are: main/S3n/c20 r6+r9, c1 r7+r8, c5/c14 r6+r8.

## Screen table (raw-IR oracle on main 5998913; `M` = masked difflib matches as measure.sh counts them)

See `data/table.md` (generated by `tools/tab.py`). Rows:

- **S3n + cashback out-param:**
  - c1-c4: flag written in the arms. c3/c4 make the fee check (line 330) read `*cf`.
  - c5/c6: flag written once at the end of validate.
  - c18: flag written right after validate's `cashback` local.
- **Derived in execute:** c9/c10 (`!hf&&st.cashback` after validate).
- **Per-arm in execute's block (S3 hf kept):**
  - c14: pa1/h2p tuple on S3;
  - c19: four arms, the non-shared arm split on holder (h2f analogue);
  - c20: the non-shared arm reuses the head cashback, so the head computation stays.
- **c15:** the holder arm clears `st.cashback` (validate takes `&mut CtoState`).
- **c16:** validate returns `Result<(Pubkey,bool)>`. It collapses like S1/ft (Result layout, Mhc 1,433).
- **c5m:** the LOO control (no S3).
- Every `e` suffix is the same form with the event's `is_cashback_coin` read from the flag instead of the curve re-read.

Flag spill slots (`data/slots.txt`):

- Original: hf at -0x950 (5 writers), cf at -0x958 (4 writers, and-1 load).
- S3n: hf at -0x900 (2 writers), cashback recomputed.
- c5: hf -0x900, cf -0x8e8 (and 1).
- c14: hf -0x928, cf -0x8f0 (and 1).
- c20: hf -0x918, cf -0x940 (and 1, 4 writers).

## Next (untried here)

- The original carries this per-arm flag and is still 27,400 B, so it spends roughly the 230 B the flag frees on
  something we lack.
  - g1 and Fa do not supply it (section 5): g1 is +24 B on c5 and Fa collapses.
  - Untested: the duplicated non-shared arm (#3435), and a per-piece Fa that copies only `new`'s 7/8/8/8/1 pieces (orig
    0x4e8-0x538, about 88 B) without routing validate through `args.0`.
- The original tests holder as `and64 r8,1` on the hopt spill inside validate (orig 0x610-0x618) and computes no `!holder`
  at the head. That is the and-1 basin that w16a08 closed as a base. It was never combined with a per-arm cashback flag,
  and the flag removes exactly the head `!holder` spill that the and-1 basin would also have to remove.
- c5's forced build ties main's rfj skeleton and gains in validate. Its losses are in the post-sweep tail
  (orig 0x5800-0x6400) and the sweep (0x3000). A lane that finds the tail lever should re-price c5/c20 against S3n.

## Tools (`tools/`, experiment only)

- `mk.py`: edit sets = S3n's 7 edits + the cell's edits, applied in order, line count kept (`e/*.py`).
- `tab.py`: the screen table. `rec.py`: ledger rows. `pairdiff.py`: skeleton-masked difflib of two candidate builds.
- The pipeline is w16a08's `t2/` and `t84/` (cap.sh, capq.sh, rx.py, mp.sh, stack.sh, full.sh, rpipe.sh, rpass2.sh),
  copied to this lane's `$OUT` with paths rewritten. It also uses w16a12's `livecs.py` and w16a09's `fuev.py`.

Kept in `$OUT` (`~/.cache/pumpfun-reconstruction/lanes/w16a21-cto-s3cashflag`):
- raw-IR captures `ir/c5.ll` and `ir/c20.ll`;
- post-opt slim modules `rx/{c2,c5,c14,c20}/m.ll`;
- every cell's `fn.bin`/`pei.mir`;
- the force sets and joint builds in `cm/` and `rx/*__ra`.
Every other capture can be regenerated from `e/<cell>.py` with `t2/cap.sh`.
