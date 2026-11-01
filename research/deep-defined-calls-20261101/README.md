# Defined dynamic calls in default diagnostic reports

The current default disassembler labels a defined `custom_panic` function call as
`call_extern custom_panic`, and the program analyzer omits its outgoing/incoming
edge. Each of the five retained captures supported by the disassembler contains
one such call. Its linked dynamic symbol is a positive-size function in `.text`,
with an extent already admitted by the unchanged ELF reader.

This extends the defined-call distinction accepted in
[#1502](https://github.com/lalalune/pumpfun-source/pull/1502) by **miracle2044**
from the opt-in roadmap diagnostic into the default disassembler and analyzer.
[#1608](https://github.com/lalalune/pumpfun-source/pull/1608) by **Musashibal**
intentionally retained the relocated `extern_symbol` label while correcting
relative calls, indirect operands and syscall fingerprints.
[#2629](https://github.com/lalalune/pumpfun-source/pull/2629) by
**dbstkddl8-create** then corrected syscall reports while preserving that label.
This integration extends those documented boundaries; it does not present their
bounded implementations as an undiscovered error or change their syscall rules.

The decoder retains `extern_symbol` as relocation metadata and adds its existing
`call_target`/`call_name` fields for admitted defined calls. Report counters prefer
that resolved target, so the label does not double-count an internal call as an
external one. The analyzer merges those targets into a local diagnostic call map, adding
one edge per supported program. The shared matching reader's calls, entries,
normalized bytes and relocation patterns remain untouched. The active analysis
output wrapper admits the two reviewed new helper hashes while retaining every
previous admitted hash.

| Capture | Internal calls before / after | External calls before / after | Analyzer edges before / after |
| --- | ---: | ---: | ---: |
| Pump | 10,591 / 10,592 | 270 / 269 | 10,591 / 10,592 |
| Pump AMM | 7,223 / 7,224 | 174 / 173 | 7,223 / 7,224 |
| Pump Fees | 4,586 / 4,587 | 155 / 154 | 4,586 / 4,587 |
| Mayhem | 4,768 / 4,769 | 134 / 133 | 4,768 / 4,769 |
| Donation Relay | 4,320 / 4,321 | 99 / 98 | Outside analyzer program selection |

Syscall reports and fingerprints stay byte-identical, as do dispatch, strings,
function indices and section layouts. After masking only the identified call
mnemonic, affected caller/callee counts and records, summary counts, README count
rows and their derived manifests, every other report field is unchanged.
[`results.json`](results.json) records the exact source/input/report hashes,
call bytes, linked symbol records and before/after counts.

## Replay the complete CLIs

The baseline is the published generated-manifest correction
`a073c5c8e561dfe0f8a842d27aa1b446de140333`. The same probe runs five real
disassembly commands and four real analyzer commands per revision, then executes
each generated packet verifier. All work uses owned temporary copies of unchanged
retained captures and IDLs. The independent witness reader parses raw linked
relocation/symbol records without importing either report producer.

```sh
python -B research/deep-defined-calls-20261101/probe.py --repo . \
  --revision a073c5c8e561dfe0f8a842d27aa1b446de140333 --expect base --output /tmp/defined-before.json
python -B research/deep-defined-calls-20261101/probe.py --repo . \
  --expect fixed --output /tmp/defined-after.json
python -B tests/test_deep_defined_calls.py
python -B scripts/test_deep_disassembly_syscall_usage.py
python -B scripts/test_deep_disassembly_publication.py
python -B scripts/test_analyze_program_publication.py
python -B tests/test_deep_elf_coordinates.py
python -B tests/test_generated_packet_census.py
python -B research/tooling-analysis-output-retention-20261029/test_generate.py
python -B scripts/verify_evidence.py
```

For both probe outputs, each program's `unrelated_report_sha256` map must be
identical, including its nested `analyzer` map where present. Their source and
input hashes and all packet hashes are bound by the recorded results. Both runs
must report `all_input_bytes_preserved: true`. The 43 affected static test methods
and all nine saved capture checks pass. Existing CI invokes `tests/` discovery,
the syscall test and the analysis wrapper's tests; the existing tooling call
assertions are updated for this intentional classification extension.

A separate read-only official SDK `llvm-readobj --dyn-symbols --relocations`
witness confirms Pump's call at `0x1aac88` refers to `custom_panic`, a global
function in `.text` at `0x1572b8`, size 200. No capture, model or VM was executed.

## Bounds

Only type-10 relocations linked to the actual admitted `.dynsym` table qualify.
The symbol must be a nonzero, positive-size `STT_FUNC` in `.text`, with its exact
translated file-offset extent already present in `elf.funcs`. Logical instruction
and extent admission remains the reader's responsibility. Undefined symbols,
unadmitted linked records and other unresolved cases retain their existing
fallback behavior. The three-argument decoder remains callable.

Zero-size definitions remain unresolved by this bounded diagnostic extension;
that is not a claim that a loader treats them as external. Tests include genuine
undefined symbols and mutated undefined/non-function/zero-value/zero-size,
outside-text/interior/partial extents and wrong table linkage. A supplemental
existing ELF fixture checks a differently named function under both identity and
nonidentity address mappings. This is static report attribution, with no runtime
callee, enabled import, execution, reconstruction or security claim.
