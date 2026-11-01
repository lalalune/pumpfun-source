# Maintained source qualification for the volatile reloads

PR #3961 was reopened with two active source changes. The selected source reads the existing curve Box pointer and the accounts-reference slot through volatile shared-reference loads. Each result is used immediately, before mutation; neither a Box owner nor a mutable-reference owner is duplicated. This depends on valid live storage, pointer provenance and the documented default-allocator Box/reference representations.

A fresh identity build of main `34899afd2bbe7cd8bc21f4df369572df3371364b` (the accepted #3974 source) was compared with the actual externally merged #3961 program source. Current maintained `score.py` retains **1,034 raw and normalized matched windows out of 1,035**, with no raw or normalized losses. At 27,400 bytes, the remaining CTO window's token ratio increases **0.67735 → 0.67825** (2,261 → 2,264 matched tokens). Its positional differences increase **3,132 → 3,220**. These are separate metrics; this adds no exact window or compiled-completion percentage.

Selected source snapshot: `44705e177028bc774e1dfad365f1ed3cd77a66ca000dfca788050d889f60dd73` (307 files). Unstripped image: `1cbd58399e985fd4e36ef072a10b84c1ce9b8d31b03eba20593d22c514a0ddd7`. Executed stripped image: `775fc2dfa50f52eac8b434d840c71ffbcc08523a4cec2fc99ec2c3763e2f4db9`.

Fresh signed synthetic qualification passes all 388 independent candidate/original case pairs and 776 nonempty signature vectors. The separate persistent lifecycle suite passes nine cases and 20 distinct transactions per image, with 40 transaction vectors, 78 individual signatures, strict saved-report admission and deterministic replay. These finite comparisons do not establish exhaustive equivalence.

The sole explicit pointer-cast plus size/alignment-guard alternative was excluded: ratio 0.47143, 27,480 bytes and 687 raw-window losses. No further variant search or VM acceptance was performed for it.

The emitted code differs within CTO, with corresponding local basic-block symbol addresses and relocation locations. The 23 moved relative LDDW relocations retain their addends, and the two moved syscall relocations retain identical call instructions and targets. All other file bytes and all ELF, program and section headers agree with the fresh baseline.

The private IR experiment tools and probe are removed. Historical notes and survivor data remain for provenance. Their broad oracle masks and reducer claims are not used for acceptance: an independent LLVM counterexample changed the reduced program and a missing-root input was admitted. Reproduction and acceptance use the maintained identity build, canonical score/target metric and signed differential/lifecycle tools.
