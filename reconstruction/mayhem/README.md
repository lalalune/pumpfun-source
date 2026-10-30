# Mayhem exact-source staging inputs

The maintained `programs/mayhem/build_exact.py --stage-only` command needs sealed
recipe files that were absent from the current tree. The restored 101 consumed files
and their original eight-byte Git checkout policy are
byte-for-byte public Git blobs from
[`decb244ccf8a81b086e940568a2d03336309046f`](https://github.com/lalalune/pumpfun-source/commit/decb244ccf8a81b086e940568a2d03336309046f),
the commit that introduced the maintained entrypoint. They retain their original
paths so that the entrypoint, its sealed parent stager, hashes, scripts, host
source archives and target-input inventories remain unchanged.

Only the consumed closure is restored: the locator pins and derived script,
sealed source stager, fresh-host build scripts, controller and host inputs.
The original `research/mayhem-fresh-host-20261028/.gitattributes` preserves sealed
CRLF JSON bytes on Windows checkouts. This 102nd restored file is a checkout
dependency, separate from the 101 files consumed by staging. Three narrow root
attribute rules also preserve the current Mayhem sources, the locator package
and the sealed parent stager outside that subtree. No Rust or entrypoint bytes change.
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
manifest mutations. A real local Git add/checkout round trip with
`core.autocrlf=true` covers all restored inputs, current source/entrypoint and new
reconstruction files, then runs the real stager. Without the three root rules,
that method changes 70 hash-bound files; with them, every checked byte survives
and all 67 sources stage. This tests Git conversion locally, not a native Windows
compiler. The stage-only CLI's own early seals cover its parent
stager, linker scripts and 67 source files; the separate verifier authenticates
the entire restored closure, including host archives before any build is attempted.

A real exact build still requires the pinned Windows SDK, target sysroot, vendor,
MSVC and Windows SDK inputs accepted by the existing entrypoint. No fresh
compilation, fresh ELF equality, runtime equivalence or checkpoint-count change
is established by this staging repair. The original published equality receipts
retain their historical scope.

The restored JSON bytes intentionally retain CRLF. A default `git diff --check`
flags those historical carriage returns; no sealed bytes were normalized. The
same check with `core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol`
passes, and the newly authored files pass the default whitespace check.
