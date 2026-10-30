# Donation Relay: measured native Linux reproduction

The historical public Relay recipe consumes support that is absent from current
`main`, including its canonical ordered linker script. This packet restores the
consumed configuration and binds a new native reproduction to the unchanged 60
program inputs. It changes no program source, selected binary, match count or
historical receipt.

The source map matches both public reference
`d75184ea323be8a83ebe11fe5f26a13f3dcbe052` and the 60 current inputs at
`2162b3b0041077af8593b0701c8471a157b30e08`. The historical source devices and
source coordinates are retained; this is no claim of possession of the original
private source.

| Actual corrected cold output | Bytes | SHA-256 |
| --- | ---: | --- |
| Symbols ELF | 929,536 | `07ab4ac487727385a3b5ec0d4bc1139e10f701c3fac2f95b88d89701a38ab9e1` |
| Ordinary `llvm-objcopy --strip-all` output | 818,280 | `56d81ec64a0ba070d3d23f3c1547b31d659e85716dfa2198ec4b0ce6cd355333` |

Every byte of the 818,280-byte meaningful captured ELF equals the actual stripped
compiler file. The retained capture is 830,448 bytes and has a separate 12,168-byte
zero allocation suffix. The full capture file and compiler file are unequal.
No padding, byte patch, original machine-code copy or comparison mask was used.

## What was measured

The native host was Debian 13, glibc 2.41, x86_64. The authenticated Linux v1.48
archive supplies the same compiler/tool/target-library bytes as the historical
measurement. Rustc prints `1.84.1-dev`, LLVM `19.1.7`, and commit/date `unknown`;
the archive's `version.md` declaration is preserved separately. Cargo prints
`1.84.0`, commit `12fe57a9d229b236a595ca14f8946da5833e1fd2`.

The original local container ID `c9bcc62…` has no established pullable image
binding. The retained official image digest resolves to a different config.
This native result does not establish container equivalence or portability to an
arbitrary Linux installation. `host-inputs.json.gz` records the exact admitted
host executables/libraries, CRT/static-linker inputs and headers. The replay
preflight refuses a different host profile.

The first actual attempt stopped with Cargo 101 while linking host build
scripts: the selected SDK subset lacked its self-contained linker wrapper.
The correction added only the archive's
`rust/lib/rustlib/x86_64-unknown-linux-gnu/bin/gcc-ld/ld.lld`
(408,048 bytes, SHA-256 `2aea8cee216207f00db286bde7131decdf6016da14e8b30ea1bcdaacd71dc136`)
and its original directory metadata. No compiler option or source variant changed.
The second attempt used a new empty target/output, compiled both local crates
once, finished in 73.93 seconds, and then ran the ordinary strip command.
Inputs were checked before and after both phases. Both process groups exited;
neither disk/timeout guard fired. Lowest free space was 137,748,480 bytes during
build and 135,979,008 during strip, above the 128 MiB floor. These observations
are not a general scratch-space requirement; the earlier 1 GiB budget was only
a provisional estimate.

The measured namespace exposes only source/config/SDK/registry and declared
native system files read-only, with fresh writable target/output and temporary
Cargo/home directories. It uses `env -i`, the canonical environment and exact
Cargo arguments, `--locked --offline`, and a disabled network namespace. Original
or expected ELFs are not build inputs. The linker wrapper and `ordered.ld` are
verbatim historical public assets, SHA-256 `3326309e…` and `4361db23…`.
The ordered script retains the historical target-derived section order; the new
attempt did not derive another order from the capture or modify compiler output.

## Verify the retained result offline

Use a checkout containing `programs/donation-relay`, `scripts/analyze.py` and
`evidence/dependencies/donation_relay/deployed.so`. No private work directory,
Git ancestry guard, SDK, package install or network is required:

```bash
cd /path/to/pumpfun-source
packet=reconstruction/donation-relay/native-linux-v148-20261030
python3 -B "$packet/verify.py" --repo "$PWD"
python3 -B "$packet/test_replay.py" --repo "$PWD"
```

