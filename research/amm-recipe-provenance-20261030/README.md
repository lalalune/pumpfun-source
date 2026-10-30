# AMM recipe input provenance at `8498ea4c`

This packet checks the source inputs for the maintained AMM workspace recipe as
tracked at the pinned source commit, without compiling source or reading or
running the original program. It is a bounded reproducibility check, not a
fresh bytecode match.

## Finding

At source commit `8498ea4c5307d8537484464d27d6d82bb90a85c1`,
`scripts/amm_sell/workspace_recipe.py` selects exactly 68 files from
`programs/pump-amm` and `crates/native-transfer-fee`. The Git tree contains
exactly the same 68 ordinary blobs. Their bytes match both the pinned Git blob
IDs and the SHA-256 values in `recipe.json`. The recipe transforms the
standalone crate manifest into a 69-file workspace; all 59 Rust files stay
byte-identical. A fresh source-only stage passes its own workspace verifier.

The recipe SHA-256 in `recipe.json` is the recipe tracked at that same
commit. Later edits to the recipe (for example #2139) or to the AMM sources do
not change this finding and do not affect the verifier.

The same commit tracks neither `repro/status.json` nor any
`repro/pump_amm` checkpoint. The repository's selected AMM verifier refers to
those missing paths. Consequently this packet cannot recheck the root README's
785/785 raw-window or meaningful-ELF-equality claims. It does not revise those
maintained claims or treat source-input equality as compiled-program equality.
`scripts/amm_sell/README.md` also documents an older 784/785 sell investigation;
its historical baseline is preserved.

## Reproduce

From a checkout whose Git history contains the source commit (in a shallow
checkout, first run `git fetch origin 8498ea4c5307d8537484464d27d6d82bb90a85c1`):

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B research/amm-recipe-provenance-20261030/verify.py
PYTHONDONTWRITEBYTECODE=1 python3 -B research/amm-recipe-provenance-20261030/test_verify.py
```

The verifier reads the recipe and the two source trees from the source commit's
Git blobs into a temporary directory, checks each written file against its blob
ID, regenerates the 69-file workspace there, and removes only that temporary
directory. It does not read the working tree's recipe or AMM sources. It never invokes Cargo, a compiler, RPC, a VM, the target program,
or the original ELF. It checks the recipe path and SHA-256 before executing
exactly those verified Python source bytes, without an import bytecode cache.
The loader controls reject a mismatched source before its sentinel side
effect, show a stale timestamp-matching `.pyc` cannot replace the verified
source, and reject a symlinked recipe. A checkout missing the source commit
fails closed. Historical controls also stage the real pinned commit without reading current source bytes, reject altered input/workspace hashes, and reject a tree object used as a commit.
The selected historical checkpoint cannot be recovered from this packet; it
would require separately authenticated artifacts and their full verification.

The provenance record is named `recipe.json` because it describes source and
recipe bindings rather than a packet-wide file-hash manifest. The repository
audit still executes `verify.py`; the filename change does not bypass the
historical source and workspace checks above.
