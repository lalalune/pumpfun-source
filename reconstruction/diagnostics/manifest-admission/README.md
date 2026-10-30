# Bounded manifest admission during revalidation

The retained batch revalidator assumes every parsed manifest is an object and
silently skips directory targets. Valid JSON arrays/null/strings can abort the
whole audit; a declared payload replaced by a directory can pass with fewer
checked files than expected.

```
python -B reconstruction/diagnostics/manifest-admission/run.py --output work/manifest-audit-new
python -B reconstruction/diagnostics/manifest-admission/test_run.py
```

This reviewed-source successor overrides only manifest admission in the actual
batch workflow. It accepts nonempty flat relative-POSIX-path/lowercase-SHA256
maps, validates declarations before reading payloads, and rejects nonregular or
symlink/reparse targets. Errors become per-packet failures instead of uncaught
exceptions or skipped files. It refuses an occupied audit output. The frozen
root helper and historical packets remain byte-for-byte intact.

The real CLI regression copies an authentic seven-file retained packet into
three isolated packet directories. The unchanged manifest passes 7/7; a JSON-array
manifest and a declared directory fail without stopping other manifest checks.
The retained packet's verifier requires --repo, which the archived batch runner
does not supply (#1709); its failure is preserved. Under the current all-checks
conjunction the overall rows therefore remain failures. The generated audit's
own integrity verifier passes; this does not mean its audited packets passed.

This guard covers the flat manifest format the retained checker supports. It
does not authenticate unsigned manifests, prove payload correctness, execute a
VM, or establish equivalence/security acceptance. The current root revalidator's all-available-check conjunction is preserved unchanged. Other limitations remain.
Use a fresh output outside the research packet directory. Existing verifier
scripts still run through the retained revalidator, so use a reviewed checkout.
