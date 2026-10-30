# Own scorer report staging before cleanup

At base `1043a51e8798c5974a84ecaed5c85e9d6938cfce`, the official scorer
opens `.score-<PID>` exclusively, but unconditionally unlinks that path in
`finally`. If it already holds an interrupted run's receipt, publication
fails and deletes a file the current call never created. Same-process
concurrent report writers also contend for this fixed staging pathname.

Use a short random suffix with exclusive creation, retry collisions, and
enter cleanup only after acquiring the stage. Plain file creation retains
umask-derived publication modes and atomic report replacement. Candidate
admission, normalization, window memberships and score formatting are unchanged.

## Real complete scoring proof

From the repository root:

```sh
python -B research/score-staging-ownership/reproduce.py
python -B reconstruction/harness/test_score_staging_ownership.py
python -B reconstruction/harness/test_score_atomic_report.py
python -B scripts/verify_evidence.py
python -B scripts/test_tooling.py
```

The same proof runs the complete actual scorer twice with a retained genuine
unstripped reconstruction ELF, the captured Pump original and all 1,035
selected original windows. It first creates a normal control report, then
puts those real report bytes at the actual scorer process's `.score-PID`
and invokes the production argument-parsing `main` again. Before, the
second full score loses the prior receipt and exits nonzero; after, it
preserves that receipt and publishes exactly the normal control bytes.
The original module and scorer behavior are not mocked or replaced.

By default the retained token-quote packet's `symbols.so.gz` is used;
`--candidate` accepts another genuine ELF or gzip-compressed ELF. Results
include its actual SHA, full score summary, return code and report hashes.
Logs and reports remain under `work/scoped-proof`. This is scorer
publication evidence, not a fresh build or new reconstruction match claim.

Supplementary real-filesystem tests cover prior-receipt survival, 24
same-process concurrent publications, a genuine failed publication to an
occupied directory, and POSIX umask (skipped on Windows). No compiler/VM
simulation supplies the primary result.

Merged #2973 repaired a different function-comparison writer. This uses the
same established exclusive random-staging pattern for the independently
demonstrated prior-receipt deletion in the authoritative window scorer.
