# Saved AMM attempts ranked by the canonical no-loss rule

The legacy `attempts.py best` filters `lost_windows_count == 0`, a fixed-address
raw comparison. The scorer's canonical `sell_score.rank` instead requires
`lost_windows_normalized_count == 0`; the maintained AMM harness README explains
that a sell-size change can move every later raw address without regressing those
functions. The read query therefore hides candidates that its own canonical
best-publication rule admits.

```
python -B reconstruction/diagnostics/amm-ledger-best/read.py --ledger scripts/amm_sell/attempts/seed.jsonl --limit 10
python -B reconstruction/diagnostics/amm-ledger-best/test_read.py
```

This read-only successor admits only the reviewed pure `rank` function from
the `sell_score.py` AST, together with the module constants that function
reads. It does not import or run the builder, scorer,
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
binding, runtime behavior or security acceptance. Rank-function transitions
require reviewed digest updates; unrelated builder maintenance does not. The historical legacy query remains unchanged.

The binding covers the unique top-level synchronous `rank` function's complete
LF-normalized source, including its signature, body and any decorators, plus
every module-level constant it reads (`SELL_SIZE`), so a changed size can no
longer re-rank the ledger silently. #2781 moved the function from `try_sell.py`
to `sell_score.py` and replaced its size literal with that constant; this
binding follows it. Changes elsewhere in the scorer do not invalidate this
read-only query. The complete scorer source SHA-256 is still reported as
`rank_source_sha256`, and no other module statements are imported, compiled or
executed. A changed or duplicate rank is refused.

The legacy CLI comparison uses the exact pre-fix source retained at1e04f5b
(SHA256 e58a8f721e29136d024b7befdd4bf7aada5c62dcf6faddb6a8a87452a34e20d1). This test-only text fixture runs
only its read-only best branch; the original file and ledger remain unchanged.
The current attempts CLI has independently changed version partitioning (#2094),
so it is no longer a valid pre-fix oracle for this historical eligibility gap.
Only Windows staging omits the old unused top-level fcntl import.
