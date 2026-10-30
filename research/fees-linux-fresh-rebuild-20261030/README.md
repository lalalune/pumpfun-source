# Fees: fresh native-Linux rebuild equals the pinned meaningful ELF

Until now, the Fees checkpoint has rested on staged source inputs plus captured
hashes. Its compiler was not rerun (`fresh_build: false` in
`reconstruction/pump-main/checkpoints/completion-20261030/other-programs.json`).
This packet reruns the unchanged builder `programs/pump-fees/build_exact.py` at
`2abb99ccb60766c3cd292e679dbac5314afb3f3b`. It runs from two empty target
directories on native x86_64 Linux.

| output | bytes | SHA-256 | both runs equal the builder pin |
| --- | ---: | --- | --- |
| symbol-bearing ELF | 1,257,952 | `7ec99a6915bcb9245a2d5199996376a76651fa893c71e455b189cf59428f4e66` | yes |
| stripped meaningful ELF | 873,256 | `5b6ceda57863f0dcc3e0e3623052f8342c2c81883379699e71d7ed5383cb3dcf` | yes |

The builder printed `exact_symbols_equal: true` and `exact_candidate_equal: true`
for both runs. Both local crates compiled fresh, once each. There were no stack
diagnostics. The source, macro, SDK-library and registry inputs were unchanged
before and after each run. Each build took 63.5 s and 64.6 s with `CARGO_BUILD_JOBS=2`.

The meaningful ELF is the 873,256-byte prefix of the captured
`evidence/original/pump_fees/deployed.so` (948,944 B, `4f2955d0…b35e`). The
remaining 75,688 bytes of the allocation are all zero.

## Inputs (all already pinned in this repository)

- **Compiler:** the official platform-tools v1.44 Linux x86_64 archive
  (`6719b889…b3e9`, pinned in `reconstruction/harness/make_hybrid144.sh`). Its
  `cargo`, `rustc` and `rust-lld` hashes equal the builder's `TOOLS`.
- **Strip:** `llvm-objcopy` from the official v1.52 archive (`8b3861e9…907e`),
  file `673b3b86…cb69`. Both are pinned in `scripts/core_linux_v144_inputs.json`.
- **Registry:** `cargo fetch --locked` of `programs/pump-fees/Cargo.lock` with
  the v1.44 cargo, 251 packages. This was the only networked step. The builder
  ran with `CARGO_NET_OFFLINE=true`.

## Deviation: no container image

`build_exact.py` invokes `podman run --network none <pinned verifiable-build image>`.
This host has no podman. `podman-bwrap-shim.py` was placed first on `PATH` as
`podman`. It runs the identical argv in a bubblewrap sandbox with the same bind
paths (`/work/src/linux-e9751bde`, `/work/sdk`, `/cargo`, ...), a cleared
environment holding only the builder's variables, and no network
(`--unshare-all`). The host's `/usr` and `/lib` stand in for the image userland.

All code-generating tools come from the SDK mount, not from the image. The
builder and its inputs are unchanged, and the outputs equal the pins. The image
digest was therefore not exercised by this run.

## Negative controls and mutation tests

- **Builder.** Appending one comment line to `programs/pump-fees/src/buyback.rs`
  in an exported copy makes the real builder refuse before compiling, with
  `ValueError: canonical input changed`. This is recorded in `RESULT.json`.
- **Verifier.** It stages the current canonical inputs with the unchanged builder
  in a temporary directory, without invoking a compiler, and binds the source,
  qualified-source, input-mapping and macro inventories to both run receipts.
  `test_verify.py` runs a positive check on the real tree and on a
  copy with a space in its path. It then runs 17 mutations that must each fail
  with a specific message:
  - an edited result without its checksum;
  - a mutated run hash;
  - a non-cold target;
  - only one run;
  - inputs that differ between runs;
  - a mutated pin in the packet;
  - a mutated pin in the builder;
  - a changed builder script;
  - a flipped byte in the capture prefix;
  - a non-zero byte in the capture suffix;
  - a wrong objcopy pin;
  - a tampered shim;
  - a changed checkpoint record;
  - a flipped byte in a supplied candidate.
  - changed current source or mutually consistent run digests that do not match
    the current source or macros.

