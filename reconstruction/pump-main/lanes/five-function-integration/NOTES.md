# Five source improvements integrated without membership loss

At main `094a06f18df738d41e77070c1a009e135671ac1a`, three complete normalized matches were blocked individually by a shared raw-call span. Compose the independently closer Create/Sweep sources with the three exact caller reconstructions. This ordinary four-file Rust change preserves every previous membership: **1,024→1,027 normalized; 277 raw**, across all 1,035 original windows. Eight windows remain unmatched.

| Original target | Main bytes | Combined bytes | Original bytes | Instruction alignment |
|---|---:|---:|---:|---|
| CreateV2 `0x1e7c0` |15632|15584|15576|.75114→.80237(partial)|
| Sweep `0x72810` |7824|7880|7832|.49139→.88669(partial)|
| Execute buy `0x83c00` |3448|3440|3440|.97278→1|
| SellV2 `0x144508` |13968|13976|13976|.97578→1|
| BuyV3 `0x147ba0` |3680|3672|3672|.93138→1|

The real source deltas total zero: −48 +56 −8 +8 −8 bytes. Actual `.text` remains 1,792,024 bytes; `.rodata` is unchanged. Two fresh generic builds produce identical complete stripped/symbol images. No emitted padding or ballast, emitted-byte editing, injected original code, compiler/scorer changes or extra emitted helpers.

Source credit: #1539/#1565 (and #1558) to Shaw/lalalune + Claude Opus 5.5; #1479 integration to Oz-0s, retaining Jonas/SORC3r3r comparison evidence; #1669 full Buy to thegeronimo, crediting #1419 analysis; w4 Create/Sweep to Shaw + Claude. This PR contributes the qualified composition. Create is the one fixed inferred reconstruction: `76f7319` source plus the literal 16-assignment `ed/v13.py` permutation from `f339b9d`; its historical input binding was not recovered; the new actual build supplies its evidence. Sweep is #1548's s6. #1669's load-order and full-match patches are both included. Exact provenance is retained in `records/selected-audit.json.gz`.

## Validation and limits

All 70 primary and 71 actual staged compiler inputs are bound separately; generated workspace manifests are retained. Official and independent physical-function censuses preserve every prior normalized/raw membership, deduplicate aliases and preserve original multiplicities. Three new bodies match only after the existing narrow normalization. These are not raw target matches or whole-program identity.

Selected callees: Execute 22/22 and Sell 80/80 match original in order; Create 125/125 does too. Buy has 28/29 original callee matches: the unchanged costs helper remains 2136 versus 2120 bytes. Sweep preserves 37 direct-callee identities as a multiset and its parent's order; two linear positions differ from original, with two external calls unchanged. Forty-nine relocated references match within decoded lengths/typed fields; vtable tails and recursive call/data closure remain unproved.

Fresh focused coverage: 129 cases, 387 original/control/candidate target executions plus 102 bootstrap sends, 690 independently verified signature fields. All raw targeted reports are published, including six additional successful native/Token/Token2022 post-complete Buy/ExactBuy crossings; the earlier Overflow boundary is retained unchanged. Fresh 44-suite / 10,468-pair and 126-extension runs pass, including ordered logs with only complete runtime compute-meter lines excluded. Broad retained signature audit: 18,595 transaction fields / 28,127 signature fields; these overlap fixtures and are not execution or unique-wire totals.

**Broad raw reports are retained locally, not included in Git.** Their sizes/SHA256, complete suite, loader and input records and signature/strict audit summaries are published in `runtime-summary.json.gz`. The default verifier independently checks the public focused observations/signatures and static records; it does not independently recheck omitted broad payloads. Reproduction regenerates them with the unchanged current helpers. This is finite synthetic/captured coverage, not exhaustive behavior, security or recursive-equivalence proof. SDK/archive admissions are retained; no fully hermetic environment claim or GitHub Actions gate.

## Reproduce

Use the measured Python 3.12 environment with `pip install -r requirements.txt` (measured versions retained). The generic builder is `scripts/pump_build_verified.py`; do not substitute the old 65-input recipe. The original ELF and all captured dependency images remain at their existing repository paths.

Restore only the eight historical fixture/harness paths listed in `records/historical-inputs.json` from commit `b10bc4b53c8b615b47677e8776b338851b04ca53`. Each entry records its exact Git blob and SHA256. They are deleted from current main and ignored; they are fixture ancestry, not current-source output. For each entry, `git show <commit>:<path>` supplies its bytes; verify SHA256 before writing a missing file. Current 44+126 commands passed after precisely this restoration.

Set `PUMP_PY` to the recorded Python environment, `PUMP_SDK` to the admitted native macOS v1.44 SDK, `PUMP_REGISTRY` to its locked registry, `PUMP_LIBS` to the 25 pinned official Linux v1.44 SBPF libraries, and fresh output paths under `work/`. Build current source and repeat with separate output directories:

```sh
"$PUMP_PY" -B scripts/pump_build_verified.py --source-directory programs/pump --sdk "$PUMP_SDK" --registry-home "$PUMP_REGISTRY" --workspace-layout --target-library-profile linux-v1.44-sbpf --target-library-directory "$PUMP_LIBS" --output "$PUMP_UNION"
"$PUMP_PY" -B reconstruction/pump-main/lanes/five-function-integration/verify.py --binary "$PUMP_UNION/unstripped.so" --stripped "$PUMP_UNION/candidate.so"
```

Build control from the 70 primary inputs at the fixed main commit; the exact maps are in `sources.json.gz`. For focused reproduction, copy the unchanged `records/{focused.py,crossings.py,case_manifest.py}` into `work/five-function-integration/runtime/` (their original repository-root resolution requires that depth), then run both scripts with `--control CONTROL/candidate.so --candidate UNION/candidate.so --output NEW.json.gz`.

Regenerate broad evidence with the existing interfaces:

```sh
"$PUMP_PY" -B scripts/pump_validate_parallel.py --candidate "$PUMP_UNION/candidate.so" --source-directory "$PUMP_UNION/source/programs/pump" --build-comparison "$PUMP_UNION/build-comparison.json" --captured-loader --workers 4 --output "$PUMP_RUN/full44.json.gz"
"$PUMP_PY" -B scripts/pump_with_captured_loader.py --receipt "$PUMP_RUN/extensions.loader.json" scripts/pump_v3_token_extensions_differential.py --candidate "$PUMP_UNION/candidate.so" --output "$PUMP_RUN/extensions.json.gz"
"$PUMP_PY" -B scripts/pump_strict_ordered_logs.py --report "$PUMP_RUN/full44.json.gz" --candidate "$PUMP_UNION/candidate.so" --expected-pairs 10468 --output "$PUMP_RUN/strict.json"
```

Exact executed commands, all admission pins and actual receipts are retained in the compressed records. Optional ELF verification recomputes all memberships using the unchanged official normalizer and a fresh injective physical assignment. Reproduction outputs may differ in metadata paths while both ELF hashes must remain identical.
