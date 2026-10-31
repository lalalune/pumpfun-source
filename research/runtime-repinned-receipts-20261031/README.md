# Preserve image roles across candidate pin paths

At `720311c88e547c3a2d5ada174429a18e53c4fd83`, five Pump differential
producers identify images only through path keys in their provenance maps.
The parallel validator pins its candidate to a fresh temporary path on each
invocation. Its `--validate-existing` receipt check consequently rejects these
otherwise valid results when the unchanged candidate has a different pin path.

The producers now include `original_sha256` and `candidate_sha256`, copied
from their existing admitted and rechecked provenance entries. Complete path
provenance remains present. The consumer already supports these explicit role
fields, so its image check need not be relaxed or infer roles from arbitrary
provenance entries. In the fee sweep and minimum-distribution receipts, that
distinction also prevents an included dependency image from satisfying the
candidate/original role check in isolation.

## Actual before and after execution

The five unmodified producer CLIs first generated 1,127 captured
original-versus-original cases: creator collection 119, creator collection v2
154, fee sweeps 504, minimum distribution 181 and set-params 169. Their actual
receipts were passed to the production `parallel.validate_result` consumer.
All five passed with the first pin and failed with a second byte-identical pin.

The fixed producers were rerun with the same inputs. All 1,127 case records
are identical to the base records, and every receipt now admits both pin paths.
Different-candidate and different-original controls reject in all five suites.
`results.json` records receipt/case hashes and the base dependency-role
control failures in two suites, without publishing machine-specific provenance paths.

The new regression executes all five real producers, then checks both image
roles and the new-pin acceptance. Both test methods pass. Eight affected
existing suites pass 35 tests; mandatory verification passes 250 tooling tests
and nine capture checks. The regression is wired into `verify.yml`.

## Reproduce

Install the repository requirements and run from the checkout under test.
Keep this packet's `reproduce.py` available when testing the base revision.
The output directory must be new.

```sh
python research/runtime-repinned-receipts-20261031/reproduce.py \
  --repo "$PWD" --output /tmp/repinned-receipts
python -B tests/test_pump_repinned_receipts.py
python scripts/verify_evidence.py
python scripts/test_tooling.py
```

Inspect `results.json` in the output directory. Before the fix,
`same_byte_second_pin_admission` is null for all five suites; afterward it
equals the retained case count. Every fixed negative control is rejected.

This executes the real producer CLIs and the actual receipt admission
function. It does not claim a full 44-suite build-bound CLI run or a source
rebuild. Historical path-only receipts remain unchanged and retain their
limitation. No live RPC, transaction, binary modification or security claim is
involved.
