# AMM liquidity transfer authority parity

Base: `90300f9d2efe3ef014b116172251a41bfb104d78`. Observed 2026-10-31.

The recovered liquidity host rejected deposits from a token account delegated to the user, although the captured AMM and token programs accepted them. When the user was both owner and delegate, the host accepted an exhausted allowance and left successful transfers' allowance bytes unchanged. It also reported a mint or owner mismatch before an insufficient source balance.

The model now applies a matching delegate allowance before the owner fallback, decrements the allowance, and preserves the captured programs' distinct serialization when that allowance reaches zero: SPL Token retains the inactive delegate key; Token-2022 clears it. Insufficient source balance is checked before mint and authority mismatches. Existing same-account handling remains scoped by the model's documented limits.

The diagnostic compared **28 external cases**, finding **23 mismatches on the base host and zero after recompilation**. `results.json` records those individual outcomes and the three captured program hashes. The committed regression method uses **24 subcases**: 18 SPL Token/Token-2022 base-source authority cases, 3 fee-bearing quote-source allowance boundaries, and 3 insufficient-balance combinations. These are distinct counts; the 28 diagnostic cases are not 28 new unittest methods.

Validation used CPython 3.12.13, solders 0.27.1 and the isolated official Rust 1.99.1 compiler. Each host was compiled with `--edition=2021 -O -D warnings`. The captured suite checks errors, rolled-back state, committed full account bytes, events and token/self-CPI payloads.

```sh
python tests/test_pump_amm_liquidity_captured.py
python scripts/verify_evidence.py
python scripts/test_tooling.py
```

For the separate 28-case diagnostic, compile `liquidity_host.rs` from the base
and fixed checkouts, then run `python research/runtime-liquidity-transfer-semantics-20261031/probe.py HOST`
with each executable. `results.json` retains both native executable digests and
the compiler digest. The new regression is also collected by the existing
`contract-tests` CI job.

This file is an unlinked recovered host model: the SBF crate's liquidity
implementation is under `src/instructions/liquidity/`. No fresh SBF build or
window-score result is claimed for this host-only correction.

Results: 6 captured-suite methods passed (124 existing fixed cases, 40 existing random cases and 24 new regression subcases); all 9 retained captures passed identity verification; all 242 tooling tests passed. These observations concern offline reconstruction behavior only. They do not establish byte identity or change a deployed program.

An independent review passed 15 further delegate, owner-fallback, withdrawal,
and second-transfer rollback cases. It also found a preexisting synthetic
boundary outside this correction: with both source and destination balances at
`u64::MAX`, an owner-authorized legacy SPL Token deposit succeeded in the
captured program and wrapped the destination balance, while both the base and
fixed hosts returned token error 14. The equivalent Token-2022 case returned
14 and rolled back in the captured program and both hosts. These artificially
inconsistent token totals do not establish a reachable on-chain state. The
legacy-token boundary remains unmodelled; the delegated-transfer results are
finite evidence and do not establish complete liquidity parity.