## Verify (offline, stdlib, under `-O` too)

```bash
python3 -B research/fees-linux-fresh-rebuild-20261030/verify.py
python3 -B -O research/fees-linux-fresh-rebuild-20261030/verify.py
python3 -B research/fees-linux-fresh-rebuild-20261030/test_verify.py
python3 -B -O research/fees-linux-fresh-rebuild-20261030/test_verify.py
(cd research/fees-linux-fresh-rebuild-20261030 && sha256sum -c SHA256SUMS)
```

## Rerun the build (x86_64 Linux, Python ≥ 3.11, bubblewrap or podman with the pinned image)

```bash
W=/var/tmp/fees-rebuild; mkdir -p $W && cd $W
curl -fsSLO https://github.com/anza-xyz/platform-tools/releases/download/v1.44/platform-tools-linux-x86_64.tar.bz2
echo "6719b889d60677a8a2fcf4c82f68441a1afe0ab093edd2efe9f84a67a808b3e9  platform-tools-linux-x86_64.tar.bz2" | sha256sum -c
mkdir sdk144 && tar -xjf platform-tools-linux-x86_64.tar.bz2 -C sdk144
curl -fsSL -o pt152.tar.bz2 https://github.com/anza-xyz/platform-tools/releases/download/v1.52/platform-tools-linux-x86_64.tar.bz2
echo "8b3861e93daf085ec12b65c4fac374d9bec4587a3de16871da6b08ab0c1d907e  pt152.tar.bz2" | sha256sum -c
mkdir pt152 && tar -xjf pt152.tar.bz2 -C pt152 ./llvm/bin/llvm-objcopy
cd "$REPO"   # clean checkout of this branch
CARGO_HOME=$W/cargo-home $W/sdk144/rust/bin/cargo fetch --locked --manifest-path programs/pump-fees/Cargo.toml
# without podman: put the shim first on PATH as `podman`
mkdir -p $W/shim && cp research/fees-linux-fresh-rebuild-20261030/podman-bwrap-shim.py $W/shim/podman && chmod +x $W/shim/podman
for n in 1 2; do PATH=$W/shim:$PATH python3 -B programs/pump-fees/build_exact.py \
  --sdk $W/sdk144 --registry $W/cargo-home/registry \
  --objcopy $W/pt152/llvm/bin/llvm-objcopy --output $W/run$n; done
python3 -B research/fees-linux-fresh-rebuild-20261030/verify.py --candidate $W/run1/candidate.so --symbols $W/run1/symbols.so
```

Expected output: the builder prints `"exact_symbols_equal": true`,
`"exact_candidate_equal": true` and
`"candidate_sha256": "5b6ceda57863f0dcc3e0e3623052f8342c2c81883379699e71d7ed5383cb3dcf"`.
The verifier then prints a line starting with `OK:`.

`RESULT.json` compacts the two full builder receipts (about 890 KB each) with
`summarize.py`. The inventories are kept as canonical-JSON digests, and the
full receipts' SHA-256 values are recorded.

## What this does not claim

- That the pinned `solanafoundation/solana-verifiable-build` image was used.
  It was not; see the deviation section above.
- Any change to the Fees source, the builder, the pins, scores or windows.
  Matched-window counts are unaffected.
- Equality of the whole deployed account. The account has a 75,688-byte zero
  allocation suffix and a loader header, which the linker does not emit.
- That this is the historical original compiler invocation or provenance.
  It is the repository's reconstructed recipe.
- Runtime equivalence, security properties, or anything about Mayhem. Mayhem
  is already rebuilt natively on Linux by
  `reconstruction/mayhem/native-linux-qualification/`.
- Byte-identical results on macOS or other hosts.
