# coordlib lane: intended moves (round 2, base i1)

Scope: Source sites whose ORIGINAL path is programs/pump/src/lib.rs (72 sites, 45 windows).
Lane "coordfiles" owns all other original files. Site map: SC/shared/sitemap-lib.json.

## Code coming INTO lib.rs (coordfiles: please do not line-position these items in their current files)
- global_init.rs: `Initialize` #[derive(Accounts)] struct            -> lib.rs (orig try_accounts init site lib.rs:2778, window 0x164e40)
- create.rs:      `Create` #[event_cpi] #[derive(Accounts)] struct    -> lib.rs (orig lib.rs:2811, windows 0x16a3e0, 0x16bdf0)
- create.rs:      `execute` body (CreatorShouldNotBeZero)              -> lib.rs `create` handler in #[program] (orig lib.rs:334, 0x138b20)
- buy.rs:         `LegacyBuy` #[derive(Accounts)] struct               -> lib.rs (orig lib.rs:2871, window 0x172110)
- set_params.rs:  `execute` body                                       -> lib.rs `set_params` handler (orig lib.rs:222..278, 0x1367c0;
                  Truncation closure orig lib.rs:268, 0x137db8). NOTE: the fee-recipient loop at the top of that body
                  (6027/6028/2005/6029) belongs to the original fee_recipient.rs helper 0x3e550 (fee_recipient.rs:47/60/78) -
                  coordfiles may factor it out of lib.rs later; coordlib will not position those 4 sites.
- trade_types.rs: `reserved_bonding_curve_fees`                        -> lib.rs (orig lib.rs:2562, window 0xa2188)
- distribution.rs: SharingConfig `AccountDeserialize` impl            -> expanded at lib.rs `declare_program!(pump_fees)` line 84
                  (orig 0x115e70, declare_program-generated in the original). SharingConfig type itself stays in distribution.rs.
- (later, if attempted) buy.rs non-exact `buy` path -> lib.rs `buy` handler (orig 608..747), sell.rs legacy sell -> lib.rs `sell`
  handler (orig 968..1037). Will be announced here before doing it.

## Items staying in lib.rs that coordlib positions
#[program] (orig 90), toggles (114/121/149), Global #[account] (1815), impl Global methods (1870..1986),
declare_program!(pump_amm)/(pump_fees) moved to the top (orig 83/84).

## Acknowledged from coordfiles CLAIMS
- InitUserVolume, set_reserved_fee_recipients body, update_buyback_config 6061 check, collect_creator_fee body leave lib.rs:
  coordlib's layout.py does not pin or position them (it only anchors lib.rs-origin sites).

## Round-2 additions (coordlib-02, base i1c) - small edits in other lanes' files (line counts unchanged)
- buy_v2.rs:68-69, sell_v2.rs:60, trade_v3.rs (3x `if is_sol{..}` + role==2 check), buy.rs (legacy), sell.rs (legacy):
  inline `require_keys_neq!(key, default, BuybackFeeRecipientMissing); require!(contains, ..NotAuthorized)` replaced by
  `global.validate_buyback_fee_recipient(key)?` (new impl Global method in lib.rs, orig 0x98438 lib.rs:1879/1884; the
  original has no other 6062/6057 sites except sell.rs:145's index check). Legacy sell.rs gains the neq check (orig does it).
  multi_hop_curve_swap.rs:184-185 NOT changed (orig multi-hop 0x5b3b0 does not call 0x98438).
- distribution.rs: SharingConfig AccountDeserialize impl wrapped in #[macro_export] macro, expanded on lib.rs:84.
- migration_native_payments.rs: boost_enabled reads crate::pump_amm::accounts::GlobalConfig (orig 0x524f0 -> 0x1091b0).
- idls/pump_amm.json: GlobalConfig without creator_fee_configurable / max_configurable_creator_fee_bps (orig layout).
