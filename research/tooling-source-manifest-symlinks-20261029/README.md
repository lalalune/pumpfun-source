# Symlinked compiler inputs in the source manifest

`scripts/build_source_manifest.py` walks a crate with `Path.rglob`, accepts every
`p.is_file()` result, and returns only `path -> sha256`. `is_file()` follows
symlinks, so a symlinked `.rs` file inside the crate is reported under its
in-repo path while its bytes come from outside the repository. A later copy
step would compile those external bytes under the local source name, and the
manifest would not reveal the substitution.

The archived helper is left byte-exact. `scripts/pump_build_verified.py` now
imports `scripts/source_manifest_guard.py` and uses its strict admission check
instead of calling the archived helper directly. The production Pump build path
therefore no longer accepts a symlinked compiler input.

## Result

The real `programs/pump` manifest has 65 entries and no symlinks; the strict
wrapper returns exactly the archived manifest. On a detached temporary crate,
the archived helper accepts `crate/src/lib.rs -> ../outside.rs` and records the
external hash under the in-repo key. The strict wrapper raises
`symlinked compiler input`. An extra-input directory containing a symlinked
asset is also rejected, and a path outside the repository raises
`compiler input resolves outside repository` without walking to the filesystem
root.

The archived script, the real source tree and all reports remain unchanged.
`scripts/pump_build_verified.py` is the only production caller changed.

## Method and limits

The reviewed helper (LF or CRLF form) is loaded and hash-checked. The production
guard `scripts/source_manifest_guard.py` checks every reported file and every
supplied extra-input file for symlinks and for a resolved path outside the
repository before returning the manifest. The packet compares the reviewed
helper's output with the production guard's output on the real repository, and
its tests assert that `pump_build_verified.source_manifest` is the production
guard. `observations.json.gz` records the 65 files and the empty symlink set;
`coverage-delta.json` records only those totals.

This is an admission check for local compiler inputs. It does not build the
crate, prove that the recorded files are the historical source, validate Cargo
feature resolution, or claim whole-program equality. It does not modify the
frozen `build_source_manifest.py`; existing evidence that pins that helper is
preserved.

## Verification

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B research/tooling-source-manifest-symlinks-20261029/verify.py --repo .
PYTHONDONTWRITEBYTECODE=1 python3 -B research/tooling-source-manifest-symlinks-20261029/test_verify.py
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/verify_evidence.py
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/test_tooling.py
```
