# Frozen native Pump checkpoint: 1ddb1255 (2026-10-30)

This packet admits the actual unchanged-source native build of **frozen
`1ddb12553ccdb4ed45407ffe53f12f4644be172a`**, with **1,034/1,035 normalized
and raw windows**. Only `admin_cto::execute` at `0x22a10` (27,400 bytes) remains
unmatched. It does not qualify later main or replace a selected checkpoint.
No Rust change, new matched window or new reconstruction mechanism is claimed.
Prior packets and failed measurements remain unchanged.

The useful addition is a portable, strict source/build admission procedure plus
a complete literal-byte closure for this actual emission. Source admission,
normalized/raw window identity, literal ELF comparisons and runtime equivalence
are different claims.

| Frozen input/output | SHA-256 |
| --- | --- |
| Authentic external artifact ZIP (2,515,348 bytes) | `4a1e1d7ebd4ffa8911bbf8a9904593d917fc7e798f7911039598c914a8dbc69a` |
| Unstripped ELF (2,665,760 bytes) | `481ba72865f36b52b3cc27e824ef3762a0baff5509c48135aa627fb927418c2b` |
| Stripped ELF (1,934,832 bytes) | `b1cc01495e331a220d1c150c9be21810f172118e45bc45201fe223a8bf783703` |
| Maintained 135-file source aggregate | `6e061e8785371cbe427c8ff591bc1a35846deafad89b8d922137a6c52c5579b9` |

## Portable replay

Python 3.12 and a local Git supporting `--no-lazy-fetch` are required. The
repository argument supplies immutable Git objects and the original capture;
its working tree and HEAD need not be the frozen revision. No private worktree,
uncommitted fixture, installed SDK, Cargo, compiler, network call or original-code
execution is used. This is an offline replay **with local Git**, not a no-Git
verifier. Emitted ELFs and the authentic ZIP stay outside Git.

```sh
python3 -I -B reconstruction/pump-main/checkpoints/native-1ddb1255-20261030/verify.py \
  --repo /path/to/public-repository \
  --artifact /path/to/artifact-12982692412.zip \
  --report /tmp/frozen-1ddb-report.json
python3 -I -B reconstruction/pump-main/checkpoints/native-1ddb1255-20261030/test_verify.py \
  --repo /path/to/public-repository \
  --artifact /path/to/artifact-12982692412.zip
```

The report must be a new file. The verifier extracts authenticated ZIP members
only into a disposable directory outside the repository. It never replaces
source, capture, SDK, registry, artifact or earlier report files. It checks:

- The fixed ZIP digest, every member hash and the complete member set.
- Frozen M and the operational direct-child commit, with only the reviewed three
  workflow/controller/documentation paths changed; all 135 source and 215 CORE
  Git leaves, bytes and modes; the exact maintained selection and 136-file stage;
  both raw source/workspace archives and actual compiler source aggregate.
- Actual cold-target, fresh local crate compilation/fingerprints and flags;
  native macOS 26 ARM64, pinned v1.44/v1.52 archives, recorded complete SDK and
  Linux target-library checks, native hybrid LLD, script/default/hook inputs,
  actual link receipt/map, and before/after registry/tool/source guards.
- Byte-identical frozen M's **six-file** official scorer import closure. It
  recomputes all 1,035 rows and requires exact recorded window and summary
  equality, preserving normalized/raw memberships independently.
- The separate literal closure described below. The official scorer rules are
  unchanged; no bytes or relocation records are patched or ignored.

The original capture at `evidence/original/pump/deployed.so` must have SHA-256
`7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`.
All `summary.gains`, `losses`, `raw_gains` and `raw_losses` compare the retained
**historical Git baseline**, not a new source improvement or later main. The
frozen 1ddb emission and this evidence contribution must not be retallied as
source recovery gains.

Missing Git objects fail explicitly. `INPUTS.json` lists every terminal object
needed by the verifier. A one-time **online public input preparation**, separate
from offline verification, can fetch only the two immutable revisions and those
listed objects. For example, after setting `REPO` to your own repository:

```sh
git -C "$REPO" fetch --no-tags --depth=1 --filter=blob:none \
  https://github.com/lalalune/pumpfun-source.git 1ddb12553ccdb4ed45407ffe53f12f4644be172a
git -C "$REPO" fetch --no-tags --depth=1 --filter=blob:none \
  https://github.com/shawkkkkk/pumpfun-source.git 49bf18401f5138b4d0bdb9446d7a3ef1a129509b
```

For a filtered object store, prefetch the exact blob IDs in `INPUTS.json` from
its corresponding public repository before disconnecting: M inputs from
`lalalune/pumpfun-source`, the three operational inputs from
`shawkkkkk/pumpfun-source`. No broad checkout or frontend restoration is needed.
Verification sets `GIT_NO_LAZY_FETCH=1` and `--no-lazy-fetch`; it never silently
uses a newer file or retrieves a missing input. The captured original must also
be physically available at the explicit repository path above.

## Recorded dependencies and physical checks

The 215 CORE Git payloads are independently read and hashed from the supplied
object store, including tracked Linux target libraries. This is distinct from
rehashing an installed native macOS SDK or Cargo registry. Default replay
reports those physical checks **NOT RUN**, while still checking the authentic
recorded full SDK/archive/tool/LLD and registry before/after bindings.

