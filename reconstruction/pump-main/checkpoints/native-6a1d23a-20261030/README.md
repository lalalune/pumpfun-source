# Frozen native Pump checkpoint: 6a1d23a (2026-10-30)

This packet makes the actual native build, complete source archives and full
1,035-window census available together. It verifies **frozen source
`6a1d23a306ce0b2213aac937d7a81472efe5986b`: 1,027 normalized / 276 raw;
8 unmatched**. It is **not a build or score of later main**, including the later
#2183, #2152 and #2154 changes. No Rust source changes or new recovery gains are
attributed to this packet's author. Prior baselines and research packets remain
unchanged.

The original machine code is only a comparison input. No compiler runs during
verification, no scorer rule is changed, and neither complete rebuilt ELF equals
the captured original.

| Retained output | SHA-256 |
| --- | --- |
| Authentic hosted artifact ZIP | `d3bfd56530ba9aa5fe0a0a3681bc1db20d34269ff4fcf08a472847a41cc6afbf` |
| `unstripped.so` (2,666,080 bytes) | `d9484de78533d6c55f76cacbee89b2ae15b0ed9d070f0d9f6df99507e53082a5` |
| `candidate.so` (1,935,152 bytes) | `0c141fa73e4981152201b87e6a50a8172ca6e52e48e6e65a103743e7f96cf578` |
| Builder's complete 99-file source aggregate | `889f4c6595381c3cb5de70398d09d073cf4365359f212f5c4ac05e0e6b107a43` |

The eight unmatched original starts are `0x1e7c0`, `0x22a10`, `0x5b3b0`,
`0x72810`, `0x80df8`, `0x13b9b8`, `0x13f630`, and `0x1489f8`.
Normalized matches mask only the maintained scorer's internal-call immediates and
actual ELF-section pointers. They do not prove call-target, runtime, transitive
pointee or whole-program identity.

## Offline replay

Python 3.10 or later and the captured original are sufficient; no Git, LLVM,
Cargo, SDK installation, network or private worktree is required:

```sh
python3 -I -B reconstruction/pump-main/checkpoints/native-6a1d23a-20261030/verify.py \
  --original evidence/original/pump/deployed.so \
  --report /tmp/pump-frozen-6a-report.json
python3 -I -B reconstruction/pump-main/checkpoints/native-6a1d23a-20261030/test_verify.py
```

Run from the repository root, or use absolute paths from any directory. The
`--report` file must not already exist. The original must have SHA-256
`7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`;
it is already a public repository capture and is not duplicated here.
The packet can be copied to a directory without `.git` for the same replay.

The verifier checks the unchanged ZIP and all 24 members; raw Git commit/tree
objects for both pinned revisions; all 99 standalone source leaves, bytes and
modes; the exact 100-file compiled workspace projection; the builder's distinct
99-file snapshot/aggregate; controller/workflow pins; recorded tool/source/host,
cold-build, bootstrap and command-chain receipts; and both ELF hashes. It loads
byte-identical frozen `score.py`, `elf_symbols.py` and `llvm_tools.py` in an
isolated temporary projection, with the original and frozen TSV. It recomputes
all 1,035 rows and requires exact equality with the retained census and summary.
The detailed report includes normalized/raw membership retention for every
window and positional byte/8-byte-slot residual summaries for hop, Sweep,
cashback-inner and claim-v2. Positional residuals are diagnostics, not an
operation-correspondence oracle.

The comparison baseline is explicitly historical: the frozen Git
`baseline/score.json` and `baseline/rescore.json` agree at **1,019 normalized /
188 raw**, symbols SHA `0f50faa8c325104dc77898ed84866dec2ad1eec475b6abba72c475cf7bf9bab6`.
Against that reference the frozen6a build retains every match, adding eight
normalized and 88 raw bodies. These are previously upstream source recoveries,
not gains produced by this contribution and not a claim about intervening main
revisions. Both the historical baseline and current frozen census remain in the
packet rather than silently replacing one with the other.

## Physical SDK, registry and target-library qualification

Artifact integrity and recorded build evidence are distinct from independently
rehashing a user's installed dependencies. Default replay explicitly reports
physical SDK, registry and unbundled toolchain checks **NOT RUN**. The packet
contains the complete 2,785-entry native SDK inventory and the authentic
8,390-entry registry hash map, but does not duplicate the SDK, registry, Linux
rlibs or large programdata capture. All 118 recorded toolchain Git leaf IDs are
verified; bundled text/census files and the explicitly supplied original also
have their bytes verified. The remaining 26 binary paths are reported by name.

Optional explicit roots enable additional checks:

```sh
python3 -I -B /path/to/packet/verify.py --original /path/to/deployed.so \
  --sdk-root /path/to/native-v1.44/platform-tools \
  --registry-source /path/to/cargo-home/registry/src \
  --toolchain-inputs /path/to/frozen-6a-repository-projection \
  --require-local-inputs --report /tmp/pump-frozen-6a-full-inputs.json
```

