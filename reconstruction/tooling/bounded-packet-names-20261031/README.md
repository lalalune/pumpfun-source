# Publish packets with valid long output names

The shared `deep_disassembly.temporary_sibling` helper appended its role, PID and
UUID to the entire requested output basename. A valid output name near the
filesystem component limit therefore became an invalid staging or backup name.
The copyable `revalidate_all.py` fallback contained the same construction.

On base `1d45788df6520afe06c6ed098f6e0608606d7350`, an actual Mayhem deep-disassembly
CLI invocation with a 240-byte ASCII output basename exited 1 with
`OSError: [Errno 63] File name too long`. The same basename could be created and
removed normally on the test filesystem (`PC_NAME_MAX=255`). A short-name control
decoded all 441 windows, published 12 files and passed its generated verifier.
The standalone revalidation CLI likewise checked its authentic captured-byte
payload successfully, then failed when creating the overlong staging directory.

The unchanged five-test regression suite was also rerun on current upstream
`d81d0f58882c55f01bf16dd113696cd579253a02` before rebasing. It again produced
five failed assertions, including the actual long-name CLI and standalone runner
failures. The rebased fix retains upstream packet-root and manifest-file admission
checks; the current source binding is recomputed over those combined bytes.

Both helper implementations now retain at most 64 filesystem-encoded bytes of
the readable output-name prefix, removing only whole characters. Their directory
parent, role, PID, UUID, collision retry and ordinary `mkdir` permissions are
unchanged. All existing callers of the shared helper receive this fix together.
Native no-replace/exchange publication logic is unchanged.

The qualified revalidation adapter hashes the entire current root runner before
loading it. Its maintained binding and README are intentionally updated to the
reviewed new bytes; no retained audit, archived script or historical seal is
rewritten. The proposed asset transition records the before/after hashes.

## Verification

```sh
python -B tests/test_packet_temporary_names.py -v
python -B -m unittest discover -s reconstruction/tooling/revalidation-qualification -p 'test_*.py' -v
python -E -X utf8 -B scripts/verify_evidence.py
python -E -X utf8 -B scripts/test_tooling.py
```

The five focused tests use the real Mayhem capture and actual command-line
analysis. They cover ASCII and multibyte output names, byte-identical short/long
packets, intact retained previous packets, the copyable standalone audit, encoded
temporary-name bounds, UUID collisions and normal umask permissions. Generated
packet verifiers run against the published files. The existing `contract-tests`
CI job discovers the new test module.

The related publication suites cover deep disassembly, program analysis, section
analysis, bytecode signatures, root revalidation, imported-lab verification,
nested/Fees runtime preparation and aggregate retained-output publication.
Qualification controls retain source-drift rejection, mutation detection and
bounded verifier supervision. Exact local results are recorded in `results.json`.

All local runs use macOS arm64/Python 3.12.13. No Linux or Windows run, compiler
execution, program rebuild, score improvement or VM equivalence is claimed. This
fix concerns temporary component names; it does not relax the output path's own
filesystem limits or change separately implemented publishers.
