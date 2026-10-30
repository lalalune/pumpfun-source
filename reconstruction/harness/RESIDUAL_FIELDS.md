# Normalized residual fields

`target_metric.py` includes `normalized_field_differences` for each candidate.
Counts cover all differing decoded fields; `--slots` bounds the first detail rows.
Offsets are relative to the selected function. Both inputs use the existing scorer
normalization, so masked relocations are not presented as reconstruction residuals.

Comparison requires equal lengths and identical instruction boundaries. Otherwise
`comparable` is false: no speculative positional alignment is attempted. LDDW is
one instruction with a 64-bit immediate; reserved continuation bytes stay visible.
Register, displacement and opcode differences can guide source experiments but do
not establish their cause, runtime equivalence, or acceptance. The score is unchanged.
