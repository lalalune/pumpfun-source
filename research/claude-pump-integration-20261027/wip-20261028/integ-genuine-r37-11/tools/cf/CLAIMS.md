# coordfiles lane: intended cross-file moves (round 2, base i1)

Scope: Source sites whose ORIGINAL path is not programs/pump/src/lib.rs. Lane "coordlib" owns lib.rs-origin sites.
Moves that touch lib.rs (code leaving lib.rs) are listed first so coordlib can account for the removed lines.

## Code leaving lib.rs (coordlib: please do not position these items inside lib.rs)
- `InitUserVolume` #[derive(Accounts)] struct (ours lib.rs ~461) -> token_incentives/init_user_volume_accumulator.rs
  (orig window 0xfdf20 try_accounts site init_user_volume_accumulator.rs:8).
- (planned, phase 3) `set_reserved_fee_recipients` handler body -> set_reserved_fee_recipients.rs
  (orig 0x6fef8 sites set_reserved_fee_recipients.rs:40 (6027) / :60 (6028)); and the 6061 check
  (orig 0x722d0 set_reserved_fee_recipients.rs:121) - to be confirmed before moving.

## Moves between non-lib files (no lib.rs impact)
- nested_create.rs module -> inline `mod` / items in create_v2.rs (orig create_v2.rs:345..473, closure 0x19cc0 at :412);
  quote helpers used by it -> pump_quote.rs (orig pump_quote.rs:61..415), constant product -> util/constant_product.rs (later phase).
- distribution.rs execute/execute_v2/get_*_amounts -> creator/distribute_creator_fees.rs + creator/distribute_creator_fee_v2.rs
  (later phase; SharingConfig impl stays for coordlib: orig lib.rs:84).
- util/fee.rs: checked_ceil_div before fee (orig :15-19 then :34) (same file reorder).
- trade_v3.rs: `add` after validate_trade (orig :149 then :390) (same file reorder).
