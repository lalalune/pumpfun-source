# Fees original-binary Surfpool verification

## Result

| ID | Status | Signed transactions | Observed outcome |
|---|---|---:|---|
| L-07 | CONFIRMED | 2 | Empty normal and stable tier queries panic at `pump-fees-math/src/lib.rs:49:23`. |
| L-08 | CONFIRMED | 3 | Old authority rotates without the incoming signature; old authority is then rejected, new authority succeeds. |
| L-15 | CONFIRMED | 2 | Readonly extend funder succeeds; readonly social authority fails recipient-ATA funding with `PrivilegeEscalation`. |
| M-07 | CONFIRMED | 2 | Legacy-sized stable update succeeds and changes raw state, but reload/query still sees zero stable tiers and panics. |
| M-12 | CONFIRMED | 2 | Token-2022 quote donation creation succeeds; legacy-token crank fails `IncorrectProgramId` before Relay settlement. |

**Totals:** 5 confirmed, 0 blocked, 0 inconclusive; 11 normally signed transactions. All transaction signatures were verified by the shared harness with `sigVerify=true`. No off-chain data was used.

## Loaded binaries

- Surfpool: `1.6.1` (pinned `tools/surfpool`)
- Original Fees `evidence/original/pump_fees/deployed.so` SHA-256: `4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e`
- Donation Relay SHA-256: `367f07a62e3f74d358187d175cf3228848e81a56c781a9a75b9df7fed1268563`
- SPL Token SHA-256: `8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697`
- Token-2022 SHA-256: `15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d`
- Associated Token SHA-256: `6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d`

The complete JSON retains loaded-program hashes, verified signatures, transaction bytes, errors, logs, return data, simulations, and before/after account state.

## L-07 — empty fee-tier vectors

Fresh/legacy 2512-byte FeeConfig state was supplied with empty normal and stable vectors. Pump-pool selection was enabled so both queries reached tier selection.

- `4rDmdhVJGhzTf9BRFWYCxX5TAzDNQ5zETwTtUT3jbodWJ2fhE6WkouSPyoHYPnyjGR9tceMLuXK7cLdznDBJQVjs`: `get_fees` failed `ProgramFailedToComplete`; log: `index out of bounds: the len is 0 but the index is 0`.
- `5MRqs1198ioTLRLq66H4JxgmH2LfonePRVjZsmxdtcrG1twz2wt43DhE1ReiSqPsZ4zMocn8RXzr4wEBh51PS567`: USDC `get_fees_with_quote_mint` failed with the same panic.

Both return data fields were null. This confirms caller transaction failure on the tested empty states; it does not assert loss of funds.

## L-08 — one-step authority rotation

- `GSzcSE5C9JYFeD1iA1Ao5AKLKYn3M8VmYwJjGPzBmMYrAQM41SYQnipgUBcPF2xaPRe23u1mio6DXBQ5jt2uf1c`: old authority alone successfully set the new authority; committed global bytes at authority offset 9 changed to the incoming key.
- `277q8G4DBACGCZ85FtCCB2dRzvwoWhh8svds8HiuryEQ1ALD1WZ8ra9YJy9gz5YPVG7sDGWMVAtv6dC9FQ5Nopxs`: old authority's next administrative call failed custom error 6016 (`NotAuthorized`).
- `3nUKz7AzWx4dXWqHwUu2UsAXPERRDLC7ia7Fcuwabj5CQSed7Bb7xNs7ctXDYnvdjh9VuHvgKPTe7GvPMuas3Emi`: new authority's administrative call succeeded.

This confirms the one-step lockout mechanism under test-owned authorities. Permanence in a real deployment still depends on recovery through the actual upgrade authority.

## L-15 — readonly generated funding accounts

Both tests used a transaction fee payer distinct from the required funding signer.

- `3n8DdjyG3okHhf1YuVJFvi5doKxEscFtrhtmp5K7o4vogYpWaiQ2BaD6XUEvwDf7sNTNtcAG3k5qCUMFY6xiPwiB`: readonly `ExtendFeeConfig.user` succeeded. The user paid 11,031,600 lamports; FeeConfig lamports increased by the same amount. The distinct fee payer separately paid the 10,000-lamport transaction fee.
- `33jHCV8peBYQP4Rv6tvzz3B6fx4RFr4Nyiyh5s7eavaPdBGi22ybG3CkD2qofP1sHUDBtutotPWtKPdKUzuhKn62`: readonly `social_claim_authority` failed instruction 1 with `PrivilegeEscalation` when the new recipient ATA required funding. Log: `Bqqt1tFkrCw35zoLcqDXK4yAmo5bw725EZkgeMMy28qw's writable privilege escalated`. Recipient ATA remained absent; funding-authority lamports were unchanged.

Thus the metadata defect is confirmed on the actual ATA-creation branch, while the extension branch is accepted despite readonly metadata.

## M-07 — invisible stable update on legacy allocation

- `2MBPpTSDbbAkgsMb3A8RzcqV1AyUPx3bxAZBMrKwYV9HLCdyr59PsL1KgasszVG8U7WQEP9nAtBzYuoegpxwCrQw`: `update_stable_fee_config` on a 2512-byte account succeeded. Raw FeeConfig SHA-256 changed from `bfab48dd90fcf8002a905f7309779314fa8a65359c922f69b61aced695196ba0` to `c84c03f08eb9ec9d6806623578929df46e4955be087e49ec78e54036e50ceb33`.
- `5MRqs1198ioTLRLq66H4JxgmH2LfonePRVjZsmxdtcrG1twz2wt43DhE1ReiSqPsZ4zMocn8RXzr4wEBh51PS567`: subsequent USDC query panicked because the reloaded stable vector length was zero.

The successful write is therefore invisible through legacy decoding/query, exactly the tested layout mismatch.

## M-12 — Token-2022 quote donation crank

Original Fees, Donation Relay, SPL Token, Token-2022, and Associated Token binaries were loaded locally.

- `NwHLbuY8QnJQn5KLpF8fDECHqWWXvp2GLAA5kan2KwRjaZdo9jtD4iwFW2fsnZerjrZ5fyh19xrxRT5N9CKoPdR`: creator-authorized donation-PDA creation succeeded with the quote mint owned by Token-2022.
- `5czFzCsAamcCEBKCkNFkPjw9ZbuCHo1JqPHmbe1CgGWjgbrVXm9L1HsHPNz1eNnSbXGE2Fp9uAXKDwvsiT62rUiZ`: crank failed instruction 1 with `IncorrectProgramId`. Associated Token invoked legacy SPL Token for the Token-2022 mint; legacy Token logged `Error: IncorrectProgramId`, and the failure propagated through Associated Token and Fees. Relay settlement was not invoked.

## Reproduction

From the repository root:

```sh
uv run --with-requirements requirements.txt python reconstruction/verification/security-surfpool/fees.py
```

The command rewrites `results/fees.json`. This verification is limited to the listed synthetic states and signed transactions; it is not a live-deployment eligibility or whole-program security assessment.
