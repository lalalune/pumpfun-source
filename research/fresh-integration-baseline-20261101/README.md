# Fresh integration baseline regression

`integrate.py` historically built only the composed candidate and compared it
with the checked-in historical score. That is useful for exploration, but it
cannot prove preservation of a match added by current upstream after that saved
score was recorded.

This packet retains the smallest witness. The historical score and composed
candidate both miss window `0x100`, so the historical comparison reports no
loss and appears acceptable. Current upstream's base matches that same window
both normalized and raw. Comparing fresh base and candidate builds therefore
reports both losses and rejects the composition.

The fixture does not claim a real Pump score or modify the scorer. It is a
synthetic membership fixture admitted by the maintained comparison rules. The
executable regression test additionally proves that historical `integrate.py`
invokes exactly one candidate build. The new fresh-control tests prove that the
paired path invokes isolated base and candidate builds and refuses these losses.

Base revision: `638fce2a34c8433177f5b778f39cf79e70c971d4`.

Reproduce the byte-identical result and verify its semantic claims:

```sh
python -B research/fresh-integration-baseline-20261101/reproduce.py \
  > /tmp/fresh-integration-results.json
cmp research/fresh-integration-baseline-20261101/results.json \
  /tmp/fresh-integration-results.json
python -B research/fresh-integration-baseline-20261101/verify.py
python -B reconstruction/harness/test_integrate_fresh_regression.py
```

## Historical author pinned-toolchain qualification

`real-qualification.json` is the compact, path-independent summary of one
genuine paired build at the base revision above. Two independently delivered
parts added different unreferenced fixture files to temporary Pump snapshots.
Both were derived from and composed onto the exact admitted upstream source;
neither changes the compiled program. The run used the authenticated v1.44 SDK,
hybrid compiler, captured Pump ELF, and maintained 1,035-window inventory.

Both cold builds succeeded with valid stack reports and produced the same
stripped and unstripped ELF hashes. Each score contained 1,034 normalized and
1,034 raw matches, with zero gained, lost, missing, added, or resized windows.
The independent verifier re-hashed all 3,887 retained artifacts and recomputed
acceptance. Full build workspaces, binaries, score reports, scoring inputs, and
the 1,011,757-byte authoritative receipt remain under the immutable local output
`reconstruction/integ/daybreak-fresh-real-638fce2a/` and are intentionally not
checked into Git.

This author receipt remains unchanged. It predates the reviewed source-only
producer and independently re-scoring reader, so it is historical evidence and
does not claim admission under the repaired helper closure. A new real
qualification must retain its own fresh receipt and complete artifacts.

Reproduce the summary after running the documented qualification command:

```sh
python -B research/fresh-integration-baseline-20261101/summarize_real.py \
  reconstruction/integ/daybreak-fresh-real-638fce2a \
  --base-revision 638fce2a34c8433177f5b778f39cf79e70c971d4
```
