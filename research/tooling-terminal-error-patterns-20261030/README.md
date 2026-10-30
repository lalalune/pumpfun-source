# Terminal branch-to-move candidates

This maintained wrapper fixes a reproduced boundary omission in the archived
`scripts/bytecode_signatures.py::detect_error_patterns`. The archived loop
stops 24 bytes before each window end, although a conditional branch requires
only one complete 8-byte slot. The corrected detector visits every complete
slot and requires the target move to fit fully inside the same window.

The root script and root test suite remain byte-for-byte unchanged from base
604917c16410d67d9b981305e28e160a93728f50. In particular, the archived script
keeps SHA256 8200e01f582be1a267d187e6340ac2d403c22cad26bfd65e2613e19ea8a55f76,
required by `research/tooling-token-program-constant-detector-20261029`.
That existing packet and its bindings are unchanged. This package follows its
source-bound proof convention rather than rewriting historical inputs.

`inputs.json` binds the archived detector, its window reader and the three
original captures used by the archived CLI. `observations.json` records full
before/after counts and each added candidate's window, branch/target offsets
and raw instruction bytes. The verifier reruns both algorithms on identical
captured windows, requires every previous candidate to remain, and rejects
additions outside the formerly skipped terminal region. `manifest.json` binds
all package files. Use a checkout preserving Git's LF bytes for raw hashes.

| Program | Windows | Archived candidates | Corrected candidates |
| --- | ---: | ---: | ---: |
| pump | 1035 | 557 | 559 |
| pump_amm | 785 | 420 | 421 |
| mayhem | 441 | 1722 | 1723 |

All four additions have immediate zero. These are branch-to-move heuristic
candidates, not proven error paths, runtime failures or security findings.
The inherited field names `error_code` and `conditional_error` are preserved
for compatibility; they do not establish error semantics. This does not repair
other heuristics, establish equivalence, or cover Pump Fees (absent from the
archived CLI's three-program selection).

From the repository root:

```sh
python research/tooling-terminal-error-patterns-20261030/test_verify.py
python research/tooling-terminal-error-patterns-20261030/verify.py
python research/tooling-token-program-constant-detector-20261029/verify.py
python research/tooling-token-program-constant-detector-20261029/test_verify.py
python scripts/test_tooling.py
python scripts/verify_evidence.py
```

To run the existing signature CLI with only this detector replaced in memory:

```sh
python research/tooling-terminal-error-patterns-20261030/proof.py --output /tmp/terminal-pattern-signatures
```

The wrapper verifies all bound inputs before loading the archived module.
The output schema and all other archived detectors remain unchanged; generated
packet metadata retains the archived terminology described above. Run the
output directory's `verify.py` to check that generated packet's inventory.
