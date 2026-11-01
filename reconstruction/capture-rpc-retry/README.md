# Capture retries after RPC failure

The archived `scripts/capture.py` creates its destination before RPC reads.
A missing account leaves an empty directory; exhausted genesis requests leave
account binaries without a manifest. Both failures block the next attempt at
the same destination.

`capture_retry.py` admits the archived source by SHA-256 before executing it.
Since #2423, `scripts/capture.py` itself stages every write in a sibling
temporary directory, renames it into place only after all RPC reads, validation
and report construction succeed, and removes the stage on failure; it keeps the
early existing-destination check and re-checks before the rename. The adapter
therefore executes the reviewed bytes unmodified; the earlier in-memory deferral
of `mkdir` and binary writes would now collide with that staging and is gone.
No deletion of prior output is performed. The callable `capture(url, name, key, out)`
keeps the archived function's arguments, output schema and RPC policy.
The authenticated source is explicitly compiled with `optimize=0`. Since #2440
its validation uses explicit checks rather than `assert`, so this is a second
layer keeping capture validation active under `-O`, `-OO` or `PYTHONOPTIMIZE`.

This package follows `scripts/README.md`'s frozen-directory rule. The archived
Python file set, source bytes, captured accounts and prior packages stay intact.

Tested base: `ee11fc91dc7768f5a92936dd98f6c850bdb08bd7`. Source binding:
`scripts/capture.py`, SHA-256
`329eaa1bda93034ee4147b4a6a3bea66ddd5403c1e79bc591c58fc75942a8465`.
This binding includes the reviewed #1289 source transition (program-address
selection only), #2423 (staged publication after success) and #2440 (explicit
checks instead of `assert`).

Run from the repository root:

```sh
python3 -B reconstruction/capture-rpc-retry/test_capture.py
python3 -B scripts/test_tooling.py
python3 -B scripts/verify_evidence.py
```

The loopback JSON-RPC fixture serves unchanged retained associated-token and
SPL Token account bytes. Four failure/retry cases cover missing accounts and six
failed genesis requests for both loaders. A fifth case preserves existing output
without any RPC request. Successful retries compare all binary bytes and stable
manifest fields. Only retry delays are patched. Optimization-mode probes also
exercise every archived loader, header, ELF and re-read assertion under ordinary
Python, `-O`, `-OO`, `PYTHONOPTIMIZE=1` and `PYTHONOPTIMIZE=2`.

Limits: this is offline capture-tool behavior, not a live RPC or program runtime
qualification. Publication is a single directory rename; a crash that
prevents the `finally` cleanup can leave a hidden `.<name>.capture-*` stage
beside the destination, never a partial destination. The archived CLI's missing `repro/programs.json` selector remains
separate work in PR #1289.

The current adapter also admits the reviewed UTF-8/LF-only writer update.
Its source binding is `d332969152829dc75dc855dc93f3132b9d6674b9765aee3be3bfe0f5c4453a5d`;
RPC, parsing and admission behavior are unchanged. The earlier binding above
identifies the historical baseline.

The adapter also rechecks account metadata after the initial observation:
program rereads must retain the loader owner and `executable: true`, and the
sliced ProgramData reread must retain its loader owner and `executable: false`.
Identical account data alone does not establish these properties. These checks
use uniquely anchored in-memory substitutions after authenticating the same
archived source hash; no archived script or capture bytes change.

`python -B reconstruction/capture-rpc-retry/test_metadata_rechecks.py` serves
retained Associated Token and SPL Token accounts over loopback HTTP. Six owner
or executable changes at the reread boundaries must leave no published capture
or abandoned stage; unchanged responses preserve the retained ELF bytes.

Since `fcfebcf73` and `77e3ff4ce`, the archived capture publishes through
`deep_disassembly.rename_directory`, a native no-replace rename, instead of
`Path.rename`. Its source binding is
`44bf6a2cdc987eeea9c5947bdd89f9b9fbd263d62cbc4876966125f1f5d3a482`. The adapter
admits only that function's source (`ast` segment, SHA-256
`36cbb216db93f59f699edbd8c46f798f8fdbf180bfcfa20fefd2a645a06d6cde`). It compiles
the function with `optimize=0` against `ctypes`, `errno`, `os` and `sys`, and
supplies it in place of the archived lazy import. The rest of
`deep_disassembly.py`, including its `window_elf_reader` import, is never
executed, so unrelated analysis edits do not re-break this adapter. A changed
rename body is refused before any capture code runs. Three tests cover the
changed body, an unrelated module edit, and refusal of an existing empty
destination.
