# Two exact source reconstructions integrated without membership loss

Base: `094a06f18df738d41e77070c1a009e135671ac1a`.

PR #1539's execute-buy block scope and statement-level selections reproduce the
original 3,440-byte normalized function. PR #1565's sell-v2 reconstruction
reproduces its original 13,976-byte normalized function. The source discoveries
belong to those PRs (including #1558's earlier sell work). This lane contributes
controlled integration, independent no-loss verification and transaction replay.
Neither patch was changed to compensate for layout.

| Cohort | Normalized | Raw | New normalized matches | Raw losses |
| --- | ---: | ---: | --- | --- |
| Main control | 1,024 | 277 | — | — |
| #1539 alone | 1,025 | 276 | 0x83c00 | 0xa868 |
| #1565 alone | 1,025 | 276 | 0x144508 | 0xa868 |
| Combined, repeated | **1,026** | **277** | **Both** | **None** |

All 1,035 memberships are checked individually. The source corrections remove
8 bytes from execute-buy and add 8 bytes to sell-v2. Thus the existing Debug
forwarder at candidate 0xa7b0 again calls 0x1a24f8, with original immediate
0x32fa7. Execute-only moves the call target to 0x1a24f0; sell-only moves it to
0x1a2500. `raw-span.json` retains the actual bytes and all normalized forwarder
candidates. No artificial padding, binary editing, original-byte injection,
compiler modification or scorer changes are involved.

Both new normalized matches retain the original ordered immediate-callee
signatures: 22 for execute-buy, 80 for sell-v2. This is not a proof about all
transitive calls or all possible runtime states.

## Validation

Five normal pinned identity builds: main, each patch alone, combined and repeat.
The two combined builds produce identical complete unstripped and stripped
images. No backend stack warnings. Dependencies are reused; no cold rebuild is
claimed. Existing ordinary compiler warnings remain.

- Unstripped: `8782e053456077638080965e0b86d11376a55e01c2ff91e4ebcecb7fef233e7b`
- Stripped: `5e75c115a6997b93606edf5114a220b31f0efac0535fed8404daac805c6b8a81`

255 existing V3 buy/exact-quote scenarios and 206 existing V2 sell scenarios,
run against original, current main and combined candidate: **1,383 normally
signed transactions**, with zero differences in checked errors, account state,
events, inner instructions, return data or ordered logs excluding complete
compute-meter lines. Each image has 213 successes/42 failures for buy and
108 successes/98 failures for sell. The sell corpus includes synthetic Token-2022
transfer-fee cases. The buy corpus does not cover transfer-fee extensions or
directly force the internal payment-add overflow. No live-chain transactions.

The replay adapters use unchanged repository suites and the public historical
fixture credited to #1292 via #1368/#1479. `verify.py --signatures` independently
rechecks all retained signatures and comparisons, binds 71 source inputs, hashes
all retained artifacts, and verifies complete membership sets. It also works
under optimized Python. Passing either isolated image to its binary acceptance
gate fails for the genuine raw loss. Original/control/candidate ELF files stay
outside Git.

## Reproduce

Use the pinned SDK setup and identity recipe in `reconstruction/README.md`.
The base source archive and two patches retaining the upstream source changes allow reproduction
without relying on moving PR branches. Apply both zero-context patches with `git apply --unidiff-zero` to the extracted base,
then build the extracted `programs/pump` with `reconstruction/harness/fastbuild.py`.
The build uses locked offline dependencies; SDK/cache locations are host-local.
Compare with the unmodified `reconstruction/harness/score.py`, using a fresh
control score. To reproduce the isolated controls, apply only one patch.

From this repository checkout, with solders 0.27.1 available:

```sh
lane=reconstruction/pump-main/lanes/v3-sellv2-integration
python "$lane/verify.py" --signatures
python "$lane/verify.py" --binary /path/to/combined/unstripped.so --objdump /path/to/pinned/llvm-objdump
python "$lane/replay_buy.py" --control /path/to/control/candidate.so --candidate /path/to/combined/candidate.so --output /tmp/buy.json.gz
python "$lane/replay_sell.py" --control /path/to/control/candidate.so --candidate /path/to/combined/candidate.so --output /tmp/sell.json.gz
```

The source verifier targets this exact source cohort. Future source changes need
fresh evidence, not edited hashes on old results. Normalized equality masks call
immediates and section pointers; neither new target is a raw match. Nine original
windows remain unmatched. This does not establish whole-ELF equality, historical
source spelling, exhaustive behavior, or security qualification.

## Related work and overlap

- [#1539](https://github.com/lalalune/pumpfun-source/pull/1539) supplies the exact
  execute-buy source; it supersedes #1479's earlier partial source. That prior
  packet remains under `execute-payment-result`, explicitly historical.
- [#1565](https://github.com/lalalune/pumpfun-source/pull/1565) supplies the exact
  sell-v2 source; [#1558](https://github.com/lalalune/pumpfun-source/pull/1558)
  supplies its credited earlier work. These are tested source dependencies here,
  not independent discoveries or extra match credit beyond the composition.
- [#1554](https://github.com/lalalune/pumpfun-source/pull/1554) also composes #1539,
  with a swap change for a different local compiler baseline. That combination
  is not included or tested here; this lane uses the documented macOS/Linux
  identity recipe and pairs two fully matched functions.
- [#1669](https://github.com/lalalune/pumpfun-source/pull/1669),
  [#1518](https://github.com/lalalune/pumpfun-source/pull/1518),
  [#1419](https://github.com/lalalune/pumpfun-source/pull/1419), and
  [#1400](https://github.com/lalalune/pumpfun-source/pull/1400) concern other
  functions in shared `trade_v3.rs`. Their pending changes are not included.
- Earlier execute work: #1421, #1243, #1189; same-file #1420 and #1436 are in
  current main. #1368 retains independent historical sell validation. Fixture
  provenance remains #1292. Shared-file overlap is not a confirmed conflict.

The final file-overlap scan covered 521 open PRs. It additionally found
[#1384](https://github.com/lalalune/pumpfun-source/pull/1384) in `sell_v2.rs`
(the safe zero-only rent helper) and
[#1164](https://github.com/lalalune/pumpfun-source/pull/1164) in `trade_v3.rs`
(quote/sell fee helpers). Neither pending patch is integrated or tested here.
Nine capture checks and ten tooling tests pass; this is not full legacy CI.
