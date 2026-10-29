# Locate grouped export declarations in their physical captured source

The selected graph's `module` lookup returns `no selected identity` for396623
and660315. That does not establish missing captured source. In one retained
object, physical439587 supplies grouped396623 through uppercase `S`, while
physical524684 supplies660315 through `s`'s optional target argument.

The new explicit source-context mode exposes those declaration witnesses through
the existing CLI, without adding virtual factories or regenerating graph data:

```sh
node app/scripts/factory-graph/cli.mjs module 396623 --source evidence/web/objects/0f4bad575370faed.js
node app/scripts/factory-graph/cli.mjs module 660315 --source evidence/web/objects/0f4bad575370faed.js
```

| Actual declaration | Physical registration and meaning |
| --- | --- |
| `S(...,396623)` at UTF-16/UTF-8 `[84773,84944)` | Physical439587, factory hash `556a5e98fc389f458883751f5ed829f9493c87444c6f5053b676b34a39f05fa9`. Six names map to namespace properties; `Root` maps to `DrawerRoot`, not a second export name. A preceding import initializer candidate is `f=e.i(524684)`. This remains syntax evidence, without claiming an alias-value resolver. |
| `s(...,660315)` at `[13739,16546)` | Physical factory hash `4a95dd69ab776beb22fce660c865256c7cc7ddc091c08d949c92213f537a1f1d`. The actual registration has aliases `[524684,660315,195636]`;660315 is already a literal alias, not a newly found function. This call declares Backdrop/Close/Popup/Portal/Root/Title; separate calls target524684 and195636. |

Both are in `evidence/web/objects/0f4bad575370faed.js`,97201 bytes,
SHA-256 `feb10137dd786820010700c4292fc2c38647c79de5493e6e0689552055ec7cbc`.
396623 has no literal registration in this context (nor in the maintained literal
index);660315 does. The full runtime method/helper definitions, raw declaration,
target, namespace and alias fields have exact source/UTF-16/UTF-8/hash witnesses
in [providers-396623.json](providers-396623.json) and
[providers-660315.json](providers-660315.json).

The runtime is authenticated as `f25d7686d048ae16.js`, SHA-256
`b5f9b5199b99ab6c141f4540f0b7d0fe803c4ecf6956849ecb6e59d3d439272e`.
Its `u.S` builds descriptors and calls `d`; `u.s=d` selects an explicit non-null
target through cache helper `f`, otherwise the current module. `m` may copy a
value/getter descriptor or create a property getter. It does **not** default a
missing alias property to its export name. The shared cache/import definitions
explain how a grouped target can be declared before its import, but declarations
remain conditional on successful producer initialization. No capture, getter,
value expression, factory, import or browser runtime is executed here.

This actual grouped chain was first used by the source attribution in PR1665.
This unit makes that investigation repeatable in the maintained module CLI; it
claims no newly acquired bytes, original-source completeness, new inventory
variants, graph identities, source credit or feature-completion milestone.

## Before/after and checks

Base `094a06f18df738d41e77070c1a009e135671ac1a`'s exact CLI was run with the same
`module <id> --source <object>` arguments. Both commands fail with no selected
identity: [396623](before-396623.log), [660315](before-660315.log). The new mode
returns one authenticated declaration for each; repeated output is byte-identical.
The legacy no-source lookup deliberately retains its old behavior.

```sh
node app/reconstruction/grouped-export-providers/verify.mjs
node --test app/tests/factory-graph-export-providers.test.mjs app/tests/original_source.test.mjs
node --test app/tests/factory_graph.test.mjs app/tests/factory-graph-inventory.test.mjs app/tests/factory-graph-output-root.test.mjs app/tests/factory-graph-bom.test.mjs
python3 scripts/verify_evidence.py
python3 scripts/test_tooling.py
python3 app/scripts/verify-evidence.py
python3 app/scripts/progress.py --check
```

Synthetic controls retain multiple physical providers in the same and different
objects, numeric/string target types, null/implicit contexts, Unicode byte ranges,
empty and missing alias properties, mixed constants/getters/setters, direct comma
statements and unsupported/dynamic forms. Capture tampering, forged index ranges,
different runtime bytes and path escapes fail. Nested functions/blocks and
lookalike receivers contribute no declarations. Tests parse expressions containing
throwing function bodies without calling them. Existing graph tests include a
full authenticated selected-corpus rebuild. [preserved-inputs.json](preserved-inputs.json)
binds15 unchanged inventory/manifest/core/source-helper/report files.

## Limits

- Only explicit captured source contexts and direct factory-body expression
  statements are inspected. Absence does not prove whole-corpus absence.
- Every physical occurrence is retained; no active variant/initialization winner
  is selected. Implicit target IDs are possible invocation contexts, not simultaneous
  export targets.
- Preceding import initializers are raw syntax candidates. The diagnostic does not
  resolve lexical bindings, aliases, assignments or control flow. It does not
  duplicate pending PR1180's graph lexical-binding correction or PR1385's graph
  literal-origin correction.
- Unsupported descriptor forms return no partial names. Dynamic targets remain
  explicitly unresolved. Runtime descriptor evaluation can still fail.
- **Existing graph aggregate export lists still ignore `s`'s target argument and
  omit uppercase `S`. This unit does not repair those lists.** The old module
  lookup, all reports, identities, reachability, inventory IDs/counts and capture
  bytes remain unchanged.
- No UI/browser/backend/build/native equivalence, API compatibility, full-source
  closure or security qualification is claimed. No frontend server was started.
