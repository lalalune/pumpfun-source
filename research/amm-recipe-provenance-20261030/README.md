# AMM recipe input provenance at `8498ea4c`

This packet checks the current tracked source inputs for the maintained AMM
workspace recipe, without compiling source or reading or running the original
program. It is a bounded reproducibility check, not a fresh bytecode match.

## Finding

At source commit `8498ea4c5307d8537484464d27d6d82bb90a85c1`,
`scripts/amm_sell/workspace_recipe.py` selects exactly 68 files from
`programs/pump-amm` and `crates/native-transfer-fee`. The Git tree contains
exactly the same 68 ordinary blobs. Their current bytes match both the pinned
Git blob IDs and the SHA-256 values in `manifest.json`. The recipe transforms
the standalone crate manifest into a 69-file workspace; all 59 Rust files stay
byte-identical. A fresh source-only stage passes its own workspace verifier.

The same commit tracks neither `repro/status.json` nor any
`repro/pump_amm` checkpoint. The repository's selected AMM verifier refers to
those missing paths. Consequently this packet cannot recheck the root README's
785/785 raw-window or meaningful-ELF-equality claims. It does not revise those
maintained claims or treat source-input equality as compiled-program equality.
`scripts/amm_sell/README.md` also documents an older 784/785 sell investigation;
its historical baseline is preserved.

## Reproduce

From a checkout containing the two complete source directories and this packet:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B research/amm-recipe-provenance-20261030/verify.py
PYTHONDONTWRITEBYTECODE=1 python3 -B research/amm-recipe-provenance-20261030/test_verify.py
```

The verifier checks the pinned Git tree and current source bytes, regenerates
the 69-file workspace in a temporary directory, and removes only that temporary
directory. It never invokes Cargo, a compiler, RPC, a VM, the target program,
or the original ELF. It checks the recipe path and SHA-256 before executing
exactly those verified Python source bytes, without an import bytecode cache.
The three synthetic tests reject a mismatched source before its sentinel side
effect, show a stale timestamp-matching `.pyc` cannot replace the verified
source, and reject a symlinked recipe. A sparse checkout missing any pinned
input fails closed.
The selected historical checkpoint cannot be recovered from this packet; it
would require separately authenticated artifacts and their full verification.
