# w16a24-cto-s3feephi: the fee-tag phi as a validated-fee out-param (wave 16, continued in wave 17 on the shim track)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 599891304 (merged to 1647da0f2; `programs/pump/src` unchanged), admin_cto 0.67436, M 2,251, 3,141 slots.
Ledger approach `s3feephi`, keys `0x22a10-w16-5998913-s3feephi-<cell>-v1` (22 rows).

**Result: notes only, nothing landed. The kill test holds for both the ordinary-source and the shim spellings.** No fee-tag
phi cell stacks above S3n's 2,347, none crosses main's raw M 2,251, and no placeholder-free form ties main. Main stays the
best zero-loss measurement (0.67436 / 3,141 slots / 27,400 B).

M is the scorer's masked difflib match count against the original window, and ratio = 2M / (6676 + (bytes - 27400)/8).
Every number comes from the raw-IR oracle (`tools/capg.sh`: capture pre-opt IR, SDK `opt -O3`, slim, `llc`), which equals a
real build byte for byte. Stacked pricing is w16a08's pipeline (`full.sh`: placement restore, permhc, then the
restore-aware sticky RA climb with its joint), which is how S3n's 2,347 was measured.

## 1. What the original does with the fee

| item | original | main |
| --- | --- | --- |
| fee value | entry slot `[r10-0x930]`, reloaded for the range check (orig 0x1648), the 757 store (0x4ba0) and the pool CPI stack arg `[r10-0xff8]` (0x4dd8) | the same slot and uses |
| fee tag | ONE phi of constants in r7: `mov64 r7,1` in the range-check OK block (orig 0x1810), `mov64 r7,0` on the None paths (0x0e48, 0x1108, 0x14f8); spilled `stxdw [r10-0x8e8],r7` (0x1998); reloaded for the 757 test `jne r1,0` (0x4b80) and the pool CPI tag `[r10-0x1000]` (0x4dc8) | the entry tag `%fee.0`, spilled to `[r10-0x8e8]` at the entry (cand 0x10) and live to both uses |
| range-check OK block | `stxdw [r10-0x918],r4; stxdw [r10-0x948],r3; mov64 r7,1` | `ldxb r1,[r10-0x6a0]` (the line-338 `read_volatile` placeholder) |

So the original's fee data flow is: the value stays in its entry slot, and the tag is a single validated-fee phi.

## 2. Ordinary source (the wave-16 angle): `fo` on main and on S3n

`fo`: `let mut fo:Option<u64>=None;` in the validate block, `validate(..,fo:&mut Option<u64>)`, the fee arm writes
`*fo=Some(f)` after the range check, and line 757 and `pargs.2` read `fo` (`tools/genes_fp.py`).

| cell | bytes | M | note |
| --- | ---: | ---: | --- |
| main m0 | 27,400 | 2,251 | `eq_main` |
| fo | 27,240 | 2,050 | byte-identical to w16a12 `ftc` (so `ftt`) |
| fo8 (fo, 338 placeholder dropped) | 27,232 | 2,060 | the phi constant now fills the OK block: +10 on fo, still -191 |
| fo84 (both placeholders dropped) | 27,224 | 2,063 | no placeholder-free tie |
| foT (fo x tail union T) | 27,304 | 1,863 | |
| S3n (w16a08) | 27,416 | 1,990 | stacked 2,347 |
| s3fo | 27,296 | 1,949 | Mperm 2,159, Mhc 2,165; RA pass 1 (7 forces) M 2,104, joint Mhc **2,210** (S3n: 2,204 / 2,308) |
| s3fo8 / s3fo84 | 27,472 / 27,464 | 1,581 / 1,581 | collapse |
| s3foT | 27,248 | 1,916 | Mperm 2,104, Mhc 2,126 |

Per orig-0x800-chunk true LCS (`data/evc3_fo.txt`): under rfj masking fo loses only 63, 45 of them at orig 0x4800. S3n+fo
loses 17 (rfj) but 216 unmasked, so on S3 the fee phi is register and frame naming, not structure.

## 3. Why `fo` loses: two mechanisms

**(a) InstCombine splits the tag phi in two.** fo's optimized IR has `%fo.sroa.0.0 = phi i64 [0,1,0]` for the pool tag and
`%trunc45 = phi i1 [false,true,false]` for the 757 branch. The original keeps ONE tag (r7). An `llc`-only IR oracle that
deletes the i1 phi and branches on `trunc` of the i64 phi (`ll/*_1phi.ll`):

| cell | M (two phis) | M (one phi) | gain |
| --- | ---: | ---: | ---: |
| fo | 2,050 @27,240 | 2,084 @27,240 | +34 |
| s3fo | 1,949 @27,296 | 2,043 @27,288 | +94 |
| s3foT | 1,916 @27,248 | 2,014 @27,216 | +98 |
| foT | 1,863 @27,304 | 1,973 @27,192 | +110 |

The split happens for ANY cast or compare user of a constant-incoming phi. `zext i1` of a flag phi folds into a new i64 phi
(`s3fbx`), and an Option rebuilt from the flag folds back to fo exactly (`s3fbo` is byte-identical to s3fo).

**(b) On main, fo flips the block placement at the sharing test.** The curve-update block (lines 752-759) is laid out right
after `match sharing_update` (fo cand 0x3ce0, `jne r1,2,+0x3a`), and the sharing CPI then jumps back to it
(`jeq r7,2,-0x1e0`). Main and the original put it after the CPI (orig 0x4ab8). That is the rfj -45 at orig 0x4800. Branch
weights on that test (2000:1, 3:2, 2:3) leave the block where it is, and 1:2000 moves the CPI to 0x6330 (0.57134). The IR CFG
there is identical to main's, so the flip comes from codegen. On S3n+fo the flip does not happen (rfj +4 at 0x4800).

