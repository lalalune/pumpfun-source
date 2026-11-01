# Preserve retryable census report destinations

The maintained portable census adapter promises to retain occupied diagnostic
outputs. Its exclusive direct write correctly refuses another writer, but a real
file write failure leaves an incomplete final file. The next unlimited run then
refuses that file as occupied. This affects the shared JSON/Markdown publisher,
independently of the diagnostic's calculations.

On exact base `60a42309a4908577f0a386513eeaee6cd6f84f42`, the actual documented
hotness command with retained `CENSUS.json` and `NOTES.md` creates a 64-byte
truncated JSON or Markdown file under an OS file-size limit, then rejects retry
with exit 2. With this correction it leaves neither final file nor temporary
file; the same unlimited command succeeds. All sixteen targets and original
error-site records are preserved. Complete JSON (9,424 bytes) and Markdown
(4,050 bytes) outputs are byte-identical to the base controls.

Complete each report in an exclusively created sibling file, then publish without
replacement: a hard link on POSIX, a refusing rename on Windows, following the
existing `scripts/probe_report.py` pattern. Cleanup checks ownership of the stage.
Ordinary file creation retains the caller umask, and bounded staging names keep
valid long basenames usable. Existing and late writers remain preserved.

This extends the per-destination protection accepted in
[#3574](https://github.com/lalalune/pumpfun-source/pull/3574) by espressoamer-sudo,
and retains the argument/occupied-link guards from
[#2687](https://github.com/lalalune/pumpfun-source/pull/2687). It does not claim a
transaction across multiple requested report files. The archived lane code,
reviewed hash map, source admission and diagnostic calculations remain unchanged.

## Actual before/after proof

```sh
python -B research/census-report-publication-20261101/probe.py --repo . \
  --revision 60a42309a4908577f0a386513eeaee6cd6f84f42 --expect base --output /tmp/census-before.json
python -B research/census-report-publication-20261101/probe.py --repo . \
  --expect fixed --output /tmp/census-after.json
python -B -m unittest discover -s reconstruction/diagnostics/census-portability -p 'test_*.py'
python -B scripts/test_tooling.py
python -B scripts/verify_evidence.py
```

The same proof copies exact selected adapter/harness/lane sources, retained census,
source notes, Pump capture and selected-window inventory into an owned temporary
cohort. Eight actual CLI runs per revision cover each format's normal write,
64-byte limit, same-path retry and late occupied destination. A Python profile
observer applies the OS limit immediately before the real report write, after
input staging and real analysis. It changes no production function or generated
report. A separate observer control creates an owned late report at that boundary.
The existing notes deliberately contain no compiler inline remarks: none are
fabricated, and this proof makes no new remark-parsing claim.

The checked-in results omit only traceback tails; private execution outputs retain
them. Sources, capture, selected-window inventory and original report bytes are
bound by SHA256 and remain unchanged. Ten focused methods pass, including the
actual proof, existing occupied/abbreviated/dangling-link controls, all five tool
parsers, late-write preservation and two real CLI long-name/umask controls.
All 255 required tooling tests and all nine saved capture checks also pass.
Existing CI already invokes the extended output-guard module.

The actual proof runs on macOS arm64 / CPython 3.12.13 and executes no compiler,
program image or VM. It qualifies the hotness producer and the adapter's shared
publisher, not a full census/callid candidate analysis. The Windows publication
branch follows the existing repository pattern but was not executed locally.
Unsupported hard-link filesystems fail without publishing a partial final file.
No all-files transaction, power-loss durability or cleanup after an uncatchable
kill is claimed. The unchanged mandatory tooling suite contains its existing
runtime fixtures; saved capture verification does not establish reconstruction.
