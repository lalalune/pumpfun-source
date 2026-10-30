# Lane w8-sibling-recipes (wave 8, build inputs): port the sibling programs' recipe to Pump Main

Base: origin/main ce53d867a (fresh build: 1027/1035 normalized, 276 raw, unstripped `31ec6381...`).
Scratch: `~/.cache/pumpfun-reconstruction/lanes/w8-sibling-recipes/`.

## What the four identical siblings needed

| program | crate name / version | anchor | build-input choices that close order and layout |
| --- | --- | --- | --- |
| AMM | `pump-amm-recovered` 0.1.0 | 0.31.1 | vendored `solana-pubkey`; ordered link script (`scripts/amm_sell/ordered.ld`, 1,586 lines: `.text`, `.rodata`, `.data.rel.ro` input sections in the original's order) |
| Fees | `pump-fun-fees-candidate` 0.1.0 (2-member workspace) | 0.31.1 | patched `anchor-attribute-program` (`vendor/used-public`), `--remap-path-prefix` for the path crate, Linux container `cargo rustc`, `exact/ordered.ld` (1,504 lines, same three sections) via a `-C linker=` wrapper that swaps `-T` |
| Mayhem | `mayhem-recovered` 0.1.0 | 1.0.0 | vendored `anchor-lang`, `profile-rustflags` remaps, `codegen-units=2` for `solana-stake-interface`, Windows host, `ordered-native.ld` (539 selectors, portable `lib<crate>-*.rlib` globs) |
| Donation Relay | `donation-relay-source-proposal` 0.1.0 | 0.32.1 | no link script in the tree |

None of them uses the original crate name. Their function order does not come from crate
identity (`-C metadata`, StableCrateId) but from an ordered link script. Under a link script the
symbol hashes only name sections, so the root crate's name and version no longer affect any
output byte. That holds for Pump too: renaming the root crate (tried by layout-order-census,
`8f9651c8`) is moot once the order is pinned. The script itself is what the siblings had and
Pump lacked.

## Kept: pinned link order for the root cdylib (`d3ad3242`, `fc1c0930`)

- `programs/pump/link/ordered.ld`: the SBF default script (`harness/sbf_default.ld`, byte-identical
  to the `rustc-sbf-linkfile.ld` that v1.44 rustc writes) with the `.text` rule replaced by
  554 selectors:
  1. **U**: the 142 upstream-generic instances in the root CGU (`Account<T>::try_from`,
     `Error::with_values`, ...) in the original's order. rustc sorts them by mangled name, which ends in
     the `17h<hash>` our crate identity determines. That is the order no source change can reach.
  2. one glob for the rest of the root CGU (local items stay in rustc def order, so every
     source-level order change still works and new or renamed functions land where rustc puts them);
  3. **D**: all 411 dependency `.text` sections (`*lib<crate>-*.rlib:*` globs plus the exact section
     name) in the original's order;
  4. the default catch-all.
- `harness/link_order.py` (+ entry points `pump_link_rustc.py`, `pump_link_lld.py`): fastbuild runs
  the root cdylib's link through a linker hook when the crate carries `link/ordered.ld`. The hook
  appends `-C linker=` only for the root cdylib (untracked rustc option: identical objects and
  dependencies), checks that the target's script is the default one, swaps in the pinned script and
  execs the same rust-lld. `check_script` admits only input-section reordering: the default script
  verbatim except for `.text`/`.rodata`/`.data.rel.ro` blocks made of `<file glob>("<section>")`
  or `<file glob>(.<section>*)` lines that end with the default catch-all. No assignments, fill,
  alignment, `BYTE`/`KEEP`/`ASSERT` or other statements. fastbuild fails if the hook did not run,
  and writes `link-receipt.json` and `link.map` next to the binaries.
- `tools/regen.sh <scratch>` regenerates the script from the current source: one default-order build
  (script = `sbf_default.ld`, hook active for the map), `census.py`/`refine.py` pairing, `genld.py`.
  On this branch it reproduces `ordered.ld` byte for byte. The original ELF is an input to the
  generator (as for the siblings' scripts), never to the build.

| metric | main ce53d86 | this branch |
| --- | ---: | ---: |
| official normalized / raw | 1027 / 276 | 1027 / **293** (raw +17, 0 losses) |
| raw gains | | U: 0xa7e0 0xea68 0xf130; D: 0x18a3b0 0x18a4d8 0x18a888 0x18e048 0x18e9c0 0x18eb28 0x18ec88 0x18fc98 0x199af0 0x199b18 0x1a6370 0x1a6468 0x1a64d8 0x1a6508 |
| 0xa868 (span-size coincidence) | raw | raw (kept) |
| model raw once the 8 unmatched reach their sizes and the 512-B extra is gone | 429 | 477 |
| same, with the L block in the original order too (`genld.py --mode all`) | | 1022 |
| unstripped sha256 | 31ec6381b4e7... | d7dca7cc2ece56e4505e71695239502f54ee996528161110d88b70f58e97e119 |
| candidate (stripped) sha256 | 1b04b8d4cf9b... | 57f3c15a15ddb788e632941e506b6baeee9df0756b054e886e1ed8fdba5cf8e4 |

The offline relink of the captured main link inputs, the lane-work-dir build and a fresh-work-dir
build all give `d7dca7cc`. `compare_scores.py` accepts against the fresh main build.

## Why not more raw now

- All 601 data-pointer windows already point at the original's in-section offsets (`dwe.py`: 601/601,
  `.rodata` 0x7d1f = original). They fail only because `.text` is 0x230 B longer than the original
  (buy_handler +32, buy_exact_quote_in +32, admin_cto -56, swap_hop -40, sweep +48, v3_buy_costs +16,
  v3 buy_exact_quote +16, and the 512-B `v2_native_payments::ensure_rent_exempt` wrapper that #2168 removes).
  So `.rodata`/`.data.rel.ro` ordering has nothing to fix today. The checker already admits it.
- The full original order of all three blocks also gives 293 at today's sizes. Moving the 9 wrong-size
  units to the start of the L block, the start or the end of `.text` gives 293. Putting them at the end of the L block gives 209.
  The remaining call-only windows cross a size delta.
- Original L order through the script (`--mode all`) is +0 now, and it would pin local section names. A
  lane that renames or moves a function would then see it drop to the end of L. So L stays
  source-driven until the handler shapes settle. Then `--mode all` lifts the fixed-size ceiling
  from 477 to 1022, without the source-level order work.

## Crate identity under a pinned order (`ab341d79`, rejected)

The likely original identity, tried as a recipe change (line-neutral): package and crate `pump`
0.1.0, `#[program] pub mod pump`, program type `Pump`, link script regenerated for that build.
- In rustc order it gives 1027/**192** (-84). The lost windows are the L tail that
  layout-order-census's `bonding_curve_instruction_accounts` wrap fixed. MergeFunctions keeps the twin
  with the smallest mangled name, and the crate name changes those lengths, so the merged
  `ToAccountInfos` bodies land at other def positions.
- With the regenerated U+D script it gives 1027/209 (the same +17).
So crate identity reaches the bytes only through which merged twin survives at which def position.
A full-order script places those bodies directly. The original name buys nothing, which is why the
siblings never recovered theirs.

## Other sibling choices checked (`2fd5f551`)

The Fees patch to `anchor-attribute-program` is 0.31.2 plus `#[used]` on the `declare_program!` ID
statics, and `anchor-syn` 0.31.1 equals 0.31.2. It only keeps otherwise-dropped statics. Pump `.rodata` is
already the original's size with every data offset equal, so it has nothing to add. The remaining
differences give no sign of a dependency version or feature difference: the 8 unmatched windows are
root-crate codegen, and `.rel.dyn` has 2 extra `R_SBF_64_RELATIVE` entries from root `.text` lddw.

## Attempts

| id | trial | result |
| --- | --- | --- |
| `d3ad3242` | offline relink with the U+D script (captured main link inputs) | 1027/293, +17 raw, 0 losses |
| `fc1c0930` | same as the pinned fastbuild recipe (lane work dir and fresh work dir) | 1027/293, sha d7dca7cc, regen reproduces the script |
| `ae684b75` | also L in original order (`--mode all`, 1037 selectors), offline relink | 1027/293, 0 losses, same raw set; not default (see above) |
| `a30bac7d` | model: the 9 wrong-size units placed at L start/end, text start/end | 293 / 209 / 293 / 293: no gain |
| `ab341d79` | crate/package `pump`, `mod pump`, type `Pump`, regenerated script | 1027/192 default order, 1027/209 with script: rejected |
| `2fd5f551` | Fees' `anchor-attribute-program` `#[used]` patch | analyzed: nothing for Pump to gain |
