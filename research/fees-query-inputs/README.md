# Restore the Fees query validator's synthetic inputs

The current documented `scripts/validate_fee_handlers.py` reads two files under
the removed `repro/experiments` tree. A full current checkout cannot execute its
two Fees query-handler differentials, including the `queries` entry of
`fees_validate_all.py`, because those required case inputs no longer exist.

Recover only the consumed synthetic input fields from the exact preserved Git
objects at `b4448f7bc202063a711565b543ae4b49770def90`, before cleanup
`fce9f28dd1cc3257d65b3c20afe60acfa8955545`. Keep all 9428 quote-selector cases
and 1215 tier-selector cases, in their original order. Do not import historical
expected outcomes, native results or compiler identities into new VM evidence.
`provenance.json` binds both original Git objects, full report hashes, unchanged
captured original hash, selected fields, counts and deterministic fixture hashes.
The existing validator loads these nested-package gzip fixtures and computes
all original/candidate outcomes afresh. Other malformed-input and allocation
boundary cases in that validator are unchanged.

`restore_cases.py` is the explicit extraction recipe from the historical objects;
it checks their Git identities and applicability to the current captured Fees
ELF. The committed gzip files are ordinary JSON data; running the validator does
not fetch history or execute historical tools. No new root script is added, and
the adjacent proposed asset transition records the one edited root script.

The proof builds the current maintained Fees workspace with authenticated native
macOS v1.44 tools and pinned Linux SBPF target libraries, retaining genuine ELF,
compiler log and source/tool hashes. This is a diagnostic VM-test build, not the
Linux container recipe's exact-ELF identity claim. It executes the actual query
validator against that rebuilt ELF. After restoration it also loads the genuine
captured Mayhem executable as an explicitly wrong program and requires real VM
mismatches and a nonzero result. No binary is patched and no compiler/VM result
is simulated.

```sh
python -B research/fees-query-inputs/reproduce.py
```

Actual build/validator logs, full VM reports and ELF gzip files are uploaded from
`work/scoped-proof`; generated registry and target directories are outside it.
This repairs the two query handlers' runnable input corpus. It does not claim the
entire 18-suite aggregate has been replayed, new byte matches or whole-program
equivalence. Original captures and historical report objects remain unchanged.
