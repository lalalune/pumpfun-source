# Completion checkpoint — 2026-10-31

The fresh identity build binds **305 source files and 10 relative directories** using v3 admission. It includes the current contract source and new unlinked reference models. The [source snapshot](source-inputs.json), [build receipt](build.json) and [input hashes](input-bindings.json) identify the exact reviewed inputs.

Pump retains **1,034/1,035 raw and normalized matched windows (99.90%)**, with no losses against a fresh build of main `9bd38c7d5`. The remaining `admin_cto::execute` window has **67.436%** instruction-token similarity, up from 67.376%, at 27,400 bytes. Its positional differences increase from 3,124 to 3,141; these are separate metrics. No new exact window is claimed. The executed Pump image changed, so the prior runtime receipt is not reused.

A fresh **388-case signed synthetic comparison** of this candidate against the captured Pump program passes with zero mismatches. All 776 original/candidate transaction signature vectors are nonempty and verify. This uses genuine dependency CPIs with pool authority nonsigner at the transaction boundary. It is finite runtime evidence, not whole-program equivalence. Prior stopped campaigns remain excluded.

Across the maintained checkpoints, **3,337/3,338 windows (99.97%)** and **5,185,728/5,213,128 code bytes (99.47%)** match. Whole meaningful ELF equality remains **4/5**. The four other program identity checkpoint receipts remain retained evidence. Separate bounded tests do not replace their identity acceptance.

- [Summary](summary.json), [full score](score.json.gz) and [fresh baseline score](baseline-score.json.gz).
- [Fresh runtime receipt](admin-runtime.json.gz) and [independent validation](runtime-validation.json).
- [Semantic review and ELF section comparison](semantic-review.json).

Historical checkpoints are unchanged. Hosted CI is tracked separately in the PR audit.
