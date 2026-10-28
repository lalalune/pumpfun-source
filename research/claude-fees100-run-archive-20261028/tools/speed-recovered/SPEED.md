# Faster edit -> build -> measure loop (speed lane, 2026-10-27)

Every tool here keeps the existing interfaces. Old scorer copies are kept in `tools/legacy/` for cross-checks.
All timings below were measured at a load average of 100-200 on this 16-core machine, so wall times are about 6x CPU times.

## 1. Scoring: fastwin.py (installed: fndiff.py, measure.py, dis.py and datacheck.py use it automatically)

| command | before | after |
|---|---:|---:|
| `fndiff.py ADDR CAND.so` | 12-30 s | **0.2-0.4 s** (0.3 s on a never-seen candidate) |
| `measure.py CAND.so --baseline B.so` | 9 s | **0.17 s** |
| `fastdiff.py` (5 candidates x 3 windows + measure) | (would be ~5 min) | **0.9 s** |

- Cause: the legacy tools called `window_map.windows()` up to 5 times per run, and `elf_layout()` (which sha256-hashes
  the whole 1.2 MB image) ran about 7,800 times per fndiff.
- `fastwin.windows(img)` returns exactly `window_map.windows(img)`. The normalizer is the same, `elf_layout` is memoized per image,
  and results are cached on disk in `tools/cache/windows/<sha256>.<normver>.pkl`. normver hashes window_map.py,
  elf_helpers.py and analyze.py, so any change to the normalizer invalidates the cache.
- A cache miss is computed by `fast_windows()`, which decodes each window once with no per-instruction dicts.
  Verified field-by-field equal to the reference on 65 images: `python3 -I fastwin.py --selftest IMG...`.
  `FASTWIN_REFERENCE=1` forces the reference implementation (still memoized and cached). Each cached image takes
  about 190 KB, and `tools/cache/` can be deleted at any time; it is rebuilt on demand. Each cached image takes
  about 190 KB, and `tools/cache/` can be deleted at any time; it is rebuilt on demand.
- Output equality: 21 command variants (fndiff on 3 windows x 4 candidates x {default, --context, --raw, --full},
  --symbol, measure with/without baseline, dis with --mask/--names-from) give byte-identical stdout and exit codes to `legacy/`.
- Caveat (pre-existing fndiff behavior): `identical=False` can persist after a window is normalized-gained, because
  fndiff prints lddw string previews (they depend on .rodata layout) and names original callees through unique pairs
  (ambiguous groups print another member's name). Example: w583 native 120816 is gained, yet fndiff shows span 3. measure.py's gained set is authoritative.

## 2. fastdiff.py: batch scorer, N candidates x M windows

    python3 -I fastdiff.py A.so B.so C.so [--addr 147944,163920] [--measure [--baseline B.so]] [--diff 20] [--tsv out.tsv]

This prints one TSV row per (candidate, window): `ratio span identical orig_insns cand_insns cand_bytes`, plus `normalized raw lost gained`
with `--measure`. The default baseline is the native one of `frontier/CURRENT`. The numbers are computed exactly as in fndiff.py
(cross-checked on 15 pairs). `--symbol ADDR=SUBSTR` overrides the candidate function. Library: `score(img, addr)` and `measure(img, base)`.

## 3. dbuild.py: direct rustc, same contract as nbuild.sh, proven byte-identical

    python3 -I dbuild.py SRC_DIR TARGET_DIR OUT_PREFIX [extra rustc args]   # -> OUT-symbols.so / -build.log / -result.json

- First build of a dependency configuration ("cargo" mode) runs nbuild.sh's exact cargo command (with -vv). It records the
  pump_fees rustc argv and environment, freezes the dependency artifacts as APFS clones in `tools/direct/<depkey>/`,
  replays the template once, and enables it only if the replay's .so equals cargo's byte for byte.
- After that ("direct" mode) it runs the recorded rustc against the frozen deps. TARGET_DIR can be an **empty dir**: the
  outputs are 9.5 MB instead of a 324 MB warm-target clone. Compile errors are rendered as cargo would render them.
- depkey hashes Cargo.toml, Cargo.lock, programs/pump-fees/ (except src/), pump-fees-math/, .cargo/, every manifest
  `path=` dependency/patch (vendored macro, patched anchor-lang, ...), ~/.cargo/config and the toolchain. Any change there
  falls back to cargo and captures a new template. Edits under programs/pump-fees/src always go direct.
- Proofs (symbols sha256 equal to plain nbuild.sh):
  - Template validation: w582 replay == cargo, e6849af5…
  - Direct, empty target: w582 gives e6849af5… (= native/w582 baseline); w583 gives 8b13fb02… (= native/w583 baseline).
  - Edited variants (comment-only, line shift, statement swap): farm run below (dbuild direct vs nbuild.sh).
- Validated template: depkey `d1b0447e2face6d5c5d0` = w582 = w583 and their lane clones. The pr304 trees have other
  path deps (patched anchor-lang / vendor path): their first dbuild runs cargo and captures their own template.
- `DBUILD_FORCE_CARGO=1` gives plain cargo behavior. Each compile holds one native slot (same lock as nbuild.sh).

Measured cost split (native): an all-Fresh cargo run takes 1.2 s wall / 0.4 s CPU. pump_fees rustc takes 11-12 s CPU per build.
dbuild direct used 11.2 s user vs nbuild's 12.0-12.4 s. The real native bottleneck is CPU contention (rustc gets ~22% of a
core at load 150-200), not cargo. JOBS has no effect on edit builds: only pump_fees recompiles, as one crate with one
codegen unit and one LLVM thread.

