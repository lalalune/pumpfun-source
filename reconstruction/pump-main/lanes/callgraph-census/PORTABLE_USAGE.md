# Running retained census tools

The scripts resolve harness imports relative to their checkout. Supply `--cand` explicitly to census.py, callid_audit.py and dataref_audit.py; no contributor-specific baseline is selected. The existing harness's SDK discovery requirements still apply.

For a different source layout, pass `census.py --pairs pairs.json`, where the JSON object maps original addresses to candidate symbol regexes, for example `{"0x14f4e0":"buy_exact_sol_in$"}`. This replaces the historical pairing map for that run. Duplicate addresses, invalid regexes, missing original windows and unmatched symbols fail rather than silently dropping a pair. Without --pairs the historical map remains available. --only limits reported targets, not identity refinement.

Example: `python reconstruction/pump-main/lanes/callgraph-census/census.py --cand /tmp/pump-out/unstripped.so --pairs /tmp/pairs.json --json /tmp/census.json`.

These reports remain diagnostics, not scoring acceptance or runtime-equivalence evidence. Existing archived census packets are unchanged.

`capture_inline.py` temporarily adapts the harness compiler command to `cargo rustc`
with `-C remark=inline`; `--lines` additionally requests source locations. The hook
is restored after the build, including failures. A failed build returns a nonzero
status and retains its compiler log; it is not a successful remark capture.
`--parse-only` only parses an existing log and does not rerun the compiler.

The real offline SBF regression is available with
`PUMP_INLINE_TEST_SDK=/absolute/path/to/platform-tools python -m unittest discover -s reconstruction/harness -p test_inline_capture_compiler.py`.
It requires the official macOS v1.44 SDK and rsync. It compiles only a dependency-free
diagnostic fixture, with normal and line-bearing remarks plus a compiler-error
control; it does not rebuild or execute a captured program.
