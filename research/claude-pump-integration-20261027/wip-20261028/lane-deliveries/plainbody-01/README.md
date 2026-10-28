# plainbody-01 (base L06 899/165 -> 900/165, +0x49708)

## Change
`src/migrate.rs` `refund_pool_authority` (migrate v1): build the pool-authority signer seeds as a nested temporary
passed to an inlined closure that calls `crate::migrate::transfer_native(system_program, pool_authority, destination,
amount, seeds)` - the same form bodyloB-01 found for the migrate_v2 twin (0x56658). Line-neutral (2 lines replace 2 lines).

## Binary evidence
- Original 0x49708 (384 B) is called once, from migrate v1 execute 0x3fb70; it reads mint via `[r2+0x10] -> [+0x58]`,
  system_program `[r2+0x30]` and pool_authority `r2+0x50` = our `Migrate` layout (our 0x574c8 had identical
  offsets/control flow; only the seeds' stack-slot order differed: bump byte at -0x41 vs original -0x1, key at -0x68 vs -0x28).
- With the closure form the seeds temporaries are created before the closure's captures, giving the original order
  (key -0x28..-0x10, bump -0x1, slices -0x58/-0x48/-0x38, outer -0x68). Same calls in the same order (transfer_native).
