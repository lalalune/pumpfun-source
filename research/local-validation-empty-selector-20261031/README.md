# Refuse a selector that validates nothing

Problem: `scripts/local_validation.py` returned the archived selector
(`repro/programs.json`) verbatim after a bare dict check. An empty object made
`main()`'s loop run zero times, so the run wrote

    {"runtime": "solders 0.27.1 / LiteSVM", "scope": "...", "programs": {}}

to `audit/local-validation.json` and exited 0 — a published, self-consistent
receipt for a smoke test that validated no program. A blank or non-string
address failed later inside `Pubkey.from_string`, far from the real cause.

Reproduction at base `9b9440fe5`:

    repro/programs.json = {}
    program_addresses() -> {}          # main() then publishes programs: {}

Fix: reject an empty selector and any non-string or blank program name or
address before returning, so a run cannot publish a receipt that validated
nothing. The valid-selector path and the capture fallback are unchanged.

Tests: `tests/test_local_validation_selector.py` (4 tests) fails 5 subtests on
base and passes after; `scripts/test_tooling.py` 228 tests OK;
`scripts/verify_evidence.py` 9 captures verified. macOS arm64, Python 3.14.3.

Original submission limits: no LiteSVM smoke run was executed then — `main()` needs solders and the
existing `audit/local-validation.json` receipt is not regenerated — so the
runtime result itself is not re-proved. This is input admission, not new
malformed-input coverage.

No live binding pins this script; the `REQUIRED-INPUTS.json` record under
`research/amm-staging-source-containment-20261030` is historical donor
provenance, not a working-tree drift guard. Peer PR
`lalalune/pumpfun-source#3104` edits the report write in `main()` for encoding
only and does not overlap `program_addresses()`.

## Review qualification

Whitespace-only names and addresses (including Unicode whitespace) are now
rejected using `strip()`, and selector/capture metadata is decoded explicitly
as UTF-8. Valid selectors are returned unchanged.

Real CLI controls show that an empty selector neither creates a report nor
replaces an existing one. A temporary Mayhem-only selector and a copied real
captured ELF completed all 67 malformed-input cases with every transaction
rejected. The historical `audit/local-validation.json` was not regenerated;
this remains bounded malformed-input smoke evidence, with no valid-state or
whole-program equivalence claim.
