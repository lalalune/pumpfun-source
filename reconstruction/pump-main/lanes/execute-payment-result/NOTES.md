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
