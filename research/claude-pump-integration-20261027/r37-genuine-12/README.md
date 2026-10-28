# Round37 genuine composite 12 — repository-builder validation

Research package composed on the maintained [Round37](../../../repro/pump/main-contract-round37-20261027/README.md) main-Pump source. It is not a maintained checkpoint and does not edit `programs/pump`. **Whole-ELF identity remains false.**

| | normalized | raw | unmatched | matched text bytes |
|---|---:|---:|---:|---:|
| Round37 as published (Codex pipeline, `a05e9965…`) | 744 | 175 | 291 | 924192 |
| Round37 primary, control build with this package's builder | 744 | 121 | 291 | 924192 |
| This package (`3e7adb17…` / `3bff6696…`) | **808** | **147** | 227 | **1071872** |

Normalized gains vs the control build: `0x340`, `0x2bc0`, `0xea68`, `0xf130`, `0x2a8e8`, `0x3b598`, `0x3b738`, `0x47d00`, `0x48710`, `0x49708`, `0x524f0`, `0x54c90`, `0x54f30`, `0x55630`, `0x56658`, `0x8b970`, `0x8c2d8`, `0x8cc58`, `0x8e908`, `0x90e60`, `0x91690`, `0x92820`, `0x93898`, `0x95610`, `0x95f38`, `0x96280`, `0x96d48`, `0x970f8`, `0x97580`, `0xa0838`, `0xa23f0`, `0xc5650`, `0xca628`, `0xcf510`, `0xd5af0`, `0xdd700`, `0x109488`, `0x10a0e0`, `0x10b0b8`, `0x10c0b8`, `0x10d638`, `0x10e938`, `0x10fb38`, `0x1100f8`, `0x110d40`, `0x1113c8`, `0x112220`, `0x1133c8`, `0x113f00`, `0x114d48`, `0x1159d8`, `0x116718`, `0x118360`, `0x119c50`, `0x1255a8`, `0x12a4e0`, `0x12abc8`, `0x12ba48`, `0x137fc0`, `0x163ea8`, `0x17c0f0`, `0x184e38`, `0x18fc98`, `0x1905a8`. Raw gains: `0x17c0f0`, `0x17ddb0`, `0x17df20`, `0x17f948`, `0x186760`, `0x18e878`, `0x194998`, `0x194ae0`, `0x197508`, `0x1991e0`, `0x199b70`, `0x19a758`, `0x19a8a0`, `0x19a9e0`, `0x19aff8`, `0x1a0f68`, `0x1a2330`, `0x1a2340`, `0x1a2fd8`, `0x1a6940`, `0x1a9150`, `0x1a9228`, `0x1a9250`, `0x1ab1f8`, `0x1ab220`, `0x1ab730`. Losses: **none**. Against the published Round37 inventory the package gains 64 normalized windows and loses 0. Raw counts depend on link order: the published round applies derived text/data-order linker scripts, while both builds here use the plain link.

The candidate ELFs are included. `source/programs/pump` is the complete compiled crate and `source.patch` is its exact diff against the base round's archived `primary` source. Both ELFs come from the repository builder (`scripts/pump_build_verified.py --workspace-layout --target-library-profile linux-v1.44-sbf --target-library-directory /Users/shawwalters/.cache/solana/v1.44-linux-probe/platform-tools/rust/lib/rustlib/sbf-solana-solana/lib`, v1.44 SDK, fresh target), and `control/` holds the same builder applied to the unchanged base primary source. The build log has no stack-offset warnings. `inventory.json.gz` uses the same window rule as the round inventories. The 44-suite captured-loader corpus passes for this exact binary: 10,468 cases, 10,464 paired diagnostic logs, zero mismatches (`full.json.gz`).

```sh
python research/claude-pump-integration-20261027/r37-genuine-12/verify.py
```



The sibling `wip-20261028/integ-genuine-r37-12` contains the identical input crate under the separate `sbpf` identity recipe. Its independently rebuilt binary has a separate regression report under `../round37-12-validation/`; the recipe counts are not interchangeable.
