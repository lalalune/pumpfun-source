# pumpfun-source

pump.fun on-chain Solana program source and validation tooling, released to the community for educational use.

The project covers Pump Main, PumpSwap/AMM, Fees, Mayhem and Donation Relay. It does not include pump.fun's website, apps, backend services, APIs or other off-chain material.

**Contribution focus: complete byte-for-byte reconstruction.** The sole objective for agents and contributors is to reverse engineer the on-chain code and recover source that rebuilds the target binaries byte for byte. All work must hillclimb toward completion by resolving remaining byte differences and preserving existing matches. Only PRs and submissions that demonstrate progress toward this goal will be accepted.

Tooling, build infrastructure and surrounding architecture may be changed only when a concrete blocker prevents reverse-engineering progress. Keep such changes to the smallest necessary fix and provide reproducible evidence of the blocker and the reconstruction progress enabled by removing it.

Window dressing, cosmetic cleanup, speculative refactoring, documentation churn and other inconsequential PRs and submissions will be closed. See [CONTRIBUTING.md](CONTRIBUTING.md) for the acceptance and evidence requirements and [AGENTS.md](AGENTS.md) for agent instructions.

- `programs/` — program source and per-program status
- `reconstruction/` — pinned toolchains, build harness and validation
- `scripts/` — build, verification and test tooling
- `tests/` — tests for the tooling

**Verified checkpoint progress — 2026-10-30**

| Program | Matched windows | Matched % | Raw-equal bodies | Normalized only | Unmatched | Whole meaningful ELF equal |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Pump Main |1,033/1,035|99.81%|1,033|0|2|No|
| PumpSwap / AMM |785/785|100.0%|785|0|0|**Yes**|
| Fees |585/585|100.0%|585|0|0|**Yes**|
| Mayhem |441/441|100.0%|441|0|0|**Yes**|
| Donation Relay |492/492|100.0%|492|0|0|**Yes**|
| **Total** |**3,336/3,338**|**99.94%**|**3,336**|**0**|**2**|**4/5**|

Matched windows cover **5,167,144/5,213,128 code bytes (99.12%)**.

Raw equality compares complete instruction bytes. Normalized windows mask specified call/address operands and do not prove whole-program identity. Whole meaningful ELF equality excludes documented zero loader-allocation padding.

See the [validation documentation](reconstruction/README.md) and [contribution guide](CONTRIBUTING.md) for build and test instructions.

## License

Repository code and documentation are [MIT licensed](LICENSE). Third-party sources and artifacts retain their original licenses and ownership.
