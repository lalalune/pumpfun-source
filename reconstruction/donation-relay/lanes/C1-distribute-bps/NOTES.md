# w20-relay-C1-distribute-bps notes

Base: origin/swarm/w20-relay-scout dfcbfc6ae (545/571, 776,384 B).

## Helper signatures (C2 shares these)

In `settlement_handlers.rs`, all `#[inline(never)]`:

- 0x18478 `distribute_after_prechecks(accounts:&DistributeAfterJustSwappingV1)->Result<()>`, lines 88, 93, 98
- 0x1a6d8 `distribute_after_finish(accounts:&mut DistributeAfterJustSwappingV1,signer_seeds:&[&[&[u8]];1])->Result<()>`
- 0x1b090 `distribute_non_swap_prechecks(accounts:&DistributeNonSwapOutputMintV1)->Result<()>`, lines 80, 85, 91, 96
- 0x1d2d0 `distribute_non_swap_finish(accounts:&mut DistributeNonSwapOutputMintV1,signer_seeds:&[&[&[u8]];1])->Result<()>`

In `tools/distribution/shared.rs`:

- 0x24578 `distribute(ctx,args)`: `ctx` stays whole so `drop_in_place<DistributionContext>` (0x8eb0) is a call at the single exit.
- 0x25f00 `transfer_shares(ctx:&DistributionContext,rows:Zip<Iter<Share>,Iter<u64>>,decimals:u8,expected_program:Pubkey,seeds:&[&[&[u8]]])->Result<()>`, lines 191, 196, 201.
