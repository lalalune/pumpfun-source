# Portable retained census diagnostics

The saved callgraph census tools import their harness through an absolute path
in the original contributor's checkout. In another checkout, even `--help`
fails before argument parsing. This successor supplies repository-relative module
bindings while retaining every archived lane source and saved report unchanged.

```
python -B reconstruction/diagnostics/census-portability/run.py hotness --remarks input.log --json work/hotness-new.json
python -B reconstruction/diagnostics/census-portability/run.py census --help
python -B reconstruction/diagnostics/census-portability/test_run.py
```

Reviewed lane hashes are admitted before running a fixed tool choice. Actual
repository score/win/coords modules are loaded without replacing their functions.
Authoritative Pump ELF/functions inputs are staged in a disposable base, avoiding
Windows Git symlink-text failures and writes to the shared window cache. Existing
JSON/Markdown outputs are refused so retained diagnostics are not overwritten.

The regression runs the actual old hotness CLI (import failure) and the successor
over the real retained CENSUS and Pump capture. The complete new 16-target report
preserves every retained original error site. Real source notes provide an
explicit no-remarks control; no LLVM remark or compilation is fabricated.
All five real CLI parsers start; occupied output bytes remain unchanged.

Full graph/data-reference/candidate commands retain the archived external SDK,
objdump and explicit unstripped-candidate requirements. They were not qualified
by a `--help` check. This does not reconstruct programs, change scorer masking,
prove source/runtime equivalence or qualify security. Frozen helper and historical
lane/report bytes remain unchanged; the source pin requires review on transitions.
