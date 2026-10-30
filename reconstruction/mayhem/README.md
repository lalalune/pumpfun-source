# Mayhem exact-source staging inputs

The maintained `programs/mayhem/build_exact.py --stage-only` command needs sealed
recipe files that were absent from the current tree. The restored 101 files are
byte-for-byte public Git blobs from
[`decb244ccf8a81b086e940568a2d03336309046f`](https://github.com/lalalune/pumpfun-source/commit/decb244ccf8a81b086e940568a2d03336309046f),
the commit that introduced the maintained entrypoint. They retain their original
paths so that the entrypoint, its sealed parent stager, hashes, scripts, host
source archives and target-input inventories remain unchanged.

Only the consumed closure is restored: the locator pins and derived script,
sealed source stager, fresh-host build scripts, controller and host inputs.
Historical output ELFs, build directories and proof results are not restored or
promoted. `recovered-stage-inputs.json` records each original Git blob, SHA-256,
size and mode. This attributes the restored recipe to its existing authors;
the new contribution repairs its missing-input dependency.

From the repository root, with a new output directory:

```sh
python3 -B programs/mayhem/build_exact.py --stage-only --repo . --output /tmp/mayhem-stage
python3 -B reconstruction/mayhem/verify_stage.py --repo . --stage /tmp/mayhem-stage
python3 -B reconstruction/mayhem/test_exact_stage.py
```

The real CLI validates all 67 current source files and stages the existing recipe
with its explicit 539-selector Cargo-filename locator transformation. The
independent verifier authenticates all 101 restored files against the pinned
public-blob manifest, then checks the 67 decompressed staged sources, 98 recipe
files and stage receipt. Neither command compiles or executes a target program.
Use `verify_stage.py --repo .` to authenticate just the restored inputs.

The tests run the actual CLI from a path containing spaces. They preserve its
missing-input failure, reject changed sealed stager/linker inputs and canonical
Rust, prove existing output is not overwritten, and reject archive or recovery
manifest mutations. The stage-only CLI's own early seals cover its parent
stager, linker scripts and 67 source files; the separate verifier authenticates
the entire restored closure, including host archives before any build is attempted.

A real exact build still requires the pinned Windows SDK, target sysroot, vendor,
MSVC and Windows SDK inputs accepted by the existing entrypoint. No fresh
compilation, fresh ELF equality, runtime equivalence or checkpoint-count change
is established by this staging repair. The original published equality receipts
retain their historical scope.
