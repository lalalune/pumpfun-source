# Cold-build score regression workflow

The manually dispatched `Pump cold-build score regression` workflow accepts two
full commit SHAs available in the workflow's repository. It checks out tooling
from the selected workflow ref and both source revisions separately. Use a
reviewed tooling ref: this is an operator-requested build, not automatic execution
of every external PR. No secrets, write token permissions, or persistent runner
are required.

Both Pump crates are built with the same v1.44 identity recipe in separate cold
target directories, offline after locked dependency acquisition. The official
macOS arm64 SDK archive is SHA-256 pinned, every SDK inventory entry is verified,
and the hybrid Linux target libraries are authenticated by the existing bootstrap.
The SDK Cargo performs acquisition too, preserving its registry-cache namespace.
The runner label follows [GitHub's macOS arm64 runner documentation](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).

One copy of the official scorer processes both binaries against the same captured
original and window inventory. A new isolated scoring-input directory prevents a
stale original-window cache from participating. No matching or normalization rule
is changed. The existing `compare_scores.py` rejects any lost normalized/raw
membership or changed window inventory. Compiler failure and stack warnings stop
scoring, even if the builder itself returns success.

Receipts retain source revision and file hashes, tool/scorer hashes, compiler and
objdump hashes, SDK/target-library manifest hashes, binary build hashes, both full
score reports, and the comparison. Logs and reports are uploaded on failures too;
build outputs/caches and keypairs are not uploaded. This is not a runtime test or
a proof of whole-ELF identity. Source changes during a build are rejected. Output
directories must be fresh so previous measurements cannot be overwritten.

Local use on a provisioned macOS arm64 host (Python 3.12):

```sh
python -B reconstruction/harness/build_score_pair.py \
  --base /path/to/base-checkout --candidate /path/to/candidate-checkout \
  --out /path/to/new-output
```

`--sdk` and `--hybrid` can select already provisioned local toolchains. Local callers
must authenticate them first; the hosted workflow performs full bootstrap checking.
Cargo dependencies must already be available in `~/.cargo`. Both source directories
must have clean `programs/pump` trees. The tooling copy, original, and inventory
come from this script's checkout, not separately from each candidate.

Related work: #1320 rejects stack-invalid builds in fastbuild itself; this runner
checks validity at its own boundary without editing fastbuild. #1339 protects shared
build workspaces; this workflow uses separate fresh workspaces. #1372 stages hybrid
toolchains safely; bootstrap runs on a fresh hosted runner here. #1386 provides an
SDK-independent symbol reader; this runner uses the authenticated SDK objdump.
#1390 binds scoring caches to inputs; this runner uses a fresh private cache instead
of changing the scorer. #1405 adds compiler timeouts; the hosted job has a 90-minute
timeout. #1392 validates composition inputs; this compares two complete source
checkouts and does not compose patches. This extends #1379's saved-score comparison. #1447 checks literal workflow input
paths; this workflow uses multiple checkout directories, which are outside that
checker's current source-root coverage.
