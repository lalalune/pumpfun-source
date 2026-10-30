# AMM source-staging output containment

The public `scripts/amm_sell/workspace_recipe.py stage` command could write into
its own inputs before rejecting the resulting workspace. At main
`1e04f5b34aa33c53f2b20b4200ba4ba266b4203e`, an output below
`crates/native-transfer-fee` created 69 files inside that consumed dependency,
then failed verification. A directory symlink into either consumed crate also
bypassed the old lexical check.

The fix checks the resolved output against both actual `MEMBERS` before any
staging writes, and uses that same resolved destination for mkdir and copying.
The existing lexical leaf-symlink/existing-output refusal remains. A canonical
existing destination is also refused before staging. The final product and test
source were frozen at `642f37bcaa5cb7da76961b3df037e3f8d5602bbe`.

Using the checked path for writes matters: the intermediate fix checked a
resolved path but still wrote through the lexical path. The peer review
reproduced `native-transfer-fee/missing-parent/../../safe-workspace` creating
`missing-parent` inside the input crate even though the destination resolves
outside it. The final fix preserves those input directories too.

## Validation

Run from the repository root:

```sh
python3 -I -B scripts/amm_sell/test_workspace_recipe_staging.py
python3 -I -B -O scripts/amm_sell/test_workspace_recipe_staging.py
python3 -B scripts/verify_evidence.py
python3 -B scripts/test_tooling.py
```

The eight package-local tests invoke the actual staging CLI with an empty
`PATH` and authored temporary Cargo/source fixtures. They cover normal staging,
both input members, directory aliases, safe external aliases, existing outputs,
and missing-parent/`..` paths. Rejection checks include source bytes and path
membership. The final test file is byte-identical across the original and final
replays:

| Source phase | Result |
| --- | --- |
| Original `1e04f5b3` | 8 tests, 5 causal failures |
| Intermediate `6eada59f` | 8 tests, 2 causal `..` failures |
| Final `642f37bc` | 8 pass; 8 pass under `-O` |

The earlier six-test intermediate success is retained privately; it does not
cover the subsequently discovered `..` counterexample. `tests-intermediate.log`
uses the final eight-test method, with failures reaching source mutation checks.

`SOURCE-INPUTS.json` binds the real public inputs to the base Git blobs and file
hashes. `QUALIFICATION.json` records actual compiler-free staging of those
68 inputs. All 69 safe workspace file hashes are identical before and after,
including all 59 Rust files. It also binds the exact original/final recipe and
test hashes. A separate changed-Rust tamper control was rejected. The new
containment checks do not transform Cargo inputs or Rust.

Independent peer review found the intermediate `..` issue and checked the final
correction. `PEER-REVIEW.json` records its two focused replays and independent
68-input/69-output hash comparison; it is separate from the author's test runs.

The required evidence command passes all nine captures. The unchanged required
tooling command runs 40 tests and reports three errors in
`InterfaceInventoryEncodingTests`: its temporary fixture omits
`evidence/original/pump/deployed.so`, followed by an empty-output `IndexError`.
The retained log shows the failure. The changed recipe is not imported by that
test. `REQUIRED-INPUTS.json` binds all 65 common-gate inputs to the base Git
blobs; no required test was removed or weakened.

## Scope and attribution

Open PR [#2048](https://github.com/lalalune/pumpfun-source/pull/2048) owns the
separate source-recipe provenance packet and its missing selected-checkpoint
finding. Its files are untouched. This packet supplies the before/after inputs
needed for the containment regression, with no first-recovery claim for that
recipe. A merge of this guard change will naturally change the public recipe
hash; it does not retarget any sealed historical recipe.

No Cargo, compiler, SDK, VM, CPI, RPC or target-program execution was performed.
No program Rust, toolchain, comparator, linker input or selected checkpoint was
changed. This does not requalify the README's AMM window/meaningful-ELF claims or
restore the absent selected checkpoint. The protection is for the public source
stager; it is not a concurrency/security guarantee for all build callers.
