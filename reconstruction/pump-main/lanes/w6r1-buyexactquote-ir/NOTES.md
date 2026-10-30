# Lane w6r1-buyexactquote-ir (wave 6, round 1): IR-oracle loop on `0x1489f8`

Target: `0x1489f8` `pump_recovered::trade::buy_exact_quote` (v3), original 7856 B.

Base: origin/main a56331f50. Its programs tree is the same as 099b0dd (1027 normalized / 276 raw; unstripped sha
`d9484de7...`): 7768 B, ratio 0.66033, llc-oracle masked 0.8928.

The sibling lane `w6r1-buyexactquote-sem` (PR #2170) reached 0.84304 (fa4d2db) and then 0.84409 (9ed6831, masked
0.9627) while this lane was running. Most of the oracle work below was therefore re-run on the sibling's state, so the results apply
to the current frontier. This lane has no source change of its own that beats #2170. The PR from this lane carries
analysis and tools only.

## Tools (`scripts/`, lane-local, never used for proposals)

- `capture.py` / `capture_raw.py`: fixed for the current `fastbuild.py`, which now compiles through
  `build_process.run_compiler` rather than `subprocess.run`. The hook now wraps `fastbuild.run_compiler`. `capture_raw.py SRC WORK OUT -C no-prepopulate-passes`
  gives rustc's pre-optimization IR. Copy `deps/pump_recovered.ll` out by hand, because the raw build "fails" at the link check.
- `rawedit.sh NAME EDIT.py`: applies `edit(text)` to the raw IR (`$RAW`), then runs `opt -O3` and the llc oracle, and prints ratio, masked ratio and
  the prologue lea line. Takes about 10 s. Edits: `e_nolt.py` (X=a,b strips all lifetime markers of those body allocas),
  `e_delline.py` (DEL="n ..." deletes body-relative lines), `e_ltpos.py` (MODE=noend|nostart|startfirst).
- Post-opt edits for `ir.py`: `phiswap.py` (PS=block swaps the `_0` phi pair), `ltadd.py` / `ltdummy.py` (extra entry
  lifetime.starts), `e_sub.py` (SUBS=file with (old,new) pairs inside the target function).
- `buckets.py orig cand [m]`: diff slots per 50-instruction region of the original.
- `hc.py`: post-opt single-block-move hill climb on a slim module.

The no-op raw-opt and post-opt oracles reproduce fastbuild exactly on base, sem and sem2.

## Findings

