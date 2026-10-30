# V3 Buy crossing loads and a held-back full normalized match

Base: `094a06f18df738d41e77070c1a009e135671ac1a`, including merged #1550.
Target: `trade::buy` / `buy_v3`, original `0x147ba0`, 3,672 bytes.

The applied source change reads the associated base-vault amount before the curve
quote reserve and migration fee, then passes the same three values to
`v3_pool_before`. The pinned compiler now schedules those loads in the original's
order. All error sites retain their physical lines. Only this caller's normalized
body changes; its 29 ordered immediate-callee signatures, `.rodata`, and
`.data.rel.ro` are unchanged. There are no new or removed named functions.

| State | Target bytes | Instruction alignment | Normalized / raw | Membership changes from base |
| --- | ---: | ---: | ---: | --- |
| Current main control | 3,680 | 0.9313835771 | 1,024 / 277 | — |
| **Applied load-order change** | **3,680** | **0.9358830146** | **1,024 / 277** | **None** |
| Unapplied full-match experiment | 3,672 | 1.0 | 1,025 / 276 | Normalized gain `0x147ba0`; raw loss `0xa868` |

The applied change is partial recovery, not a new matched function. Alignment is
a diagnostic; the unmodified official `score.py` supplies the membership counts.
Original-only/candidate-only aligned instructions improve from 30/31 to 28/29.

## Full-match experiment: source found, not integrated

`full-match.patch` applies **on top of** the load-order change and contains two
additional source transformations:

1. `v3_buy_costs(...).map_err(core::convert::identity)?` preserves the same error
   while changing the compiler's placement of its return block and payload load.
2. An `#[inline(always)] buy_body` wrapper restores the shared return layout without
   adding the event-result tag test introduced by `v3_emit_buy(...)?; Ok(())`.

Together with the load-order change, the ordinary pinned source build gives a
complete normalized match for `0x147ba0`. No edited IR, binary patch, padding,
original-code injection, or toolchain/scorer modification produces these images.
The experiment is source reconstruction, not authenticated historical source.

The eight-byte shrink changes the relative call immediate of a 24-byte Debug
forwarder that currently supplies the raw match for `0xa868`. Its address remains
`0xa7b0`; its callee moves from `0x1a24f8` to `0x1a24f0`, and the call immediate
changes from `0x32fa7` to `0x32fa6`. The callee's complete normalized body is
unchanged. `raw-loss.json` retains the actual bytes and targets. This is still a
raw membership loss under the repository's acceptance rule, so the experiment is
**not applied to programs/pump**. Do not apply it until a combined ordinary source
build preserves every baseline membership. No compensating padding was added.

Both proposed and experimental callers preserve all 29 ordered callee signatures
relative to control. Two callees still differ from the deployed original:
`v3_buy_costs` (`0x80df8`, 2,136 vs 2,120 bytes) and `v3_execute_buy` (`0x83c00`,
3,448 vs 3,440 bytes). Thus even a normalized caller match is not a claim that its
complete transitive behavior or the whole program is proven identical.

## Validation

- Normal pinned v1.44 identity builds, locked and offline, with no stack warnings.
  Both proposed and experimental builds reproduce their entire stripped and
  unstripped ELF hashes in a second normal build. This is not a cold-dependency
  reproducibility claim. Hashes are in `SUMMARY.json`; compiler logs are retained.
- All 1,035 original windows scored in every cohort. Proposed source preserves
  every normalized and raw membership, not merely the aggregate counts.
- 117 existing configured-fee Buy cases plus 36 new crossing cases. The crossing
  cases exceed the real reserve with partial fill both on and off, two creator-fee
  settings, and SOL, SPL Token, and Token-2022 quote accounts.
- **153 cases × four images = 612 signed transactions**: original, control,
  proposed and experimental. State, errors, events, inner instructions, return
  data and ordered logs agree after excluding only complete compute-meter lines.
  Each image has 129 successes and 24 expected errors; the new crossing cases
  contain 24 successes and 12 expected errors. Transaction signatures were
  independently checked from their serialized bytes. Synthetic token quotes have
  no transfer-fee extensions; this is not exhaustive path coverage.
