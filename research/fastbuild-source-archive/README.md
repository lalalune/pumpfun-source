# Preserve the previous build's source binding

`fastbuild` archives prior ELF outputs and `build.log`, then writes a new
`source-inputs.json` at the same output path. The original source receipt is not
in the archive list, so a normal rerun permanently replaces the old ELF's source
binding even though its binary and log were deliberately retained.

Archive `source-inputs.json` together with the same attempt's ELF/log files. New
attempts still publish their own current source receipt. No source, compiler,
matching, normalization or receipt schema changes.

Current main also archives the genuine `link-receipt.json` and `link.map` from its
pinned link-order hook. Keep those entries and add the source receipt to that
same attempt archive. The current-main proof additionally compares both archived
link artifacts byte-for-byte with their actual producer outputs.

The proof performs an actual cold Pump compilation with the authenticated v1.44
identity SDK, checks its genuine producer source receipt against the returned
source digest, then reruns the same workspace/output with a temporary source copy
containing an explicit `compile_error!`. That second real compiler invocation must
reach the controlled error. It then verifies the archived actual ELF hashes and
all 1035 byte-window memberships, and requires the exact old source receipt to be
alongside them. Old and new source manifests must differ. No compiler or successful
ELF is simulated, and the original repository Rust is never changed.

Run on a provisioned macOS ARM64 host with the documented pinned SDK:

```sh
python -B research/fastbuild-source-archive/reproduce.py
```

The original failed evidence, real ELF gzip files, compiler log and source receipts
are retained in `work/scoped-proof`. This is provenance/file-preservation evidence,
not a new source-matching gain, VM execution or whole-program equivalence claim.
