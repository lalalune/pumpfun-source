# Complete comparison output publication

`scripts/compare.py` wrote `comparison.json` into its final output directory before
writing the optional allocation-padded artifact. A write failure could therefore
leave a complete equality receipt beside an incomplete artifact, and the existing
output check prevented a retry at the same destination.

At base `8f730b4a3e331d035bd979ef7d21aa65ace67d9f`, the real CLI was run against the
captured Donation Relay bytes with `--pad-zero-to-allocation` and a child-process
file-size limit of 4,096 bytes. It exited 1 with `EFBIG`, but left a 670-byte receipt
claiming equality and `candidate_bytes: 830448` beside a 4,096-byte
`candidate.deployed.so`. Retrying without the limit exited 2 because the output
already existed. No capture or candidate input was changed.

The comparator now stages the report and optional artifact in a private sibling
directory and publishes the complete directory with the existing
`deep_disassembly.rename_directory` no-replace helper. Write and publication
failures remove only the private stage. A concurrent destination remains intact.
An inner directory created with ordinary `mkdir` retains the caller's umask when
published. The bounded temporary prefix does not depend on the output name.
The isolated CLI fixture in `test_tooling.py` copies the helper's two modules as
well as the comparator and analyzer.

## Reproduction and validation

Run from the repository root with the pinned `requirements.txt` environment:

```sh
python -E -X utf8 -B tests/test_compare_publication.py -v
python -E -X utf8 -B scripts/verify_evidence.py
python -E -X utf8 -B scripts/test_tooling.py
```

To reproduce the original failure, copy the new test file into a checkout of the
base revision and run:

```sh
python -E -X utf8 -B tests/test_compare_publication.py -v ComparePublicationTests.test_real_write_failures_leave_no_output_and_allow_retry
```

Both resource-limit cases fail on the base: a 64-byte limit leaves a partial report,
and a 4,096-byte limit leaves the report and truncated padded artifact. On the
changed comparator both failures leave the destination absent and permit a normal
retry. The tests use actual captured bytes, actual subprocess writes and Unix
resource limits; the competing-destination test schedules a real directory
creation immediately before the real native no-replace operation.

On macOS arm64 with Python 3.12.13, all six publication tests, all 211 root tooling
tests and all nine saved captures pass. Positive controls retain unpadded equality
and mismatch exits, padded artifact/hash binding, input bytes, existing outputs
and POSIX umask permissions. The existing `contract-tests` CI job discovers the new
test file. Linux and Windows were not run locally; the resource-limit and umask
cases are skipped where their operating-system facilities are unavailable.

## Scope and retained evidence

This is comparison-output consistency, not reconstruction progress or compilation
provenance. The tests compare captured bytes and an ELF-extent prefix solely as
comparator controls. Reports retain `source_provenance_verified: false`.
No compiler, VM or live network transaction was run.

`proposed-asset-transition.json` records the two changed maintained script hashes.
No `scripts/*.py` file is added or removed. Existing historical checkpoint
verifiers still refer to `compare.py` through packages under the removed `repro/`
tree; those packages and their seals are not available or changed here. This does
not revalidate historical checkpoints. The live comparator had already received
the separate program-discovery, Relay-capture and equal-byte performance fixes.

Publication uses the existing helper's macOS, Linux and Windows behavior; hosts
without its native no-replace support fail without exposing a partial result.
The change does not promise fsync or power-loss durability. Abrupt process
termination can leave a private temporary directory, but not a newly published
partial comparison directory.
