# Admit AMM cached attempts against their actual inputs and outputs

`try_sell.py` previously keyed a whole compiler/score attempt by only Sell bytes,
patch bytes, flags, linker bytes and a manual score version. It would replay the
same result after other baseline Rust or the harness changed, after its candidate
ELF disappeared, and when a later caller requested a listing the cached run never
produced. This affects the normal documented native AMM iteration workflow.

The cache context now includes every selected baseline file, the native builder,
workspace transform, scorer/ELF reader and linker metadata, the SDK tree, captured
original identity, release-profile environment overrides and listing request.
Existing lane baselines are respected; a new lane uses PRISTINE. Receipt hashes
bind every required retained output, including actual candidate/symbol ELF hashes
and requested listings. Invalid or old cache entries trigger an actual attempt.
Replacement cache entries preserve the prior entry under `cache/previous` and are
published through a temporary file. Changing inputs during a build refuses to
publish a reusable cache entry, while the native output remains retained.

The proof provisions a private copy of the authenticated official macOS v1.44 SDK
with its pinned Linux SBPF libraries, fetches the locked workspace dependencies,
then runs the real `try_sell.py --baseline` compiler and scorer. An intact repeat
must reuse that exact actual attempt. A listing request must produce all three
real listings; a missing actual ELF must trigger another successful native build;
and an ordinary comment in non-Sell baseline Rust must get a different cache key
in a new lane. These checks use actual compiler outputs, not a fabricated goal
cache. The status-only unit fixtures remain explicitly synthetic and never claim
compiler/ELF/VM evidence.

```sh
python -B research/amm-cache-admission/reproduce.py
python -B scripts/amm_sell/test_cached_status.py
```

Real CLI stdout/stderr, producer build log/record and original compiled ELF gzip
files are retained under `work/scoped-proof`. The private SDK, Cargo registry and
large target directories stay outside the uploaded proof. The registry remains
the native builder's trusted locked dependency cache; this does not claim a
hermetic build, concurrent-lane serialization, new byte matches or VM equivalence.
