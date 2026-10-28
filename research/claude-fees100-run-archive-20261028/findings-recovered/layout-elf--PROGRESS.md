# recovered from the transcript of lane layout-elf (PROGRESS.md); entries in order

# layout-elf lane — PROGRESS (resume point)

Lane dir: R/lanes/layout-elf  (R = fees100 run root)
Goal: (1) shared/tools/relayout.py (ordered.ld regeneration after source changes), (2) whole-ELF
inventory + diagnostic proof of end state, (3) lanes/layout-elf/WHOLE-ELF-PLAN.md.

## State
- 11:50 lane set up (src = w582 clone, target = warm native).

- 12:12 DONE: tools lbuild.py / relink.py / relobj.py / elfinv.py / transplant.py. Inventory: zero independent
  residuals. Transplant diagnostic: whole-ELF identical (diag/transplant3-candidate.so == original extent).
- NEXT: relayout.py (shared/tools), validate on w580->w582 real transition + synthetic change; WHOLE-ELF-PLAN.md.

- 12:16 relayout.py passes T1/T2/T3 (real transitions, exact). Copied to shared/tools/relayout.py.
  Running synthetic S1 (rename legacy_distribute_creator_fees->..feez + `impl BuybackVault {}` on blank line 2
  of state.rs) and S2 (extra msg! in create -> new rodata atom + .L__unnamed renumbering) with STALE w583 ld.
  Plan: relayout -> relink.py (3 s) + a full lbuild/cbuild with the new ld -> measure raw/normalized, elfinv.

- 12:22 relayout.py DELIVERED + announced (DIRECTIVES 12:22). Proofs T1/T2/T3 exact, S1 (cbuild-confirmed), S2.
  Pending: S2 full cbuild confirmation; T4 = PR304-create on stale w583 ld (event-data body vanishes);
  WHOLE-ELF-PLAN.md sec 3/4 final text.

# layout-elf lane — PROGRESS (resume point)

Lane dir: R/lanes/layout-elf (R = fees100 run root). STATUS 12:31: DONE (coordinator 12:11 BUDGET: "finish the
end-state packet, then return").

## Delivered
- R/shared/tools/relayout.py (+ relayout_build.py one-shot pipeline, lbuild.py, relink.py, elfinv.py, transplant.py
  [diagnostic only], relobj.py, regress.sh). Masters in lanes/layout-elf/tools/.
- lanes/layout-elf/WHOLE-ELF-PLAN.md — end-state proof, full ELF inventory, relayout proofs, final recipe/checklist,
  remaining delta with the target-level facts for Crank/Create.
- Announced in DIRECTIVES 12:04 (end state) and 12:22 (relayout).

## Key results
- Diagnostic transplant of the 3 original bodies into the w582 root object + relink with unchanged ordered.ld:
  stripped == deployed.so[:873256] (0 differing bytes), 585/585 normalized+raw. diag/transplant3-*.
- elfinv on w582, w583, PR304-create(relayout): independent residuals NONE.
- relayout regression (tools/regress.sh, ~5 s): T1 T2 T3 (real transitions, byte-identical to integrators' lds),
  S1 S2 S3 (synthetic; S1/S2 confirmed by full cbuild.py), T4 (PR #304 create) all pass.

## If resuming
- Re-run tools/regress.sh after any relayout.py change (needs builds/ and relayout-tests/ artifacts kept here).
- When a new frontier lands: reference = frontier/<n>/ordered.ld + frontier/container/<n>.map + <n>-container-symbols.so.
- Possible follow-ups: relayout for an anchor-lang-patched crank (dependency rlib hash change; T3-like, untested),
  re-run transplant.py on the newest frontier to re-prove the end state with only Crank/Create transplanted.