The verifier checks the original 18-member seal, actual result, source map,
unchanged input records, canonical seven-root command correspondence, preserved
first failure/correction, both raw ELF hashes and literal captured ELF bytes.
It uses the checkout's official `scripts/analyze.py` to parse the extent.
It does not execute an ELF or establish transaction behavior or security clearance.

`measurements/attempt1.tar.gz`, `attempt2.tar.gz` and `preparation.tar.gz` are
compression containers for the unmodified raw logs/receipts/methods and compiler
outputs. Historical absolute paths inside those raw records are provenance,
not defaults or executable replay instructions. The original first seal is
unchanged; root's independent byte comparison is a separate additive record.
Preparation failures, including empty-directory creation, tar-mode/name handling,
an initial Python syntax check and the overstrict runtime Rust commit assertion,
remain explicit. None is relabeled as a source-program failure.

## Prepare explicit inputs and a new replay path

Obtain the exact archive named in `sdk-inputs.json` and the 253 public `.crate`
archives listed with lock checksums in `registry-inputs.json`. The helpers make
no downloads and inspect no credentials, home-directory Cargo configuration or
implicit cache. The SDK/crate payloads are not shipped here. The retained public
index snapshot contains only the 235 consumed sparse entries and public config;
it is not claimed to be the historical index bytes.

```bash
cache="/absolute/owned/relay inputs"
python3 -B "$packet/prepare_sdk.py" \
  --archive "$cache/platform-tools-linux-x86_64.tar.bz2" --out "$cache/new-sdk"
python3 -B "$packet/prepare_registry.py" \
  --archives "$cache/locked-crate-archives" --out "$cache/new-registry"
python3 -B "$packet/stage.py" --repo "$PWD" \
  --sdk "$cache/new-sdk" --registry "$cache/new-registry" --work "$cache/run 1"
python3 -B "$packet/launch.py" --work "$cache/run 1"
```

The last command validates and prints a plan; it does not build. Staging requires
a new work directory outside the source/SDK/registry/package inputs, preserves
existing paths, and validates the complete measured input profile. Incoming
checkout permissions may reflect umask; owned staged source copies receive the
exact measured Git modes without changing file contents. Build target and output
directories are created only on explicit execution and must be absent beforehand.
Failed/previous targets are never reused or removed automatically.

If deliberately performing a new measured build on the admitted host profile:

```bash
python3 -B "$packet/launch.py" --work "$cache/run 1" --execute
python3 -B "$packet/verify.py" --repo "$PWD" \
  --candidate "$cache/run 1/output/candidate.so" --symbols "$cache/run 1/output/symbols.so"
```

Execution has the 128 MiB floor on the actual work filesystem, 30-minute timeout,
owned-process-group termination and no automatic retry. A false output-hash check
returns nonzero. Partial outputs/logs remain. The final command is a byte check
of supplied artifacts; it alone does not prove their source/build provenance.

## Qualification boundaries

| Surface | Qualification |
| --- | --- |
| Retained corrected private controller | Actual cold build and ordinary strip; both exact raw hashes; literal meaningful-ELF comparison; independent root and peer read-only audit. |
| Public stager/plan | Complete existing authenticated roots staged into an owned path with spaces; canonical command correspondence and a metadata-only namespace probe; zero SDK executions. |
| Public guarded launcher | Source review plus real host-process floor/timeout checks; no third cold build of this new entrypoint. |
| New SDK extraction / registry assembly helpers | Static correspondence to retained preparation algorithms and refusal/tamper controls; not rerun to completion on another full SDK/registry. |
| Program behavior | No new transactions, differential corpus, handler count or security claim. |

This restores a measured reproduction route for an already matching target.
It does not claim a new byte/window gain, full-allocation identity, a historical
container identity, or a tested turnkey build on other Linux profiles.
