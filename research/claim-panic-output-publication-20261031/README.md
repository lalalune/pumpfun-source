# Claim-panic receipt publication

`scripts/pump_claim_panic_differential.py` refused an existing `--output` with
`Path.exists()`, which follows links. A dangling symlink therefore passed the
check and `write_bytes` created the report at the link target: at base
`5889e795eba64e85e613b4409921323bfecec414`, pointing `out.gz` at an absent
`escaped-report.gz` produced a 5,765-byte gzip at the external path, exit 0 and
`{"cases": 2, "mismatches": []}`, with the symlink left in place.

The fix checks `is_symlink() or exists()` before running, and writes the payload
with mode `'xb'`, so a path created by another writer after the preflight check
is still refused and a symlink that appears in between is not followed. A fresh
path keeps the existing behaviour: exit 0 and a complete gzip report.

`tests/test_claim_panic_output_publication.py` drives the real CLI three times:
dangling symlink (refused, target absent), existing receipt (refused, bytes
intact) and fresh output (2 cases, gzip). On the base script only the first fails;
on the proposed script all three pass in 0.2s. The suite is discovered by
`python -B -m unittest discover -s tests -v`.

Required checks on the proposed tree: `python3 -E -X utf8 scripts/test_tooling.py`
(217 pass) and `python3 -E -X utf8 scripts/verify_evidence.py` (nine captures
verified). macOS arm64, Python 3.14.3. No fixture, capture or case message
changes; the diagnostic remains a two-case regression, not an exhaustive claim
or program-equivalence proof.
