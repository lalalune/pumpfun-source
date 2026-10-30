# Protect the create and cashback differential inputs

Problem: `pump_create_differential.py` and `pump_cashback_differential.py` wrote
their receipts with a direct `write_bytes()` and never resolved the destination
against their inputs. Pointing `--output` at the candidate replaced the captured
ELF with the report and still exited 0.

Fix: construct the shared `PumpReport` publisher before the case loop and
publish through it. Aliasing any input (candidate, evidence images, loaded
modules, the cashback curve fixture) is refused with
`report output aliases an input`, and complete bytes are staged before the
destination is replaced.

Reproduction, base revision `8cf3c5f8a7912b36ced352e49ac8538ff864a4c2`:

```
cp evidence/original/pump/deployed.so /tmp/candidate.so
python -B scripts/pump_create_differential.py --candidate /tmp/candidate.so --output /tmp/candidate.so
# exit 0; /tmp/candidate.so is now a 349,915-byte gzip report
```

With the change the same command exits 1 with the alias message and leaves the
candidate byte-identical; normal runs still publish (87 and 283 cases, zero
mismatches).

Limits: no full 44-suite corpus run is repeated here. The aggregate always uses
fresh temporary outputs, so this protection matters for standalone runs.
macOS arm64, Python 3.14.3.

Review follow-up: the publisher now also protects the Token Metadata and Mayhem
program inputs for create, and the complete `pump_trade_fixture.REPORT_INPUTS`
set for cashback, including capture metadata. The original migration did not
protect those paths. The proposal hashes name this repaired version.
