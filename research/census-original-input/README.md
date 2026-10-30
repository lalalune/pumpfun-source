# Resolve the captured original for direct census diagnostics

At base `1043a51e8798c5974a84ecaed5c85e9d6938cfce`, the shared census
module reads `BASE/original.so` directly as ELF. With `core.symlinks=false`,
that tracked file contains Git's exact known link payload, while the scorer
already resolves it correctly. Direct call-target/data-reference diagnostics
therefore fail before processing the candidate. All census consumers share
the same original definition.

Use the existing narrow `resolve_original` helper at that definition. Candidate
decoding is unchanged: supplying link text as a candidate still fails. Update
only the current portability wrapper's reviewed census hash, preserving its
admission and positive-control behavior. No historical sealed packet is repinned.

## Actual ELF commands and controls

```sh
python -B research/census-original-input/reproduce.py --repo-root . --out work/census-after --expect after
python -B reconstruction/harness/test_census_original_input.py
python -B reconstruction/diagnostics/census-portability/test_run.py
python -B scripts/verify_evidence.py
python -B scripts/test_tooling.py
```

The same reproducer is run with `--expect before` on the proof-only base
revision. `proof_entry.py` supplies the expected behavior only for the two
explicitly reviewed census hashes; it never patches any audit/scoring function.
A successful before proof means the real direct CLIs failed as expected,
not that the original defect was fixed.

The proof stages the real original capture, complete inventory and actual
module closure, writing only the exact known Git link payload at the staged
original path. It executes the actual callid/dataref CLI entrypoints in separate
isolated processes, from an unrelated working directory, and runs the existing
digest-admitted wrapper as a positive control. The default retained compiled
candidate is `research/pump-multihop-sell-fees-20261029/build/candidate/symbols.so.gz`,
uncompressed SHA-256
`b79428215bac7c4cb487681ea3a5cdad84197fcaa04142a0e68f4a4706008898`.

Before, direct CLI calls fail parsing original link text and publish no JSON.
After, complete direct reports must equal wrapper controls byte for byte.
Cross-run comparison excludes only the declared candidate pathname, since
the independent output trees differ; every diagnostic field/finding remains.
Candidate-link negatives reject in both versions. Original capture and link
text remain unchanged. Full logs/reports/hashes are retained in the output tree.

Earlier #2111 repaired harness original resolution, #2091 introduced the current
wrapper that materializes actual capture bytes, and #1508 made direct lane imports
repository-relative. This repairs their remaining common direct census input
without splitting contributions by consuming CLI.

This is static analysis of a genuine historical compiler-built candidate, not
a fresh current-source build, new score gain, runtime equivalence, exhaustive
call/data validation or security approval. Existing call-target mismatches and
data-reference flags remain explicit. Full disassembly-dependent census rendering
is outside this bounded proof.
