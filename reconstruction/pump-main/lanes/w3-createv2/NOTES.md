# Lane w3-createv2 (wave 3)

Target: `0x1e7c0` `pump_recovered::create_v2::execute` (original 15,576 B, 125 direct calls).
Base: origin/main 665499915 (1022 normalized / 276 raw); target 0.74106, 15,584 B, 125 calls.

## Trial log

| Trial | Mechanism | Bytes | Ratio | Calls | Official | Ledger id |
| --- | --- | ---: | ---: | ---: | --- | --- |
| base 665499915 | main | 15,584 | 0.74106 | 125 | 1022/276 | - |
| t01 | port of the unmerged createv2-reconstruction round-2 commits (control_account mint by value, vqr before the curve borrow, `creator_fee_bps>0` tested first, creator stored first) on top of the `static MAYHEM_ID` main | 15,632 | 0.75114 | 125 | 1022/276, no gains/losses | edbe0cdb7b824d5791de6665be7f0db4 |

PR #1220 was merged at its first commit, so the three later round-2 commits never reached main.

## IR-oracle analysis (R1 family)

Tools (`scripts/`): `slim.py` turns rustc's module IR into one defined function (execute) plus declarations,
so `llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext` reproduces execute exactly in **0.2 s**
(verified identical to the fastbuild window). `ir.py <name> <edit.py|ll> [base.ll]` applies an IR edit,
runs llc, diffs against the original window; `ir.frame()` dumps frame objects via `-stop-after=prologepilog`.
`maps.py` counts register vs stack-offset mismatches over the abstract alignment; `trace.py`/`dumpat.py`
read `-print-changed` logs.

Oracle results on the R1nc IR (Option<u64> reserves + `Nested(u8)`, quote_mint compared in place; 0.509 built):

| IR edit | llc ratio |
| --- | ---: |
| none (R1nc) | 0.5097 |
| `sel`: else block loads ivqr eagerly and uses `select isNone, ivqr, r` (no bb65.sink.split) | 0.5453 |
| `swap`: quote_mint (32 B) alloca moved to the top slot, val8.sroa.2 (24 B) to quote_mint's slot | 0.7522 |
| `sel` + `swap` | **0.8141** |
| `sel` + `swap` + val8.sroa.2 left unused (orig has an untouched 24 B object at -0x4d8) | 0.8137, frame identical to orig through -0x508 |

So the original frame is: quote_mint 32 B at -0x188 (top, memcmp'd in place), validate Pubkey tail 24 B at -0x4c0,
an untouched 24 B object at -0x4d8, creator1 at -0x4f8, Result slots from -0x508. Residual after that is
register allocation / spill choice (e.g. orig keeps `&ctx.accounts.bonding_curve` spilled from before the
memcmp and loads `accounts+0x100` before the event call).

Mechanisms behind the two edits:
- **sel**: `-print-changed` shows the first module-level InstCombine sinks the eager `unwrap_or` default load
  into the empty None arm block (the load directly precedes the inlined switch), and the last SimplifyCFG
  then merges it with the sol load (bb65.sink.split). In BPF a `select` lowers to the original diamond
  (`r3=ivqr; jeq tag,0; r3=reserves`), so the original IR had a select in the else block.
- **swap**: optimized MIR shows that in R1nc `quote_mint` stays the user local `_83` (`_83 = _353`) because
  it is borrowed by `==`; CopyProp cannot unify a borrowed copy, so its alloca sits at the low (late) slot.
  In x27 quote_mint is never borrowed and unifies with the `?` value fragment `_350` (top slot). The original
  needs both: quote_mint unified with the fragment (top) and compared in place (escaping, so not split).

Source trials (all 1022/276, no gains/losses, all rejected): vqr helper by value (0.452: ArgPromotion hoists
both Global loads), by reference (0.509), result kept as `quote` with fields in place (0.416: 56 B quote alloca),
`to_bytes()==[0;32]` compare (0.448) and a by-value `is_sol_quote` helper (0.455, MIR-inlined): the last two
put quote_mint at the top slot but, no longer escaping, SROA splits it to 24 B.
