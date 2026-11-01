# Fresh-control composition qualification

The default `integrate.py` flow remains an exploratory historical-baseline
comparison. It composes source snapshots, builds the candidate once, and shows
changes relative to the checked-in score. That mode cannot prove that a current
upstream match survived composition.

`--fresh-control` is the fail-closed qualification mode. It admits a caller-pinned
base source tree, requires every declared part to apply (or records an identical
part as an explicit no-op), and performs sequential cold base and candidate
builds. Both binaries are scored by the official scorer against private copies
of the same captured ELF and function inventory.

## Prepare snapshots

Use immutable crate snapshots for the fresh upstream base, each delivered part,
and the source revision from which each part was derived. No snapshot may contain
links or overlap the output tree. Compute the base identity with the maintained
source receipt code:

```sh
BASE_SOURCE=/path/to/fresh-main/programs/pump
BASE_SHA256=$(python -B -c \
  'import sys; sys.path.insert(0,"reconstruction/harness"); from source_inputs import snapshot; print(snapshot(sys.argv[1])["sha256"])' \
  "$BASE_SOURCE")
```

Then qualify several non-overlapping changes:

```sh
python -B reconstruction/harness/integrate.py \
  --name contributor-composition-001 \
  --base-src "$BASE_SOURCE" \
  --expect-base-sha256 "$BASE_SHA256" \
  --fresh-control \
  --part window-a=/snapshots/window-a \
  --base-of window-a=/snapshots/window-a-base \
  --part window-b=/snapshots/window-b \
  --base-of window-b=/snapshots/window-b-base \
  --timeout 900
```

The name is an immutable publication key under `reconstruction/integ/`; an
existing output is never replaced. Each `--base-of` value must be the exact
source snapshot from which its part was developed. Omitting it means the part
was derived from `--base-src`.

## Acceptance

The command exits zero only if:

- every nonempty part applies completely and no patch tool reports an error;
- the admitted base digest still equals `--expect-base-sha256`;
- both isolated builds succeed with valid stack reports;
- reported source and ELF hashes match the retained inputs and artifacts;
- source, compiler, SDK, target libraries, scorer, captured ELF, and function
  inventory remain unchanged throughout both builds;
- both reports have identical address and byte-size domains; and
- the candidate loses no normalized or raw match present in the freshly built
  base.

An added, missing, or resized window is a domain mismatch and rejects the pair.
Ambiguous symbol membership is listed in each score summary. Gains are retained
but do not excuse any loss. A conflict, build failure, corrupt score, mutation,
or interrupted dependency is a rejection, never a passing comparison.

## Receipts

`report.json` records composition inputs and every applied, empty, conflicted,
or rejected part. `fresh-control/receipt.json` is canonical sorted JSON and is
the authoritative build/score decision. It retains:

- complete source manifests including directories and execute bits;
- compiler, SDK, target-library, scorer, and captured-evidence hashes;
- public build receipts and hashes of both stripped and unstripped binaries;
- both complete score reports and their hashes;
- gained/lost/raw/normalized/domain comparisons; and
- hashes and byte lengths for all retained artifacts except the self-referential
  receipt itself.

Reports are published atomically. Repeating the same admitted inputs with the
same artifact bytes produces the same inner receipt; host paths and elapsed time
are excluded. Independently re-hash every retained artifact, source snapshot,
binary, score, toolchain input, and scorer input and recompute the decision with:

```sh
python -B reconstruction/harness/verify_fresh_control.py \
  reconstruction/integ/contributor-composition-001/fresh-control
```

The verifier does not trust the producer's acceptance boolean or comparison. It
loads both score reports through `compare_scores.py`, independently re-scores
both actual unstripped ELF images with the admitted official scorer, and checks
every retained membership and symbol row before deriving the decision again.
Boolean and integer claims use exact JSON types. Receipt bytes, source snapshots,
scorer inputs and retained artifacts are checked again after verification.
Links, special files and unrecorded directory membership are refused.
For a standalone pair outside `reconstruction/integ`, supply
`--base-source` and `--candidate-source` explicitly.

The producer and reader execute a private graph of captured local Python source
bytes, including lazy imports. Timestamp-valid bytecode caches cannot replace
those modules, and the source graph is rechecked before and after execution.
External compiler/linker Python hooks receive a private empty cache prefix and
bytecode writes are disabled; cache changes reject the build. Both earlier ELF
images and score files are rechecked after the second build, so later build code
cannot silently alter an already-scored artifact. Canonical Python module entries
are not replaced by this private graph.

This mode intentionally performs two cold Pump builds and should be scheduled as
the only heavy SBF build on a host. Saved score summaries cannot substitute for
either fresh build.
