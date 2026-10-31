# Reject stale macOS hybrid library names without aborting bootstrap

Baseline: `13fe4536be64d8c5c10f8905e9d2236f423ac4f4`.

`bootstrap.hybrid_ok()` chose its SDK comparison paths from the libraries found
in the existing macOS hybrid cache. Replacing either of its two library names
with an obsolete name kept the file count at two but made it hash a nonexistent
SDK pathname. The resulting `FileNotFoundError` aborted bootstrap instead of
returning false and entering its normal cache-assembly branch.

The fix compares the cached library names to the SDK's complete two-library
set before hashing. Expected SDK files, rather than stale cache filenames,
define the comparisons. The existing compiler, library-byte, host-link and
target-library checks remain intact. This follows the existing Linux host
library-set validation and does not change the SDK inventory or recipe.

The regression extends the existing real-file macOS fixture. It renames each
cached library in turn, checks rejection without an exception, restores it and
checks valid-cache admission. Both corruptions raise on the baseline
(`before.log`) and pass after the fix. Only fixture paths/platform selection
are overridden; the admission and hashing functions read actual files.

Run from the repository root on Linux with Python 3.12.3:

```sh
python3 -m unittest discover -s reconstruction/toolchain -p 'test_bootstrap*.py' -v
python3 -B tests/test_linux_hybrid_publication.py
python3 scripts/verify_evidence.py
python3 scripts/test_tooling.py
```

The bootstrap suites run 15 tests (14 pass, one native macOS assembly skip).
The Linux publication suite passes 17 tests. Required checks authenticate nine
captures and pass 228 tooling tests on native Linux. The latter suite includes
offline runtime controls. No real macOS compiler, native macOS assembly,
program build, score gain or bytecode equivalence is claimed. No toolchain or
dependencies were downloaded. Existing local pinned validation inputs were
reused; public logs redact the local checkout prefix and omit verbose success
details. `results.json` states the remaining platform gap explicitly.

Live searches for macOS hybrid/dylib work found only merged #2986, which restored
the validation root and tests; it does not reject stale host-library names.
This permitted reconstruction-toolchain fix changes no program source,
compiler input, imported data or retained binary.
