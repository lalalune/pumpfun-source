# Dependency-path producers: ten further raw data corrections

This is a compiler-input research packet, with no program-source or output-byte
patch. Main `3bbbe91e881df9ff617ecb5392ecb0559a7691c0` is rebuilt from 112 pinned
source files, including 107 Git blobs, using four pinned tools and 207 cached
root dependency inputs. The compiler is the previously recorded Windows
v1.44-associated toolchain, reporting Rust 1.79.0-dev, unknown commit, LLVM 18.1.7.
Its SDK-associated source revision does not authenticate the compiler binary's
historical provenance.

| Compiler inputs | Changed output bytes | Original `.rodata` differences | Normalized / raw |
| --- | ---: | ---: | ---: |
| Fresh main control | 0 | 104 | 1027 / 273 |
| Prior Borsh + Metaplex recipe | 7 | 97 | 1027 / 273 |
| Selected additional dependency mappings | 17 | 87 | 1027 / 273 |

Every changed byte is `0x5c -> 0x2f` within a corresponding original filename.
Every other byte in the 2,666,328-byte compiler output is identical to control,
including code, relocated data, relocation tables and ELF metadata. All 1,035
membership decisions are preserved. This corrects ten more raw data bytes than
the prior producer packet. It adds no exact function match and does not close
the formatter gap.

The original capture remains the 10,485,715-byte artifact with SHA-256
`7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`.
These comparisons use section-relative data positions, not whole-original
file-position identity or allocation-image equality. Nothing is padded or
rewritten after compilation.

- Fresh control: `8d9c35696664888ec05c42de2e81f40d9ef79284839f32b090aae36df570c88c`.
- Prior recipe: `3eb5a1e655ed741aa9ad8fb6ab54940834dbbc5e9f8b5abf3d81ecfb18e4f20e`.
- Selected recipe and independent repeat: `2838d90f7e6d15904f9d3727746fa020c23e6248568ccbaa91badc14befc379b`.

## Producer controls and selection

Each selected crate's logged command reproduces the complete retained library
used by the current root cache before any mapping is added. Source files match
their vendor `.cargo-checksum.json` entries. Package environment, tools, direct
extern inputs and dependency search-directory inputs are recorded and checked
unchanged during each command. `-C metadata` is unchanged.

As in the Borsh packet, compilation occurs outside the vendor directory while
retaining `-Zremap-cwd-prefix=`. An explicit vendor-root-to-empty mapping reproduces
the control; later absolute-file-to-relative-slash mappings select filenames.
The selected mappings are:

| Crate | Files mapped | Changed metadata / object bytes | Additional root corrections |
| --- | --- | ---: | ---: |
| spl-token 7.0.0 | `src/instruction.rs`, `src/state.rs` | 2 / 2 | 2 |
| spl-token-2022 6.0.0 | `src/extension/transfer_fee/instruction.rs` | 3 / 3 | 3 |
| spl-token-metadata-interface 0.6.0 | `src/instruction.rs` | 1 / 1 | 1 |
| anchor-lang 0.31.1 | `src/bpf_writer.rs`, `src/common.rs` | 2 / 2 | 2 |
| solana-borsh 2.2.1 | `src/v1.rs` | 1 / 1 | 1 |
| bincode 1.3.3 | `src/ser/mod.rs` | 2 / 2 | 0 |
| bs58 0.5.1 | `src/encode.rs` | 1 / 1 | 1 |

For every selected library, the complete archive differs only by those slash
bytes. All other members, headers and layout are identical. Seven independent
dependency repeats and a root rebuild reproduce the selected outputs exactly.
The source locations were attributed by filename, line and column in the prior
packet's `path_attribution`, not merely by ambiguous short filenames.

The Bincode correction does not reach the root; one BS58 copy also remains.
These negative propagation results are retained. The selected root differs
from the prior recipe at `.rodata` offsets 18419, 18429, 18442, 18639, 18739,
18861, 19593, 19610, 25291 and 27142.

## Rejected trials are part of the evidence

1. An earlier complete Cargo cache reproduced six libraries that differ from
   those actually used by the current root, despite identical filenames and
   logged arguments after build-path normalization. Their direct dependency
   bytes differ. Substituting that batch fails crate resolution. Both failed
   root attempts are retained; matching artifact names is insufficient.
2. Replaying the current cache fixes that control error. Including Anchor's
   `src/idl.rs` mapping changes 3,729 metadata bytes, beyond its three object
   separators, and the combined root still fails to resolve Anchor. The cause
   of this metadata change is not established; selecting the other two Anchor
   files avoids it. No binary metadata repair is attempted.
3. Mapping all three observed Token-2022 files adds 128 object bytes. A control
   that additionally supplies corrected Token and token-metadata-interface
   externs produces the same expanded library, so that hypothesis does not fix
   it. The corresponding roots retain all function memberships but worsen raw
   `.rodata` differences to 251, or 249 with the two Anchor mappings. Rejected.
4. Mapping only Token-2022's transfer-fee filename gives six slash changes in
   its complete archive and three root corrections without other output changes.

There are ten root invocations (three failed) and 38 dependency invocations in
this increment. All logs, commands, checksums and outcomes are retained.
`ATTEMPTS.jsonl` uses the upstream ledger schema. Before each invocation the
tracked upstream snapshot and local records were checked; the mechanism search
is retained. The shared live POSIX ledger was not accessed from this Windows
host. These are lane-local records, not a claim of shared-ledger synchronization.

## Replay and limits

`SUMMARY.json` exposes the exact identities, archive changes, offsets, rejected
stage metrics and validation results as plain text. `VERIFICATION.json` is the
successful read-only replay. `PRODUCTION.json.gz` contains the recorded recipes,
controller sources, source/checksum bindings, input hashes and ledger review.
`COMPILER-LOGS.json.gz` includes failures; `MEMBERSHIPS.json.gz` includes all
scored membership sets and exact raw differences.

Copy these three scripts with their sibling layout intact:

```text
path-producers/verify_paths.py
mpl-producer/verify_mpl.py
borsh-producer/verify_producer.py
```

Supply the 26 pinned ELF/rlib files separately and create a JSON object mapping
each `PINS` key in `verify_paths.py` to its absolute local path. Then run:

```sh
python3 -I -B path-producers/verify_paths.py --inputs inputs.json --report result.json
python3 -I -B -O path-producers/verify_paths.py --inputs inputs.json --report optimized.json
```

The two reports must be identical. Both modes pass from a minimal export at a
path containing spaces. Three actual counterfactual inputs are rejected: the
broad remap root, the earlier seven-byte result, and a control library from the
wrong cache. The current unmodified scorer and independent census agree for
all 1,035 windows. No target, VM or live-chain execution occurs.

This is a replay against supplied pinned caches, **not a clean-machine build
recipe**. Build outputs remain outside Git. The remaining 87 data differences
are 81 bytes from two strings in opposite order and six separators at 18225,
18627, 19855, 26740, 26744 and 26754. Future work should trace the unpropagated
Bincode/BS58 copies and the Token-2022/Anchor exclusions before broadening maps.

Upstream advanced to `2162b3b0041077af8593b0701c8471a157b30e08` during this work,
changing `create_v2.rs` and `util/payments.rs`. That later source was not rebuilt;
all results remain pinned to `3bbbe91e8`. Native preservation, whole-original
identity, historical source/compiler authentication, runtime equivalence and
security are not established.
