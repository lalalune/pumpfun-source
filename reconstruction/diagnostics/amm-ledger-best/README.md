# Saved AMM attempts ranked by the canonical no-loss rule

The legacy `attempts.py best` filters `lost_windows_count == 0`, a fixed-address
raw comparison. The builder's canonical `try_sell.rank` instead requires
`lost_windows_normalized_count == 0`; the maintained AMM harness README explains
that a sell-size change can move every later raw address without regressing those
functions. The read query therefore hides candidates that its own canonical
best-publication rule admits.

```
python -B reconstruction/diagnostics/amm-ledger-best/read.py --ledger scripts/amm_sell/attempts/seed.jsonl --limit 10
python -B reconstruction/diagnostics/amm-ledger-best/test_read.py
```

This read-only successor extracts only the pure `rank` function from a
digest-admitted `try_sell.py` AST. It does not import or run the builder, scorer,
fcntl, SDK or VM. Failed/unscored and incomplete metric records do not qualify.
Results preserve ledger order on rank ties and display raw and normalized loss
counts separately; raw losses are never erased or reported as zero.

Actual retained data: nine ledgers contain 353 record lines, including 306 build
record lines. The old filter admits 55; the canonical rank admits 266, including
211 records hidden solely because they have raw address/layout differences.
These are per-file saved record counts, not unique new executions or new matches.
All ledger bytes remain unchanged. The CLI reports input/source hashes.

The regression runs the actual old read-only best branch on copies of every
retained ledger and the new CLI, checking all selected attempt IDs and ordering.
For Windows only, its baseline copy omits the unused `fcntl` import; no old
query function changes or compiler/process mocks are used. Additional controls
exclude failed records with leftover metrics and incomplete records.

This changes saved-record queries only, not history, active caches, BEST.json,
program source, scorer semantics or acceptance. Normalized no-loss metrics remain
saved finite diagnostics; they do not prove raw/whole-ELF equality, current source
binding, runtime behavior or security acceptance. Source transitions require
reviewed digest updates, and the historical legacy query remains unchanged.