## 4. Shim track (wave 17): one flag phi

The owner's 2026-11-01 decision allows marked steering constructs in admin_cto.rs. `tools/genes_fb.py`:

- `fb`: `let mut fb=false;` out-param set by the validated arm (`*fb=true` after the range check). Line 757 is
  `if fb{curve.creator_fee_bps=unsafe{fee.unwrap_unchecked()}/*shim: ...*/;}`, and `pargs.2` is
  `if fb{Some(unsafe{fee.unwrap_unchecked()}/*shim: ...*/)}else{None}`. `unwrap_unchecked` runs only under the flag, so it adds
  no UB. The fee tag dies in validate, and the value stays in its entry slot.
- `fbx`: `pargs.2` transmuted from `[fb as u64, transmute::<Option<u64>,[u64;2]>(fee)[1]]` (no branch).
- `fbo`: one `Option` rebuilt from the flag on line 752, read by both 757 and `pargs.2`.
- `fe`: fo with `*fo=fee;` (the whole argument, which is `Some(f)` in that arm).

| cell | bytes | M | IR |
| --- | ---: | ---: | --- |
| fb | 27,288 | 2,080 | one i1 phi (`%fb.not`) for 757; the pool tag is rebuilt through a branch and a new phi (+48 B against the oracle) |
| s3fb | 27,352 | 2,036 | +46 over S3n raw, +87 over s3fo |
| s3fbx | 27,288 | 1,946 | zext folded into a second phi |
| s3fbo | 27,296 | 1,949 | byte-identical to s3fo |
| fe | 27,392 | 2,244 | LLVM folds the phi back to `%fee.0`: main's data flow (no tag phi) at -8 B, -7 M |
| s3fe | 27,408 | 1,989 | S3n at -8 B, -1 M: a size knob for the S3 repay, not the fee phi |
| fb8 / s3fb8 (338 placeholder dropped) | 27,280 / 27,536 | 2,057 / 1,589 | fb8 is 23 below fb; S3 + d338 collapses again, as s3fo8 does |

Stacked pricing (w16a08 pipeline):

| build | bytes | M | Mperm | Mhc | RA pass 1: M (forces) / joint Mperm, Mhc | RA pass 2: M (forces) / joint |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| S3n (w16a08) | 27,416 | 1,990 | 2,289 | 2,296 | 2,204 (7) / 2,308 | 2,273 (13) / **2,347** |
| s3fo | 27,296 | 1,949 | 2,159 | 2,165 | 2,104 (7) / 2,196, 2,210 | - |
| s3fo1p (IR oracle: one tag phi) | 27,288 | 2,043 | - | - | 2,157 (7) / 2,236, 2,241 | climbing at the time box: M 2,263 @27,256 after 4 rounds (11 forces, +1928=r9 +238=r5 +1695=r6 +337=r2); joint pending |
| s3fb (shim) | 27,352 | 2,036 | - | - | 2,125 (12) / 2,237, 2,253 | not run (time box) |

Pass-1 forces: s3fo `1674=r9,476=r2,1882=r6,220=r9,1693=r7,1686=r8,1989=r5`; s3fo1p
`1669=r9,475=r2,2002=r2,1681=r8,1713=r4,1709=r3,1719=r6`; s3fb `1968=r5,1697=r7,1700=r6,1699=r6,1693=r7,473=r2,217=r1,
1690=r8,1637=r4,1638=r4,1727=r6,1719=r3`. The `1669/1674=r9` force has the same signature as S3n's `1739=r9` (max_fee
in r9 through validate, w16a18).

## 5. Kill test

- S3+fo stacks at RA pass 1 2,104 / joint 2,210, against S3n's pass 1 2,204 / joint 2,308 and pass 2 2,347. **Below.**
- fo x T on S3 (s3foT) has Mhc 2,126 before any forces. **Below** ftcT's 2,342.
- No placeholder-free form ties main (fo8 2,060, fo84 2,063, fb8 2,057).
- Shim spellings: the best one, s3fb, is +46 over S3n raw. At RA pass 1 it stacks to a joint Mhc of 2,253, 55 below S3n's pass-1 joint of 2,308. The merged-phi oracle reaches 2,241 at pass 1. Neither comes near S3n at the same stage. **Kill.**

## Next ideas

1. The original reaches InstCombine with a tag phi that has no cast or compare user, or with a non-constant incoming value
   that only becomes a constant after InstCombine's last run. `fe` shows that an incoming `%fee.0` is folded away
   completely, which is too far. A spelling whose OK-path incoming value is proven equal to 1 only by a late pass (for
   example the `Some` arm's own discriminant read after a call) would sit between fe and fo. It is untested.
2. The block-placement flip on main+fo (section 3b) is codegen-only. It needs a check of which `MachineBlockPlacement`
   input changes (block frequency of the curve-update join) before any source lever is tried.
3. For the S3 lanes: `fe` is a -8 B knob at -1 M on S3n (s3fe 27,408), and `fb` raises S3n's raw M by 46.

## Tools (experiment only; paths point at this lane's `$OUT`)

- `tools/genes_fp.py` (fo, fob, d338, d334, S3n via w16a08 `e/S3n.py`) and `tools/genes_fb.py` (fb, fu, fbm, fbx, fbo, fe).
- `tools/capg.sh <name> <gene,...> <slot>`: copy the crate, apply genes (line count kept), capture pre-opt IR, run the rx oracle.
- `data/evc3_fo.txt`: per-chunk true LCS of fo, fo8, s3fo and S3n against main. `data/rx_results.txt` and
  `data/ir_oracles.txt`: the oracle results.
