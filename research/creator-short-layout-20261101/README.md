# Truncated creator reads in the native assignment model

The creator-assignment native model accepts a logical creator and a serialized curve length separately. At base `9120883a957d7d9b2cab6140f66fb5bc9e6774d5`, both setters use that logical creator even when the account is too short to contain its complete 32-byte field (offset 49, minimum length 81). The existing migration model already reads such a creator as unset through `stored_creator`.

Both setters now use that same reader. With a 49–80-byte curve, a nonzero logical creator and an empty metadata creator list, the model previously predicted a write error. Actual signed execution of the captured Pump image reads an unset creator and reaches the empty-list panic first. At length 81 the stored nonzero creator remains present and the write-error prediction remains correct.

The 252-case matrix crosses lengths 48, 49, 50, 64, 80, 81, 165, 166 and 200, three logical creators, four metadata creator-list variants, both setters and earlier account/authority failures. Exact baseline native compilation yields 16 mismatches; the correction yields zero. Inputs and all capture outputs are identical between runs. The earlier account/seed checks, full-size successes, creator bytes, event data and transaction fees remain checked by the existing matcher. Failure cases compare error outcomes; this packet does not add a separate rollback claim.

The fixture loads only the captured Pump ELF, SHA-256 `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`. Metadata is synthetic account data; no Metaplex program is loaded or executed. Production SBF source and historical capture bytes are unchanged. These synthetic local cases qualify the native model only, not live account reachability, a security finding, full behavior coverage or binary identity.

With repository requirements installed and rustc on PATH:

```sh
python -B research/creator-short-layout-20261101/reproduce.py --revision 9120883a957d7d9b2cab6140f66fb5bc9e6774d5 --output /tmp/creator-before.json
python -B research/creator-short-layout-20261101/reproduce.py --output /tmp/creator-after.json
python -B tests/test_creator_assignment_captured.py -v
```

Retained execution used CPython 3.12.13, solders 0.27.1 and rustc 1.99.1. `results.json` retains source hashes and each mismatching baseline input and outcome.
