# w17a29-shim-feetagpt: the original's single fee-tag phi on main (admin_cto 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. Wave 17 shim track.
Base: main 53ec7fb53 (origin/main 5e05222b5, `programs/` identical): 0.68754, M 2,295, 3,096 slots, 27,400 B.
Continues w16a24-cto-s3feephi (#3957; its next ideas 1, 2 and 4) with w17a15's passthrough fold.
Ledger approach `feetagpt`, keys `0x22a10-w17-53ec7fb-feetagpt-<cell>-v1`.

`M` = scorer matched tokens (ratio = 2M / (6676 + (bytes - 27400)/8)). Every number below comes from the exact slim
pre-opt oracle (w17a06 `capraw.py` + `preslim.py` + `fx.py`, survivor list `surv-1647da0.txt`), which reproduces main
(M 2,295 @27,400, sig `61dcfe87f489`) and, for `foje`, the real `measure.sh` build (0.68683 @27,432).

**Interim result (notes only so far): the single fee-tag phi is realised in source and, with a 1:2000 weight on the
native-quote test, sits 1 M below main (`foje` 2,294 @27,432, the original's 757 test shape). It is 32 B over the pin; the
size repay is in progress (section 5).**

## 1. The original's fee data flow (Ghidra J1, w16a24 section 1)

| item | original | main 53ec7fb |
| --- | --- | --- |
| fee tag | ONE phi of constants in r7: `mov64 r7,1` in the range-check OK block (orig 0x1810), `mov64 r7,0` on the None paths (0x0e48, 0x1108, 0x14f8), spilled `stxdw [r10-0x8e8],r7` (0x1998), reloaded for the 757 test `ldxdw r1,[r10-0x8e8]; jne r1,0; ja` (0x4b80) and the pool tag `[r10-0x1000]` (0x4dc8) | the entry tag `%fee.0` (`stxdw [r10-0x908],r4` at entry), tested `jeq r1,1; ja` at 757 |
| fee value | entry value, slot `[r10-0x930]`, for the 757 store (0x4ba0) and the pool value `[r10-0xff8]` (0x4dd8) | same |
| OK block | `stxdw [r10-0x918],r4; stxdw [r10-0x948],r3; mov64 r7,1` | `ldxb r1,[r10-0x6a0]` (the line-338 `read_volatile` placeholder) |

## 2. Spellings of the single tag phi (source captures)

`fo` = w16a24's out-param: `let mut fo:Option<u64>=None;` in the validate block, `validate(..,fo:&mut Option<u64>)`,
`*fo=Some(f)` after the range check, line 757 and `pargs.2` read `fo`. The passthrough helper (line 8, no new line):

```rust
#[inline(always)]unsafe fn pto<const N:u32>(o:Option<u64>)->Option<u64>{let mut r=o;let p=&mut r as *mut Option<u64> as *mut u64;*p=pt64(N,*p);r}
```

| cell | spelling | M @ bytes | phis reaching llc | note |
| --- | --- | --- | --- | --- |
| main | | 2,295 @27,400 | entry tag, no phi | Mperm 2,321, Mhc 2,329 |
| fo | out-param | **2,280 @27,440** | i1 phi (757) + i64 phi (pool) | -15 on this main (was -201 on 5998913): V -2, C1 -13; Mperm 2,315, Mhc 2,317 |
| fo8 | fo, 338 placeholder dropped | 2,271 @27,432 | two | |
| foj | fo + `pto::<31>(fo)` after the validate join | 1,873 @27,392 | **one** (`icmp eq tag,1`) | byte-identical to the llc-only single-phi oracle (fo IR, i1 phi replaced by `icmp ne/eq` or `trunc` of the i64 phi) |
| foc | fo + OK constant through pt: `*fo=transmute([pt64(32,1),f])` | 1,873 @27,384 | **one** (`icmp eq tag,0`) | `focb` (before the placeholder) identical |
| fos757 | pt only at the 757 test | = foj | one | |
| focs2 / focsc2 | None init `[pt64(33,0), uninit]` (+ OK pt) | = foc | one | value word `0` instead of uninit adds a value phi: 2,070 |
| foj8 / foc8 | 338 dropped | 1,850 | one | |

So the single phi is source-realisable (the w17a15 fold: a pt on the tag word keeps InstCombine from splitting it), but on
main it collapses to 1,873 (T1 -306, tail -123).

## 3. Why the single phi collapses: a post-RA tail duplication flips block placement

Debug llc (`-debug-only=block-placement`, `-print-before=block-placement`) on fo against the single-phi oracle:

- The 757 branch weight is NOT the cause. The single phi gets the BPI zero heuristic (62.5/37.5) instead of fo's
  50/50, but explicit 1:1, 5:3, 3:5 and 2000:1 weights all give the same collapsed signature.
- The wallet exit test block `bb55.i89` (the join of the two CPI `?` results, then `jeq r7,2`) is
  `dead $r1 = LDD [r10-0x8e0]; JEQ r7,2; JMP` in fo: 3 instructions. That dead reload is a split piece of the phi
  spilled at `[r10-0x8e0]`. With one tag phi the greedy RA splits differently, the dead reload disappears, the block is 2
  instructions, and post-RA tail duplication copies it into its single-successor predecessor `bb85.i`. MBP then chains the
  error-return chunk `[bb5.i bb3.i.i95 bb2.i bb3.i.i68 bb74]` after `bb89.i` (position 176 instead of 251).
- The original keeps the same dead reload in its wallet exit test: orig 0x3b80 `ldxdw r8,[r10-0x8d8]; ldxdw r1,[r10-0x8e0];
  jeq r7,0x2,0x1fb8`.
- Diagnostic (not source): an empty inline asm in IR `bb55.i89` blocks the duplication. Layout then equals fo's except one
  block, and foc reaches 2,158 @27,256 (foj 2,161 @27,264; fo unchanged). The rest of the loss is register naming in T1
  (T1 -105 exact, -2 at m3). mp.py: Mperm 2,258, Mhc 2,268.
- RA-only climb (private RAPRIO llc, sticky) on foc: `731=r9` alone lifts 1,873 to **2,215** @27,272. Vreg 731 is the
  sweep's `q==native_mint` memcmp result; the original holds it in r9 (orig 0x5be0 `mov64 r9,r0 .. jeq r9,0`), main in r7.
  Four forces reach 2,244 @27,288. On main the same force (727=r9 sticky) collapses to 2,066: the single-phi basin and
  main's basin want opposite registers there.

## 4. The zero-footprint placement fix: a 1:2000 weight on quote_locked's native test

An IR beam over shim-expressible single edits on foc (w17a06 `gen.py` + w17a15 `ptgen.py`, 2,955 edits, `screen.py`)
found that a 1:2000 weight on execute's `q==native_mint::ID` branch inside `quote_locked` (cell `bwf:execute:28810`)
escapes the collapse: **1,873 -> 2,286 @27,424**. On main the same weight is byte-identical (sig `61dcfe87f489`); on fo it is
2,281. Source (line 339, the existing `llvm.expect` extern):

```rust
let quote_locked={let q=a.bonding_curve.quote_mint;(unsafe{expect(q==Pubkey::default(),false)})/*shim: ..*/||(unsafe{expect(q==anchor_spl::token::spl_token::native_mint::ID,false)})/*shim: native-quote test weighted 1:2000 ..*/||a.global.whitelisted_quote_mints.contains(&q)};
```

| cell | M @ bytes | 757 code | note |
| --- | --- | --- | --- |
| foce (foc + weight) | 2,286 @27,424 | `ldxdw r1,[r10-0x900]; jeq r1,0,skip` | source capture = beam cell sig `f38d2bf62ba0` |
| **foje** (foj + weight) | **2,294 @27,432** | `ldxdw r1,[r10-0x900]; jne r1,0; ja` = the original's shape | real build 0.68683 @27,432, normalized 1034, calls 154/3, differential 388/0 |
| foce8 / foje8 (338 dropped) | 2,264 @27,416 / 2,272 @27,424 | | the placeholder still carries +22 on this base |

Other escaping single cells on foc: `bf:validate:27869` 2,286 @27,448, `pb:validate:27732` 2,278 @27,448,
`bwt:execute:28719` 2,232 @27,288.

## 5. Size repay toward 27,400 B

In progress.

## Tools (`tools/`, experiment only; paths point at this lane's `$OUT`)

- `variants.py`: every source variant above (line-kept replacements), for `capvar.sh`/`batch.sh` (w17a21's capture
  scripts, slim oracle) and `mkvar.sh` (crate copy for `measure.sh`).
- `irw.py`: apply an IR edit inside one admin_cto body of a slim module. `combo2.py`: size-targeted combinations of beam
  singles for a base that is not at 27,400 B. `top.py`: beam summary. `rec.py`: ledger rows.
- Beam and climb: w17a06 `gen.py`/`screen.py`, w17a15 `ptgen.py`/`screen.py`, w17a21 `rvote.py`/`climb.py`/`lx.py`,
  w17a16 `mbb.py` (final MBB order), debug llc `~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/llc`.
