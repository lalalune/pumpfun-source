# Scope and deployment evidence

Network: Solana mainnet-beta, genesis hash `5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d`.
Captures use finalized read-only RPC at `https://api.mainnet-beta.solana.com`.
Each program is captured independently; this is not an atomic multi-program snapshot.
The loader pointer and metadata are rechecked after each payload fetch to reject an
intervening upgrade. Account hashes are RPC evidence, not independent consensus proofs.

## Official program scope

- **pump**: `6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P`. [Official address source](https://github.com/pump-fun/pump-public-docs/blob/639b87fb45c3adeffa6f7c4a1bf0cb85e392bf22/docs/PUMP_PROGRAM_README.md).
- **pump_amm**: `pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA`. [Official address source](https://github.com/pump-fun/pump-public-docs/blob/639b87fb45c3adeffa6f7c4a1bf0cb85e392bf22/docs/PUMP_SWAP_README.md).
- **pump_fees**: `pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ`. [Official address source](https://github.com/pump-fun/pump-public-docs/blob/639b87fb45c3adeffa6f7c4a1bf0cb85e392bf22/idl/pump_fees.json).
- **mayhem**: `MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e`. [Official address source](https://github.com/pump-fun/pump-public-docs/blob/639b87fb45c3adeffa6f7c4a1bf0cb85e392bf22/docs/instructions/COIN_CREATION.md).

Pump, PumpSwap and Pump Fees are first-party protocol programs. Mayhem is included
as the separately deployed Pump-integrated Mayhem program explicitly required in
the official creation interface. The documentation establishes its integration;
matching legal ownership of upgrade keys is not inferred from addresses.

| Program | Last deployment slot | Full payload bytes | SHA-256 |
| --- | ---: | ---: | --- |
| pump | 458921440 | 10485715 | `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d` |
| pump_amm | 458921517 | 10485715 | `6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7` |
| pump_fees | 456132171 | 948944 | `4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e` |
| mayhem | 452655053 | 777408 | `a87fa9f866272514e6acb852b668c4a08aeb173d56c883039991d114d1199bdb` |

| Program | ELF extent | Zero allocation suffix |
| --- | ---: | ---: |
| pump | 1934800 | 8550915 |
| pump_amm | 1268504 | 9217211 |
| pump_fees | 873256 | 75688 |
| mayhem | 775416 | 1992 |

The full ProgramData account, including its 45-byte loader header, is preserved
alongside the exact payload and 36-byte Program account. Per-capture JSON records
ProgramData address, upgrade authority, observation slots and capture timestamp.
The last deployment slot is loader metadata, not the observation slot.

## Separately deployed dependencies

SPL Token, Token-2022 and Associated Token are external SPL infrastructure. Token
Metadata is external Metaplex infrastructure. The donation relay is referenced by
the Pump Fees IDL; its organizational ownership is unresolved, so it is not labeled
first-party. These captures preserve dependency evidence; their source reconstruction
and security audit are outside the four-program target.

| Dependency | Address | Last deployment slot | Payload SHA-256 |
| --- | --- | ---: | --- |
| spl_token | `TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA` | 419472000 | `8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697` |
| spl_token_2022 | `TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb` | 460497271 | `15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d` |
| associated_token | `ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL` | Unavailable (legacy loader) | `6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d` |
| token_metadata | `metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s` | 380725176 | `31f0a627dba051a938de650464e55cc5397a4be0fd496929c1f9cf02fe5e9011` |
| donation_relay | `RLAYHr9TRFcKB2ubYQhspcnXiaGpaVzNQvHytt47RZu` | 415422992 | `367f07a62e3f74d358187d175cf3228848e81a56c781a9a75b9df7fed1268563` |

Associated Token uses the immutable legacy loader and stores its ELF directly in
the Program account, so no ProgramData account or last-deploy slot is available.
System Program is a native runtime dependency. Rent is a sysvar and wrapped SOL is
a mint, not separate executable programs. Fixed administrator addresses are wallets,
not inferred programs. Dynamic token-program arguments are not automatically treated
as first-party dependencies. The IDL account/address inventory is preserved in
`evidence/interface-inventory.json`.

The official transfer-hook-authority repository declares
`333UA891CYPpAJAthphPT3hg1EkUBLhNFoP9HoWW3nug` in a localnet configuration. That ID is
not a fixed dependency in these IDLs; no mainnet deployment or essential dependency
relationship is asserted for it. Broader website services, PUMP-token staking,
vesting and other unrelated deployments are not part of this scope.
