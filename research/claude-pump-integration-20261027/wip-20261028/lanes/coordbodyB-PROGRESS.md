# coordbodyB lane PROGRESS (base L06: 899 normalized / 165 raw, identity recipe)

Targets: W/targets/r4-coordbodyB.json (24 windows >= 0x80000 with Source sites, body differs on layout base).
Lane src: W/lanes/coordbodyB/src (copy of W/base/current/pump = L06). Experiments: W/lanes/coordbodyB/exp/<name>.

## Experiments
- b00: unchanged L06 rebuild -> sha 7bc1563b4965... 899/165, gains=[] losses=[] (harness reproduces base).
- e01 (0x94e28/0x95360): native Fee::calculate_fee/calculate_pre_fee_amount take self by value -> binary unchanged in callers (LLVM still forwards the Option payload pointer; original copies the 24-byte Fee to a stack temp first). 899, no gain.
- e02 (0x89b48/0x89ec8): added util/fee.rs `calculate_fee_tier`(first-threshold gate + reverse find) and `get_fees` (quote-mint dispatch:
  default/WSOL/QUOTE_2 -> fee_tiers, USDC -> stable (len>4072 else empty), else exotic/flat; creator override; fee() on protocol+creator);
  v3 buy handler now computes fees via get_fees(&global,curve,&fee_config.0,config_len,cap,quote). -> 900, gain 0x89b48 (calculate_fee_tier,
  fee.rs:162), no losses. DELIVERED coordbodyB-01.
- e03 (split get_fees -> inner get_fee_basis_points with require), e04 (tier-slice-then-call), e05 (negated SOL condition): all 900, same
  single gain 0x89b48. get_fees body (0x89ec8) ratio improved 0.43->0.527 but not matched yet: original does 4 sequential memcmp
  (default,WSOL,QUOTE_2,USDC) inline then calls calculate_fee_tier; arg/reg allocation (orig r7=fee_config,r9=len,r8=&quote_mint) and the
  USDC/exotic block ordering still differ. coordbodyB-01 promotes e05.
- e06 (`let fee=*fee; match fee`), e07 (`Fee::calculate_fee(&{fee},..)` block temp): both identical SHA to coordbodyB-01 (f534182b...).
  0x94e28/0x95360 (transfer_fee_recovered::calculate_fee/pre_fee_amount, ratio 0.85): the ONLY diff is the original UNCONDITIONALLY
  copies the 3-word Fee payload to a fresh stack slot before the tag branch, then passes &copy to Fee::calculate_fee(&self); our build
  aliases the incoming Option payload in place (add64 r2,0x8) and elides the copy. self-by-value (e01), local copy, block-temp all elided
  by LLVM (Fee only read). Not source-controllable (copy-elision artifact, like bodyloA StackSlotColoring). PARKED for integrator/toolchain.
- 0x84970/0x84b78/0x857a8 (trade_v3.rs:721/767/997) and 0x14eec8 (lib.rs:679): noncoord_slots=0 -> body already byte-identical to a sibling
  closure; only the Source {line,filename-len} differ (our nearest emits lib.rs len=24 / line 666 etc. vs trade_v3.rs len=29 / 721). These are
  the v3 trade::buy require! sites that land on padded lines in our layout. PURE COORDINATE: the integrator must place the v3 buy require sites
  at trade_v3.rs 721/767/997 and lib.rs 679 (needs the v3 buy body laid out; see big-handler work below). No body fix in this lane.
- e08 (inline positive get_fees) == e02 SHA (5ad659eb); e04/e05 split (0.52) beat inline (0.43) but 0x89ec8 blocked by a stable allocator
  tie-break: original keeps fee_config in r7 / len in r9; every source form we build gets fee_config->r9, len->r7 (first instruction
  `mov r9,r4` vs orig `mov r7,r4`). Same ops, swapped regs -> propagates through the whole body. Not source-controllable (like the fee copy).
  get_fees DOES sit at the correct site fee.rs:183 and calls calculate_fee_tier (0x89b48, matched), so a future reg-alloc alignment converts
  directly. Lane stays at coordbodyB-01.
