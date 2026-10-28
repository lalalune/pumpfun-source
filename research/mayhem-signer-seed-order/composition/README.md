# Checked-arithmetic composition: retained negative controls

The subsequent [arithmetic-lowering investigation](arithmetic/README.md) reuses
PR #327's overflow-tuple form and composes it with late inline seeds. It restores
price-before-guard ordering but leaves the original branch layout and complete
handler unmatched. Actual compiler traces and repeated outputs are retained.

The late signer-seed read from this packet does not compose cleanly with the
merged trade source in [PR #330](https://github.com/lalalune/pumpfun-source/pull/330).
The native baseline reproduces all four upstream partial handler shapes and
their resolved callee sequences. Applying any of three late-seed forms reduces
Legacy Sell's ordered callee correspondence from **50/51 to 45/51**, despite
retaining its complete callee multiset. These are negative source controls;
the higher instruction overlap is not an overall recovery.

The [compiler-pass follow-up](placement/README.md) now locates this divergence
in LLVM's block-placement pass. Both variants have the same 51-callee sequence
before the pass and different sequences after it; each after-sequence matches
its final ELF. The score is about file layout, not dynamic execution order or
a behavioral regression. Four actual diagnostic builds retain both optimized
IR and before/after machine traces, with complete output bindings.

| Form | Handler bytes | Context bump-load offset | Diagnostic aligned slots | Ordered callee correspondence |
| --- | ---: | ---: | ---: | ---: |
| Original | 12,992 | 6,296 | — | 51/51 |
| Merged composition, native baseline | 12,864 | 2,368 | 599 | 50/51 |
| Inline late seeds | 12,848 | 6,136 | 954 | 45/51 |
| Named accounts/context, late seeds | 12,640 | 6,168 | 366 | 45/51 |
| Context literal, late seeds | 12,800 | 6,152 | 752 | 45/51 |

Both alignment columns use `SequenceMatcher(autojunk=False)` on ordered
normalized instruction slots or resolved immediate-callee identities. They
do not prove recovered instructions, dynamic execution order, CFG equivalence,
or a complete body match. Imported calls participate in the 51-call sequence;
their implementations are not closed by matching symbol names.

The controls start from all **67 exact source inputs** at
`ea2b4e13db1c4e3d81836a4bdacbf312697d74d1`, now merged upstream. The acquired
source archive, three overrides, source maps and complete upstream compiler
outputs retain their exact Git blob identities and original manifest hashes.
Main was reviewed through `200b0f5c5185e8d8f16711f92bb1b4a59c8cf6c7`.
The merged source includes checked sell arithmetic and typed price checking
from PR #327 plus the BuyV2 composition. Allocator-provider research remains a
separate compiler context; it is not silently included here. Later main
`842a263682d883d39fd033b4b401faf54c7a7b51` includes the separately reported
O0075 sweep recovery. These pinned trade-source controls do not include that
source or claim its 433-window result; the paused sweep/burn scope is unchanged.

Only `pump_interface.rs` changes in each new control. Three source forms
replace its Legacy Sell CPI preparation region with the already retained
parent controls. Two further paired controls move the checked-price
`ok_or(...)?` conversion before the price calculation. These produce complete
ELFs identical to their respective early- and late-seed parents. Thus this
particular eager/deferred conversion cannot resolve the observed gap. All
other modules, the CPI error macro line/column and line counts are held.

Eight actual isolated root compilations reuse the previously recorded native
dependencies: baseline, its repeat, three CPI forms, an inline repeat and two
price-conversion controls. Both complete outputs repeat for baseline and
inline sources. Logs, exact source maps, commands/environments, tool/dependency
hashes, linker captures, symbols ELFs and ordinary stripped ELFs are retained.
These eight runs are **not fresh dependency builds**. Originals are comparison
inputs, never compiler/linker inputs; no allocation image or binary rewriting
is used. `recorded-producer.py` and `recorded-acquisition.py` preserve the actual
exploratory scripts and original workspace locators.

The public composition `rebuild.py` was also executed in a new output directory.
This ninth successful build starts with fresh dependencies, records **163
actual compiler commands** (85 target commands), and reproduces both complete
inline outputs above. Its separate logs, launch, compiler records and output
comparison are retained under `rebuild-validation/`. Identical ELF bytes reuse
the inline artifact files. Complete dependency-archive equality is not claimed.

All eight builds preserve exactly the native **432 normalized / 77 raw-local /
431 injective** inventory and **4,314 positive internal immediate-call
observations**. This internal-only diagnostic excludes imported calls and must
not be substituted for upstream's 4,383 mixed internal/import observations.
The upstream Linux artifact's **432/84** and qualified **432/100** counts stay
separate. Legacy Buy, BuyV2 and SellV2 retain their complete baseline normalized
shapes and ordered callee sequences. Every original business body remains
unmatched. There is no target execution, inherited runtime qualification,
selected-source promotion, transitive/data closure or historical-source claim.

The parent verifier automatically replays this evidence. The standalone check
is also available, using only ordinary Python's standard library:

```sh
python3 -I -B research/mayhem-signer-seed-order/composition/verify.py
```

`rebuild.py` is an explicit optional full dependency/root rebuild using the
same caller-supplied pinned Windows tools and offline vendor inputs as the
parent recipe. Use `--variant baseline` or one of the retained source labels,
plus the parent's `--sdk`, `--target-sysroot`, `--vendor`, `--msvc`,
`--windows-sdk`, `--kit-version` and a new `--output` directory. It never
downloads dependencies or executes the target. Run this explicitly; the
offline verifier does not build anything.
