# Synthetic Mayhem CPI test inputs

These two immutable inputs were recovered from commit
`cfe9d4c9d3aae10209154c926864d3ce82abd9cf`, directory
`repro/pump/mayhem-synthetic/`.

- `account-snapshot.json.gz`: SHA-256 `1467baf77192d9af2db092b0e9ef649b5b12b9a938bbdfd29c9d456b912ae86b` (2,181 bytes).
- `synthetic-caller.so`: SHA-256 `9578ec8fc94ce3d00f79177dfb14da8c75542c4eb8a8399fc33b5f9cef9a0f87` (26,640 bytes).

The caller is a test-only program deployed at the Mayhem address inside LiteSVM.
It signs its own PDA and invokes Pump. This is not a captured deployed Mayhem
caller and does not establish a production route. The tests use the captured
Pump program as a diagnostic candidate; they do not claim a reconstructed or
independently built candidate. Historical candidate binaries and result/build
receipts are intentionally not included.

Token-2022's snapshot contains only its upgradeable program account. The runner
supplies the matching captured ProgramData from
`evidence/dependencies/spl_token_2022/` before applying that account.
