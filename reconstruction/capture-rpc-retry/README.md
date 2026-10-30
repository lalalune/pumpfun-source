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
