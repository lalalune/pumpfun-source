# Mayhem native Linux exact-build qualification

This recipe reproduces the selected Mayhem ELF on native x86_64 Linux using
ordinary compiler and linker outputs. It does not copy code from the capture,
patch an ELF after linking, or use the captured program as a compiler input.

## Qualified result

The qualification compiles one diagnostic candidate and then two independent
exact candidates from fresh target directories. On Ubuntu 24.04 x86_64 with
the authenticated Anza platform-tools v1.54 archive, both exact builds produced:

| output | bytes | SHA-256 |
| --- | ---: | --- |
| symbol-bearing ELF | 907,776 | `7b15bb1e5c7c9c53041322fa64d4a420906fffd96ff97a55d70d627bcb854960` |
| stripped meaningful ELF | 775,416 | `9af9e3b1cbc9d89340af4d9d46e4c88d3dc2fc67e0090f9370047d97532ff09d` |

The stripped file equals every meaningful byte of the authenticated capture.
The deployed payload is 777,408 bytes because its account allocation contains
a separate 1,992-byte all-zero suffix. The ProgramData account is 777,453 bytes:
a 45-byte loader header followed by that payload. Neither suffix nor loader
header is emitted by the linker.

The retained 67-source input set and the staged 98-file recipe remain the
maintained `programs/mayhem/build_exact.py` inputs. This Linux entrypoint adds no
Rust source revision and preserves the existing exact Windows build.

The checked-in [`QUALIFICATION.json`](QUALIFICATION.json) summarizes the clean
2026-10-30 qualification. That run extracted the SDK from its authenticated
archive, compiled with networking disabled, deleted every target cache after
retaining its evidence, and completed in 1,423.479 seconds. The two exact builds
took 317.746 and 296.848 seconds. The receipt records the host kernel, container
image digest, tool and input hashes, diagnostic output, resource measurements,
and repeat-build result.

## Root cause and correction

Cargo's target `-C metadata` identities differ between the selected Windows
build and a native Linux invocation, even with the same package and source
bytes. The existing exact wrapper therefore could not recognize Linux's old
metadata values. In passthrough mode, all source compiled and linked, but two
otherwise coalescible allocator monomorphizations remained:

| extra section in the Linux probe | bytes |
| --- | ---: |
| `alloc::raw_vec::finish_grow` | 312 |
| `alloc::raw_vec::RawVec::grow_one` | 408 |

That diagnostic ELF was 776,136 bytes, exactly 720 bytes larger than the
selected image. The difference is introduced in Cargo/rustc crate identity
before LLVM code generation and is observed as failed section coalescing at
the final link.

`published-metadata-bindings.json` binds each of the 85 target compilations by
crate name and source-package identity to the already selected published
metadata value. A real passthrough compiler build discovers the current Linux
old value; the driver refuses missing, duplicate, or unexpected bindings and
derives a Linux-specific map. With that authenticated admission, the resulting
function bodies, ordering, call displacements, relocations, data, symbols,
headers, and padding are necessarily identical because both complete ELFs have
the selected hashes.

## Reproduction

Run on native x86_64 Linux from a clean checkout. The input preparation step
needs network access. The compiler step can and should run without network:

```sh
python3 -I -B reconstruction/mayhem/native-linux-qualification/test_native_linux.py
python3 -I -B reconstruction/mayhem/native-linux-qualification/prepare_inputs.py \
  --repo "$PWD" --output /var/tmp/mayhem-linux-inputs
python3 -I -B reconstruction/mayhem/native-linux-qualification/build_linux.py \
  --repo "$PWD" \
  --sdk-archive /var/tmp/mayhem-linux-inputs/platform-tools-linux-x86_64-v1.54.tar.bz2 \
  --vendor /var/tmp/mayhem-linux-inputs/vendor \
  --output /var/tmp/mayhem-linux-qualification
```

`prepare_inputs.py` authenticates the official SDK archive and reconstructs the
complete 215-package vendor tree from package archives, checking every package
and source-file hash. `build_linux.py` also checks individual rustc, Cargo,
rustdoc, LLVM, objcopy, and linker identities; all staged sources and linker
scripts; the historical proc-macro source closure; canonical-source stability;
and vendor and SDK stability after compilation. It refuses an existing output
directory and does not execute the SBF target.

The final result is `result.json`. Compiler stdout/stderr, launch environments,
all 176 wrapper records per target build, linker invocations/maps, unstripped
and stripped ELFs, source inventories, and input receipts remain below the
chosen output directory. The workflow uploads those items without target
caches for independent inspection.

## Scope

This establishes complete meaningful-ELF identity for the maintained source on
native x86_64 Linux and repeat-build determinism for the tested environment. It
does not claim that arbitrary Linux architectures or SDK releases reproduce
the bytes, does not include the account-allocation suffix in the ELF, and does
not establish a general process sandbox. No live transaction or target-program
execution is part of this compiler qualification.
