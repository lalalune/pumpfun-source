# Migration attribution: the Raydium era and the 2025-03-20 PumpSwap cutover

Question: where does a completed Pump bonding curve's liquidity go on
`migrate`, and where did it go before PumpSwap existed? The retained docs did
not record the historical Raydium connection or the cutover. This note binds
the answer to captured bytes, recovered source lines, the retained IDL
dispatch map and two on-chain anchor transactions. It changes no handler
disposition, completion count or whole-binary comparison, and it is not a
security statement. The machine-readable records are in
[migration-raydium-cutover.json](migration-raydium-cutover.json).

## Current path: `migrate` goes to PumpSwap, not Raydium

The captures bound here are the same ones tabulated in
[scope and hashes](SCOPE.md) and recorded in
`evidence/original/pump/capture.json` and
`evidence/original/pump_amm/capture.json`:

| Program | Last deployment slot | Payload SHA-256 |
| --- | ---: | --- |
| pump `6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P` | 458921440 | `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d` |
| pump_amm `pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA` | 458921517 | `6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7` |

The recovered `Migrate` account list (`programs/pump/src/migrate.rs`,
`Accounts` struct) contains **no Raydium account**. Its AMM account is
`pump_amm: Program<Amm>` (migrate.rs:14), the pool is the PumpSwap PDA with
seeds `["pool", 0u16, pool_authority, mint, wsol_mint]`, the pool authority
is the PDA `["pool-authority", mint]`, the LP mint is
`["pool_lp_mint", pool]`, and the AMM configuration and event authority are
the `["global_config"]` and `["__event_authority"]` PDAs under the Pump AMM
program.

Execution in the same recovered source:

- The migration fee is read from state, not embedded in code:
  `fee = a.global.pool_migration_fee` (migrate.rs:48).
- First CPI, to Pump AMM: instruction data begins with bytes
  `[233, 146, 209, 142, 207, 104, 64, 188]` = `e992d18ecf6840bc`,
  followed by the pool index, base/quote amounts, creator and curve flags
  (migrate.rs:62). The retained dispatch map binds that discriminator to
  Pump AMM `create_pool`
  (`evidence/dispatch-map.json`, `/pump_amm/instructions/create_pool/discriminator`).
- Second CPI, to Pump AMM, only for non-Mayhem curves: data is exactly
  `[140, 233, 33, 94, 132, 90, 194, 143]` = `8ce9215e845a2c8f`, with
  `remaining_accounts[0]` and `[1]` admitted as the boost and vault
  accounts (migrate.rs:64). This discriminator does not appear in the
  retained dispatch map, so no IDL name is asserted for it here.
- The LP position is then burned in full: a Token-2022 burn (instruction
  byte `8`) of the pool authority's entire LP balance, followed by closing
  the account (migrate.rs:66).
- `CompletePumpAmmMigrationEvent` is emitted with data prefix
  `[228, 69, 165, 46, 81, 203, 154, 29]` = `e445a52e51cb9a1d`
  (migrate.rs:70; struct at migrate.rs:72). The event carries
  `pool_migration_fee`, so the charged fee is part of the emitted record.

The only occurrence of the string `raydium` in `programs/` or `docs/` at
this revision is the legacy error text at `programs/pump/src/lib.rs:225`:

> "The bonding curve has completed and liquidity migrated to raydium."
> (`BondingCurveComplete`, lib.rs:226)

So in the currently deployed and captured program, the Raydium connection
survives only as an error string. The live destination is PumpSwap.

## The Raydium era: withdraw, then off-chain `initialize2`

Before the cutover, graduation was a two-step, operator-driven flow:

1. The privileged `Global.withdraw_authority` withdrew the completed
   curve's liquidity. The recovered `Global` state carries
   `withdraw_authority`, `enable_migrate` (lib.rs:190) and the
   `DisabledWithdraw` error (lib.rs:250); `set_params` sets both
   `enable_migrate` and `pool_migration_fee` (lib.rs:94). Withdraw is the
   pre-migrate path and is disabled once migration is enabled.
2. An off-chain flow created the pool on **Raydium AMM v4**
   (`675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8`, with its Serum/OpenBook
   market accounts) by calling `initialize2`, and the LP tokens were
   burned.

