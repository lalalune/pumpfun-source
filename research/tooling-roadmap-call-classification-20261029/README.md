# Roadmap call/syscall classification

`scripts/reconstruction_roadmap.py` extracts the source nibble as
`(register_byte >> 4) & 0xf`, then compares it with `0x10`. A nibble cannot be
16. Every captured `0x85` instruction therefore falls through to `call_other`:
the roadmap reports zero internal relative calls and an empty `syscalls`
mapping for every window.

The captured SBPF v0 corpus encodes both forms as `0x85 0x10`. Relocation type
10 marks the relocated external placeholder; a non-type-10 `0x85 0x10` is an
internal relative call whose target is `pc + 8 + immediate * 8`. The archived
helper is hash-checked and only that comparison plus the matching call-count
predicate are adapted in memory. The root script, historical reports and every
captured byte remain unchanged.

```sh
python3 -B research/tooling-roadmap-call-classification-20261029/test_verify.py
python3 -B research/tooling-roadmap-call-classification-20261029/verify.py --repo .
python3 -B scripts/verify_evidence.py
python3 -B scripts/test_tooling.py
```

## Real corpus before/after

| program | call sites | internal | relocated externals | syscall terms before | syscall terms after | changed windows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| pump | 10,861 | 10,591 | 270 | 0 | 270 | 240 |
| pump_amm | 7,397 | 7,223 | 174 | 0 | 174 | 151 |
| mayhem | 4,902 | 4,768 | 134 | 0 | 134 | 85 |
| total | 23,160 | 22,582 | 578 | 0 | 578 | 476 |

The corrected `calls` total is unchanged because syscalls remain call sites;
only the class label and the new `syscalls` mapping change. `call_internal` goes
from 0 to 22,582 and `call_other` from 23,160 to 0 across the three programs.
The top external terms are `abort`, `sol_log_` and
`sol_try_find_program_address`; counts are in `observations.json.gz`.

## Method and limits

`inputs.json` binds the reviewed helper and the three captured `.text` images.
`observations.json.gz` is regenerated from those bytes; `coverage-delta.json`
records the tooling totals and makes no payload-byte coverage claim. This is a
static classification correction. It does not prove call-graph closure,
runtime reachability, source provenance, whole-program equality or security
clearance, and it does not rewrite the archived roadmap outputs.

Run from the repository root. `verify.py` re-hashes the manifest, inputs and
fresh observations; `test_verify.py` checks synthetic internal, external and
legacy call forms plus the complete real-corpus totals.
