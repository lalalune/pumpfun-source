# crank-transfer findings (window 147944 crank_donation_fee_pda)
Lane: RR/lanes/crank-transfer. Mechanism transfer from create-g01 (cold-callsite inliner, IR block order, SROA tuple
slots, named slice locals, helper parameter order, explicit returns inside borrow scopes).

- 20:58 lane set up; baseline w584 native reproduced (sha 45d10d76).
- 21:00 crank-b's v08 near-miss RECONSTRUCTED on w584 from its findings text (source trees were lost in the reboot):
  lanes/crank-transfer/specs/v07.py + v08.py (tree v/v08/src): 15976B/1950i, masked 0.9641 span 74, raw 0.9508 rspan
  115, ordered calls == original, depth 2168. This is the starting point of this lane.
- 21:08 **KEY RESULT (IR level)**: the whole remaining v08 residual (RA in the SyncNative metas/infos region) is caused
  by ONE IR fact: in v08 the rent AccountInfo key pointer is loaded once (meta `rent.key()`) and reused for the infos
  clone (`rent.clone()` key field) because the helper param `rent: &AccountInfo` is noalias -> scoped-noalias metadata
  lets GVN CSE the load across TokenInstruction::pack. Editing ONLY that (fresh `load ptr, ptr %rent` for the clone's
  key) and running llc on the extracted IR gives the EXACT original 147944 body (normalizer-identical, 0 differing
  insns). File: lanes/crank-transfer/ir/e1-MATCH.ll. So the original's rent AccountInfo was not noalias-protected in
  that region (rent passed as a non-noalias form, captured before pack, or cloned outside the helper's scope).
- 21:07 **SOURCE MATCH** (independent of crank-brute, same fix, byte-identical result): v08 + the native helper takes
  `rent: &UncheckedAccount<'info>` (call site `&ctx.accounts.rent`) and clones it with `rent.to_account_info()`.
  Spec lanes/crank-transfer/specs/v10.py (tree v/v10/src). Native .so sha e77815918e6e... == crank-brute-g01's .so.
  measure vs native w584: gained_normalized [147944], lost []; normalizer view 0 differing instructions.
  v11 (+ `let rent_info: &AccountInfo<'info> = rent.as_ref();` at the helper top) builds the identical .so.
  Mechanism: noalias/readonly now sits on the 8-byte UncheckedAccount wrapper inside the accounts struct, not on the
  AccountInfo; the AccountInfo pointer is a loaded value (escape source), so the inliner gives its fields no scope and
  GVN cannot reuse rent.key across the bump-allocator stores / TokenInstruction::pack -> original `ldxdw r3,[r6+0]`
  @13264 with the AccountInfo pointer in r6 across pack (the exact register assignment of the original).
- 21:08 harvested as crank-transfer-g01 = DUPLICATE CONFIRMATION of crank-brute-g01 (harvested 1 min earlier).
- FINAL (21:10): lane stopped per DIRECTIVES 21:08 (Crank closed by crank-brute-g01). Reusable tools left in
  lanes/crank-transfer/tools: mkvar.py (spec-driven variants), run.sh/score.py, extract_fn.py + ocmp.py (rustc IR ->
  llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext in ~0.1 s reproduces the crank body exactly; ocmp compares an
  .o or .so body with the original under the window_map normalizer view).
  Leftover cleanup note for the coordinator: `donation::donation_clone_account` (donation.rs tail) is no longer used by
  the crank in this source (dead_code warning only; no binary effect).