The direct on-chain evidence for step 2 is the last Raydium graduation
anchor below: its fee payer is the migration authority
`39azUYFWPz3VHgKCf3VChUwbpURdCHRxjWVowf5jUJjg` itself, and the
transaction's AMM v4 instruction is `initialize2`. Pool creation was not a
CPI from the Pump program; it was the authority's own transaction. The
era's account list is from the public IDL and history, not from a byte
capture (see Limits).

## Cutover anchors

Both transactions were fetched with `getTransaction` over read-only
mainnet RPC on 2026-10-27; signature, slot, block time and log markers are
as recorded there. RPC records are evidence of the same class as the
capture metadata in [SCOPE.md](SCOPE.md), not independent consensus proofs.

| Event | Signature | Slot | Block time (UTC) | Marker |
| --- | --- | ---: | --- | --- |
| Last Raydium graduation | `51BEbbzn35GDCLHW23f5sEahNmRsGN83YJAzG3wvCEPNSpqeT2MuWY62ayhr1MdFGeSEJmaik4kTpv25rDFFmY44` | 328032881 | 1742486600 (2025-03-20 16:03:20) | Fee payer is the migration authority `39azUYFW…`; log shows `initialize2: InitializeInstruction2` on Raydium AMM v4 |
| First PumpSwap migrate | `5S6kofZs81D26cm6qDAYcZJR16415vmMj1bMwUJPQP5tnTVAbaPFnKjwpAWdAVed8hHosCkrz6e76FwDwaqNTEGj` | 328038776 | 1742488955 (2025-03-20 16:42:35) | Log shows `Instruction: Migrate` on the Pump program; fee payer is an ordinary user |

Between them sits the off-chain announcement: pump.fun post
`1902762309950292010`, 2025-03-20 16:41:00 UTC, stating that completed
curves would "migrate directly to PumpSwap — instant, 0 migration fees
(down from 6 SOL)". The first PumpSwap migrate lands 95 seconds after the
announcement; the last Raydium graduation precedes it by about 38 minutes.
The announcement is off-chain corroboration, not program evidence.

## `pool_migration_fee` history

The migration fee is a `Global` configuration field
(`pool_migration_fee: u64`, lib.rs:191), written by `set_params`
(lib.rs:94), read by `migrate` (migrate.rs:48) and emitted in the
migration event. It is not an ELF constant, so its history is a history of
configuration values:

- Raydium era: 6 SOL, per the cutover announcement's "down from 6 SOL".
- Current: a read-only RPC read of the `Global` account
  `4wTV1YmiEkRvAtNtsSGPtUrqRYQMe5SKy2uB4Jjaxnjf` on 2026-10-27 returned
  the u64 little-endian at offset 146 as **15,000,001 lamports**, observed
  at slot 462126299. Offset 146 is the field's position in the recovered
  `Global` layout (8-byte discriminator, then the fields in declaration
  order through `enable_migrate`, lib.rs:180–191). The value is reported
  as read; it is not a round 0.015 SOL.

## Limits

- The REA captures behind the current-path tracing fetch the **current**
  ProgramData only. No Raydium-era ELF is captured in this repository at
  this revision (`evidence/pre-pumpswap/` is absent), so the pre-cutover
  account list rests on the public IDL/history and the anchor transaction,
  not on byte-level program evidence. A byte-level Raydium-era capture
  would need an archival source for the program account at a
  pre-2025-03-20 slot.
- The current path was traced with an external sBPF analyzer (REA,
  `analyze-solana-program`; 215,873 instructions disassembled for Pump,
  55 handler candidates for Pump AMM, research session 2026-10-27). The
  load-bearing bindings above are the in-repository ones: recovered source
  lines, the dispatch-map discriminator entry and the capture hashes,
  which agree with [SCOPE.md](SCOPE.md).
- The second CPI's discriminator (`8ce9215e845a2c8f`) is described by its
  data prefix and account shape only; the retained IDL dispatch map does
  not name it.
- The 6 SOL era fee is known from the announcement text, not from a
  captured historical `Global` account.
- Nothing here establishes source equivalence, complete migration
  behavior for every curve mode (the Mayhem branch skips the second CPI),
  or any security property of either migration path.
