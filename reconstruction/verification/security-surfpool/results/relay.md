# Donation Relay Surfpool security results

**Target:** retained `evidence/dependencies/donation_relay/deployed.so`  
**Runner:** pinned Surfpool 1.6.1, offline mode, using the shared RPC harness and original Token/Token-2022/ATA dependencies.  
**Coverage:** 8 assigned IDs; all 8 executed and met their expected assertions.

## Authority and substitution boundaries

- Donor and attacker actions were genuinely signed and committed. This includes the M-09 donations, C-01 ATA precreation, C-02 delegate transfer, H-07 pause, L-12 unsolicited credits, and all donation setup.
- The production relayer key is unavailable. Every privileged Relay call is explicitly marked `unsigned_simulation_sigVerify_false` in the JSON. These runs establish **post-authorization behavior only**, not an authorization bypass, committed privileged state, or a full signature-verified privileged exploit.
- Real Jupiter is absent. M-13, C-03, and L-11 load an explicitly labeled Token-CPI test stub at the fixed Jupiter address. The stub debits a chosen input and mints a chosen output through the retained Token programs. It isolates Relay pre/post-CPI checks and is **not end-to-end Jupiter proof**.
- Swap/post-close fixtures replay the simulated close into local synthetic state before the next simulation. Accounts and mint configurations are synthetic; no current production vulnerable mint, live loss, or production configuration is asserted.
- Surfpool simulations do not commit state, so their recorded state deltas are empty. Signed failures may still charge the fee payer; M-09's overflow changed only the fee-payer account.

## Loaded hashes

`file_sha256` hashes the retained file. `loaded_elf_sha256` hashes the exact ELF image loaded into Surfpool after the shared harness removes any trailing allocation padding.

| Program | File SHA-256 | Loaded ELF SHA-256 |
|---|---|---|
| Donation Relay | `367f07a62e3f74d358187d175cf3228848e81a56c781a9a75b9df7fed1268563` | `56d81ec64a0ba070d3d23f3c1547b31d659e85716dfa2198ec4b0ce6cd355333` |
| SPL Token | `8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697` | `8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697` |
| SPL Token-2022 | `15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d` | `3dde54d202caa2d10514fd58a154df5f26f07643f9f5fd0402ff08084f0cb954` |
| Associated Token | `6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d` | `6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d` |
| Explicit test stub | `219ca86b08a9ce84ea33948d5a95250c20ee114414b1b0cd5371df61fdd591ae` | `219ca86b08a9ce84ea33948d5a95250c20ee114414b1b0cd5371df61fdd591ae` |

## Findings

| ID | Outcome | Actual Surfpool evidence | Exact limitations / blockers |
|---|---|---|---|
| **L-11** | Confirmed defense-in-depth gap; Jupiter bypass unproven | With the explicit stub, zero output fails with Relay `Custom(6023)` (`OutputAmountMustBeGreaterThanZero`); one-unit output succeeds. No independent Relay output floor was observed. | Privileged close/swap are post-authorization simulations. Stub substitution only; no real Jupiter minimum-output bypass or end-to-end route claim. |
| **L-12** | Confirmed post-authorization | Signed 111-unit unsolicited debouncer credit is excluded from the recorded close total. A separate signed 222-unit distribution credit is accepted; simulated non-swap settlement succeeds, distributing the recorded 1,000,000 and burning the 222-unit residual. | Close/distribution are simulations; post-close state is explicitly replayed locally. Tests unsolicited surplus only, not recorded-principal loss. |
| **M-09** | Confirmed with signed committed transactions | Signed 10^16 donation with 125 bps tip succeeds. Signed 10^18 donation fails with `Custom(6008)` (`ArithmeticOverflow`); only the fee-payer account changes, so donation state rolls back. | Demonstrates atomic donation denial, not existing-fund loss. |
| **M-13** | Confirmed post-authorization with stub | Signed whitelisted 10%-fee donation records net 900,000. Simulated close transfers gross 900,000, yielding 810,000. The stub's exact 900,000-input transfer then fails with Token-2022 `Custom(1)` and `Error: insufficient funds`. | Real Jupiter absent. Post-close state is replayed. Withheld-fee cleanup after a successful swap is not reached in this shortfall case. |
| **H-07** | Confirmed post-authorization | Signed non-whitelisted pausable Token-2022 donation succeeds. The independent pause authority signs and commits pause. Simulated authorized close then fails with Token-2022 `Custom(67)` and no state mutation. | Requires a funded accepted mint with an independently controlled pause authority; no current production mint asserted. Close is simulation only. |
| **C-01** | Confirmed post-authorization | Signed donation and signed outsider precreation of the deterministic distribution ATA both commit. Simulated authorized close fails with `IllegalOwner`; ATA logs `Provided owner is not allowed`, and state remains unchanged. | Close is simulation only. No authorization bypass or committed privileged freeze claimed. |
| **C-02** | Confirmed conditional behavior with signed committed transactions | Signed donation into a whitelisted Token-2022 mint with PermanentDelegate succeeds. The independent delegate then signs and commits a 1,000,000-unit transfer from the debouncer ATA to the attacker ATA. | Requires relayer-approved whitelist state and an independently controlled permanent delegate. No current production vulnerable funded mint asserted. |
| **C-03** | Confirmed post-authorization with stub | Signed WSOL donation and simulated close succeed. In the replayed post-close state, the stub spends exactly 1,000,000 and leaves 777 WSOL; Relay's residual native Burn fails with SPL Token `Custom(10)`. | Real Jupiter absent; this proves Relay pre/post-CPI residual behavior only. Post-close state is replayed because simulations cannot commit. |

## Evidence file

`relay.json` contains the complete per-ID rows, loaded-program hashes, transaction signatures, signature modes, errors, logs, before/after account hashes, and state deltas. The runner is `../relay.py`; the explicit stub source and build receipt are under `relay-work/stub/`.

Reproduce from the repository root:

```bash
uv run --with-requirements requirements.txt python reconstruction/verification/security-surfpool/relay.py
```
