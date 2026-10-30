# Proposed analyzer asset transition: resolve the current evidence root

`scripts/analyze.py` reads inputs and writes outputs through its current `ROOT`,
but `program_names(root=ROOT)` captures the import-time root. Redirecting analysis
to an isolated retained-evidence tree therefore enumerates the checkout's four
programs and attempts to read them in a tree that contains only Mayhem. The real
interface-inventory workflow already demonstrates this failure.

Use `root=None` and resolve the current module `ROOT` at invocation. Explicit
root arguments keep their existing precedence. Both the archived-selector and
captured-original fallback now select from the same root as the rest of analysis.
No ELF parsing, instruction attribution, score, program source or capture changes.

This is the proposed one-file script asset transition for review, consistent with
the current on-chain tooling scope in CONTRIBUTING.md. No script is added/removed
from `scripts/`, no frozen checkpoint is re-sealed, and no historical result is
overwritten. `transition.json` binds the base and proposed script text.

Before/after on base `1cacecfbf`:

- `python -X utf8 tests/test_analyze_runtime_root.py`: before 2 failures / 1 pass;
  after 3 pass. Uses the complete retained 777408-byte Mayhem ELF, SHA-256
  `a87fa9f866272514e6acb852b668c4a08aeb173d56c883039991d114d1199bdb`,
  and actual retained upstream IDLs. Positive control preserves explicit-root
  selection. Both current-root fallback and archived mapping are covered.
- `python -X utf8 scripts/test_analysis_interface_inventory.py`: before three
  errors (including missing Pump in the Mayhem-only root); after one test passes
  with both CP936 and UTF-8 default-encoding subcases.
- `python scripts/verify_evidence.py`: 9 retained captures pass.
- `python -X utf8 scripts/test_tooling.py`: attempted but blocked on this Windows
  host by its pinned solders 0.27.1 wheel: `solders.litesvm` imports `FeatureSet`,
  which that native wheel does not export. This occurs before tests execute; no
  VM capability, passing full suite or mocked replacement is claimed.

The explicit root test is local filesystem/ELF analysis, not a VM or compiler run.
No new match count, native behavior or security acceptance is established.
The original report schemas, capture bytes and existing valid default checkout
behavior stay the same. Generated evidence is written only into temporary roots.
