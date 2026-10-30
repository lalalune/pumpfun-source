# QuoteControl independently supplied ELF paths

The fresh QuoteControl differential explicitly accepts independently supplied ELF
files, but labels every bound input with `relative_to(ROOT)`. An external candidate
therefore raises before any VM case executes. The serial/parallel corpus consumers
repeat that assumption, and external loader-receipt output has the same problem.

Use repository-relative labels for internal inputs and resolved absolute labels
for explicit external files. Reuse the same representation in the producer and
consumers, keeping all digest/unchanged-input and per-case comparison checks. The
producer now also binds the shared path helper's module source hash. The serial
and parallel callers share the unchanged QuoteControl admission checks.

`reproduce.py` runs `tests/test_quote_control_external_inputs.py` against the real
retained original and compiler-produced candidate. It runs the complete existing
507-case QuoteControl suite for an external candidate and an internal positive
control, then admits the actual receipt and rejects a post-run candidate mutation.
It does not execute all 44 corpus suites or establish whole-program equivalence.

The inert config JSON is separately restored by PR #2164. When absent, this proof
retrieves only that reviewed public fixture, verifies its fixed SHA-256, and
removes the temporary copy afterward. This PR does not include or claim that
separately owned fixture restoration. The source revision and digest are retained
in the proof output. No remote source code is retrieved for execution.

Run on Python 3.12 with the pinned requirements and actual LiteSVM support:

```sh
python -B research/quote-control-external-inputs/reproduce.py
```

Outputs go to `work/scoped-proof` when this packet driver is used. Direct unittest
execution uses temporary outputs. The captured ELF and program sources are never
rewritten. VM accounts and funds are synthetic; nothing is broadcast.

`asset-transition.json` proposes changes to four existing script assets, with
base/proposed LF-source hashes. No script is added to or removed from the frozen
root set and no historical checkpoint is re-sealed.
