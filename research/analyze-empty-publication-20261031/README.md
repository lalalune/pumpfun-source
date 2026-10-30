# analyze.py empty-input publication

`scripts/analyze.py` builds `evidence/binary-analysis.json` from the captured
programs and `evidence/interface-inventory.json` from the upstream IDLs, then
publishes both. Neither input set was checked for emptiness: at base
`5889e795eba64e85e613b4409921323bfecec414`, pointing `analyze.ROOT` at a tree
that holds only an empty `evidence/upstream` directory published `{}` to both
tracked report paths and returned normally.

`results.json` records the before and after runs. The fix raises
`SystemExit: no captured programs or upstream IDLs; refusing to publish empty
reports` before serializing, so a partial checkout or a moved evidence tree
cannot replace the reports with empty objects. Captures without IDLs, and IDLs
without captures, are refused the same way; a tree with both still publishes
both reports.

`tests/test_analyze_empty_inputs.py` covers the two empty cases and a control
that copies the captured `pump` ELF, its `capture.json` and `pump.json` into a
temporary tree and checks both reports contain only the `pump` key. The two
empty cases fail on the base script; all three pass in 0.11s here.

Required checks on the proposed tree: `python3 -E -X utf8 scripts/test_tooling.py`
(217 pass) and `python3 -E -X utf8 scripts/verify_evidence.py` (nine captures
verified). macOS arm64, Python 3.14.3. The tracked reports, captured bytes and
IDLs in the repository are unchanged by this proposal.

## Review qualification

The current five regression tests invoke a copied `scripts/analyze.py` through
its real command-line entrypoint, without mocking its analysis or publisher.
They cover missing captures and IDLs, each missing side separately, preserved
prior report bytes, the guard under optimized Python, and a real captured Pump
ELF plus its IDL publishing both reports. Existing paired-publication tests also
pass. The three-test timing in `results.json` records the original submission.
