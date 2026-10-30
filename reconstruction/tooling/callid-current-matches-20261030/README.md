# Audit current matches before applying historical pairings

`callid_audit.py` used to exempt every address in the historical 16-window
`census.PAIRS` table from call-graph refinement, even after a later compiler
artifact normalized-matched one of those windows. A matching former pairing
was both omitted from the reported normalized count and left unaudited by
the normal fixpoint. Historical pairings now apply only to initially unmatched
windows. Scoring and program sources are unchanged.

## Real retained compiler artifact

The existing [V3 Sell packet](../../pump-main/lanes/v3-sell-payment-layout/NOTES.md)
retains the independently built merge cohort `e075a8ec15add21ed8ec07712e65d709a6e79db9`.
Its `candidate.so.gz` SHA-256 is
`b0ab1d836e8b6c04a8954d2ffea86223ad40550b517fa4adf67febb84ea563d7`.
Decompression yields 2,664,816 bytes with SHA-256
`969811b0e0f673b693695ea651008cacd93eafa5a663dd8bec0e61d3b22d09a9`,
matching that packet's `candidate-build.json` unstripped hash. The original Pump
capture SHA-256 is `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`.

The retained official score contains 1,020 normalized and 188 raw memberships.
Its normalized match at `0x14f4e0` (`buy_exact_sol_in`) was nevertheless pinned
by the historical audit table. Actual CLI runs against the same artifact give:

| Audit | Normalized matched | Bisimilar matched | Pinned targets |
| --- | ---: | ---: | ---: |
| Before | 1,019 | 1,019 | 16 |
| After | 1,020 | 1,020 | 15 |

`before.json` and `after.json` are those complete reports, with line endings
normalized to LF for retention. Both contain the
same candidate path from the local controlled run. No actual hidden wrong-callee
defect was found in this artifact. The unit regression separately models a
formerly pinned match with a wrong callee and verifies that refinement rejects it.
These runs reuse a retained compiler artifact: no new compilation, VM execution,
source-equivalence, or current-main score claim is made.

## Reproduce

Decompress the retained `candidate.so.gz` to a temporary `candidate.so`, verify
the hashes above, and set `CALLID_REAL_CANDIDATE` to its absolute path. From the
repository root run Python 3.12:

```sh
python -X utf8 reconstruction/harness/test_callid_current_matches.py
```

The lane's [portable usage](../../pump-main/lanes/callgraph-census/PORTABLE_USAGE.md)
documents harness discovery and inputs. This audit and its focused tests use only
the Python standard library and the retained ELF; no SDK executable is invoked.

This runs both regressions when the environment variable is set, independently
scores the real artifact and checks that every normalized former pin is included
in the audit relation. Without that artifact it runs the unit regression and
explicitly skips the retained-artifact regression.

The actual CLI command used for the retained reports was:

```sh
python -X utf8 <scratch-root>/reconstruction/pump-main/lanes/callgraph-census/callid_audit.py \
  --cand <temporary>/candidate.so --json <temporary>/after.json
```

The scratch root contained unchanged copies of `reconstruction/harness/`, the
census lane and `reconstruction/base/functions.tsv`. Its `base/original.so`
contained a copy of the real capture bytes, so Windows Git's regular-file symlink
payload did not interfere with this separate call-relation measurement. Before
and after used the pre-fix and post-fix audit source respectively; prior reports
were preserved.

Validation also runs the repository's saved-capture and tooling gates. Those
verify retained evidence and tooling behavior, not a build or VM replay.
