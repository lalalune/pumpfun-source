# Preserve inventory output ownership during publication

This is a static tooling correction tested against
`599891304e83e853ec723dc1417550bef4e1c074`. The inventory CLI disassembles the
nine retained ELF captures; it does not execute, assemble or modify them.

The fresh-directory contract established by [#2303](https://github.com/lalalune/pumpfun-source/pull/2303)
has two gaps. Resolving `--output` before testing `is_symlink()` hides a dangling
leaf link. Plain `Path.rename()` can also replace an empty directory created by
another process after the initial admission check. Both situations publish a
complete inventory into a destination the caller no longer owns exclusively.

The correction keeps the lexical absolute leaf for admission and calls the
existing `deep_disassembly.rename_directory` no-replace helper for publication.
That helper was introduced in
[`240ad77c6`](https://github.com/lalalune/pumpfun-source/commit/240ad77c6cc0b5777f8dd9274ed0e98b4f7deb92).
It is reused unchanged; parent directory aliases and the short staging prefix
from [#3622](https://github.com/lalalune/pumpfun-source/pull/3622) remain supported.

`before.json` and `after.json` record ten actual CLI invocations per revision.
`reproduce.py` copies exact script bytes and genuine retained captures into a
private cohort. It uses an unmodified, independently built Blueshift executable.
For the late-directory case, the supervising process waits for the real staging
directory to appear, then creates the destination while actual disassembly is
still running. No tool, production function or publication operation is mocked.

| Case | Base | Corrected |
| --- | --- | --- |
| Fresh output | Success | Success |
| Parent directory symlink | Success | Success |
| Dangling output symlink | Follows link and publishes target | Refuses; target remains absent |
| Output symlink to populated directory | Refuses; preserves bytes | Same |
| Existing empty/full directory or regular file | Refuses; preserves inode/bytes | Same |
| Empty directory created after admission | Replaces directory inode | Refuses; preserves directory |
| Real captured input used directly/as link target for output | Refuses; preserves capture | Same |

Each completed packet covers **788,302 logical instructions** from nine captures.
The two normal output cases retain identical bytes for all **27 payload files**
before and after. The semantic manifest is identical too; only its intended
`generator_sha256` changes. All original captures, private input copies, the
admitted executable and its tracked source remain unchanged. Failed cases leave
no staging directory.

## Reproduce

The host tool is the official [`blueshift-gg/sbpf`](https://github.com/blueshift-gg/sbpf)
at commit `422a6316cbb1ac60b07b60a555bfbcb8e557bcef` (version 0.3.3), built with
`cargo build --locked --release --package sbpf --bin sbpf`. Its lockfile SHA-256
is `998462a5c5cac8433f7039ea7727e0b80ab7e7f43ffd4b4f9c23599bfd5c2a1c`.
Use an already inspected checkout and separate Cargo cache/target directory;
the inventory expects the executable at `<tool-source>/target/release/sbpf`.
`tool-build.json` records the tested host compiler, successful build and binary.
The local build emitted optional debug-stripping warnings for a missing
`libLLVM.dylib`; Cargo returned zero and the resulting executable passed version
and real disassembly checks. No upstream test, assembly, deployment or VM command
was run. Tool hashes can differ when another host builds the same locked source.

From this repository, with Python 3.12 and an unused result path:

```sh
python -B research/sbpf-inventory-publication-20261101/reproduce.py . \
  --tool-source /path/to/pinned/sbpf \
  --revision 599891304e83e853ec723dc1417550bef4e1c074 \
  --expect before --output /tmp/inventory-before.json
python -B research/sbpf-inventory-publication-20261101/reproduce.py . \
  --tool-source /path/to/pinned/sbpf \
  --expect fixed --compare /tmp/inventory-before.json \
  --output /tmp/inventory-after.json
python -B scripts/test_sbpf_disassembly_inventory_publication.py
python -B scripts/test_sbpf_disassembly_inventory_long_output.py
python -B scripts/test_deep_disassembly_publication.py
python -B scripts/verify_evidence.py
```

The existing inventory publication suite is already invoked by CI. Its small
regressions use controlled workers for deterministic boundary coverage; the
separate retained proof above exercises the real executable and all captures.
Twenty-five affected static regression methods and the nine-capture verifier
passed locally. This packet does not claim an additional full tooling run.

Limits: the actual publication proof ran on macOS arm64. The unchanged helper
also implements Linux and Windows no-replace publication; those hosts were not
executed here. Other unsupported hosts fail closed. Parent-directory replacement
races are not addressed, and parent symlinks remain intentional. This establishes
output preservation and unchanged static diagnostic payloads, not source
reconstruction, runtime equivalence or security acceptance. Historical manifests
and capture bytes are preserved; no historical inventory pin was refreshed.

## Section-name adapter follow-up

After the original publication packet was frozen, the documented
`research/sbpf-section-name-admission/inventory.py` command was also found to
reject current sources. This maintained adapter has previously been rebound in
[#2510](https://github.com/lalalune/pumpfun-source/pull/2510),
[#2992](https://github.com/lalalune/pumpfun-source/pull/2992) and
[#3126](https://github.com/lalalune/pumpfun-source/pull/3126).
Its old `08070b3...` generator identity matches the merged #3126 source at
`d07c6f6507bcf4e901bb9aefe4d93a58bd03a692`. The next and only change before this
publication correction was #3622's `output.name[:32]` staging prefix and its
two explanatory comment lines, producing `81c0f7...`. The adapter had not been
updated and already failed at the original tested base.

This follow-up explicitly binds the same adapter to the reviewed current
generator `0d3714567123a34fd504b97609d00bd1a61eb223213d8b2dc39af68a61081bcf`.
The full reviewed transition is that prefix correction plus this packet's
lexical leaf and no-replace publication changes. The new publication import
loads the existing `deep_disassembly.rename_directory` helper through the
same scripts directory the adapter already installs on `sys.path`.
The helper and its `window_elf_reader` dependency remain unchanged. Parsing,
section-name admission, capture selection, raw disassembly, instruction records
and generator attribution do not change. The adapter continues identifying its
own exact bytes as the emitted generator. Its one hard-coded digest is neither
learned at runtime nor broadened into an allowlist.

`adapter-results.json` records six real CLI invocations against exact current main
`1647da0f22312730b2e6b3eec7a468d9d3d89041` (after #3912 merged) and the follow-up:

1. The prior adapter rejects the current generator before output creation.
2. The corrected adapter emits a complete nine-capture packet.
3. An owned historical adapter plus its exact admitted `08070b3...` generator
   emits the same 27 payloads and semantic manifest.
4. The corrected adapter rejects a source containing an unreviewed execution
   canary before that source can execute.
5. The corrected adapter rejects the earlier generator identity.
6. The direct current generator emits the same payloads and semantic manifest
   with the same executable, independently of any stored host-specific build.

On the tested host, the current adapter also matches the direct result retained in
`after.json`. All captures, copied sources and executable bytes remain unchanged.
The original `before.json`, `after.json`, `reproduce.py`, build receipt and this
README's preceding content are preserved exactly.

```sh
python -B research/sbpf-inventory-publication-20261101/adapter_probe.py . \
  --tool-source /path/to/pinned/sbpf --output /tmp/adapter-results.json
python -B research/sbpf-section-name-admission/test_inventory.py
```

The six existing section-map tests pass and are now included in CI; five
inventory publication tests, two long-name tests and nine-capture verification
also pass. This follows the merged static publication PR with maintained-consumer
compatibility. It adds no decoder behavior, source reconstruction or runtime
claim, and it does not rewrite historical stored evidence.
