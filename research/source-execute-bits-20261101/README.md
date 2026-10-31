# Exact execute permissions in source receipts

Base: `9120883a957d7d9b2cab6140f66fb5bc9e6774d5`.

An owner-executable source helper (0755) and an otherwise identical helper with
only the other execute bit (0645) produce the same v2 source receipt. On POSIX,
the file owner cannot execute the second helper. The real SBF build succeeds
for 0755 but fails with PermissionDenied for 0645; `assert_unchanged` nevertheless
accepts that permission change on the base revision.

The v3 receipt retains the existing boolean and adds `execute_bits` (mode & 0111)
to each file row and its digest. The same workflow now produces distinct receipts
and detects the change. It does not alter source modes or compiler behavior.
Historical v1/v2 packages keep their original hashes and schemas. Permissions
outside the execute bits, ownership and ACLs remain outside this receipt.

## Reproduce

Use a non-root POSIX file owner, Python 3.12+, rsync and the official macOS arm64
platform-tools v1.44 SDK (rustc 1.79.0-dev). This fixture is dependency-free and
compiles offline. It does not install or download tools.

```sh
python3 research/source-execute-bits-20261101/probe.py /path/to/checkout /path/to/platform-tools
python3 reconstruction/harness/test_source_input_execute_bits.py
```

The first command runs actual production fastbuild with SDK Cargo/rustc/linker/
objcopy. The second exercises the same permission distinction with real host
Cargo (non-root POSIX host with Cargo/rustc required).

| Helper mode | Actual SBF outcome before and after | V2 receipt | V3 receipt |
| --- | --- | --- | --- |
| 0755 | success | same as 0645 | distinct |
| 0645 | PermissionDenied | change from 0755 missed | change detected |
| 0644 | PermissionDenied | distinct | distinct |

`before.json` and `after.json` retain the same-method results; only temporary
root prefixes in compiler logs are normalized. Every run leaves its source
unchanged. The successful candidate SHA-256 stays
`dcbf63f7b5b5ae4a4c6efde978fd4ac803105e31527776ef94d89815e8a68087`.
This is an input-identity correction, not a whole-program rebuild, score gain,
security claim, or complete build-environment identity. Source timestamps stay
excluded and a timestamp-only control preserves the receipt.
