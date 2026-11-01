# w17a29-shim-feetagpt: the original's single fee-tag phi on main (admin_cto 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. Wave 17 shim track.
Base: main 53ec7fb53 (origin/main 5e05222b5, `programs/` identical): 0.68754, M 2,295, 3,096 slots, 27,400 B.
Continues w16a24-cto-s3feephi (#3957; its next ideas 1, 2 and 4) with w17a15's passthrough fold.
Ledger approach `feetagpt`, keys `0x22a10-w17-53ec7fb-feetagpt-<cell>-v1`.

`M` = scorer matched tokens (ratio = 2M / (6676 + (bytes - 27400)/8)). Every number below comes from the exact slim
pre-opt oracle (w17a06 `capraw.py` + `preslim.py` + `fx.py`, survivor list `surv-1647da0.txt`), which reproduces main
(M 2,295 @27,400, sig `61dcfe87f489`) and, for `foje`, the real `measure.sh` build (0.68683 @27,432).

**Result: notes only, nothing landed. The kill test does NOT fire: the single fee-tag phi is realised in source and,
with one more marked shim (a 1:2000 weight on quote_locked's native-quote test), `foje` is 2,294 @27,432, 1 M below
main, with the original's 757 test shape. It prices level with main (Mperm 2,321, Mhc 2,329, both equal to main's), and
a short sticky RA climb reaches 2,315 @27,400 (main's own climb: 2,302 @27,400, 2,310 @27,384). What is missing is the
32 B size repay at no M cost: every shim-expressible byte cut found here stops at 27,416 B or costs 9 M or more (section 5).**

| build | M @ bytes | ratio | note |
| --- | --- | ---: | --- |
| main 53ec7fb | 2,295 @27,400 | 0.68754 | Mperm 2,321, Mhc 2,329 |
| fo (two phis) | 2,280 @27,440 | 0.68253 | |
| foj / foc (one phi) | 1,873 @27,392 / 27,384 | 0.5612 | tail-dup + MBP collapse (section 3) |
| foce (foc + native-quote weight) | 2,286 @27,424 | 0.68453 | |
| **foje** (foj + native-quote weight) | **2,294 @27,432** | 0.68683 | real build: 0.68683 @27,432, normalized 1034, raw 347 (size shift only), calls 154/3, differential 388 cases / 0 mismatches |
| foje without the 284 placeholder (fjp5) | 2,294 @27,424 | 0.68693 | the 284 placeholder is worth 0 M on this base |
| foje + RA climb (oracle only) | 2,315 @27,400 | 0.69353 | forces 1684=r7, 472=r2 (this one removes the 32 B), 2155=r9, 1631=r3 |

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

## 5. Size repay toward 27,400 B (not found)

foje against main by instruction class: +3 `mov reg,imm` (the phi constants) and +1 spill store (the phi spill), exactly
the 32 B. The original pays the same instructions (4 constant moves and one spill) inside its 27,400 B, so main carries
32 B of non-original code elsewhere (by class, main against the original: spill loads -37, other loads +30, frame
immediate stores +14, register moves +10, mov-imm -16).

| lever (on foje unless noted) | M @ bytes | note |
| --- | --- | --- |
| 338 placeholder dropped (foje8) | 2,272 @27,424 | the placeholder still carries +22 M here |
| 284 placeholder dropped (fjp5) | 2,294 @27,424 | -8 B at 0 M |
| TCF owner pin peeled (fjp4, line 659) | 2,294 @27,432 | neutral (new sig): a peel candidate on this base |
| curve-box reload peeled, shared arm (fjp1) / creator store (fjp2) / pool accounts reload (fjp3) | 2,293 @27,456 / 2,289 @27,424 / 2,153 @27,456 | |
| IR cell: volatile cashback byte in the CtoState literal | 2,293 @27,416 | source `read_volatile(&a.bonding_curve.is_cashback_coin)` does NOT reproduce it (1,782 @27,440) |
| IR cell: volatile holder_enabled byte | 2,293 @27,416 | source form 2,276 @27,416 |
| IR cell: volatile holder_reward byte in validate (line 289) | 2,284 @27,400 | source form 2,234 @27,488; beam on that base: best +1 @-8 B |
| 400 size-targeted IR combos of the -8/-16 B singles (`combo2.py`) | best 2,293 @27,416 | byte cuts saturate at 27,416 |
| foce: 300 combos to 27,400 B | best 2,281 @27,400 | |
| ptp on the accounts pointer of the `sk` load (fjsa) / of the `shared` key load (fjsb), aimed at force 472=r2 | 2,294 @27,432 (= foje) / 1,880 @27,416 | |

Beams (single shim-expressible IR edits, `screen.py`): foc 176 (stopped once the weight cell appeared), foce 984,
**foje all 2,964** (w17a06 vload/vstore/fence/bw/swbw/reread/noalias + w17a15 pt/pb), fj2 (both volatile bytes) 380,
fv (holder_reward volatile) 369, fjp5 89. On foje the only positive cells sit above the pin (`vl:execute:28714` +2 @+48 B,
`vs:execute:28713` +2 @+40 B, `vl:validate:28491` and `vs:validate:28483` +1 @+8 B, `vl:execute:29096` +1 @+16 B); the best
loss-free cut is `pt:validate:27955` (0 M @-8 B). The single-edit shim family is exhausted on foje: the repay needs RA
steering (section 6) or a multi-site rewrite.

## 6. Pricing (step 3)

| build | M @ bytes | Mperm | Mhc | short sticky RA climb (top-30 votes) |
| --- | --- | ---: | ---: | --- |
| main | 2,295 @27,400 | 2,321 | 2,329 | 1679=r7 2,302 @27,400; +2152=r9 2,307 @27,384; +1626=r3 2,310 @27,384 |
| fo | 2,280 @27,440 | 2,315 | 2,317 | |
| foc + asm diagnostic | 2,158 @27,256 | 2,258 | 2,268 | 2174=r6 +86, then 4 more: 2,270 @27,272 |
| foc (collapsed) | 1,873 @27,384 | | | 731=r9 (the sweep memcmp result, r9 in the original) 2,215 @27,272; 4 forces 2,244 @27,288 |
| **foje** | 2,294 @27,432 | **2,321** | **2,329** | 1684=r7 2,301; +472=r2 2,307 @27,400; +2155=r9 2,312; +1631=r3 **2,315 @27,400** |

Single forces on foje: **`472=r2` alone gives M 2,300 @27,400 (0.68904, above main's 0.68754)**; `472=r2,2155=r9` 2,305;
`472=r2,1631=r3` 2,303; `1684=r7` alone 2,301 @27,432. So ONE realised register choice would land this lane.

Vreg 472 is the `a.sharing_config` account pointer loaded for the `sk` copy in the validate entry block. foje:
`ldxdw r3,[r10-0x8d8]; ldxdw r3,[r3+0x90]; ldxdw r3,[r3+0x0]` (the accounts reload in r3 dies there, and r1/r2 are busy:
r2 still holds the CtoState `mayhem` byte for the `jne r2,0` test right after the copy). Original (orig 0x540):
`ldxdw r6,[r10-0x8d8]; ldxdw r2,[r6+0x90]; ldxdw r2,[r2+0x0]`, the accounts reload kept in r6.
Tried without success: ptp on the accounts pointer of the `sk` load (byte-identical) or of the `shared` key load (1,880);
`fo` declared after `sk` (byte-identical); `sk` moved before `args=&(new,)` (2,206 @27,272); volatile `st.mayhem` in
validate (IR 2,179 @27,296).

## Next ideas

1. Realise `472=r2` on foje (one force = a landing at 2,300 @27,400): free r2 at the `sk` copy (the `mayhem` byte must
   not stay in r2 across it) or keep the accounts reload live in a callee-saved register as the original does. Then
   `2155=r9` (curve pointer at entry) and `1631=r3` (a bool phi) for +5/+3 more. `1684=r7` (the accounts reload in block
   95) is the same force main's own climb wants (1679=r7 +7). The weighted Rc-trap / passthrough / lifetime families of
   w17a04/w17a15/w17a19 are the tools.
2. Re-run the volatile-byte size cells with spellings that keep the IR cell (bind-first on the same line, or a raw
   byte read `*(p as *const u8)` through `read_volatile`), since the IR cells exist at -16 B / -1 M.
3. Re-base other shim lanes on foje: main's own tuning shims are partly neutral there (TCF owner pin, 284 placeholder),
   which frees 8+ B and possibly more.
4. Once foje lands at the pin, try dropping the 338 placeholder again (foje8 is -22 on the unrepaid base).

## Tools (`tools/`, experiment only; paths point at this lane's `$OUT`)

- `variants.py`: every source variant above (line-kept replacements), for `capvar.sh`/`batch.sh` (w17a21's capture
  scripts, slim oracle) and `mkvar.sh` (crate copy for `measure.sh`).
- `irw.py`: apply an IR edit inside one admin_cto body of a slim module. `combo2.py`: size-targeted combinations of beam
  singles for a base that is not at 27,400 B. `top.py`: beam summary. `rec.py`: ledger rows.
- Beam and climb: w17a06 `gen.py`/`screen.py`, w17a15 `ptgen.py`/`screen.py`, w17a21 `rvote.py`/`climb.py`/`lx.py`,
  w17a16 `mbb.py` (final MBB order), debug llc `~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/llc`.

## Data (`data/`)

- `captures.jsonl`: every source capture (slim oracle M, bytes, signature); the spellings are in `tools/variants.py`.
- `beam_foje.jsonl` (all 2,964 singles on foje that changed code), `beam_foce.jsonl`, `beam_foc.jsonl`: id, M, bytes, sig.
- `climb_*.log`: the short sticky RA climbs (foje, main, foc, foc + asm diagnostic).