### On base (0.66033)
1. **Prologue lea** (`prepare_bonding_curve` sret lea; original early, ours late). This is the same list-ilp critical-path
   mechanism as sell_v3 (#1549). Entry chain nodes ahead of the ctx.accounts load: we have 1 (`val.sroa.5.i`). Duplicating it gives lea early at 4 total
   nodes and late at 2 or 3, but the duplicates change stack coloring (0.6392). Stripping markers from any single body alloca (a 202-alloca scan)
   never moves the lea. Stripping quote_fee+fees+post together moves it early: 0.6624 / masked 0.8970.
2. **fees slot**: the original passes `&fees` to v3_emit_buy from T=0x160 (the val.sroa.5 group). Ours uses T=0x40 (the formatter group).
   b01 (`let (amount,quote,fees,post,costs);(..)=if ..`) broke the frame (0.3414). a01 (`let (fees,post)=(fees,post);`)
   gave 0.3233.
3. All 11 missing instructions are spill, reload and copy instructions (`ldxdw fp` +7, `stxdw fp` +2, `mov rr` +2). Calls, branches and ALU ops match.

### On sem (fa4d2db, 0.84304) and sem2 (9ed6831, 0.84409)
4. **Phi order is no longer a lever.** Swapping the `_0` pair at the quote_fee exit join now loses (0.6320). ctx is already in r6.
5. **quote_fee error-exit lifetime.end (+0.064).** The raw IR has quote_fee lifetime.end in `bb193` (normal path) and in `bb113`
   (the shared error-return join). Deleting only the `bb113` end gives 0.9071 on sem and 0.9081 on sem2, with masked unchanged.
   Deleting only the normal-path end, or only the start, does not help (0.8430 / 0.8346).
   With no end in the join, SimplifyCFG merges the post-quote_fee error returns into the final exit (16 preds), and register
   assignment matches the original much better.
6. **quote_fee + post unmarked**: on sem2, 0.9149, masked 0.9685, 952 insns (the original's count), **and the lea becomes early**.
7. Hill climb (post-opt, sem): the best single move creates the net_quote_for_budget Err stub (`bb137.i`) after the
   non-whitelist try_from block (`bb140.i`): 0.8430 -> 0.8567. A second round adds only bb57>bb68 (0.8576).
8. The original copies quote_fee's payload with all loads grouped before the stores, in descending order, and the is_sol load comes first. Ours interleaves.
   A post-opt oracle 24-byte memcpy (s3) does not reproduce this (0.8409). Moving or deleting the `_44` lifetime.end does not either.

### Why 5 and 6 have no source spelling yet
In rustc 1.79, CopyProp removes StorageLive/Dead only from the **head** of a non-trivial copy class. It never replaces a
borrowed non-head member. `quote_fee` is always `_42 = copy _536`, where `_536` is the SRoA field of the `?` val.
`post` is `_103 = copy _533`, the if-result temp. Both are borrowed non-heads, so they keep their markers in every
spelling tried. The variants were: deferred declaration (x04), declaration before 881 (g01), declaration at the top (g02), match instead of `?` (m1-m4),
and a fill function that takes quote_fee by value (f01: 7856 B, but 0.8424, because the inliner puts the end at the fill
exit and a separate join remains). Arguments have no markers, but an LLVM-inlined callee still ends the caller's
local after the call returns.

## Trials (ledger keys `0x1489f8-main-a56331f-*`)

| trial | state | mechanism | bytes | ratio | masked | result |
| --- | --- | --- | ---: | ---: | ---: | --- |
| a01 | base | `let (fees,post)=(fees,post);` | 7768 | 0.3233 | 0.7998 | rejected |
| b01 | base | deferred `let (amount,quote,fees,post,costs);` + destructuring assignment | 7760 | 0.3414 | 0.7992 | rejected |
| f01 | sem | `buy_exact_quote_fill(.., quote_fee:Option<Fee>)` inline(always) split | 7856 | 0.8424 | 0.9601 | rejected |
| g01 | sem | quote_fee declared before the 881 check | 7864 | 0.8347 | 0.9596 | rejected |
| g02 | sem | quote_fee declared at the body top | 7864 | 0.8347 | 0.9596 | = g01 |
| m1/m3 | sem | check_quote via `match{Ok(v)=>v,Err(e)=>return Err(e)}` (deferred) | 7880 | 0.6702 | 0.9072 | rejected |
| m2/m4 | sem | same as m1/m3, non-deferred | 7888 | 0.6205 | 0.9088 | rejected |

Oracle rows: `ir-oracle-entry-lifetime-lea`, `ir-oracle-sem-quote-fee-error-end`, `ir-oracle-sem2-unmark-quote-fee-post`,
`ir-oracle-sem-hc-block-order`.

## Next ideas
- A source shape where quote_fee (and post) carry no StorageDead on `?` error returns. Two candidates: make each the head of a copy
  class, by assigning it straight from a projection and then copying it into a non-borrowed SSA local; or have GVN reuse it
  (GVN's StorageRemover strips every marker of a reused local). Check each candidate in seconds with `capture_raw.py` plus a grep for
  `lifetime.end.p0(i64 32, ptr %quote_fee)` in the error join.
- Create the net_quote_for_budget Err stub after the Ok chain (hill-climb move, +0.014).
