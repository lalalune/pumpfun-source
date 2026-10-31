# Portable retained census diagnostics

The saved callgraph census tools import their harness through an absolute path
in the original contributor's checkout. In another checkout, even `--help`
fails before argument parsing. This successor supplies repository-relative module
bindings while preserving saved reports. The census source pin now includes the bounded
argument-normalization correction described below.

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
prove source/runtime equivalence or qualify security. Frozen helpers and historical reports remain unchanged; the source pin requires
review on transitions.


Argument setup retains scalar immediates, including large MOV and LDDW constants.
Only a LDDW whose value `score.normalize` identifies inside an ELF section is
shown as `ADDR`. The previous text heuristic erased every hexadecimal value with
five or more digits, including captured Pump's `mov64 r3, 0x10001` at `0x1afd68`.
The reviewed census hash is updated for this source correction; retained CENSUS
reports are historical results and have not been regenerated or reinterpreted.

`reconstruction/harness/test_census_argument_constants.py` checks actual Pump
capture instruction bytes even without objdump, plus real capture disassembly
(scalar and section-pointer controls) when objdump is available. With the explicit
`PUMP_BUILD_TEST_SDK`, it also compiles four real SBF fixtures differing in MOV or
LDDW scalar arguments. Set `PUMP_OBJDUMP` to the real SDK objdump if needed.
These diagnostics remain heuristic and do not change official score acceptance.

The data-reference length hint stops at calls, jumps and exits. In the retained
Pump window `0x132510`, a load of a 32-byte value is followed by a call and then
the unrelated scalar `r1 = 2`. Previously that scalar limited comparison to two
bytes and hid a difference in the third byte under the default width of 16.
`reconstruction/harness/test_dataref_length.py` runs the actual CLI on temporary
symbolized capture copies: differences inside the requested width are flagged,
an unchanged copy stays clean, and the genuine two-byte string at `0xa8f0` still
excludes neighbouring bytes. A candidate target with fewer available bytes than
the original also reports the unequal extents, instead of declaring their common
prefix clean. A complete matching relocation and an explicitly narrower comparison
remain clean. Capture files and retained reports are unchanged.
