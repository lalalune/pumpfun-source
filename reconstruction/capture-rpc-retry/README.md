# Capture retries after RPC failure

The archived `scripts/capture.py` creates its destination before RPC reads.
A missing account leaves an empty directory; exhausted genesis requests leave
account binaries without a manifest. Both failures block the next attempt at
the same destination.

`capture_retry.py` admits the archived source by SHA-256 before executing it and
adapts its two loader branches in memory. It defers directory creation and binary
writes until all RPC reads, validation and report construction succeed. It retains
the early existing-destination check and final exclusive `mkdir`. No cleanup or
deletion of prior output is performed. The callable `capture(url, name, key, out)`
keeps the archived function's arguments, output schema and RPC policy.
The authenticated source is explicitly compiled with `optimize=0`, so its capture
validation assertions remain active even when the adapter runs under `-O`, `-OO`
or `PYTHONOPTIMIZE`.

This package follows `scripts/README.md`'s frozen-directory rule. The archived
Python file set, source bytes, captured accounts and prior packages stay intact.

Tested base: `ccd3330bfd12ed04c3a598af9a2ab95ed5de77ac`. Source binding:
`scripts/capture.py`, SHA-256
`71e28a5fb815a45664f06d6902ef1437f469a4d3c99a00e221efe583daa11905`.
This binding includes the reviewed #1289 source transition, which changed only
the archived CLI's program-address selection; the adapted `capture()` body and
the retry adapter's transformation anchors are unchanged.

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
qualification. Filesystem failures after publication begins can still leave
partial output. The archived CLI's missing `repro/programs.json` selector remains
separate work in PR #1289.
