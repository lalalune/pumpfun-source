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

**Verified checkpoint progress**

| Program | Matched windows | Matched % | Raw-equal bodies | Normalized only | Unmatched | Whole meaningful ELF equal |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Pump Main |1,020/1,035|98.6%|188|832|15|No|
| PumpSwap / AMM |785/785|100.0%|785|0|0|**Yes**|
| Fees |585/585|100.0%|585|0|0|**Yes**|
| Mayhem |441/441|100.0%|441|0|0|**Yes**|
| Donation Relay |492/492|100.0%|492|0|0|**Yes**|
| **Total** |**3,323/3,338**|**99.6%**|**2,491**|**832**|**15**|**4/5**|

Matched windows cover **5,045,232/5,213,128 code bytes (96.8%)**.
Raw equality compares complete instruction bytes. Normalized windows mask
specified call/address operands and do not prove whole-program identity.
These counts describe the selected maintained recipes; they are not a
percentage of engineering work completed.

The [reconstruction toolchain](reconstruction/README.md) rebuilds `programs/pump` and
scores it against the captured original in `evidence/original/`.

## License

Repository code and documentation are [MIT licensed](LICENSE). Third-party
sources and artifacts retain their original licenses and ownership.
