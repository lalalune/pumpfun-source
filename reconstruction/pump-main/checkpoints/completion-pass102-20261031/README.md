# Completion checkpoint — 2026-10-31

The fresh identity build of current merged Pump source preserves **1,034/1,035 raw and normalized windows (99.90%)**, with zero losses. Across all five maintained checkpoints, **3,337/3,338 windows (99.97%)** match, covering **5,185,728/5,213,128 code bytes (99.47%)**. Whole meaningful ELF equality remains **4/5**.

Only `admin_cto::execute` (`0x22a10`, 27,400 bytes) remains unmatched. Source #3621 improves its token similarity from **67.316% to 67.346%** at unchanged call counts (154 internal, 3 syscall). Positional differences increase from 3,123 to **3,124**. This adds no fully matched window.

All **388 signed synthetic admin-CTO cases** pass against the captured original with genuine dependency CPIs. The [runtime report](admin-runtime.json.gz) is bound to the freshly rebuilt candidate hash. This is bounded behavior evidence, not general equivalence. Prior swap coverage remains historical and was not rerun here.

- [summary.json](summary.json) records source, binary, score and runtime bindings and limits.
- [source-inputs.json](source-inputs.json) seals all 261 program inputs, including unlinked recovered models.
- [score.json.gz](score.json.gz) and [baseline-score.json.gz](baseline-score.json.gz) retain complete inventories scored with the current reviewed scorer.
- New recovered models and captured-program tests provide separate bounded evidence; they do not count as compiled bytecode completion.
- The other four programs retain their [existing exact checkpoints](../completion-20261030/other-programs.json); no fresh build of those programs is claimed.
