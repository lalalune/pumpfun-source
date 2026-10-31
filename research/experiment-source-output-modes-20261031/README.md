# Preserve exact execute modes in experiment source and output identity

Original reproduction base: `90300f9d2efe3ef014b116172251a41bfb104d78`.
Integrated main: `ed47ac72a632e54a4d5ca9a192912c8d5b40faf2`.

Source and retained-output manifests recorded only whether any execute bit was
set. Changing a file owned by the current user from mode `0700` to `0601` keeps
that Boolean true but removes the owner's permission to execute it. The cache
therefore reused a passing experiment even though a fresh run failed. It also
reused a retained executable artifact that the same user could no longer run.

Record the owner/group/other execute mask alongside the existing Boolean and
content digest in both manifests. Source changes now change the experiment key;
changed output modes invalidate the retained artifact and cause a new attempt.
Historical attempts remain intact. Write-only mode changes keep valid hits.
Declared external inputs already had this exact mask after #3558; this change
closes the separate source-tree and output-manifest paths.

```sh
python -B reconstruction/harness/test_experiment_source_output_modes.py
python -B -m unittest discover -s reconstruction/harness -p 'test_experiment*.py'
python -B scripts/verify_evidence.py
python -B scripts/test_tooling.py
```

The new test runs real Python and shell processes, copies an actual executable
into the output, changes its mode, and checks actual OS execution. Both stale
reuse cases fail on the base and pass with the fix. The write-bit control stays
cached. Three new tests pass; the complete experiment suite reports 64 tests
with one explicit SDK-dependent skip. Integrated-main checks pass all nine
captures and 250 tooling tests. CI invokes the regression.

Proof is on macOS arm64, Python 3.12.13 with ordinary user permissions. The
regression skips root and non-POSIX environments because they do not provide the
same permission control. Ownership, ACLs, read/write permissions and changes
restored between checks are outside this execute-mode identity. No compiler,
reconstructed program or SBF identity result is claimed.
