# pumpfun-source

This repository has one goal: exact bytecode reconstruction of pump.fun's
on-chain Solana programs — Pump Main, PumpSwap/AMM, Fees, Mayhem and the
Donation Relay. Each program is rebuilt from source with a pinned toolchain
and scored instruction-by-instruction against the captured deployed binary.

**Scope.** Only the program bytecode publicly deployed on-chain is
reconstructed. This project does not reconstruct, capture or reproduce
pump.fun's website, apps, backend services, APIs, SDKs, branding or any other
off-chain material. Pull requests for frontend, backend, SDK or off-chain
capture work are closed without review. See [CONTRIBUTING.md](CONTRIBUTING.md).

Everything here serves building, scoring, verifying or differential-testing
those programs. There is no frontend, backend, SDK or off-chain service code.

- `programs/` — reconstructed program sources and per-program status
- `reconstruction/` — toolchain recipes, build harness and scoring
- `evidence/` — captured original binaries and analysis inputs
- `scripts/` — build, scoring, verification and differential-test tooling
- `crates/`, `binaries/` — supporting crates and experimental build outputs
- `research/` — retained investigation packets with their own verifiers
- `tests/` — unit tests for the tooling

**Verified checkpoint progress — 2026-10-31**

| Program | Matched windows | Matched % | Raw-equal bodies | Normalized only | Unmatched | Whole meaningful ELF equal |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Pump Main |1,034/1,035|99.90%|1,034|0|1|No|
| PumpSwap / AMM |785/785|100.0%|785|0|0|**Yes**|
| Fees |585/585|100.0%|585|0|0|**Yes**|
| Mayhem |441/441|100.0%|441|0|0|**Yes**|
| Donation Relay |492/492|100.0%|492|0|0|**Yes**|
| **Total** |**3,337/3,338**|**99.97%**|**3,337**|**0**|**1**|**4/5**|

Matched windows cover **5,185,728/5,213,128 code bytes (99.47%)**.
The latest fresh Pump Main identity build preserves all matched windows, with
no raw or normalized losses. Only `admin_cto::execute` remains unmatched
(27,400 bytes); its instruction-token similarity is **68.065%**, with **3,170
positional differences**. The previous checkpoint measured 68.005% and the same
3,170 positional differences. This adds two matched tokens; no new exact window
is claimed.
All **388 targeted signed synthetic admin-CTO cases** pass in a fresh comparison
of this candidate against the captured program. All 776 original/candidate
transaction signature vectors verify. This is bounded runtime evidence.
The new unlinked reference models add captured-program test coverage without
increasing compiled completion. Pump Main's meaningful ELF is not yet equal.

AMM, Fees, Mayhem and Donation Relay retain their exact meaningful-ELF
checkpoints. Separate bounded tests do not replace those identity receipts. See the
[latest scores, runtime coverage and limits](reconstruction/pump-main/checkpoints/completion-pass110-20261031/README.md),
[other-program checkpoint provenance](reconstruction/pump-main/checkpoints/completion-20261030/other-programs.json)
and [Fees Linux rebuild packet](research/fees-linux-fresh-rebuild-20261030/README.md).

Raw equality compares complete instruction bytes. Normalized windows mask
specified call/address operands and do not prove whole-program identity.
Whole meaningful ELF equality excludes documented zero loader-allocation padding.
These counts describe the selected maintained recipes; they are not a
percentage of engineering work completed.

The [reconstruction toolchain](reconstruction/README.md) rebuilds `programs/pump` and
scores it against the captured original in `evidence/original/`.

## License

Repository code and documentation are [MIT licensed](LICENSE). Third-party
sources and artifacts retain their original licenses and ownership.
