# Qualification setup history

The initial public verifier rejected Cargo.lock permissions `0600` in this sparse
checkout (Git records `100644`). Incoming checkouts now authenticate file bytes/types;
staging applies the exact measured Git modes to owned copies before the namespace
probe. The measured cold source and all compiler inputs were unchanged.

The first required-tooling export omitted current scorer sibling original_input.py
(169 tests/two errors). Adding its sparse pattern reapplied sparse checkout and
removed 49 previously admitted out-of-pattern files (157 tests/10 failures/92 errors).
The next fully restored export identified score_admission.py as the other current
scorer sibling (169 tests/two errors). Both real tracked imports are now present;
all 67 read inputs authenticate to the tested Git tree, and the final169-test run
passes. Every failed gate log is retained; none is an upstream source defect or
a new Relay execution. No test/source shim or assertion weakening was used.

The original actual cold build failures and corrected successful measurement are
separately sealed in measurements/. This setup history does not retarget them.
