# C3-jupiter-swap lane notes

Base: `origin/swarm/w20-relay-scout` (dfcbfc6ae), 545 of 571, 776,384 B, 91.137%.

## invoke_jupiter (0x11668): exact

The metas closure is a struct literal, not `AccountMeta::new` / `new_readonly`:
`AccountMeta {pubkey:*a.key,is_signer:a.key==&authority,is_writable:a.is_writable}`.
Result: 546 of 571, 778,712 B, no losses.
