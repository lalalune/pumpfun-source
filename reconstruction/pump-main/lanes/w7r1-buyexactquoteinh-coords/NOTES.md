# w7r1-buyexactquoteinh-coords: 0x13f630 buy_v2::buy_exact_quote_in_handler

Angle: coordinate archaeology. Base: origin/main 6edd839 (1027 normalized / 276 raw; eq 20,216 B vs 20,184 B, ratio 0.99635).
No source change is proposed. This is an analysis-only result.

## Coordinate census (ledger ddb201a4)
- All 11 Source{file,line} sites in the window (buy_v2.rs 767, 769, 771, 780, 873, 907, 921, 967, 986, 979, 997) match ours in slot order and line.
- All 59 lddw rodata references decode to identical content: error-name tables, the ix_name, `__event_authority`, and event discriminators. There are no core panic Location constants in this window.
- The residual region (TradeEvent emit_cpi Ok tail, Complete-if, prepare, terminal tag check) has **no coordinates**. The last site is 997, so coordinates cannot tell the candidate tail shapes apart.
- File-wide: buy_v2.rs sites are at 55-129 (helpers plus the BuyV2 try_accounts closure at 129), 345-500 (buy_handler, with closures at 465/469 next to the handler and 498/500 after BuyV2::exit) and 767-997 (eq, closures 881/927/949/959/983/995). There are 200+ line gaps with no sites (130-344, 501-766), which is consistent with helpers that have no error sites, but not proof.
- buy_handler (0x13b9b8) has the same three tail residuals (Complete-if sense, terminal jne tag check, Rc drop-tail dup), so any tail fix should be applied to both handlers.

## Mechanism findings
- GVN strips the StorageLive/Dead of emit_cpi! temps `authority_info`, `inner_data` and the iterator. It reuses the let-bound local for the `[move authority_info]` and `into_iter(move inner_data)` operands. This happens to the TradeEvent and Complete temps alike. `ix_data` keeps its markers because it is borrowed. (ledger beb24bc2)
- **No local helper is MIR-inlined into this handler.** complete_and_prepare, snapshot_quote_mint and emit_complete_cpi are all still calls in the PreCodegen MIR, even with #[inline(always)]. They are inlined by LLVM (alwaysinline). So the markers on the Complete temps in helper forms come from LLVM InlineFunction. The helper's Result reaches the caller as a {i64,ptr} pair, and the Err path re-tests it (`jne r7,2`) because Error::from is opaque. The original has no re-test: its Complete CPI Err path goes straight to the handler return at 0x141cf0. A plain-fn helper is not inlined by LLVM (the call site is cold: threshold 45, cost 955). (ledger d11cf12b)
- Renaming the helper does not change whether it is inlined. (ledger 6b1247e0)
- Repros on 6edd839: e2 is 20,184 B at 0.99432; f2 (e2 plus an inline(always) by-ref emit helper) is 20,216 B at 0.98865. Neither has losses. (ledger 099a5cd3)

## Next ideas (outside this angle)
- Find what makes local helpers MIR-ineligible in this caller, for example the MIR inliner's cycle-avoidance or caller-size gates. A truly MIR-inlined emit helper would give StorageLive-based markers and might let MIR JumpThreading resolve the Result before codegen.
