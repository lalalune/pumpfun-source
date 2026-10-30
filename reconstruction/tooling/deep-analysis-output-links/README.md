# Preserve external files during deep-analysis publication

Both deep-analysis generators admit existing packet files with `exists()` and
`is_file()`. Those predicates follow links. An allowed name such as `summary.json`
can therefore redirect a successful analysis write into a different retained
file. A dangling link is admitted as absent, and a linked output directory is
also followed. This affects the two independent CLIs, so both are repaired here.

Base revision: `59d90994bb46cfe840f158ac5b102713145e7b4c`.

The actual Mayhem CLI reproduction on Windows replaced an external 21-byte
sentinel with 849 bytes from deep disassembly or 772 bytes from section analysis;
both commands exited zero. The regression suite runs both real CLIs with the
captured Mayhem ELF and filesystem links, without replacing parsers or filesystem
calls. It checks existing and dangling links at `summary.json`, `verify.py` and
`manifest.json`, output-directory symlinks, and native Windows directory junctions.
All 16 negative cases were accepted at base. After the change they fail before
publication, preserving link targets and directory contents.

Each generator now uses `lstat()` to reject direct output-directory links and
linked packet entries before the first write. Windows reparse attributes/tags
are rejected as well. The helpers stay local to preserve the generators' existing
import dependencies. Ordinary output regeneration remains supported.

Run with Python 3.12:

```sh
python -B reconstruction/tooling/deep-analysis-output-links/test_verify.py
```

The four tests pass on native Windows Python 3.12.14, including the junction test.
On other systems that test is explicitly skipped. Both regular generated packets
verify and remain byte-identical on repeated generation. A separate base-versus-
fixed run also found all 21 generated files unchanged (12 disassembly, 9 section),
including manifests and generated verifiers. `evidence.json` retains those hashes
and the before/after CLI outcomes.

Affected existing publication tests (2 + 2), encoding tests (2), disassembly
reproducibility test (1), and interior-string-reference tests (2) pass. All nine
saved captures verify. The required root tooling suite passes all 187 tests on
WSL Linux Python 3.12.14 with the pinned Linux `solders==0.27.1` package. The
initial sparse checkout lacked the tracked base ELF and imported config snapshot;
materializing those inputs resolved its setup failures. Existing unclosed-reader ResourceWarnings remain unchanged.

This is bounded output admission, not atomic publication or a filesystem sandbox.
It does not reject hard links, symlinked ancestors, or concurrent path replacement.
No program source, captured bytes, historical packet or sealed source hash is
changed. The proposed asset transition binds the two changed root scripts; it
does not rewrite or requalify historical snapshots. Existing related fixes cover
`analyze_program.py` (#2246), `analyze.py` (#2258), and `bytecode_signatures.py`
(#2458); neither deep generator was covered by those changes.
