# fees100 run archive (Claude parallel-lane run that completed Pump Fees)

Preserves the tooling, coordination files, lane findings and harvested sources of the Claude `fees100` run
(2026-10-27/28). That run produced the merged Fees packets for ATA stable Rust (#312), the whole-ELF end state
(#317), CreateDonation (#385) and Crank (#392). Archive only: no new claim, and no maintained source or status change.

- `tools/` — build and measure loop:
  - `nbuild.sh`: native v1.44 build.
  - `cbuild.py`: canonical Linux container build. The vendored macro must sit at `/work/next637/vendor/used-public`,
    because Cargo hashes that relative path into every crate metadata hash and `ordered.ld` selects sections by those
    hashes. The script always relinks.
  - `measure.py`, `fndiff.py`, `dis.py`: window measurement and masked per-function diffs.
  - `integrate.sh`, `package_pr.py`, `packet_verify_template.py`, `pr.sh`: harvest → qualified packet → PR.
  - `relayout.py`, `elfinv.py`, `transplant.py`: the whole-ELF tools from #317.
  - `speed-recovered/`: fast scorer/farm/direct-rustc builder, reconstructed from transcripts and not re-validated.
  - `replay_tools.py`: the transcript replayer.
- `coordination/` — lane rules, the coordinator's directive log, the harvest index and the PR log.
- `findings/`, `findings-recovered/` — per-lane experiment logs. The `-recovered` ones were rebuilt from subagent
  transcripts after a reboot wiped `/private/tmp`.
- `harvest/` — every harvested source with its notes and patches:
  - `create-g01` (CreateDonation, #385);
  - `crank-brute-g01` (Crank, #392);
  - `crank-transfer-g01` and `crank-derive-g01`, independent alternative Crank sources reaching the same match.
- `review/` — scripts and result tables from re-running every Fees PR packet's verifier at its PR head before merging.
- `lanes/` — lane progress notes and leaderboards.

```sh
python3 -B research/claude-fees100-run-archive-20261028/verify.py
```
