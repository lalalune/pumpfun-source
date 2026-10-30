# Generated roadmap packet membership

The roadmap verifier previously hashed only the members named by its manifest.
Removing `pump-details.json`, `reconstruction-plan.json`, or `README.md` together
with its manifest entry still produced `All checks passed.` on a fresh roadmap
generated from the captured Pump, Pump AMM, and Mayhem programs.

The generator now embeds its required output names in the generated verifier.
The names come from the programs actually analyzed, rather than mutable packet
metadata. A manifest must be an object containing every required member before
hash or summary checks run. Additional hash-bound adapter inputs remain allowed
and their hashes are still checked.

`results.json` records the real CLI before/after checks and byte comparison.
With `PYTHONHASHSEED=0` for both generation processes, all six analysis/document
payloads are byte-identical; only the generated
verifier and its manifest binding change. The focused tests also cover every
individual membership omission, empty/non-object manifests, an intact packet,
and an added adapter input before and after corruption. Removing the verifier
itself prevents execution, so that case removes only its manifest entry.
Missing `summary.json` already failed before this change; the report preserves
that result rather than counting every old test failure as false acceptance.

Run from the repository root:

```sh
python -B reconstruction/tooling/roadmap-manifest-members/test_verify.py
python -B scripts/test_reconstruction_roadmap_publication.py
python -B scripts/test_tooling.py
python -B scripts/verify_evidence.py
```

To reproduce before/after, generate a packet with
`python -B scripts/reconstruction_roadmap.py --output /tmp/roadmap-before`
at the base revision in `proposed-asset-transition.json`, then run the focused
test from the changed checkout with `--packet /tmp/roadmap-before` (expected to
fail). Run without `--packet` to generate and test the changed verifier.
The optional `--report PATH` retains individual results in a new JSON file.

This is a completeness check for newly generated packets, not authentication
of an unsigned manifest or proof of reconstructed program equivalence.
Existing historical packets and their source bindings remain unchanged.
The proposed transition identifies the changed generator for maintainer review.