Optional explicit roots add physical checks; supplied missing or changed inputs
fail without consulting private donors or choosing a fallback:

```sh
python3 -I -B /path/to/packet/verify.py --repo "$REPO" --artifact /path/to/artifact.zip \
  --registry-root /path/to/cargo/registry/src \
  --sdk-root /path/to/native-v1.44/platform-tools \
  --report /tmp/frozen-1ddb-physical-inputs.json
```

The native SDK check covers the full file/symlink set, modes, sizes, hashes and
symlink targets. The registry check hashes every recorded source file. No
installation or SDK/compiler execution is performed. `runtime_valid` is the
builder's static stack-diagnostic gate, not a VM or security qualification.

## Literal byte closure and limits

[LITERAL-CLOSURE.md](LITERAL-CLOSURE.md) and `literal_closure.py` bind the complete
meaningful stripped file against the captured original, without normalization.
All **1,034 non-CTO bodies / 1,764,808 text bytes** match at the same original
physical offsets. `.rodata`, `.data.rel.ro`, `.dynsym` and `.dynstr` payloads also
match literally. All 6,060 relocation records outside CTO match in sequence.
The changed relocation records target CTO; the two extra type-8 entries account
for the 32-byte meaningful-size increase and the checked ELF bookkeeping shifts.
The executable still differs inside CTO and is **not whole-ELF equal**.
The original's 8,550,915-byte zero allocation tail is accounted separately.

This is a new authenticated replay and closure for this frozen emission, not a
new explanation of the two-relocation/vtable mechanism already covered by
#2253/#2370/#2380/#2416. Existing source authors retain their attribution. The
metadata/source admission and archive shape build on accepted #2232's frozen6a
checkpoint and the unchanged independent method; #2232's different source,
binaries and failures remain historical. The literal attachment is separately
authored and qualified; see its method notes. No new runtime cases, general
behavioral equivalence, financial correctness or security clearance is claimed.

## Historical pass13 and rebuild availability

The pass13 checkpoint recorded 133 inputs with aggregate `4b5048e5…`. The frozen
1ddb tree adds two recovered host-test files; the unchanged maintained selection
includes all 135. The actual new native control independently repeats **both
complete ELF hashes** from pass13. That is measured corroboration, not a forced
expected-output gate or a claim that the two source inventories are identical.

The actual run is [41065537974](https://github.com/shawkkkkk/pumpfun-source/actions/runs/41065537974),
artifact **12982692412**. Its immutable operational checkout is
[`49bf18401f5138b4d0bdb9446d7a3ef1a129509b`](https://github.com/shawkkkkk/pumpfun-source/commit/49bf18401f5138b4d0bdb9446d7a3ef1a129509b),
a direct child of frozen 1ddb. The registered workflow path is
`.github/workflows/qualify-pump-macos-v144.yml`; the controller is
`reconstruction/pump-main/lanes/current-native-control/pump_current_control.py`.
The word `current` in these immutable path names does not qualify later main.
The controller preserves `PYTHONDONTWRITEBYTECODE=1` in child environments and
keeps exact input-set checks with added/missing diagnostics.

Hosted artifact retention is **30 days** and may expire. This packet does not
promise permanent hosted ZIP availability: retain the authentic ZIP externally
and verify its fixed digest. The immutable operational checkout documents a
fresh rebuild procedure with the same pinned recipe; a fresh run has new
run/archive receipts and cannot be relabeled as this measurement or substituted
for this verifier's fixed ZIP. No extra rebuild was performed for the packet.
Earlier failed paired run 41026749133 remains incomplete and separate; its
candidate was never built. Its original receipts, failed methods and the earlier
private admission remain preserved, without being retargeted here.

## Packet qualification

[QUALIFICATION.json](QUALIFICATION.json) binds the measured source/method files
and retained success logs. The exported-path portable workflow and three early
rejection/preservation controls pass **4/4 unique cases**. The initial batch
passed the three early controls and failed before scoring because its supplied
sparse repository lacked the required physical original capture. Changing only
that explicit input argument allowed the unchanged four-case method to pass.
The original setup failure remains preserved; repeated controls are not new
cases. No additional compiler or SDK run occurred.

The compact report gives the exact frozen domain/counts and singleton unequal
CTO range. Every complete row is independently checked against the authenticated
external ZIP's `score.json`, which retains the full 1,035-row census. The fixed
domain plus 1,034 raw/normalized matches and singleton false CTO determines all
memberships; another duplicate score map is not stored in Git.

At publication base `54b9208d848ada3fec330fd52bbe8f5815e737c4`, unchanged
`python3 scripts/verify_evidence.py` passes **9 captures**, and unchanged
`python3 scripts/test_tooling.py` passes **209 tests / zero skips**. These gates
bind 136 exact Git inputs that remain unchanged; the new checkpoint alters none
of them. Earlier minimal-export missing-input attempts are disclosed separately
in the qualification record, preserved without source fixes or test shims.
This is a common-gate result for that publication base, not a build of it.

Git hashes establish pinned content association, not a signed build attestation.
Hosted-run receipt provenance and optional physical dependency rehashing retain
the separate limits described above.
