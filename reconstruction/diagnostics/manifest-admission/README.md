# Bounded manifest admission during revalidation

This entrypoint admits the reviewed `scripts/revalidate_all.py` bytes, executes
those same bytes, and replaces its manifest checker with this package's bounded
flat-manifest checker. The current root revalidator already records malformed
manifests as per-packet failures and rejects nonregular payloads; this wrapper
retains its narrower nonempty flat-map format. Both runners require every
available check to pass before classifying a packet as a pass.

```sh
python -B reconstruction/diagnostics/manifest-admission/run.py --output work/manifest-audit-new
python -B reconstruction/diagnostics/manifest-admission/test_run.py
```

The checker accepts nonempty relative POSIX path-to-lowercase-SHA256 maps,
validates all declarations before reading payloads, and rejects symlink/reparse
payloads. Malformed shapes become per-packet failures. The wrapper refuses an
existing output or dangling output symlink. The admitted revalidator stages the
complete audit and publishes it without replacing a late destination on supported
hosts. Canonical root scripts and historical packets remain unchanged by this
entrypoint repair. A future reviewed revalidator change requires refreshing the
source digest.

The retained-packet test copies all eight declared files, including `archived/`.
Its unchanged manifest passes 8/8; array and directory variants fail. Those copies
are deliberately renamed and are outside the root runner's explicit `--repo`
allowlist, so their verifier failures remain failures. The generated audit's own
integrity verifier passes without implying that all audited packets passed.
A separate complete CLI control has one passing manifest and verifier; source
mutation, source replacement after admission, existing and dangling-link outputs,
late empty directories and staging failure are also exercised.

This wrapper does not authenticate unsigned manifests, prove payload correctness,
freeze packet verifier source before execution, or establish VM/source/security
acceptance. Use a reviewed checkout: packet `verify.py` scripts still execute
through the retained runner. Prefer a fresh output outside existing research
packet directories.