- Root capture verification passes for all nine captures, and ten tooling tests
  pass. `git diff --check` passes. No claim is made about unrelated legacy CI.

`runtime.json.gz` is one retained run, not a sum of repeated replays. `replay.py`
uses the unchanged checked-in fixture and configured-fee logic, relocates the
historical fixture input, and adds only the explicit crossing cases. The fixture
is the same historical public fixture used by #1292. No RPC is performed.

## Reproduction

The 71-file control source archive includes Rust, manifests, lockfile and IDLs.
`source-inputs.json` records all three complete source cohorts. `load-order.patch`
maps control to proposed source; `full-match.patch` maps proposed to experimental.
Compiler-produced ELF files remain outside Git, as required by the recovery rules.

From the repository root, with the SDK prepared as in `reconstruction/README.md`:

```sh
lane=reconstruction/pump-main/lanes/v3-buy-crossing-layout
task_dir=$(mktemp -d)
mkdir -p "$task_dir/control" "$task_dir/candidate" "$task_dir/experimental"
tar -xzf "$lane/control-source.tar.gz" -C "$task_dir/control"
cp -R "$task_dir/control/." "$task_dir/candidate/"
git -C "$task_dir/candidate" apply --unidiff-zero "$PWD/$lane/load-order.patch"
cp -R "$task_dir/candidate/." "$task_dir/experimental/"
git -C "$task_dir/experimental" apply --unidiff-zero "$PWD/$lane/full-match.patch"
for cohort in control candidate experimental; do
  python3 reconstruction/harness/fastbuild.py \
    --src "$task_dir/$cohort/programs/pump" \
    --work "$task_dir/build-$cohort" --out "$task_dir/out-$cohort"
done
python3 reconstruction/harness/score.py "$task_dir/out-control/unstripped.so" \
  --json "$task_dir/control-score.json"
python3 reconstruction/harness/score.py "$task_dir/out-candidate/unstripped.so" \
  --baseline "$task_dir/control-score.json" --json "$task_dir/candidate-score.json"
python3 reconstruction/harness/score.py "$task_dir/out-experimental/unstripped.so" \
  --baseline "$task_dir/control-score.json" --json "$task_dir/experimental-score.json"
python3 "$lane/replay.py" --control "$task_dir/out-control/candidate.so" \
  --candidate "$task_dir/out-candidate/candidate.so" \
  --experimental "$task_dir/out-experimental/candidate.so" \
  --output "$task_dir/runtime.json.gz"
python3 "$lane/verify_packet.py" --signatures
```

Replay and signature checking require `solders==0.27.1` (validated with Python
3.12). `verify_packet.py` checks retained evidence; it does not rebuild or rerun
the VM. The build/scoring/replay commands above perform those separate checks.

## Prior work and overlap

Open and recently closed PRs were checked before work and again before publication;
the bounded snapshots and selection decision are in `pr-review.json`.

- #1550 supplies the merged `v3_can_cross` improvement this work builds on.
- #1419 identified the remaining load-order issue in an IR oracle. Credit that
  analysis for the direction; this PR supplies a compiling source expression and
  validation on current main. Its pending analysis patch is not copied here.
- #1479 and #1539 change **v3_execute_buy**, a different function in the same
  file. #1518 changes **buy_exact_quote**. None is the applied Buy caller change.
- #1565 and #1518 independently document the same raw forwarder sensitivity in
  other functions. Their source changes have not been included or reimplemented.
- #1292 remains separate verification of the earlier merged V3 Sell checkpoint.

Twenty-two source attempts, including failures and unchanged binaries, are kept
in `attempts.jsonl`. The first uninitialized-binding run had a local Cargo staging
collision; its serialized retry is byte-identical to control. Final proposed and
experimental images were built serially and reproduced independently. This
infrastructure failure is not evidence against the Rust spelling.
