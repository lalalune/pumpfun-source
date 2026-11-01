# SBPF residual analysis

`residual_analysis.py` compares one exact captured function window with one exact
function in an unstripped reconstruction ELF. It is an offline diagnostic. It
does not modify `score.py`, and none of its fingerprints, block matches,
similarities or rankings are acceptance criteria.

## Why this tool exists

The maintained harness previously had two separate views:

- `target_metric.py` and `win.py` reported flat normalized instruction/field
  differences and sequence similarity.
- `control_flow.py` described the CFG of one image.

Block-order-insensitive and paired-CFG analysis existed only in target-specific
research scripts such as `lanes/callgraph-census/blocksim.py` and
`lanes/admincto-reconstruction/cfg.py`. Those scripts did not admit two arbitrary
ELFs, bind score receipts, retain ambiguous matches, or emit a reusable residual
schema. This analyzer composes the maintained ELF reader, logical instruction
decoder, official normalization and CFG decoder instead of replacing them.

## What is admitted

Both images must be ELF64 little-endian legacy SBPFv0/v1 files with a bounded
`.text` section. Selectors are exact `START:SIZE` ranges or exact ELF symbol
names. The candidate must be unstripped, and its selected range must equal a
complete function-symbol range. A captured original may be stripped. Ranges must
start and end on logical instruction boundaries, so neither half of a two-slot
`LDDW` can be selected independently.

Each image and score receipt is read once and identified by SHA-256 in the report.
Linked type-10 call symbols distinguish relocation identities even when their raw
placeholder immediates are equal. Malformed, duplicate or non-instruction call
relocations are rejected. Symbol labels remain diagnostic evidence, not behavioral
equivalence or source attribution. Repeatable
`--score-receipt` arguments accept `score.py --json` output, require its
`candidate_sha256` to identify the candidate bytes, and require the selected
original window and byte length to be present.
These checks bind supplied receipt metadata; they do not authenticate its producer
or establish that its asserted score flags were recomputed.

The analyzer calls `score.normalize` unchanged. Exact raw and normalized equality
are reported separately from every heuristic result.

## Analyze `admin_cto` at `0x22a10`

From the repository root, build and score the current reconstruction, retaining
the score receipt:

```bash
python3 reconstruction/harness/fastbuild.py \
  --src programs/pump \
  --work ~/.cache/pumpfun-reconstruction/work/admin-cto-residual \
  --out /tmp/pump-admin-cto

python3 reconstruction/harness/score.py \
  /tmp/pump-admin-cto/unstripped.so \
  --baseline reconstruction/pump-main/baseline/score.json \
  --json /tmp/pump-admin-cto/score.json
```

The retained original window is exactly 27,400 bytes. Produce a readable report
on stdout and a complete JSON report at a new destination:

```bash
python3 -B reconstruction/harness/residual_analysis.py \
  evidence/original/pump/deployed.so \
  /tmp/pump-admin-cto/unstripped.so \
  --original-window 0x22a10:27400 \
  --candidate-window 0x22a10:27400 \
  --score-receipt /tmp/pump-admin-cto/score.json \
  --top 30 \
  --json /tmp/pump-admin-cto/admin-cto-residuals.json
```

If a later link layout moves the candidate function, list its exact symbol and
range first:

```bash
python3 reconstruction/harness/win.py sym 'admin_cto::execute$' \
  --cand /tmp/pump-admin-cto/unstripped.so
```

Then replace only `--candidate-window` with the printed address and size. An
exact mangled name from the ELF may instead be passed with `--candidate-symbol`.

For JSON on stdout, omit `--json` and use `--format json`.

## Report interpretation

Block matching proceeds deterministically through equal-position content,
unique target-independent normalized content, unique structural fingerprints,
matched-edge context, and finally mutual-best structural similarity. Every match
records its method, confidence and evidence. Low-margin choices remain under
`control_flow.matching.ambiguities`; they are not forced.

Residuals are ranked with structural gaps first, then unresolved/ambiguous
evidence, then evidence-backed positional shifts. The report detects:

- inserted, removed and replaced opcode sequences;
- normalized immediate/displacement/reserved-field differences;
- destination/source register changes;
- branch-edge and branch-target changes;
- direct, indirect and syscall-or-relocated call ordering and targets;
- equal target-independent blocks or matched branch endpoints that moved.

`positional` means the report has explicit matching evidence for a layout shift.
`structural` means a decoded instruction or CFG property differs. `ambiguous`
means the available ELF evidence cannot distinguish those explanations. None of
these labels claims a source-level cause or runtime equivalence.

## Offline tests

```bash
cd reconstruction/harness
python3 -B -m unittest -v test_residual_analysis.py
python3 -B -m unittest -v \
  test_instruction_stream.py \
  test_residual_fields.py \
  test_control_flow.py \
  test_control_flow_machine.py \
  test_elf_symbols.py \
  test_normalization_conformance.py
```

The first suite includes synthetic malformed inputs, deterministic-output checks,
two-slot `LDDW` coverage, structural/positional residual fixtures, and an
integration check over the retained Pump `admin_cto` capture. It never changes
the captured ELF.