The last projection needs only the reported unbundled paths, including the
Linux target libraries and programdata capture, with their exact frozen bytes.
A supplied missing/changed input fails; no private donor or SDK fallback is
consulted. `--require-local-inputs` rejects incomplete qualification. SDK checks
include the full file/symlink set, sizes, modes, hashes and symlink targets.
Registry checks hash all recorded source files. They do not install dependencies
or authenticate additional unrecorded files.

## Build and provenance boundary

The unmodified archive comes from [fork Actions run 41003848803](https://github.com/shawkkkkk/pumpfun-source/actions/runs/41003848803),
artifact **12954757170**, controller commit
[`2e208af56710ddfa404cd9dffacc2069580d27fb`](https://github.com/shawkkkkk/pumpfun-source/commit/2e208af56710ddfa404cd9dffacc2069580d27fb).
Its controller is at
`reconstruction/pump-main/lanes/current-native-control/pump_current_control.py`
(SHA `e7ed2474df380c81d55b822515055c953f0947117d28ef5bb783355d4f415c2e`),
and workflow SHA is
`89ae5bcecc3da9a48fc4fd3c7bf0e69cf3e6edd559ab655ea19f90f31dffbb8b`.
Both source files and the frozen fastbuild/bootstrap source are retained in the
compact input archive and authenticated to their actual Git trees.

The recorded host is macOS 26.6.2 arm64, Python 3.12.10. The identity recipe uses
native macOS platform-tools **v1.44** rustc/Cargo/objcopy with authenticated
**Linux v1.44 SBPF target libraries**, target `sbpf-solana-solana`, release,
locked/offline, `-Zremap-cwd-prefix=`, and the frozen physical-source wrapper.
The recorded hybrid rustc equals the native compiler. v1.52 objdump is an
analysis tool, not the compiler or target library recipe. The cold target and
unchanged before/after source/registry/SDK checks are retained. `runtime_valid`
in `build.json` is the builder's static stack-validity gate; it is not a VM replay.
No new runtime or transaction validation is claimed here.

The v1.44 download receipt records an archive digest but a null expected archive
digest; full SDK inventory checks bind installed bytes. Do not reinterpret this
as a preconfigured archive-digest gate. Hosted artifacts have a **30-day
retention setting** and may expire. The checked-in authentic ZIP remains usable
offline. A future controller run would have new run/artifact receipts and must
be separately authenticated, not relabeled as this frozen measurement. Raw Git
object hashes prove content association, not a Git signature or independent
Actions-service attestation.

`CHECKPOINT.json` retains the digest of the earlier private independent seal
`32e6db3297aeddbd10cb1f2f0be7da07ef1b16af5762a58ea3c82d9ac7414319`.
The original private reports are preserved in place; they contain local paths
and are not copied or represented as portable public receipts. This packet's
fresh portable replay stands separately. Earlier strict admission first failed
on missing local Git objects, before scoring; hydration of the exact expected
objects allowed the unchanged checker to pass. A failed CLI artifact download
was not used; the authenticated connector download is the retained ZIP. No
network failure stdout, credentials, temporary signed URLs or conversations are
included.

The initial portability tests exposed an isolated-Python import-path error in
the new checker entrypoint (seven controls passed, one failed). The entrypoint
now selects its own sibling module explicitly; all eight controls pass. This
was a verifier integration correction, not a program or native-build change.
The original failed test receipt remains private and unchanged.

The authentic ZIP is also the raw-output distribution. After successful
verification it can be extracted into a **new** empty directory using a standard
ZIP reader; `program-source.tar.gz` and `compiled-workspace.tar.gz` contain the
complete 99-file standalone and 100-file staged projections. The verifier itself
extracts only into disposable temporary directories and never replaces source,
SDK, registry, captures or previous output. `PORTABLE-REPLAY.json` records a
successful clean export with no `.git` and an empty `PATH`.
`LOCAL-REGISTRY-CHECK.json` separately records an explicit 8,390-file local
registry rehash; it does not change the default replay's missing-input statuses.

## Required repository gates

At publication base `a7135a6a64c446166895f7e3ea4ca84ac1a9b848`, unchanged
`python3 scripts/verify_evidence.py` verifies **9 captures** and unchanged
`python3 scripts/test_tooling.py` passes **169 tests**. The isolated gate
projection binds 428 source/evidence inputs by Git blob and SHA-256; all remain
unchanged after execution. Its first tooling attempt passed 167 tests and hit
two missing-scorer-file errors in the projection. The five actual scorer/import/
baseline inputs were restored from that exact Git revision, and all 169 passed.
The initial failed raw log is preserved privately, hash-bound in
`COMMON-GATES.json`; it is not presented as a program defect. This PR adds only
this checkpoint directory and changes none of those gate inputs.
