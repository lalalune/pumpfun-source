# crank-transfer PROGRESS (window 147944 crank_donation_fee_pda)
Lane dir: RR/lanes/crank-transfer. src/ = pristine w584 clone, target/ = warm native target.
Build: nbuild.sh needs ABSOLUTE paths (it cd's into SRC). Baseline build = w584 native sha 45d10d76 (12 s).

## Log
- 20:58 lane set up; baseline verified (out/base-symbols.so == frontier/native/w584-symbols.so).
- Tools: tools/mkvar.py NAME [SPEC] (v/NAME/src = src + spec edits; specs/*.py with inherit()), tools/run.sh NAME SLOT
  (build into tSLOT, score -> out/scores.log), tools/score.py SYMBOLS [NAME]. Targets t1..t4.
- 21:00 v08 (crank-b v08 reconstructed from findings, specs/v08.py): 15976B/1950i masked 0.9641 span 74 raw 0.9508
  rspan 115, calls_eq, depth 2168. v07 (no event data change) 15952B/1947i masked 0.8935.
- 21:05 IR loop: tools/extract_fn.py (crank fn + all others as declares) + llc -O3 -relocation-model=pic
  -mattr=+store-imm,+jmp-ext (0.1 s) + tools/ocmp.py (sig view == window_map normalizer). v08 IR reproduces v08 exactly.
- 21:08 **IR-LEVEL MATCH**: ir/e1-MATCH.ll = v08 IR + ONE change: the rent AccountInfo clone (infos[1]) reloads
  rent.key (`%rk2 = load ptr, ptr %_17`) instead of reusing the meta's rent.key load %_72.i (CSE'd across pack via the
  helper's noalias `rent: &AccountInfo` scope). llc output: sig span 0 = EXACT original 147944.
  => need a source form where the rent key is NOT CSE'd between AccountMeta::new_readonly(rent.key()) and rent.clone().
- 21:07 SOURCE MATCH: v10 (specs/v10.py = v08 + helper param `rent: &UncheckedAccount<'info>`, call `&ctx.accounts.rent`,
  `rent.to_account_info()` in infos) and v11 (+ named `rent_info = rent.as_ref()`): identical .so (sha e7781591),
  measure gained_normalized [147944], lost []; ocmp sig span 0.
- 21:08 harvested RR/shared/harvest/crank-transfer-g01 (INDEX.log). crank-brute-g01 harvested the SAME fix 1 min
  earlier (byte-identical native .so) -> my harvest is an independent duplicate confirmation (noted in its NOTES.md).
- 21:10 DIRECTIVES 21:08: Crank CLOSED by crank-brute-g01; all lanes stop. Lane finished. Nothing running.
