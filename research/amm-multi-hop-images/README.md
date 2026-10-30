# Retained PumpSwap images for the multi-hop packets

The `research/amm-multi-hop-*` packets replay every case on three PumpSwap
images and bind each one by sha256 in `runtime/report.json.gz`:

| image | stripped sha256 | source |
|---|---|---|
| original | `6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7` | `evidence/original/pump_amm/deployed.so` |
| control | `7a300434dced61413bde10788594b427d5649563e0223efcf09e6b214aff7ad3` | `control.so.gz` |
| candidate | `d17a657baf5cc19736a924c41e75424604411ddbe9f6e72cddf41ab72a695007` | `candidate.so.gz` |

The packets originally read control and candidate from the author's
`~/workspace/slop-verify`. These two files are the stripped Linux v1.44
artifacts retained by the PRs that built them, copied byte-for-byte. Their git
blobs are unchanged:

- `control.so.gz` (blob `edca5724e6f766de6a10ff8b6661b9190f64f290`) is
  `research/amm-multi-hop-group-slice-recovery/artifacts/candidate.so.gz` from
  #424 (head `ae0c45690bdd12973b90503499f918e5e09fd46f`).
  `control-build-provenance.json` is that packet's `build-provenance.json`.
- `candidate.so.gz` (blob `517e074ca556ef5ef1e5a351e3149459365ecda0`) is
  `research/amm-transfer-fee-diagnostic-recovery/artifacts/candidate.so.gz`
  from #427 (head `4e15e3930a8e1ee6ae0c1101e50f409b8f4633c8`).
  `candidate-build-provenance.json` is that packet's `build-provenance.json`.
  It names the control image as its baseline.

Those packets are not in the current `main` history, but both PR heads remain
fetchable from GitHub, for example
`git fetch origin ae0c45690bdd12973b90503499f918e5e09fd46f`.

Every packet `verify.py` binds all three images to the report hashes, and
every `producer.py` loads them from here: it decompresses control and candidate
into a temporary file only for the VM. `test_packets.py` runs every packet
verifier with an empty `HOME`.

`verify.py` checks that each image decompresses to the stripped hash and size
in its provenance, and that the candidate's baseline is the control image.
This directory only retains the images; it makes no new build or equivalence
claim.