## 4. farm.py: many variants at once, leaderboard

    python3 -I farm.py --base R/shared/frontier/w583 --out R/lanes/<lane>/farmX --addr 147944 \
        [--include-base] [--parallel 3] [--builder dbuild|nbuild] [--variants-dir DIR] [NAME=]VARIANT ...

- A VARIANT is a `.patch`/`.diff` (git a/b/ or `diff -ru /abs/base /abs/variant`; headers are rewritten to clone-relative
  paths and nothing outside the clone can be touched), a `.py` mutator (`python3 -I m.py CLONE_DIR`), an overlay dir
  (tree-relative files), or a full tree.
- For each variant it makes an APFS clone of the base, applies the variant, builds (dbuild direct by default, so no target
  clone), and scores every `--addr` exactly like fndiff, plus normalized/raw counts and lost/gained vs the CURRENT native baseline.
- `FARM/leaderboard.tsv` is rewritten after every finished variant: loss rows last, then identical, ratio desc, span asc,
  with a `dup_of` column for identical binaries. `results.jsonl` keeps every row. Re-running skips unchanged variants;
  `--rescore` only rescores. Failed builds list their `error` lines.
- `--parallel` is this farm's concurrency. Each compile still waits for one of the 6 machine-wide native slots shared by
  every lane, so keep it at 2-4.

## 5. Not done / next ideas (ranked)

1. **Container (cbuild.py, ~90-160 s/build):** the same direct-rustc template plus a container-local target
   (`/tmp` in the container instead of virtiofs `/work/targets`) should roughly halve it. Codex measured
   268 s → 161 s for direct rustc alone in its container: `REPO/work/fees-next-trial/parallel-sharing/fees-direct-native-control-proof.json`.
   Validate the same way (replay sha == cargo sha) before use.
2. Byte-identity tests still to run with `dbuild.py SRC TGT OUT <flag>` vs plain: `-Zthreads=4` (parallel front-end;
   gives more CPU share under contention) and `-C incremental=TGT/inc` (reuses typeck/MIR across edits; with
   codegen-units=1 the LLVM part is not saved). Adopt only if the sha equals plain across several edited variants.
3. `--emit=obj` plus objfn.py for single-function screening skips link and rlib writing (a small saving, under 10% by
   estimate). Dropping `--crate-type lib` would change symbol export levels, so it is not expected to be byte-identical.
