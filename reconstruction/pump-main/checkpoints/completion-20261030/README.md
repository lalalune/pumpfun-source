# Completion checkpoint — 2026-10-30

The current Pump Main identity build matches **1,032/1,035 windows** (347 raw,
685 normalized only). The three unmatched windows are `create_v2::execute`
(`0x1e7c0`), `admin_cto::execute` (`0x22a10`) and `multi_hop_curve::swap_hop`
(`0x5b3b0`). Together they contain 61,560 code bytes.

Across the five selected program checkpoints, **3,335/3,338 windows (99.9%)**
match, covering **5,151,568/5,213,128 code bytes (98.8%)**. These are bytecode
match metrics, not an estimate of engineering work remaining. Normalized
matches mask the scorer's specified call/address operands. Pump Main does
not yet have whole meaningful ELF identity.

## Evidence

- [summary.json](summary.json) pins the built main revision, source digest,
  tool and binary hashes, counts and verification limits.
- [pump-windows.json.gz](pump-windows.json.gz) retains the per-window output
  from `reconstruction/harness/score.py`.
- [pump-source-inputs.json](pump-source-inputs.json) binds all staged Pump
  inputs to the fresh identity build. The compiler reported no stack warnings.
- [amm-score.json](amm-score.json) records a fresh current-source native
  AMM build: 785/785 raw windows. Its 1,268,504 meaningful ELF bytes equal
  the captured program; the captured allocation has a separate zero suffix.
- [other-programs.json](other-programs.json) records the other four program
  checkpoints and their verification boundaries. Fees and Mayhem retain
  historical exact checkpoints: current input staging checks passed, but
  their compilers were not rerun and the old full receipts are absent from
  the current tree. Donation Relay's retained native cold-build packet
  verifies current source inputs and literal meaningful ELF equality.

Pump was built from main `974ba6ab302c352b3c6440e47d7aa61d4cdf7944`.
The subsequent main revision recorded in `summary.json` has identical Pump
source, `fastbuild.py`, `score.py` and scoring inputs.

To reproduce the Pump measurement from this source tree:

```sh
python3 reconstruction/harness/fastbuild.py --src programs/pump --work /tmp/pump-checkpoint-work --out /tmp/pump-checkpoint-out --recipe identity
python3 reconstruction/harness/score.py /tmp/pump-checkpoint-out/unstripped.so --no-baseline --json /tmp/pump-checkpoint-out/score.json --quiet
```

## Open-PR review

[pr-review.json](pr-review.json) records 85 PR heads observed during the
review, including new PRs arriving while main advanced. None supplies an
additional demonstrated official completion gain against the reviewed main.
The advertised normalized matches in #2377 and #2272 already exist through
#2397 and #2346. Other program variants are already incorporated, superseded
or partial; the remaining PRs add research, tests or tooling. #2208's ten raw
gains describe an older experiment already represented in current main.

No score-neutral or regressing program variant was merged for this update.
The review does not constitute a correctness review of unrelated tooling PRs.
