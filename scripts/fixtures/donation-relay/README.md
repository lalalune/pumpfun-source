# Relay differential ABI fixture

`idl.json` is restored byte for byte from repository commit
`0cbb40c702d662922573bf9382cd4e05d0e9aa6b`, path `repro/donation-relay/local-validation-proposal/inputs/idl.json`.
Git blob: `985636e92f481cb899b10fd8cbefcf79109dd850`. SHA-256: `b075f7b39b019630067e5f6a67015396ccbd66d282c7da048753660506472d6c`.

This historical on-chain ABI metadata constructs synthetic, locally signed
transactions for the relay differential. It is not a new capture or a proof of
program equivalence. No off-chain traffic or SDK input was recovered.

The historical AMM fixture is byte-identical to
`research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json` (SHA-256
`2e775505852caf55203c826ee08b9341aa275f52f59a933c4fb0740535ee316f`).
The two historical token dependency images are also byte-identical to the
current retained SPL Token and associated-token images. The runner uses those
canonical retained inputs instead of restoring duplicate binaries.
