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

Argument setup also stops at intervening external and indirect calls, even when
the census selects only internal call sites for alignment. The retained Pump
window `0x1ab918` calls through `r4` before setting `r1` and `r2` for its next
internal call; its earlier `r3` and `r4` writes must not be carried across that
call. `reconstruction/harness/test_census_call_barriers.py` checks this and a
retained `sol_memcpy_` call, plus unchanged scalar/pointer controls. It invokes
the production API with text decoded from actual capture bytes by the repository
decoder, without replacing analysis functions. This API test does not qualify
a complete SDK/objdump census run or establish argument liveness across branches.

The census external-call counters resolve type-10 relocation symbols from the
same loaded ELF bytes. Keys such as `symbol:abort` and `symbol:sol_log_` preserve
identity that the common `ffffffff` placeholder cannot convey; non-relocated
hash-immediate keys keep their existing hexadecimal format. This uses the
repository's pinned `pyelftools` dependency. Internal-call graph refinement and
score acceptance remain unchanged. `test_census_external_symbols.py` compares
the captured CTO window with the retained multihop-sell-fees compiler artifact;
its real census CLI test additionally runs when `PUMP_OBJDUMP` names an SBF tool.
That CLI control also compares JSON and Markdown across Python hash seeds;
callee identities break ties between identical display names in report rows.
Census disassembly uses a temporary snapshot of each loaded image. If a build
replaces or removes the original candidate path during analysis, argument text
still describes the bytes used for call sites and the recorded candidate hash.
`test_census_disassembly_snapshot.py` exercises unchanged, replaced and removed
paths with retained compiler artifacts when `PUMP_OBJDUMP` names an SBF tool.

Each JSON/Markdown report is now completed in a private sibling file before
no-replace publication. An ordinary write failure leaves that destination absent,
so the same command can be retried; an existing or late report stays intact.
The [actual retained-data proof](../../../research/census-report-publication-20261101/README.md)
exercises file-size failures and same-path retries without changing diagnostics
or archived source pins. This protects each report independently, not a transaction
across several requested outputs or power-loss durability.
