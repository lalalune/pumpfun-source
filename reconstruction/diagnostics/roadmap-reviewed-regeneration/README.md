# Reviewed-source roadmap regeneration

The archived call-classification generator derives an allowed CRLF digest from
the current source bytes at import time. A changed CRLF script can authorize
itself. The archived packet verifier separately checks its fixed input manifest;
this defect concerns direct regeneration with `proof.py`, not that verifier.

Use this guarded entrypoint for new regeneration:

```
python -B reconstruction/diagnostics/roadmap-reviewed-regeneration/generate.py --output work/reviewed-roadmap-new
python -B reconstruction/diagnostics/roadmap-reviewed-regeneration/test_generate.py
```

The guard admits LF or CRLF serialization of fixed reviewed roadmap and proof
hashes before importing either. It writes a fresh observations/input/manifest
packet and refuses occupied outputs. Original scripts, archived packet files and
observations remain unchanged. Tests run the actual legacy generator and guarded
generator over three authentic retained captures in isolated temporary layouts.

This admission boundary does not certify the archived analysis. In particular,
its historical relocation-only syscall classification is retained, not corrected
or endorsed here. Raw input hashes bind the chosen newline form. An unsigned
manifest is local integrity evidence, not authorship authentication, equivalence
or security acceptance. The archived entrypoint remains available with its
original limitation; use this explicit successor when regenerating.
