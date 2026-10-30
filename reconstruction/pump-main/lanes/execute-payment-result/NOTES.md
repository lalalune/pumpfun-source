> Historical comparisons, preserved from the earlier source and concurrent review.
> The no-loss integration in ../v3-sellv2-integration/NOTES.md supersedes the
> standalone-patch merge recommendation below; it combines #1539 with #1565.

# Current-main comparison and choice (2026-10-29)

Base `094a06f18df738d41e77070c1a009e135671ac1a`; #1479 source `d6b0c3a421ac1c79b98255235f70c6cb15e2722c`; #1539 source `8803c0dff736fa99dfc2e104234f301596424da1` merged cleanly onto this base as `22dce395c1c792385249c7bdd414e52248080b85`.

| Fresh image | Normalized / raw | Execute bytes | Ratio | Lost memberships |
| --- | --- | --- | --- | --- |
| Main | 1024 / 277 | 3448 | 0.97278 | — |
| #1479 labelled result | 1024 / 276 | 3440 | 0.985782 | raw 0xa868 |
| #1539 split selection | 1025 / 276 | 3440 | 1.0 | raw 0xa868 |

**Choice: prefer [#1539](https://github.com/lalalune/pumpfun-source/pull/1539)'s split-selection implementation, not both alternative rewrites.** It recovers the complete normalized 0x83c00 target while #1479 still differs in 24 slots. Both preserve all 22 ordered original/control callee signatures. Both lose the same raw window; neither passes the no-loss gate. Keep #1479 draft as the retained partial-source comparison, not an independently merge-ready rewrite. Its old zero-loss claim is historical and does not apply to this base. No unvalidated compensating layout change is included.

Both fresh candidates independently replay 255 buy/exact-quote cases against original and current control: 765 signature-verified transactions per candidate (1,530 executions total, repeated original/control runs). Both report zero differences/regressions for errors, accounts, inner instructions, events, return data and ordered non-meter logs. Bounded fixture coverage still does not force the internal payment-add overflow or establish general equivalence.

`main094-validation.json` binds source trees, exact alternative patches, binaries, runtime inputs and compressed receipts. The two comparison files retain full memberships and callee hashes. `verify_current.py` is the existing static audit adapted to this target and its 22 calls; it deliberately exits nonzero for both observed raw losses. All three root builds have no stack warnings. No compiler/scorer changes, cold dependency rebuild, repeated-build claim or full legacy CI claim.

Other open overlaps: [#1554](https://github.com/lalalune/pumpfun-source/pull/1554) composes #1539 with swap changes for a different qualified toolchain; its native no-loss gate is unresolved and that composition is not tested here. [#1518](https://github.com/lalalune/pumpfun-source/pull/1518), [#1669](https://github.com/lalalune/pumpfun-source/pull/1669) and [#1164](https://github.com/lalalune/pumpfun-source/pull/1164) share trade_v3.rs but are not included in these candidates. Shared-file overlap alone is not a confirmed conflict.

## Historical base b08fd90 evidence

# V3 execute-buy payment result

Target `trade::v3_execute_buy`, original window `0x83c00`, 3440 bytes.

## Source mechanism

Keep the existing amount/account selection, but collect its checked-add error and the transfer result in one labelled payment block. Propagate that result once, after the block. Both error values remain unchanged, and account selection, transfers, amounts, and subsequent operations retain their order. Source line numbers are unchanged.

On base `b08fd908203a76d84c8dd68b60310582aa2c4fba`, this reduces the candidate from 3448 to 3440 bytes and raises diagnostic similarity from 0.97278 to 0.98578. It is **not a complete normalized match**: 24 aligned slots differ. The remaining difference concerns the transfer error payload load and success/error branch layout. Official memberships remain 1023/1035 normalized and 276 raw, with no gains or losses in either set. Immediate callee signatures are unchanged and match the original in order (22 calls).

## Related work and overlap

- #1421 supplies the shared-error baseline and the reduced-IR diagnosis. This is a further source change to the same function, not credit for its earlier improvements.
- #1243 and #1189 established the earlier execute-buy reconstruction.
- #1436 and #1368 concern sell reconstruction/validation in the same `trade_v3.rs` file; this change only alters execute-buy.
- #1420 changes the exact-quote caller in the same file and is included in the tested base. #1419 studies the buy caller; #1400 studies the fee helper in that file. Their scopes differ from this payment block.
- Runtime adapter and fixture derive from #1292 (`4a8336358fd5d2fd00257ef5523202222d6c8cc5`) through #1368's replay adapter. This replay selects the existing buy and exact-quote cases instead of sell cases.

## Experiments

`TRIALS.json` records 25 completed source experiments on the earlier base `3159e64`. Internal runners, reduced compiler modules, and rejected source snapshots remain local. Both the original shared-error form and a separate-select form can each recover one necessary compiler property; combining them is nontrivial. The retained labelled-result form is the best source measured here. No binary patch, original-byte injection, compiler/scorer modification, or synthetic branch hint is used in the contribution.

A local diagnostic reduced module reproduced the baseline target and demonstrated an exact normalized target after moving its success block. This is an experimental compiler model, not a source reconstruction or official gain. Its measured 0.399-second run versus the 18.8-second baseline build illustrates why it is useful for hypothesis testing; it is not a benchmark of end-to-end reconstruction throughput.

## Reproduction and limits

Use the repository's pinned identity fastbuild recipe for both base and candidate, then run the unchanged scorer and `target_metric.py` for `0x83c00` / `v3_execute_buy`. Retained memberships and hashes bind the validation outputs. Dependencies were reused; no cold dependency build is claimed.

With Python 3.12 and solders 0.27.1, run:

```sh
python reconstruction/pump-main/lanes/execute-payment-result/replay.py --control /path/to/base/candidate.so --candidate /path/to/candidate/candidate.so --output /tmp/execute-runtime.json.gz
```

The replay performs 255 existing buy and exact-quote scenarios for each of the original, base, and candidate images (765 signed transactions). It checks errors, account states, inner instructions, event payloads, return data, and ordered logs excluding compute-meter lines. This bounded synthetic-fixture coverage does not establish general program equivalence or security. The existing case suite does not specifically force the internal `pool_quote + total_buyback` overflow; that early return is reviewed structurally, not claimed as directly covered.
